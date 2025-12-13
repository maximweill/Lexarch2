import os
import pandas as pd
import ast

def load_word_data(filename="lexarchDataProcessing/word_dataset_with_difficulties.csv"):
    # Look in current folder OR data/ folder
    if not os.path.exists(filename):
        print(f"DEBUG: Could not find {filename} in current directory.")
        return pd.DataFrame() # Return empty if missing

    try:
        words = pd.read_csv(filename)
        if 'Pronunciation' in words.columns:
            words['Pronunciation'] = words['Pronunciation'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
        if 'Syllables' in words.columns:
            words['Syllables'] = words['Syllables'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
        return words
    except Exception as e:
        print(f"Error loading words: {e}")
        return pd.DataFrame()