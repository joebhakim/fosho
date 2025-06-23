"""Auto-generated schema for complex_metrics.csv."""

import pandera.pandas as pa

schema = pa.DataFrameSchema({
    'Patient ID#': pa.Column(int),
    'Heart Rate (bpm)': pa.Column(int),
    'Blood Pressure@Systolic': pa.Column(float),
    'Temperature °C': pa.Column(float),
    'Status-Code': pa.Column(str),
    'Mixed$Column': pa.Column(str),
    'Weight (kg)': pa.Column(float, nullable=True),
    'Notes & Comments': pa.Column(str),
})

def validate_dataframe(df):
    """Validate DataFrame against schema."""
    return schema.validate(df)