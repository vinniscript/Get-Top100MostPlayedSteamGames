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

    def scroll_to_load_all(self, loading_indicator_selector=(By.CLASS_NAME, 'search_infinite_scroll_throbber')):
        """Rola a página até que o indicador de "carregando mais conteúdo" desapareça."""
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        scroll_count = 0
        max_scrolls = 10  # Defina um máximo para evitar loops infinitos

        while scroll_count < max_scrolls:
            # Rola até o final da página
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            # Espera um pouco para o conteúdo carregar
            time.sleep(2)

            # Verifica se o indicador de carregamento ainda está presente
            try:
                loading_element = WebDriverWait(self.driver, 5).until(
                    EC.invisibility_of_element_located(loading_indicator_selector)
                )
                # Se o elemento ficou invisível, pode significar que mais conteúdo carregou ou não há mais para carregar
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    print("Fim do conteúdo carregado.")
                    break  # Não há mais conteúdo sendo carregado
                last_height = new_height
            except TimeoutException:
                # Se o indicador não for encontrado (desapareceu), esperamos um pouco mais e verificamos novamente
                time.sleep(1)
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    print("Indicador de carregamento não encontrado e altura da página inalterada.")
                    break
                last_height = new_height

            scroll_count += 1
            print(f"Scroll #{scroll_count} realizado.")

        print("Processo de scroll concluído.")

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
        """Coleta dados dos jogos da página de busca da Steam, rolando infinitamente."""
        all_game_data = set() # Usar um set para evitar duplicatas
        scroll_attempts = 0
        max_scroll_attempts = 10  # Número máximo de tentativas sem novos jogos
        loaded_count = 0

        try:
            self.driver.get(self.base_url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(self.game_container_selector)
            )

            while scroll_attempts < max_scroll_attempts:
                soup_before_scroll = BeautifulSoup(self.driver.page_source, 'html.parser')
                results_container_before = soup_before_scroll.find('div', id=self.game_container_selector[1])
                initial_game_count = 0
                if results_container_before:
                    game_links_before = results_container_before.find_all('a', class_=self.game_link_selector[1])
                    initial_game_count = len(game_links_before)
                    print(f"Número de jogos antes do scroll: {initial_game_count}")
                else:
                    print("Contêiner de resultados não encontrado antes do scroll.")
                    break

                # Rola até o final da página
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)  # Espera o conteúdo carregar

                soup_after_scroll = BeautifulSoup(self.driver.page_source, 'html.parser')
                results_container_after = soup_after_scroll.find('div', id=self.game_container_selector[1])
                current_game_data = []

                if results_container_after:
                    game_links = results_container_after.find_all('a', class_=self.game_link_selector[1])
                    new_games_loaded = False
                    for game_link in game_links:
                        url = self.get_game_url(game_link)
                        if url and not any(data['url'] == url for data in all_game_data):
                            description = self.get_game_description(url) if url else "Não pegou a descrição"
                            name = self.get_game_name(BeautifulSoup(str(game_link), 'html.parser'))

                            game_data = {
                                'name': name,
                                'description': description,
                                'url': url
                            }
                            current_game_data.append(game_data)
                            print(f"Coletados dados para: {name}, URL: {url[:50]}, Descrição: {description[:50]}")
                            new_games_loaded = True

                    if new_games_loaded:
                        all_game_data.extend(current_game_data)
                        scroll_attempts = 0  # Resetar as tentativas de scroll
                        print(f"Mais {len(current_game_data)} jogos carregados. Total coletados: {len(all_game_data)}")
                    else:
                        scroll_attempts += 1
                        print(f"Nenhum jogo novo carregado após o scroll ({scroll_attempts}/{max_scroll_attempts}).")

                else:
                    print("Contêiner de resultados não encontrado após o scroll.")
                    break  # Parar se não encontrar o contêiner

                # Verificar se chegamos ao final da página (você pode precisar adaptar essa lógica)
                current_height = self.driver.execute_script("return document.body.scrollHeight")
                previous_height = current_height  # Inicializa previous_height na primeira iteração
                time.sleep(1)
                if current_height == previous_height and scroll_attempts >= max_scroll_attempts - 1:
                    print("Possível fim da página.")
                    break
                previous_height = current_height  # Atualiza a altura anterior

            print(f"Coleta de dados concluída. Total de {len(all_game_data)} jogos coletados.")
            return all_game_data

        except Exception as e:
            print(f"Erro durante a coleta de dados infinita: {e}")
            return all_game_data

if __name__ == "__main__":

    # configuração do Selenium com Firefox
    service = FirefoxService(GeckoDriverManager().install())
    options = FirefoxOptions()
    #options.add_argument('--headless')  # Executa o Firefox em modo headless (sem interface gráfica)
    options.add_argument('--no-sandbox')
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
        print(f"\nNome: {game['name']},"
              f"\nDescrição: {game['description']},"
              f"\nURL: {game['url']},")




