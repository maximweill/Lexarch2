import numpy as np

def parse_phonemes(path:str)->dict[str,str]:
    """Return a dict that maps phoneme -> phones list"""
    data = {}
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            parts = line.strip().split("	")
            if len(parts) != 2:
                continue
            phoneme = parts[0]
            category = parts[1]
            data[phoneme] = category
    return data
phoneme_dict = parse_phonemes("cmu/cmudict-0.7b.phones")

sonority_scale = {
    "vowel": 6,
    "semivowel": 5,
    "liquid": 4,
    "nasal": 3,
    "fricative": 2,
    "aspirate": 2, # also known as voiceless glottal fricative
    "affricate": 1,
    "stop": 0
}
def pronunciation_syllables(pronunciation: list[str]) -> list[list[str]]:
    """
    Convert a pronunciation list to a syllable structure using
    the Sonority Sequencing Principle and maximal onset principle.

    """
    pronunciation = [p.strip("0123456789 ") for p in pronunciation]

    phones = np.array([phoneme_dict[p] for p in pronunciation])

    # split along vowels
    vowels = np.where(phones == "vowel")[0]
    pronunciation_splits = np.split(pronunciation, vowels+1) # assume maximal onset

    p_syllables = []
    for section in pronunciation_splits: #verify sonority hierarchy and create codas if needed
        sonority_values = [sonority_scale[phoneme_dict[p]] for p in section]
        coda = []
        onset_nuclues = section
        if 6 not in sonority_values and 5 not in sonority_values: # no vowels in section
            coda = section
            onset_nuclues = []
        else:
            for i,(current,after) in enumerate(zip(sonority_values, sonority_values[1:])):
                if current > after:# found a sonority drop
                    split_index = i + 1
                    onset_nuclues = section[split_index:]
                    coda = section[:split_index]
        if len(coda)>0: #coda identified by sonority drop
            if len(p_syllables)==0:# first syllable exception
                onset_nuclues = np.concatenate((coda, onset_nuclues))
            else:
                p_syllables[-1] = np.concatenate((p_syllables[-1], coda))
        if len(onset_nuclues) > 0:
            p_syllables.append(onset_nuclues)

    p_syllables = corrected_CVrV(p_syllables)
    return p_syllables

def corrected_CVrV(p_syllables:list[list[str]])->list[list[str]]:
    """Correct syllable structures of the form CVrV to CVr-V"""
    p_syllables = [list(p) for p in p_syllables]
    for p,p_next in zip(p_syllables,p_syllables[1:]):
        if p_next[0]=="R" and phoneme_dict[p[-1]] == "vowel":
            p.append(p_next.pop(0))
    return p_syllables

def main():
    pronunciation = ["K", "AA1", "N", "S", "T", "AH0", "T", "UW", "SH", "AH", "N"]
    syllables = pronunciation_syllables(pronunciation)
    print(syllables)

if __name__ == "__main__":
    main()
