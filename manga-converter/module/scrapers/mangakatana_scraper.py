import re
import ast
from bs4 import BeautifulSoup

import utils
from module.abstract_classes.base_scraper import BaseScraper

class MangakatanaScraper(BaseScraper):
    """Scraper pour le site mangakatana.com."""

    def __init__(self):
        super().__init__("https://mangakatana.com")

    def get_manga_details(self, manga_url: str) -> dict:
        """
        Récupère les détails d'un manga depuis sa page URL.
        Utilise BeautifulSoup pour un parsing plus robuste.
        """
        html_page, driver = self.fetch_page(manga_url)
        if not html_page:
            print(f"❌ Impossible de récupérer la page pour {manga_url}")
            return {}

        soup = BeautifulSoup(html_page, 'html.parser')
        details = {}

        # Nom du manga
        title_tag = soup.select_one('h1.heading')
        details['manga_name'] = title_tag.text.strip() if title_tag else "Nom inconnu"

        # Auteur
        author_tag = soup.select_one('a.author')
        details['author'] = author_tag.text.strip() if author_tag else "Auteur inconnu"

        # Genres
        details['manga_genres'] = [tag.text.strip() for tag in soup.select('.info .genres a')]

        # Couverture
        cover_tag = soup.select_one('#single_book .cover img')
        details['cover'] = self.download_cover(cover_tag.get('src') if cover_tag else None, details['manga_name'], driver)

        # Chapitres
        chapters_data = []
        for link_tag in soup.select('.chapters table.uk-table-striped tr a[href]'):
            match = re.search(r'Chapter\s*([\d\.]+)', link_tag.text)
            if match:
                chapters_data.append({
                    "id": utils.normalize_volume(match.group(1)),
                    "link": link_tag['href']
                })

        details['chapters_data'] = chapters_data
        return details

    def get_chapter_images(self, chapter_url: str) -> tuple[list,None]:
        """
        Récupère la liste des URLs des images pour un chapitre donné.
        """
        html_page, driver = self.fetch_page(chapter_url)
        if not html_page:
            return [], driver

        # Les liens des pages sont stockés dans la variable JavaScript 'thzq'
        match = re.search(r"var\s+thzq\s*=\s*(\[[^\]]+\])", html_page, re.DOTALL)
        if match:
            try:
                return ast.literal_eval(match.group(1)), driver
            except (ValueError, SyntaxError):
                print(f"❌ Erreur de parsing pour les images de {chapter_url}")

        return [], driver

    def search(self, key_word: str) -> list[tuple[str, str]]:
        html_page, _ = self.fetch_page(f"{self.base_url}/?search={key_word.replace(' ', '+')}&search_by=book_name")
        if not html_page:
            return []

        soup = BeautifulSoup(html_page, 'html.parser')
        return [(link.text.strip(), link['href']) for link in soup.select('#book_list h3.title a[href]')]

    def get_language(self) -> str:
        """
        Permet de retourner la langues des mangas du site mangakatana.

        :return: 'fr' ou 'en' en fonction de la langue du site
        :rtype: str
        """
        return "en"

    def do_require_driver(self) -> bool:
        return False
