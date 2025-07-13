"""Auto-generated schema for a_broken.csv."""

import pandera.pandas as pa

schema = pa.DataFrameSchema({
    "id": pa.Column(str),
    "description": pa.Column(str),
})

def validate_dataframe(df):
    """Validate DataFrame against schema."""
    return schema.validate(df)