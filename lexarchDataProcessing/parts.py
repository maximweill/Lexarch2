import pandas as pd
import ast
from load_files import load_word_data

# Create "Parts Database" for Si
# milarity Search (Exploded View)
def create_parts_database(df):
    if df.empty: return pd.DataFrame()
    rows = []
    for _, row in df.iterrows():
        word = row['Word']
        diff = row.get('Spelling Difficulty', 0)
        freq = row.get('Frequency', 1)
        # Safe eval
        syls = ast.literal_eval(row['Syllables']) if isinstance(row['Syllables'], str) else row['Syllables']
        prons = ast.literal_eval(row['Pronunciation']) if isinstance(row['Pronunciation'], str) else row['Pronunciation']
        
        if len(syls) == len(prons):
            for s, p in zip(syls, prons):
                rows.append([word, f"{s} ({p})", diff, freq])
                
    return pd.DataFrame(rows, columns=['Word', 'Signature', 'Difficulty', 'Frequency'])

def main():
    df = load_word_data("word_dataset_with_difficulties.csv")
    
    print("Creating Parts Database...")
    parts_df = create_parts_database(df)
    
    parts_df.to_csv("parts_database.csv", index=False, encoding="utf-8")

if __name__ == "__main__":
    main()