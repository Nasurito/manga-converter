import re
import requests
import utils
from module.manga import Manga


class Search_engine:
    def __init__(self,key_word):
        """ Cette methode est appelée à chaque création d'une recherche de manga,
            Elle permet de récupéré les manga en fonction du nom sur les sites supporté

        Args:
            key_word (string): nom du manga a chercher sur les sites de scans
        """
        self.list_fr,self.list_en=[],[]
        self.selected_manga = None

        # Recherche avec lelmangavf :
        link = "https://www.lelmanga.com/?s="+key_word.replace(" ", "+")
        lelmanga_search = utils.get_page(link).text
        matches = re.findall(r'<div class="bs">.*?<a href="([^"]+)"', lelmanga_search, re.DOTALL)

        for match in matches:
            manga_to_add=Manga(match)
            if manga_to_add.manga_name!= None:
                self.list_fr.append(manga_to_add)

        matches=[]
        match=None

        # Recherche avec mangakatana
        # Requête
        link = "https://mangakatana.com/?search=" + key_word.replace(" ", "+") + "&search_by=book_name"

        try:
            html = utils.get_page(link).text
            # Extraire le bloc complet de #book_list jusqu'à la pagination (prochaine balise connue après)
            container_match = re.search(
                r'<div id="book_list">(.*?)<ul class="uk-pagination">', 
                html, 
                re.DOTALL
            )

            if container_match:
                book_list_html = container_match.group(1)
                # Extraire les liens des titres de manga
                pattern = r'<h3 class="title">\s*<a href="(https://mangakatana\.com/manga/[^"]+)"'
                matches = re.findall(pattern, book_list_html)
            else:
                print("❌ Bloc #book_list introuvable")

            for match in matches:
                self.list_en.append(Manga(match))
        except:
            self.list_en = None
            return None


        print("Resultat de recherche pour mot clé : ",key_word)
        self.__listing()
    def __listing(self):
        """ Cette methode est appelée à chaque création d'une recherche de manga,
            Elle permet d'afficher tout les mangas qui ont été récupéré
            Et les afficher avec le nom des sites en questions 

        Args:
            key_word (string): nom du manga a chercher sur les sites de scans
        """
        print("--------------------- VF ------------------")
        if self.list_fr != []:
            for manga in self.list_fr:
                print(manga.manga_name ," - ",manga.domain_name)
        else: 
            print("Aucune correspondance")
        print("--------------------- EN ------------------")
        if self.list_en != []:
            for manga in self.list_en:
                print(manga.manga_name ," - ",manga.domain_name)
        else: 
            print("Aucune correspondance")
    def Select_Manga(self):
        """
        Cette Methode permet a l'utilisateur de séléctionner un chapitre et de faire ce qu'il veux 
        """
        while True:
            try:
                search_input = int(input("Quelle langue vous intéresse ?\n1 : VF\n2 : EN\n> "))
                if search_input in [1, 2]:
                    break
                else:
                    print(f"{search_input} n'est pas dans la liste des choix.")
            except ValueError:
                print("Veuillez entrer un chiffre (1 ou 2).")

        if search_input == 1:
            list_to_use = self.list_fr
        else :
            list_to_use = self.list_en

        print("Liste des manga:")
        for i, manga in enumerate(list_to_use, start=1):
            print(i," : ",manga.manga_name)
        
        while True:
            try:
                id = int(input("Selectionner le numéro du manga à traiter\n> "))
                if id-1 <= len(list_to_use):
                    break
                else:
                    print("Veuillez choisir un numero dans la liste")
            except ValueError:  
                print("Veuiller entrer un chiffre dans ceux de la liste")

        self.selected_manga = list_to_use[id-1] 
    
    def Action_Manga(self):
        """
        Cette fonction est utilisée pour que l'utilisateur puisse intéragir avec le manga qu'il aura choisi
        """
        if self.selected_manga == None:
            self.Select_Manga()
        
        