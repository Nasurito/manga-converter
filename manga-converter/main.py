import argparse

from module.search_engine import Search_engine
from module.manga import Manga

def parse_chapter_number(number_string: str) -> int|float:
    """Convertit un numéro de chapitre en nombre, en gardant les demi-chapitres. Exemples: '5' -> 5, '12.5' -> 12.5"""
    number = float(number_string)
    return int(number) if number.is_integer() else number

def parse_chapter_range(chapter_string: str) -> tuple[int|float, int|float]:
    """
    Analyse une chaîne de caractères représentant une plage de chapitres.
    Exemples: '5' -> (5, 5), '1-10' -> (1, 10), '12.5' -> (12.5, 12.5).
    """
    if '-' in chapter_string:
        try:
            start, end = map(parse_chapter_number, chapter_string.split('-'))
            return min(start, end), max(start, end)
        except ValueError:
            raise argparse.ArgumentTypeError(f"La plage '{chapter_string}' est invalide. Utilisez le format 'début-fin', ex: 5-10.")
    else:
        try:
            chapter_num = parse_chapter_number(chapter_string)
            return chapter_num, chapter_num
        except ValueError:
            raise argparse.ArgumentTypeError(f"Le numéro de chapitre '{chapter_string}' doit être un nombre (ex: 5 ou 12.5).")
 

FORMATS = ["EPUB", "PDF", "CBZ", "CBR"]

def process_manga(manga: Manga, use_cache: bool = True) -> None:
    """Affiche les informations du manga puis demande la plage de chapitres et le format à télécharger."""
    if manga.manga_name is None:
        print("❌ Impossible de récupérer les informations du manga. Vérifiez l'URL ou le support du site.")
        return

    print("ℹ️ Informations trouvées :")
    manga.review()

    try:
        chapters_input = input("Entrez la plage de chapitres à télécharger (ex: '5' ou '1-10'): ")
        start_chapter, end_chapter = parse_chapter_range(chapters_input)

        format_input = input(f"Entrez le format de sortie ({', '.join(FORMATS)}) [EPUB]: ").upper() or "EPUB"
        if format_input not in FORMATS:
            print("⚠️ Format non valide. 'EPUB' sera utilisé par défaut.")
            format_input = "EPUB"

        print(f"▶️  Lancement du téléchargement des chapitres de {start_chapter} à {end_chapter} au format {format_input}...")

        if manga.download(start_chapter, end_chapter, format_input, use_cache):
            print("\n✅ Opération terminée avec succès.")
        else:
            print("\n❌ Une erreur est survenue durant l'opération.")

    except argparse.ArgumentTypeError as e:
        print(f"❌ Erreur: {e}")
    except KeyboardInterrupt:
        print("\n Opération annulée par l'utilisateur.")


def main():
    """
        Point d'entrée principal du script pour le téléchargement de mangas.
    """
    parser = argparse.ArgumentParser(
        description="Télécharge, convertit et sauvegarde des chapitres de manga depuis une URL ou via une recherche."
    )
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-u", "--url",
        type=str,
        help="L'URL de la page principale du manga."
    )
    group.add_argument(
        "-s", "--search",
        type=str,
        help="Le nom du manga à rechercher."
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Re-télécharge les images même si elles sont déjà dans le cache."
    )
     
    args = parser.parse_args()
     
    if args.url:
        print(f"▶️  Chargement du manga depuis : {args.url}")
        process_manga(Manga(args.url), use_cache=not args.no_cache)
    elif args.search:
        print(f"🔍 Recherche de '{args.search}'...")
        manga = Search_engine(args.search).Select_Manga()
        if manga:
            process_manga(manga, use_cache=not args.no_cache)
    else:
        # Affichage de l'aide si aucune option n'est fournie
        parser.print_help()

if __name__ == "__main__":
    main()
