from bs4 import BeautifulSoup

from module.scrapers import get_scraper_from_domain
from module.scrapers.lelmanga_scraper import LelmangaScraper
from module.scrapers.mangakatana_scraper import MangakatanaScraper
from module.scrapers.sushiscan_scraper import SushiscanScraper


def chapter_ids(details):
    return [chapter["id"] for chapter in details["chapters_data"]]


def test_lelmanga_manga_details(offline_pages):
    offline_pages({"manga": "lelmanga-manga.html"})
    details = LelmangaScraper().get_manga_details("manga")

    assert details["manga_name"] == "Jujutsu Kaisen"
    assert details["author"] == "Akutami Gege"
    assert "Action" in details["manga_genres"]
    assert len(details["chapters_data"]) == 274
    assert details["chapters_data"][0] == {"id": 271.5, "link": "https://www.lelmanga.com/jujutsu-kaisen-271-5/"}


def test_lelmanga_keeps_half_chapters(offline_pages):
    offline_pages({"manga": "lelmanga-manga.html"})
    ids = chapter_ids(LelmangaScraper().get_manga_details("manga"))

    # 271.5 ne doit plus être confondu avec 271, et "168.5 (VUS)" doit être lu comme 168.5
    assert {271, 271.5, 262.5, 168.5} <= set(ids)
    assert len(ids) == len(set(ids)), "deux chapitres ont le même numéro"


def test_lelmanga_chapter_images(offline_pages):
    offline_pages({"chapter": "lelmanga-chapter.html"})
    images, driver = LelmangaScraper().get_chapter_images("chapter")

    assert driver is None
    assert len(images) == 51
    assert images[0] == "https://www.lelmanga.com/wp-content/uploads/2021/11/01-145.jpg"


def test_mangakatana_manga_details(offline_pages):
    offline_pages({"manga": "mangakatana-manga.html"})
    details = MangakatanaScraper().get_manga_details("manga")

    assert details["manga_name"] == "Kaiju No. 8"
    assert details["author"] == "Matsumoto Naoya"
    assert "Shounen" in details["manga_genres"]
    assert len(details["chapters_data"]) == 122
    assert details["chapters_data"][0] == {"id": 121, "link": "https://mangakatana.com/manga/kaiju-no-8.24869/c121"}


def test_mangakatana_keeps_half_chapters(offline_pages):
    offline_pages({"manga": "mangakatana-manga.html"})
    ids = chapter_ids(MangakatanaScraper().get_manga_details("manga"))

    assert {11, 11.5, 12} <= set(ids)
    assert len(ids) == len(set(ids)), "deux chapitres ont le même numéro"


def test_mangakatana_chapter_images(offline_pages):
    offline_pages({"chapter": "mangakatana-chapitre.html"})
    images, _ = MangakatanaScraper().get_chapter_images("chapter")

    assert len(images) == 53
    assert all(url.startswith("https://i1.mangakatana.com/") for url in images)


def test_chapterlist_fallback_on_href():
    # Pas d'attribut data-num : le numéro est lu dans le lien (cas de sushiscan)
    soup = BeautifulSoup("""
        <ul id="chapterlist">
            <li><a href="https://sushiscan.fr/test-chapter-13/">Chapitre</a></li>
            <li data-num="12.5"><a href="https://sushiscan.fr/test-chapter-12/">Chapitre</a></li>
        </ul>""", "html.parser")

    chapters = SushiscanScraper().parse_chapterlist(soup, r'chapter-([\d\.]+)', fallback_on_href=True)

    assert chapters == [
        {"id": 13, "link": "https://sushiscan.fr/test-chapter-13/"},
        {"id": 12.5, "link": "https://sushiscan.fr/test-chapter-12/"},  # data-num est prioritaire
    ]


def test_reader_images_prefers_data_src():
    soup = BeautifulSoup("""
        <div id="readerarea">
            <img src="placeholder.gif" data-src=" https://img/1.jpg ">
            <img src="https://img/2.jpg">
            <img src="">
        </div>""", "html.parser")

    assert SushiscanScraper().parse_reader_images(soup, "#readerarea img") == ["https://img/1.jpg", "https://img/2.jpg"]


def test_get_scraper_from_domain():
    assert isinstance(get_scraper_from_domain("lelmanga"), LelmangaScraper)
    assert isinstance(get_scraper_from_domain("mangakatana"), MangakatanaScraper)
    assert get_scraper_from_domain("unknown-site") is None
    assert get_scraper_from_domain(None) is None
