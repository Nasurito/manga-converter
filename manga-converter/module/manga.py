import utils
import chapter

class Manga:
    """Cette classe est utilisé pour définir un manga, un manga possede plusieurs chapitres (objet de la classe chapitre)"""
    def __init__(self,link):
        """Cette fonction est appalée à chaque création d'un manga, elle permet de récupéré les informations en fonctions du lien et des sites supporté

        Args:
            link (string): lien du manga sur le site de scan
        """
        self.manga_name,self.manga_chapter = self.get_info(link)
    
    def get_info(self,link):
        """
        Cette fonction récupére les informations relative à un manga avec les différentes informations intéréssante tel que le nom du manga et la liste des chapitres
        Args:
            link (_type_): lien du fichier
        """
        site = utils.get_domain(link)
        page_fetched = utils.get_page(link)
        
        if site == 'mangakatana':
            """Si le site est mangakatana, on va chercher les informations à cette endroit"""
       
        elif site == 'lelmanga' :
            """Si le site est lelmanga, on va chercher les informations à cette endroit"""
        else:
            print("Veuillez choisir un site supporté")
        