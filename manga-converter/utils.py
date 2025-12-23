import os
import re
import shutil
import base64
import img2pdf
import zipfile
import requests
import subprocess
import undetected_chromedriver as uc

def get_domain(url:str)->str:
    """Cette fonction récupére le domaine d'un site web et le retourne, si il n'y a pas de valeur de retour, il retourne None

    Args:
        url (string): url sur laquelle faire la recherche

    Returns:
        string|None: domaine du site ou none
    """
    pattern = r'https?:\/\/(?:www\.)?([^\/\.]+)'
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    return None

def get_page(url_request:str,require_driver)->tuple[str,uc.Chrome]|None:
    """
    Cette fonction permet de récupéré le contenue d'une page web sous format HTML

    Args:
        url_request (string): l'url de la page a récupéré (par exemple www.google.com)

    Returns:
        string: Le contenu de la page sous format HTML ou None si une érreur s'est produite
    """
    domain_name = get_domain(url_request)
    return_value = None
    driver = None

    if require_driver:
        # Options pour rendre la navigation plus humaine
        options = uc.ChromeOptions()
        # options.add_argument('--headless') # Ne pas utiliser le mode headless (sans fenêtre) pour les CAPTCHAs !
        # Initialisation du driver "indétecté"
        driver = uc.Chrome(options=options, version_main=142)
        driver.set_script_timeout(120)

        try:
            print("Chargement de la page...")
            driver.get(url_request)
            # Pause pour vous laisser le temps de gérer le CAPTCHA manuellement
            # Le chargement ne devrait plus être infini ici
            print("ATTENTION : Résolvez le CAPTCHA dans la fenêtre ouverte.")
            input("Appuyez sur Entrée ici une fois le contenu chargé...")

            # Récupération des données
            return_value = driver.page_source
            print("Contenu récupéré !")
        except Exception as e:
            print(f"Une erreur est survenue : {e}")
    else: 
        s = requests.Session()
        s.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        })
        
        if domain_name == "lelmanga":
            s.headers.update({"Referer": "https://www.lelmanga.com/"})
        elif domain_name == "lelmanga":
            s.headers.update({"Referer": "https://mangakatana.com"})

        response = None
        try:
            response = s.get(url_request, timeout=20)  # Ajout d'un timeout
            response.raise_for_status()
            response.encoding = 'utf-8'
            return_value = response.text    
        except requests.exceptions.HTTPError as error:
            print("An HTTP error occurred:", error)
        except requests.exceptions.ReadTimeout:
            print("Request timed out")
        except requests.exceptions.ConnectionError:
            print("Connection error")
        except requests.exceptions.RequestException as error:
            print("An unexpected error occurred:", error)

    return return_value,driver # Retourner le resultat de la requete

def remove_temp_folder(folder_path :str)->None:
    if os.path.exists(folder_path):
        # Supprimer tous les fichiers dans le dossier
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)  # Supprime le fichier
            elif os.path.isdir(file_path):
                remove_temp_folder(file_path)  # Supprime les sous-dossiers récursivement

        # Après avoir supprimé les fichiers et sous-dossiers, supprimer le dossier lui-même
        os.rmdir(folder_path)
        #print(f"Dossier supprimé : {folder_path}")
    else:
        print(f"Le dossier {folder_path} n'existe pas.")

def download_image(url:str, filename:str,require_driver:bool,driver:uc.Chrome)->bool:
    """
    Cette fonction est utilisée pour télécharger une image à partir de son url
    Args:
        url (lien): le lien de l'image à télécharger
        filename (string): chemin du fichier et nom du fichier telecharger
    """
    if require_driver and driver is not None:
        return download_image_with_driver_single(driver, url, filename)
    else:
        try:
            response = requests.get(url, timeout=20)
            response.raise_for_status()  # Vérifie si la requête a réussi
            
            with open(filename, "wb") as file:  # Ouvrir en mode binaire
                file.write(response.content)  # Écrire le contenu brut de l'image
            
            #print(f"Image téléchargée : {filename}")
            return True
        except requests.exceptions.RequestException as error:
            print("Erreur lors du téléchargement :", error)
            return False

def download_image_with_driver_single(driver:uc.Chrome, url:str, filename:str)->bool:
    """
    Downloads an image using the session from the provided selenium driver.
    This method is faster as it uses requests with the driver's cookies.
    """
    try:
        # Get cookies from the driver
        cookies = driver.get_cookies()

        # Create a requests session
        s = requests.Session()

        # Add cookies to the session
        for cookie in cookies:
            # A cookie domain may not be defined, in which case it is only valid for the current domain.
            if 'domain' in cookie:
                s.cookies.set(cookie['name'], cookie['value'], domain=cookie['domain'])
            else:
                s.cookies.set(cookie['name'], cookie['value'])

        # Get User-Agent and Referer from driver and set them in the session
        user_agent = driver.execute_script("return navigator.userAgent;")
        referer_url = driver.current_url
        s.headers.update({
            "User-Agent": user_agent,
            "Referer": referer_url
        })

        # Download the image
        response = s.get(url, timeout=30)
        response.raise_for_status()

        # Save the image
        with open(filename, "wb") as file:
            file.write(response.content)

        return True

    except requests.exceptions.RequestException as e:
        print(f"Erreur lors du téléchargement de l'image avec la session : {e}")
        return False
    except Exception as e:
        print(f"Une erreur inattendue est survenue lors du téléchargement avec la session : {e}")
        return False

def images_to_pdf(img_list:list[str], output_pdf:str)->bool:
    """
    Convertit une liste d'images en un fichier PDF.

    Args:
        img_list (list[str]): Liste des chemins des images à convertir.
        output_pdf (str): Chemin du fichier PDF de sortie.

    Returns:
        bool: True si la conversion réussit, False sinon.
    """
    try:
        with open(output_pdf, "xb") as f:  
            f.write(img2pdf.convert(img_list))
        print(f"✅ PDF créé : {output_pdf}")
        return True
    except FileExistsError:
        print(f"❌ Erreur : le fichier '{output_pdf}' existe déjà.")
        return False
    except Exception as e:
        print(f"❌ Erreur lors de la création du PDF : {e}")
        return False

def images_to_cbr(image_paths:list[str], cbr_path:str)->None:
    """Crée un fichier CBR (Comic Book RAR) sous Ubuntu en utilisant rar ou 7z."""
    
    # Vérifier si 'rar' ou '7z' est disponible
    if shutil.which("rar"):
        command = ["rar", "a", "-ep", cbr_path] + image_paths
    elif shutil.which("7z"):
        command = ["7z", "a", cbr_path] + image_paths  # Utilisation de 7z si rar n'est pas installé
    else:
        raise FileNotFoundError("Ni 'rar' ni '7z' ne sont installés. Installez-les avec 'sudo apt install rar' ou 'sudo apt install p7zip-full'.")

    # Exécuter la commande
    subprocess.run(command, check=True)
    
    print(f'Conversion en CBR terminée : {cbr_path}')

def images_to_cbz(image_paths:list[str], cbz_path:str)->None:
    """Crée un fichier CBZ (Comic Book Zip) sous Ubuntu."""
    
    with zipfile.ZipFile(cbz_path, 'w') as cbz:
        for image_path in image_paths:
            cbz.write(image_path, os.path.basename(image_path))
    
    print(f'Conversion en CBZ terminée : {cbz_path}')

def normalize_volume(label: str) -> int:
    m = re.search(r'\d+', label)
    return int(m.group()) if m else None