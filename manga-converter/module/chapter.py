import utils

class Chapter:
    """Cette classe est utilisé pour définir un chapitre dans un manga, un chapitre posséde plusieurs pages (image récupérée depuis le site)"""
    def __init__(self,link):
        """Cette fonction est appalée à chaque création d'un chapitre, elle permet de récupéré les informations en fonctions du lien et des sites supporté

        Args:
            link (string): lien du chapitre sur le site de scan
        """
        chapter_html_page = utils.get_page(link).text
        domain_name = utils.get_domain(link)
        
        