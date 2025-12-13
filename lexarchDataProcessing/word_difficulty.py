import json
import pandas as pd
from search_datasets import load_data


def word_difficulty(from_sylls: list[str], to_sylls: list[str], search_dataset) -> float:
    syll_difficulties = []
    for from_syll,to_syll in zip(from_sylls,to_sylls):
        if from_syll not in search_dataset:
            syll_difficulties.append(1)
            continue
        if to_syll not in search_dataset[from_syll]:
            syll_difficulties.append(1)
            continue
        total = search_dataset[from_syll]["_total"]["_"]
        word_count = search_dataset[from_syll][to_syll]["_total"]
        difficulty = 1 - (word_count / total)
        syll_difficulties.append(difficulty)
    
    return sum(syll_difficulties) / len(syll_difficulties)

def add_difficulty_to_df(
        df: pd.DataFrame,
        search_dataset:dict[str, dict[str, dict[str, int]]],
        name:str,
        from_to:tuple[str, str]) -> pd.DataFrame:
    difficulties = []
    for _, row in df.iterrows():
        from_sylls = row[from_to[0]]
        to_sylls = row[from_to[1]]
        difficulty = word_difficulty(from_sylls, to_sylls, search_dataset)
        difficulties.append(difficulty)
    df[name] = difficulties
    return df

def main()->None:
    df = load_data()
    with open("spelling_search.json", "r", encoding="utf-8") as f:
        spelling_search = json.load(f)
    df = add_difficulty_to_df(df, spelling_search,"Reading Difficulty",("Syllables","Pronunciation"))

    with open("pronunciation_search.json", "r", encoding="utf-8") as f:
       pronunciation_search = json.load(f)
    df = add_difficulty_to_df(df, pronunciation_search,"Spelling Difficulty",("Pronunciation","Syllables"))

    df.to_csv("word_dataset_with_difficulties.csv", index=False)   

if __name__ == "__main__":
    main()