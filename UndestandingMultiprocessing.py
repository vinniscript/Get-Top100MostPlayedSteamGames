import multiprocessing
import time
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

def get_firefox_driver():
    try:
        driver_path = GeckoDriverManager().install()
        service = FirefoxService(executable_path=driver_path)
        options = FirefoxOptions()
        #options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        return webdriver.Firefox(service=service, options=options)
    except Exception as e:
        print(f"Erro ai inicializar o Firefox Driver: {e}")
        return None

def bypass_age_gate(driver):
    try:
        if "agecheck" in driver.current_url:
            day_select = Select(WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, 'ageDay'))  # Correção: Uma única tupla como argumento
            ))
            day_select.select_by_value('1')

            month_select = Select(WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, 'ageMonth')) # Correção: Uma única tupla como argumento
            ))
            month_select.select_by_value('January')

            year_select = Select(WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, 'ageYear'))  # Correção: Uma única tupla como argumento
            ))
            year_select.select_by_value('1990')

            view_page_button_selector = (By.ID, 'view_product_page_btn')
            try:
                view_page_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(view_page_button_selector)
                )
                view_page_button.click()
                time.sleep(3) # Espera a página carregar após o clique
                print(f"Processo {multiprocessing.current_process().pid}: Página de idade bypassada.")
                return True
            except TimeoutException:
                view_page_button_selector_class = (By.CLASS_NAME, 'btnv6_blue_hoverfade')
                try:
                    view_page_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable(view_page_button_selector_class)
                    )
                    view_page_button.click()
                    print(f"Processo {multiprocessing.current_process().pid}: Página de idade bypassada (usando classe).")
                    return True
                except TimeoutException:
                    print(f"Processo {multiprocessing.current_process().pid}: Botão 'View Page' não encontrado.")
                    return False

        return True # Se não houver página de idade, retorna True
    except NoSuchElementException:
        print(f"Processo {multiprocessing.current_process().pid}: Elementos de seleção de data não encontrados.")
        return False
    except Exception as e:
        print(f"Processo {multiprocessing.current_process().pid}: Erro ao tentar bypassar a página de idade: {e}")
        return False

def atualizar_html_steam(shared_html):
    driver = get_firefox_driver() # Sua função para inicializar o driver
    if driver:
        try:
            driver.get("https://store.steampowered.com/?l=brazilian")
            time.sleep(5)
            while True:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(5) # Espera para carregar mais conteúdo
                shared_html.value = driver.page_source
                time.sleep(30) # Espera antes da próxima atualização (ajuste conforme necessário)
        except Exception as e:
            print(f"Erro no processo de atualização do HTML: {e}")
        finally:
            driver.quit()

def get_game_urls_from_steam_store(driver, num_scrolls=1):
    """
    Função para coletar URLs de jogos da página principal da Steam, rolando a página.

    Args:
        driver: A instância do Selenium WebDriver já inicializada.
        num_scrolls (int): O número de vezes para rolar a página para carregar mais jogos

    Returns:
        list: Uma lista de URLs de jogos encontradas na página de Steam.
    """

    game_urls = set()  # Usar um set par eivtar URLs duplicadas
    try:
        driver.get("https://store.steampowered.com/search/?sort_by=Relevance&max_pages=10")
        time.sleep(5) # Espera a página carregar

        for _ in range(num_scrolls):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3) # Espera para os novos elementos de jogos chegarem.

        soup = BeautifulSoup(driver.page_source, 'lxml')
        # Encontra os elementos 'a' que contém os links dos jogos.
        # A classe 'search_results_row' é comum em páginas de busca, mas na principal pode ser diferente.
        # Vamos tentar uma classe mais genérica que envolve os links dos jogos na página principal
        # Inspecione o HTML da página principal da Steam para encontrar a classe correta.
        link_elements = soup.find('a', class_='search_result_row') # Ajuda a pegar os links dos jogos

        for link in link_elements:
            href = link.get('href')
            if href and '/app/' in href:
                game_urls.add(href.split('?')[0])  # Adiciona a URL ao conjunto, removendo parâmetros extras
    except Exception as e:
        print(f"Erro ao coletar URLs da página da Steam: {e}")
    return list(game_urls)


