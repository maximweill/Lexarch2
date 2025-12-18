import json

hypenation_algorithms = []

def hyphenate(word:str,pronunciation:list[str])->list:
    if len(pronunciation) == 1:
        return [word] # no need to hyphenate single-syllable words
    hyphenation = hyphenate_with_phoneme_pairs(word,pronunciation)
    return hyphenation

def hyphenate_with_phoneme_pairs(word:str,pronunciation:list[str])->list[str]:
    hyphenation = []
    remaining_word = word
    skip_first = 0
    for cur_s,next_s in zip(pronunciation,pronunciation[1:]):
        search_text = remaining_word[skip_first:]
        #print(f"Processing phoneme pair '{cur_s}' -> '{next_s}' in {search_text}")
        syll_end = cur_s.split(" ")[-1]
        next_start = next_s.split(" ")[0]
        combined_indices = find_combined_phoneme_indices(syll_end,next_start,search_text)
        if combined_indices:
            min_index = min(ind for ind, _ in combined_indices) # find most early split
            hyphenation.append(remaining_word[:min_index+skip_first])
            remaining_word = remaining_word[min_index+skip_first:]

            if len(next_s.split(" ")) > 1:
                skip_first = sorted((skip for (ind, skip) in combined_indices if ind == min_index))[0] #use the shortest grapheme length to skip
            else:
                skip_first = 0
            #print(f"> Found grapheme pair for phonemes at index {min_index}, skipping next {skip_first}, hyphenation now: {hyphenation} + {remaining_word}")
        else:
            search_text = remaining_word # desperate attempt without skipping
            skip_first = 0
            #print(f"> No grapheme pair found for phonemes '{cur_s}' -> '{next_s}' in '{search_text}'")
            if len(cur_s.split(" ")) > 1: # could be an implied phoneme at end
                syll_end = cur_s.split(" ")[-2] 
                next_start = next_s.split(" ")[0]
                #print(f"  Trying implied phoneme at end '{syll_end}' -> '{next_start}'")
                combined_indices = find_combined_phoneme_indices(syll_end,next_start,search_text)
                if combined_indices:
                    #print(f"> Found grapheme pair for implied phonemes at end '{syll_end}' -> '{next_start}'")
                    min_index = min(ind for ind, _ in combined_indices) # find most early split
                    hyphenation.append(remaining_word[:min_index+skip_first])
                    remaining_word = remaining_word[min_index+skip_first:]

                    if len(next_s.split(" ")) > 1:
                        skip_first = sorted((skip for (ind, skip) in combined_indices if ind == min_index))[0] #use the shortest grapheme length to skip
                    else:
                        skip_first = 0 # start and end phoneme are done by the same grapheme
                else:
                    if len(next_s.split(" ")) > 1: # could be an implied phoneme at start (Ex: w)
                        syll_end = cur_s.split(" ")[-1] 
                        next_start = next_s.split(" ")[1]
                        #print(f"> Trying implied phonemes at start '{syll_end}' -> '{next_start}'")
                        combined_indices = find_combined_phoneme_indices(syll_end,next_start,search_text)
                        if combined_indices:
                            #print(f"> Found grapheme pair for implied phonemes at end '{syll_end}' -> '{next_start}'")
                            min_index = min(ind for ind, _ in combined_indices) # find most early split
                            hyphenation.append(remaining_word[:min_index+skip_first])
                            remaining_word = remaining_word[min_index+skip_first:]

                            if len(next_s.split(" ")) > 1:
                                skip_first = sorted((skip for (ind, skip) in combined_indices if ind == min_index))[0] #use the shortest grapheme length to skip
                            else:
                                skip_first = 0 # start and end phoneme are done by the same grapheme
                        else:
                            #print("X no implied phoneme found at start, stopping hyphenation")
                            break
            else:
                if len(next_s.split(" ")) > 1: # could be an implied phoneme at start (Ex: w)
                    syll_end = cur_s.split(" ")[-1] 
                    next_start = next_s.split(" ")[1]
                    combined_indices = find_combined_phoneme_indices(syll_end,next_start,search_text)
                    if combined_indices:
                        #print(f"> Found grapheme pair for implied phonemes at end '{syll_end}' -> '{next_start}'")
                        min_index = min(ind for ind, _ in combined_indices) # find most early split
                        hyphenation.append(remaining_word[:min_index+skip_first])
                        remaining_word = remaining_word[min_index+skip_first:]

                        if len(next_s.split(" ")) > 1:
                            skip_first = sorted((skip for (ind, skip) in combined_indices if ind == min_index))[0] #use the shortest grapheme length to skip
                        else:
                            skip_first = 0 # start and end phoneme are done by the same grapheme
                    else:
                        #print("X no implied phoneme found at start, stopping hyphenation")
                        break


    hyphenation.append(remaining_word)
    return hyphenation

def find_combined_phoneme_indices(syll_end:str, next_start:str, search_text:str)->tuple[list[int], list[int]]:
    graphemes_end,lengths_end = find_phoneme_indices(syll_end,search_text)
    end_indices = [ind+length for ind,length in zip(graphemes_end,lengths_end)]
    graphemes_next_start,lengths_next_start = find_phoneme_indices(next_start,search_text)
    start_indices = graphemes_next_start
    combined_indices = [(ind, length) for (ind, length) in zip(start_indices,lengths_next_start) if ind in end_indices]
    return combined_indices


with open("phoneme2grapheme.json","r",encoding="utf-8") as f:
    phoneme2grapheme = json.load(f)  
def find_phoneme_indices(phoneme:str,word:str)->tuple[list[int], list[int]]:
    graphemes_indices = []
    graphemes_lengths = []
    for grapheme in phoneme2grapheme[phoneme]:
        indices = [i for i in range(len(word)) if word.startswith(grapheme, i)]
        if indices:
            graphemes_indices.extend(indices)
            graphemes_lengths.extend([len(grapheme)] * len(indices))

    return graphemes_indices, graphemes_lengths

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
            ##print(f"Found compound word: {word} -> {start} + {end}")
            frequencies = (freq_dict[start],freq_dict[end])
            if max(frequencies) > 15_000_000 and min(frequencies) > 1_000_000:  # only accept if both parts are common words
                return [start, end]

    return [word]

def main()->None:
    # Example usage
    word,pronunciation = 'EVENTUALLY',['IH', 'V EH N', 'CH AH', 'W AH', 'L IY']
    hyphenation = hyphenate(word,pronunciation)
    #print(f"Hyphenation for '{word}': {hyphenation}")
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
    ##print(compound)

if __name__ == "__main__":
    main()
    #main_compound()