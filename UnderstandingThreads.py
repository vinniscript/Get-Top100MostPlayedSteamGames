import threading # Biblioteca para trabalhar com threads (execução paralela)
import time # Biblioteca para manipulação de tempo (como pausas)
from selenium import webdriver # Bibilioteca para controlar navegadores web
from selenium.webdriver.firefox.service import Service as FirefoxService # Serviço para o Firefox
from webdriver_manager.firefox import GeckoDriverManager # Gerenciador de drivers do Firefox
from selenium.webdriver.firefox.options import Options as FirefoxOptions # Opções para o Firefox
from selenium.webdriver.common.by import By # Módulo para localizar elementos na página
from bs4 import BeautifulSoup # Biblioteca para analisar o HTML

"""
game_urls_to_scrape = [
    "https://store.steampowered.com/app/730/CounterStrike_2/",
    "https://store.steampowered.com/app/578080/PUBG_BATTLEGROUNDS/",
    "https://store.steampowered.com/app/440/Team_Fortress_2/"
]
"""

def scrape_game_data(url, thread_id, results):
    """
      Função para coletar o nome de um jogo da Steam a partir de sua URL.
      Esta função será executada por uma thread separada.

      Args:
          url (str): A URL da página do jogo na Steam.
          thread_id (int): Um identificador único para a thread.
          results (list): Uma lista compartilhada para armazenar os resultados da coleta.
      """
    print(f"Thread {thread_id} iniciando a coleta para {url}")
    driver = None # Inicailiza o driver como one para podermos verificar se foi criado

    try:
        # Confiugrar o driver do Firefox para essa thread
        service = FirefoxService(GeckoDriverManager().install())
        options = FirefoxOptions()
        options.add_argument("--headless") # Executar sem interface gráfica (opcional)
        options.add_argument("--no-sandbox") # Desabilitar o sandbox (opcional), que é um recurso de segurança
        options.add_argument("--disable-dev-shm-usage") # Desabilitar o uso de memória compartilhada (opcional), serve para evitar problemas de memória em containers

        # Iniciar o driver do Firefox
        driver = webdriver.Firefox(service=service, options=options)
        driver.get(url)
        time.sleep(2) # Espera a página carregar (ajuste conforme necessário)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        name_element = soup.find('div', class_='apphub_AppName')

        if name_element:
            game_name = name_element.text.strip()
            print(f"thread {thread_id}: Nome do jogo encontrado em {url}: {game_name}")
            # Adicionar o resultado à lista compartilhada
            results.append({'url': url, 'name': game_name})
        else:
            print(f"Thread {thread_id}: Nome do jogo não encontrado em {url}")
    except Exception as e:
        print(f"Thread {thread_id}: Erro nao acesar {url}: {e}")

    finally:
        # Certificar-se de que o driver seja fechado, mesmo se ocorrer um erro
        if driver:
            driver.quit()
        print(f"Thread {thread_id}: Finalizou o processamento de {url}")

if __name__ == "__main__":
    results = [] # Lista para armazenar os resultados de todas as threads
    threads = [] # Lista para guardar os objetos das threads que criaremos

    # Criar e iniciar uma thread para cada URL na nossa lista
    for i, url in enumerate(game_urls_to_scrape):
        print(f"Url {i+1}: {url}")
        thread_id = i + 1 # Criar um ID único para cada thread
        # Criar um objeto Thread
        # target: especifica a função que a thread irá executar (scrape_game_data)
        # args: é uma tupla com os argumentos que serão passados para a função target
        thread = threading.Thread(target=scrape_game_data, args=(url, thread_id, results))
        threads.append(thread) # Adicionar a thread à nossa lista de threads
        thread.start()

        # Aguardar todas as threads terminarem sua execução
        for thread in threads: thread.join()

        # Após todas as threads terminarem, podemos processar os resultados
        print("\n--- Resultados da Coleta ---\n")
        if results:
            for item in results:
                print(  f"URL: {item['url']}, Nome {item['name']}")
        else:
            print("Nenhum dado de jogo foi coletado.")

        print("\n--- Coleta Concluída ---")

# O código está bom. Mas está lento. Vamos entrar num conceito de multiprocessamento, para utilizar mais de um núcleo do processador.

