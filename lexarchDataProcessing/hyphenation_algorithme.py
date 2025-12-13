from functools import wraps
from typing import Callable

hypenation_algorithms = []

def hyphenate(word:str)->list:
    CV_structure = [get_cvc(word)]
    hyphenation = [word]
    for algorithm in hypenation_algorithms:
        #print("---")
        hyphenation, CV_structure = hyphenate_each_syllable(
            hyphenation, CV_structure, algorithm=algorithm
        )
    return hyphenation

vowels = "AEIOUY"

def get_cvc(word:str)->str:
    """Return the CVC structure of the word as a list."""
    structure = ""
    for letter in word:
        if letter in vowels:
            structure += "V"
        else:
            structure += "C"
    return structure

def hyphenate_each_syllable(
        hyphenation:list[str],
        CV_structure:list[str],
        algorithm:Callable[[str, str],tuple[list[str], list[str]]]
        )->tuple[list[str],list[str]]:
    """Hyphenate each syllable based on its CV structure."""

    final_hyphenation = []
    final_CV_structure = []
    for syl, CV in zip(hyphenation, CV_structure):
        syl_hyph, syl_CV = algorithm(syl, CV)
        final_hyphenation+=syl_hyph
        final_CV_structure+=syl_CV
    return final_hyphenation, final_CV_structure

def hyphenation_decorator(func):
    @wraps(func)
    def wrapper(word:str, CV:str)->list:
        hyphenation, CV_structure = func(word, CV)
        hyphenation = [syl for syl in hyphenation if syl]  # Remove empty strings
        CV_structure = [syl for syl in CV_structure if syl]  # Remove empty strings
        #print(f"Applying {func.__name__} on word: {word} with CV: {CV} -> Hyphenation: {hyphenation}, CV_structure: {CV_structure}")
        return hyphenation, CV_structure
    hypenation_algorithms.append(wrapper)
    return wrapper

c_ends = {
    "SM",
    "THM"
}
@hyphenation_decorator
def consonant_endings(syl: str, CV: str):
    split_points = []

    for ends in c_ends:
        if syl.endswith(ends) and len(syl) > len(ends):
            split_points.append(len(syl) - len(ends))
            break

    hyphenation = slice_by_indices(syl, split_points)
    CV_structure = slice_by_indices(CV, split_points)

    return hyphenation, CV_structure

@hyphenation_decorator
def vR_(syl: str, CV: str):
    split_points = []
    for i in range(len(CV) - 2):
        if CV[i] == "V" and syl[i+1] == "R":
            if i+2 < len(CV) and (syl[i+2] == "R" or syl[i+2] == "E"):
                split_points.append(i + 3)
            else :
                split_points.append(i + 2)
    hyphenation = slice_by_indices(syl, split_points)
    CV_structure = slice_by_indices(CV, split_points)

    return hyphenation, CV_structure


valid_dithongs = {
    "AY","EY", #/ei/
    "AI", #/ai/
    "OW","OA", #/ou/
    "OI","OY", #/ɔi/
    "OU", #/au/,/ʊə/
    "EE","EA", #/ɪə/
    "AI","EA", #/eə/
    "IY","IE", #/i:/
    }
@hyphenation_decorator
def vvv_c(syl: str, CV: str):
    split_points = []
    for i in range(len(CV) - 3):
        if CV[i] == "V" and CV[i+1] == "V" and CV[i+2] == "V" and CV[i+3] == "C":
            if syl[i+1:i+3] in valid_dithongs:
                split_points.append(i + 1)
            elif syl[i:i+2] in valid_dithongs:
                split_points.append(i + 2)
    hyphenation = slice_by_indices(syl, split_points)
    CV_structure = slice_by_indices(CV, split_points)
    return hyphenation, CV_structure

@hyphenation_decorator
def vv_cv(syl: str, CV: str):
    split_points = []

    for i in range(len(CV) - 3):
        if CV[i] == "V" and CV[i+1] == "V" and CV[i+2] == "C" and CV[i+3] == "V":
            if syl[i:i+2] not in valid_dithongs:
                split_points.append(i + 2)

    hyphenation = slice_by_indices(syl, split_points)
    CV_structure = slice_by_indices(CV, split_points)

    return hyphenation, CV_structure


# ignore double consonant clusters that are valid only at start
#s2c = {"S"+ a for a in "PTKC"} #only valid at start
c2h = {"CH","SH","TH","PH","WH"}
valid_double_consonant_clusters = set({
    "CH","SH","TH","PH","WH",
    "CK","QU","NG",
    "BL", "BR",
    "CL", "CR",
    "DR",
    "FL", "FR",
    "GL", "GR",
    "PL", "PR",
    "TR","NC",
    "CK",
    })|{a+a for a in "BCFGHKLMNPQRSTVXYZ" 
    }|{a+"S" for a in "BCFGHKLMNPQRSTVXYZ" 
    }|c2h
