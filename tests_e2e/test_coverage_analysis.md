# E2E Test Coverage Analysis

## Current Test Status
- **3 tests total**: All failing due to schema generation issues
- **Root cause**: Schema scaffolding bug treating CSV files incorrectly
- **Impact**: Core validation workflow broken

## Current Test Coverage

### ✅ Tests That Should Work (After Schema Fix)
1. **Happy Path Workflow**
   - Scan → Sign → Verify → Status → Read → Validate
   - Basic DataFrame operations after validation
   - Proper manifest tracking

2. **Data Modification Detection**
   - CRC32 change detection
   - Validation prevention after file changes

### ❌ Current Issues
1. **Schema Generation Bug**: CSVs parsed as single-row, many-column files
2. **Missing Error Handling**: FileNotFoundError not raised properly
3. **MD5 Mismatch**: Schema generation inconsistency

## Missing Test Cases (High Priority)

### 1. **Complex Schema Types**
- Multi-index columns (already has scaffolding support)
- Mixed data types (int, float, str, nullable)
- Special characters in column names
- Large files (>100MB) for performance testing

### 2. **Pernicious Data Changes** (Hard to Detect)
- **Column reordering**: Same data, different order
- **Precision loss**: 1.0 → 1, 100.0 → 100
- **Encoding changes**: UTF-8 → Latin-1
- **Whitespace changes**: Trailing spaces, different line endings
- **Type coercion**: "1" → 1, "true" → True

### 3. **Edge Cases**
- Empty CSV files
- Single-row files
- Files with only headers
- Unicode in data and column names
- Very long column names
- Duplicate column names

### 4. **Concurrency & Performance**
- Multiple processes accessing same manifest
- Large file scanning performance
- Memory usage with large datasets

### 5. **Error Recovery**
- Corrupted manifest.json
- Missing schema files
- Partial scan failures
- Network interruptions (for future remote features)

### 6. **Schema Evolution**
- Adding new columns to existing data
- Changing column types
- Removing columns
- Schema backwards compatibility

## Recommended Test Additions

### Phase 1: Fix Current Tests
1. Fix schema generation bug
2. Add proper error handling tests
3. Ensure existing 3 tests pass

### Phase 2: Add Critical Edge Cases
```python
def test_column_reordering_detection():
    # Same data, different column order should be detected
    
def test_precision_loss_detection():
    # 1.0 → 1 should be detected as change
    
def test_encoding_change_detection():
    # UTF-8 → Latin-1 should be detected
    
def test_empty_file_handling():
    # Empty CSV should not crash
    
def test_unicode_support():
    # Unicode in data and columns should work
```

### Phase 3: Performance & Concurrency
```python
def test_large_file_performance():
    # 100MB+ file should scan in reasonable time
    
def test_concurrent_access():
    # Multiple processes should handle manifest correctly
```

## Test Data Fixtures Needed

### Basic Test Data
- ✅ `test_data.csv` (4 columns, 4 rows) - **Fixed**
- ❌ `complex_types.csv` (int, float, str, nullable columns)
- ❌ `unicode_data.csv` (Unicode characters in data and columns)
- ❌ `large_data.csv` (10,000+ rows for performance testing)

### Edge Case Data
- ❌ `empty.csv` (empty file)
- ❌ `headers_only.csv` (only headers, no data)
- ❌ `single_row.csv` (one data row)
- ❌ `special_chars.csv` (special characters in column names)

### Corruption Test Data
- ❌ `reordered_columns.csv` (same data, different column order)
- ❌ `precision_loss.csv` (1.0 vs 1, 100.0 vs 100)
- ❌ `encoding_variants.csv` (same data, different encodings)

## Implementation Priority

1. **CRITICAL**: Fix schema generation bug
2. **HIGH**: Add missing error handling tests
3. **MEDIUM**: Add pernicious change detection tests
4. **LOW**: Add performance and concurrency tests 