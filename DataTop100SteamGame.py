import requests
import json
import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv('.env')

# Carrega variáveis de ambiente
STEAM_API_KEY = os.getenv('STEAM_API_KEY')
if STEAM_API_KEY is None:
    raise ValueError('STEAM_API_KEY não configurada')
else:
    print('Chave steam carregada com sucesso.')


url_most_played = "https://api.steampowered.com/ISteamChartsService/GetMostPlayedGames/v1/"
params_most_played = {
    'key': STEAM_API_KEY
}

# Faz a requisição
response_most_played = requests.get(url_most_played, params=params_most_played)

# Verifica o status da requisição
if response_most_played.status_code != 200:
    raise Exception(f"Erro na requisição dos jogos mais populares: {response_most_played.status_code}")

# Converte a resposta para JSON
data_most_played = response_most_played.json()

# Exibe a resposta
#print(json.dumps(data_most_played, indent=4, sort_keys=True)) # sort_keys serve para ordenar as chaves do json.

if 'response' in data_most_played and 'ranks' in data_most_played['response']:
    appids = [game['appid'] for game in data_most_played['response']['ranks']]
else:
    raise KeyError("A chave 'ranks' não foi encontrada na resposta da API.")

print(f"appids coletados {appids}")

# URL da API do appDetails
url_app_details = "https://store.steampowered.com/api/appdetails"

# Lista para armazenar os detalhes dos jogos
all_games_details = []

#Itera sobre cada appid e faz requisição para obter os resultados
for appid in appids:
    params_details = {
        'appids': appid,
        'key': STEAM_API_KEY
    }

    response_details = requests.get(url_app_details, params=params_details)

    if response_details.status_code == 200:
        game_details = response_details.json()
        all_games_details.append(game_details)
        print(f"Detalhes do appid {appid} coletados com suceso.")
    else:
        print(f"Erro ao coletar detalhes do appid {appid}: {response_details.status_code}")

# Salva tods os detalhes em um arquivo JSON
with open('detalhes_jogos.json', 'w', encoding='utf-8') as arquivo_json:
    json.dump(all_games_details, arquivo_json, ensure_ascii=False, indent=4)

print("Detalhes de todos os jogos salvos em 'detalhes_jogos.json")

