# Manga-converter

## Dépendance

### Ubuntu

- python3
- calibre
- Kcc [(voir marche a suivre)](https://github.com/ciromattia/kcc/wiki/Installation)

### Python

Utilisé cette commande pour installer les requirements à l'aide du fichier à la racine

```bash
pip install -r requirements.txt
```

Utilisé cette commande pour récupéré tout les paquets utilisé dans le projet

```bash
pip freeze > requirements.txt
```

## Utilisation

Depuis le dossier `manga-converter/` :

```bash
python main.py -u <url du manga>      # depuis l'url d'un manga
python main.py -s "nom du manga"      # via une recherche
python main.py -u <url> --no-cache    # re-télécharge les images même si elles sont en cache
```

Les plages de chapitres acceptent les demi-chapitres (ex: `12.5` ou `270-271.5`).

## Tests

Les tests utilisent les pages HTML d'exemple de `Docs/html_fetched_exemple/` (aucun accès réseau).
Depuis la racine du projet :

```bash
pip install -r requirements-dev.txt
pytest
```
