import requests
import json
import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv('.env')

# Carrega variáveis de ambiente
STEAM_API_KEY = os.getenv('STEAM_API_KEY')
if (STEAM_API_KEY is None):
    raise ValueError('STEAM_API_KEY não configurada')
else:
    print('STEAM_API_KEY carregada com sucesso.')

url = "https://api.steampowered.com/ISteamChartsService/GetMostPlayedGames/v1/"
params = {
    'key': STEAM_API_KEY
}

# Faz a requisição
response = requests.get(url, params=params)

# Verifica o status da requisição
if response.status_code == 200:
    data = response.json()
    print(data) # Exibe a resposta para depuração
else:
    print(f"Erro na requisição: {response.status_code}")
    print(response.text)
