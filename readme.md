# fosho - Data Signing & Quality

**F**ile-&-schema **O**ffline **S**igning & **H**ash **O**bservatory

Deterministic data-quality guard-rails for scientists who refuse to upload their data to the cloud. Provides byte-level immutability with CRC32 file hashing, MD5 schema hashing, and offline approval loops using Pandera schemas.

## Key Features

- **CRC32 file hashing** - Sub-second hashing for CSV/Parquet files with 1MB streaming chunks
- **MD5 schema hashing** - Detects changes in Pandera schema definitions  
- **Offline-first workflow** - No cloud dependencies for approval loops
- **Automatic schema scaffolding** - Infers Pandera schemas with multi-index and nested field support
- **CLI interface** - Simple `scan`, `sign`, `verify` workflow for CI/CD integration
- **Comprehensive testing** - 24 passing tests with edge case coverage

## Installation

```bash
# Install with uv (recommended)
cd fosho
uv sync --dev

# Or with pip
pip install -e ".[dev]"
```

## Quick Start

The core workflow involves three commands: `scan`, `sign`, and `verify`:

```bash
# 1. Generate example datasets
uv run python examples/generate_examples.py

# 2. Scan directory for datasets → writes schema stubs & unsigned manifest
uv run fosho scan examples/data/

# 3. Review generated schemas in schemas/ directory (optional)
ls schemas/

# 4. Sign datasets → marks all as approved in manifest.json  
uv run fosho sign

# 5. Verify integrity → exits 0 (success) or 1 (failure)
uv run fosho verify
```

## CLI Commands

### `fosho scan [PATH]`
- Discovers all `*.csv` and `*.parquet` files recursively
- Computes CRC32 checksums for each file
- Auto-generates Pandera schema stubs in `schemas/` directory
- Updates `manifest.json` with unsigned entries for new/changed files
- Use `--overwrite-schemas` to regenerate existing schema files

### `fosho sign`
- Verifies all files exist and checksums match current state
- Marks all datasets as signed with UTC timestamps
- Updates manifest integrity hash

### `fosho verify`
- Loads manifest and verifies its integrity
- Checks all files exist and match their checksums
- Automatically unsigns datasets with checksum mismatches
- Exits with code 0 on success, 1 on failure

### `fosho status`
- Shows table of all datasets with their signing status
- Displays CRC32 hashes and signing timestamps

## Example Datasets

The package includes 4 example datasets that test edge cases:

- **`complex_metrics.csv`** - Weird column names, mixed dtypes, NaN values
- **`vitals_multiindex.csv`** - Multi-level column headers
- **`nested_json.csv`** - JSON strings in columns
- **`static_notes.csv`** - Randomized column order to test CRC32 sensitivity

Generate examples:
```bash
uv run python examples/generate_examples.py
```

## Manifest Format

The `manifest.json` file tracks dataset integrity:

```json
{
  "datasets": {
    "examples/data/complex_metrics.csv": {
      "crc32": "6046382b",
      "schema_md5": "1d87476c32b102275e385d5f699366b4",
      "signed": true,
      "signed_at": "2025-06-23T01:34:04.990291Z"
    }
  },
  "manifest_md5": "d0df2253b95bae1ac026fee7776e6e62"
}
```

## Schema Generation

Automatically generates executable Pandera schema files:

```python
"""Auto-generated Pandera schema for complex_metrics.csv."""

import pandera.pandas as pa
from pandera.typing import DataFrame

# Schema definition in YAML format:
schema_yaml = """
schema_type: dataframe
version: 0.24.0
columns:
  Patient ID#:
    dtype: int64
    nullable: false
    checks:
    - value: 1
      options:
        check_name: greater_than_or_equal_to
  # ... more columns
"""

# Load schema from YAML  
schema = pa.io.from_yaml(schema_yaml)

def validate_dataframe(df) -> DataFrame:
    """Validate DataFrame against schema."""
    return schema.validate(df)
```

## Development

### Setup
```bash
# Install dependencies
uv sync --dev

# Run tests
uv run python -m pytest tests/ -v

# Type checking  
uvx ty check src/

# Code formatting
uv run black src/
```

### Testing
```bash
# Run all tests
uv run python -m pytest tests/ -v

# Quick test
uv run python -m pytest tests/ -q

# Test specific module
uv run python -m pytest tests/test_cli_flow.py -v
```

All 24 tests pass without external network dependencies.

## Workflow Example

```bash
# Initial scan
$ uv run fosho scan examples/data/
Found 4 dataset(s)
Processing: examples/data/complex_metrics.csv
  Added (unsigned)
  Schema: schemas/complex_metrics_schema.py
Manifest updated: manifest.json

# Sign datasets
$ uv run fosho sign
Verifying datasets before signing...
Successfully signed 4 dataset(s)

# Verify integrity
$ uv run fosho verify
All datasets verified successfully

# Simulate file drift
$ echo "tampered data" >> examples/data/complex_metrics.csv

# Verify detects changes
$ uv run fosho verify
Verification failed:
  - Checksum mismatch: examples/data/complex_metrics.csv

# Re-scan updates checksums
$ uv run fosho scan examples/data/
Processing: examples/data/complex_metrics.csv
  Updated (unsigned due to changes)
```

## Architecture

### Core Components

- **`src/fosho/hashing.py`** - CRC32 file hashing and MD5 schema hashing utilities
- **`src/fosho/manifest.py`** - JSON manifest file operations with integrity checking
- **`src/fosho/scaffold.py`** - Automatic Pandera schema inference with multi-index support
- **`src/fosho/cli.py`** - Typer-based command line interface

### Project Structure
```
fosho/
├── src/fosho/           # Python package source
├── tests/               # Comprehensive test suite  
├── examples/            # Example datasets & generator
├── schemas/             # Auto-generated Pandera schemas
├── manifest.json        # Dataset integrity tracking
├── pyproject.toml       # Modern Python packaging
└── readme.md           # This file
```

## Design Principles

- **Deterministic**: Same data always produces same hashes
- **Offline**: No network dependencies or cloud services
- **Transparent**: Human-readable manifest and schema files
- **Fast**: CRC32 streaming for large files
- **Safe**: Immutable workflows with explicit signing steps
- **Pythonic**: First-class Pandera integration with executable schemas