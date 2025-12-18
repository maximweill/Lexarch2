import pandas as pd
from phonotactics import pronunciation_syllables
from hyphenation_algorithme import hyphenate,closed_compound_words
from itertools import chain

# -----------------------------
# Parsing functions (return dictionaries)
# -----------------------------
def parse_cmu(path:str)->dict:
    """Return a dict: word -> pronunciation list"""
    data = {}
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.upper()
            parts = line.strip().split("  ")
            if len(parts) != 2:
                continue
            word, pron = parts
            if not word.isalpha():
                continue
            data[word] = pron.lstrip().split(" ")
    return data


def parse_common_words(path:str)->dict:
    """Return a dict: word -> frequency count"""
    data = {}
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.upper()
            parts = line.strip().split(",")
            if len(parts) != 2:
                continue
            word, count = parts
            if not word.isalpha() or not count.isnumeric():
                continue
            data[word] = int(count)
    return data


def parse_hyphenation(path:str)->dict:
    """Return a dict: word -> hyphenation list"""
    data = {}
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.upper()
            word = line.strip().replace("�", "")
            if not word.isalpha():
                continue
            data[word] = line.strip().split("�")
    return data


def main()->None:
    # -----------------------------
    # Load data as dictionaries
    # -----------------------------
    cmu_dict = parse_cmu("cmu/cmudict-0.7b")
    freq_dict = parse_common_words("frequency/unigram_freq.csv")
    # -----------------------------
    # Keep only words present in all datasets
    # -----------------------------
    acronyms_dict = parse_cmu("cmu/acronym-0.7b")
    all_words_set = (set(cmu_dict) & set(freq_dict)) - set(acronyms_dict)

    # -----------------------------
    # Build final parallel lists
    # -----------------------------
    final_words = sorted(all_words_set)
    singles_dict,compound_dict = closed_compound_words(final_words,freq_dict)
    final_word_count = [freq_dict[w] for w in final_words]
    final_pronunciations_syllables_dict = {}
    for word,_ in singles_dict.items():
        final_pronunciations_syllables_dict[word] = [" ".join(syllable) for syllable in pronunciation_syllables(cmu_dict[word])]
    for word,compound_list in compound_dict.items():
        final_pronunciations_syllables_dict[word] = list(
        chain.from_iterable(
            final_pronunciations_syllables_dict[part]
            for part in compound_list
            )
        )
    final_pronunciations_syllables = [final_pronunciations_syllables_dict[word] for word in final_words]
    
    final_syllables_dict = {}
    for word,_ in singles_dict.items():
        final_syllables_dict[word] = hyphenate(word, final_pronunciations_syllables_dict[word])
    for word,compound_list in compound_dict.items():
        final_syllables_dict[word] = list(
        chain.from_iterable(
            final_syllables_dict[part]
            for part in compound_list
            )
        )
    final_syllables = [final_syllables_dict[word] for word in final_words]

    df = pd.DataFrame({
        "Word": final_words,
        "Compound": [compound_dict[word] if word in compound_dict else [word] for word in final_words],
        "Pronunciation": final_pronunciations_syllables,
        "Syllables": final_syllables,
        "Frequency": final_word_count,
    })
    matching_length_mask = df["Pronunciation"].apply(len) == df["Syllables"].apply(len)
    incorrect = df[~matching_length_mask] # remove rows where lengths don't match
    correct = df[matching_length_mask] # remove rows where lengths don't match

    correct.to_parquet("final_dataset.parquet", index=False)
    incorrect.to_parquet("incorrect_rows.parquet", index=False)

    print(f"Saved {len(correct)}, incorrect {len(incorrect)} rows.")


if __name__ == "__main__":
    main()