"""Auto-infer Pandera schemas from datasets."""

import re
from pathlib import Path
from typing import List, Tuple, Union, Optional

import pandas as pd
import pandera.pandas as pa
from pandera.typing import DataFrame


def create_schema_slug(file_path: Union[str, Path]) -> str:
    """Create a schema slug from file path."""
    file_path = Path(file_path)
    # Remove file extension and make filesystem-safe
    slug = file_path.stem
    slug = re.sub(r"[^a-zA-Z0-9_]", "_", slug)
    slug = re.sub(r"_+", "_", slug)  # Collapse multiple underscores
    return slug


def detect_multiindex_columns(df: pd.DataFrame) -> bool:
    """Detect if DataFrame has multi-level column names."""
    return isinstance(df.columns, pd.MultiIndex)


def infer_column_schema(series: pd.Series, col_name: Union[str, Tuple]) -> pa.Column:
    """Infer Pandera column schema from pandas Series."""
    dtype = series.dtype
    nullable = bool(series.isnull().any())  # Convert numpy.bool_ to bool

    # Handle different dtypes
    if pd.api.types.is_integer_dtype(dtype):
        # For integers, assume non-negative if all values >= 0
        checks = []
        if not nullable and len(series) > 0:
            min_val = series.min()
            if min_val >= 0:
                checks.append(pa.Check.greater_than_or_equal_to(int(min_val)))
        return pa.Column(dtype, nullable=nullable, checks=checks)

    elif pd.api.types.is_float_dtype(dtype):
        return pa.Column(dtype, nullable=True)  # Floats can have NaN

    elif pd.api.types.is_bool_dtype(dtype):
        return pa.Column(dtype, nullable=nullable)

    elif pd.api.types.is_datetime64_any_dtype(dtype):
        return pa.Column(dtype, nullable=nullable)

    else:
        # Default to object/string type
        return pa.Column("object", nullable=True)


def detect_index_columns(df: pd.DataFrame) -> List[str]:
    """Detect columns that look like index columns."""
    index_columns = []

    for col in df.columns:
        col_name = col if isinstance(col, str) else str(col)
        # Check for unnamed columns or columns that look like default index names
        if (
            col_name == ""
            or col_name.startswith("Unnamed:")
            or col_name.lower() in ["index", "id"]
        ):
            index_columns.append(col)

    return index_columns


def scaffold_schema_from_dataframe(
    df: pd.DataFrame, file_path: Union[str, Path]
) -> pa.DataFrameSchema:
    """Create a Pandera schema from a DataFrame."""
    columns = {}
    index_schemas = []

    # Handle multi-index columns
    if detect_multiindex_columns(df):
        for col in df.columns:
            columns[col] = infer_column_schema(df[col], col)
    else:
        # Detect potential index columns
        index_columns = detect_index_columns(df)

        for col in df.columns:
            if col in index_columns:
                # Create index schema
                index_schema = pa.Index(df[col].dtype, name=col if col != "" else None)
                index_schemas.append(index_schema)
            else:
                columns[col] = infer_column_schema(df[col], col)

    # Create schema
    if index_schemas:
        if len(index_schemas) == 1:
            return pa.DataFrameSchema(columns=columns, index=index_schemas[0])
        else:
            return pa.DataFrameSchema(
                columns=columns, index=pa.MultiIndex(index_schemas)
            )
    else:
        return pa.DataFrameSchema(columns=columns)


def load_dataset(file_path: Union[str, Path]) -> pd.DataFrame:
    """Load dataset from CSV or Parquet file."""
    file_path = Path(file_path)

    if file_path.suffix.lower() == ".csv":
        # Try to detect multi-header CSV files
        # First, peek at the first few lines to detect headers
        with open(file_path, "r") as f:
            first_lines = [f.readline().strip() for _ in range(3)]

        # Simple heuristic: if first two lines have similar structure, assume multi-header
        if len(first_lines) >= 2:
            first_commas = first_lines[0].count(",")
            second_commas = first_lines[1].count(",")

            if abs(first_commas - second_commas) <= 1 and first_commas > 0:
                # Try loading with multi-header
                try:
                    df = pd.read_csv(file_path, header=[0, 1])
                    if len(df.columns.names) == 2:  # Successfully loaded multi-header
                        return df
                except:
                    pass

        # Fall back to single header
        return pd.read_csv(file_path)

    elif file_path.suffix.lower() in [".parquet", ".pq"]:
        return pd.read_parquet(file_path)

    else:
        raise ValueError(f"Unsupported file format: {file_path.suffix}")


def generate_schema_file(
    schema: pa.DataFrameSchema,
    file_path: Union[str, Path],
    output_dir: Union[str, Path] = "schemas",
) -> Path:
    """Generate Python schema file from Pandera schema."""
    file_path = Path(file_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)

    slug = create_schema_slug(file_path)
    schema_file = output_dir / f"{slug}_schema.py"

    # Generate schema code
    schema_yaml = schema.to_yaml()

    schema_code = f'''"""Auto-generated Pandera schema for {file_path.name}."""

import pandera.pandas as pa
from pandera.typing import DataFrame

# Schema definition in YAML format:
schema_yaml = """
{schema_yaml}
"""

# Load schema from YAML
schema = pa.io.from_yaml(schema_yaml)

def validate_dataframe(df) -> DataFrame:
    """Validate DataFrame against schema."""
    return schema.validate(df)
'''

    with open(schema_file, "w") as f:
        f.write(schema_code)

    return schema_file


def scaffold_dataset_schema(
    file_path: Union[str, Path],
    output_dir: Union[str, Path] = "schemas",
    overwrite: bool = False,
) -> Tuple[pa.DataFrameSchema, Optional[Path]]:
    """Scaffold schema for a dataset file.

    Args:
        file_path: Path to dataset file
        output_dir: Directory to write schema files
        overwrite: Whether to overwrite existing schema files

    Returns:
        Tuple of (schema, schema_file_path)
    """
    file_path = Path(file_path)
    output_dir = Path(output_dir)

    slug = create_schema_slug(file_path)
    schema_file = output_dir / f"{slug}_schema.py"

    # Check if schema file already exists
    if schema_file.exists() and not overwrite:
        # Try to load existing schema
        try:
            import importlib.util
            import types

            spec = importlib.util.spec_from_file_location(f"{slug}_schema", schema_file)
            if spec is None or spec.loader is None:
                raise ImportError("Could not load schema module")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if not hasattr(module, "schema"):
                raise AttributeError("Schema module has no 'schema' attribute")
            return module.schema, schema_file  # type: ignore
        except:
            # If loading fails, regenerate
            pass

    # Load dataset and generate schema
    df = load_dataset(file_path)
    schema = scaffold_schema_from_dataframe(df, file_path)

    # Generate schema file
    schema_file_path = generate_schema_file(schema, file_path, output_dir)

    return schema, schema_file_path
