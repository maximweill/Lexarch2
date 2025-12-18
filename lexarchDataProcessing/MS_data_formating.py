import pandas as pd
from hyphen import Hyphenator
from correct_hyphenation_DEPRECATED import corrected_hyph
MS = pd.read_parquet("spelling_pairs.parquet")

   
def load_word_data():
    """
    Load the word dataset CSV and convert string lists to actual lists.
    """
    # Path to your CSV
    p_file = "word_dataset_with_difficulties.parquet"

    # Load CSV
    words = pd.read_parquet(p_file)
    # Check the DataFrame
    return words
word_dataset = load_word_data()


h = Hyphenator('en_US') # more consistent with our dataset
MS = MS[MS["correct"].isin(word_dataset["Word"])]
MS = MS[~MS["incorrect"].isin(word_dataset["Word"])]

print(MS.head())


MS["Pronunciation"] = [word_dataset[word_dataset["Word"] == word]["Pronunciation"].values[0] for word in MS["correct"]]
MS["True_syllables"] = [word_dataset[word_dataset["Word"] == word]["Syllables"].values[0] for word in MS["correct"]]


def get_fake_syllables(incorrect, pronunciation):
    if not isinstance(incorrect, str) or not incorrect: # Some error
        return pd.NA
    hyph_syl = h.syllables(incorrect)
    hyph_syl = corrected_hyph(hyph_syl, pronunciation)
    if len(hyph_syl) != len(pronunciation): # considering this as a failure of the automatic hyphenator
        return pd.NA
    return hyph_syl

MS["Fake_syllables"] = [
    get_fake_syllables(incorrect, pronunciation)
    for incorrect, pronunciation in zip(MS["incorrect"], MS["Pronunciation"])
]
MS = MS.dropna()


MS.to_parquet("miss_spellings/spelling_pairs_with_syllables.parquet", index=False)
#print(errors)