#!/usr/bin/env python3
"""Generate schema for the mock dataset."""

import fosho
from pathlib import Path

# Load the mock dataset
from data.mock_hh_rlhf_dataset import dataset

# Generate schema
schemas_dir = Path(__file__).parent / "schemas"
schema_file = fosho.generate_dataset_schema_file(
    dataset, 
    "hh_rlhf", 
    schemas_dir
)

print(f"Generated schema: {schema_file}")