import requests

def download_steam_html(url, filename='steam_page.html'):
    try:
        response = requests.get(url)
        response.raise_for_status() # Lança uma exceção para códigos de status HTTP 4xx/5xx

        with open(filename, 'w' , encoding='utf-8') as f:
            f.write(response.text)

        print(f"GTML da página '{url} salvo com sucesso em '{filename}")
    except requests.exceptions.RequestException as e:
        print(f"Erro ao baixar a páginar '{url}': {e}")

if __name__ == '__main__':
    steam_url_to_download = "https://store.steampowered.com/search/?sort_by=Relevance&max_pages=1"
    output_filename = "steam_search_page.html"
    download_steam_html(steam_url_to_download, output_filename)