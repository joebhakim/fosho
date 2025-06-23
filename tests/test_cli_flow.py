"""Integration tests for CLI flow."""

import json
import tempfile
from pathlib import Path

import pandas as pd
import pytest
from typer.testing import CliRunner

from fosho.cli import app


@pytest.fixture
def temp_workspace():
    """Create temporary workspace with test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        
        # Create test CSV
        data = pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['Alice', 'Bob', 'Charlie'],
            'age': [25, 30, 35]
        })
        
        csv_path = workspace / "test.csv"
        data.to_csv(csv_path, index=False)
        
        yield workspace


def test_cli_scan_command(temp_workspace):
    """Test dsq scan command."""
    runner = CliRunner()
    
    # Change to temp workspace
    original_cwd = Path.cwd()
    try:
        import os
        os.chdir(temp_workspace)
        
        # Run scan command
        result = runner.invoke(app, ["scan", "."])
        
        assert result.exit_code == 0
        assert "Found 1 dataset(s)" in result.stdout
        assert "Processing: test.csv" in result.stdout
        
        # Check manifest was created
        manifest_path = temp_workspace / "manifest.json"
        assert manifest_path.exists()
        
        with open(manifest_path) as f:
            manifest = json.load(f)
        
        assert "datasets" in manifest
        assert "test.csv" in manifest["datasets"]
        assert manifest["datasets"]["test.csv"]["signed"] == False
        
    finally:
        os.chdir(original_cwd)


def test_cli_sign_command(temp_workspace):
    """Test dsq sign command."""
    runner = CliRunner()
    
    original_cwd = Path.cwd()
    try:
        import os
        os.chdir(temp_workspace)
        
        # First scan
        result = runner.invoke(app, ["scan", "."])
        assert result.exit_code == 0
        
        # Then sign
        result = runner.invoke(app, ["sign"])
        assert result.exit_code == 0
        assert "Successfully signed 1 dataset(s)" in result.stdout
        
        # Check manifest was updated
        with open("manifest.json") as f:
            manifest = json.load(f)
        
        assert manifest["datasets"]["test.csv"]["signed"] == True
        assert manifest["datasets"]["test.csv"]["signed_at"] is not None
        
    finally:
        os.chdir(original_cwd)


def test_cli_verify_command(temp_workspace):
    """Test dsq verify command."""
    runner = CliRunner()
    
    original_cwd = Path.cwd()
    try:
        import os
        os.chdir(temp_workspace)
        
        # Scan and sign
        runner.invoke(app, ["scan", "."])
        runner.invoke(app, ["sign"])
        
        # Verify should pass
        result = runner.invoke(app, ["verify"])
        assert result.exit_code == 0
        assert "All datasets verified successfully" in result.stdout
        
    finally:
        os.chdir(original_cwd)


def test_cli_verify_with_unsigned_dataset(temp_workspace):
    """Test dsq verify command with unsigned dataset."""
    runner = CliRunner()
    
    original_cwd = Path.cwd()
    try:
        import os
        os.chdir(temp_workspace)
        
        # Only scan, don't sign
        runner.invoke(app, ["scan", "."])
        
        # Verify should fail with warning
        result = runner.invoke(app, ["verify"])
        assert result.exit_code == 1
        assert "dataset(s) not signed" in result.stdout
        
    finally:
        os.chdir(original_cwd)


def test_cli_verify_with_modified_file(temp_workspace):
    """Test dsq verify command after file modification."""
    runner = CliRunner()
    
    original_cwd = Path.cwd()
    try:
        import os
        os.chdir(temp_workspace)
        
        # Scan and sign
        runner.invoke(app, ["scan", "."])
        runner.invoke(app, ["sign"])
        
        # Modify the file
        with open("test.csv", "a") as f:
            f.write("4,David,40\n")
        
        # Verify should fail
        result = runner.invoke(app, ["verify"])
        assert result.exit_code == 1
        assert "Checksum mismatch" in result.stdout
        
    finally:
        os.chdir(original_cwd)


def test_cli_status_command(temp_workspace):
    """Test dsq status command."""
    runner = CliRunner()
    
    original_cwd = Path.cwd()
    try:
        import os
        os.chdir(temp_workspace)
        
        # Scan first
        runner.invoke(app, ["scan", "."])
        
        # Check status
        result = runner.invoke(app, ["status"])
        assert result.exit_code == 0
        assert "test.csv" in result.stdout
        assert "Unsigned" in result.stdout
        
        # Sign and check status again
        runner.invoke(app, ["sign"])
        result = runner.invoke(app, ["status"])
        assert result.exit_code == 0
        assert "Signed" in result.stdout
        
    finally:
        os.chdir(original_cwd)


def test_full_cli_workflow(temp_workspace):
    """Test complete CLI workflow as specified in requirements."""
    runner = CliRunner()
    
    original_cwd = Path.cwd()
    try:
        import os
        os.chdir(temp_workspace)
        
        # Step 1: Scan directory
        result = runner.invoke(app, ["scan", "."])
        assert result.exit_code == 0
        
        # Check schemas directory was created
        schemas_dir = temp_workspace / "schemas"
        assert schemas_dir.exists()
        
        # Step 2: Sign datasets
        result = runner.invoke(app, ["sign"])
        assert result.exit_code == 0
        
        # Step 3: Verify should pass
        result = runner.invoke(app, ["verify"])
        assert result.exit_code == 0
        
        # Step 4: Modify a file (simulate drift)
        with open("test.csv", "a") as f:
            f.write("999,Hacker,25\n")
        
        # Step 5: Verify should fail
        result = runner.invoke(app, ["verify"])
        assert result.exit_code == 1
        
        # Step 6: Re-scan should detect changes
        result = runner.invoke(app, ["scan", "."])
        assert result.exit_code == 0
        
        # Verify shows unsigned due to changes
        result = runner.invoke(app, ["verify"])
        assert result.exit_code == 1  # Should fail due to unsigned dataset
        
    finally:
        os.chdir(original_cwd)