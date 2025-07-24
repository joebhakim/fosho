"""Auto-generated schema for vitals_multiindex.csv."""

import pandera.pandas as pa

schema = pa.DataFrameSchema({
    "HeartRate": pa.Column(object),
    'HeartRate.1': pa.Column(object),
    "BloodPressure": pa.Column(object),
    'BloodPressure.1': pa.Column(object),
    "Temperature": pa.Column(object),
    "Weight": pa.Column(object),
})

def validate_dataframe(df):
    """Validate DataFrame against schema."""
    return schema.validate(df)