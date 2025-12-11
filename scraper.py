import requests
import urllib.parse
import matplotlib


matplotlib.use('Agg') 
import matplotlib.pyplot as plt

def runQuery(query, start_year=1800, end_year=2020, corpus=26, smoothing=3):
    """
    Scrapes data from Google Ngram Viewer using the method described by GeeksforGeeks.
    """
 
    query_encoded = urllib.parse.quote(query)
    

    url = (f'https://books.google.com/ngrams/json?content={query_encoded}'
           f'&year_start={start_year}&year_end={end_year}'
           f'&corpus={corpus}&smoothing={smoothing}')
    
    print(f"Fetching data for: {query}...")
    try:
        response = requests.get(url)
        response.raise_for_status() 
        output = response.json()
    except Exception as e:
        print(f"Error fetching data: {e}")
        return []

    return_data = []
    if not output:
        print("No data available for this Ngram.")
    else:
        for item in output:
    
            return_data.append((item['ngram'], item['timeseries']))
            
    return return_data

def plot_ngram_data(data, start_year, end_year):
    """
    Plots the scraped Ngram data using Matplotlib and saves it to a file.
    """
    if not data:
        print("Nothing to plot.")
        return


    years = list(range(start_year, end_year + 1))
    
    plt.figure(figsize=(12, 6))
    
    for name, timeseries in data:

        limit = min(len(years), len(timeseries))
        plt.plot(years[:limit], timeseries[:limit], label=name, linewidth=2)

    plt.title("Google Ngram Viewer Analysis", fontsize=16)
    plt.xlabel("Year", fontsize=12)
    plt.ylabel("Frequency (%)", fontsize=12)
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    

    output_filename = "ngram_chart.png"
    plt.savefig(output_filename)
    

if __name__ == "__main__":

    test_query = "Albert Einstein,Isaac Newton"
    data = runQuery(test_query)
    plot_ngram_data(data, 1800, 2020)