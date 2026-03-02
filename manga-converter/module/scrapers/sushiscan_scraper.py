import os
import tempfile
import re
from bs4 import BeautifulSoup
import utils
from module.abstract_classes.BaseScaper import BaseScraper

class SushiscanScraper(BaseScraper):
    """Scraper pour le site sushiscan.fr (ou .net)"""

    def __init__(self):
        super().__init__("https://sushiscan.fr")
        self.driver=None

    def get_manga_details(self, manga_url: str) -> dict:
        html_page, driver = utils.get_page(manga_url,self.do_require_driver())
        if not html_page:
            return {}
        
        self.driver = driver

        soup = BeautifulSoup(html_page, 'html.parser')
        details = {}

        # Titre
        title_tag = soup.select_one('h1.entry-title')
        details['manga_name'] = title_tag.text.strip() if title_tag else "Inconnu"

        # Auteur
        # Sushiscan utilise souvent un tableau ou des listes pour les infos
        author_row = soup.find(lambda tag: tag.name == "td" and "Auteur" in tag.text)
        if author_row:
            next_td = author_row.find_next_sibling('td')
            details['author'] = next_td.text.strip() if next_td else "Inconnu"
        else:
            details['author'] = "Inconnu"

        # Genres
        genres_tags = soup.select('.seriestugenre a')
        details['manga_genres'] = [tag.text.strip() for tag in genres_tags]

        # Couverture
        cover_tag = soup.select_one('.thumb img')
        if cover_tag and 'src' in cover_tag.attrs:
            cover_url = cover_tag['src']
            root_dir = os.path.join(tempfile.gettempdir(), details['manga_name'])
            os.makedirs(root_dir, exist_ok=True)
            cover_path = os.path.join(root_dir, "thumb.jpg")
            utils.download_image(cover_url, cover_path,self.do_require_driver(),self.driver)
            details['cover'] = cover_path
        else:
            details['cover'] = None
            
        # Chapitres
        chapters_data = []
        # Souvent dans une liste avec id #chapterlist
        chapter_links = soup.select('#chapterlist li')
        
        for li in chapter_links:
            link_tag = li.select_one('a')
            num_attr = li.get('data-num')
            
            if link_tag and 'href' in link_tag.attrs:
                if not num_attr:
                    # Fallback regex sur le texte ou le lien
                    match = re.search(r'chapter-([\d\.]+)', link_tag['href'])
                    num_attr = match.group(1) if match else "0"

                chapters_data.append({
                    "id": utils.normalize_volume(num_attr),
                    "link": link_tag['href']
                })

        details['chapters_data'] = chapters_data
        return details

    def get_chapter_images(self, chapter_url: str) -> list:
        html_page, driver = utils.get_page(chapter_url,self.do_require_driver(),self.driver)
        if not html_page:
            return [],None

        soup = BeautifulSoup(html_page, 'html.parser')
        images = []

        # Sushiscan met souvent les images dans #readerarea
        # Attention : parfois les images sont en lazy loading avec data-src
        img_tags = soup.select('#readerarea img')
        
        for img in img_tags:
            src = img.get('data-src') or img.get('src')
            if src:
                images.append(src.strip())
        
        return images,driver
    
    def get_language(self) -> str:
        """
        Permet de retourner la langues des mangas du site Sushiscan.
        
        :param self: Description
        :return: 'fr' ou 'en' en fonction de la langue du site
        :rtype: str
        """
        return "fr"
    
    def do_require_driver(self) -> bool:
        return True