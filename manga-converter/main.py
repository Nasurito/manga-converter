from module.manga import Manga

if __name__ == "__main__":
    test = Manga("https://mangakatana.com/manga/kaiju-no-8.24869")
    test.review()
    test.download_chapter(12)
    
    test = Manga("https://www.lelmanga.com/manga/jujutsu-kaisen")
    test.review()
    test.download_chapter(12)