def scrape_game_data(driver, url, process_id, results_queue):
    """Função para coletar o nome de um jogo da Steam a partir de sua URL."""
    print(f"    [Processo {process_id}]: Iniciando a coleta para {url}...")
    try:
        driver.get(url)
        time.sleep(5) # Espera a página carregar

        if "agecheck" in driver.current_url:
            if not bypass_age_gate(driver):
                print(f"    [Processo {process_id}]: Falha ao bypassar a página de idade para {url}.")
                results_queue.put({'url': url, 'name': None, 'error': 'Falha no bypass da idade'})
                return

            time.sleep(3)

        soup = BeautifulSoup(driver.page_sorce, 'lxml')
        name_element = soup.find('div', class_='apphub_AppName')

        if name_element:
            game_name = name_element.text.strip()
            print(f"    [Processo {process_id}]: Nome encontrado: {game_name}")
            results_queue.put({'url': url, 'name': game_name, 'error': None})
        else:
            print(f"    [Processo {process_id}]: Nome não encontrado em {url}")
            results_queue.put({'url': url, 'name': None, 'error': 'Nome não encontrado'})
    except (WebDriverException, TimeoutException) as e:
        print(f"    [Processo {process_id}]: Erro ao acessar ou interagir com {url}: {e}")
        results_queue.put({'url': url, 'name': None, 'error': str(e)})
    except Exception as e:
        print(f"    [Processo {process_id}]: Erro inesperado ao processar {url}: {e}")
        results_queue.put({'url': url, 'name': None, 'error': str(e)})

def scrape_multiple_games(urls_to_process, process_id, results_queue):
    """
    Função para coletar dados de múltiplos jogos com tratamento de erros aprimorado.
    """
    print(f"Processo {process_id}: Iniciando o processamento de {len(urls_to_process)} URLs.")
    driver = get_firefox_driver()
    if driver is None:
        print(f"Processo {process_id}: Falha ao inicializar o driver. Encerrando.")
        return

    try:
        for url in urls_to_process:
            print(f"Processo {process_id}: Coletando dados de {url}")
            try:
                driver.get(url)
                time.sleep(5)

                if "agecheck" in driver.current_url:
                    if not bypass_age_gate(driver):
                        print(f"Processo {process_id}: Falha ao bypassar a página de idade para {url}.")
                        results_queue.put({'url': url, 'name': None, 'error': 'Falha no bypass da idade'})
                        continue

                    time.sleep(3)

                soup = BeautifulSoup(driver.page_source, 'lxml')
                name_element = soup.find('div', class_='apphub_AppName')

                if name_element:
                    game_name = name_element.text.strip()
                    print(f"Processo {process_id}: Nome encontrado: {game_name}")
                    results_queue.put({'url': url, 'name': game_name, 'error': None})
                else:
                    print(f"Processo {process_id}: Nome não encontrado em {url}")
                    results_queue.put({'url': url, 'name': None, 'error': 'Nome não encontrado'})

            except (WebDriverException, TimeoutException) as e:
                print(f"Processo {process_id}: Erro ao acessar ou interagir com {url}: {e}")
                results_queue.put({'url': url, 'name': None, 'error': str(e)})
            except Exception as e:
                print(f"Processo {process_id}: Erro inesperado ao processar {url}: {e}")
                results_queue.put({'url': url, 'name': None, 'error': str(e)})

    finally:
        if driver:
            driver.quit()
        print(f"Processo {process_id}: Finalizou.")



if __name__ == "__main__":

    """    
        game_urls_to_scrape = [
        "https://store.steampowered.com/app/730/CounterStrike_2/",
        "https://store.steampowered.com/app/578080/PUBG_BATTLEGROUNDS/",
        "https://store.steampowered.com/app/440/Team_Fortress_2/",
        "https://store.steampowered.com/app/271590/Grand_Theft_Auto_V/",
        "https://store.steampowered.com/app/1086940/Baldurs_Gate_3/"
    ]
    """

    num_processes = 3 # Número de processos a serem criados, ajuste conforme necessário e seu computer aguentar
    results_queue = multiprocessing.Queue()
    processes = []

    # Inicializa o driver principal para coletar as URLs
    driver_for_urls = get_firefox_driver()
    if driver_for_urls is None:
        print("Falha ao inicializar o driver para coletar URLs. Encerrando.")
    else:
        # Coleta as URLs dos jogos da página da Steam
        game_urls_to_scrape = get_game_urls_from_steam_store(driver_for_urls, num_scrolls=2)
        driver_for_urls.quit() # Fecha o driver após coletar a URLs

        if game_urls_to_scrape:
            chunk_size = len(game_urls_to_scrape) // num_processes + (1 if len(game_urls_to_scrape) % num_processes else 0)
            url_chunks = [game_urls_to_scrape[i * chunk_size:(i + 1) * chunk_size] for i in range(num_processes)]

            for i, urls in enumerate(url_chunks):
                process_id = i
                process = multiprocessing.Process(target=scrape_multiple_games, args=(urls, process_id, results_queue))
                processes.append(process)
                process.start()

            for process in processes:
                process.join()

            print("\n--- Resultados da coleta (de múltiplos jogos por processo) ---")
            all_results = []
            while not results_queue.empty():
                result = results_queue.get()
                if result and 'name' in result:
                    print(f"URL: {result['url']}, Nome: {result['name']}")
                elif result and 'error' in result:
                    print(f"URL: {result['url']}, Erro: {result['error']}")
                else:
                    print(f"URL: {result['url']}, Resultado desconhecido. {result}")

            print("\n--- Fim da execução ---")
        else:
            print("Nenhuma URL de jogo encontrada na página da steam")