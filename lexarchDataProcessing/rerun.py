#reruns all the scripts in order
import gen_data
gen_data.main()
import search_datasets
search_datasets.main()
import search2csv
search2csv.main()
import word_difficulty
word_difficulty.main()
import parts
parts.main()
print("Generated data.")