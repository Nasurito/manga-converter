import re
import utils
from module.chapter import Chapter

class Manga:
    """Cette classe est utilisé pour définir un manga, un manga possede plusieurs chapitres (objet de la classe chapitre)"""
    def __init__(self,link):
        """Cette fonction est appalée à chaque création d'un manga, elle permet de récupéré les informations en fonctions du lien et des sites supporté

        Args:
            link (string): lien du manga sur le site de scan
        """
        
        manga_html_page = utils.get_page(link).text
        
        domain_name = utils.get_domain(link)
        
        if domain_name == "mangakatana":
            self.manga_name,self.author,self.manga_genres,self.manga_chapter = self.get_info_from_mangakatana(manga_html_page)
        if domain_name == "lelmanga":
            self.manga_name,self.author,self.manga_genres,self.manga_chapter = self.get_info_from_lelmanga(manga_html_page)
        else:
            raise Exception("Le site utilisé n'est pas supporté par le programme")

        print(self.manga_name,self.author,self.manga_genres,self.manga_chapter)
    
    def get_info_from_mangakatana(self,html_page):
        """Cette fonction récupére les informations relative a un manga si le lien fournis viens du site mangakatana

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
        # Extraire la première div avec la classe "chapters" qui est suivis de l'initialisation du tableau
        pattern_div = r'<div class="chapters">.*?<table class="uk-table uk-table-striped"[^>]*>(.*?)</table>.*?</div>'
        match_div = re.search(pattern_div, html_page, re.DOTALL)
        # Récupérer le contenu de la table
        chapters_html = match_div.group(1)
        # Extraire tous les liens href à l'intérieur de la table
        pattern_links = r'<a[^>]*href=["\'](https?://[^"\'<>]+)["\'][^>]*>'
        
        chapters_link_found = re.findall(pattern_links, chapters_html)
        
        for chapter in chapters_link_found:
             chapters_list.append(Chapter(chapter))

        return manga_name, author,genres, chapters_list
    
    def get_info_from_lelmanga(self,html_page):
        """Cette fonction récupére les informations d'un manga depuis le site www.lelmanga.com
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
            chapter_html = match_div.group(1)  # Contenu de <ul> avec les chapitres
            # Regex pour extraire tous les liens dans les balises <a>, sans se baser sur le nom du manga
            pattern_links = r'href=["\'](https://www.lelmanga.com/[^"\']+)["\']'
            chapter_links = re.findall(pattern_links, chapter_html)
        
        for chapters in chapter_links:
            chapters_list.append(Chapter(chapters))

        return manga_name, author,genres, chapters_list
        
            
