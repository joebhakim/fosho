"""Auto-generated schema for text_example.csv."""

import pandera.pandas as pa
import pandas as pd

schema = pa.DataFrameSchema({
    "id": pa.Column(int),
    "timestamp": pa.Column(str, pa.Check(lambda x: pd.to_datetime(x, errors='raise') is not None)),
    "category": pa.Column(str, pa.Check.isin(["A", "B", "C"])),
    "notes": pa.Column(str),
    "value": pa.Column(int, pa.Check.ge(0)),
})

def validate_dataframe(df):
    """Validate DataFrame against schema."""
    return schema.validate(df)