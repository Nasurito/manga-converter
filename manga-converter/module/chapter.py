import os
import tempfile
import utils
from module.abstract_classes.base_scraper import BaseScraper

# Fonction de conversion associée à chaque format de sortie (l'extension du fichier est le format en minuscule)
CONVERTERS = {
    "PDF": utils.images_to_pdf,
    "CBZ": utils.images_to_cbz,
    "CBR": utils.images_to_cbr,
}

class Chapter:
    """Cette classe est utilisé pour définir un chapitre dans un manga, un chapitre posséde plusieurs pages (image récupérée depuis le site)"""
    def __init__(self,id:int,manga_name:str,link:str, scraper: BaseScraper, output_dir:str="./export")->None:
        """
        Cette fonction est appalée à chaque création d'un chapitre, elle permet de récupéré les informations en fonctions du lien et des sites supporté

        Args:
            link (string): lien du chapitre sur le site de scan
            output_dir (string): dossier dans lequel les chapitres convertis sont exportés
        """
        self.id_chapter = id
        self.manga_name = manga_name
        self.folder_name = utils.safe_filename(manga_name)  # nom utilisable dans les chemins
        self.output_dir = output_dir
        self.chapter_html_link = link
        self.scraper = scraper
        self.pages_link = []
        self.pages_path = []

    def id(self):
        return int(self.id_chapter) if float(self.id_chapter).is_integer() else float(self.id_chapter)

    def export_path(self, format:str)->str:
        """Retourne le chemin du fichier exporté pour un format donné (ex: ./export/<manga>/cbz/chapter_1.cbz)."""
        extension = format.lower()
        return os.path.join(self.output_dir, self.folder_name, extension, f"chapter_{self.id()}.{extension}")

    def fetch_images(self, use_cache:bool=True)->bool:
        """
        Récupère les images du chapitre (avec plusieurs tentatives).

        Args:
            use_cache (bool): réutiliser les images déjà téléchargées dans le dossier temporaire si elles sont complètes
        """
        if self.pages_path:  # Déjà fait
            return True

        max_retries = 5
        for attempt in range(1, max_retries + 1):
            if self._try_fetch_images(use_cache):
                return True
            if attempt < max_retries:
                print(f"⚠️ Problème lors du téléchargement du chapitre {self.id()}, tentative {attempt}/{max_retries}. Nouvel essai...")
                # Reset state for a clean retry
                self.pages_link = []
                self.pages_path = []

        print(f"❌ Échec du téléchargement du chapitre {self.id()} après {max_retries} tentatives.")
        return False

    def _try_fetch_images(self, use_cache:bool)->bool:
        driver = None
        try:
            # Extraire les liens si pas déjà fait
            if not self.pages_link:
                self.pages_link,driver = self.scraper.get_chapter_images(self.chapter_html_link)

            if not self.pages_link:
                print(f"❌ Pas de pages trouvées pour chapitre {self.id()}")
                return False

            # Vérification spéciale : si une seule image est trouvée, c'est probablement une erreur
            if len(self.pages_link) == 1:
                print(f"⚠️ Une seule image a été trouvée pour le chapitre {self.id()}, ce qui signale une erreur probable. Tentative de rafraîchissement.")
                return False

            # Télécharger les images
            self.pages_path = self.__download_chapter_images(driver, use_cache)

            if len(self.pages_path) != len(self.pages_link):
                print(f"❌ Problème avec le téléchargement des images du chapitre {self.id()} (téléchargées: {len(self.pages_path)}, attendues: {len(self.pages_link)})")
                return False
            return True
        except Exception as e:
            print(f"❌ Erreur lors de la récupération des images du chapitre {self.id()}: {e}")
            return False

    def download(self, format:str, use_cache:bool=True)->bool:
        """Télécharge le chapitre et le convertit au format demandé (PDF, CBZ ou CBR)."""
        if format not in CONVERTERS:
            return self.fetch_images(use_cache)  # Aucun format = téléchargement seul

        output_path = self.export_path(format)
        if os.path.exists(output_path):
            print(f"ℹ️  Le chapitre {self.id()} est déjà converti : {output_path}")
            return True

        if not self.fetch_images(use_cache):
            return False

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        return CONVERTERS[format](self.pages_path, output_path)

    def __download_chapter_images(self,driver=None,use_cache:bool=True)->list[str]:
        """
        Cette méthode télécharge toutes les images d'un chapitre et les stocke dans un dossier temporaire.
        Si use_cache est vrai et que le cache contient toutes les images du chapitre, elles sont réutilisées.

        Retour:
            list: Une liste contenant les chemins des fichiers téléchargés pour chaque image du chapitre.
        """
        chapter_dir = os.path.join(tempfile.gettempdir(), self.folder_name, f"chapter_{self.id()}")
        os.makedirs(chapter_dir, exist_ok=True)

        # Vérifier le cache
        cached_files = sorted(os.path.join(chapter_dir, f) for f in os.listdir(chapter_dir))
        if use_cache and cached_files and len(cached_files) == len(self.pages_link):
            print(f"✅ Chapitre {self.id()} : utilisation des {len(cached_files)} images du cache.")
            return cached_files

        for file_path in cached_files:
            os.remove(file_path)

        downloaded_images = []  # Liste pour stocker les chemins locaux des images téléchargées
        for index, url in enumerate(self.pages_link, 1):
            image_path = os.path.join(chapter_dir, f"{index:03d}.jpg")
            if utils.download_image(url, image_path, driver):
                downloaded_images.append(image_path)

        return downloaded_images
