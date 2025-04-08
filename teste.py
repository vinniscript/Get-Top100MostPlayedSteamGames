from selenium import webdriver
from selenium.common import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import  Options as FirefoxOptions
from selenium.webdriver.support.select import Select
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import re

class SteamGameDataCollector:
    def __init__(self, driver):
        self.driver = driver
        self.base_url = 'https://store.steampowered.com/search/'
        self.game_container_selector = (By.ID, 'search_resultsRows')
        self.game_link_selector = (By.CLASS_NAME, 'search_result_row')
        self.game_title_selector = (By.CLASS_NAME, 'title')
        self.review_summary_selector = (By.CLASS_NAME, 'search_review_summary')
        self.image_container_selector = (By.ID, 'highlight_strip_scroll')
        self.movie_image_selector = (By.CLASS_NAME, 'movie_thumb')
        self.screenshot_image_selector = (By.CLASS_NAME, 'highlight_strip_screenshot')
        self.game_description_selector = (By.CLASS_NAME, 'game_description_snippet')

    def bypass_age_gate(self, driver):
        try:
            # Seleciona uma data de nascimento que seja maior que 18 anos atrás
            day_select = Select(WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, 'ageDay'))
            ))
            day_select.select_by_value('1') # Seleciona o dia 1

            month_select = Select(WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, 'ageMonth'))
            ))
            month_select.select_by_value('January') # Seleciona o mês de janeiro

            year_select = Select(WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, 'ageYear'))
            ))
            # Seleciona um ano que seja maior que 18 anos atrás
            year_select.select_by_value('1990')

            # Agora é preciso encontrar o botão do "View page"
            # Inspecione o HTML da página real para encontrar o seletor correto para o botão
            view_page_button_selector = (By.ID, 'view_product_page_btn')
            try:
                view_page_button = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(view_page_button_selector)
                )
                view_page_button.click()
                print("Página de confirmação de idade bypassada.")
                return True
            except TimeoutException:
                # Se o ID não funcionar, tente encontrar por classe ou outro seletor
                view_page_button_class = (By.CLASS_NAME, 'btnv6_blue_hoverfade') # Exemplo de classe
                try:
                    view_page_button_class = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located(view_page_button_class)
                    )
                    view_page_button = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located(view_page_button_class)
                    )
                    view_page_button.click()
                    print("Página de confirmação de idade bypassada (usando a classe).")
                    return True
                except TimeoutException:
                    print("Botão 'View Page' não encontrado.")
                    return False

        except NoSuchElementException:
                print("Elementos de seleção de data de nascimento não encontrados")
                return False
        except Exception as e:
            print(f"Erro ao tentar contornar a página de confirmação de idade: {e}")
            return False


    def get_game_name(self, soup):
        """Extrai o nome do jogo do elemento BeautifulSoup."""
        title_span = soup.find('span', class_=self.game_title_selector[1])
        return title_span.text.strip() if title_span else None

    def get_game_url(self, game_element):
        """Extrai a lista de IDs de gênero da string do atributo."""
        return game_element.get('href')

    def _extract_genre_ids(self, tag_ids_str):
        """Extrai a lista de IDs de gênero da string do atributo."""
        if tag_ids_str:
            match = re.search(r'\[(.*?)\', tag_ids_str')
            if match:
                ids_str = match.group(1)
                return [int(id.strip()) for id in ids_str.split(',') if id.strip()]
        return []

    def get_game_description(self, game_url):
        description = None
        try:
            self.driver.get(game_url)
            if "agecheck" in self.driver.current_url:
                if self.bypass_age_gate(self.driver):
                    time.sleep(3)  # Espera a página do jogo carregar após bypass
                    soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                    description_element = soup.find('div', class_=self.game_description_selector[1])
                    if description_element:
                        description = re.sub(r'\s+', ' ', description_element.text).strip()
                        print(f" Descrição coletada: {description[:50]}...")
                    else:
                        print(f" Elemento de descrição não encontrado em {game_url}")
                else:
                    print(f" Falha ao bypassar a página de confirmação de idade para {game_url}")
                    return None
            else:
                # Se não houver agecheck, tenta coletar a descrição normalmente
                time.sleep(3)
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                description_element = soup.find('div', class_=self.game_description_selector[1])
                if description_element:
                    description = re.sub(r'\s+', ' ', description_element.text).strip()
                    print(f" Descrição coletada: {description[:50]}...")
            return description
        except Exception as e:
            print(f" Erro ao acessar ou analisar a página do jogo ({game_url}): {e}")
            return None

    #def _extract_review_data(self, tooltip_html):


    def SCRAP_RESULT(self):
        """Coleta dados dos jogos da página de busca da Steam."""
        game_data_list = []
        try:
            self.driver.get(self.base_url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(self.game_container_selector)
            )
            soup_busca = BeautifulSoup(self.driver.page_source, 'html.parser')
            results_container = soup_busca.find('div', id=self.game_container_selector[1])

            if results_container:
                game_links = results_container.find_all('a', class_=self.game_link_selector[1])
                for game_link in game_links:
                    url = self.get_game_url(game_link)
                    description = self.get_game_description(url) if url else "Não pegou a descrição"
                    # Crie um BeautifulSoup separado para cada link
                    soup_jogo = BeautifulSoup(str(game_link), 'html.parser')
                    name = self.get_game_name(soup_jogo)

                    game_data = {
                        'name': name,
                        'description': description,
                        'url': url
                    }
                    game_data_list.append(game_data)
                    print(f"Coletados dados para: {name}")

            else:
                print("Nenhum resultado encontrado na página de busca.")
        except Exception as e:
            print(f"Erro ao acessar a página de busca: {e}")
        return game_data_list

if __name__ == "__main__":

    # configuração do Selenium com Firefox
    service = FirefoxService(GeckoDriverManager().install())
    options = FirefoxOptions()
    options.add_argument('--headless')  # Executa o Firefox em modo headless (sem interface gráfica)
    #options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    # inicializa o driver do Firefox
    driver = webdriver.Firefox(service=service, options=options)

    # Coleta de informação
    Steam = SteamGameDataCollector(driver)
    game_data = Steam.SCRAP_RESULT()

    # Fecha o driver
    driver.quit()

    # Exibe os dados coletados
    for game in game_data:
        print(f"\nNome: {game['name']}")



