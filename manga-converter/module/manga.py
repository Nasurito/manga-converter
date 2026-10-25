import io
import os
from PIL import Image
from ebooklib import epub

import utils
from module.chapter import Chapter
from module.scrapers import get_scraper_from_domain

def prepare_epub_image(img_path:str)->bytes:
    """
    Prépare une page pour l'EPUB et retourne son contenu JPEG : les pages en paysage sont tournées
    pour tenir sur l'écran. Tout se fait en mémoire, l'image du cache n'est pas modifiée
    (elle sert aussi aux exports CBZ/CBR/PDF).
    """
    with Image.open(img_path) as img:
        if img.format == 'JPEG' and img.width <= img.height and img.mode in ['RGB', 'L']:
            # Rien à changer : on garde le fichier d'origine, sans le recompresser
            with open(img_path, "rb") as f:
                return f.read()

        if img.width > img.height:
            img = img.rotate(90, expand=True)
        if img.mode not in ['RGB', 'L']:
            img = img.convert('RGB')
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG')
        return buffer.getvalue()

class Manga:
    """Cette classe est utilisé pour définir un manga, un manga possede plusieurs chapitres (objet de la classe chapitre)"""
    def __init__(self,url:str,output_dir:str="./export")->None:
        """Cette methode est appalée à chaque création d'un manga, elle permet de récupéré les informations en fonction du lien et des sites supporté
        Args:
            link (string): lien du manga sur le site de scan
            output_dir (string): dossier dans lequel les fichiers sont exportés
        """
        
        self.domain = utils.get_domain(url)
        self.url = url
        self.output_dir = output_dir
        self.scraper = get_scraper_from_domain(self.domain)
        
        if not self.scraper:
            raise Exception(f"Le site {self.domain} n'est pas supporté par le programme")
        
        try:
            details = self.scraper.get_manga_details(self.url)
        except Exception:
            self.close()
            raise
        
        if details:
            self.title = details.get('title')
            self.author = details.get('author')
            self.genres = details.get('genres', [])
            self.cover = details.get('cover')
            self.chapters = [
                Chapter(
                    number=chapter_data['number'],
                    manga_title=self.title,
                    url=chapter_data['url'],
                    scraper=self.scraper,  # On passe l'instance du scraper au chapitre
                    output_dir=self.output_dir
                ) for chapter_data in details.get('chapters', [])
            ]
        else:
            # Initialisation en cas d'échec du scraping
            self.title, self.author, self.genres, self.chapters, self.cover = None, None, [], [], None

    def close(self)->None:
        """Libère les ressources du scraper (ex: ferme le navigateur ouvert pour le CAPTCHA)."""
        self.scraper.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.close()

    def print_summary(self):
        """
        Cette fonction permet d'afficher les informations relative a un manga sous cette forme :
        Nom                : lorem ipsum
        Autheur            : Lorem ipsum
        Genres             : lorem, ipsume, dolores
        Nombre de chapitre : xxx
        """
        print("Nom                :",self.title)
        print("Autheur            :",self.author)
        print("Genres             :",self.genres)
        
        numbers = [chapter.number for chapter in self.chapters]
        print("Nombre de chapitre :", min(numbers, default=0) ,"-", max(numbers, default=0))
        print("\n")
    
    def download_chapters(self, start_chapter:float, end_chapter:float,output_format:str="CBZ",use_cache:bool=True)->bool:
        """
        Télécharge une plage de chapitres dans le format demandé.

        Args:
            start_chapter (float): Numéro du premier chapitre à télécharger (inclus).
            end_chapter (float): Numéro du dernier chapitre à télécharger (inclus).

        Returns:
            bool: True si tous les chapitres ont été téléchargés.
        """
        chapters = sorted((c for c in self.chapters if start_chapter <= c.number <= end_chapter), key=lambda c: c.number)
        if not chapters:
            print(f"❌ Aucun chapitre entre {start_chapter} et {end_chapter} pour ce manga sur le site {self.domain}")
            return False

        success = True
        for chapter in chapters:
            if chapter.download(output_format, use_cache):
                print(f"Chapitre {chapter.number}, téléchargé")
            else:
                print(f"Erreur de téléchargement du chapitre {chapter.number}")
                success = False
        return success

    def download(self, start_chapter:float, end_chapter:float, output_format:str="EPUB", use_cache:bool=True)->bool:
        """Télécharge une plage de chapitres au format demandé (EPUB, PDF, CBZ ou CBR)."""
        if output_format == "EPUB":
            return self.download_epub(start_chapter, end_chapter, use_cache)
        return self.download_chapters(start_chapter, end_chapter, output_format, use_cache)

    def download_epub(self, start_chapter:float, end_chapter:float=None, use_cache:bool=True)->bool:

        """
        Cette fonction permet de télécharger un ou plusieurs chapitres d'un manga et de les convertir en un seul fichier epub

        Args:
            start_chapter (float): Numéro du premier chapitre à télécharger (inclus).
            end_chapter (float, optional): Numéro du dernier chapitre à télécharger (inclus). Si non spécifié, seul le chapitre de start_chapter sera téléchargé. Defaults to None.
        """
        if end_chapter is None:
            end_chapter = start_chapter

        chapter_numbers = [chapter.number for chapter in self.chapters]
        if start_chapter not in chapter_numbers:
            print(f"❌ Le chapitre {start_chapter} n'existe pas pour ce manga sur le site {self.domain}")
            return False
        elif end_chapter not in chapter_numbers:
            print(f"❌ Le chapitre {end_chapter} n'existe pas pour ce manga sur le site {self.domain}")
            return False


        book = epub.EpubBook()

        book.set_identifier(self.title)
        book.set_title(self.title)
        language = self.scraper.get_language()
        book.set_language(language)
        book.add_author(self.author)

        if self.cover and os.path.exists(self.cover):
            with open(self.cover, "rb") as f:
                book.set_cover("cover.jpg", f.read())

        spine = ['nav']
        toc = []

        chapters_to_process = [ch for ch in self.chapters if start_chapter <= ch.number <= end_chapter]
        chapters_to_process = sorted(chapters_to_process, key=lambda c: c.number)

        for chapter in chapters_to_process:
            print(f"📥 Traitement du chapitre {chapter.number}...")

            if not chapter.fetch_images(use_cache):
                print(f"❌ Échec téléchargement chapitre {chapter.number}")
                continue

            first_page_file = None

            for i, img_path in enumerate(chapter.page_paths, 1):
                img_name = os.path.basename(img_path)

                img_item = epub.EpubItem(
                    uid=f"img_{chapter.number}_{i}",
                    file_name=f"images/chapter_{chapter.number}/{img_name}",
                    media_type="image/jpeg",
                    content=prepare_epub_image(img_path)
                )
                book.add_item(img_item)

                page = epub.EpubHtml(
                    uid=f"chap_{chapter.number}_page_{i}",
                    title=None,
                    file_name=f"chapter_{chapter.number}_page_{i}.xhtml",
                    lang=language
                )

                page.set_content(f"""<!DOCTYPE html>
    <html lang="{language}" dir="rtl">
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
    <img src="images/chapter_{chapter.number}/{img_name}" alt="Page"/>
    </body>
    </html>""")

                book.add_item(page)
                spine.append(page)
                if i == 1:
                    first_page_file = page

            if first_page_file:
                first_page_file.title = " "
                toc.append(epub.Link(first_page_file.file_name, f"Chapitre {chapter.number}", first_page_file.id))

        book.toc = tuple(toc)
        book.spine = spine
        book.spine_direction = 'rtl'

        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

        folder_name = utils.safe_filename(self.title)
        output_path = os.path.join(self.output_dir, folder_name, f"{folder_name}_{start_chapter}")
        if start_chapter != end_chapter:
            output_path += f"-{end_chapter}"
        output_path += ".epub"

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        epub.write_epub(output_path, book)
        print(f"✅ EPUB créé : {output_path}")
        return True
