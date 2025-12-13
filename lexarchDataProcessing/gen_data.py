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
    compound_lists = closed_compound_words(final_words,freq_dict)
    final_word_count = [freq_dict[w] for w in final_words]
    final_pronunciations_syllables = [
        [" ".join(syllable) for syllable in pronunciation_syllables(cmu_dict[word])] 
        if len(compound_list) == 1
        else list(
            chain.from_iterable(
                [" ".join(syllable) for syllable in pronunciation_syllables(cmu_dict[part])]
                for part in compound_list
                )
            )
        for word,compound_list in zip(final_words, compound_lists)
    ]
    final_syllables = [
        hyphenate(word) if len(compound_list) == 1
        else list(chain.from_iterable(hyphenate(part) for part in compound_list))
        for word,compound_list in zip(final_words, compound_lists)
    ]


    output_path = "final_dataset.csv"

    df = pd.DataFrame({
        "Word": final_words,
        #"Compound": compound_lists,
        "Pronunciation": final_pronunciations_syllables,
        "Syllables": final_syllables,
        "Frequency": final_word_count,
    })
    df = df[df["Pronunciation"].apply(len) == df["Syllables"].apply(len)] # remove rows where lengths don't match

    df.to_csv(output_path, index=False, encoding="utf-8")

    print(f"Saved {len(df)} words to {output_path}")
    print(f"Removed {len(final_words) - len(df)} words from {output_path}")


if __name__ == "__main__":
    main()