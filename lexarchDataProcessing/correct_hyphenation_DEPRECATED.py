from functools import wraps
from typing import Callable
from phonotactics import phoneme_dict

pure_consonants = "BCDFGHJKLMNPQSTVWXZ" # R,Y can behave like a vowel

from functools import wraps
from typing import Callable

def not_one_syllable(func: Callable) -> Callable:
    """Decorator to skip processing for one-syllable words."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # assume the first positional argument is hyphenation
        hyphenation = args[0] if args else kwargs.get("hyphenation", [])
        hyphenation = [syllable for syllable in hyphenation if syllable != ""]
        if len(hyphenation) <= 1:
            return hyphenation
        
        # replace hyphenation in args/kwargs before calling original function
        if args:
            new_args = (hyphenation, *args[1:])
            return func(*new_args, **kwargs)
        kwargs["hyphenation"] = hyphenation
        return func(**kwargs)
    
    return wrapper


@not_one_syllable
def group_double_consonants(hyphenation:list[str])->list[str]:
    """Detect if there are double consonants between syllables."""
    i=0
    while i<len(hyphenation)-1:
        if hyphenation[i][-1] == hyphenation[i+1][0]:
            if hyphenation[i][-1] in pure_consonants:
                hyphenation[i+1] = hyphenation[i][-1] + hyphenation[i+1]
                hyphenation[i] = hyphenation[i][:-1]
            elif hyphenation[i][-1] in ["R"]: 
                hyphenation[i] = hyphenation[i] + hyphenation[i+1][0]
                hyphenation[i+1] = hyphenation[i+1][1:]
        if "" in hyphenation:
            hyphenation = [syllable for syllable in hyphenation if syllable != ""]
            # do not increment i, as the list has changed
        else:
            i += 1
    return hyphenation

@not_one_syllable
def correct_suffix(hyphenation:list[str])->list[str]:
    """Detect if the syllable is a common suffix starting with a vowel."""
    noun_suffixes = { #with a vowel start
        "AGE","AL","ANCE","ENCE",
        "ERY","ITY","ORY","OUS",
        "EE","ER","OR","ISM","IST",
        "ENT","Y","ION","EST"
    }
    adj_suffixes = { #with a vowel start
        "ABLE","IBLE","AL","UL","EN","ESE","I","IC","ISH","IVE","IAN","OUS","IOUS"
    }
    verb_suffixes = { #with a vowel start
        "ATE","EN","IFY","ISE","IZE","ED","ING"
    }
    adverb_suffixes = set() #none start with vowel
    suffixes = noun_suffixes|adj_suffixes|verb_suffixes|adverb_suffixes


    last_syllable = hyphenation[-1]
    pre_last_syllable = hyphenation[-2]
    if last_syllable in suffixes and pre_last_syllable[-1] in pure_consonants:
        if pre_last_syllable.endswith("GH"):
            last_syllable = "GH" + last_syllable
            pre_last_syllable = pre_last_syllable[:-2]
        else:
            last_syllable = pre_last_syllable[-1] + last_syllable
            pre_last_syllable = pre_last_syllable[:-1]
        
        hyphenation[-2] = pre_last_syllable
        hyphenation[-1] = last_syllable
    return hyphenation

def corrected_hyph(hyphenation:list[str],pronunciation:list[str])->list[str]:
    """Apply hyphenation corrections to the entire hyphenation dictionary."""

    hyphenation = correct_suffix(hyphenation)
    hyphenation = group_double_consonants(hyphenation)
    hyphenation = correct_vowel_r(hyphenation, pronunciation)
    hyphenation = correct_NG(hyphenation, pronunciation)
    hyphenation = correct_single_vowel_syllables(hyphenation, pronunciation)
    return hyphenation

@not_one_syllable
def correct_vowel_r(hyphenation:list[str],pronunciation:list[str])->list[str]:
    for i,(pron,hyph,hyph_next) in enumerate(zip(pronunciation, hyphenation,hyphenation[1:])):
        if "" in (pron,hyph,hyph_next):
            continue
        if pron.endswith("R") and not hyph.endswith("R") : #there is a missing r at the end
            if hyph_next.startswith("R"): # the hyphenation is wrong
                hyphenation[i+1] = hyph_next[1:]
                hyphenation[i] = hyph + "R"
        elif not pron.endswith("R") and hyph.endswith("R"): #there is am extra r at the end
            if not hyph_next.startswith("R"): # the hyphenation is wrong
                hyphenation[i+1] = "R"+hyph_next
                hyphenation[i] = hyph[:-1]
    return hyphenation

@not_one_syllable
def correct_NG(hyphenation: list[str], pronunciation: list[str]) -> list[str]:
    hyphenation = hyphenation.copy()  # avoid mutating original
    n = len(hyphenation)
    
    for i, (pron, hyph) in enumerate(zip(pronunciation, hyphenation)):
        # NG at end
        if pron.endswith("NG"):
            if hyph.endswith("N") and i + 1 < n and hyphenation[i+1].startswith("G"):
                hyphenation[i] = hyph + "G"
                hyphenation[i+1] = hyphenation[i+1][1:]
            elif not hyph.endswith("NG") and i + 1 < n and hyphenation[i+1].startswith("NG"):
                hyphenation[i] = hyph + "NG"
                hyphenation[i+1] = hyphenation[i+1][2:]
        
        # NG at start
        if pron.startswith("NG"):
            if hyph.startswith("G") and i - 1 >= 0 and hyphenation[i-1].endswith("N"):
                hyphenation[i] = "N" + hyph
                hyphenation[i-1] = hyphenation[i-1][:-1]
            elif not hyph.startswith("N") and i - 1 >= 0 and hyphenation[i-1].endswith("NG"):
                hyphenation[i] = "NG" + hyph
                hyphenation[i-1] = hyphenation[i-1][:-2]
    
    hyphenation = [h for h in hyphenation if h]  # remove empty strings
    return hyphenation

@not_one_syllable
def correct_single_vowel_syllables(hyphenation:list[str],pronunciation:list[str])->list[str]:
    for i,(pron,hyph) in enumerate(zip(pronunciation,hyphenation)):
        if pron in phoneme_dict: # must be a valid phoneme
            new_hyphenation = hyph
            for letter in hyph[::-1]:
                if letter in pure_consonants:
                    if i+1 < len(hyphenation): #next syllable exists
                        new_hyphenation = new_hyphenation[:-1]
                        hyphenation[i+1] = letter + hyphenation[i+1]
            hyphenation[i] = new_hyphenation
    return hyphenation
            

def get_closed_compound_words(hyph_dict:dict,actually_words:set)->dict:
    """Remove closed compound words from hyphenation dictionary."""
    exceptions = [
        "EST",
        "A",
        "I",
    ]


    closed_compound_words = {}
    for word, hyphenation in hyph_dict.items():
        # we only need to classify words that we consider real
        if word not in actually_words:
            continue

        # A word is a closed compound if every syllable is a real word (or exception)
        is_compound = (
            len(hyphenation) >= 2 and
            all((syll in actually_words) and (syll not in exceptions)
                for syll in hyphenation)
        )

        if is_compound:
            closed_compound_words[word] = hyphenation

    return closed_compound_words

def main()->None:
    hyph = correct_vowel_r(['COM', 'PA', 'RA', 'TOR'],['K AH M', 'P AE R', 'AH', 'T ER'])
    print(hyph)
    ng = correct_NG(['SING', 'ER'],['S IH', 'NG ER'])
    print(ng)
    single = correct_single_vowel_syllables(['AB', 'OUT'],['AH', 'B AW T'])
    print(single)


if __name__ == "__main__":
    main()