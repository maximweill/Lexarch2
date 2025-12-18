import pandas as pd

csv_file = 'lexarchDataProcessing\word_dataset_with_difficulties.parquet'

def get_similar_words(word, max_results=10):
    # Load CSV
    df = pd.read_parquet(csv_file)

    # Normalize search case
    df['Word'] = df['Word'].astype(str)
    search_word = word.upper()

    # Find the row for the given word
    match = df[df['Word'] == search_word]

    if match.empty:
        return []

    # Extract pronunciation & syllable for similarity grouping
    pronunciation = match.iloc[0]['Pronunciation']
    syllable = match.iloc[0]['Syllable']

    # Similar spelling = same syllable
    similar_spelling = df[df['Syllable'] == syllable]['Word']

    # Similar pronunciation = same pronunciation
    similar_pronunciation = df[df['Pronunciation'] == pronunciation]['Word']

    # Combine
    combined = set(similar_spelling).union(set(similar_pronunciation))

    # Remove the word itself
    combined.discard(search_word)

    # Limit results
    return list(combined)[:max_results]


if __name__ == "__main__":
    test_word = "AACHEN"
    similar_words = get_similar_words(test_word, max_results=5)
    print(f"Similar words to '{test_word}': {similar_words}")
