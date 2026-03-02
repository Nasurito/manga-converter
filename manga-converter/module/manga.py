import re
import os
import tempfile
import subprocess
from PIL import Image
from ebooklib import epub

import utils
from module.chapter import Chapter
# Import des scrapers concrets
from module.scrapers.mangakatana_scraper import MangakatanaScraper
from module.scrapers.lelmanga_scraper import LelmangaScraper
from module.scrapers.sushiscan_scraper import SushiscanScraper
# Les autres scrapers seront importés ici au fur et à mesure de leur création

# Dictionnaire pour mapper les domaines aux classes de scraper (le "Strategy" mapping)
SCRAPERS = {
    "mangakatana": MangakatanaScraper,
    "lelmanga": LelmangaScraper,
    "sushiscan": SushiscanScraper,
}

def get_scraper_from_domain(domain):
    """Trouve et instancie le scraper approprié pour un domaine donné."""
    for scraper_domain, scraper_class in SCRAPERS.items():
        if scraper_domain in domain:
            return scraper_class()
    return None

class Manga:
    """Cette classe est utilisé pour définir un manga, un manga possede plusieurs chapitres (objet de la classe chapitre)"""
    def __init__(self,link:str)->None:
        """Cette methode est appalée à chaque création d'un manga, elle permet de récupéré les informations en fonction du lien et des sites supporté
        Args:
            link (string): lien du manga sur le site de scan
        """
        
        self.domain_name = utils.get_domain(link)
        self.link = link
        self.scraper = get_scraper_from_domain(self.domain_name)
        
        if not self.scraper:
            raise Exception(f"Le site {self.domain_name} n'est pas supporté par le programme")
        
        details = self.scraper.get_manga_details(self.link)
        
        if details:
            self.manga_name = details.get('manga_name')
            self.author = details.get('author')
            self.manga_genres = details.get('manga_genres', [])
            self.cover = details.get('cover')
            self.manga_chapters = [
                Chapter(
                    id=chap_data['id'],
                    manga_name=self.manga_name,
                    link=chap_data['link'],
                    scraper=self.scraper  # On passe l'instance du scraper au chapitre
                ) for chap_data in details.get('chapters_data', [])
            ]
        else:
            # Initialisation en cas d'échec du scraping
            self.manga_name, self.author, self.manga_genres, self.manga_chapters, self.cover = None, None, [], [], None

    def review(self):
        """
        Cette fonction permet d'afficher les informations relative a un manga sous cette forme :
        Nom                : lorem ipsum
        Autheur            : Lorem ipsum
        Genres             : lorem, ipsume, dolores
        Nombre de chapitre : xxx
        """
        print("Nom                :",self.manga_name)
        print("Autheur            :",self.author)
        print("Genres             :",self.manga_genres)
        
        higher_id = 0
        for chapter in self.manga_chapters:
            higher_id = chapter.id() if chapter.id() >= higher_id else higher_id
        lower_id = higher_id
        for chapter in self.manga_chapters:
            lower_id = chapter.id() if chapter.id() <= lower_id else lower_id
        print("Nombre de chapitre :", lower_id ,"-", higher_id)
        print("\n")
    
    def download_chapter(self, chapter_number:int,format:str="CBZ")->bool:
        """Télécharge un chapitre spécifique dans le bon format

        Args:
            chapter_number (float): Numéro du chapitre à télécharger.
        """

        chapter_to_download = next((chapter for chapter in self.manga_chapters if chapter.id() == chapter_number), None)

        if chapter_to_download.download(format):
            print(f"Chapitre {chapter_to_download.id()}, téléchargé")
            return True
        
        print(f"Erreur de téléchargement du chapitre {chapter_to_download.id()}")
        return False

    def download_chapters(self, chapter_start:int, chapter_end:int,format:str="CBZ")->None:
        """
        Télécharge une plage de chapitres.

        Args:
            chapter_start (float): Numéro du premier chapitre à télécharger (inclus).
            chapter_end (float): Numéro du dernier chapitre à télécharger (inclus).
        """

        # Si un seul chapitre est demandé, appeler la fonction correspondante
        if chapter_start == chapter_end:
            return self.download_chapter(chapter_start,format)

        # Correction si l'utilisateur a inversé les bornes
        start, end = min(chapter_start, chapter_end), max(chapter_start, chapter_end)

        # Filtrer les chapitres à télécharger et les télécharger directement
        for chapter in filter(lambda c: start <= c.id() <= end, self.manga_chapters):
            self.download_chapter(chapter.id(),format)

    def download_chapter_to_epub(self, start_chapter:int, end_chapter:int, output_path:str=None)->bool:

        """
        Cette fonction permet de télécharger un ou plusieurs chapitres d'un manga et de les convertir en un seul fichier epub

        Args:
            start_chapter (float): Numéro du premier chapitre à télécharger (inclus).
            end_chapter (float, optional): Numéro du dernier chapitre à télécharger (inclus). Si non spécifié, seul le chapitre de start_chapter sera téléchargé. Defaults to None.
        """
        if end_chapter is None:
            end_chapter = start_chapter

        list_of_chapter_ids = [chapter.id() for chapter in self.manga_chapters]
        if start_chapter not in list_of_chapter_ids:
            print(f"❌ Le chapitre {start_chapter} n'existe pas pour ce manga sur le site {self.domain_name}")
            return False
        elif end_chapter not in list_of_chapter_ids:
            print(f"❌ Le chapitre {end_chapter} n'existe pas pour ce manga sur le site {self.domain_name}")
            return False


        book = epub.EpubBook()

        book.set_identifier(self.manga_name)
        book.set_title(self.manga_name)
        book.set_language(self.scraper.get_language())
        book.add_author(self.author)

        cover_path = os.path.join(tempfile.gettempdir(), self.manga_name, "thumb.jpg")
        if os.path.exists(cover_path):
            with open(cover_path, "rb") as f:
                book.set_cover("cover.jpg", f.read())

        spine = ['nav']
        toc = []

        chapters_to_process = [ch for ch in self.manga_chapters if start_chapter <= ch.id() <= end_chapter]
        chapters_to_process = sorted(chapters_to_process, key=lambda c: c.id())

        for chapter in chapters_to_process:
            print(f"📥 Traitement du chapitre {chapter.id()}...")

            if not chapter.pages_path:
                if not chapter.fetch_images():
                    print(f"❌ Échec téléchargement chapitre {chapter.id()}")
                    continue

            first_page_file = None

            for i, img_path in enumerate(chapter.pages_path, 1):
                img_name = os.path.basename(img_path)

                with Image.open(img_path) as img:
                    if img.width > img.height:
                        img = img.rotate(90, expand=True)
                    if img.mode not in ['RGB', 'L']:
                        img = img.convert('RGB')
                    img.save(img_path)

                with open(img_path, "rb") as img_file:
                    img_item = epub.EpubItem(
                        uid=f"img_{chapter.id()}_{i}",
                        file_name=f"images/chapter_{chapter.id()}/{img_name}",
                        media_type="image/jpeg",
                        content=img_file.read()
                    )
                    book.add_item(img_item)

                page = epub.EpubHtml(
                    uid=f"chap_{chapter.id()}_page_{i}",
                    title=None,
                    file_name=f"chapter_{chapter.id()}_page_{i}.xhtml",
                    lang="fr"
                )

                page.set_content(f"""<!DOCTYPE html>
    <html lang="fr" dir="rtl">
    <head>
    <meta charset="UTF-8"/>
    <meta name="viewport" content="width=device-width, height=device-height, initial-scale=1.0"/>
    <style>
        html, body {{
            margin: 0;
            padding: 0;
            height: 100%;
            background-color: black;
        }}
        body {{
            direction: rtl;            /* <<< sens de lecture manga */
            display: flex;
            justify-content: center;
            align-items: center;
        }}
        img {{
            max-width: 100%;
            max-height: 100vh;
            height: auto;
            width: auto;
            display: block;
        }}
    </style>
    </head>
    <body>
    <img src="images/chapter_{chapter.id()}/{img_name}" alt="Page"/>
    </body>
    </html>""")

                book.add_item(page)
                spine.append(page)
                if i == 1:
                    first_page_file = page

            if first_page_file:
                first_page_file.title = " "
                toc.append(epub.Link(first_page_file.file_name, f"Chapitre {chapter.id()}", first_page_file.id))

        book.toc = tuple(toc)
        book.spine = spine
        book.spine_direction = 'rtl'

        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

        output_path = f"./export/{self.manga_name}/{self.manga_name}_{start_chapter}"
        if start_chapter != end_chapter:
            output_path += f"-{end_chapter}"
        output_path += ".epub"

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        epub.write_epub(output_path, book)
        print(f"✅ EPUB créé : {output_path}")
        return True
