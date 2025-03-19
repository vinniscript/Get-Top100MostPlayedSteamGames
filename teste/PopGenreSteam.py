import requests

url = "https://steamspy.com/api.php"

def get_top_genre_games(genres_, top_n = 10):
    genre_ranking = {}

    for genre in genres_:
        # Busca jogos por gêneros
        response = requests.get(
            url,
            params={"request": "genre", "genre": genre}
        )
        if response.status_code == 200:
            games = response.json()
            print(games)

            # Converte o dicionário para uma lista e ordena por 'ownwers' (popularidade)
            games_list = list(games.values())
            sorted_games = sorted(
                games_list,
                key=lambda x: x.get('owners', 0),
                reverse=True
            )[:top_n] # Pega os top_n jogos mais populares

            genre_ranking[genre] = sorted_games

    return genre_ranking

# Lista de gêneros (exemplos - ajuste confome necessário)
genres = ["action", "adventure", "rpg", "strategy", "simulation"]

# Obtém os top 10 jogos de cada gênero
top_genre_games = get_top_genre_games(genres, top_n=10)

# Exibe os resultados
for genre, games in top_genre_games.items():
    print(f"\n--- Top {len(games)} {genre} Games ---")
    for idx, game in enumerate(games, 1):
        print(f"{idx}. {game['name']} (Owners: {game['owners']})")

# Pegar os top 10 GÊNEROS mais famosos que retornam na loja da steam

