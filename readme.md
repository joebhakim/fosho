# fosho - Data Validation for Half-Asleep Scientists

**F**ile-&-schema **O**ffline **S**igning & **H**ash **O**bservatory

Stop wondering if your downstream scripts are using the data you think they are. fosho gives you confidence that your data hasn't changed under your feet.

## Quick Start (Copy-Paste Ready)

### Step 1: Put your messy CSV somewhere
```bash
# You already have data somewhere, like data/my_messy_data.csv
```

### Step 2: Generate a simple schema
```bash
uv run python -c "
from src.fosho.scaffold import scaffold_dataset_schema
schema, schema_file = scaffold_dataset_schema('data/my_messy_data.csv')
print(f'✅ Generated: {schema_file}')
"
```
This creates `schemas/my_messy_data_schema.py` with basic validation:
```python
schema = pa.DataFrameSchema({
    "id": pa.Column(int),
    "name": pa.Column(str),
    "score": pa.Column(float, nullable=True),
})
```

### Step 3: Look at the schema (always do this!)
```bash
cat schemas/my_messy_data_schema.py
```
The schema is minimal - just column names and types. Edit it if you want more validation rules.

### Step 4: Use validated data in your scripts
```python
import pandas as pd
import sys
sys.path.append('schemas')
from my_messy_data_schema import validate_dataframe

# Load and validate your data
df = pd.read_csv('data/my_messy_data.csv')
validated_df = validate_dataframe(df)  # 🚨 Fails if schema doesn't match

# Now you can trust this data structure
print(validated_df['column_name'])
```

## What This Solves

❌ **Before:** "Wait, did my preprocessing script change this CSV? Is my downstream analysis using old data?"

✅ **After:** Your script crashes with a clear error if the data changed. No more silent failures.

## The Magic

1. **File hashing** - Detects when CSVs change (even 1 byte)
2. **Schema validation** - Ensures data structure matches expectations  
3. **Signing workflow** - Explicit approval step prevents accidents
4. **Fail-fast** - Scripts error immediately if using stale/changed data

## Example Workflow

```bash
# Initial setup
mkdir data
echo "id,name
1,alice
2,bob" > data/example.csv

# Generate schema
uv run python -c "
from src.fosho.scaffold import scaffold_dataset_schema
schema, schema_file = scaffold_dataset_schema('data/example.csv')
print(f'Generated: {schema_file}')
"

# Use in Python
python -c "
import pandas as pd
import sys; sys.path.append('schemas')
from example_schema import validate_dataframe

df = pd.read_csv('data/example.csv')
validated_df = validate_dataframe(df)
print('✅ Data is valid!')
print(validated_df)
"
```

## When Things Change

If your data changes:
```bash
# Re-scan to update checksums
uv run fosho scan data/

# Review what changed
uv run fosho status

# Re-approve if changes are intentional
uv run fosho sign
```

Your Python scripts will refuse to run until you explicitly re-approve the changes.

## Commands

- `fosho scan data/` - Find CSVs, generate schemas, update manifest
- `fosho sign` - Approve all current data/schemas  
- `fosho status` - Show what's signed vs unsigned
- `fosho verify` - Check if everything still matches

## Installation

```bash
cd your-project
uv add fosho  # or pip install fosho
```

## Philosophy

Data scientists need **simple validation first**, not complex rules. fosho generates minimal schemas (just column types + nullability) so you can:

1. Get protection immediately
2. Add more validation rules later as you learn about your data
3. Never wonder "is my script using the right data?"

Perfect for preprocessing pipelines that keep changing and downstream analyses that need to stay in sync.