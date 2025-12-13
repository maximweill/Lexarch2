import json
import pandas as pd
import numpy as np

def json_to_csv_pronunciation(json_file: str, csv_file: str) -> None:
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    rows = []
    for pron, syll_dict in data.items():
        for syll, word_dict in syll_dict.items():
            if syll == "_total":
                continue
            for word, freq in word_dict.items():
                if word == "_total":
                    continue
                rows.append({
                    "Pronunciation": pron,
                    "Syllables": syll,
                    "Word": word,
                    "Frequency": freq,
                    "Show": np.log(freq/10_000_000 + 1)
                })

    df = pd.DataFrame(rows)
    df.to_csv(csv_file, index=False, encoding="utf-8")

def main():
    json_to_csv_pronunciation("pronunciation_search.json", "search.csv")

if __name__ == "__main__":
    main()
