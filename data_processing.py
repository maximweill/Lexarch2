import pandas as pd
import ast
import os

def load_word_data(filename="lexarchDataProcessing/word_dataset_with_difficulties.parquet"):
    # Look in current folder OR data/ folder
    if not os.path.exists(filename):
        print(f"DEBUG: Could not find {filename} in current directory.")
        return pd.DataFrame() # Return empty if missing

    words = pd.read_parquet(filename)
    return words


def load_search_csv(filename="lexarchDataProcessing/search.parquet"):
    # Look in current folder OR data/ folder
    if not os.path.exists(filename):
        print(f"DEBUG: Could not find {filename} in current directory.")
        return pd.DataFrame() # Return empty if missing

    df = pd.read_parquet(filename)
    return df