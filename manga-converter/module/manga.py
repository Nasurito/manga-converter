import re
import os
import tempfile
import subprocess
import utils
from module.chapter import Chapter

class Manga:
    """Cette classe est utilisé pour définir un manga, un manga possede plusieurs chapitres (objet de la classe chapitre)"""
    def __init__(self,link):
        """Cette methode est appalée à chaque création d'un manga, elle permet de récupéré les informations en fonction du lien et des sites supporté

        Args:
            link (string): lien du manga sur le site de scan
        """
        
        manga_html_page = utils.get_page(link).text
        
        self.domain_name = utils.get_domain(link)
        
        if self.domain_name == "mangakatana":
            self.manga_name,self.author,self.manga_genres,self.manga_chapters,self.cover = self.__get_info_from_mangakatana(manga_html_page)
        elif self.domain_name == "lelmanga":
            self.manga_name,self.author,self.manga_genres,self.manga_chapters,self.cover = self.__get_info_from_lelmanga(manga_html_page)
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

        manga_name = re.search('<h1[^>]*class=["\'][^"\']*heading[^"\']*["\'][^>]*>(.*?)<\/h1>', html_page, re.IGNORECASE).group(1)
        author_search = re.search('<a class=["\']author["\'][^>]*>(.*?)<\/a>',html_page)
        author = author_search.group(1)
        
        match_div =  re.search('<div class=["\']genres["\'][^>]*>(.*?)<\/div>', html_page, re.DOTALL)
        genres_html = match_div.group(1)
        # Récupére tout les genres
        genres = re.findall('<a[^>]*>(.*?)<\/a>', genres_html)
        

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
             chapters_list.append(Chapter(data_num,manga_name,link))

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
        
        # Utiliser re.search pour récupérer uniquement le premier (ou seul) auteur
        author = re.search('<div class=["\']imptdt["\'][^>]*>\s*Auteur\s*<i>(.*?)<\/i>', html_page).group(1)
        # Utiliser re.search pour récupéré le nom du manga
        manga_name = re.search('<h1[^>]*class=["\']entry-title["\'][^>]*>(.*?)<\/h1>', html_page, re.IGNORECASE).group(1)

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
             chapters_list.append(Chapter(data_num,manga_name,link))

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
        """Télécharge une plage de chapitres.

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

    def convert_to_epub(self):
        """
        Convertit plusieurs chapitres en un seul fichier EPUB.

        Returns:
            bool: True si la conversion a réussi, False sinon.
        """

        epub_files_folder = f"./export/{self.manga_name}/epub"

        if not os.path.exists(epub_files_folder):
            print(f"Erreur : Le dossier {epub_files_folder} n'existe pas.")
            return False

        fichiers_epub = [os.path.join(epub_files_folder, f) for f in os.listdir(epub_files_folder) if f.endswith(".epub")]
        
        if not fichiers_epub:
            raise FileNotFoundError(
                "Aucun chapitre trouvé en format EPUB. Vous devez d'abord convertir les fichiers CBR/CBZ en EPUB."
            )

        # Trier les fichiers par numéro de chapitre
        fichiers_epub = sorted(fichiers_epub, key=lambda x: utils.extraire_numero(x) if utils.extraire_numero(x) is not None else x)

        # Fichier EPUB final
        fichier_sortie = f"./export/{self.manga_name}/{self.manga_name}.epub"

        # Fusionner les fichiers EPUB avec calibre-debug
        command = [
            "calibre-debug",
            "--run-plugin", "EpubMerge",  # Assure-toi que le plugin "EpubMerge" est installé
            "--",
            "-o", fichier_sortie  # Ce sera le fichier de sortie, où les chapitres seront combinés
        ] + fichiers_epub  # Ajouter les fichiers EPUB à fusionner

        print(f"Fusion des fichiers EPUB en : {fichier_sortie}")
        result = subprocess.run(command, capture_output=True)

        if result.returncode != 0:
            print(f"Erreur lors de la fusion des fichiers EPUB : {result.stderr.decode()}")
            return False

        # Vérifier si le fichier de sortie existe
        if not os.path.exists(fichier_sortie):
            print("Erreur : Le fichier EPUB final n'a pas été généré.")
            return False

        # Ajouter les métadonnées
        command_meta = [
            "ebook-meta", 
            fichier_sortie,
            "--title", self.manga_name,
            "--language", "en" if self.domain_name=="mangakatana" else "fr",
            "--authors", self.author,
            "--tags", ', '.join(map(str, self.manga_genres))
        ]

        # Vérifier et ajouter la couverture si elle existe
        cover_path = os.path.join(tempfile.gettempdir(), self.manga_name, "thumb.jpg")
        if os.path.exists(cover_path):
            command_meta += ["--cover", cover_path]

        print("Ajout des métadonnées à l'EPUB...")
        result = subprocess.run(command_meta, capture_output=True)

        if result.returncode != 0:
            print(f"Erreur lors de l'ajout des métadonnées : {result.stderr.decode()}")
            return False

        print(f"Conversion réussie : {fichier_sortie}")
        return True

