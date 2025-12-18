import json
from phonotactics import phoneme_dict

hypenation_algorithms = []

def hyphenate(word:str,pronunciation:list[str])->list:
    if len(pronunciation) == 1:
        return [word] # no need to hyphenate single-syllable words
    hyphenation = hyphenate_with_pronunciation(word,pronunciation)
    return hyphenation

with open("phoneme2grapheme.json","r",encoding="utf-8") as f:
    phoneme2grapheme = json.load(f)
def hyphenate_with_pronunciation(word:str,pronunciation:list[str])->list:
    hyphenation = hyphenate_with_phoneme_end(word,pronunciation)
    if len(hyphenation) != len(pronunciation): # try the other direction if lengths don't match
        hyphenation = hyphenate_with_phoneme_start(word,pronunciation)
    return hyphenation

def hyphenate_with_phoneme_start(word:str,pronunciation:list[str])->list[str]:
    word = word[::-1]  # reverse the word for easier processing
    pronunciation = [pron[::-1] for pron in pronunciation[::-1]]  # reverse the pronunciation list and each phoneme
    reversed_hyphenation = hyphenate_with_phoneme_end(word,pronunciation,flip_dict=True)
    hyphenation = [syl[::-1] for syl in reversed_hyphenation[::-1]]  # reverse back the syllables and their order
    return hyphenation


def hyphenate_with_phoneme_end(word:str,pronunciation:list[str],flip_dict:bool=False)->list[str]:
    hyphenation = [word]
    for pron in pronunciation[:-1]:
        #print(f"Processing phoneme '{pron}' for hyphenation...")
        phoneme = pron.split(" ")[-1][::-1] if flip_dict else pron.split(" ")[-1]
        #print(f"--Hyphenating with phoneme '{phoneme}' on word part '{hyphenation[-1]}'--")
        graphemes_indices = find_phoneme_indices(phoneme,hyphenation[-1],flip_dict=flip_dict)
        minimums = [min(indices) if indices else float('inf') for indices in graphemes_indices]
        min_index = min(minimums)
        length_of_min_index = (len(minimums) - 1) - minimums[::-1].index(min_index)
        if min_index != float('inf'):
            hyphenation = hyphenation[:-1] + slice_by_indices(hyphenation[-1],[min_index+(length_of_min_index+1)])
            #print(f"--> Found grapheme for phoneme '{phoneme}' at index {min_index}, hyphenation now: {hyphenation}")
    hyphenation = [syl for syl in hyphenation if syl]
    return hyphenation
        
def find_phoneme_indices(phoneme:str,word:str,flip_dict:bool=False)->list[list[int]]:
    graphemes_indices = [[] for _ in range(4)]

    for grapheme in phoneme2grapheme[phoneme]:
        grapheme = grapheme[::-1] if flip_dict else grapheme
        index = word.find(grapheme)
        if index != -1:
            #print(f"> Found grapheme '{grapheme}' for phoneme '{phoneme}' in word '{word}' at index {index}")
            graphemes_indices[len(grapheme)-1].append(index)

    #print(f"Grapheme indices for phoneme '{phoneme}' in word '{word}': {graphemes_indices}")
    return graphemes_indices



def slice_by_indices(text: str, indices: list[int]) -> list[str]:
    starts = [0] + indices
    ends = indices + [len(text)]
    return [text[s:e] for s, e in zip(starts, ends)]

def closed_compound_words(words: list[str], freq_dict) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """Return closed compound words as fully expanded components, or [word] if none found."""
    words_set = set(words)

    # Step 1: compute direct compounds
    direct = {}
    for word in words:
        direct[word] = closed_compound_word(word, words_set, freq_dict)

    expanded = {}
    singles = {}

    def expand(word, seen=None):
        if seen is None:
            seen = set()
        if word in seen:
            return [word]  # safety against cycles
        if word in expanded:
            return expanded[word]

        seen.add(word)
        parts = direct[word]

        if len(parts) == 1:
            result = parts
        else:
            result = []
            for part in parts:
                if part in direct:
                    result.extend(expand(part, seen))
                else:
                    result.append(part)

        expanded[word] = result
        return result

    # Step 2: expand everything
    for word in words:
        result = expand(word)
        if len(result) == 1:
            singles[word] = result
        else:
            expanded[word] = result

    compounds = {w: expanded[w] for w in expanded if len(expanded[w]) > 1}
    return singles, compounds


suffixes_that_are_words = { #lol they are all words...weird
    "ING", "NESS", "MENT", "TION", "ITY",
    "FUL", "LESS", "ABLE", "IBLE", "IZE", "ISE","HER"
}
def closed_compound_word(word: str, words_set:set[str],freq_dict) -> list[str]:
    """Return closed compound word as [start, end], or [word] if none found."""
    # try all possible splits
    for i in range(1, len(word)):
        start = word[:i]
        end = word[i:]
        if end in suffixes_that_are_words or len(end) <= 2 or len(start) <=2:
            continue # skip splits where the end is a common suffix
        if start in words_set and end in words_set:
            #print(f"Found compound word: {word} -> {start} + {end}")
            frequencies = (freq_dict[start],freq_dict[end])
            if max(frequencies) > 15_000_000 and min(frequencies) > 1_000_000:  # only accept if both parts are common words
                return [start, end]

    return [word]

def main()->None:
    # Example usage
    word,pronunciation = 'ABBREVIATE',['AH', 'B R IY', 'V IY', 'EY T']
    hyphenation = hyphenate_with_phoneme_end(word,pronunciation)
    print(f"Hyphenation for '{word}': {hyphenation}")
    hyphenation = hyphenate_with_phoneme_start(word,pronunciation)
    print(f"Hyphenation for '{word}': {hyphenation}")
def main_compound()->None:
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
    
    freq_dict = parse_common_words("frequency/unigram_freq.csv")
    words = set(freq_dict.keys())
    compound = closed_compound_word("HOMEOWNER", words, freq_dict)
    #print(compound)

if __name__ == "__main__":
    main()
    #main_compound()