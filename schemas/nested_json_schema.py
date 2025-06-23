"""Auto-generated schema for nested_json.csv."""

import pandera.pandas as pa

schema = pa.DataFrameSchema({
    "patient_info": pa.Column(str),
    "age": pa.Column(int),
})

def validate_dataframe(df):
    """Validate DataFrame against schema."""
    return schema.validate(df)