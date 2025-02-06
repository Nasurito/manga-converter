import re
import utils
import subprocess
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
            self.manga_name,self.author,self.manga_genres,self.manga_chapters = self.__get_info_from_mangakatana(manga_html_page)
        elif self.domain_name == "lelmanga":
            self.manga_name,self.author,self.manga_genres,self.manga_chapters = self.__get_info_from_lelmanga(manga_html_page)
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

        return manga_name, author,genres, chapters_list
    
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

        return manga_name, author,genres, chapters_list
    
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

        converted_chapter = []
        # Filtrer les chapitres à télécharger et les télécharger directement
        for chapter in filter(lambda c: start <= c.id() <= end, self.manga_chapters):
            self.download_chapter(chapter.id(),format)

            converted_chapter.append(chapter.get_convetion_path(format))

        
        self.convert_to_epub(converted_chapter)

    def convert_to_epub(self, chapter_path):
        """
        Convertit un ou plusieurs chapitres en EPUB.

        Args:
            chapter_path (list): Liste des chemins des fichiers de chapitres.

        Returns:
            bool: True si la conversion a réussi pour au moins un chapitre, False sinon.
        """
        
        fichier_sortie = f"./export/{self.manga_name}/{self.manga_name}.epub"
        
        # Commande Calibre pour convertir les fichiers CBR en un seul EPUB
        command = [
            "ebook-convert"
        ] + chapter_path + [fichier_sortie]  # On ajoute les fichiers et le fichier de sortie

        # Exécution de la commande
        result = subprocess.run(command, capture_output=True)

        # Vérification du succès de la conversion
        if result.returncode != 0:
            print(f"Erreur lors de la conversion : {result.stderr.decode()}")
            return False

        # Commande pour ajouter les métadonnées à l'EPUB
        command = [
            "ebook-meta", 
            fichier_sortie,
            "--title", self.manga_name,
            "--author", self.author,
            #"--cover", image_couverture,
            "--tags", ' , '.join(map(str, self.manga_genres))
        ]
        
        # Exécution de la commande
        result = subprocess.run(command, capture_output=True)
        
        # Vérification du succès de l'ajout des métadonnées
        if result.returncode != 0:
            print(f"Erreur lors de l'ajout des métadonnées : {result.stderr.decode()}")
            return False

        return True
