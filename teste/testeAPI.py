import requests

def get_current_players(appid):
    url = f"https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?appid={appid}"
    response = requests.get(url)
    data = response.json()
    return data["response"]["player_count"]

# Exemplo para CS:GO (appid=730)
print(get_current_players(730))  # Retorna algo como 452230

appid = 292030  # The Witcher 3
response = requests.get(f"https://steamspy.com/api.php?request=appdetails&appid={appid}")
data = response.json()
print("Estimativa de owners de", data['name'], data["owners"])

