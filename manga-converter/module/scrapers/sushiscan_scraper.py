from bs4 import BeautifulSoup
from module.abstract_classes.base_scraper import BaseScraper

class SushiscanScraper(BaseScraper):
    """Scraper pour le site sushiscan.fr (ou .net)"""

    def __init__(self):
        super().__init__("https://sushiscan.fr")
        # Le driver est conservé pour ne résoudre le CAPTCHA qu'une seule fois
        self.driver = None

    def get_manga_details(self, manga_url: str) -> dict:
        html_page, self.driver = self.fetch_page(manga_url, self.driver, ready_selector='#chapterlist li')
        if not html_page:
            return {}

        soup = BeautifulSoup(html_page, 'html.parser')
        details = {}

        # Titre
        title_tag = soup.select_one('h1.entry-title')
        details['manga_name'] = title_tag.text.strip() if title_tag else "Inconnu"

        # Auteur
        # Sushiscan utilise souvent un tableau ou des listes pour les infos
        author_row = soup.find(lambda tag: tag.name == "td" and "Auteur" in tag.text)
        next_td = author_row.find_next_sibling('td') if author_row else None
        details['author'] = next_td.text.strip() if next_td else "Inconnu"

        # Genres
        details['manga_genres'] = [tag.text.strip() for tag in soup.select('.seriestugenre a')]

        # Couverture
        cover_tag = soup.select_one('.thumb img')
        details['cover'] = self.download_cover(cover_tag.get('src') if cover_tag else None, details['manga_name'], self.driver)

        # Chapitres
        details['chapters_data'] = self.parse_chapterlist(soup, r'chapter-([\d\.]+)', fallback_on_href=True)
        return details

    def get_chapter_images(self, chapter_url: str) -> tuple[list,object]:
        # Au moins 2 images : en mode de lecture "page par page", une seule image est affichée
        html_page, self.driver = self.fetch_page(chapter_url, self.driver, ready_selector='#readerarea img', min_count=2)
        if not html_page:
            return [], self.driver

        soup = BeautifulSoup(html_page, 'html.parser')
        # Attention : parfois les images sont en lazy loading avec data-src
        return self.parse_reader_images(soup, '#readerarea img'), self.driver

    def close(self) -> None:
        """Ferme le navigateur ouvert pour le CAPTCHA."""
        if self.driver:
            self.driver.quit()
            self.driver = None

    def get_language(self) -> str:
        """
        Permet de retourner la langues des mangas du site Sushiscan.

        :return: 'fr' ou 'en' en fonction de la langue du site
        :rtype: str
        """
        return "fr"

    def do_require_driver(self) -> bool:
        return True
