import pandas as pd
from data_processing import load_word_data

df = load_word_data()
minimum = 5/100
maximum = 10/100

def similarly_hard(existing_words, confidence_metric, minimum, maximum):
    difficulty_map = df.set_index('Word')['Spelling Difficulty'].to_dict()
    
    # 1. Block existing words + current input words to avoid duplicated words
    current_batch_keys = list(confidence_metric.keys())
    temp_existing = set(existing_words)
    temp_existing.update(current_batch_keys)
    blocked_words = list(temp_existing) 
    
    similarity_map = []
    
    for word_key, word_dict in confidence_metric.items():
        target_diff = difficulty_map.get(word_key, None)
        if target_diff is None: continue
        
        
        for syl, pron in word_dict.items():
            similarity_map.append([target_diff, syl, pron])

    similar_sound = {}
    similar_spell = {}
    save = []
  
    for row_index, row in df.iterrows():
        if row['Word'] in blocked_words: continue
            
        current_diff = row['Spelling Difficulty']
        current_syllables = row['Syllables']
        current_pronunciation = row['Pronunciation']

        if len(current_syllables) != len(current_pronunciation): continue

        for data in similarity_map:
            target_diff = data[0]
            target_syl = data[1]
            target_pron = data[2]

            
            if target_syl in current_syllables:
                if (target_diff - minimum) <= current_diff <= (target_diff + maximum):
                    similar_spell[row['Word']] = [target_syl]
                    blocked_words.append(row['Word']) 
                    break # Stop checking this word against other targets
                
                elif current_diff < (target_diff - minimum - 0.1) or current_diff > (target_diff + maximum + 0.1):
                    save.append([row['Word'], target_syl])

            
            if target_pron in current_pronunciation:
                indices = [i for i, x in enumerate(current_pronunciation) if x == target_pron]
                for idx in indices:
                    associated_syllable = current_syllables[idx]
                    
                    if (target_diff - minimum) <= current_diff <= (target_diff + maximum):
                        if associated_syllable != target_syl:
                            if row['Word'] not in blocked_words:
                                similar_sound[row['Word']] = {associated_syllable, target_pron}
                                blocked_words.append(row['Word'])

    # Backup Logic in case no word was found that was within the original difficulty range
    if not similar_spell and not similar_sound and len(save) > 0:
        limit = min(5, len(save))
        for i in range(limit):
            backup_word = save[i][0]
            if backup_word not in blocked_words:
                backup_syl = save[i][1]
                similar_spell[backup_word] = [backup_syl]
                blocked_words.append(backup_word)

    input_keys = list(confidence_metric.keys())
    return similar_spell, similar_sound, input_keys, blocked_words


def generate_test_words(tested_words, minimum, maximum):
    input_words = []
    all_words = []
    saved_dicts = {}
    
    existing_words = []
    for batch in tested_words:
        existing_words.extend(list(batch.keys()))
    
    for batch in tested_words:
        res1, res2, res3, updated_existing = similarly_hard(existing_words, batch, minimum, maximum)

        
        TARGET_NEW_WORDS = 9 
        
        all_spelling = list(res1.items())
        all_sounds = list(res2.items())
        
        # Take max 4 sounds
        final_sounds = all_sounds[:4]
        
        # Fill remainder with spelling matches
        slots_taken = len(final_sounds)
        slots_needed = TARGET_NEW_WORDS - slots_taken
        final_spelling = all_spelling[:slots_needed]
        
        batch_generated = {}
        batch_generated.update(dict(final_spelling))
        batch_generated.update(dict(final_sounds))

        saved_dicts.update(batch_generated)
        input_words.append(res3)
        all_words.extend(res3)

        existing_words = updated_existing

        

    for i in saved_dicts.keys():
        all_words.append(i)
        
    all_words = list(set(all_words))
    
    return saved_dicts, input_words, all_words


if __name__ == "__main__":
    print("--- STARTING TEST ---")

    
    tested_words = [
        {'AACHEN': {'AA': 'AA'}}, 
        {'GLYCOLIC': {'GLY': 'G L AY'}} 
    ]
    
    min_range = 0.05
    max_range = 0.10

    df = df.sample(frac=1).reset_index(drop=True)
    
    result = generate_test_words(tested_words, min_range, max_range)
    
    print("\n--- FINAL RESULT ---")
    print(f"Total Words: {len(result)}")
    print(result)