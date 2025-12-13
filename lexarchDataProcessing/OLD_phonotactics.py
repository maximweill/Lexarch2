def parse_phonemes(path:str)->dict[str,str]:
    """Return a dict: phoneme -> features list"""
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

def pronunciation_syllables(pronunciation:list[str])->list[list[str]]:
    """Convert pronunciation list to syllable structure using maximal onset principle."""
    syllables = []
    current_syllable = []
    current_syllable_structure = []
    for phoneme in pronunciation:
        phoneme = phoneme.rstrip("012")  # remove stress markers
        current_syllable.append(phoneme)
        category = phoneme_dict[phoneme]
        current_syllable_structure.append(category)
        if category == "vowel": # syllable boundary
            if len(syllables)>0:
                while not check_valid_onset(current_syllable, current_syllable_structure):
                    syllables[-1] += current_syllable[0] # move first consonant to previous syllable
                    current_syllable = current_syllable[1:]
                    current_syllable_structure = current_syllable_structure[1:]

            syllables.append(current_syllable)
            current_syllable = []
            current_syllable_structure = []

    if "vowel" not in current_syllable_structure:
        # Append remaining consonants to the last syllable
        syllables[-1]+= current_syllable

    return syllables

def check_sonority_gradient(syllable:list,syllable_structure:list)->bool:
    """Check if the syllable follows the sonority sequencing principle."""
    sonority_scale = {
        "vowel": 5,
        "semivowel": 4,
        "liquid": 3,
        "nasal": 2,
        "fricative": 1,
        "stop": 0
    }
    sonority_values = [sonority_scale[category] for category in syllable_structure]
    
    # Find the peak (vowel)
    peak_index = sonority_values.index(max(sonority_values))
    
    # Check increasing sonority to the peak
    for i in range(peak_index):
        if sonority_values[i] > sonority_values[i+1]:
            return False
    
    # Check decreasing sonority after the peak
    for i in range(peak_index, len(sonority_values)-1):
        if sonority_values[i] < sonority_values[i+1]:
            return False
    
    return True


def check_valid_onset(syllable:list,syllable_structure:list)->bool:
    """Check if the onset of a syllable is valid according to English phonotactics."""
    # Define valid onsets (this is a simplified example)


    # if no onset, it's valid
    if syllable_structure[0] == "vowel":
        return True
    
    # Check single consonant onsets
    if syllable_structure[1] == "vowel" or syllable_structure[1] == "semivowel":
        if syllable[0] != "NG":
            return True
        return False
    
    pre_initials = ["S","SH"]
    initials = ["T","W","M","K","N","P","B","D","G","F","V","TH","DH","CH","JH","Z","ZH"]
    post_initials = ["L","R","W","J","HH"]

    # Check two-consonant onsets
    if syllable_structure[2] == "vowel"or syllable_structure[2] == "semivowel":
        if syllable[0] in pre_initials and (syllable[1] in initials or syllable[1] in post_initials):
            return True
        if syllable[0] in initials and syllable[1] in post_initials:
            return True
        return False

    # Check three-consonant onsets
    if syllable_structure[3] == "vowel":
        if syllable[0] in pre_initials and syllable[1] in initials and syllable[2] in post_initials:
            return True
        return False

    return False

#NOT NEEDED (checked all good)
def check_valid_coda(syllable:list,syllable_structure:list)->bool:
    """Check if the coda of a syllable is valid according to English phonotactics."""

    # Remove any plural s, past morpheme ed or other post-finals
    for _ in range(2):
        if syllable[-1] in ["S","D","T"]:
            syllable = syllable[:-1]
            syllable_structure = syllable_structure[:-1]

    # if no coda, it's valid
    if syllable_structure[-1] == "vowel":
        return True
    
    # Check single consonant codas
    if syllable_structure[-2] == "vowel":
        if syllable[-1] in ["W","R","HH","JH"]:
            return False
        return True
    
    # Check two-consonant codas
    if syllable_structure[-3] == "vowel":
        if syllable_structure[-2] == "nasal" or syllable[-2] in ["S","L"]:
            return True
        return False

    return False