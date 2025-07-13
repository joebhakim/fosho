"""Auto-generated schema for test_data.csv."""

import pandera.pandas as pa

schema = pa.DataFrameSchema({
    "id": pa.Column(int),
    "name": pa.Column(str),
    "category": pa.Column(str),
    "value": pa.Column(int),
})

def validate_dataframe(df):
    """Validate DataFrame against schema."""
    return schema.validate(df)