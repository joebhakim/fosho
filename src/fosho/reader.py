"""Data reading with validation integration."""

import pandas as pd
import pandera.pandas as pa
from pathlib import Path
from typing import Union, Any
from .manifest import Manifest
from .hashing import compute_file_crc32, compute_schema_md5


class ValidatedDataFrame:
    """Wrapper around pandas DataFrame with validation guarantees."""
    
    def __init__(self, df: pd.DataFrame, file_path: str, schema_path: str, manifest: Manifest):
        self._df = df
        self._file_path = file_path
        self._schema_path = schema_path
        self._manifest = manifest
        self._schema = None
        self._validated = False
    
    def validate(self) -> pd.DataFrame:
        """Validate DataFrame against schema and manifest. Raises error if not signed."""
        # Check if dataset is signed in manifest
        dataset_info = self._manifest.get_dataset(self._file_path)
        if not dataset_info:
            raise ValueError(f"Dataset {self._file_path} not found in manifest. Run 'fosho scan' first.")
        
        if not dataset_info["signed"]:
            raise ValueError(f"Dataset {self._file_path} is not signed. Run 'fosho sign' first.")
        
        # Verify file hasn't changed since signing
        current_crc32 = compute_file_crc32(self._file_path)
        if current_crc32 != dataset_info["crc32"]:
            raise ValueError(f"Dataset {self._file_path} has been modified since signing. CRC32 mismatch.")
        
        # Load and verify schema
        schema_path = Path(self._schema_path)
        if not schema_path.exists():
            raise ValueError(f"Schema file {self._schema_path} not found.")
        
        # Load Python schema module
        import importlib.util
        spec = importlib.util.spec_from_file_location("schema_module", schema_path)
        schema_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(schema_module)
        self._schema = schema_module.schema
        
        # Verify schema hasn't changed since signing
        schema_md5 = compute_schema_md5(self._schema)
        if schema_md5 != dataset_info["schema_md5"]:
            raise ValueError(f"Schema {self._schema_path} has been modified since signing. MD5 mismatch.")
        
        # Validate DataFrame against schema
        validated_df = self._schema.validate(self._df)
        self._validated = True
        return validated_df
    
    def __getattr__(self, name: str) -> Any:
        """Delegate attribute access to underlying DataFrame."""
        if not self._validated:
            raise ValueError("DataFrame not validated. Call .validate() first.")
        return getattr(self._df, name)
    
    def __getitem__(self, key):
        """Delegate item access to underlying DataFrame."""
        if not self._validated:
            raise ValueError("DataFrame not validated. Call .validate() first.")
        return self._df[key]
    
    def __repr__(self) -> str:
        status = "validated" if self._validated else "unvalidated"
        return f"ValidatedDataFrame({status}, shape={self._df.shape})"


def read_csv(file: Union[str, Path], schema: Union[str, Path], 
             manifest_path: str = "manifest.json") -> ValidatedDataFrame:
    """Read CSV file with validation integration.
    
    Args:
        file: Path to CSV file
        schema: Path to Python schema file
        manifest_path: Path to manifest.json file
    
    Returns:
        ValidatedDataFrame wrapper with validation methods
    """
    file_path = Path(file)
    schema_path = Path(schema)
    
    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found: {file}")
    
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema}")
    
    # Load DataFrame
    df = pd.read_csv(file_path)
    
    # Load manifest
    manifest = Manifest(manifest_path)
    manifest.load()
    
    # Create relative path for manifest lookup
    try:
        relative_file_path = str(file_path.relative_to(Path.cwd()))
    except ValueError:
        relative_file_path = str(file_path)
    
    return ValidatedDataFrame(df, relative_file_path, str(schema_path), manifest)


def read_csv_with_schema(file: Union[str, Path], schema: pa.DataFrameSchema) -> ValidatedDataFrame:
    """Read CSV file with provided schema for validation (used during signing).
    
    Args:
        file: Path to CSV file
        schema: Pandera DataFrameSchema object
    
    Returns:
        ValidatedDataFrame wrapper with validation methods
    """
    file_path = Path(file)
    
    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found: {file}")
    
    # Load DataFrame
    df = pd.read_csv(file_path)
    
    # Create a minimal ValidatedDataFrame for testing validation only
    class MinimalValidatedDataFrame:
        def __init__(self, df: pd.DataFrame, schema: pa.DataFrameSchema):
            self._df = df
            self._schema = schema
        
        def validate(self) -> pd.DataFrame:
            """Validate DataFrame against schema."""
            return self._schema.validate(self._df)
    
    return MinimalValidatedDataFrame(df, schema)