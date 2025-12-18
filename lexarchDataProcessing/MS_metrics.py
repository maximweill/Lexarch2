import pickle
import pandas as pd


with open("pronunciation_search.pkl", "rb") as f:
    pronunciation_search = pickle.load(f)

def load_spelling_pairs_with_syllables_data():
    """
    Load the word dataset CSV and convert string lists to actual lists.
    """
    # Path to your CSV
    csv_file = "miss_spellings/spelling_pairs_with_syllables.parquet"

    # Load CSV
    words = pd.read_parquet(csv_file)
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

with open("frequency_ratios_data.pkl", "wb") as f:
    pickle.dump(frequency_ratios_data, f)
with open("incorrect_syllables_pairs.pkl", "wb") as f:
    pickle.dump(incorrect_syllables_pairs, f)
