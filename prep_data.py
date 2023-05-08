import os
import pandas as pd
import gzip
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import functools

c = 0
@functools.lru_cache(maxsize=None)
def closest_match(orig_name, choices):
    global c
    name = orig_name
    for suffix in [' U19', ' U21', ' II', ' U23', ' U21', ' U18', ' U17', ' U16']:
        if name.endswith(suffix):
            name = name[:-3]
    if name in choices:
        return name
    bm = process.extractOne(name, choices, scorer=fuzz.token_set_ratio, score_cutoff=80)
    c=c+1
    if c%100==1:
        print(f"{c}: {orig_name} matches {bm}")
    return bm and bm[0]
    
def concat_csv_files_and_save(input_directory, output_file):
    dataframes = []

    for file in os.listdir(input_directory):
        if file.endswith('.csv'):
            dataframes.append(pd.read_csv(os.path.join(input_directory, file)))
    combined_df = pd.concat(dataframes, ignore_index=True)        
    # Create a dictionary mapping club names to league names
    club_to_league_map = combined_df.groupby('club_name')['league_name'].agg(lambda x: x.value_counts().index[0]).to_dict()
    
    # Get unique club names from the DataFrame
    club_names = tuple(combined_df['club_name'].unique())  

    combined_df['club_involved_cleaned'] = combined_df['club_involved_name'].apply(lambda x: closest_match(x, club_names))
    combined_df['involved_league'] = combined_df['club_involved_cleaned'].apply(lambda x: club_to_league_map.get(x))
    print(combined_df)
    with gzip.open(output_file, 'wt') as f:
        combined_df.to_csv(f, index=False)


input_directory = 'transfers/data'
output_file = 'combined_transfers_data.csv.gz'
concat_csv_files_and_save(input_directory, output_file)
