"""Generate example datasets for testing dsq functionality."""

import json
import random
from pathlib import Path

import pandas as pd
import numpy as np

# Ensure reproducible examples (but allow reshuffling)
np.random.seed(42)


def generate_complex_metrics():
    """Generate complex_metrics.csv with weird column names and mixed data."""
    data = {
        'Patient ID#': [1],
        'Heart Rate (bpm)': [72],
        'Blood Pressure@Systolic': [120.5],
        'Temperature °C': [37.2],
        'Status-Code': ['Normal'],
        'Mixed$Column': ['123x'],  # Int-like but has trailing char
        'Weight (kg)': [np.nan],   # Float with NaN
        'Notes & Comments': ['Patient doing well']
    }
    
    df = pd.DataFrame(data)
    return df


def generate_vitals_multiindex():
    """Generate vitals_multiindex.csv with multi-level column headers."""
    # Create multi-index columns
    columns = pd.MultiIndex.from_tuples([
        ('HeartRate', 'mean'),
        ('HeartRate', 'std'),
        ('BloodPressure', 'systolic'),
        ('BloodPressure', 'diastolic'),
        ('Temperature', 'celsius'),
        ('Weight', 'kg')
    ])
    
    data = [
        [72.3, 5.2, 120, 80, 36.8, 70.2],
        [68.1, 4.8, 118, 78, 37.1, 71.5]
    ]
    
    df = pd.DataFrame(data, columns=columns)
    return df


def generate_nested_json():
    """Generate nested_json.csv with JSON strings in one column."""
    patient_data = [
        {'name': 'John Doe', 'allergies': ['peanuts'], 'emergency_contact': '555-1234'},
        {'name': 'Jane Smith', 'allergies': [], 'emergency_contact': '555-5678'},
        {'name': 'Bob Johnson', 'allergies': ['shellfish', 'latex'], 'emergency_contact': '555-9999'}
    ]
    
    data = {
        'patient_info': [json.dumps(info) for info in patient_data],
        'age': [45, 32, 67]
    }
    
    df = pd.DataFrame(data)
    return df


def generate_static_notes():
    """Generate static_notes.csv with shuffled column order."""
    base_data = {
        'id': [1, 2, 3, 4],
        'timestamp': ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04'],
        'category': ['A', 'B', 'A', 'C'],
        'value': [100, 200, 150, 300],
        'notes': ['First note', 'Second note', 'Third note', 'Fourth note']
    }
    
    # Shuffle column order to test CRC32 sensitivity
    columns = list(base_data.keys())
    random.shuffle(columns)
    
    # Create DataFrame with shuffled columns
    shuffled_data = {col: base_data[col] for col in columns}
    df = pd.DataFrame(shuffled_data)
    return df


def main():
    """Generate all example datasets."""
    # Create examples/data directory
    data_dir = Path(__file__).parent / "data"
    data_dir.mkdir(exist_ok=True)
    
    # Generate datasets
    datasets = {
        'complex_metrics.csv': generate_complex_metrics(),
        'vitals_multiindex.csv': generate_vitals_multiindex(),
        'nested_json.csv': generate_nested_json(),
        'static_notes.csv': generate_static_notes()
    }
    
    for filename, df in datasets.items():
        file_path = data_dir / filename
        
        if filename == 'vitals_multiindex.csv':
            # Save with multi-index header
            df.to_csv(file_path, index=False)
        else:
            df.to_csv(file_path, index=False)
        
        print(f"Generated: {file_path}")
        print(f"  Shape: {df.shape}")
        print(f"  Columns: {list(df.columns)}")
        print()


if __name__ == "__main__":
    main()