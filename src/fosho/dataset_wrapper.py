"""Dataset wrapper providing schema validation for HuggingFace datasets."""

import importlib.util
from typing import Union, Optional
from pathlib import Path

try:
    from datasets import Dataset, DatasetDict
    HF_DATASETS_AVAILABLE = True
except ImportError:
    HF_DATASETS_AVAILABLE = False
    Dataset = None
    DatasetDict = None

from .dataset_schema import DatasetSchema


class ValidatedDataset:
    """Wrapper around HuggingFace Dataset/DatasetDict with schema validation.
    
    Provides the same interface as the original dataset but with a .validate() method
    that ensures the dataset conforms to the expected schema before use.
    """
    
    def __init__(
        self, 
        dataset: Union[Dataset, DatasetDict], 
        schema: Union[DatasetSchema, str, Path],
        dataset_name: Optional[str] = None
    ):
        """Initialize validated dataset wrapper.
        
        Args:
            dataset: HuggingFace Dataset or DatasetDict object
            schema: DatasetSchema object or path to schema file
            dataset_name: Optional name for the dataset
        """
        if not HF_DATASETS_AVAILABLE:
            raise ImportError("datasets library is required for dataset validation")
        
        self._dataset = dataset
        self._dataset_name = dataset_name
        self._validated = False
        
        # Load schema if provided as path
        if isinstance(schema, (str, Path)):
            self._schema = self._load_schema_from_file(schema)
        elif isinstance(schema, DatasetSchema):
            self._schema = schema
        else:
            raise ValueError("Schema must be either a DatasetSchema object or path to schema file")
    
    def _load_schema_from_file(self, schema_path: Union[str, Path]) -> DatasetSchema:
        """Load schema from Python file."""
        schema_path = Path(schema_path)
        
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")
        
        # Load the schema module
        spec = importlib.util.spec_from_file_location("schema_module", schema_path)
        schema_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(schema_module)
        
        # Get the schema object
        if hasattr(schema_module, 'schema'):
            return schema_module.schema
        else:
            raise ValueError(f"Schema file {schema_path} must contain a 'schema' variable")
    
    def validate(self):
        """Validate dataset against schema and return self for chaining.
        
        Returns:
            Self for method chaining (same pattern as pandas DataFrame.validate())
            
        Raises:
            ValueError: If validation fails
        """
        try:
            self._schema.validate(self._dataset)
            self._validated = True
            return self
        except Exception as e:
            raise ValueError(f"Dataset validation failed: {e}")
    
    def __getattr__(self, name):
        """Delegate attribute access to the wrapped dataset."""
        if name.startswith('_'):
            # Avoid infinite recursion for private attributes
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
        
        return getattr(self._dataset, name)
    
    def __getitem__(self, key):
        """Delegate item access to the wrapped dataset."""
        return self._dataset[key]
    
    def __len__(self):
        """Delegate length to the wrapped dataset."""
        return len(self._dataset)
    
    def __iter__(self):
        """Delegate iteration to the wrapped dataset."""
        return iter(self._dataset)
    
    def __repr__(self):
        """String representation including validation status."""
        validation_status = "✓ Validated" if self._validated else "⚠ Not validated"
        dataset_info = repr(self._dataset)
        return f"ValidatedDataset({validation_status}):\n{dataset_info}"
    
    @property
    def is_validated(self) -> bool:
        """Check if dataset has been validated."""
        return self._validated
    
    @property
    def schema(self) -> DatasetSchema:
        """Get the dataset schema."""
        return self._schema
    
    @property
    def dataset_name(self) -> Optional[str]:
        """Get the dataset name."""
        return self._dataset_name


def load_dataset_with_schema(
    dataset_name_or_path: str,
    schema_path: Union[str, Path],
    *args,
    **kwargs
) -> ValidatedDataset:
    """Load a HuggingFace dataset with schema validation.
    
    This function loads a dataset using the datasets library and wraps it
    with schema validation capabilities.
    
    Args:
        dataset_name_or_path: HuggingFace dataset name or local path
        schema_path: Path to the schema file
        *args: Additional arguments passed to load_dataset
        **kwargs: Additional keyword arguments passed to load_dataset
        
    Returns:
        ValidatedDataset wrapper
        
    Example:
        >>> ds = load_dataset_with_schema(
        ...     "Anthropic/hh-rlhf", 
        ...     "schemas/hh_rlhf_dataset_schema.py"
        ... )
        >>> validated_ds = ds.validate()
        >>> for key in ["train", "test"]:  # Now safe to use
        ...     for record in validated_ds[key]:
        ...         chosen = record["chosen"]
        ...         rejected = record["rejected"]
    """
    if not HF_DATASETS_AVAILABLE:
        raise ImportError("datasets library is required. Install with: pip install datasets")
    
    from datasets import load_dataset
    
    # Load the dataset
    dataset = load_dataset(dataset_name_or_path, *args, **kwargs)
    
    # Wrap with validation
    return ValidatedDataset(dataset, schema_path, dataset_name_or_path)


def create_dataset_wrapper(
    dataset: Union[Dataset, DatasetDict],
    schema_path: Union[str, Path],
    dataset_name: Optional[str] = None
) -> ValidatedDataset:
    """Create a validated wrapper around an existing dataset.
    
    Args:
        dataset: Existing HuggingFace dataset object
        schema_path: Path to the schema file
        dataset_name: Optional name for the dataset
        
    Returns:
        ValidatedDataset wrapper
        
    Example:
        >>> from datasets import load_dataset
        >>> ds = load_dataset("Anthropic/hh-rlhf")
        >>> validated_ds = create_dataset_wrapper(
        ...     ds, 
        ...     "schemas/hh_rlhf_dataset_schema.py",
        ...     "hh-rlhf"
        ... ).validate()
    """
    return ValidatedDataset(dataset, schema_path, dataset_name)