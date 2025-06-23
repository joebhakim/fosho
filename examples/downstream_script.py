import pandas as pd

import pandera.pandas as pa

# This is how the library should work


import fosho


wrapped_df = fosho.read_csv(file="data/static_notes.csv", schema="data_and_schemas/")


df = pd.read_csv("data/a.csv")

validated_schema = {}
