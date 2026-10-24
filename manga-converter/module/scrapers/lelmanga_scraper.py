import re
from bs4 import BeautifulSoup
from module.abstract_classes.base_scraper import BaseScraper

class LelmangaScraper(BaseScraper):
    """Scraper pour le site lelmanga.com"""

    def __init__(self):
        super().__init__("https://www.lelmanga.com")

    def get_manga_details(self, manga_url: str) -> dict:
        html_page, driver = self.fetch_page(manga_url)
        if not html_page:
            return {}

        soup = BeautifulSoup(html_page, 'html.parser')
        details = {}

        # Titre
        title_tag = soup.select_one('h1.entry-title')
        details['manga_name'] = title_tag.text.strip() if title_tag else "Inconnu"

        # Auteur (souvent dans une div avec class 'imptdt' ou 'fmed')
        details['author'] = "Auteur inconnu"
        author_tag = soup.find(string=re.compile("Auteur"))
        if author_tag:
            parent = author_tag.find_parent('div')
            if parent:
                details['author'] = parent.get_text(strip=True).replace("Auteur", "").strip()

        # Genres
        details['manga_genres'] = [tag.text.strip() for tag in soup.select('.mgen a')]

        # Couverture
        cover_tag = soup.select_one('.thumb img')
        details['cover'] = self.download_cover(cover_tag.get('src') if cover_tag else None, details['manga_name'], driver)

        # Chapitres
        details['chapters_data'] = self.parse_chapterlist(soup, r'Chapitre\s*([\d\.]+)')
        return details

    def get_chapter_images(self, chapter_url: str) -> tuple[list,None]:
        html_page, driver = self.fetch_page(chapter_url)
        if not html_page:
            return [], driver

        soup = BeautifulSoup(html_page, 'html.parser')
        return self.parse_reader_images(soup, '.readerarea img, #readerarea img'), driver

    def search(self, key_word: str) -> list[tuple[str, str]]:
        html_page, _ = self.fetch_page(f"{self.base_url}/?s={key_word.replace(' ', '+')}")
        if not html_page:
            return []

        soup = BeautifulSoup(html_page, 'html.parser')
        results = []
        for div in soup.select('div.bs'):
            link = div.select_one('a[href]')
            if link:
                title_tag = div.select_one('.tt')
                title = link.get('title') or (title_tag.text.strip() if title_tag else link['href'])
                results.append((title, link['href']))
        return results

    def get_language(self) -> str:
        """
        Permet de retourner la langues des mangas du site lelmanga.com

        :return: 'fr' ou 'en' en fonction de la langue du site
        :rtype: str
        """
        return "fr"

    def do_require_driver(self) -> bool:
        return False
