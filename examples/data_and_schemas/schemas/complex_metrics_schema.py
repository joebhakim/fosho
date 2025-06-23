"""Auto-generated Pandera schema for complex_metrics.csv."""

import pandera.pandas as pa
from pandera.typing import DataFrame

# Schema definition in YAML format:
schema_yaml = """
schema_type: dataframe
version: 0.24.0
columns:
  ? - Patient ID#
    - '1'
  : title: null
    description: null
    dtype: object
    nullable: true
    checks: null
    unique: false
    coerce: false
    required: true
    regex: false
  ? - Heart Rate (bpm)
    - '72'
  : title: null
    description: null
    dtype: object
    nullable: true
    checks: null
    unique: false
    coerce: false
    required: true
    regex: false
  ? - Blood Pressure@Systolic
    - '120.5'
  : title: null
    description: null
    dtype: object
    nullable: true
    checks: null
    unique: false
    coerce: false
    required: true
    regex: false
  ? - "Temperature \xB0C"
    - '37.2'
  : title: null
    description: null
    dtype: object
    nullable: true
    checks: null
    unique: false
    coerce: false
    required: true
    regex: false
  ? - Status-Code
    - Normal
  : title: null
    description: null
    dtype: object
    nullable: true
    checks: null
    unique: false
    coerce: false
    required: true
    regex: false
  ? - Mixed$Column
    - 123x
  : title: null
    description: null
    dtype: object
    nullable: true
    checks: null
    unique: false
    coerce: false
    required: true
    regex: false
  ? - Weight (kg)
    - 'Unnamed: 6_level_1'
  : title: null
    description: null
    dtype: object
    nullable: true
    checks: null
    unique: false
    coerce: false
    required: true
    regex: false
  ? - Notes & Comments
    - Patient doing well
  : title: null
    description: null
    dtype: object
    nullable: true
    checks: null
    unique: false
    coerce: false
    required: true
    regex: false
checks: null
index: null
dtype: null
coerce: false
strict: false
name: null
ordered: false
unique: null
report_duplicates: all
unique_column_names: false
add_missing_columns: false
title: null
description: null

"""

# Load schema from YAML
schema = pa.io.from_yaml(schema_yaml)

def validate_dataframe(df) -> DataFrame:
    """Validate DataFrame against schema."""
    return schema.validate(df)
