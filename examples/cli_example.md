# CLI Example: Half-Asleep Data Scientist Workflow

## The Problem
You have `downstream_script.py` that works today but breaks tomorrow when your data changes. You want it to fail loudly instead of producing wrong results.

## Current (Broken) Workflow

```python
# downstream_script.py - DANGEROUS VERSION
import pandas as pd

# This silently breaks when CSV structure changes
df = pd.read_csv("data/experiment_results.csv")
print(f"Average score: {df['score'].mean()}")  # KeyError if 'score' column disappears
```

## Fixed Workflow with fosho

### Step 1: Generate schema (once, when half-asleep)
```bash
# Generate basic schema from your current data
uv run python -c "
from src.fosho.scaffold import scaffold_dataset_schema
schema, schema_file = scaffold_dataset_schema('data/experiment_results.csv')
print(f'✅ Generated: {schema_file}')
"
```

### Step 2: Human-check the schema (always do this!)
```bash
cat schemas/experiment_results_schema.py
```
You'll see something minimal like:
```python
"""Auto-generated schema for experiment_results.csv."""

import pandera.pandas as pa

schema = pa.DataFrameSchema({
    "experiment_id": pa.Column(int),
    "condition": pa.Column(str),
    "score": pa.Column(float),
    "participant": pa.Column(str, nullable=True),
})
```

**Edit this file** if you want more validation (e.g., score must be between 0-100, conditions must be specific values, etc.).

### Step 3: Update your downstream script (2-line change)
```python
# downstream_script.py - SAFE VERSION  
import pandas as pd
import sys; sys.path.append('schemas')
from experiment_results_schema import validate_dataframe

df = pd.read_csv("data/experiment_results.csv")
validated_df = validate_dataframe(df)  # 🚨 CRASHES if structure changed
print(f"Average score: {validated_df['score'].mean()}")  # Now safe!
```

### Step 4: Run your script
- ✅ **Data unchanged:** Script runs normally
- 🚨 **Data structure changed:** Script crashes with clear error:
  ```
  SchemaError: column 'score' not in dataframe. 
  Columns in dataframe: ['experiment_id', 'condition', 'rating']
  ```
- 🎯 **No silent failures:** You immediately know when someone changed your data

## When Data Changes (Intentionally)

1. **Regenerate schema:**
   ```bash
   uv run python -c "
   from src.fosho.scaffold import scaffold_dataset_schema
   schema, schema_file = scaffold_dataset_schema('data/experiment_results.csv', overwrite=True)
   print(f'Updated: {schema_file}')
   "
   ```

2. **Review changes:** Check what changed in the schema file

3. **Test your script:** Make sure it still works with new data structure

## Result
Your downstream scripts now fail fast with clear errors instead of producing wrong results when data changes. Perfect for preprocessing pipelines that keep evolving.

