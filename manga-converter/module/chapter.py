import json
import re
import os
import tempfile
import utils
from module.abstract_classes.BaseScaper import BaseScraper

class Chapter:
    """Cette classe est utilisé pour définir un chapitre dans un manga, un chapitre posséde plusieurs pages (image récupérée depuis le site)"""
    def __init__(self,id:int,manga_name:str,link:str, scraper: BaseScraper)->None:
        """
        Cette fonction est appalée à chaque création d'un chapitre, elle permet de récupéré les informations en fonctions du lien et des sites supporté

        Args:
            link (string): lien du chapitre sur le site de scan
        """
        self.id_chapter = id
        self.manga_name = manga_name
        self.chapter_html_link = link
        self.scraper = scraper
        self.pages_link = []
        self.pages_path = []
        self.converted_pdf_chapters_path = None
        if os.path.exists(f"./export/{self.manga_name}/pdf/chapter_{self.id()}.pdf"):
            self.converted_pdf_chapters_path = f"./export/{self.manga_name}/pdf/chapter_{self.id()}.pdf"
        
        self.converted_cbr_chapters_path = None
        if os.path.exists(f"./export/{self.manga_name}/cbr/chapter_{self.id()}.cbr"):
            self.converted_cbr_chapters_path = f"./export/{self.manga_name}/cbr/chapter_{self.id()}.cbr"
        
        self.converted_cbz_chapters_path = None
        if os.path.exists(f"./export/{self.manga_name}/cbz/chapter_{self.id()}.cbz"):
            self.converted_cbz_chapters_path = f"./export/{self.manga_name}/cbz/chapter_{self.id()}.cbz"
            
    def id(self):
        return int(self.id_chapter) if float(self.id_chapter).is_integer() else float(self.id_chapter)

    def get_convetion_path(self,format:str)->str:
        if format == 'CBZ':
            return self.converted_cbz_chapters_path
        elif format == 'CBR':
            return self.converted_cbr_chapters_path
        else:
            return self.converted_pdf_chapters_path

    def fetch_images(self)->bool:
        if self.pages_path:  # Déjà fait
            return True

        max_retries = 5
        for attempt in range(1, max_retries + 1):
            success = self._try_fetch_images()
            if success:
                return True
            elif attempt < max_retries:
                print(f"⚠️ Problème lors du téléchargement du chapitre {self.id()}, tentative {attempt}/{max_retries}. Nouvel essai...")
                # Reset state for a clean retry
                self.chapter_html_page = None
                self.pages_link = []
                self.pages_path = []
            else:
                print(f"❌ Échec du téléchargement du chapitre {self.id()} après {max_retries} tentatives.")
                return False
        return False

    def _try_fetch_images(self)->bool:
        driver = None
        try:
            # Extraire les liens si pas déjà fait
            if not self.pages_link:
                # Utilise le scraper pour obtenir les liens des images.
                # La logique de récupération de page est maintenant dans le scraper.
                self.pages_link,driver = self.scraper.get_chapter_images(self.chapter_html_link)

            if not self.pages_link:
                print(f"❌ Pas de pages trouvées pour chapitre {self.id()}")
                return False
            
            # Vérification spéciale : si une seule image est trouvée, c'est probablement une erreur
            if len(self.pages_link) == 1:
                print(f"⚠️ Une seule image a été trouvée pour le chapitre {self.id()}, ce qui signale une erreur probable. Tentative de rafraîchissement.")
                return False

            # Télécharger les images
            self.pages_path = self.__download_chapter_images(driver)

            if not self.pages_path or len(self.pages_path) != len(self.pages_link):
                print(f"❌ Problème avec le téléchargement des images du chapitre {self.id()} (téléchargées: {len(self.pages_path)}, attendues: {len(self.pages_link)})")
                return False
            return True
        except Exception as e:
            print(f"❌ Erreur lors de la récupération des images du chapitre {self.id()}: {e}")
            return False

    def download(self, format:str)->bool:
        if not self.fetch_images():
            return False

        if format == "PDF":
            return self.__convert_to_pdf()
        elif format == "CBZ":
            return self.__convert_to_CBZ()
        elif format == "CBR":
            return self.__convert_to_CBR()
        
        return True  # Aucun format = téléchargement seul

    def __download_chapter_images(self,driver=None)->list[str]:
        """
        Cette méthode télécharge toutes les images d'un chapitre et les stocke dans un dossier temporaire.
        Elle vérifie d'abord si les images existent en cache et demande à l'utilisateur s'il veut les réutiliser.
        
        Elle crée un répertoire temporaire pour le manga, puis un sous-dossier pour le chapitre spécifié.
        Ensuite, elle télécharge les images des pages et les enregistre localement.

        Retour:
            list: Une liste contenant les chemins des fichiers téléchargés pour chaque image du chapitre.
        """
        # Définir les chemins pour le cache
        root_dir = os.path.join(tempfile.gettempdir(), self.manga_name)
        chapter_dir = os.path.join(root_dir, f"chapter_{self.id()}")
        os.makedirs(chapter_dir, exist_ok=True)

        # Vérifier le cache
        if os.path.exists(chapter_dir) and len(os.listdir(chapter_dir)) > 0:
            cached_files = sorted([os.path.join(chapter_dir, f) for f in os.listdir(chapter_dir)])
            
            if len(cached_files) == len(self.pages_link):
                print(f"ℹ️  Le chapitre {self.id()} a été trouvé dans le cache avec {len(cached_files)} images.")
                user_choice = input("Voulez-vous réutiliser le cache ? (O/n) : ").strip().lower()
                
                if user_choice != 'n':
                    print("✅ Utilisation des images du cache.")
                    return cached_files
                else:
                    print("🗑️ Suppression des anciennes images du cache...")
                    for file_path in cached_files:
                        os.remove(file_path)

        os.makedirs(chapter_dir, exist_ok=True)
        
        downloaded_images = []  # Liste pour stocker les chemins locaux des images téléchargées

        # Télécharger chaque image du chapitre et enregistrer dans le dossier du chapitre
        for index, url in enumerate(self.pages_link, 1):
            image_path = os.path.join(chapter_dir, f"{index:03d}.jpg")
            # La logique de téléchargement spécifique (ex: avec un driver pour sushiscan)
            # devra être gérée par le scraper correspondant à l'avenir.
            if utils.download_image(url, image_path,self.scraper.do_require_driver(),driver):
                downloaded_images.append(image_path)

        # Retourner la liste des chemins des images téléchargées
        return downloaded_images
    
    def __convert_to_pdf(self):
        """
        Convertit les images du chapitre en un fichier PDF et l'enregistre dans le dossier export.
        """        
        # Définir le dossier d'exportation
        root_dir = os.path.join("./export", self.manga_name+"/pdf/")
        os.makedirs(root_dir, exist_ok=True)  # Créer le dossier s'il n'existe pas
        path_for_convertion = root_dir+f"chapter_{self.id()}.pdf"
        
        if self.converted_pdf_chapters_path == None:
            # Convertir les images en PDF
            self.converted_pdf_chapters_path = path_for_convertion
            return utils.images_to_pdf(self.pages_path,path_for_convertion )
        else :
            print (f"Chapter {self.id()} is already converted")
            return True
    
    def __convert_to_CBR(self):
        """
        Convertit les images du chapitre en un fichier PDF et l'enregistre dans le dossier export.
        """        
        # Définir le dossier d'exportation
        root_dir = os.path.join("./export", self.manga_name+"/cbr/")
        os.makedirs(root_dir, exist_ok=True)  # Créer le dossier s'il n'existe pas
        path_for_convertion = root_dir+f"chapter_{self.id()}.cbr"
        
        if self.converted_cbr_chapters_path == None:
            # Convertir les images en PDF
            self.converted_cbr_chapters_path = path_for_convertion
            return utils.images_to_cbr(self.pages_path,path_for_convertion)
        else :
            print (f"Chapter {self.id()} is already converted")
            return True
    
    def __convert_to_CBZ(self):
        """
        Convertit les images du chapitre en un fichier PDF et l'enregistre dans le dossier export.
        """        
        # Définir le dossier d'exportation
        root_dir = os.path.join("./export", self.manga_name+"/cbz/")
        os.makedirs(root_dir, exist_ok=True)  # Créer le dossier s'il n'existe pas
        path_for_convertion = root_dir+f"chapter_{self.id()}.cbz"
        
        if self.converted_cbz_chapters_path == None:
            # Convertir les images en PDF
            self.converted_cbz_chapters_path = path_for_convertion
            return utils.images_to_cbz(self.pages_path,path_for_convertion)
        else :
            print (f"Chapter {self.id()} is already converted")
            return True