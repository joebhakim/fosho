"""Dataset schema validation framework using Pandera for HuggingFace datasets."""

import json
from typing import Dict, Any, List, Optional, Union, Type
from pathlib import Path

import pandera as pa
from pydantic import BaseModel, Field, validator

try:
    from datasets import Dataset, DatasetDict
    HF_DATASETS_AVAILABLE = True
except ImportError:
    HF_DATASETS_AVAILABLE = False
    Dataset = None
    DatasetDict = None


class DatasetStructureSchema(BaseModel):
    """Schema for validating DatasetDict structure.
    
    For a typical HuggingFace dataset like:
    DatasetDict({
        train: Dataset({features: ['chosen', 'rejected'], num_rows: 160800})
        test: Dataset({features: ['chosen', 'rejected'], num_rows: 8552})
    })
    """
    
    expected_splits: List[str] = Field(description="Required splits (e.g., ['train', 'test'])")
    optional_splits: List[str] = Field(default_factory=list, description="Optional splits")
    min_records_per_split: int = Field(default=1, description="Minimum records required per split")
    
    @validator('expected_splits')
    def validate_expected_splits(cls, v):
        if not v:
            raise ValueError("At least one expected split must be specified")
        return v


class DatasetRecordSchema(BaseModel):
    """Schema for validating individual records within each Dataset.
    
    For records like: {"chosen": "...", "rejected": "..."}
    """
    
    required_features: Dict[str, str] = Field(description="Required features and their types")
    optional_features: Dict[str, str] = Field(default_factory=dict, description="Optional features and their types")
    feature_constraints: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Additional constraints per feature")
    
    @validator('required_features')
    def validate_required_features(cls, v):
        if not v:
            raise ValueError("At least one required feature must be specified")
        return v


class DatasetSchema:
    """Combined schema for HuggingFace DatasetDict validation."""
    
    def __init__(
        self,
        structure_schema: DatasetStructureSchema,
        record_schema: DatasetRecordSchema,
        name: Optional[str] = None
    ):
        self.structure_schema = structure_schema
        self.record_schema = record_schema
        self.name = name or "dataset_schema"
    
    def validate_structure(self, dataset: Union[Dataset, DatasetDict]) -> bool:
        """Validate DatasetDict structure against schema.
        
        Args:
            dataset: HuggingFace dataset object
            
        Returns:
            True if structure is valid
            
        Raises:
            ValueError: If structure validation fails
        """
        if not HF_DATASETS_AVAILABLE:
            raise ImportError("datasets library is required for dataset validation")
        
        # Handle single Dataset vs DatasetDict
        if isinstance(dataset, Dataset):
            # Single dataset - treat as if it has a "default" split
            available_splits = {"default"}
            dataset_dict = {"default": dataset}
        elif isinstance(dataset, DatasetDict):
            available_splits = set(dataset.keys())
            dataset_dict = dataset
        else:
            raise ValueError(f"Unsupported dataset type: {type(dataset)}")
        
        # Check required splits
        required_splits = set(self.structure_schema.expected_splits)
        missing_splits = required_splits - available_splits
        if missing_splits:
            raise ValueError(f"Missing required dataset splits: {missing_splits}")
        
        # Validate each split
        for split_name in required_splits:
            split_dataset = dataset_dict[split_name]
            
            if not isinstance(split_dataset, Dataset):
                raise ValueError(f"Split '{split_name}' is not a Dataset object")
            
            # Check minimum records
            if len(split_dataset) < self.structure_schema.min_records_per_split:
                raise ValueError(f"Split '{split_name}' has {len(split_dataset)} records, minimum {self.structure_schema.min_records_per_split} required")
        
        return True
    
    def validate_records(self, dataset: Union[Dataset, DatasetDict], sample_size: int = 3) -> bool:
        """Validate record structure against schema.
        
        Args:
            dataset: HuggingFace dataset object
            sample_size: Number of records to validate per split
            
        Returns:
            True if records are valid
            
        Raises:
            ValueError: If record validation fails
        """
        if not HF_DATASETS_AVAILABLE:
            raise ImportError("datasets library is required for dataset validation")
        
        required_features = set(self.record_schema.required_features.keys())
        
        def validate_record_features(record: Dict[str, Any], context: str = ""):
            """Validate a single record's features."""
            record_features = set(record.keys())
            
            # Check required features
            missing_features = required_features - record_features
            if missing_features:
                raise ValueError(f"Missing required features in {context}: {missing_features}")
            
            # Check feature types
            for feature_name, expected_type in self.record_schema.required_features.items():
                if feature_name in record:
                    value = record[feature_name]
                    if not self._check_feature_type(value, expected_type):
                        raise ValueError(f"Feature '{feature_name}' in {context} has type {type(value).__name__}, expected {expected_type}")
            
            for feature_name, expected_type in self.record_schema.optional_features.items():
                if feature_name in record:
                    value = record[feature_name]
                    if not self._check_feature_type(value, expected_type):
                        raise ValueError(f"Optional feature '{feature_name}' in {context} has type {type(value).__name__}, expected {expected_type}")
        
        # Handle single Dataset vs DatasetDict
        if isinstance(dataset, Dataset):
            dataset_dict = {"default": dataset}
        elif isinstance(dataset, DatasetDict):
            dataset_dict = dataset
        else:
            raise ValueError(f"Unsupported dataset type: {type(dataset)}")
        
        # Validate records in each split
        for split_name, split_dataset in dataset_dict.items():
            if not isinstance(split_dataset, Dataset):
                continue
                
            # Validate sample records from this split
            for i in range(min(sample_size, len(split_dataset))):
                try:
                    record = split_dataset[i]
                    validate_record_features(record, f"split '{split_name}' record {i}")
                except Exception as e:
                    raise ValueError(f"Record validation failed in split '{split_name}': {e}")
        
        return True
    
    def _check_feature_type(self, value: Any, expected_type: str) -> bool:
        """Check if value matches expected type string."""
        type_mapping = {
            'str': str,
            'int': int,
            'float': float,
            'bool': bool,
            'list': list,
            'dict': dict,
            'object': object
        }
        
        if expected_type in type_mapping:
            return isinstance(value, type_mapping[expected_type])
        elif "string" in expected_type.lower():
            # Handle HuggingFace string features (Value('string'))
            return isinstance(value, str)
        elif "int" in expected_type.lower():
            return isinstance(value, int)
        elif "float" in expected_type.lower():
            return isinstance(value, float)
        else:
            # Default to string representation match or just accept as valid
            return True  # Be permissive for complex HF feature types
    
    def validate(self, dataset: Union[Dataset, DatasetDict]) -> bool:
        """Validate both structure and records.
        
        Args:
            dataset: HuggingFace dataset object
            
        Returns:
            True if validation passes
            
        Raises:
            ValueError: If validation fails
        """
        self.validate_structure(dataset)
        self.validate_records(dataset)
        return True


