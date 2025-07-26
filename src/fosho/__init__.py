from .reader import read_csv

# Dataset validation functionality
try:
    from .dataset_wrapper import load_dataset_with_schema, create_dataset_wrapper
    from .dataset_schema import generate_dataset_schema_file
    DATASET_SUPPORT = True
except ImportError:
    DATASET_SUPPORT = False

# Convenience function for dataset loading (matches pandas pattern)
if DATASET_SUPPORT:
    def load_dataset(dataset_name_or_path: str, schema: str, *args, **kwargs):
        """Load HuggingFace dataset with schema validation.
        
        Args:
            dataset_name_or_path: HuggingFace dataset name or local path
            schema: Path to schema file
            *args: Additional arguments passed to load_dataset
            **kwargs: Additional keyword arguments passed to load_dataset
            
        Returns:
            ValidatedDataset that can be validated with .validate()
            
        Example:
            >>> ds = fosho.load_dataset("Anthropic/hh-rlhf", "schemas/hh_rlhf_schema.py")
            >>> validated_ds = ds.validate()
            >>> for key in ["train", "test"]:
            ...     for record in validated_ds[key]:
            ...         chosen = record["chosen"]
        """
        return load_dataset_with_schema(dataset_name_or_path, schema, *args, **kwargs)

def main() -> None:
    """Main entry point for fosho CLI with dsq subcommands."""
    from .cli import app

    app()
