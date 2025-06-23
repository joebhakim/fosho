"""CRC32 file hashing and MD5 schema hashing utilities."""

import hashlib
import zlib
from pathlib import Path
from typing import Union

import pandera.pandas as pa


def compute_file_crc32(file_path: Union[str, Path]) -> str:
    """Compute CRC32 hash of a file, streaming in 1MB chunks.

    Args:
        file_path: Path to the file to hash

    Returns:
        8-character hex string of CRC32 hash
    """
    file_path = Path(file_path)
    crc32_hash = 0
    chunk_size = 1024 * 1024  # 1MB chunks

    with open(file_path, "rb") as f:
        while chunk := f.read(chunk_size):
            crc32_hash = zlib.crc32(chunk, crc32_hash)

    # Convert to unsigned 32-bit and format as 8-char hex
    return f"{crc32_hash & 0xffffffff:08x}"


def compute_schema_md5(schema: pa.DataFrameSchema) -> str:
    """Compute MD5 hash of a Pandera schema serialized to YAML.

    Args:
        schema: Pandera DataFrameSchema to hash

    Returns:
        32-character hex string of MD5 hash
    """
    schema_yaml = schema.to_yaml()
    if schema_yaml is None:
        raise ValueError("Schema YAML serialization returned None")
    schema_bytes = schema_yaml.encode("utf-8")
    return hashlib.md5(schema_bytes).hexdigest()


def compute_manifest_md5(manifest_content: str) -> str:
    """Compute MD5 hash of manifest.json content.

    Args:
        manifest_content: JSON string content of manifest

    Returns:
        32-character hex string of MD5 hash
    """
    return hashlib.md5(manifest_content.encode("utf-8")).hexdigest()
