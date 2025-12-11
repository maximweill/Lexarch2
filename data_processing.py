import pandas as pd
import ast
import os

def load_word_data(filename="word_dataset_with_difficulties.csv"):
    # Look in current folder OR data/ folder
    if os.path.exists(filename):
        path = filename
    elif os.path.exists(os.path.join("data", filename)):
        path = os.path.join("data", filename)
    else:
        return pd.DataFrame() # Return empty if missing

    try:
        words = pd.read_csv(path)
        if 'Pronunciation' in words.columns:
            words['Pronunciation'] = words['Pronunciation'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
        if 'Syllables' in words.columns:
            words['Syllables'] = words['Syllables'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
        return words
    except Exception as e:
        print(f"Error loading words: {e}")
        return pd.DataFrame()

def load_search_csv(filename="search.csv"):
    # Look in current folder OR data/ folder
    if os.path.exists(filename):
        path = filename
    elif os.path.exists(os.path.join("data", filename)):
        path = os.path.join("data", filename)
    else:
        print(f"DEBUG: Could not find {filename} in current directory or data/ subdirectory.")
        return pd.DataFrame()

    try:
        df = pd.read_csv(path)
        # Apply the logic from your snippet
        if 'Frequency' in df.columns:
            df = df[df['Frequency'] >= 10_000_000]
            df["Show"] = df["Frequency"]**0.00001
        return df
    except Exception as e:
        print(f"Error loading search CSV: {e}")
        return pd.DataFrame()