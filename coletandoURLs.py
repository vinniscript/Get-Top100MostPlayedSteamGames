from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.firefox.options import Options as FirefoxOptions
import time
from bs4 import BeautifulSoup
import csv

def get_firefox_driver(headless=True):
    try:
        driver_path = GeckoDriverManager().install()
        service = FirefoxService(executable_path=driver_path)
        options = FirefoxOptions()
        if headless:
            options.add_argument('--headless')
        return webdriver.Firefox(service=service, options=options)
    except Exception as e:
        print(f"Erro ao inicializar o Firefox Driver: {e}")
        return None

def get_game_data_from_steam_list(driver, num_scrolls=5, output_csv="steam_games_basic.csv"):
    """
    Função para coletar dados básicos de jogos da página de busca da Steam usando infinite scroll
    e salvar os resultados em um arquivo CSV (sem coleta de imagens).

    Args:
        driver: A instância do Selenium WebDriver já inicializada.
        num_scrolls (int): O número de vezes para rolar a página para carregar mais jogos.
        output_csv (str): O nome do arquivo CSV onde os dados serão salvos.
    """
    game_data = []
    search_url = "https://store.steampowered.com/search/?sort_by=Relevance"
    try:
        driver.get(search_url)
        time.sleep(5)

        for i in range(num_scrolls):
            print(f"Rolagem {i+1}...")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)

            soup = BeautifulSoup(driver.page_source, 'lxml')
            link_elements = soup.find_all('a', class_='search_result_row')

            for link in link_elements:
                url = link.get('href').split('?')[0] if link.get('href') else None
                title_element = link.find('span', class_='title')
                title = title_element.text.strip() if title_element else None
                platform_elements = link.find('div', class_='col search_name ellipsis').find_all('span', class_='platform_img')
                platforms = [p['class'][1] for p in platform_elements if len(p['class']) > 1]
                release_date_element = link.find('div', class_='col search_released responsive_secondrow')
                release_date = release_date_element.text.strip() if release_date_element else None
                price_element = link.find('div', class_='discount_final_price')
                price = price_element.text.strip() if price_element else None

                game_data.append({
                    'URL': url,
                    'Nome': title,
                    'Plataformas': ', '.join(platforms),
                    'Preço': price,
                    'Data_Lancamento': release_date
                })

            print(f"Número de jogos coletados após a rolagem {i+1}: {len(game_data)}")

        # Salvar os dados em CSV
        with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['URL', 'Nome', 'Plataformas', 'Preço', 'Data_Lancamento']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for data in game_data:
                writer.writerow(data)

        print(f"\nDados básicos dos jogos foram salvos em: {output_csv}")

    except Exception as e:
        print(f"Erro ao coletar dados básicos da página de busca da Steam: {e}")
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    driver = get_firefox_driver(headless=True)
    if driver:
        num_scrolls_to_perform = 20
        output_csv_file = "steam_games_basic.csv"
        get_game_data_from_steam_list(driver, num_scrolls_to_perform, output_csv_file)
    else:
        print("Falha ao inicializar o WebDriver.")