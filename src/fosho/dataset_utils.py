"""Dataset utilities for HuggingFace dataset metadata extraction and hashing."""

import hashlib
import json
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

try:
    from datasets import Dataset, DatasetDict
    HF_DATASETS_AVAILABLE = True
except ImportError:
    HF_DATASETS_AVAILABLE = False
    Dataset = None
    DatasetDict = None


def extract_dataset_metadata(dataset: Union[Dataset, DatasetDict]) -> Dict[str, Any]:
    """Extract metadata from a HuggingFace dataset for schema validation.
    
    Args:
        dataset: HuggingFace Dataset or DatasetDict object
        
    Returns:
        Dictionary containing dataset structure metadata
        
    Raises:
        ImportError: If datasets library is not installed
        ValueError: If dataset type is not supported
    """
    if not HF_DATASETS_AVAILABLE:
        raise ImportError("datasets library is required for dataset validation. Install with: pip install datasets")
    
    metadata = {
        "dataset_type": type(dataset).__name__,
        "available_keys": [],
        "splits": {},
        "features": {},
        "record_structure": {},
        "total_size": 0
    }
    
    if isinstance(dataset, DatasetDict):
        # Multi-split dataset (e.g., train/test or helpful-base/harmless-base)
        metadata["available_keys"] = list(dataset.keys())
        
        for key, subset in dataset.items():
            # Convert features to simple strings for JSON serialization
            features_dict = {}
            if hasattr(subset, 'features') and subset.features:
                features_dict = {name: str(feature) for name, feature in subset.features.items()}
            
            metadata["splits"][key] = {
                "num_rows": len(subset),
                "features": features_dict,
                "splits": list(subset.keys()) if hasattr(subset, 'keys') else []
            }
            metadata["total_size"] += len(subset)
            
            # Extract sample record structure from first item
            if len(subset) > 0:
                try:
                    sample_record = subset[0]
                    metadata["record_structure"][key] = {
                        field: type(value).__name__ 
                        for field, value in sample_record.items()
                    }
                except Exception:
                    metadata["record_structure"][key] = {}
        
        # Extract global features if available
        first_key = list(dataset.keys())[0]
        if hasattr(dataset[first_key], 'features') and dataset[first_key].features:
            metadata["features"] = {name: str(feature) for name, feature in dataset[first_key].features.items()}
            
    elif isinstance(dataset, Dataset):
        # Single dataset
        metadata["available_keys"] = ["default"]
        metadata["total_size"] = len(dataset)
        # Convert features to simple strings for JSON serialization
        features_dict = {}
        if hasattr(dataset, 'features') and dataset.features:
            features_dict = {name: str(feature) for name, feature in dataset.features.items()}
        
        metadata["splits"]["default"] = {
            "num_rows": len(dataset),
            "features": features_dict,
            "splits": []
        }
        
        # Extract features and sample record
        metadata["features"] = features_dict
            
        if len(dataset) > 0:
            try:
                sample_record = dataset[0]
                metadata["record_structure"]["default"] = {
                    field: type(value).__name__ 
                    for field, value in sample_record.items()
                }
            except Exception:
                metadata["record_structure"]["default"] = {}
    else:
        raise ValueError(f"Unsupported dataset type: {type(dataset)}")
    
    return metadata


def compute_dataset_hash(dataset: Union[Dataset, DatasetDict]) -> str:
    """Compute a hash for dataset structure and sample content.
    
    This creates a fingerprint that detects changes in:
    - Available keys/splits
    - Dataset structure
    - Sample record content (first few records)
    
    Args:
        dataset: HuggingFace Dataset or DatasetDict object
        
    Returns:
        MD5 hash string representing dataset state
    """
    if not HF_DATASETS_AVAILABLE:
        raise ImportError("datasets library is required for dataset validation")
    
    # Extract metadata for hashing
    metadata = extract_dataset_metadata(dataset)
    
    # Add sample content for change detection
    sample_content = {}
    
    if isinstance(dataset, DatasetDict):
        for key, subset in dataset.items():
            if len(subset) > 0:
                # Hash first 3 records to detect content changes
                sample_records = []
                for i in range(min(3, len(subset))):
                    try:
                        record = subset[i]
                        # Convert to serializable format
                        serializable_record = {}
                        for k, v in record.items():
                            if isinstance(v, (str, int, float, bool)):
                                serializable_record[k] = str(v)[:100] if isinstance(v, str) else v
                            elif isinstance(v, list):
                                serializable_record[k] = f"list_len_{len(v)}"
                            elif isinstance(v, dict):
                                serializable_record[k] = f"dict_keys_{len(v)}"
                            else:
                                serializable_record[k] = str(type(v).__name__)
                        sample_records.append(serializable_record)
                    except Exception:
                        break
                sample_content[key] = sample_records
    elif isinstance(dataset, Dataset):
        if len(dataset) > 0:
            sample_records = []
            for i in range(min(3, len(dataset))):
                try:
                    record = dataset[i]
                    serializable_record = {}
                    for k, v in record.items():
                        if isinstance(v, (str, int, float, bool)):
                            serializable_record[k] = str(v)[:100] if isinstance(v, str) else v
                        elif isinstance(v, list):
                            serializable_record[k] = f"list_len_{len(v)}"
                        elif isinstance(v, dict):
                            serializable_record[k] = f"dict_keys_{len(v)}"
                        else:
                            serializable_record[k] = str(type(v).__name__)
                    sample_records.append(serializable_record)
                except Exception:
                    break
            sample_content["default"] = sample_records
    
    # Combine metadata and sample content for hashing
    hash_data = {
        "metadata": metadata,
        "sample_content": sample_content
    }
    
    # Create stable JSON representation
    json_str = json.dumps(hash_data, sort_keys=True)
    
    # Return MD5 hash
    return hashlib.md5(json_str.encode()).hexdigest()


def validate_dataset_keys(dataset: Union[Dataset, DatasetDict], expected_keys: List[str]) -> bool:
    """Validate that dataset contains expected keys.
    
    Args:
        dataset: HuggingFace dataset object
        expected_keys: List of keys that should be present
        
    Returns:
        True if all expected keys are present, False otherwise
    """
    if not HF_DATASETS_AVAILABLE:
        raise ImportError("datasets library is required for dataset validation")
    
    if isinstance(dataset, DatasetDict):
        available_keys = set(dataset.keys())
    elif isinstance(dataset, Dataset):
        available_keys = {"default"}
    else:
        return False
    
    expected_keys_set = set(expected_keys)
    return expected_keys_set.issubset(available_keys)


def get_dataset_fingerprint(dataset: Union[Dataset, DatasetDict]) -> Optional[str]:
    """Get the HuggingFace dataset fingerprint if available.
    
    This uses the built-in dataset fingerprint when available,
    which is more precise than our custom hash.
    
    Args:
        dataset: HuggingFace dataset object
        
    Returns:
        Dataset fingerprint string if available, None otherwise
    """
    try:
        if isinstance(dataset, DatasetDict):
            # Combine fingerprints from all splits
            fingerprints = []
            for key, subset in dataset.items():
                if hasattr(subset, '_fingerprint'):
                    fingerprints.append(f"{key}:{subset._fingerprint}")
            return hashlib.md5("|".join(sorted(fingerprints)).encode()).hexdigest()
        elif isinstance(dataset, Dataset):
            if hasattr(dataset, '_fingerprint'):
                return dataset._fingerprint
    except Exception:
        pass
    
    return None