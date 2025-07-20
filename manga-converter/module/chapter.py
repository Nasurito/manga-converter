import re
import os
import tempfile
import utils

class Chapter:
    """Cette classe est utilisé pour définir un chapitre dans un manga, un chapitre posséde plusieurs pages (image récupérée depuis le site)"""
    def __init__(self,id,manga_name,link):
        """
        Cette fonction est appalée à chaque création d'un chapitre, elle permet de récupéré les informations en fonctions du lien et des sites supporté

        Args:
            link (string): lien du chapitre sur le site de scan
        """
        self.id_chapter = id
        self.manga_name = manga_name
        self.chapter_html_page = None
        self.chapter_html_link = link
        self.domain_name = utils.get_domain(link)
        self.pages_link = []
        self.pages_path = []
        self.converted_pdf_chapters_path = None
        if os.path.exists(f"./export/{self.manga_name}/pdf/chapter_{self.id()}.pdf"):
            self.converted_pdf_chapters_path = f"./export/{self.manga_name}/pdf/chapter_{self.id()}.pdf"
        
        self.converted_cbr_chapters_path = None
        if os.path.exists(f"./export/{self.manga_name}/cbr/chapter_{self.id()}.cbr"):
            self.converted_cbr_chapters_path = f"./export/{self.manga_name}/cbr/chapter_{self.id()}.cbr"
        
        self.converted_cbz_chapters_path = None
        if os.path.exists(f"./export/{self.manga_name}/cbr/chapter_{self.id()}.cbz"):
            self.converted_cbz_chapters_path = f"./export/{self.manga_name}/cbz/chapter_{self.id()}.cbz"
            
    def id(self):
        return int(self.id_chapter) if float(self.id_chapter).is_integer() else float(self.id_chapter)

    def get_convetion_path(self,format):
        if format == 'CBZ':
            return self.converted_cbz_chapters_path
        elif format == 'CBR':
            return self.converted_cbr_chapters_path
        else:
            return self.converted_pdf_chapters_path

    def fetch_images(self):
        """
        Cette méthode permet de télécharger les pages d'un chapitre d'un manga.

        Elle récupère d'abord la page HTML du chapitre, extrait les liens des pages d'images,
        puis télécharge ces images dans un dossier temporaire.

        Le processus est effectué en plusieurs étapes conditionnelles :
        - Récupération de la page HTML du chapitre si elle n'a pas encore été récupérée.
        - Extraction des liens des pages d'images en fonction du site d'origine.
        - Téléchargement des images si elles n'ont pas encore été téléchargées.

        Si toutes les étapes sont réussies, la méthode retourne `True`. Sinon, elle retourne `False`.

        Retour:
            bool: `True` si le téléchargement a réussi (pages et images récupérées et téléchargées correctement),
                `False` en cas d'échec (par exemple, si les liens des pages ou les images sont manquants ou incorrects).
        """

        # retourne directement True si le chemin d'acces est déja existant
        if self.pages_path:
            return True

        if self.chapter_html_page is None:
            # Récupération de la page HTML du chapitre via un utilitaire (extraction du contenu texte)
            self.chapter_html_page = utils.get_page(self.chapter_html_link).text
            # Suppression des espaces inutiles dans le HTML pour nettoyer le contenu
            self.chapter_html_page = re.sub(r'\s+', ' ', self.chapter_html_page)

        # Si la liste des liens des pages est vide (c'est-à-dire qu'elles n'ont pas encore été extraites)
        if not self.pages_link:
            # Selon le domaine (site d'origine), on utilise la méthode appropriée pour extraire les liens des pages d'images
            if self.domain_name == "mangakatana":
                self.pages_link = self.__get_pages_link_from_mangakatana()
            elif self.domain_name == "lelmanga":
                self.pages_link = self.__get_pages_link_from_lelmanga()
        
        # Si les chemins des images n'ont pas encore été trouvée
        if not self.pages_link:
            return False

        #Appel de la fonction qui télécharges toutes les images d'un chapitre
        self.pages_path = self.__download_chapter_images()

        # Suppression du dossier temporaire déplacée ailleurs si nécessaire
        return self.pages_path is not None and len(self.pages_path) == len(self.pages_link)
    
    def fetch_images(self):
        if self.pages_path:  # Déjà fait
            return True

        # Récupérer et nettoyer la page HTML
        if not self.chapter_html_page:
            html = utils.get_page(self.chapter_html_link)
            if not html:
                return False
            self.chapter_html_page = re.sub(r'\s+', ' ', html.text)

        # Extraire les liens si pas déjà fait
        if not self.pages_link:
            if self.domain_name == "mangakatana":
                self.pages_link = self.__get_pages_link_from_mangakatana()
            elif self.domain_name == "lelmanga":
                self.pages_link = self.__get_pages_link_from_lelmanga()

        if not self.pages_link:
            print(f"❌ Pas de pages trouvées pour chapitre {self.id()}")
            return False

        # Télécharger les images
        self.pages_path = self.__download_chapter_images()

        if not self.pages_path or len(self.pages_path) != len(self.pages_link):
            print(f"❌ Problème avec le téléchargement des images du chapitre {self.id()}")
            return False

        return True


    def download(self, format):
        if not self.fetch_images():
            return False

        if format == "PDF":
            return self.__convert_to_pdf()
        elif format == "CBZ":
            return self.__convert_to_CBZ()
        elif format == "CBR":
            return self.__convert_to_CBR()
        
        return True  # Aucun format = téléchargement seul



    def __get_pages_link_from_mangakatana(self):
        """
        Cette méthode récupère les liens de toutes les pages d'un chapitre du site mangakatana.com.
        Elle extrait les liens des pages à partir du code JavaScript de la page HTML.

        La méthode utilise une expression régulière pour rechercher une variable JavaScript contenant un tableau des URLs des pages.

        Retour:
            list: Un tableau de chaînes de caractères contenant les liens des pages du chapitre dans l'ordre.
        """
        # Définir le modèle d'expression régulière pour rechercher la variable JavaScript contenant les liens des pages
        pattern = r"var\s+thzq\s*=\s*(\[[^\]]+\])"
        
        # Rechercher la correspondance dans la page HTML du chapitre
        match = re.search(pattern, self.chapter_html_page, re.DOTALL)
        
        # Si une correspondance est trouvée, on renvoie le contenu du tableau de liens
        if match is not None:
            return eval(match.group(1))  # Evaluer la chaîne de caractères en un tableau Python
    
    def __get_pages_link_from_lelmanga(self):
        """
        Cette méthode récupère les liens de toutes les pages d'un chapitre du site lelmanga.com.
        Elle extrait les liens des pages en utilisant une expression régulière qui recherche les attributs `src` des images.

        Retour:
            list: Un tableau de chaînes de caractères contenant les liens des pages du chapitre dans l'ordre.
        """
        # Définir le modèle d'expression régulière pour extraire les liens des images depuis les balises <img>
        regex = r'<img\s+loading=["\']lazy["\'][^>]*\s+src=["\']([^"\']+)["\']'
        
        # Trouver toutes les correspondances dans la page HTML pour extraire les liens des images
        matches = re.findall(regex, self.chapter_html_page)
        
        # Si des correspondances sont trouvées, renvoyer la liste des liens des pages
        if matches is not None:
            return matches
    
    def __download_chapter_images(self):
        """
        Cette méthode télécharge toutes les images d'un chapitre et les stocke dans un dossier temporaire.
        
        Elle crée un répertoire temporaire pour le manga, puis un sous-dossier pour le chapitre spécifié.
        Ensuite, elle télécharge les images des pages et les enregistre localement.

        Retour:
            list: Une liste contenant les chemins des fichiers téléchargés pour chaque image du chapitre.
        """
        # Créer un dossier racine pour le manga dans le répertoire temporaire (en utilisant le nom du manga)
        root_dir = os.path.join(tempfile.gettempdir(), self.manga_name)
        os.makedirs(root_dir, exist_ok=True)  # Créer le dossier s'il n'existe pas
        
        # Créer un sous-dossier pour le chapitre en utilisant son ID
        chapter_dir = os.path.join(root_dir, f"chapter_{self.id()}")
        os.makedirs(chapter_dir, exist_ok=True)  # Créer le dossier du chapitre
        
        downloaded_images = []  # Liste pour stocker les chemins locaux des images téléchargées

        # Télécharger chaque image du chapitre et enregistrer dans le dossier du chapitre
        for index, url in enumerate(self.pages_link,1):
            # Définir le chemin où l'image sera enregistrée (nom du fichier basé sur l'index)
            image_path = os.path.join(chapter_dir, f"{index:03d}.jpg")
            
            # Télécharger l'image et la sauvegarder
            if utils.download_image(url, image_path):
                # Ajouter le chemin de l'image téléchargée à la liste
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