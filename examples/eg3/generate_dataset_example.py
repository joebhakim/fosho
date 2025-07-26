#!/usr/bin/env python3
"""Generate a mock HuggingFace dataset for fosho testing.

This simulates the Anthropic/hh-rlhf dataset structure without requiring
actual download from HuggingFace Hub.
"""

import json
from pathlib import Path
from typing import Dict, Any, List

try:
    from datasets import Dataset, DatasetDict
    HF_DATASETS_AVAILABLE = True
except ImportError:
    HF_DATASETS_AVAILABLE = False
    print("datasets library not available. Install with: pip install datasets")
    exit(1)


def create_mock_anthropic_dataset() -> DatasetDict:
    """Create a mock dataset that mimics Anthropic/hh-rlhf structure.
    
    Returns DatasetDict with train/test splits, each containing chosen/rejected fields.
    """
    # Sample data mimicking the actual structure
    train_data = [
        {
            "chosen": "\n\nHuman: How do I make a peanut butter sandwich?\n\nAssistant: Here's how to make a peanut butter sandwich:\n\n1. Get two slices of bread\n2. Spread peanut butter on one slice\n3. Optionally add jelly or other ingredients\n4. Put the slices together\n\nEnjoy your sandwich!",
            "rejected": "\n\nHuman: How do I make a peanut butter sandwich?\n\nAssistant: Just put peanut butter on bread. Done."
        },
        {
            "chosen": "\n\nHuman: What's the weather like?\n\nAssistant: I don't have access to real-time weather data. You can check the weather by looking outside, using a weather app, or visiting a weather website like weather.com.",
            "rejected": "\n\nHuman: What's the weather like?\n\nAssistant: It's sunny everywhere all the time."
        },
        {
            "chosen": "\n\nHuman: How do I learn Python programming?\n\nAssistant: Here are some great ways to learn Python:\n\n1. Start with official Python tutorial\n2. Try interactive platforms like Codecademy or Python.org\n3. Practice with small projects\n4. Read books like 'Automate the Boring Stuff'\n5. Join Python communities\n\nConsistent practice is key!",
            "rejected": "\n\nHuman: How do I learn Python programming?\n\nAssistant: Python is hard, just give up."
        },
        {
            "chosen": "\n\nHuman: What are the benefits of exercise?\n\nAssistant: Regular exercise provides many benefits:\n\n1. Improves cardiovascular health\n2. Strengthens muscles and bones\n3. Enhances mental health and mood\n4. Helps maintain healthy weight\n5. Boosts energy levels\n6. Improves sleep quality\n\nAim for at least 150 minutes of moderate activity per week.",
            "rejected": "\n\nHuman: What are the benefits of exercise?\n\nAssistant: Exercise is overrated. Just stay on the couch."
        }
    ]
    
    # Create test split with subset of data
    test_data = train_data[:2]
    
    # Create Dataset objects
    train_dataset = Dataset.from_list(train_data)
    test_dataset = Dataset.from_list(test_data)
    
    # Create DatasetDict
    dataset_dict = DatasetDict({
        "train": train_dataset,
        "test": test_dataset
    })
    
    return dataset_dict


def save_mock_dataset_locally(dataset_dict: DatasetDict, output_dir: Path):
    """Save the mock dataset locally for offline use."""
    output_dir.mkdir(exist_ok=True)
    
    # Save as JSON files for easy inspection
    for split_name, split_dataset in dataset_dict.items():
        split_file = output_dir / f"{split_name}.json"
        
        # Convert to list of dicts
        split_data = [record for record in split_dataset]
        
        with open(split_file, "w") as f:
            json.dump(split_data, f, indent=2)
        
        print(f"Saved {split_name} split: {len(split_data)} records -> {split_file}")


def main():
    """Generate the mock dataset and save it."""
    if not HF_DATASETS_AVAILABLE:
        print("Error: datasets library is required")
        print("Install with: pip install datasets")
        return
    
    # Create eg3 directory structure
    eg3_dir = Path(__file__).parent
    data_dir = eg3_dir / "data"
    
    print("Generating mock HuggingFace dataset for fosho testing...")
    
    # Create the mock dataset
    dataset_dict = create_mock_anthropic_dataset()
    
    print(f"Created DatasetDict:")
    print(f"  Type: {type(dataset_dict)}")
    print(f"  Keys: {list(dataset_dict.keys())}")
    
    for split_name, split_dataset in dataset_dict.items():
        print(f"  {split_name}: {len(split_dataset)} records")
        if hasattr(split_dataset, 'features'):
            print(f"    Features: {list(split_dataset.features.keys())}")
    
    # Save locally for inspection
    save_mock_dataset_locally(dataset_dict, data_dir)
    
    # Save the dataset object as well (for direct loading)
    dataset_file = data_dir / "mock_hh_rlhf_dataset.py"
    with open(dataset_file, "w") as f:
        f.write('''"""Mock HuggingFace dataset for testing."""

from datasets import Dataset, DatasetDict

def load_mock_dataset():
    """Load the mock dataset."""
    import json
    from pathlib import Path
    
    data_dir = Path(__file__).parent
    
    dataset_dict = {}
    for split_file in ["train.json", "test.json"]:
        split_name = split_file.replace(".json", "")
        with open(data_dir / split_file) as f:
            split_data = json.load(f)
        dataset_dict[split_name] = Dataset.from_list(split_data)
    
    return DatasetDict(dataset_dict)

# Global dataset instance
dataset = load_mock_dataset()
''')
    
    print(f"\nDataset saved to: {dataset_file}")
    print("\nNext steps:")
    print("1. Run 'uv run fosho scan-dataset' to generate schema (when implemented)")
    print("2. Or manually create schema using fosho.generate_dataset_schema_file()")
    print("3. Test with example script using fosho.load_dataset()")


if __name__ == "__main__":
    main()