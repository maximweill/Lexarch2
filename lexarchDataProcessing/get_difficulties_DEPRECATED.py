import pandas as pd
import ast
import math
import collections
import os
import numpy as np
import re

# --- CONFIGURATION ---
INPUT_FILE = "final_dataset.parquet"
OUTPUT_FILE = "word_dataset_with_difficulties.parquet"

# --- WEIGHTS (The recipe) ---
# 1. Phonetic Match: How surprising is the mapping? (e.g. KN -> N)
W_MATCH = 0.35
# 2. Ambiguity: Does this syllable usually map to many different sounds?
W_AMBIGUITY = 0.25
# 3. Complexity: Penalty for vowel clusters (EA, OU, IEU) and cluster length
W_COMPLEXITY = 0.20
# 4. Length: Syllable count penalty
W_LENGTH = 0.20

# Frequency Dampener (0.0 to 0.5)
# A value of 0.4 means a very common word can reduce its difficulty by 40%
# It CANNOT reduce it to zero.
MAX_FREQ_DISCOUNT = 0.4 

# --- TUNING ---
SMOOTHING_K = 5
MAX_FREQ_LOG = 7.0 
MAX_SYLLABLES = 6.0

def load_data(filename):
    print(f"📂 Loading {filename}...")
    if not os.path.exists(filename):
        print(f"❌ Error: {filename} not found.")
        exit()
    df = pd.read_parquet(filename)
    return df

class LanguageModel:
    def __init__(self, df, from_col, to_col):
        self.counts = collections.defaultdict(lambda: collections.defaultdict(int))
        self.totals = collections.defaultdict(int)
        
        print(f"⚙️ Training model: {from_col} -> {to_col}...")
        for _, row in df.iterrows():
            src_list = row[from_col]
            tgt_list = row[to_col]
            if len(src_list) != len(tgt_list): continue
                
            for s, t in zip(src_list, tgt_list):
                self.counts[s][t] += 1
                self.totals[s] += 1
                
        # Calculate Entropy (Ambiguity)
        self.entropy = {}
        for src, total in self.totals.items():
            ent = 0
            for tgt, count in self.counts[src].items():
                p = count / total
                ent -= p * math.log2(p)
            self.entropy[src] = ent

    def get_metrics(self, src_list, tgt_list):
        if len(src_list) != len(tgt_list): return 0.5, 0.5, 0.0

        match_scores = []
        ambiguity_scores = []
        complexity_scores = []
        
        for s, t in zip(src_list, tgt_list):
            # A. Match Probability (Bayesian)
            c = self.counts[s][t]
            tot = self.totals[s]
            prob = (c + 1) / (tot + SMOOTHING_K)
            match_scores.append(1.0 - prob)
            
            # B. Ambiguity (Entropy)
            e = self.entropy.get(s, 1.5) # Default to high ambiguity if unknown
            norm_e = min(e / 3.0, 1.0)
            ambiguity_scores.append(norm_e)

            # C. Visual Complexity (Vowel Clusters)
            # Regex to find double/triple vowels (e.g., 'EA', 'OUI', 'IE')
            vowel_cluster = len(re.findall(r'[AEIOUY]{2,}', s, re.IGNORECASE))
            # Penalty if the text is significantly longer than the sound (e.g., KNIGHT vs NIT)
            len_diff = max(0, len(s) - len(t))
            
            comp = (vowel_cluster * 0.2) + (len_diff * 0.1)
            complexity_scores.append(min(comp, 1.0))
            
        final_match = (max(match_scores) * 0.6) + (np.mean(match_scores) * 0.4)
        final_ambig = np.mean(ambiguity_scores)
        final_comp = max(complexity_scores) if complexity_scores else 0.0
        
        return final_match, final_ambig, final_comp

def calculate_row_raw(row, read_model, spell_model):
    sylls = row['Syllables']
    prons = row['Pronunciation']
    freq = row['Frequency']
    
    # 1. Get Core Metrics
    r_match, r_ambig, r_comp = read_model.get_metrics(sylls, prons)
    s_match, s_ambig, s_comp = spell_model.get_metrics(prons, sylls)
    
    # 2. Length Score (Non-linear)
    length_val = len(sylls)
    len_score = min((length_val - 1) / (MAX_SYLLABLES - 1), 1.0)
    len_score = math.pow(len_score, 0.7) # Curve it to make medium words harder

    # 3. Frequency Factor (0.0 to 1.0)
    if pd.isna(freq) or freq <= 0:
        freq_factor = 0
    else:
        freq_factor = min(math.log10(freq) / MAX_FREQ_LOG, 1.0)

    # 4. RAW Score Calculation (Before Normalization)
    def calc(match, ambig, comp, length, f_factor, is_spelling=False):
        # Base Difficulty
        raw = (match * W_MATCH) + \
              (ambig * W_AMBIGUITY) + \
              (comp * W_COMPLEXITY) + \
              (length * W_LENGTH)
        
        # Apply Multiplicative Discount
        # Common words get scaled down, but never to zero
        # e.g., Raw 0.8 * (1 - (0.9 * 0.4)) = 0.8 * 0.64 = 0.51
        discount_strength = MAX_FREQ_DISCOUNT
        if is_spelling: discount_strength *= 0.7 # Less discount for spelling
        
        multiplier = 1.0 - (f_factor * discount_strength)
        return raw * multiplier

    r_raw = calc(r_match, r_ambig, r_comp, len_score, freq_factor, False)
    s_raw = calc(s_match, s_ambig, s_comp, len_score, freq_factor, True)
    
    return r_raw, s_raw

def main():
    df = load_data(INPUT_FILE)
    
    # Train
    read_model = LanguageModel(df, 'Syllables', 'Pronunciation')
    spell_model = LanguageModel(df, 'Pronunciation', 'Syllables')
    
    print("🧮 Calculating Raw Scores...")
    results = df.apply(lambda row: calculate_row_raw(row, read_model, spell_model), axis=1, result_type='expand')
    
    # --- NORMALIZATION STEP ---
    # This forces the hardest word to be 1.0 and spreads the rest
    print("⚖️ Normalizing to 0.0 - 1.0 scale...")
    
    r_raw = results[0]
    s_raw = results[1]
    
    # Min-Max Scaling
    df['Reading Difficulty'] = (r_raw - r_raw.min()) / (r_raw.max() - r_raw.min())
    df['Spelling Difficulty'] = (s_raw - s_raw.min()) / (s_raw.max() - s_raw.min())
    
    # Save
    df.to_parquet(OUTPUT_FILE, index=False)
    print(f"✅ Success! Saved to {OUTPUT_FILE}")

    # Sanity Check
    check_words = ['KOBE', 'KNUTE', 'ZEUS', 'ZEALOUS', 'THE', 'ANTIDISESTABLISHMENTARIANISM']
    subset = df[df['Word'].isin(check_words)]
    if not subset.empty:
        print("\n--- SANITY CHECK ---")
        print(subset[['Word', 'Reading Difficulty', 'Spelling Difficulty', 'Frequency']])

if __name__ == "__main__":
    main()