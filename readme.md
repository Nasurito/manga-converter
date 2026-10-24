# Manga-converter

## Dépendances

### Système (Ubuntu / WSL)

- Python 3.10 ou plus récent
- Google Chrome : nécessaire uniquement pour les sites protégés par CAPTCHA (sushiscan). La version de Chrome installée est détectée automatiquement.
- `p7zip-full` (ou `rar`) : nécessaire uniquement pour l'export CBR

```bash
sudo apt install python3-venv p7zip-full
```

### Python

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

`requirements.txt` ne liste que les dépendances directes du programme : en cas d'ajout d'une bibliothèque, l'ajouter à la main
plutôt que d'utiliser `pip freeze` (qui y ajouterait toutes les dépendances indirectes).

## Utilisation

```bash
python manga-converter/main.py -u <url du manga>      # depuis l'url d'un manga
python manga-converter/main.py -s "nom du manga"      # via une recherche
python manga-converter/main.py -u <url> -o ~/mangas   # choisir le dossier d'export (par défaut : ./export)
python manga-converter/main.py -u <url> --no-cache    # re-télécharge les images même si elles sont en cache
```

Les plages de chapitres acceptent les demi-chapitres (ex: `12.5` ou `270-271.5`).

## Ajouter un site

Créer une sous-classe de `BaseScraper` (`manga-converter/module/abstract_classes/base_scraper.py`) dans
`manga-converter/module/scrapers/`, puis l'enregistrer dans `SCRAPERS` (`manga-converter/module/scrapers/__init__.py`).
Surcharger `search()` pour que le site apparaisse dans la recherche.

## Outils optionnels

Ces outils ne sont pas utilisés par le programme, mais peuvent servir à retravailler les fichiers exportés :

- Calibre avec le plugin EpubMerge, pour fusionner des EPUB : [Docs/install_calibre.md](Docs/install_calibre.md)
- KCC (Kindle Comic Converter), pour optimiser les fichiers pour liseuse : [Docs/install_kcc.md](Docs/install_kcc.md)

## Tests

Les tests utilisent les pages HTML d'exemple de `Docs/html_fetched_exemple/` (aucun accès réseau).
Depuis la racine du projet :

```bash
pip install -r requirements-dev.txt
pytest
```
