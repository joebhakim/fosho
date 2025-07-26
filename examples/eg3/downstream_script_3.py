#!/usr/bin/env python3
"""Example downstream script using fosho dataset validation."""

import fosho
from pathlib import Path
from datasets import load_dataset

# Load the actual dataset (your original use case)
ds = load_dataset("Anthropic/hh-rlhf")

# Wrap with fosho validation using the generated schema
schema_path = Path(__file__).parent / "schemas" / "Anthropic_hh-rlhf_dataset_schema.py"
validated_ds = fosho.create_dataset_wrapper(ds, schema_path, "Anthropic/hh-rlhf").validate()

# Now safe to use - your original pattern
train = []
for key in ["train", "test"]:  # These keys are now validated to exist
    for ex in validated_ds[key]:
        train.append({"chosen": ex["chosen"], "rejected": ex["rejected"]})

print(f"Processed {len(train)} total records")