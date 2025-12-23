import re
import json
import os
import tempfile
from bs4 import BeautifulSoup

import utils
from module.abstract_classes.BaseScaper import BaseScraper

class MangakatanaScraper(BaseScraper):
    """Scraper pour le site mangakatana.com."""

    def __init__(self):
        super().__init__("https://mangakatana.com")

    def get_manga_details(self, manga_url: str) -> dict:
        """
        Récupère les détails d'un manga depuis sa page URL.
        Utilise BeautifulSoup pour un parsing plus robuste.
        """
        html_page, driver = utils.get_page(manga_url,self.do_require_driver())
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
        genres_tags = soup.select('.info .genres a')
        details['manga_genres'] = [tag.text.strip() for tag in genres_tags]

        # Couverture
        cover_tag = soup.select_one('#single_book .cover img')
        if cover_tag and 'src' in cover_tag.attrs:
            cover_url = cover_tag['src']
            root_dir = os.path.join(tempfile.gettempdir(), details['manga_name'])
            os.makedirs(root_dir, exist_ok=True)
            cover_path = os.path.join(root_dir, "thumb.jpg")
            utils.download_image(cover_url, cover_path,self.do_require_driver(),driver)
            details['cover'] = cover_path
        else:
            details['cover'] = None

        if driver:
            driver.quit()

        # Chapitres
        chapters_data = []
        chapters_table = soup.select_one('.chapters table.uk-table-striped')
        if chapters_table:
            for row in chapters_table.find_all('tr'):
                link_tag = row.find('a')
                if link_tag and 'href' in link_tag.attrs:
                    chapter_link = link_tag['href']
                    match = re.search(r'Chapter\s*([\d\.]+)', link_tag.text)
                    if match:
                        chapter_num_str = match.group(1)
                        chapters_data.append({
                            "id": utils.normalize_volume(chapter_num_str),
                            "link": chapter_link
                        })
        
        details['chapters_data'] = chapters_data
        return details

    def get_chapter_images(self, chapter_url: str) -> list[str]:
        """
        Récupère la liste des URLs des images pour un chapitre donné.
        """
        html_page, driver = utils.get_page(chapter_url,self.do_require_driver())
        if not html_page:
            return []

        # Définir le modèle d'expression régulière pour rechercher la variable JavaScript contenant les liens des pages
        pattern = r"var\s+thzq\s*=\s*(\[[^\]]+\])"
        
        # Rechercher la correspondance dans la page HTML du chapitre
        match = re.search(pattern, html_page, re.DOTALL)
        
        if match:
            try:
                image_urls = eval(match.group(1))
                return image_urls,driver
            except json.JSONDecodeError:
                print(f"❌ Erreur de parsing JSON pour les images de {chapter_url}")
                return [],driver
        
        return [] ,driver 
    
    def get_language(self) -> str:
        """
        Permet de retourner la langues des mangas du site mangakatana.
        
        :param self: Description
        :return: 'fr' ou 'en' en fonction de la langue du site
        :rtype: str
        """
        return "en"
    
    def do_require_driver(self) -> bool:
        return False