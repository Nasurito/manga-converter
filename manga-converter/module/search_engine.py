import utils
from module.scrapers import SCRAPERS

LANGUAGES = {"fr": "VF", "en": "EN"}

class SearchEngine:
    def __init__(self,key_word):
        """ Cette methode est appelée à chaque création d'une recherche de manga,
            Elle permet de récupéré les manga en fonction du nom sur les sites supporté.
            Seuls les titres et les liens sont récupérés : le manga choisi est chargé ensuite.

        Args:
            key_word (string): nom du manga a chercher sur les sites de scans
        """
        # Résultats regroupés par langue : {"fr": [(titre, url), ...], "en": [...]}
        self.results = {language: [] for language in LANGUAGES}

        for scraper_class in SCRAPERS.values():
            scraper = scraper_class()
            try:
                self.results.setdefault(scraper.get_language(), []).extend(scraper.search(key_word))
            finally:
                scraper.close()

        print("Resultat de recherche pour mot clé : ",key_word)
        self._print_results()

    def _print_results(self):
        """ Affiche tout les mangas qui ont été récupérés avec le nom des sites en question """
        for language, mangas in self.results.items():
            print(f"--------------------- {LANGUAGES.get(language, language.upper())} ------------------")
            if mangas:
                for title, url in mangas:
                    print(title ," - ",utils.get_domain(url))
            else:
                print("Aucune correspondance")

    def select_manga(self)->str:
        """
        Cette Methode permet a l'utilisateur de séléctionner un manga parmi les résultats et retourne son url
        """
        languages = [language for language, mangas in self.results.items() if mangas]
        if not languages:
            return None

        choices = self.results[languages[0]]
        if len(languages) > 1:
            print("Quelle langue vous intéresse ?")
            for i, language in enumerate(languages, start=1):
                print(f"{i} : {LANGUAGES.get(language, language.upper())}")
            choices = self.results[languages[self._ask_index(len(languages))]]

        print("Liste des manga:")
        for i, (title, _) in enumerate(choices, start=1):
            print(i," : ",title)
        print("Selectionner le numéro du manga à traiter")

        _, url = choices[self._ask_index(len(choices))]
        return url

    def _ask_index(self, size:int)->int:
        """Demande un numéro entre 1 et size à l'utilisateur et retourne l'index correspondant (base 0)."""
        while True:
            try:
                choice = int(input("> "))
                if 1 <= choice <= size:
                    return choice - 1
                print("Veuillez choisir un numero dans la liste")
            except ValueError:
                print("Veuiller entrer un chiffre dans ceux de la liste")
