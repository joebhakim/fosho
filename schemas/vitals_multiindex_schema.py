"""Auto-generated schema for vitals_multiindex.csv."""

import pandera.pandas as pa

schema = pa.DataFrameSchema({
    "HeartRate": pa.Column(str),
    'HeartRate.1': pa.Column(str),
    "BloodPressure": pa.Column(str),
    'BloodPressure.1': pa.Column(str),
    "Temperature": pa.Column(str),
    "Weight": pa.Column(str),
})

def validate_dataframe(df):
    """Validate DataFrame against schema."""
    return schema.validate(df)