valid_triple_consonant_clusters = set({
})|{a + "L" for a in c2h
    }|{a + "W" for a in c2h
    }|{a + "J" for a in c2h
    }|{"S" + a for a in c2h
    }|{a + "R" for a in valid_double_consonant_clusters}

@hyphenation_decorator
def fourConsonantClustersv(syl: str, CV: str):
    split_points = []
    # add virtual letters to start to catch initial clusters
    for i in range(len(CV) - 5):
        if CV[i] == "V" and CV[i+1] == "C" and CV[i+2] == "C" and CV[i+3] == "C" and CV[i+4] == "C" and CV[i+5] == "V":
            cluster = syl[i+1:i+5]
            if cluster[1:] in valid_triple_consonant_clusters:
                split_points.append(i + 2)

    hyphenation = slice_by_indices(syl, split_points)
    CV_structure = slice_by_indices(CV, split_points)

    return hyphenation, CV_structure

@hyphenation_decorator
def threeConsonantClustersv(syl: str, CV: str):
    split_points = []
    # add virtual letters to start to catch initial clusters
    for i in range(len(CV) - 4):
        if CV[i] == "V" and CV[i+1] == "C" and CV[i+2] == "C" and CV[i+3] == "C" and CV[i+4] == "V":
            cluster = syl[i+1:i+4]
            if cluster in valid_triple_consonant_clusters:
                split_points.append(i+1)
            elif cluster[1:] in valid_double_consonant_clusters:
                split_points.append(i + 2)
            elif cluster[:2] in valid_double_consonant_clusters:
                split_points.append(i + 3)
            elif "R" in cluster:
                split_points.append(i + cluster.index("R") + 2)

    hyphenation = slice_by_indices(syl, split_points)
    CV_structure = slice_by_indices(CV, split_points)

    return hyphenation, CV_structure

@hyphenation_decorator
def doubleConsonantClustersv(syl: str, CV: str):
    split_points = []
    # add virtual letters to start to catch initial clusters
    for i in range(len(CV) - 3):
        if CV[i] == "V" and CV[i+1] == "C" and CV[i+2] == "C" and CV[i+3] == "V":
            cluster = syl[i+1:i+3]
            ##print(f"Checking cluster: {cluster} in syllable: {syl}")
            if cluster in valid_double_consonant_clusters:
                split_points.append(i+1)
            elif cluster not in valid_double_consonant_clusters:
                split_points.append(i+2)
            elif "R" in cluster:
                split_points.append(i + cluster.index("R"))

    hyphenation = slice_by_indices(syl, split_points)
    CV_structure = slice_by_indices(CV, split_points)

    return hyphenation, CV_structure

@hyphenation_decorator
def v_cv(syl: str, CV: str):
    split_points = []

    for i in range(len(CV) - 2):
        if CV[i] == "V" and CV[i+1] == "C" and CV[i+2] == "V":
            if not(syl[i+2] == "E" and i+2 == len(syl)-1):  # E ending exception
                split_points.append(i + 1)

    hyphenation = slice_by_indices(syl, split_points)
    CV_structure = slice_by_indices(CV, split_points)

    return hyphenation, CV_structure

def slice_by_indices(text: str, indices: list[int]) -> list[str]:
    starts = [0] + indices
    ends = indices + [len(text)]
    return [text[s:e] for s, e in zip(starts, ends)]

def closed_compound_words(words: list[str],freq_dict) -> list[list[str]]:
    """Return closed compound words as [start, end], or [word] if none found."""
    result = []
    words_set = set(words)
    for word in words:
        compound = closed_compound_word(word, words_set, freq_dict)
        result.append(compound)
    return result

def closed_compound_word(word: str, words_set:set[str],freq_dict) -> list[str]:
    """Return closed compound word as [start, end], or [word] if none found."""
    # try all possible splits
    for i in range(1, len(word)):
        start = word[:i]
        end = word[i:]

        if start in words_set and end in words_set:
            ##print(f"Found compound word: {word} -> {start} + {end}")
            if freq_dict[start] > 30_000_000 and freq_dict[end] > 30_000_000:  # only accept if both parts are common words
                return [start, end]

    return [word]

def main()->None:
    # Example usage
    word = "BASARA".upper()
    hyphenation = hyphenate(word)
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
    #print(compound)

if __name__ == "__main__":
    main()
    #main_compound()