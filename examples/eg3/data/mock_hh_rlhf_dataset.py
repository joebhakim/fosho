"""Mock HuggingFace dataset for testing."""

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
