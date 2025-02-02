# Exemple d'utilisation
if __name__ == "__main__":
    url = "https://www.example.com"
    response = get_page(url)
    if response:
        print("Page fetched successfully:", response.status_code)
