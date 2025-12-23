import os
import tempfile
import re
from bs4 import BeautifulSoup
import utils
from module.abstract_classes.BaseScaper import BaseScraper

class LelmangaScraper(BaseScraper):
    """Scraper pour le site lelmanga.com"""

    def __init__(self):
        super().__init__("https://www.lelmanga.com")

    def get_manga_details(self, manga_url: str) -> dict:
        html_page, driver = utils.get_page(manga_url,self.do_require_driver())
        if not html_page:
            return {}

        soup = BeautifulSoup(html_page, 'html.parser')
        details = {}

        # Titre
        title_tag = soup.select_one('h1.entry-title')
        details['manga_name'] = title_tag.text.strip() if title_tag else "Inconnu"

        # Auteur (souvent dans une div avec class 'imptdt' ou 'fmed')
        author_tag = soup.find(string=re.compile("Auteur"))
        if author_tag:
            # On essaie de trouver le parent ou le suivant
            parent = author_tag.find_parent('div')
            if parent:
                details['author'] = parent.get_text(strip=True).replace("Auteur", "").strip()
        
        if 'author' not in details:
            details['author'] = "Auteur inconnu"

        # Genres
        genres_tags = soup.select('.mgen a')
        details['manga_genres'] = [tag.text.strip() for tag in genres_tags]

        # Couverture
        cover_tag = soup.select_one('.thumb img')
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
        # Lelmanga liste souvent les chapitres dans une div #chapterlist ou .eplister
        chapter_list = soup.select('#chapterlist li')
        
        for li in chapter_list:
            link_tag = li.select_one('a')
            num_tag = li.get('data-num')
            
            if link_tag and 'href' in link_tag.attrs:
                chap_link = link_tag['href']
                # Si data-num n'est pas présent, on essaie de l'extraire du titre
                if not num_tag:
                    match = re.search(r'Chapitre\s*([\d\.]+)', link_tag.text, re.IGNORECASE)
                    num_tag = match.group(1) if match else "0"
                
                chapters_data.append({
                    "id": utils.normalize_volume(num_tag),
                    "link": chap_link
                })

        details['chapters_data'] = chapters_data
        return details

    def get_chapter_images(self, chapter_url: str) -> list:
        html_page, driver = utils.get_page(chapter_url,self.do_require_driver())
        if not html_page:
            return []

        soup = BeautifulSoup(html_page, 'html.parser')
        images = []

        # Les images sont souvent dans une div readerarea ou content
        # On cherche toutes les images qui semblent être des pages de scan
        img_tags = soup.select('.readerarea img, #readerarea img')
        
        for img in img_tags:
            if 'src' in img.attrs:
                src = img['src'].strip()
                if src:
                    images.append(src)
        
        return images , driver
    
    def get_language(self) -> str:
        """
        Permet de retourner la langues des mangas du site lelmanga.com
        
        :param self: Description
        :return: 'fr' ou 'en' en fonction de la langue du site
        :rtype: str
        """
        return "fr"
    
    def do_require_driver(self) -> bool:
        return False