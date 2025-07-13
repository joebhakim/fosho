"""End-to-end test for the failure path workflow: downstream fails->scan->sign->downstream succeeds."""

import pytest
import subprocess
import tempfile
import shutil
import os
from pathlib import Path
import json
import fosho


def test_failure_path_workflow(tmp_path):
    """Test the failure path workflow where downstream fails first, then succeeds after signing."""
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
        # Step 1: Try downstream script WITHOUT scanning first - should fail
        # First create a dummy schema to test with (since we need something to reference)
        dummy_schema = test_schemas_dir / "test_data_schema.py"
        dummy_schema.write_text('''"""Dummy schema for testing."""
import pandera.pandas as pa

schema = pa.DataFrameSchema({
    "id": pa.Column(int),
    "name": pa.Column(str),
    "category": pa.Column(str),
    "value": pa.Column(int),
})

def validate_dataframe(df):
    """Validate DataFrame against schema."""
    return schema.validate(df)
''')
        
        # Try to use fosho.read_csv without manifest - should fail
        with pytest.raises(FileNotFoundError, match="manifest.json"):
            df = fosho.read_csv(
                file="data/test_data.csv",
                schema="schemas/test_data_schema.py",
                manifest_path="manifest.json"
            )
        
        # Step 2: Scan - should create proper schema and manifest
        result = subprocess.run(
            ["uv", "run", "fosho", "scan", "data"], 
            capture_output=True, text=True, cwd=str(tmp_path)
        )
        assert result.returncode == 0, f"Scan failed: {result.stderr}"
        assert "Found 1 dataset(s)" in result.stdout
        assert "Added (unsigned)" in result.stdout
        
        # Verify manifest was created
        manifest_file = Path("manifest.json")
        assert manifest_file.exists(), "Manifest file was not created"
        
        # Step 3: Try downstream script with unsigned dataset - should fail validation
        df = fosho.read_csv(
            file="data/test_data.csv",
            schema="schemas/test_data_schema.py",
            manifest_path="manifest.json"
        )
        
        # Should fail because dataset is not signed
        with pytest.raises(ValueError, match="is not signed"):
            df.validate()
        
        # Step 4: Sign the dataset
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
        
        # Step 5: Verify - should pass verification
        result = subprocess.run(
            ["uv", "run", "fosho", "verify"], 
            capture_output=True, text=True, cwd=str(tmp_path)
        )
        assert result.returncode == 0, f"Verify failed: {result.stderr}"
        assert "All datasets verified successfully" in result.stdout
        
        # Step 6: Status - should show signed status
        result = subprocess.run(
            ["uv", "run", "fosho", "status"], 
            capture_output=True, text=True, cwd=str(tmp_path)
        )
        assert result.returncode == 0, f"Status failed: {result.stderr}"
        assert "✓ Signed" in result.stdout
        
        # Step 7: Downstream script - should now work successfully
        df = fosho.read_csv(
            file="data/test_data.csv",
            schema="schemas/test_data_schema.py",
            manifest_path="manifest.json"
        )
        
        # Should not be validated yet
        assert "unvalidated" in repr(df)
        
        # Validate should work now
        validated_df = df.validate()
        assert validated_df.shape == (4, 4)  # 4 rows, 4 columns
        assert list(validated_df.columns) == ["id", "name", "category", "value"]
        
        # Should be able to use DataFrame methods after validation
        assert df.shape == (4, 4)
        assert df["value"].sum() == 750  # 100+200+150+300
        
    finally:
        os.chdir(original_cwd)


def test_data_modification_detection(tmp_path):
    """Test that data modifications are detected and prevent validation."""
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
        # Scan and sign
        subprocess.run(
            ["uv", "run", "fosho", "scan", "data"], 
            capture_output=True, text=True, cwd=str(tmp_path)
        )
        subprocess.run(
            ["uv", "run", "fosho", "sign"], 
            capture_output=True, text=True, cwd=str(tmp_path)
        )
        
        # Verify it works initially
        df = fosho.read_csv(
            file="data/test_data.csv",
            schema="schemas/test_data_schema.py",
            manifest_path="manifest.json"
        )
        validated_df = df.validate()  # Should work
        
        # Modify the data file
        test_csv.write_text("id,name,category,value\n1,Modified,TypeX,999\n")
        
        # Try to validate again - should fail due to CRC32 mismatch
        df = fosho.read_csv(
            file="data/test_data.csv",
            schema="schemas/test_data_schema.py",
            manifest_path="manifest.json"
        )
        
        with pytest.raises(ValueError, match="CRC32 mismatch"):
            df.validate()
        
    finally:
        os.chdir(original_cwd)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])