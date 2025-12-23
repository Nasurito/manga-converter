from abc import ABC, abstractmethod
import undetected_chromedriver as uc

class BaseScraper(ABC):
    """
    Classe de base abstraite pour tous les scrapers de mangas.
    Elle ne peut pas être instanciée directement.
    """

    def __init__(self, base_url):
        self.base_url = base_url

    @abstractmethod
    def get_manga_details(self, manga_url: str) -> dict:
        """
        Récupère les informations d'un manga (titre, auteur, chapitres, etc.).
        Doit être implémenté par les sous-classes.
        """
        pass

    @abstractmethod
    def get_chapter_images(self, chapter_url: str) -> tuple[list,uc.Chrome]:
        """
        Récupère la liste des URLs des images pour un chapitre donné.
        Doit être implémenté par les sous-classes.
        """
        pass

    @abstractmethod
    def get_language(self) -> str:
        """
        Récupère la langue du site.
        Doit être implémenté par les sous-classes.
        """
        pass

    @abstractmethod
    def do_require_driver(self) -> bool:
        """
        Indique si le scraper nécessite un driver pour fonctionner.
        Doit être implémenté par les sous-classes.
        """
        pass

    # Vous pouvez aussi inclure des méthodes concrètes (partagées)
    def clean_url(self, url: str) -> str:
        return url.strip()
