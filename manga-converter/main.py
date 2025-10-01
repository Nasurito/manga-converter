import time
from module.search_engine import Search_engine
from module.manga import Manga

if __name__ == "__main__":
   
    """
    search_input = input("🔍 Quel manga recherchez-vous ? ")
    engine = Search_engine(search_input)
    if engine != None:
        engine.Select_Manga()
    """
    

    test = Manga("https://www.lelmanga.com/manga/shuumatsu-no-valkyrie")
    test.review()
    test.download_chapter_to_epub(1, 5)
    #test.download_chapters(1,50,"CBR")