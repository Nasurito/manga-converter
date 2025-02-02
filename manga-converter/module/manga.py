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
            self.manga_name,self.author,self.manga_genres,self.manga_chapter =self.get_info_from_lelmanga(manga_html_page)

        print(self.manga_name,self.author,self.manga_genres,self.manga_chapter)
    
    def get_info_from_mangakatana(self,html_page):
        """Cette fonction récupére les informations relative a un manga si le lien fournis viens du site mangakatana

        Args:
            html_page (html): _description_

        Returns:
            _type_: _description_
        """
        manga_name=""
        author=""
        genres=""
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
        """
        
        manga_name = re.search('<h1[^>]*class=["\']entry-title["\'][^>]*>(.*?)<\/h1>', html_page, re.IGNORECASE)
        author = ""
        genres = []
            
