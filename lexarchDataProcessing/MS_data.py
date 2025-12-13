import pandas as pd

def get_misspellings_df():
    raw_text = ""
    with open('miss_spellings/aspell.dat.txt', 'r', encoding='utf-8') as f:
        raw_text += f.read()
    with open('miss_spellings/holbrook-missp.dat.txt', 'r', encoding='utf-8') as f:
        raw_text += f.read()
    with open('miss_spellings\missp.dat.txt', 'r', encoding='utf-8') as f:
        raw_text += f.read()
    with open('miss_spellings\wikipedia.dat.txt', 'r', encoding='utf-8') as f:
        raw_text += f.read()
    raw_text = raw_text.upper()

    correct = None
    rows = []
    for line in raw_text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith('$'):
            correct = line[1:]  # true spelling
        else:
            rows.append({"correct": correct, "incorrect": line})

    # Create DataFrame
    df = pd.DataFrame(rows)
    print(df)

    # Optionally save it
    df.to_csv('spelling_pairs.csv', index=False)

if __name__ == "__main__":
    get_misspellings_df()