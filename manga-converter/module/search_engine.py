from module.manga import Manga
from module.scrapers import SCRAPERS

LANGUAGES = {"fr": "VF", "en": "EN"}

class Search_engine:
    def __init__(self,key_word):
        """ Cette methode est appelée à chaque création d'une recherche de manga,
            Elle permet de récupéré les manga en fonction du nom sur les sites supporté

        Args:
            key_word (string): nom du manga a chercher sur les sites de scans
        """
        # Résultats regroupés par langue : {"fr": [Manga, ...], "en": [...]}
        self.results = {language: [] for language in LANGUAGES}
        self.selected_manga = None

        for scraper_class in SCRAPERS.values():
            scraper = scraper_class()
            for link in scraper.search(key_word):
                try:
                    manga = Manga(link)
                except Exception as e:
                    print(f"⚠️ Impossible de charger {link} : {e}")
                    continue
                if manga.manga_name is not None:
                    self.results.setdefault(scraper.get_language(), []).append(manga)

        print("Resultat de recherche pour mot clé : ",key_word)
        self.__listing()

    def __listing(self):
        """ Affiche tout les mangas qui ont été récupérés avec le nom des sites en question """
        for language, mangas in self.results.items():
            print(f"--------------------- {LANGUAGES.get(language, language.upper())} ------------------")
            if mangas:
                for manga in mangas:
                    print(manga.manga_name ," - ",manga.domain_name)
            else:
                print("Aucune correspondance")

    def Select_Manga(self)->Manga:
        """
        Cette Methode permet a l'utilisateur de séléctionner un manga parmi les résultats et le retourne
        """
        languages = [language for language, mangas in self.results.items() if mangas]
        if not languages:
            return None

        list_to_use = self.results[languages[0]]
        if len(languages) > 1:
            print("Quelle langue vous intéresse ?")
            for i, language in enumerate(languages, start=1):
                print(f"{i} : {LANGUAGES.get(language, language.upper())}")
            list_to_use = self.results[languages[self.__ask_index(len(languages))]]

        print("Liste des manga:")
        for i, manga in enumerate(list_to_use, start=1):
            print(i," : ",manga.manga_name)
        print("Selectionner le numéro du manga à traiter")

        self.selected_manga = list_to_use[self.__ask_index(len(list_to_use))]
        return self.selected_manga

    def __ask_index(self, size:int)->int:
        """Demande un numéro entre 1 et size à l'utilisateur et retourne l'index correspondant (base 0)."""
        while True:
            try:
                choice = int(input("> "))
                if 1 <= choice <= size:
                    return choice - 1
                print("Veuillez choisir un numero dans la liste")
            except ValueError:
                print("Veuiller entrer un chiffre dans ceux de la liste")
