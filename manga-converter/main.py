import argparse

from module.search_engine import Search_engine
from module.manga import Manga

def parse_chapter_range(chapter_string: str) -> tuple[int, int]:
    """
    Analyse une chaîne de caractères représentant une plage de chapitres.
    Exemples: '5' -> (5, 5), '1-10' -> (1, 10).
     """
    if '-' in chapter_string:
        try:
            start, end = map(int, chapter_string.split('-'))
            return min(start, end), max(start, end)
        except ValueError:
            raise argparse.ArgumentTypeError(f"La plage '{chapter_string}' est invalide. Utilisez le format 'début-fin', ex: 5-10.")
    else:
        try:
            chapter_num = int(chapter_string)
            return chapter_num, chapter_num
        except ValueError:
            raise argparse.ArgumentTypeError(f"Le numéro de chapitre '{chapter_string}' doit être un entier.")
 

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
     
    args = parser.parse_args()
     
    if args.url:
        print(f"▶️  Chargement du manga depuis : {args.url}")
        manga = Manga(args.url)
        
        if manga.manga_name is None:
            print("❌ Impossible de récupérer les informations du manga. Vérifiez l'URL ou le support du site.")
            return

        print("ℹ️ Informations trouvées :")
        manga.review()
        
        try:
            chapters_input = input("Entrez la plage de chapitres à télécharger (ex: '5' ou '1-10'): ")
            start_chapter, end_chapter = parse_chapter_range(chapters_input)
            
            format_input = input("Entrez le format de sortie (PDF, EPUB, CBZ, CBR) [EPUB]: ").upper()
            if not format_input:
                format_input = "EPUB"
            
            if format_input not in ["EPUB", "PDF", "CBZ", "CBR"]:
                print("⚠️ Format non valide. 'EPUB' sera utilisé par défaut.")
                format_input = "EPUB"

            print(f"▶️  Lancement du téléchargement des chapitres de {start_chapter} à {end_chapter} au format {format_input}...")

            if format_input == 'EPUB':
                success = manga.download_chapter_to_epub(start_chapter, end_chapter)
            else:
                manga.download_chapters(start_chapter, end_chapter, format=format_input)
                success = True

            if success:
                print("\n✅ Opération terminée avec succès.")
            else:
                print("\n❌ Une erreur est survenue durant l'opération.")

        except argparse.ArgumentTypeError as e:
            print(f"❌ Erreur: {e}")
        except KeyboardInterrupt:
            print("\n Opération annulée par l'utilisateur.")
            
    elif args.search:
        print(f"🔍 Recherche de '{args.search}'...")
        engine = Search_engine(args.search)
        if engine:
            engine.Select_Manga()
    else:
        # Affichage de l'aide si aucune option n'est fournie
        parser.print_help()

if __name__ == "__main__":
    main()

