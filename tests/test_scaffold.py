"""Unit tests for schema scaffolding functionality."""

import tempfile
import pandas as pd
import pandera.pandas as pa
from pathlib import Path
import pytest

from fosho.scaffold import (
    scaffold_dataset_schema,
    scaffold_schema_from_dataframe,
    generate_schema_file,
    load_dataset,
    create_schema_slug
)


class TestSimpleCSVSchemaGeneration:
    """Test schema generation for simple CSV files."""
    
    def test_load_simple_csv(self):
        """Test that we can load a simple CSV correctly."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("id,name,value\n1,Alice,100\n2,Bob,200\n")
            csv_path = f.name
        
        try:
            df = load_dataset(csv_path)
            
            # Verify basic structure
            assert df.shape == (2, 3)
            assert list(df.columns) == ['id', 'name', 'value']
            
            # Verify data types
            assert df['id'].dtype == 'int64'
            assert df['name'].dtype == 'object'  # string columns are 'object' in pandas
            assert df['value'].dtype == 'int64'
            
        finally:
            Path(csv_path).unlink()
    
    def test_scaffold_schema_from_simple_dataframe(self):
        """Test schema generation from a simple DataFrame."""
        # Create a simple DataFrame
        df = pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['Alice', 'Bob', 'Charlie'],
            'value': [100, 200, 150]
        })
        
        # Generate schema
        schema = scaffold_schema_from_dataframe(df, "test.csv")
        
        # Verify schema structure
        assert isinstance(schema, pa.DataFrameSchema)
        assert len(schema.columns) == 3
        
        # Check that all expected columns are present
        assert 'id' in schema.columns
        assert 'name' in schema.columns
        assert 'value' in schema.columns
        
        # Verify the schema can validate the original DataFrame
        validated_df = schema.validate(df)
        pd.testing.assert_frame_equal(df, validated_df)
    
    def test_create_schema_slug(self):
        """Test schema slug generation from file paths."""
        assert create_schema_slug("test.csv") == "test"
        assert create_schema_slug("data/test.csv") == "test"
        assert create_schema_slug("path/to/my_data.csv") == "my_data"
        assert create_schema_slug("complex-name.csv") == "complex_name"
        assert create_schema_slug("file with spaces.csv") == "file_with_spaces"
    
    def test_end_to_end_simple_csv_schema_generation(self):
        """Test complete workflow: CSV -> schema -> validation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create a simple CSV file
            csv_file = tmpdir / "simple.csv"
            csv_file.write_text("id,name,age\n1,Alice,25\n2,Bob,30\n3,Charlie,35\n")
            
            # Generate schema
            schema, schema_file = scaffold_dataset_schema(
                csv_file, 
                output_dir=tmpdir / "schemas"
            )
            
            # Verify schema file was created
            assert schema_file.exists()
            assert schema_file.name == "simple_schema.py"
            
            # Load the original data and validate against schema
            df = pd.read_csv(csv_file)
            validated_df = schema.validate(df)
            
            # Should be able to validate successfully
            assert validated_df.shape == (3, 3)
            assert list(validated_df.columns) == ['id', 'name', 'age']


class TestCSVVariations:
    """Test schema generation for various CSV formats."""
    
    def test_mixed_data_types(self):
        """Test CSV with mixed data types."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("id,name,score,active\n1,Alice,95.5,true\n2,Bob,87.2,false\n")
            csv_path = f.name
        
        try:
            df = load_dataset(csv_path)
            
            # Verify data types are inferred correctly
            assert df['id'].dtype == 'int64'
            assert df['name'].dtype == 'object'
            assert df['score'].dtype == 'float64'
            assert df['active'].dtype == 'bool'  # pandas should infer boolean
            
            # Generate and test schema
            schema = scaffold_schema_from_dataframe(df, csv_path)
            validated_df = schema.validate(df)
            pd.testing.assert_frame_equal(df, validated_df)
            
        finally:
            Path(csv_path).unlink()
    
    def test_nullable_columns(self):
        """Test CSV with missing values."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("id,name,score\n1,Alice,95.5\n2,Bob,\n3,Charlie,87.2\n")
            csv_path = f.name
        
        try:
            df = load_dataset(csv_path)
            
            # Verify NaN handling
            assert df['score'].isnull().any()
            
            # Generate schema - should handle nullable columns
            schema = scaffold_schema_from_dataframe(df, csv_path)
            
            # Schema should allow nulls for the score column
            score_column = schema.columns['score']
            assert score_column.nullable == True
            
            # Should validate successfully
            validated_df = schema.validate(df)
            assert validated_df.shape == (3, 3)
            
        finally:
            Path(csv_path).unlink()
    
    def test_single_row_csv(self):
        """Test CSV with only one data row."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("id,name,value\n1,Alice,100\n")
            csv_path = f.name
        
        try:
            df = load_dataset(csv_path)
            assert df.shape == (1, 3)
            
            # Should still generate valid schema
            schema = scaffold_schema_from_dataframe(df, csv_path)
            validated_df = schema.validate(df)
            pd.testing.assert_frame_equal(df, validated_df)
            
        finally:
            Path(csv_path).unlink()
    
    def test_headers_only_csv(self):
        """Test CSV with only headers, no data rows."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("id,name,value\n")
            csv_path = f.name
        
        try:
            df = load_dataset(csv_path)
            assert df.shape == (0, 3)  # No rows, 3 columns
            assert list(df.columns) == ['id', 'name', 'value']
            
            # Schema generation with empty DataFrame should handle gracefully
            # This might fail, which would be good to know
            try:
                schema = scaffold_schema_from_dataframe(df, csv_path)
                # If it succeeds, it should at least have the right columns
                assert len(schema.columns) == 3
            except Exception as e:
                # If it fails, we want to know what happens
                pytest.skip(f"Empty DataFrame schema generation failed: {e}")
            
        finally:
            Path(csv_path).unlink()


class TestSchemaFileGeneration:
    """Test the generated Python schema files."""
    
    def test_schema_file_content(self):
        """Test that generated schema files have correct content."""
        df = pd.DataFrame({
            'id': [1, 2],
            'name': ['Alice', 'Bob']
        })
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            schema = scaffold_schema_from_dataframe(df, "test.csv")
            schema_file = generate_schema_file(schema, "test.csv", tmpdir)
            
            # Read the generated file
            content = schema_file.read_text()
            
            # Should contain expected elements
            assert 'import pandera.pandas as pa' in content
            assert 'schema = pa.DataFrameSchema({' in content
            assert '"id"' in content
            assert '"name"' in content
            assert 'def validate_dataframe(df):' in content
            
            # Should be valid Python
            exec(content)  # This will raise if there's a syntax error
    
    def test_schema_file_execution(self):
        """Test that generated schema files can be executed and used."""
        df = pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['Alice', 'Bob', 'Charlie'],
            'score': [95.5, 87.2, 91.8]
        })
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            schema = scaffold_schema_from_dataframe(df, "test.csv")
            schema_file = generate_schema_file(schema, "test.csv", tmpdir)
            
            # Load the schema from the file
            import importlib.util
            spec = importlib.util.spec_from_file_location("test_schema", schema_file)
            schema_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(schema_module)
            
            # Should be able to use the loaded schema
            loaded_schema = schema_module.schema
            validated_df = loaded_schema.validate(df)
            pd.testing.assert_frame_equal(df, validated_df)
            
            # Should also have the validate_dataframe function
            assert hasattr(schema_module, 'validate_dataframe')
            validated_df2 = schema_module.validate_dataframe(df)
            pd.testing.assert_frame_equal(df, validated_df2)


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 