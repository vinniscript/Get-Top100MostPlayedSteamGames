import threading
from queue import Queue
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import csv

# Configurações
OUTPUT_FILE = "steam_game_details.csv"
URLS_FILE = "game_urls.txt"

def get_firefox_driver(headless=True):
    firefox_options = FirefoxOptions()
    if headless:
        firefox_options.add_argument("-headless")
    service = FirefoxService(GeckoDriverManager().install())
    driver = webdriver.Firefox(service=service, options=firefox_options)
    return driver


def collect_game_details(url):
    driver = None
    game_data = {'URL': url}
    print(f"Coletando dados de: {url}")
    try:
        driver = get_firefox_driver(headless=True)
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "apphub_AppName"))
        )

        # Nome
        game_data['Nome'] = driver.find_element(By.CLASS_NAME, "apphub_AppName").text.strip()

        # Preço
        try:
            game_data['Preco'] = driver.find_element(By.CLASS_NAME, "discount_final_price").text.strip()
        except:
            try:
                game_data['Preco'] = driver.find_element(By.CLASS_NAME, "game_purchase_price").text.strip()
            except:
                game_data['Preco'] = "N/A"

        # Data de Lançamento
        try:
            release_date_element = driver.find_element(By.CLASS_NAME, "release_date")
            date_element = release_date_element.find_element(By.CLASS_NAME, "date")
            game_data['Data_Lancamento'] = date_element.text.strip()
        except:
            game_data['Data_Lancamento'] = "N/A"

        # Plataformas
        platforms = []
        try:
            platform_elements = driver.find_elements(By.CSS_SELECTOR,
                                                     ".game_area_purchase_platform span, .game_area_purchase_platform img")
            for element in platform_elements:
                platform = element.text.strip() or element.get_attribute('alt')
                if platform:
                    platforms.append(platform)
            game_data['Plataformas'] = ", ".join(platforms)
        except:
            game_data['Plataformas'] = "N/A"

        # Descrição
        try:
            game_data['Descricao'] = driver.find_element(By.CSS_SELECTOR, "#game_area_description").text.replace(
                "ABOUT THIS GAME", "").strip()
        except:
            game_data['Descricao'] = "N/A"

        # Avaliações
        try:
            reviews_filter_options = driver.find_element(By.ID, "reviews_filter_options")

            # Avaliações Totais
            all_reviews_element = reviews_filter_options.find_element(By.CSS_SELECTOR,
                                                                      'label[for="review_type_all"] .user_reviews_count')
            game_data['Avaliacoes_Total'] = all_reviews_element.text.strip('()').replace(',',
                                                                                         '')  # Remove os parênteses e vírgulas

            # Avaliações Positivas
            positive_reviews_element = reviews_filter_options.find_element(By.CSS_SELECTOR,
                                                                           'label[for="review_type_positive"] .user_reviews_count')
            game_data['Avaliacoes_Positivas'] = positive_reviews_element.text.strip('()').replace(',',
                                                                                                  '')  # Remove os parênteses e vírgulas

        except:
            game_data['Avaliacoes_Total'] = "0"
            game_data['Avaliacoes_Positivas'] = "0"

        print(f"Dados coletados de: {url}")

    except Exception as e:
        print(f"Erro ao coletar dados de {url}: {e}")
    finally:
        if driver is not None:
            driver.quit()
    return game_data

def main():
    urls = ["https://store.steampowered.com/app/1501750/Lords_of_the_Fallen/"]  # Use apenas uma URL para teste

    for url in urls:
        game_details = collect_game_details(url)
        if game_details:
            print("\nDetalhes do Jogo:")
            for key, value in game_details.items():
                print(f"  {key}: {value}")

if __name__ == "__main__":
    main()