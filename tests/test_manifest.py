"""Tests for manifest functionality."""

import json
import tempfile
from pathlib import Path

import pytest

from fosho.manifest import Manifest


def test_manifest_initialization():
    """Test manifest initialization."""
    manifest = Manifest()
    assert manifest.data == {"datasets": {}}


def test_manifest_add_dataset():
    """Test adding dataset to manifest."""
    manifest = Manifest()
    
    manifest.add_dataset("test.csv", "abc12345", "def67890")
    
    assert "test.csv" in manifest.data["datasets"]
    dataset = manifest.data["datasets"]["test.csv"]
    assert dataset["crc32"] == "abc12345"
    assert dataset["schema_md5"] == "def67890"
    assert dataset["signed"] == False
    assert dataset["signed_at"] is None


def test_manifest_add_dataset_signed():
    """Test adding signed dataset to manifest."""
    manifest = Manifest()
    
    manifest.add_dataset("test.csv", "abc12345", "def67890", signed=True)
    
    dataset = manifest.data["datasets"]["test.csv"]
    assert dataset["signed"] == True
    assert dataset["signed_at"] is not None


def test_manifest_sign_dataset():
    """Test signing a dataset."""
    manifest = Manifest()
    manifest.add_dataset("test.csv", "abc12345", "def67890")
    
    manifest.sign_dataset("test.csv")
    
    dataset = manifest.data["datasets"]["test.csv"]
    assert dataset["signed"] == True
    assert dataset["signed_at"] is not None


def test_manifest_sign_all():
    """Test signing all datasets."""
    manifest = Manifest()
    manifest.add_dataset("test1.csv", "abc12345", "def67890")
    manifest.add_dataset("test2.csv", "ghi12345", "jkl67890")
    
    manifest.sign_all()
    
    for dataset in manifest.data["datasets"].values():
        assert dataset["signed"] == True
        assert dataset["signed_at"] is not None


def test_manifest_unsign_dataset():
    """Test unsigning a dataset."""
    manifest = Manifest()
    manifest.add_dataset("test.csv", "abc12345", "def67890", signed=True)
    
    manifest.unsign_dataset("test.csv")
    
    dataset = manifest.data["datasets"]["test.csv"]
    assert dataset["signed"] == False
    assert dataset["signed_at"] is None


def test_manifest_get_dataset():
    """Test getting dataset by path."""
    manifest = Manifest()
    manifest.add_dataset("test.csv", "abc12345", "def67890")
    
    dataset = manifest.get_dataset("test.csv")
    assert dataset is not None
    assert dataset["crc32"] == "abc12345"
    
    # Non-existent dataset
    assert manifest.get_dataset("nonexistent.csv") is None


def test_manifest_has_dataset():
    """Test checking if dataset exists."""
    manifest = Manifest()
    manifest.add_dataset("test.csv", "abc12345", "def67890")
    
    assert manifest.has_dataset("test.csv") == True
    assert manifest.has_dataset("nonexistent.csv") == False


def test_manifest_save_and_load():
    """Test saving and loading manifest."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manifest_path = Path(tmpdir) / "test_manifest.json"
        
        # Create and populate manifest
        manifest = Manifest(str(manifest_path))
        manifest.add_dataset("test.csv", "abc12345", "def67890")
        manifest.save()
        
        # Load in new instance
        manifest2 = Manifest(str(manifest_path))
        manifest2.load()
        
        assert manifest2.has_dataset("test.csv")
        dataset = manifest2.get_dataset("test.csv")
        assert dataset["crc32"] == "abc12345"
        assert dataset["schema_md5"] == "def67890"


def test_manifest_integrity_verification():
    """Test manifest integrity verification."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manifest_path = Path(tmpdir) / "test_manifest.json"
        
        # Create manifest
        manifest = Manifest(str(manifest_path))
        manifest.add_dataset("test.csv", "abc12345", "def67890")
        manifest.save()
        
        # Load and verify
        manifest2 = Manifest(str(manifest_path))
        manifest2.load()
        assert manifest2.verify_integrity() == True
        
        # Tamper with manifest file
        with open(manifest_path, 'r') as f:
            data = json.load(f)
        
        data["datasets"]["test.csv"]["crc32"] = "tampered"
        
        with open(manifest_path, 'w') as f:
            json.dump(data, f)
        
        # Load tampered manifest
        manifest3 = Manifest(str(manifest_path))
        manifest3.load()
        assert manifest3.verify_integrity() == False


def test_manifest_nonexistent_file():
    """Test loading nonexistent manifest file."""
    manifest = Manifest("nonexistent_manifest.json")
    manifest.load()  # Should not raise error
    assert manifest.data == {"datasets": {}}