"""Auto-generated schema for complex_metrics.csv."""

import pandera.pandas as pa

schema = pa.DataFrameSchema({
    'Patient ID#': pa.Column(int),
    'Heart Rate (bpm)': pa.Column(int),
    'Blood Pressure@Systolic': pa.Column(float),
    'Temperature °C': pa.Column(float),
    'Status-Code': pa.Column(object),
    'Mixed$Column': pa.Column(object),
    'Weight (kg)': pa.Column(float, nullable=True),
    'Notes & Comments': pa.Column(object),
})

def validate_dataframe(df):
    """Validate DataFrame against schema."""
    return schema.validate(df)