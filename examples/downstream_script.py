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
