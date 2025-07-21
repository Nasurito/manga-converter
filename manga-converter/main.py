import time
from module.search_engine import Search_engine
from module.manga import Manga

if __name__ == "__main__":
    search_input = input("🔍 Quel manga recherchez-vous ? ")
    engine = Search_engine(search_input)


    #test = Manga("https://www.lelmanga.com/manga/one-piece")
    #test.review()
    #test.download_chapter_to_epub(1, 200)
    ##test.download_chapters(1,50,"CBR")