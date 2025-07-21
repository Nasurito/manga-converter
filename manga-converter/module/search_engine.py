import re
import requests
import utils
from module.manga import Manga


class Search_engine:
    def __init__(self,key_word):
        """ Cette methode est appalée à chaque création d'une recherche de manga,
            Elle permet de récupéré les manga en fonction du nom sur les sites supporté

        Args:
            name (string): nom du manga a chercher sur les sites de scans
        """
        self.list_fr,self.list_en=[],[]

        
        # Recherche avec lelmangavf :
        link = "https://www.lelmanga.com/?s="+key_word.replace(" ", "+")
        lelmanga_search = utils.get_page(link).text
        matches = re.findall(r'<div class="bs">.*?<a href="([^"]+)"', lelmanga_search, re.DOTALL)

        for match in matches:
            self.list_fr.append(Manga(match))

        # Recherche avec mangakatana
        # Requête
        link = "https://mangakatana.com/?search=" + key_word.replace(" ", "+") + "&search_by=book_name"
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


        print("Resultat de recherche pour mot clé : ",key_word)
        self.__listing()

    def __listing(self):
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
