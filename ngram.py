import urllib.parse
import requests

def fetch_ngram_data(query, start_year=1800, end_year=2019, corpus=26, smoothing=3):
    """Fetches historical frequency data from Google Books Ngram Viewer."""
    try:
        query_encoded = urllib.parse.quote(query)
        url = f'https://books.google.com/ngrams/json?content={query_encoded}&year_start={start_year}&year_end={end_year}&corpus={corpus}&smoothing={smoothing}'
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except:
        return []