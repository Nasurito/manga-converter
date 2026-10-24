import pytest

import module.manga
import module.search_engine
from module.manga import Manga
from module.search_engine import SearchEngine


class FakeScraper:
    """Scraper factice qui enregistre s'il a été fermé."""
    instances = []

    def __init__(self, language="fr", results=None, fail=False):
        self.language, self.results, self.fail = language, results or [], fail
        self.closed = False
        FakeScraper.instances.append(self)

    def get_manga_details(self, url):
        if self.fail:
            raise RuntimeError("page introuvable")
        return {"manga_name": "Test", "author": "A", "manga_genres": [], "cover": None,
                "chapters_data": [{"id": 1, "link": "c1"}, {"id": 1.5, "link": "c1.5"}]}

    def search(self, key_word):
        return self.results

    def get_language(self):
        return self.language

    def close(self):
        self.closed = True


@pytest.fixture(autouse=True)
def reset_instances():
    FakeScraper.instances.clear()


def test_manga_context_manager_closes_scraper(monkeypatch):
    monkeypatch.setattr(module.manga, "get_scraper_from_domain", lambda domain: FakeScraper())

    with Manga("https://site.com/manga", output_dir="out") as manga:
        assert [c.id() for c in manga.manga_chapters] == [1, 1.5]
        assert manga.manga_chapters[0].output_dir == "out"
        assert not manga.scraper.closed

    assert manga.scraper.closed


def test_manga_closes_scraper_when_loading_fails(monkeypatch):
    monkeypatch.setattr(module.manga, "get_scraper_from_domain", lambda domain: FakeScraper(fail=True))

    with pytest.raises(RuntimeError):
        Manga("https://site.com/manga")
    assert FakeScraper.instances[0].closed


def test_search_lists_titles_without_loading_mangas(monkeypatch):
    monkeypatch.setattr(module.search_engine, "SCRAPERS", {
        "fr-site": lambda: FakeScraper("fr", [("Titre FR", "https://fr-site.com/a")]),
        "en-site": lambda: FakeScraper("en", [("Title EN", "https://en-site.com/b")]),
    })
    # Charger un manga pendant la recherche ferait un appel réseau par résultat : on l'interdit
    monkeypatch.setattr(module.manga.Manga, "__init__", lambda *a, **k: pytest.fail("Manga chargé pendant la recherche"))

    engine = SearchEngine("titre")

    assert engine.results == {"fr": [("Titre FR", "https://fr-site.com/a")], "en": [("Title EN", "https://en-site.com/b")]}
    assert all(scraper.closed for scraper in FakeScraper.instances)

    answers = iter(["2", "1"])  # langue EN, puis premier résultat
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))
    assert engine.select_manga() == "https://en-site.com/b"


def test_search_without_results(monkeypatch, no_prompt):
    monkeypatch.setattr(module.search_engine, "SCRAPERS", {"site": lambda: FakeScraper("fr", [])})

    assert SearchEngine("rien").select_manga() is None
