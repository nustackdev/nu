# Overview

## Key Changes from Original

### Removed

- ✗ All validation logic (`validate_key`, `validate_key_component`, `validate_string_component`)
- ✗ String pattern validation (`VALID_STRING_PATTERN`)
- ✗ Complex constraint checking

### Kept (Critical Boundaries)

- ✓ Integer overflow/underflow checks (int64 range: -2^63 to 2^63-1)
- ✓ String length bounds (min: 1 byte, max: 10MB)
- ✓ Empty tuple rejection
- ✓ Type checking (only int and str allowed)
- ✓ UTF-8 decode error handling

### Performance Optimizations

1. **Pure C Hot Paths**
   - No Python object overhead in encode/decode loops
   - Direct memory operations via `memcpy`
   - Inline integer encoding (no function calls)

2. **Efficient Memory Strategy**
   - Two-pass encoding: calculate size → allocate once → fill
   - No intermediate buffers or reallocations
   - Direct byte buffer manipulation

3. **Compiler Optimizations**

   ```python
   boundscheck=False      # No array bounds checking
   wraparound=False       # No negative indexing
   cdivision=True         # C division semantics
   initializedcheck=False # No initialization checks
   nonecheck=False        # No None checks
   overflowcheck=False    # Manual overflow handling
   ```

4. **Integer Encoding**

   - Inline bias/offset encoding
   - Direct bit shifts for big-endian conversion
   - Uses `uint64_t` for efficient unsigned ops

5. **Build Flags**

   ```text
   -O3              # Maximum GCC optimization
   -march=native    # CPU-specific optimizations
   -ffast-math      # Fast math operations
   ```

## Technical Details

### Encoding Format (Unchanged)

```text
Integer: [0x01][8 bytes big-endian][0xFF]
String:  [0x02][UTF-8 bytes][0xFF]
```

### Type Ordering

- `0x01` (int) < `0x02` (str) ensures integers sort before strings
- Critical for maintaining lexicographic ordering

### Integer Encoding Algorithm

```cython
# Bias encoding: shift to unsigned range
biased_value = value + 2^63

# Manual big-endian conversion (8 bytes)
buffer[0] = (biased_value >> 56) & 0xFF
buffer[1] = (biased_value >> 48) & 0xFF
# ... etc
```

This preserves ordering:

- `-2^63` → `0x0000000000000000` (smallest)
- `0`     → `0x8000000000000000` (middle)
- `2^63-1` → `0xFFFFFFFFFFFFFFFF` (largest)

### Memory Allocation Strategy

### Encoding (Two-Pass)

```python
# Pass 1: Calculate exact size
for component in key:
    if int: size += 1 + 8 + 1
    if str: size += 1 + len(utf8_bytes) + 1

# Pass 2: Allocate and fill
buffer = allocate(size)
# ... fill buffer directly
```

### Decoding (Single-Pass)

```python
# Parse on-the-fly, accumulate results in list
while pos < len(data):
    type = data[pos]
    if type == INT: decode int
    if type == STR: decode str
```

## Performance Characteristics

[Inference] Expected performance (actual results depend on hardware):

### Throughput

- **Encoding**: ~100K-500K keys/second
- **Decoding**: ~100K-400K keys/second
- **Combined**: ~200K-450K operations/second

### Latency (per operation)

- **Encoding**: ~2-10 microseconds
- **Decoding**: ~2-12 microseconds

### Factors Affecting Performance

- Key complexity (number of components)
- String lengths (longer = slower)
- Integer vs string ratio
- CPU speed and architecture
- Cache effects
- System load

### Memory Usage

- **Encoding**: Single allocation sized exactly for output
- **Decoding**: List for components + string allocations
- **No intermediate allocations** in hot paths
- Typical encoded key: 50-200 bytes
