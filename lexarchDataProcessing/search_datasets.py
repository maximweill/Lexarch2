import pandas as pd
import pickle
from collections import defaultdict


def load_data()->pd.DataFrame:
    df = pd.read_parquet("final_dataset.parquet")
    df.dropna(inplace=True)
    
    return df

def pronunciation_search(df: pd.DataFrame)->dict[str, dict[str, dict[str, int]]]:
    result = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

    for _, row in df.iterrows():
        word = row["Word"]
        prons = row["Pronunciation"]
        sylls = row["Syllables"]
        frequency = row["Frequency"]
        if len(prons) != len(sylls):
            continue

        for pron, syll in zip(prons, sylls):
            result[pron][syll][word] += frequency
            result[pron][syll]["_total"] += frequency
            result[pron]["_total"]["_"] += frequency

    return result

def spelling_search(df: pd.DataFrame)->dict[str, dict[str, list[str]]]:
    result = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

    for _, row in df.iterrows():
        word = row["Word"]
        prons = row["Pronunciation"]
        sylls = row["Syllables"]
        frequency = row["Frequency"]
        if len(prons) != len(sylls):
            continue

        for pron, syll in zip(prons, sylls):
            result[syll][pron][word] += frequency
            result[syll][pron]["_total"] += frequency
            result[syll]["_total"]["_"] += frequency

    return result

def freeze(d):
    if isinstance(d, defaultdict):
        d = {k: freeze(v) for k, v in d.items()}
    elif isinstance(d, dict):
        d = {k: freeze(v) for k, v in d.items()}
    return d

def main()->None:
    df = load_data()

    pron_search = pronunciation_search(df)
    pron_search = freeze(pron_search)
    with open("pronunciation_search.pkl", "wb") as f:
        pickle.dump(pron_search, f)

    spell_search = spelling_search(df)
    spell_search = freeze(spell_search)
    with open("spelling_search.pkl", "wb") as f:
        pickle.dump(spell_search, f)
    


if __name__ == "__main__":
    main()
