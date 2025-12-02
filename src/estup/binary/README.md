# Cython BinaryKeyCodec - High-Performance Implementation

Optimized Cython implementation of binary key codec for lexicographic ordering preservation in KV storage systems.

## Performance Optimizations

### Core Optimizations

1. **Zero Python Overhead**
   - All hot paths execute in pure C
   - Direct memory operations via `libc.string.memcpy`
   - Inline integer encoding/decoding (no function call overhead)

2. **Efficient Memory Management**
   - Two-pass encoding: calculate exact size, then allocate once
   - No intermediate allocations or buffer resizing
   - Direct byte buffer manipulation

3. **Compiler Directives**
   - `boundscheck=False`: Disable array bounds checking
   - `wraparound=False`: Disable negative indexing
   - `cdivision=True`: Use C division semantics
   - `initializedcheck=False`: Skip initialization checks
   - `nonecheck=False`: Skip None checks in hot paths
   - `overflowcheck=False`: No overflow checks (we handle manually)

4. **Integer Encoding**
   - Inline bias/offset encoding (no function calls)
   - Direct bit manipulation for big-endian conversion
   - Uses uint64_t for efficient unsigned operations

5. **String Handling**
   - Direct UTF-8 byte operations
   - No escaping needed (0xFF separator is invalid UTF-8)
   - Efficient memcpy for string data

## Performance Characteristics

Expected performance ([Inference] - actual performance depends on hardware and data):

- **Encoding**: ~2M-2.5M keys/sec for typical mixed int/string keys
- **Decoding**: ~2M-2.5M keys/sec
- **Memory**: Single allocation per encode/decode operation
- **Overhead**: Minimal Python overhead (mainly tuple creation in decode)

## Encoding Format

Same as original implementation:

```text
[TYPE_INT (0x01)][8 bytes big-endian][SEP (0xFF)] for integers
[TYPE_STR (0x02)][UTF-8 bytes][SEP (0xFF)] for strings
```

### Type Ordering

- `TYPE_INT (0x01) < TYPE_STR (0x02)` ensures integers sort before strings

### Integer Encoding

- Bias/offset encoding: `biased_value = value + 2^63`
- Maps signed int64 to unsigned for natural byte ordering
- Range: `-2^63` to `2^63-1`

### String Encoding

- Direct UTF-8 bytes
- No escaping needed (separator 0xFF is invalid UTF-8)
- Length limits: 1 byte to 10MB

## Exception Handling

- `IntegerOverflowError`: Integer outside int64 range
- `EncodeError`: Invalid key structure or string constraints
- `DecodeError`: Corrupted or invalid encoded data

## API

- `BinaryKeyCodec.encode(key: tuple) -> bytes`
- `BinaryKeyCodec.decode(encoded: bytes) -> tuple`
