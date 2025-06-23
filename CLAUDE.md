# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
fosho is a **F**ile-&-schema **O**ffline **S**igning & **H**ash **O**bservatory - a Python package providing deterministic data-quality guard-rails for scientists who refuse to upload their data to the cloud. It focuses on byte-level immutability, offline approval loops, and Pythonic schema power using CRC32 file hashing and MD5 schema hashing.

## Development Commands

### Installation
```bash
# Development installation with uv
cd fosho/
uv sync --dev
```

### Running the Application
```bash
# Run the main CLI
uv run fosho

# Or via Python module
uv run python -m fosho
```

### Development Tools
```bash
# Type checking
uvx ty check

# Code formatting
uv run black .

# Linting
uv run ruff check

# Run tests
uv run pytest
```

### Key CLI Commands (Based on README)
The main CLI interface provides:
- `dsq scan` - Scan files and generate checksums
- `dsq sign` - Sign/approve files (toggles bit in manifest.json)  
- `dsq verify` - Verify file integrity against checksums

## Architecture

### Project Structure
```
fosho/
├── src/fosho/
│   ├── __init__.py          # Main entry point with main() function
│   └── run_checksum_tests.py # Currently empty, likely for checksum testing
├── pyproject.toml           # Python packaging configuration with uv support
└── README.md               # Empty placeholder
```

### Core Concepts
- **CRC32 file hashing** - Sub-second hashing for CSV/Parquet files
- **MD5 schema hashing** - Diff detection for Pandera schema rules
- **manifest.json** - Central file for tracking signed/approved data states
- **Offline-first workflow** - No cloud dependencies for approval loops
- **Pandera integration** - Pythonic schema definitions instead of YAML

### Python Configuration
- **Python version**: 3.12 (specified in .python-version)
- **Minimum Python**: >=3.12 (pyproject.toml)
- **Build system**: Hatchling
- **Package structure**: Modern src/ layout
- **Package manager**: uv (with dev dependencies: pytest, ruff, black)

### Entry Points
- Console script: `fosho` command maps to `fosho:main`
- Main function: `fosho/__init__.py:main()`

## Current Development Status
This appears to be an early-stage project with:
- Basic package structure in place
- README with comprehensive feature planning
- Minimal implementation (main() just prints "Hello from fosho!")
- Empty test files and placeholder documentation
- Updated to use modern uv tooling

The README indicates planned features including offline anomaly detection, DuckDB/Delta-Lake support, and future cryptographic signing capabilities.