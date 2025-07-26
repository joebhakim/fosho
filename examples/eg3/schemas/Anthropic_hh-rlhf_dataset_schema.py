"""Auto-generated dataset schema for Anthropic_hh-rlhf."""

from fosho.dataset_schema import DatasetStructureSchema, DatasetRecordSchema, DatasetSchema

# Structure schema - defines expected splits
structure_schema = DatasetStructureSchema(
    expected_splits=['train', 'test'],
    min_records_per_split=1
)

# Record schema - defines expected features in each record
record_schema = DatasetRecordSchema(
    required_features={'chosen': "Value('string')", 'rejected': "Value('string')"}
)

# Combined schema
schema = DatasetSchema(structure_schema, record_schema, name='Anthropic_hh-rlhf')

def validate_dataset(dataset):
    """Validate dataset against schema."""
    return schema.validate(dataset)