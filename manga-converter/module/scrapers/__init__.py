from module.scrapers.mangakatana_scraper import MangakatanaScraper
from module.scrapers.lelmanga_scraper import LelmangaScraper
from module.scrapers.sushiscan_scraper import SushiscanScraper

# Dictionnaire pour mapper les domaines aux classes de scraper (le "Strategy" mapping)
# Pour ajouter un site : créer une sous-classe de BaseScraper et l'enregistrer ici.
SCRAPERS = {
    "mangakatana": MangakatanaScraper,
    "lelmanga": LelmangaScraper,
    "sushiscan": SushiscanScraper,
}

def get_scraper_from_domain(domain):
    """Trouve et instancie le scraper approprié pour un domaine donné."""
    for scraper_domain, scraper_class in SCRAPERS.items():
        if domain and scraper_domain in domain:
            return scraper_class()
    return None
