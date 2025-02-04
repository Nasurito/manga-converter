import os
import re
import img2pdf
import requests
import subprocess

def get_domain(url):
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

def get_page(url_request):
    """
    Cette fonction permet de récupéré le contenue d'une page web sous format HTML

    Args:
        url_request (string): l'url de la page a récupéré (par exemple www.google.com)

    Returns:
        string: Le contenu de la page sous format HTML ou None si une érreur s'est produite
    """
    try:
        response = requests.get(url_request, timeout=20)  # Ajout d'un timeout
        response.raise_for_status()
        response.encoding = 'utf-8'   
    except requests.exceptions.HTTPError as error:
        print("An HTTP error occurred:", error)
        response = None 
    except requests.exceptions.ReadTimeout:
        print("Request timed out")
        response = None
    except requests.exceptions.ConnectionError:
        print("Connection error")
        response = None
    except requests.exceptions.RequestException as error:
        print("An unexpected error occurred:", error)
        response = None
    return response # Retourner le resultat de la requete

def remove_temp_folder(folder_path):
    """Supprime un dossier et son contenu sans utiliser shutil."""
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
        print(f"Dossier supprimé : {folder_path}")
    else:
        print(f"Le dossier {folder_path} n'existe pas.")



def download_image(url, filename):
    """
    Cette fonction est utilisée pour télécharger une image à partir de son url
    Args:
        url (lien): le lien de l'image à télécharger
        filename (string): chemin du fichier et nom du fichier telecharger
    """
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

def images_to_pdf(img_list, output_pdf):
    """
    Convertit une liste d'images en un fichier PDF.

    Args:
        img_list (list[str]): Liste des chemins des images à convertir.
        output_pdf (str): Chemin du fichier PDF de sortie.

    Returns:
        bool: True si la conversion réussit, False sinon.
    """
    try:
        with open(output_pdf, "wb") as f:
            f.write(img2pdf.convert(img_list))
        print(f"✅ PDF créé : {output_pdf}")
        return True
    except Exception as e:
        print(f"❌ Erreur lors de la création du PDF : {e}")
        return False
    
def convert_pdf_to_epub(input_pdf, output_epub):
    """
    Cette fonction utilise la commande bash "ebook-convert" (avec subproscess)  utilisée avec calibre pour convertir un pdf en ebook
    Args:
        input_pdf (_type_): lien du pdf a ajouter en entrée
        output_epub (_type_): emplacement voulu de l'ebook en sortie
    """
    subprocess.run(['ebook-convert', input_pdf, output_epub])