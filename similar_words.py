import pandas as pd
import os
import ast
import itertools

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
spelling_file = os.path.join(BASE_DIR, 'spelling_search.json')
pronounciation_file = os.path.join(BASE_DIR, 'pronunciation_search.json')

def load_json_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = file.read()
    return ast.literal_eval(data)   


def get_similar_words(word, max_results=10):
    spelling_data = load_json_file(spelling_file)
    pronunciation_data = load_json_file(pronounciation_file)

    spelling_df = pd.DataFrame(spelling_data)
    pronunciation_df = pd.DataFrame(pronunciation_data)

    spelling_matches = spelling_df[spelling_df['word'] == word]
    pronunciation_matches = pronunciation_df[pronunciation_df['word'] == word]

    similar_spelling_words = set()
    similar_pronunciation_words = set()

    if not spelling_matches.empty:
        similar_spelling_words = set(itertools.chain.from_iterable(
            spelling_matches['similar_words'].apply(lambda x: x[:max_results])
        ))

    if not pronunciation_matches.empty:
        similar_pronunciation_words = set(itertools.chain.from_iterable(
            pronunciation_matches['similar_words'].apply(lambda x: x[:max_results])
        ))

    combined_similar_words = list(similar_spelling_words.union(similar_pronunciation_words))
    
    return combined_similar_words[:max_results]

if __name__ == "__main__":
    test_word = "example"
    similar_words = get_similar_words(test_word, max_results=5)
    print(f"Similar words to '{test_word}': {similar_words}")