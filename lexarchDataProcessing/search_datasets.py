import pandas as pd
import json
from collections import defaultdict


def load_data()->pd.DataFrame:
    df = pd.read_csv("final_dataset.csv")
    df.dropna(inplace=True)
    for col in ("Pronunciation", "Syllables"):
        df[col] = df[col].apply(eval)
    
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
    
def main()->None:
    df = load_data()

    pron_search = pronunciation_search(df)
    with open("pronunciation_search.json", "w", encoding="utf-8") as f:
        json.dump(pron_search, f, ensure_ascii=False, indent=4)

    spell_search = spelling_search(df)
    with open("spelling_search.json", "w", encoding="utf-8") as f:
        json.dump(spell_search, f, ensure_ascii=False, indent=4)
    


if __name__ == "__main__":
    main()
