"""Auto-generated schema for text_example.csv."""

import pandera.pandas as pa

schema = pa.DataFrameSchema({
    "id": pa.Column(int),
    "timestamp": pa.Column(object),
    "category": pa.Column(object),
    "notes": pa.Column(object),
    "value": pa.Column(int),
})

def validate_dataframe(df):
    """Validate DataFrame against schema."""
    return schema.validate(df)