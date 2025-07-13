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
    """Infer simple Pandera column schema from pandas Series."""
    dtype = series.dtype
    nullable = bool(series.isnull().any())  # Convert numpy.bool_ to bool

    # Simple schema: just dtype and nullable, no complex checks
    return pa.Column(dtype, nullable=nullable)


def detect_index_columns(df: pd.DataFrame) -> List[str]:
    """Detect columns that look like index columns."""
    index_columns = []

    for col in df.columns:
        col_name = col if isinstance(col, str) else str(col)
        # Only detect truly unnamed columns - be more conservative
        if (
            col_name == ""
            or col_name.startswith("Unnamed:")
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

        # Disable multi-header detection for now - keep it simple
        # Simple heuristic: if first two lines have similar structure, assume multi-header
        # if len(first_lines) >= 2:
        #     first_commas = first_lines[0].count(",")
        #     second_commas = first_lines[1].count(",")

        #     if abs(first_commas - second_commas) <= 1 and first_commas > 0:
        #         # Try loading with multi-header
        #         try:
        #             df = pd.read_csv(file_path, header=[0, 1])
        #             if len(df.columns.names) == 2:  # Successfully loaded multi-header
        #                 return df
        #         except:
        #             pass

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
    """Generate simple Python schema file from Pandera schema."""
    file_path = Path(file_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)

    slug = create_schema_slug(file_path)
    schema_file = output_dir / f"{slug}_schema.py"

    # Generate simple Python schema content
    lines = [
        f'"""Auto-generated schema for {file_path.name}."""',
        "",
        "import pandera.pandas as pa",
        "",
        "schema = pa.DataFrameSchema({",
    ]
    
    for col_name, col_schema in schema.columns.items():
        # Handle column names with special characters
        if isinstance(col_name, str) and col_name.isidentifier():
            col_repr = f'"{col_name}"'
        else:
            col_repr = repr(col_name)
        
        # Preserve exact pandas dtype to maintain consistency
        dtype_name = str(col_schema.dtype)
        if "int" in dtype_name:
            dtype_str = "int"
        elif "float" in dtype_name:
            dtype_str = "float"
        elif "object" in dtype_name:
            # Keep as object dtype to match pandas inference
            dtype_str = "object"
        elif "string" in dtype_name:
            dtype_str = "str"
        elif "bool" in dtype_name:
            dtype_str = "bool"
        else:
            dtype_str = "object"  # Default to object to match pandas behavior
        
        # Simple column definition
        if col_schema.nullable:
            lines.append(f'    {col_repr}: pa.Column({dtype_str}, nullable=True),')
        else:
            lines.append(f'    {col_repr}: pa.Column({dtype_str}),')
    
    lines.extend([
        "})",
        "",
        "def validate_dataframe(df):",
        '    """Validate DataFrame against schema."""',
        "    return schema.validate(df)",
    ])

    with open(schema_file, "w") as f:
        f.write("\n".join(lines))

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
            spec = importlib.util.spec_from_file_location("schema_module", schema_file)
            schema_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(schema_module)
            schema = schema_module.schema
            return schema, schema_file
        except:
            # If loading fails, regenerate
            pass

    # Load dataset and generate schema
    df = load_dataset(file_path)
    schema = scaffold_schema_from_dataframe(df, file_path)

    # Generate schema file
    schema_file_path = generate_schema_file(schema, file_path, output_dir)

    return schema, schema_file_path
