import os
import re
import shutil
import img2pdf
import zipfile
import requests
import subprocess
import undetected_chromedriver as uc

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

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

def get_chrome_major_version()->int:
    """
    Retourne la version majeure du Chrome installé (ex: 144), ou None si elle n'est pas détectée.
    Sans cette information, undetected_chromedriver télécharge le dernier chromedriver,
    qui peut être plus récent que le Chrome installé et refuser de se lancer.
    """
    candidates = [uc.find_chrome_executable(), "google-chrome", "google-chrome-stable", "chromium", "chromium-browser"]
    for executable in filter(None, candidates):
        path = shutil.which(executable)
        if not path:
            continue
        try:
            output = subprocess.run([path, "--version"], capture_output=True, text=True, timeout=10).stdout
        except (OSError, subprocess.SubprocessError):
            continue
        match = re.search(r'(\d+)\.\d+', output)
        if match:
            return int(match.group(1))
    return None

def build_session(driver:uc.Chrome=None, referer:str=None)->requests.Session:
    """
    Crée une session requests. Si un driver est fourni, la session reprend ses cookies,
    son User-Agent et son url courante (Referer) afin de passer les protections anti-bot.
    """
    s = requests.Session()
    s.headers.update(DEFAULT_HEADERS)

    if driver is not None:
        for cookie in driver.get_cookies():
            # Le domaine d'un cookie peut ne pas être défini, il n'est alors valable que pour le domaine courant.
            if 'domain' in cookie:
                s.cookies.set(cookie['name'], cookie['value'], domain=cookie['domain'])
            else:
                s.cookies.set(cookie['name'], cookie['value'])
        s.headers.update({"User-Agent": driver.execute_script("return navigator.userAgent;")})
        referer = driver.current_url

    if referer:
        s.headers.update({"Referer": referer})
    return s

def get_page(url_request:str,require_driver:bool,passed_driver:uc.Chrome=None,referer:str=None)->tuple[str,uc.Chrome]:
    """
    Cette fonction permet de récupéré le contenue d'une page web sous format HTML

    Args:
        url_request (string): l'url de la page a récupéré (par exemple www.google.com)
        require_driver (bool): utiliser un navigateur (nécessaire pour les sites protégés par CAPTCHA)
        passed_driver (uc.Chrome): driver déjà ouvert à réutiliser
        referer (string): Referer à envoyer avec la requête (sans driver uniquement)

    Returns:
        tuple: Le contenu de la page sous format HTML (ou None si une érreur s'est produite) et le driver utilisé
    """
    return_value = None
    driver = None

    if require_driver:

        if passed_driver:
            driver = passed_driver
        else:
            # Options pour rendre la navigation plus humaine
            options = uc.ChromeOptions()
            # options.add_argument('--headless') # Ne pas utiliser le mode headless (sans fenêtre) pour les CAPTCHAs !
            # Initialisation du driver "indétecté"
            # On aligne le chromedriver sur la version du Chrome installé
            driver = uc.Chrome(options=options, version_main=get_chrome_major_version())
            driver.set_script_timeout(120)

        try:
            print("Chargement de la page...")
            driver.get(url_request)
            # Pause pour vous laisser le temps de gérer le CAPTCHA manuellement
            print("ATTENTION : Résolvez le CAPTCHA dans la fenêtre ouverte.")
            input("Appuyez sur Entrée ici une fois le contenu chargé...")

            # Récupération des données
            return_value = driver.page_source
            print("Contenu récupéré !")
        except Exception as e:
            print(f"Une erreur est survenue : {e}")
    else:
        try:
            response = build_session(referer=referer).get(url_request, timeout=20)
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

def download_image(url:str, filename:str, driver:uc.Chrome=None)->bool:
    """
    Cette fonction est utilisée pour télécharger une image à partir de son url
    Args:
        url (lien): le lien de l'image à télécharger
        filename (string): chemin du fichier et nom du fichier telecharger
        driver (uc.Chrome): si fourni, sa session (cookies, User-Agent) est utilisée pour la requête
    """
    try:
        response = build_session(driver).get(url, timeout=30)
        response.raise_for_status()  # Vérifie si la requête a réussi

        with open(filename, "wb") as file:  # Ouvrir en mode binaire
            file.write(response.content)  # Écrire le contenu brut de l'image
        return True
    except Exception as error:
        print("Erreur lors du téléchargement :", error)
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

def images_to_cbr(image_paths:list[str], cbr_path:str)->bool:
    """Crée un fichier CBR (Comic Book RAR) en utilisant rar ou 7z."""

    # Vérifier si 'rar' ou '7z' est disponible
    if shutil.which("rar"):
        command = ["rar", "a", "-ep", cbr_path] + image_paths
    elif shutil.which("7z"):
        command = ["7z", "a", cbr_path] + image_paths  # Utilisation de 7z si rar n'est pas installé
    else:
        print("❌ Ni 'rar' ni '7z' ne sont installés. Installez-les avec 'sudo apt install rar' ou 'sudo apt install p7zip-full'.")
        return False

    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de la création du CBR : {e}")
        return False

    print(f'Conversion en CBR terminée : {cbr_path}')
    return True

def images_to_cbz(image_paths:list[str], cbz_path:str)->bool:
    """Crée un fichier CBZ (Comic Book Zip)."""

    with zipfile.ZipFile(cbz_path, 'w') as cbz:
        for image_path in image_paths:
            cbz.write(image_path, os.path.basename(image_path))

    print(f'Conversion en CBZ terminée : {cbz_path}')
    return True

def normalize_volume(label: str) -> int:
    m = re.search(r'\d+', label)
    return int(m.group()) if m else None
