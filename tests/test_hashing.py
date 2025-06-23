"""Tests for hashing functionality."""

import tempfile
from pathlib import Path

import pandas as pd
import pandera.pandas as pa
import pytest

from fosho.hashing import compute_file_crc32, compute_schema_md5, compute_manifest_md5


def test_compute_file_crc32():
    """Test CRC32 file hashing."""
    # Create a temporary file with known content
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("Hello, World!")
        temp_path = f.name
    
    try:
        # Compute CRC32
        crc32_hash = compute_file_crc32(temp_path)
        
        # Should be 8-character hex string
        assert len(crc32_hash) == 8
        assert all(c in '0123456789abcdef' for c in crc32_hash)
        
        # Should be deterministic
        assert compute_file_crc32(temp_path) == crc32_hash
        
    finally:
        Path(temp_path).unlink()


def test_compute_file_crc32_different_content():
    """Test that different content produces different CRC32."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f1:
        f1.write("Content A")
        path1 = f1.name
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f2:
        f2.write("Content B")
        path2 = f2.name
    
    try:
        hash1 = compute_file_crc32(path1)
        hash2 = compute_file_crc32(path2)
        
        assert hash1 != hash2
        
    finally:
        Path(path1).unlink()
        Path(path2).unlink()


def test_compute_schema_md5():
    """Test MD5 schema hashing."""
    # Create a simple schema
    schema = pa.DataFrameSchema({
        "col1": pa.Column(int),
        "col2": pa.Column(str, nullable=True)
    })
    
    # Compute MD5
    md5_hash = compute_schema_md5(schema)
    
    # Should be 32-character hex string
    assert len(md5_hash) == 32
    assert all(c in '0123456789abcdef' for c in md5_hash)
    
    # Should be deterministic
    assert compute_schema_md5(schema) == md5_hash


def test_compute_schema_md5_different_schemas():
    """Test that different schemas produce different MD5."""
    schema1 = pa.DataFrameSchema({
        "col1": pa.Column(int),
        "col2": pa.Column(str)
    })
    
    schema2 = pa.DataFrameSchema({
        "col1": pa.Column(float),  # Different type
        "col2": pa.Column(str)
    })
    
    hash1 = compute_schema_md5(schema1)
    hash2 = compute_schema_md5(schema2)
    
    assert hash1 != hash2


def test_compute_manifest_md5():
    """Test manifest MD5 hashing."""
    manifest_content = '{"datasets": {}, "test": true}'
    
    md5_hash = compute_manifest_md5(manifest_content)
    
    # Should be 32-character hex string
    assert len(md5_hash) == 32
    assert all(c in '0123456789abcdef' for c in md5_hash)
    
    # Should be deterministic
    assert compute_manifest_md5(manifest_content) == md5_hash


def test_compute_manifest_md5_different_content():
    """Test that different manifest content produces different MD5."""
    content1 = '{"datasets": {}, "test": true}'
    content2 = '{"datasets": {}, "test": false}'
    
    hash1 = compute_manifest_md5(content1)
    hash2 = compute_manifest_md5(content2)
    
    assert hash1 != hash2