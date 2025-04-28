from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from bs4 import BeautifulSoup
import csv
import os

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

def get_game_data_from_steam_list_persistent_scroll(driver, output_csv="steam_games_basic.csv", progress_file="progress.txt", initial_wait=10, scroll_timeout=5, max_retry=5, retry_interval=60):
    game_data = []
    search_url = "https://store.steampowered.com/search/?sort_by=Relevance"
    collected_count = 0

    # Tentar carregar o progresso anterior
    if os.path.exists(progress_file):
        with open(progress_file, "r") as f:
            try:
                collected_count = int(f.readline().strip())
                print(f"Progresso anterior encontrado: {collected_count} jogos já coletados.")
            except ValueError:
                print("Arquivo de progresso inválido. Iniciando do zero.")

    try:
        driver.get(search_url)
        WebDriverWait(driver, initial_wait).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "search_result_row"))
        )
        print("Página de busca carregada.")

        initial_game_count = len(driver.find_elements(By.CLASS_NAME, "search_result_row"))
        num_scrolls = 0
        last_game_count = collected_count
        consecutive_fails = 0

        while consecutive_fails < max_retry:
            num_scrolls += 1
            print(f"Rolagem {num_scrolls} (Falhas consecutivas: {consecutive_fails})...")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            try:
                WebDriverWait(driver, scroll_timeout).until(
                    lambda d: len(d.find_elements(By.CLASS_NAME, "search_result_row")) > (initial_game_count if num_scrolls == 1 else last_game_count)
                )
                print("Novos jogos carregados.")
                consecutive_fails = 0 # Resetar o contador de falhas
            except:
                print(f"Nenhuma nova jogo carregado após a rolagem {num_scrolls}.")
                consecutive_fails += 1
                print(f"Tentativa {consecutive_fails} de {max_retry} falhou.")
                if consecutive_fails < max_retry:
                    print(f"Aguardando {retry_interval} segundos antes de tentar novamente.")
                    time.sleep(retry_interval)
                continue # Ir para a próxima iteração do loop

            soup = BeautifulSoup(driver.page_source, 'lxml')
            link_elements = soup.find_all('a', class_='search_result_row')
            current_game_count = len(link_elements)

            for link in link_elements[last_game_count:]:
                game_info = parse_game_row(link)
                if game_info and game_info['URL'] not in [d['URL'] for d in game_data]:
                    game_data.append(game_info)

            last_game_count = current_game_count
            print(f"Total de jogos coletados até agora: {len(game_data)}")

            # Salvar o progresso a cada lote
            with open(progress_file, "w") as f:
                f.write(str(len(game_data)))

        print("Número máximo de tentativas sem novos jogos atingido. Encerrando a coleta.")

        # Salvar os dados em CSV (isso acontecerá após o loop terminar)
        with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['URL', 'Nome', 'Plataformas', 'Preço', 'Data_Lancamento']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for data in game_data:
                writer.writerow(data)
        print(f"\nDados básicos dos jogos foram salvos em: {output_csv}")

    except Exception as e:
        print(f"Erro durante a coleta: {e}")
    finally:
        print("Fechando o driver.")
        driver.quit() # Fechar o driver apenas no final ou em caso de erro grave

def parse_game_row(link):
    url = link.get('href').split('?')[0] if link.get('href') else None
    title_element = link.find('span', class_='title')
    title = title_element.text.strip() if title_element else None
    platform_elements = link.find('div', class_='col search_name ellipsis').find_all('span', class_='platform_img')
    platforms = [p['class'][1] for p in platform_elements if len(p['class']) > 1]
    release_date_element = link.find('div', class_='col search_released responsive_secondrow')
    release_date = release_date_element.text.strip() if release_date_element else None
    price_element = link.find('div', class_='discount_final_price')
    price = price_element.text.strip() if price_element else None
    return {'URL': url, 'Nome': title, 'Plataformas': ', '.join(platforms), 'Preço': price, 'Data_Lancamento': release_date}

if __name__ == "__main__":
    driver = get_firefox_driver(headless=True) # Deixando headless=False para você ver o que acontece
    if driver:
        output_csv_file = "steam_games_basic.csv"
        progress_file = "progress.txt"
        get_game_data_from_steam_list_persistent_scroll(driver, output_csv_file, progress_file, initial_wait=10, scroll_timeout=5, max_retry=5, retry_interval=60)
    else:
        print("Falha ao inicializar o WebDriver.")