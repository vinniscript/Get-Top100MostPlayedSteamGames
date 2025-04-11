import UnderstandingThreads

from selenium import webdriver
from selenium.common import TimeoutException, NoSuchElementException
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.support.select import Select
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import json

class SteamGameDataCollector:
    def __init__(self):
        self.base_url = "https://store.steampowered.com/search/?sort_by=Relevance&max_pages=10"
        self.driver = self._setup_driver()
        self.all_game_data_threaded = []  # Lista compartilhada para os dados dos jogos
        self.data_lock = threading.Lock()  # Lock para proteger o acesso à lista

    def _setup_driver(self):
        service = FirefoxService(GeckoDriverManager(cache_valid_range=365).install())  # Cache por 365 dias
        options = FirefoxOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--headless') # Executar sem interface gráfica (opcional)
        return webdriver.Firefox(service=service, options=options)

    def bypass_age_gate_threaded(self, driver):
        try:
            day_select = Select(WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, 'ageDay'))
            ))
            day_select.select_by_value('1')

            month_select = Select(WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, 'ageMonth'))
            ))
            month_select.select_by_value('January')

            year_select = Select(WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, 'ageYear'))
            ))
            year_select.select_by_value('1990')

            view_page_button_selector = (By.ID, 'view_product_page_btn')
            try:
                view_page_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(view_page_button_selector)
                )
                view_page_button.click()
                print(f"Thread {threading.current_thread().name}: Página de idade bypassada.")
                return True
            except TimeoutException:
                view_page_button_selector_class = (By.CLASS_NAME, 'btnv6_blue_hoverfade')
                try:
                    view_page_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable(view_page_button_selector_class)
                    )
                    view_page_button.click()
                    print(f"Thread {threading.current_thread().name}: Página de idade bypassada (usando classe).")
                    return True
                except TimeoutException:
                    print(f"Thread {threading.current_thread().name}: Botão 'View Page' não encontrado.")
                    return False

        except NoSuchElementException:
            print(f"Thread {threading.current_thread().name}: Elementos de seleção de data não encontrados.")
            return False
        except Exception as e:
            print(f"Thread {threading.current_thread().name}: Erro ao bypassar idade: {e}")
            return False

    def get_game_urls(self):
        urls = set()
        try:
            self.driver.get(self.base_url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, 'search_resultsRows'))
            )
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            results_container = soup.find('div', id='search_resultsRows')
            if results_container:
                game_links = results_container.find_all('a', class_='search_result_row')
                for link in game_links:
                    url = link.get('href')
                    if url:
                        urls.add(url)
        except Exception as e:
            print(f"Erro ao coletar URLs: {e}")
        return list(urls)

    def process_game_url_threaded(self, url):
        game_data = {'name': None, 'description': None, 'url': url}
        try:
            driver = self._setup_driver()  # Criar um driver separado para cada thread (mais seguro)
            driver.get(url)
            if "agecheck" in driver.current_url:
                if self.bypass_age_gate_threaded(driver):  # Adaptar bypass para receber driver
                    time.sleep(2)
                else:
                    print(f"Falha ao bypassar a página de idade para {url} (thread).")
                    driver.quit()
                    return
            time.sleep(2)
            soup = BeautifulSoup(driver.page_source, 'html.parser')

            name_element = soup.find('div', class_='apphub_AppName')
            if name_element:
                game_data['name'] = name_element.text.strip()
                print(f"Thread {threading.current_thread().name}: Detalhes obtidos para: {game_data['name']} ({url})")

            desc_element = soup.find('div', class_='game_description_snippet')
            if desc_element:
                game_data['description'] = desc_element.text.strip()

            driver.quit()  # Fechar o driver da thread

            if game_data['name']:
                with self.data_lock:
                    self.all_game_data_threaded.append(game_data)

        except Exception as e:
            print(f"Thread {threading.current_thread().name}: Erro ao obter detalhes de {url}: {e}")

    def save_data(self, data_list, filename="steam_game_data_simple.json"):
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data_list, f, indent=4, ensure_ascii=False)
            print(f"Dados salvos em {filename}")
        except Exception as e:
            print(f"Erro ao salvar dados: {e}")

    def close_driver(self):
        if self.driver:
            self.driver.quit()

if __name__ == "__main__":
    collector = SteamGameDataCollector()
    game_urls = collector.get_game_urls()
    print(f"Encontradas {len(game_urls)} URLs de jogos.")

    threads = []
    for url in game_urls:
        thread = threading.Thread(target=collector.process_game_url_threaded, args=(url,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    collector.save_data(collector.all_game_data_threaded, filename="steam_game_data_threaded.json")
    collector.close_driver()