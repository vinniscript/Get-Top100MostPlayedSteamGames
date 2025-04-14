import multiprocessing
import time
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

def scrape_multiple_games(urls_to_process, process_id, results_queue):
    """
    Função para coletar dados de múltiplos jogos usando um único webdriver
    dentro de um processo separado.
    """
    print(f"Processo {process_id}: Iniciando o processamento de {len(urls_to_process)} URLs.")
    driver = None
    try:
        service = FirefoxService(GeckoDriverManager().install())
        options = FirefoxOptions()
        driver = webdriver.Firefox(service=service, options=options)

        for url in urls_to_process:
            print(f"Processo {process_id}: Coletando dados de {url}")
            driver.get(url)
            time.sleep(2)

            soup = BeautifulSoup(driver.page_source, 'lxml')  # Usando lxml como parser
            name_element = soup.find('div', class_='apphub_AppName')

            if name_element:
                game_name = name_element.text.strip()
                print(f"Processo {process_id}: Nome encontrado: {game_name}")
                results_queue.put({'url': url, 'name': game_name})
            else:
                print(f"Processo {process_id}: Nome não encontrado em {url}")
                results_queue.put({'url': url, 'name': None}) # Coloca um resultado com None para indicar falha

    except Exception as e:
        print(f"Processo {process_id}: Erro no processo: {e}")
        for url in urls_to_process: # Ainda coloca algo na fila para cada URL processada
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
    # for i in range(num_processes);
        # Este loop irá iterar sobre os números de - até num_processes - 1. Se num_processes for 3, o loop irá iterar sobre 0, 1 e 2.
        # Cada valor de i representará o índice do processo que estamos "criando" (na verdade, estamos cirando a lista de URLs para esse processo).
    # i * chunk_size;
        # Para cada valor de i, multiplicamos pelo tamanho de chunk_size. Isso nos dá índice de início do pedaço de URLs para o processo atual.
        # - Para i = 0, 0 * chunk_size = 0 (o primeiro pedaço começa no índice 0).
        # - Para i = 1, 1 * chunk_size = chunk_size (o segundo pedaço começa no índice chunk_size).
        # - Para i = 2, 2 * chunk_size = 2 * chunk_size (o terceiro pedaço começa no índice 2 * chunk_size).
    # (i + 1) * chunk_size;
        # Para cada valor de i, somamos 1 ao índice inicial e multiplicamos pelo tamanho do pedaço. Isso nos dá o índice final do pedaço de URLs para o processo atual.
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