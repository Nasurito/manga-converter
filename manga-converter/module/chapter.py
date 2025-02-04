import utils

class Chapter:
    """Cette classe est utilisé pour définir un chapitre dans un manga, un chapitre posséde plusieurs pages (image récupérée depuis le site)"""
    def __init__(self,id,link):
        """
        Cette fonction est appalée à chaque création d'un chapitre, elle permet de récupéré les informations en fonctions du lien et des sites supporté

        Args:
            link (string): lien du chapitre sur le site de scan
        """
        self.id_chapter = id
        self.chapter_html_page = None
        self.chapter_html_link = link
        self.domain_name = utils.get_domain(link)
        self.pages = []
    
    def id(self):
        return float(self.id_chapter)    
    
    def get_scanned_pages(self):
        self.chapter_html_page = utils.get_page(self.chapter_html_link)