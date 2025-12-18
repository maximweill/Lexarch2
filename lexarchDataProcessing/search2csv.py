import pickle
import pandas as pd
import numpy as np

def dict_to_parquet_pronunciation(pkl: str, parquet_file: str) -> None:
    with open(pkl, "rb") as f:
        data = pickle.load(f)
    
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
                    "Show": np.log(freq*10 + 1)
                })

    df = pd.DataFrame(rows)
    df.to_parquet(parquet_file, index=False)

def main():
    dict_to_parquet_pronunciation("pronunciation_search.pkl", "search.parquet")

if __name__ == "__main__":
    main()
