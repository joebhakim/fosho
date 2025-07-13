import pandas as pd

import pandera.pandas as pa

# This is how the library should work


import fosho


# Warn here if not validated
wrapped_df = fosho.read_csv(
    file="data/static_notes.csv",
    schema="data_and_schemas/static_notes.yaml",
    validation_artifacts="static_notes_validation_artifacts",
)


wrapped_df.validate()  # Error here if not validated

# If we make it to this line, we should be able to use wrapped_df as a df

print("head:", wrapped_df.head())

wrapped_df.to_csv("data/static_notes_wrapped_after_validation.csv")
