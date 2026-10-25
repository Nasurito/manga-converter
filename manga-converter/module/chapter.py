import os
import tempfile
from concurrent.futures import ThreadPoolExecutor
import utils
from module.abstract_classes.base_scraper import BaseScraper

# Nombre d'images téléchargées en même temps : assez pour aller vite, assez peu pour ne pas être bloqué par le site
PARALLEL_DOWNLOADS = 4
# Nombre d'essais par image avant de considérer le téléchargement du chapitre comme raté
DOWNLOAD_ATTEMPTS = 3

# Fonction de conversion associée à chaque format de sortie (l'extension du fichier est le format en minuscule)
CONVERTERS = {
    "PDF": utils.images_to_pdf,
    "CBZ": utils.images_to_cbz,
    "CBR": utils.images_to_cbr,
}

class Chapter:
    """Cette classe est utilisé pour définir un chapitre dans un manga, un chapitre posséde plusieurs pages (image récupérée depuis le site)"""
    def __init__(self,number:int|float,manga_title:str,url:str, scraper: BaseScraper, output_dir:str="./export")->None:
        """
        Cette fonction est appalée à chaque création d'un chapitre, elle permet de récupéré les informations en fonctions du lien et des sites supporté

        Args:
            number (int|float): numéro du chapitre (12 ou 12.5 pour un demi-chapitre)
            url (string): lien du chapitre sur le site de scan
            output_dir (string): dossier dans lequel les chapitres convertis sont exportés
        """
        # 12.0 est stocké comme 12 pour que les chemins et l'affichage restent "chapter_12"
        self.number = int(number) if float(number).is_integer() else float(number)
        self.manga_title = manga_title
        self.folder_name = utils.safe_filename(manga_title)  # nom utilisable dans les chemins
        self.output_dir = output_dir
        self.url = url
        self.scraper = scraper
        self.page_urls = []
        self.page_paths = []

    def export_path(self, output_format:str)->str:
        """Retourne le chemin du fichier exporté pour un format donné (ex: ./export/<manga>/cbz/chapter_1.cbz)."""
        extension = output_format.lower()
        return os.path.join(self.output_dir, self.folder_name, extension, f"chapter_{self.number}.{extension}")

    def fetch_images(self, use_cache:bool=True)->bool:
        """
        Récupère les images du chapitre (avec plusieurs tentatives).

        Args:
            use_cache (bool): réutiliser les images déjà téléchargées dans le dossier temporaire si elles sont complètes
        """
        if self.page_paths:  # Déjà fait
            return True

        max_retries = 5
        for attempt in range(1, max_retries + 1):
            if self._try_fetch_images(use_cache):
                return True
            if attempt < max_retries:
                print(f"⚠️ Problème lors du téléchargement du chapitre {self.number}, tentative {attempt}/{max_retries}. Nouvel essai...")
                # Reset state for a clean retry
                self.page_urls = []
                self.page_paths = []

        print(f"❌ Échec du téléchargement du chapitre {self.number} après {max_retries} tentatives.")
        return False

    def _try_fetch_images(self, use_cache:bool)->bool:
        driver = None
        try:
            # Extraire les liens si pas déjà fait
            if not self.page_urls:
                self.page_urls,driver = self.scraper.get_chapter_images(self.url)

            if not self.page_urls:
                print(f"❌ Pas de pages trouvées pour chapitre {self.number}")
                return False

            # Vérification spéciale : si une seule image est trouvée, c'est probablement une erreur
            if len(self.page_urls) == 1:
                print(f"⚠️ Une seule image a été trouvée pour le chapitre {self.number}, ce qui signale une erreur probable. Tentative de rafraîchissement.")
                return False

            # Télécharger les images
            self.page_paths = self._download_images(driver, use_cache)

            if len(self.page_paths) != len(self.page_urls):
                print(f"❌ Problème avec le téléchargement des images du chapitre {self.number} (téléchargées: {len(self.page_paths)}, attendues: {len(self.page_urls)})")
                return False
            return True
        except Exception as e:
            print(f"❌ Erreur lors de la récupération des images du chapitre {self.number}: {e}")
            return False

    def download(self, output_format:str, use_cache:bool=True)->bool:
        """Télécharge le chapitre et le convertit au format demandé (PDF, CBZ ou CBR)."""
        if output_format not in CONVERTERS:
            return self.fetch_images(use_cache)  # Aucun format = téléchargement seul

        output_path = self.export_path(output_format)
        if os.path.exists(output_path):
            print(f"ℹ️  Le chapitre {self.number} est déjà converti : {output_path}")
            return True

        if not self.fetch_images(use_cache):
            return False

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        return CONVERTERS[output_format](self.page_paths, output_path)

    def _download_images(self,driver=None,use_cache:bool=True)->list[str]:
        """
        Cette méthode télécharge toutes les images d'un chapitre et les stocke dans un dossier temporaire.
        Si use_cache est vrai et que le cache contient toutes les images du chapitre, elles sont réutilisées.

        Retour:
            list: Une liste contenant les chemins des fichiers téléchargés pour chaque image du chapitre.
        """
        chapter_dir = os.path.join(tempfile.gettempdir(), self.folder_name, f"chapter_{self.number}")
        os.makedirs(chapter_dir, exist_ok=True)

        # Vérifier le cache
        cached_files = sorted(os.path.join(chapter_dir, f) for f in os.listdir(chapter_dir))
        if use_cache and cached_files and len(cached_files) == len(self.page_urls):
            print(f"✅ Chapitre {self.number} : utilisation des {len(cached_files)} images du cache.")
            return cached_files

        for file_path in cached_files:
            os.remove(file_path)

        # Une seule session pour tout le chapitre : les cookies du navigateur (CAPTCHA) ne sont copiés
        # qu'une fois et la connexion au serveur d'images est réutilisée d'une image à l'autre
        session = utils.build_session(driver)
        image_paths = [os.path.join(chapter_dir, f"{index:03d}.jpg") for index in range(1, len(self.page_urls) + 1)]

        def download(url, image_path):
            return utils.download_image(url, image_path, session=session, attempts=DOWNLOAD_ATTEMPTS)

        print(f"📥 Chapitre {self.number} : téléchargement de {len(self.page_urls)} images...")
        with ThreadPoolExecutor(max_workers=PARALLEL_DOWNLOADS) as executor:
            results = list(executor.map(download, self.page_urls, image_paths))

        # Chemins des images téléchargées, dans l'ordre des pages
        return [path for path, success in zip(image_paths, results) if success]
