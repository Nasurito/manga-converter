import os
import re
import tempfile
from abc import ABC, abstractmethod
import undetected_chromedriver as uc

import utils

class BaseScraper(ABC):
    """
    Classe de base abstraite pour tous les scrapers de mangas.
    Elle ne peut pas être instanciée directement.
    """

    def __init__(self, base_url):
        self.base_url = base_url

    @abstractmethod
    def get_manga_details(self, manga_url: str) -> dict:
        """
        Récupère les informations d'un manga (titre, auteur, chapitres, etc.).
        Doit être implémenté par les sous-classes.
        """
        pass

    @abstractmethod
    def get_chapter_images(self, chapter_url: str) -> tuple[list,uc.Chrome]:
        """
        Récupère la liste des URLs des images pour un chapitre donné.
        Doit être implémenté par les sous-classes.
        """
        pass

    @abstractmethod
    def get_language(self) -> str:
        """
        Récupère la langue du site.
        Doit être implémenté par les sous-classes.
        """
        pass

    @abstractmethod
    def do_require_driver(self) -> bool:
        """
        Indique si le scraper nécessite un driver pour fonctionner.
        Doit être implémenté par les sous-classes.
        """
        pass

    def search(self, key_word: str) -> list[str]:
        """
        Retourne les URLs des mangas correspondant au mot clé.
        Par défaut le site ne supporte pas la recherche, les sous-classes peuvent la surcharger.
        """
        return []

    # Méthodes concrètes partagées par les scrapers

    def fetch_page(self, url: str, driver: uc.Chrome = None, ready_selector: str = None, min_count: int = 1) -> tuple[str,uc.Chrome]:
        """
        Récupère le HTML d'une page du site, avec un driver si le site l'exige.
        Avec un driver, ready_selector/min_count indiquent quand la page est chargée (voir utils.wait_for_page).
        """
        return utils.get_page(url, self.do_require_driver(), driver, referer=self.base_url,
                              ready_selector=ready_selector, min_count=min_count)

    def download_cover(self, cover_url: str, manga_name: str, driver: uc.Chrome = None) -> str:
        """Télécharge la couverture dans le dossier temporaire du manga et retourne son chemin (ou None)."""
        if not cover_url:
            return None
        root_dir = os.path.join(tempfile.gettempdir(), manga_name)
        os.makedirs(root_dir, exist_ok=True)
        cover_path = os.path.join(root_dir, "thumb.jpg")
        return cover_path if utils.download_image(cover_url, cover_path, driver) else None

    def parse_chapterlist(self, soup, fallback_pattern: str, fallback_on_href: bool = False) -> list[dict]:
        """
        Parse la liste '#chapterlist li' utilisée par les sites basés sur le thème WordPress MangaReader.
        Le numéro est lu dans l'attribut 'data-num', sinon extrait avec fallback_pattern
        depuis le texte du lien (ou son href si fallback_on_href).
        """
        chapters_data = []
        for li in soup.select('#chapterlist li'):
            link_tag = li.select_one('a[href]')
            if not link_tag:
                continue

            number = li.get('data-num')
            if not number:
                source = link_tag['href'] if fallback_on_href else link_tag.text
                match = re.search(fallback_pattern, source, re.IGNORECASE)
                number = match.group(1) if match else "0"

            chapters_data.append({
                "id": utils.normalize_volume(number),
                "link": link_tag['href']
            })
        return chapters_data

    def parse_reader_images(self, soup, selector: str) -> list[str]:
        """Retourne les URLs des images du lecteur (gère le lazy loading via 'data-src')."""
        images = []
        for img in soup.select(selector):
            src = img.get('data-src') or img.get('src')
            if src and src.strip():
                images.append(src.strip())
        return images
