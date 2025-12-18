#reruns all the scripts in order
import gen_data
#gen_data.main()
import search_datasets
#search_datasets.main()
import search2csv
#search2csv.main()
import word_difficulty
#word_difficulty.main()
import parts
#parts.main()
print("Generated data.")

import MS_data
print("spelling_pairs.parquet generated.")
import MS_data_formating
print("spelling_pairs_with_syllables.parquet generated.")


print("uses pronunciation_search.pkl")
import MS_metrics
print("incorrect_syllables_pairs.pkl and incorrect_syllables_pairs.pkl")