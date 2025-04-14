import multiprocessing
import time
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
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

def scrape_multiple_games(urls_to_process, process_id, results_queue):
    """
    Função para coletar dados de múltiplos jogos usando um único webdriver
    dentro de um processo separado. Com bypass de página de idade.
    """
    print(f"Processo {process_id}: Iniciando o processamento de {len(urls_to_process)} URLs.")
    driver = get_firefox_driver()
    if driver is None:
        print(f"Processo {process_id}: Falha ao inicializar o driver. Encerrando.")
        return

    try:
        for url in urls_to_process:
            print(f"    [{process_id}]: Coletando dados de {url}...")
            driver.get(url)
            time.sleep(5)

            if "agecheck" in driver.current_url:
                if not bypass_age_gate(driver):
                    print(f"    Processo {process_id}: Falha ao bypassar a página de idade para {url}.")
                    continue

                    time.sleep(5) # Espera a página carregar após o bypass

            soup = BeautifulSoup(driver.page_source, 'lxml') # Usando lxml como parser
            name_element = soup.find('div', class_='apphub_AppName')

            if name_element:
                game_name = name_element.text.strip()
                print(f"Processo {process_id}: Nome do jogo encontrado: {game_name}")
                results_queue.put({'url': url, 'name': game_name})
            else:
                print(f"Processo {process_id}: Nome de jogo não encontrado em {url}")
                results_queue.put({'url': url, 'name': None})

    except Exception as e:
        print(f"Processo {process_id}: Erro no processo: {e}")
        for url in urls_to_process:
            results_queue.put({'url': url, 'name': None})
    finally:
        if driver:
            driver.quit()
        print(f"Processo {process_id}: Finalizou.")



if __name__ == "__main__":
    game_urls_to_scrape = [
        "https://store.steampowered.com/app/730/CounterStrike_2/",
        "https://store.steampowered.com/app/578080/PUBG_BATTLEGROUNDS/",
        "https://store.steampowered.com/app/440/Team_Fortress_2/",
        "https://store.steampowered.com/app/271590/Grand_Theft_Auto_V/",
        "https://store.steampowered.com/app/1086940/Baldurs_Gate_3/"
    ]
    num_processes = 3 # Número de processos a serem criados, ajuste conforme necessário e seu computer aguentar

    # Pega o total de URLs e aplica uma divisão inteira '//' do número de URLs pelo número de processos, por exemplo
    # 10 URLs e 3 processos, o resultado é 3, então cada processo vai pegar 3 URLs.
    chunk_size = len(game_urls_to_scrape) // num_processes + (1 if len(game_urls_to_scrape) % num_processes else 0)
    # len(game_urls_to_scrape) % num_processes else 0); Calcula o resto da divisão o número total de URLs pelo número de processos '&'
    # Isso no diz se há alguma URL "sobrando", ou seja, que não foi distruibuída igualmente, como no caso hipotético acima.
    # No nosso exemplo de 10 URLs e 3 processos, o chunk_size seria 3 + 1 = 4. Isso significa que alguns processos receberão 4 URLs e outros receberão 3 (a divisão não é perfeitamente igual).

    # Divide as URLs em partes iguais para cada processo.
        # Muito complexo para continuar a explicar via comentários, mas basicamente é o mesmo que o anterior, só que agora estamos pegando o índice final do pedaço de URLs para o processo atual.
        # Procure IAs
    url_chunks = [game_urls_to_scrape[i * chunk_size:(i + 1) * chunk_size] for i in range(num_processes)]

    results_queue = multiprocessing.Queue()
    processes = []

    for i, urls in enumerate(url_chunks):
        process_id = i
        process = multiprocessing.Process(target=scrape_multiple_games, args=(urls, process_id, results_queue))
        processes.append(process)
        process.start()

    for process in processes:
        process.join()

    print("\n--- Resultados da Coleta (de múltiplos jogos por processo) ---")
    all_results = []
    while not results_queue.empty():
        result = results_queue.get()
        if result and 'name' in result: # Verifica se o resultado é válido e tem a chave 'name'
            all_results.append(result)

    if all_results:
        for item in all_results:
            print(f"URL: {item['url']}, Nome: {item['name']}")
    else:
        print("Nenhum dado de jogo foi coletado com sucesso.")

    print("\n--- Fim da Execução ---")