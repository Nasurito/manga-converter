from module.manga import Manga

if __name__ == "__main__":
    test = Manga("https://www.lelmanga.com/manga/kaiju-no-8")
    test.review()
    test.download_chapters(1,50,"CBR")
    print(test.convert_to_epub())
