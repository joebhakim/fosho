"""Auto-generated dataset schema for squad."""

from fosho.dataset_schema import DatasetStructureSchema, DatasetRecordSchema, DatasetSchema

# Structure schema - defines expected splits
structure_schema = DatasetStructureSchema(
    expected_splits=['train', 'validation'],
    min_records_per_split=1
)

# Record schema - defines expected features in each record
record_schema = DatasetRecordSchema(
    required_features={'id': "Value('string')", 'title': "Value('string')", 'context': "Value('string')", 'question': "Value('string')", 'answers': "{'text': List(Value('string')), 'answer_start': List(Value('int32'))}"}
)

# Combined schema
schema = DatasetSchema(structure_schema, record_schema, name='squad')

def validate_dataset(dataset):
    """Validate dataset against schema."""
    return schema.validate(dataset)