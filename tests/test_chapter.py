import os
import tempfile
import zipfile

import pytest

import utils
from module.chapter import Chapter


class FakeScraper:
    """Scraper factice qui renvoie trois pages et compte les appels."""
    def __init__(self):
        self.calls = 0

    def get_chapter_images(self, chapter_url):
        self.calls += 1
        return ["https://img/1.jpg", "https://img/2.jpg", "https://img/3.jpg"], None

    def requires_driver(self):
        return False


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    """Isole le cache (dossier temporaire) et les exports (./export) dans un dossier de test."""
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path / "cache"))
    os.makedirs(tmp_path / "cache")
    monkeypatch.chdir(tmp_path)

    downloads = []
    def fake_download(url, path, driver=None, **kwargs):
        downloads.append(url)
        with open(path, "wb") as f:
            f.write(url.encode())
        return True
    monkeypatch.setattr(utils, "download_image", fake_download)
    return downloads


def test_number_keeps_half_chapters():
    assert Chapter(12, "M", "x", FakeScraper()).number == 12
    assert Chapter(12.5, "M", "x", FakeScraper()).number == 12.5
    assert Chapter(12.0, "M", "x", FakeScraper()).number == 12


def test_export_path():
    assert Chapter(12.5, "Manga", "x", FakeScraper()).export_path("CBZ") == os.path.join("./export", "Manga", "cbz", "chapter_12.5.cbz")


def test_download_cbz(workspace, no_prompt):
    chapter = Chapter(1, "Manga", "x", FakeScraper())

    assert chapter.download("CBZ") is True
    with zipfile.ZipFile(chapter.export_path("CBZ")) as cbz:
        assert sorted(cbz.namelist()) == ["001.jpg", "002.jpg", "003.jpg"]


def test_existing_export_is_not_downloaded_again(workspace, no_prompt):
    Chapter(1, "Manga", "x", FakeScraper()).download("CBZ")

    scraper = FakeScraper()
    assert Chapter(1, "Manga", "x", scraper).download("CBZ") is True
    assert scraper.calls == 0


def test_cache_is_reused_without_asking(workspace, no_prompt):
    Chapter(1, "Manga", "x", FakeScraper()).fetch_images()
    workspace.clear()

    chapter = Chapter(1, "Manga", "x", FakeScraper())
    assert chapter.fetch_images(use_cache=True) is True
    assert workspace == []  # aucune image re-téléchargée
    assert len(chapter.page_paths) == 3


def test_cache_is_ignored_with_use_cache_false(workspace, no_prompt):
    Chapter(1, "Manga", "x", FakeScraper()).fetch_images()
    workspace.clear()

    chapter = Chapter(1, "Manga", "x", FakeScraper())
    assert chapter.fetch_images(use_cache=False) is True
    assert len(workspace) == 3  # toutes les images re-téléchargées


def test_unsafe_manga_title_is_cleaned_in_paths(workspace, no_prompt):
    chapter = Chapter(1, "Re:Zero / Arc 1?", "x", FakeScraper(), output_dir="mes_mangas")

    assert chapter.export_path("CBZ") == os.path.join("mes_mangas", "Re_Zero _ Arc 1_", "cbz", "chapter_1.cbz")
    assert chapter.download("CBZ") is True
    assert os.path.exists(chapter.export_path("CBZ"))


class ManyPagesScraper(FakeScraper):
    def get_chapter_images(self, chapter_url):
        self.calls += 1
        return [f"https://img/{i}.jpg" for i in range(1, 21)], "driver"


def test_one_session_for_the_whole_chapter_and_pages_stay_in_order(workspace, monkeypatch, no_prompt):
    import random, time
    sessions = []
    def fake_build_session(driver=None, referer=None):
        sessions.append(driver)
        return "session"
    monkeypatch.setattr(utils, "build_session", fake_build_session)

    received = []
    def fake_download(url, path, session=None, **kwargs):
        received.append(session)
        time.sleep(random.uniform(0, 0.01))  # les téléchargements parallèles finissent dans le désordre
        with open(path, "w") as f:
            f.write(url)
        return True
    monkeypatch.setattr(utils, "download_image", fake_download)

    chapter = Chapter(1, "Manga", "x", ManyPagesScraper())
    assert chapter.fetch_images() is True

    assert sessions == ["driver"]  # cookies du navigateur copiés une seule fois
    assert set(received) == {"session"}
    assert [open(p).read() for p in chapter.page_paths] == [f"https://img/{i}.jpg" for i in range(1, 21)]


def test_failed_image_makes_the_chapter_retry(workspace, monkeypatch, no_prompt):
    monkeypatch.setattr("module.chapter.DOWNLOAD_ATTEMPTS", 1)
    failures = {"https://img/2.jpg"}
    def fake_download(url, path, **kwargs):
        if url in failures:
            failures.clear()  # échoue une seule fois
            return False
        with open(path, "w") as f:
            f.write(url)
        return True
    monkeypatch.setattr(utils, "download_image", fake_download)

    scraper = FakeScraper()
    chapter = Chapter(1, "Manga", "x", scraper)

    assert chapter.fetch_images() is True
    assert scraper.calls == 2
    assert len(chapter.page_paths) == 3
