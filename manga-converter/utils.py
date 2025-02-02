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
    pattern = r'https?:\/\/(?:www\.)?([^\/]+)'
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
        
        print(f"Image téléchargée : {filename}")
    except requests.exceptions.RequestException as error:
        print("Erreur lors du téléchargement :", error)

def images_to_pdf(img_list, output_pdf):
    """
    Cette fonction prend en paramètre une liste d'image et un nom de fichier pour la sortie pdf

    Args:
        img_list (array[string]): une liste contenant le lien vers les images à transformer en pdf
        output_pdf (string): sortie pdf des images combinées
    """
    with open(output_pdf, "wb") as f:
        f.write(img2pdf.convert(img_list))
    print(f"PDF créé : {output_pdf}")
    
def convert_pdf_to_epub(input_pdf, output_epub):
    """
    Cette fonction utilise la commande bash "ebook-convert" (avec subproscess)  utilisée avec calibre pour convertir un pdf en ebook
    Args:
        input_pdf (_type_): lien du pdf a ajouter en entrée
        output_epub (_type_): emplacement voulu de l'ebook en sortie
    """
    subprocess.run(['ebook-convert', input_pdf, output_epub])