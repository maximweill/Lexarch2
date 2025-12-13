import numpy as np
import json
import pandas as pd
import ast


with open("pronunciation_search.json", "r", encoding="utf-8") as f:
    pronunciation_search = json.load(f)

def load_spelling_pairs_with_syllables_data():
    """
    Load the word dataset CSV and convert string lists to actual lists.
    """
    # Path to your CSV
    csv_file = "miss_spellings/spelling_pairs_with_syllables.csv"

    # Load CSV
    words = pd.read_csv(csv_file)

    # Convert string representations of lists into actual Python lists
    words['Pronunciation'] = words['Pronunciation'].apply(ast.literal_eval)
    words['True_syllables'] = words['True_syllables'].apply(ast.literal_eval)
    words['Fake_syllables'] = words['Fake_syllables'].apply(ast.literal_eval)
    # Check the DataFrame
    return words
MS_spelling_pairs = load_spelling_pairs_with_syllables_data()

def find_incorrect_syllables():
    incorrect_syllables = []
    frequency_ratios = []
    for _, row in MS_spelling_pairs.iterrows():
        true_sylls = row["True_syllables"]
        fake_sylls = row["Fake_syllables"]
        true_pronunciation = row["Pronunciation"]
        incorrect_syll = []
        for true_syll, fake_syll, true_pron in zip(true_sylls, fake_sylls,true_pronunciation):
            if fake_syll != true_syll:
                incorrect_syll.append((true_syll,fake_syll))
                if true_pron in pronunciation_search: 
                    if true_syll in pronunciation_search[true_pron]:
                        if fake_syll in pronunciation_search[true_pron]:
                            frequency_ratios.append(
                                pronunciation_search[true_pron][fake_syll]["_total"] /
                                pronunciation_search[true_pron][true_syll]["_total"]
                            )
                        else:
                            frequency_ratios.append(0)
        incorrect_syllables += incorrect_syll
    return incorrect_syllables,frequency_ratios

incorrect_syllables_pairs,frequency_ratios_data = find_incorrect_syllables()

with open("frequency_ratios_data.json", "w", encoding="utf-8") as f:
    json.dump(frequency_ratios_data, f, ensure_ascii=False, indent=4)
with open("incorrect_syllables_pairs.json", "w", encoding="utf-8") as f:
    json.dump(incorrect_syllables_pairs, f, ensure_ascii=False, indent=4)

