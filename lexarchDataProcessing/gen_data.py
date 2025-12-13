import csv
from phonotactics import pronunciation_syllables
from correct_hyphenation_DEPRECATED import corrected_hyph, get_closed_compound_words
import json
from hyphenation_algorithme import hyphenate

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
    hyph_dict = {word:hyphenate(word) for word in cmu_dict} #parse_hyphenation("hyphenation/mhyph.txt")

    # -----------------------------
    # Keep only words present in all datasets
    # -----------------------------
    acronyms_dict = parse_cmu("cmu/acronym-0.7b")
    all_words_set = (set(cmu_dict) & set(freq_dict) & set(hyph_dict)) - set(acronyms_dict)
    closed_compound_words = get_closed_compound_words(hyph_dict, set(all_words_set))
    all_words_set = all_words_set - set(closed_compound_words)


    # -----------------------------
    # Build final parallel lists
    # -----------------------------
    final_words = sorted(all_words_set)
    final_pronunciations = [cmu_dict[w] for w in final_words]
    final_word_count = [freq_dict[w] for w in final_words]
    final_pronunciations_syllables = [[" ".join(syllable) for syllable in pronunciation_syllables(pron)] for pron in final_pronunciations]
    final_syllables = [corrected_hyph(hyph_dict[w], pronunciation) for w,pronunciation in zip(final_words,final_pronunciations_syllables)]


    # -----------------------------
    # Save datasets
    # -----------------------------
    print(f"Removed {len(closed_compound_words)} closed compound words")
    with open("closed_compound_words.json", "w", encoding="utf-8") as f:
        json.dump(closed_compound_words, f, indent=2)
    

    output_path = "final_dataset.csv"
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        # Write header
        writer.writerow(["Word", "Pronunciation", "Syllables", "Frequency"])
        
        # Write rows
        for word, pron_syl, syl, freq in zip(final_words, final_pronunciations_syllables, final_syllables, final_word_count):
            # Join pronunciation and syllables lists as space-separated strings
            writer.writerow([word, pron_syl, syl, freq])

    print(f"Saved {len(final_words)} words to {output_path}")


if __name__ == "__main__":
    main()