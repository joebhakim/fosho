# fosho - Data Validation for Half-Asleep Scientists

**F**ile-&-schema **O**ffline **S**igning & **H**ash **O**bservatory

Stop wondering if your downstream scripts are using the data you think they are. fosho gives you confidence that your data hasn't changed under your feet.

## Zombie-Proof Steps (Copy-Paste Ready)

**Scenario:** You have `downstream_script.py` that keeps breaking because your data changes. You want it to fail fast with clear errors instead of producing wrong results.

### Step 1: You already have data + a script that breaks
```bash
# Your current situation:
# - data/my_data.csv (keeps changing)  
# - downstream_script.py (breaks silently when data changes)
```

### Step 2: Generate schema and manifest (once)
```bash
# Scan your data directory - generates schemas automatically
uv run fosho scan data/

# This creates:
# - schemas/my_data_schema.py (auto-generated schema)
# - manifest.json (tracks file hashes and signing status)
```

### Step 3: Look at schema, edit if needed
```bash
cat schemas/my_data_schema.py
```
You'll see something like:
```python
schema = pa.DataFrameSchema({
    "id": pa.Column(int),
    "name": pa.Column(str),
    "score": pa.Column(float, nullable=True),
})
```
Edit this file if you want stricter validation (ranges, required values, etc.).

### Step 4: Sign your data (approve current state)
```bash
# Approve the current data state
uv run fosho sign

# Check status
uv run fosho status
```

### Step 5: Replace your pandas.read_csv() calls
**Before (dangerous):**
```python
import pandas as pd
df = pd.read_csv('data/my_data.csv')  # Silent failures
```

**After (safe):**
```python
import fosho

# Load with validation
df = fosho.read_csv(
    file='data/my_data.csv',
    schema='schemas/my_data_schema.py',
    manifest_path='manifest.json'
)

# Must validate before use - crashes if data changed since signing
validated_df = df.validate()  # 🚨 CRASHES if data changed
```

### Step 6: Run your script
- ✅ **If data matches schema:** Script runs normally
- 🚨 **If data changed:** Script crashes with clear error message
- 🎯 **No more silent failures:** You immediately know when data structure changes

## What This Solves

❌ **Before:** "Wait, did my preprocessing script change this CSV? Is my downstream analysis using old data?"

✅ **After:** Your script crashes with a clear error if the data changed. No more silent failures.

## The Magic

1. **File hashing** - Detects when CSVs change (even 1 byte)
2. **Schema validation** - Ensures data structure matches expectations  
3. **Signing workflow** - Explicit approval step prevents accidents
4. **Fail-fast** - Scripts error immediately if using stale/changed data

## Concrete Example

**Your messy situation:**
```bash
# You have this data that keeps changing
cat data/sales.csv
# id,product,revenue
# 1,widget,100.50
# 2,gadget,75.25

# And this script that breaks when data structure changes
cat analyze_sales.py
# import pandas as pd
# df = pd.read_csv('data/sales.csv')
# print(df['revenue'].mean())  # Breaks if 'revenue' column disappears
```

**The fosho solution:**
```bash
# 1. Scan and generate schema
uv run fosho scan data/

# 2. Check what it generated
cat schemas/sales_schema.py
# schema = pa.DataFrameSchema({
#     "id": pa.Column(int),
#     "product": pa.Column(str), 
#     "revenue": pa.Column(float),
# })

# 3. Sign the data state
uv run fosho sign

# 4. Update your script (safer approach)
cat analyze_sales_safe.py
# import fosho
# 
# df = fosho.read_csv(
#     file='data/sales.csv',
#     schema='schemas/sales_schema.py',
#     manifest_path='manifest.json'
# )
# validated_df = df.validate()  # <- This line protects you
# print(validated_df['revenue'].mean())  # Now safe!
```

**Result:** Your script now crashes immediately with a clear error if someone changes the data structure, instead of producing wrong results.

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