"""End-to-end test for the happy path workflow: scan->sign->verify->status->downstream."""

import pytest
import subprocess
import tempfile
import shutil
import os
from pathlib import Path
import json
import fosho


def test_happy_path_workflow(tmp_path):
    """Test the complete happy path workflow."""
    # Setup test environment
    test_data_dir = tmp_path / "data"
    test_schemas_dir = tmp_path / "schemas"
    test_data_dir.mkdir()
    test_schemas_dir.mkdir()
    
    # Copy test data
    test_csv = test_data_dir / "test_data.csv"
    fixtures_dir = Path(__file__).parent / "fixtures"
    shutil.copy(fixtures_dir / "test_data.csv", test_csv)
    
    # Change to test directory
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        # Step 1: Scan - should create schema and manifest
        result = subprocess.run(
            ["uv", "run", "fosho", "scan", "data"], 
            capture_output=True, text=True, cwd=str(tmp_path)
        )
        assert result.returncode == 0, f"Scan failed: {result.stderr}"
        assert "Found 1 dataset(s)" in result.stdout
        assert "Added (unsigned)" in result.stdout
        
        # Verify schema file was created
        schema_file = test_schemas_dir / "test_data_schema.py"
        assert schema_file.exists(), "Schema file was not created"
        
        # Verify manifest was created
        manifest_file = Path("manifest.json")
        assert manifest_file.exists(), "Manifest file was not created"
        
        # Step 2: Sign - should sign the dataset
        result = subprocess.run(
            ["uv", "run", "fosho", "sign"], 
            capture_output=True, text=True, cwd=str(tmp_path)
        )
        assert result.returncode == 0, f"Sign failed: {result.stderr}"
        assert "Successfully signed 1 dataset(s)" in result.stdout
        
        # Verify dataset is signed in manifest
        with open(manifest_file) as f:
            manifest_data = json.load(f)
        dataset_key = "data/test_data.csv"
        assert dataset_key in manifest_data["datasets"]
        assert manifest_data["datasets"][dataset_key]["signed"] is True
        
        # Step 3: Status - should show comprehensive verification
        result = subprocess.run(
            ["uv", "run", "fosho", "status"], 
            capture_output=True, text=True, cwd=str(tmp_path)
        )
        assert result.returncode == 0, f"Status failed: {result.stderr}"
        assert "Signed" in result.stdout
        assert "Exists" in result.stdout
        assert "Valid" in result.stdout  # Both data and schema should be valid
        
        # Step 4: Downstream script - should work successfully
        df = fosho.read_csv(
            file="data/test_data.csv",
            schema="schemas/test_data_schema.py",
            manifest_path="manifest.json"
        )
        
        # Should not be validated yet
        assert "unvalidated" in repr(df)
        
        # Validate should work
        validated_df = df.validate()
        assert validated_df.shape == (4, 4)  # 4 rows, 4 columns
        assert list(validated_df.columns) == ["id", "name", "category", "value"]
        
        # Should be able to use DataFrame methods after validation
        assert df.shape == (4, 4)
        assert df["value"].sum() == 750  # 100+200+150+300
        
    finally:
        os.chdir(original_cwd)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])