#!/usr/bin/env python3
"""Test downstream script using fosho.read_csv with Python schemas."""

import fosho

# Test the read_csv function with Python schema
df = fosho.read_csv(
    file="data/text_example.csv",
    schema="schemas/text_example_schema.py",
    manifest_path="manifest.json"
)

print("Before validation:")
print(repr(df))

# Validate and use the DataFrame
validated_df = df.validate()
print("\nAfter validation:")
print(validated_df.head())

# Should be able to use as normal DataFrame after validation
print(f"\nDataFrame shape: {df.shape}")
print(f"Average value: {df['value'].mean()}")