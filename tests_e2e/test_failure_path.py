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
        
        # Try to use fosho.read_csv without manifest - should load but fail validation
        df = fosho.read_csv(
            file="data/test_data.csv",
            schema="schemas/test_data_schema.py",
            manifest_path="manifest.json"
        )
        # Should fail because dataset is not in manifest
        with pytest.raises(ValueError, match="not found in manifest"):
            df.validate()
        
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
        
        # Step 5: Status - should show comprehensive verification
        result = subprocess.run(
            ["uv", "run", "fosho", "status"], 
            capture_output=True, text=True, cwd=str(tmp_path)
        )
        assert result.returncode == 0, f"Status failed: {result.stderr}"
        assert "Signed" in result.stdout
        assert "Exists" in result.stdout
        assert "Valid" in result.stdout  # Both data and schema should be valid
        
        # Step 6: Downstream script - should now work successfully
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


def test_auto_unsealing_on_data_changes(tmp_path):
    """Test that status command automatically unseals datasets when data changes."""
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
        
        # Verify signed status
        result = subprocess.run(
            ["uv", "run", "fosho", "status"], 
            capture_output=True, text=True, cwd=str(tmp_path)
        )
        assert "Signed" in result.stdout
        
        # Modify the data file
        test_csv.write_text("id,name,category,value\n1,Modified,TypeX,999\n")
        
        # Check status - should auto-unseal and show data changed
        result = subprocess.run(
            ["uv", "run", "fosho", "status"], 
            capture_output=True, text=True, cwd=str(tmp_path)
        )
        assert result.returncode == 0
        assert "Unsigned" in result.stdout
        assert "Changed" in result.stdout  # Data status
        assert "automatically unsigned due to data changes" in result.stdout
        
        # Verify manifest was updated
        with open("manifest.json") as f:
            manifest_data = json.load(f)
        assert manifest_data["datasets"]["data/test_data.csv"]["signed"] is False
        
    finally:
        os.chdir(original_cwd)


def test_schema_change_detection(tmp_path):
    """Test that schema modifications are detected by status command."""
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
        
        # Verify initially all valid
        result = subprocess.run(
            ["uv", "run", "fosho", "status"], 
            capture_output=True, text=True, cwd=str(tmp_path)
        )
        assert "Signed" in result.stdout
        assert "Valid" in result.stdout
        
        # Modify the schema file - add a validation constraint
        schema_file = test_schemas_dir / "test_data_schema.py"
        schema_content = schema_file.read_text()
        modified_schema = schema_content.replace(
            '"value": pa.Column(int),',
            '"value": pa.Column(int, pa.Check.ge(0)),'
        )
        schema_file.write_text(modified_schema)
        
        # Check status - should detect schema change
        result = subprocess.run(
            ["uv", "run", "fosho", "status"], 
            capture_output=True, text=True, cwd=str(tmp_path)
        )
        assert result.returncode == 0
        assert "Signed" in result.stdout  # Still signed (only data changes auto-unseal)
        assert "Valid" in result.stdout   # Data still valid
        assert "Changed" in result.stdout  # Schema changed
        
    finally:
        os.chdir(original_cwd)


def test_schema_validation_failure_during_signing(tmp_path):
    """Test that signing fails when schema doesn't validate against data."""
    # Setup test environment
    test_data_dir = tmp_path / "data"
    test_schemas_dir = tmp_path / "schemas"
    test_data_dir.mkdir()
    test_schemas_dir.mkdir()
    
    # Create data with problematic values
    test_csv = test_data_dir / "test_data.csv"
    test_csv.write_text("id,name,category,value\n1,Test,A,-999\n2,Test2,B,100\n")
    
    # Change to test directory
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        # Scan to create initial schema
        subprocess.run(
            ["uv", "run", "fosho", "scan", "data"], 
            capture_output=True, text=True, cwd=str(tmp_path)
        )
        
        # Manually modify schema to add constraint that will fail
        schema_file = test_schemas_dir / "test_data_schema.py"
        schema_content = schema_file.read_text()
        modified_schema = schema_content.replace(
            '"value": pa.Column(int),',
            '"value": pa.Column(int, pa.Check.ge(0)),'  # Require non-negative values
        )
        schema_file.write_text(modified_schema)
        
        # Rescan to update schema hash
        subprocess.run(
            ["uv", "run", "fosho", "scan", "data"], 
            capture_output=True, text=True, cwd=str(tmp_path)
        )
        
        # Try to sign - should fail because data has negative value
        result = subprocess.run(
            ["uv", "run", "fosho", "sign"], 
            capture_output=True, text=True, cwd=str(tmp_path)
        )
        assert result.returncode != 0
        assert "Schema validation failed" in result.stdout
        assert "fix the schema or data before signing" in result.stdout
        
        # Verify dataset remains unsigned
        with open("manifest.json") as f:
            manifest_data = json.load(f)
        assert manifest_data["datasets"]["data/test_data.csv"]["signed"] is False
        
    finally:
        os.chdir(original_cwd)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])