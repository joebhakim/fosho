"""Auto-generated schema for static_notes.csv."""

import pandera.pandas as pa

schema = pa.DataFrameSchema({
    "id": pa.Column(int),
    "timestamp": pa.Column(str),
    "category": pa.Column(str),
    "notes": pa.Column(str),
    "value": pa.Column(int),
})

def validate_dataframe(df):
    """Validate DataFrame against schema."""
    return schema.validate(df)