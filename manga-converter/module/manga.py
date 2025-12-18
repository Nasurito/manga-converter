import re
import os
import tempfile
import subprocess
from PIL import Image
from ebooklib import epub

import utils
from module.chapter import Chapter

class Manga:
    """Cette classe est utilisé pour définir un manga, un manga possede plusieurs chapitres (objet de la classe chapitre)"""
    def __init__(self,link):
        """Cette methode est appalée à chaque création d'un manga, elle permet de récupéré les informations en fonction du lien et des sites supporté

        Args:
            link (string): lien du manga sur le site de scan
        """
        
        self.domain_name = utils.get_domain(link)
        manga_html_page,self.driver = utils.get_page(link)
        
        if self.domain_name == "mangakatana":
            manga= self.__get_info_from_mangakatana(manga_html_page)
            if manga!=None:
                self.manga_name,self.author,self.manga_genres,self.manga_chapters,self.cover = manga
            else:
                self.manga_name,self.author,self.manga_genres,self.manga_chapters,self.cover=None,None,None,None,None
        elif self.domain_name == "lelmanga":
            manga=self.__get_info_from_lelmanga(manga_html_page)
            if manga!=None:
                self.manga_name,self.author,self.manga_genres,self.manga_chapters,self.cover = manga
            else:
                self.manga_name,self.author,self.manga_genres,self.manga_chapters,self.cover=None,None,None,None,None
        elif self.domain_name == "sushiscan":
            manga=self.__get_info_from_sushiscan(manga_html_page)
            if manga!=None:
                self.manga_name,self.author,self.manga_genres,self.manga_chapters,self.cover = manga
            else:
                self.manga_name,self.author,self.manga_genres,self.manga_chapters,self.cover=None,None,None,None,None
        else:
            raise Exception("Le site utilisé n'est pas supporté par le programme")
    
    def __get_info_from_mangakatana(self,html_page):
        """Cette methode privée récupére les informations relative a un manga si le lien fournis viens du site mangakatana

        Args:
            html_page (html): correspond à la page html récupéré avec le lien fournis a la création du manga

        Returns:
            manga_name (string) : Correspond au nom du manga
            author (string) : Nom de l'auteur du manga
            Genres (string[]) : Tout les genres du manga
            chapters_list (Chapter[]) : Tableau d'objet chapter
        """
        manga_name=""
        author=""
        genres=[]
        chapters_list=[]

        manga_name = re.search(r'<h1[^>]*class=["\'][^"\']*heading[^"\']*["\'][^>]*>(.*?)<\/h1>', html_page, re.IGNORECASE).group(1)
        author_search = re.search(r'<a class=["\']author["\'][^>]*>(.*?)<\/a>',html_page)
        author = "autheur inconnu " if author_search == None else author_search.group(1)
        
        match_div =  re.search(r'<div class=["\']genres["\'][^>]*>(.*?)<\/div>', html_page, re.DOTALL)
        genres_html = match_div.group(1)
        # Récupére tout les genres
        genres = re.findall(r'<a[^>]*>(.*?)<\/a>', genres_html)
        

        regex = r'<div class="cover"[^>]*>.*?<img[^>]*\s+src=["\']([^"\']+)["\']'
        match = re.search(regex, html_page)
        if match:
            # Créer un dossier racine pour le manga dans le répertoire temporaire (en utilisant le nom du manga)
            root_dir = tempfile.gettempdir()+f"/{manga_name}"
            os.makedirs(root_dir, exist_ok=True)  # Créer le dossier s'il n'existe pas
            utils.download_image(match.group(1),root_dir+"/thumb.jpg")
                
        # Nettoyer les espaces et tabulations inutiles dans le HTML
        clean_html = re.sub(r'\s+', ' ', html_page)
        # Extraire la première div avec la classe "chapters" qui est suivis de l'initialisation du tableau
        pattern_div = r'<div class="chapters">.*?<table class="uk-table uk-table-striped"[^>]*>(.*?)</table>.*?</div>'
        match_div = re.search(pattern_div, clean_html, re.DOTALL)
        # Récupérer le contenu de la table
        chapters_html = match_div.group(1)
        # Extraire tous les liens href à l'intérieur de la table
        pattern_links = r'<a[^>]*href=["\'](https?://[^"\'<>]+)["\'][^>]*>\s*Chapter\s*(\d+)'
  
        chapters_link_found = re.findall(pattern_links, chapters_html)
        
        for link, data_num  in chapters_link_found:
             chapters_list.append(Chapter(utils.normalize_volume(data_num),manga_name,link))

        return manga_name, author,genres, chapters_list,root_dir+"/thumb.jpg"
    
    def __get_info_from_lelmanga(self,html_page):
        """Cette methode privée récupére les informations d'un manga depuis le site www.lelmanga.com
        Args:
            html_page (html): correspond a la page html récupéré avec le lien fournis a la création du manga
        Returns:
            manga_name (string) : Correspond au nom du manga
            author (string) : Nom de l'auteur du manga
            Genres (string[]) : Tout les genres du manga
            chapters_list (Chapter[]) : Tableau d'objet chapter
        """
        manga_name=""
        author=""
        genres=[]
        chapters_list=[]
        
        try:
            # Utiliser re.search pour récupérer uniquement le premier (ou seul) auteur
            author = re.search(r'<div class=["\']imptdt["\'][^>]*>\s*Auteur\s*<i>(.*?)<\/i>', html_page).group(1)
        except:
            author = "Autheur inconnu"

        # Utiliser re.search pour récupéré le nom du manga
        match = re.search(r'<h1[^>]*class=["\']entry-title["\'][^>]*>(.*?)<\/h1>', html_page, re.IGNORECASE)
        if match:
            manga_name = match.group(1)
        else:
            return None 
        # Regex pour extraire le contenu de la div avec la classe "wd-full"
        pattern_div = r'<div class=["\']wd-full["\'][^>]*>\s*<span class=["\']mgen["\'][^>]*>(.*?)<\/span><\/div>'
        match_div = re.search(pattern_div, html_page,re.DOTALL)
        # Si la div est trouvée, extraire les genres dans les balises <a>
        if match_div:
            genres_html = match_div.group(1)  # Contenu de <span class="mgen">
            pattern_genres = r'<a[^>]*href=["\'][^"\'<>]*["\'][^>]*>(.*?)<\/a>'
            genres = re.findall(pattern_genres, genres_html)
        
        # Nettoyer les espaces et tabulations inutiles dans le HTML
        clean_html = re.sub(r'\s+', ' ', html_page)
        
        regex = r'<div class="thumb"[^>]*>.*?<img[^>]*\s+src=["\']([^"\']+)["\']'
        match = re.search(regex, clean_html)
        if match:
            # Créer un dossier racine pour le manga dans le répertoire temporaire (en utilisant le nom du manga)
            root_dir = tempfile.gettempdir()+f"/{manga_name}"
            os.makedirs(root_dir, exist_ok=True)  # Créer le dossier s'il n'existe pas
    
            utils.download_image(match.group(1),root_dir+"/thumb.jpg")
        
        
        # Regex pour extraire le contenu de la div "eplister" et récupérer les liens dans les balises <a>
        pattern_div = r'<div class=["\']eplister["\'][^>]*><ul[^>]*>(.*?)<\/ul><\/div>'
        match_div = re.search(pattern_div, clean_html, re.DOTALL)
        # Si la div est trouvée, extraire les liens des chapitres
        if match_div:
            chapters_html = match_div.group(1)  # Contenu de <ul> avec les chapitres
            # Regex pour extraire tous les liens dans les balises <a>, sans se baser sur le nom du manga
            pattern_links = r'<li data-num=["\']([\d\.]+)["\'].*?<a href=["\'](https://www\.lelmanga\.com/[^"\']+)["\']'

            chapters_link_found = re.findall(pattern_links, chapters_html)
        
        for data_num, link in chapters_link_found:
             chapters_list.append(Chapter(utils.normalize_volume(data_num),manga_name,link))

        return manga_name, author,genres, chapters_list,root_dir+"/thumb.jpg"
    
    def __get_info_from_sushiscan(self,html_page):
        """Cette methode privée récupére les informations d'un manga depuis le site www.lelmanga.com
        Args:
            html_page (html): correspond a la page html récupéré avec le lien fournis a la création du manga
        Returns:
            manga_name (string) : Correspond au nom du manga
            author (string) : Nom de l'auteur du manga
            Genres (string[]) : Tout les genres du manga
            chapters_list (Chapter[]) : Tableau d'objet chapter
        """
        manga_name=""
        author=""
        genres=[]
        chapters_list=[]
        
        try:
            # Utiliser re.search pour récupérer uniquement le premier (ou seul) auteur
            author = re.search(r'<tr><td>Auteur</td><td>([^<]+)</td></tr>', html_page).group(1)
        except:
            author = "Autheur inconnu"

        # Utiliser re.search pour récupéré le nom du manga
        match = re.search(r'<h1[^>]*class=["\']entry-title["\'][^>]*>(.*?)<\/h1>', html_page, re.IGNORECASE)
        if match:
            manga_name = match.group(1)
        else:
            return None 
        # Regex pour extraire le contenu de la div avec la classe "wd-full"
        regex = r'<div class="seriestugenre">.*?</div>'
        block = re.search(regex, html_page, re.S).group()

        genres = re.findall(r'>([^<]+)</a>', block)

        # Nettoyer les espaces et tabulations inutiles dans le HTML
        clean_html = re.sub(r'\s+', ' ', html_page)
        
        regex = r'<div class="thumb"[^>]*>.*?<img[^>]*\s+src=["\']([^"\']+)["\']'
        match = re.search(regex, clean_html)
        if match:
            # Créer un dossier racine pour le manga dans le répertoire temporaire (en utilisant le nom du manga)
            root_dir = tempfile.gettempdir()+f"/{manga_name}"
            os.makedirs(root_dir, exist_ok=True)  # Créer le dossier s'il n'existe pas
    
            utils.download_image_with_driver_single(self.driver,match.group(1),root_dir+"/thumb.jpg")
        
        
        matches = re.findall(
            r'data-num="([^"]+)".*?<a\s+href="([^"]+)"',
            clean_html,
            re.S
        )
        matches.reverse()
    
        for data_num, link in matches:
             chapters_list.append(Chapter(utils.normalize_volume(data_num),manga_name,link))

        return manga_name, author,genres, chapters_list,root_dir+"/thumb.jpg"
    
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
        
        print("Nombre de chapitre :",higher_id)
        print("\n")
    
    def download_chapter(self, chapter_number,format="CBZ"):
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

    def download_chapters(self, chapter_start, chapter_end,format="CBZ"):
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

    def download_chapter_to_epub(self, start_chapter, end_chapter=None):

        """
        Cette fonction permet de télécharger un ou plusieurs chapitres d'un manga et de les convertir en un seul fichier epub

        Args:
            start_chapter (float): Numéro du premier chapitre à télécharger (inclus).
            end_chapter (float, optional): Numéro du dernier chapitre à télécharger (inclus). Si non spécifié, seul le chapitre de start_chapter sera téléchargé. Defaults to None.
        """
        if end_chapter is None:
            end_chapter = start_chapter


        book = epub.EpubBook()

        book.set_identifier(self.manga_name)
        book.set_title(self.manga_name)
        book.set_language("fr" if self.domain_name == "lelmanga" else "en")
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

        output_path = f"./export/{self.manga_name}/{self.manga_name}_{start_chapter}-{end_chapter}.epub"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        epub.write_epub(output_path, book)
        print(f"✅ EPUB créé : {output_path}")
        return True
