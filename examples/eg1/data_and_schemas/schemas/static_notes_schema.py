"""Auto-generated Pandera schema for static_notes.csv."""

import pandera.pandas as pa
from pandera.typing import DataFrame

# Schema definition in YAML format:
schema_yaml = """
schema_type: dataframe
version: 0.24.0
columns:
  ? - id
    - '1'
  : title: null
    description: null
    dtype: int64
    nullable: false
    checks:
    - value: 2
      options:
        check_name: greater_than_or_equal_to
        raise_warning: false
        ignore_na: true
    unique: false
    coerce: false
    required: true
    regex: false
  ? - timestamp
    - '2024-01-01'
  : title: null
    description: null
    dtype: object
    nullable: true
    checks: null
    unique: false
    coerce: false
    required: true
    regex: false
  ? - category
    - A
  : title: null
    description: null
    dtype: object
    nullable: true
    checks: null
    unique: false
    coerce: false
    required: true
    regex: false
  ? - notes
    - First note
  : title: null
    description: null
    dtype: object
    nullable: true
    checks: null
    unique: false
    coerce: false
    required: true
    regex: false
  ? - value
    - '100'
  : title: null
    description: null
    dtype: int64
    nullable: false
    checks:
    - value: 150
      options:
        check_name: greater_than_or_equal_to
        raise_warning: false
        ignore_na: true
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