def generate_dataset_schema_file(
    dataset: Union[Dataset, DatasetDict],
    dataset_name: str,
    output_dir: Union[str, Path] = "schemas",
    expected_splits: Optional[List[str]] = None
) -> Path:
    """Generate a Python schema file for a HuggingFace dataset.
    
    Args:
        dataset: HuggingFace dataset object
        dataset_name: Name for the schema file  
        output_dir: Directory to write schema files
        expected_splits: Specific splits to expect (if None, infer from dataset)
        
    Returns:
        Path to generated schema file
    """
    if not HF_DATASETS_AVAILABLE:
        raise ImportError("datasets library is required for dataset validation")
    
    from .dataset_utils import extract_dataset_metadata
    
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # Extract metadata
    metadata = extract_dataset_metadata(dataset)
    
    # Determine splits and structure
    if isinstance(dataset, DatasetDict):
        if expected_splits is None:
            expected_splits = list(dataset.keys())
        
        # Get features from first split
        first_split_name = list(dataset.keys())[0]
        first_split = dataset[first_split_name]
        
        if hasattr(first_split, 'features') and first_split.features:
            # Use HuggingFace features if available
            required_features = {name: str(feature) for name, feature in first_split.features.items()}
        else:
            # Infer from sample record
            if len(first_split) > 0:
                sample_record = first_split[0]
                required_features = {name: type(value).__name__ for name, value in sample_record.items()}
            else:
                required_features = {}
    
    elif isinstance(dataset, Dataset):
        if expected_splits is None:
            expected_splits = ["default"]
            
        if hasattr(dataset, 'features') and dataset.features:
            required_features = {name: str(feature) for name, feature in dataset.features.items()}
        else:
            # Infer from sample record
            if len(dataset) > 0:
                sample_record = dataset[0]
                required_features = {name: type(value).__name__ for name, value in sample_record.items()}
            else:
                required_features = {}
    else:
        raise ValueError(f"Unsupported dataset type: {type(dataset)}")
    
    # Generate schema file content
    schema_file = output_dir / f"{dataset_name}_dataset_schema.py"
    
    lines = [
        f'"""Auto-generated dataset schema for {dataset_name}."""',
        "",
        "from fosho.dataset_schema import DatasetStructureSchema, DatasetRecordSchema, DatasetSchema",
        "",
        "# Structure schema - defines expected splits",
        "structure_schema = DatasetStructureSchema(",
        f"    expected_splits={expected_splits},",
        f"    min_records_per_split=1",
        ")",
        "",
        "# Record schema - defines expected features in each record",
        "record_schema = DatasetRecordSchema(",
        f"    required_features={required_features}",
        ")",
        "",
        "# Combined schema",
        f"schema = DatasetSchema(structure_schema, record_schema, name='{dataset_name}')",
        "",
        "def validate_dataset(dataset):",
        '    """Validate dataset against schema."""',
        "    return schema.validate(dataset)",
    ]
    
    with open(schema_file, "w") as f:
        f.write("\n".join(lines))
    
    return schema_file