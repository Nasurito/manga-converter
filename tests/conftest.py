import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Le programme importe ses modules depuis le dossier manga-converter (import utils, from module...)
sys.path.insert(0, os.path.join(ROOT, "manga-converter"))

# Pages HTML réelles enregistrées depuis les sites, utilisées à la place du réseau
SAMPLES_DIR = os.path.join(ROOT, "Docs", "html_fetched_exemple")

import utils


@pytest.fixture
def offline_pages(monkeypatch):
    """
    Remplace le réseau : get_page renvoie la page d'exemple associée à l'url demandée
    et download_image n'écrit rien. Usage : offline_pages({"url": "fichier.html"})
    """
    def install(pages: dict[str, str]):
        def fake_get_page(url, *args, **kwargs):
            with open(os.path.join(SAMPLES_DIR, pages[url]), encoding="utf-8") as f:
                return f.read(), None
        monkeypatch.setattr(utils, "get_page", fake_get_page)
        monkeypatch.setattr(utils, "download_image", lambda *args, **kwargs: True)
    return install


@pytest.fixture
def no_prompt(monkeypatch):
    """Fait échouer le test si le code demande quelque chose à l'utilisateur."""
    def fail(*args, **kwargs):
        raise AssertionError(f"input() appelé de façon inattendue : {args}")
    monkeypatch.setattr("builtins.input", fail)
