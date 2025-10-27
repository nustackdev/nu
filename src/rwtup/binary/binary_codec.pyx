# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True
# cython: initializedcheck=False
# cython: nonecheck=False
# cython: overflowcheck=False
"""Optimized Cython implementation of binary key codec."""

from libc.stdint cimport int64_t, uint64_t, INT64_MIN, INT64_MAX
from libc.string cimport memcpy
from cpython.bytes cimport PyBytes_FromStringAndSize, PyBytes_AS_STRING, PyBytes_GET_SIZE
from cpython.unicode cimport PyUnicode_AsUTF8String, PyUnicode_DecodeUTF8

# Type markers for lexicographic ordering (int < str)
cdef unsigned char TYPE_INT = 0x01
cdef unsigned char TYPE_STR = 0x02
cdef unsigned char SEPARATOR = 0xFF

# Integer range constants
cdef int64_t INT64_MIN_VAL = INT64_MIN
cdef int64_t INT64_MAX_VAL = INT64_MAX
cdef uint64_t INT64_BIAS = 0x8000000000000000ULL  # 2^63

# String constraints
cdef size_t MAX_STRING_LENGTH = 10 * 1024 * 1024  # 10MB


cdef class IntegerOverflowError(Exception):
    """Raised when integer is outside int64 range."""
    pass


cdef class EncodeError(Exception):
    """Raised when encoding fails."""
    pass


cdef class DecodeError(Exception):
    """Raised when decoding fails."""
    pass


cdef inline void encode_integer_inline(int64_t value, unsigned char* buffer) noexcept nogil:
    """Encode integer using bias/offset encoding directly into buffer.
    
    Args:
        value: Integer to encode (must be in int64 range)
        buffer: Output buffer (must have at least 8 bytes available)
    """
    cdef uint64_t biased_value = <uint64_t>(value + <int64_t>INT64_BIAS)
    
    # Write as big-endian (most significant byte first)
    buffer[0] = <unsigned char>((biased_value >> 56) & 0xFF)
    buffer[1] = <unsigned char>((biased_value >> 48) & 0xFF)
    buffer[2] = <unsigned char>((biased_value >> 40) & 0xFF)
    buffer[3] = <unsigned char>((biased_value >> 32) & 0xFF)
    buffer[4] = <unsigned char>((biased_value >> 24) & 0xFF)
    buffer[5] = <unsigned char>((biased_value >> 16) & 0xFF)
    buffer[6] = <unsigned char>((biased_value >> 8) & 0xFF)
    buffer[7] = <unsigned char>(biased_value & 0xFF)


cdef inline int64_t decode_integer_inline(const unsigned char* buffer) noexcept nogil:
    """Decode integer from buffer using bias/offset encoding.
    
    Args:
        buffer: Input buffer (must have at least 8 bytes)
        
    Returns:
        Decoded integer value
    """
    cdef uint64_t biased_value = (
        (<uint64_t>buffer[0] << 56) |
        (<uint64_t>buffer[1] << 48) |
        (<uint64_t>buffer[2] << 40) |
        (<uint64_t>buffer[3] << 32) |
        (<uint64_t>buffer[4] << 24) |
        (<uint64_t>buffer[5] << 16) |
        (<uint64_t>buffer[6] << 8) |
        <uint64_t>buffer[7]
    )
    
    # Remove bias to get original signed value
    return <int64_t>(biased_value - INT64_BIAS)


cdef class BinaryKeyCodec:
    """Optimized binary key codec that preserves lexicographic ordering.
    
    This Cython implementation provides maximum performance for encoding and
    decoding tuple keys into binary format while maintaining sort order.
    
    Features:
    - Zero Python overhead in hot paths
    - Direct memory operations
    - Inline integer encoding/decoding
    - Efficient buffer management
    - Preserves lexicographic ordering
    
    Encoding format:
    - Each component: TYPE_MARKER + ENCODED_VALUE + SEPARATOR
    - Integers: TYPE_INT (0x01) + 8_BYTES + SEPARATOR (0xFF)
    - Strings: TYPE_STR (0x02) + UTF8_BYTES + SEPARATOR (0xFF)
    """
    
    def encode(self, tuple key):
        """Encode tuple key into binary format preserving lexicographic order.
        
        Args:
            key: Tuple containing strings and/or integers
            
        Returns:
            Binary encoded key (bytes)
            
        Raises:
            IntegerOverflowError: If integer is outside int64 range
            EncodeError: If encoding fails
        """
        if not key:
            raise EncodeError("Empty tuple not allowed as key")
        
        cdef Py_ssize_t num_components = len(key)
        cdef Py_ssize_t i
        cdef object component
        cdef int64_t int_val
        cdef bytes str_bytes
        cdef const unsigned char* str_data
        cdef Py_ssize_t str_len
        
        # Estimate buffer size: each component has type(1) + separator(1)
        # Plus 8 bytes for int or string length for str
        cdef Py_ssize_t estimated_size = num_components * 10
        
        # First pass: calculate exact size
        cdef Py_ssize_t total_size = 0
        for i in range(num_components):
            component = key[i]
            
            if isinstance(component, int):
                # Check bounds
                int_val = <int64_t>component
                if int_val < INT64_MIN_VAL or int_val > INT64_MAX_VAL:
                    raise IntegerOverflowError(
                        f"Integer {component} outside int64 range "
                        f"[{INT64_MIN_VAL}, {INT64_MAX_VAL}]"
                    )
                total_size += 1 + 8 + 1  # type + 8 bytes + separator
                
            elif isinstance(component, str):
                str_bytes = PyUnicode_AsUTF8String(component)
                str_len = PyBytes_GET_SIZE(str_bytes)
                
                # Check string length bounds
                if str_len == 0:
                    raise EncodeError(f"Empty string at index {i} not allowed")
                if str_len > MAX_STRING_LENGTH:
                    raise EncodeError(
                        f"String at index {i} too long: {str_len} bytes "
                        f"(max {MAX_STRING_LENGTH})"
                    )
                
                total_size += 1 + str_len + 1  # type + utf8 bytes + separator
            else:
                raise EncodeError(
                    f"Component at index {i} must be str or int, "
                    f"got {type(component).__name__}"
                )
        
        # Allocate output buffer
        cdef bytes result = PyBytes_FromStringAndSize(NULL, total_size)
        cdef unsigned char* buffer = <unsigned char*>PyBytes_AS_STRING(result)
        cdef Py_ssize_t pos = 0
        
        # Second pass: encode into buffer
        for i in range(num_components):
            component = key[i]
            
            if isinstance(component, int):
                int_val = <int64_t>component
                
                # Write type marker
                buffer[pos] = TYPE_INT
                pos += 1
                
                # Encode integer
                encode_integer_inline(int_val, &buffer[pos])
                pos += 8
                
                # Write separator
                buffer[pos] = SEPARATOR
                pos += 1
                
            else:  # isinstance(component, str)
                str_bytes = PyUnicode_AsUTF8String(component)
                str_data = <const unsigned char*>PyBytes_AS_STRING(str_bytes)
                str_len = PyBytes_GET_SIZE(str_bytes)
                
                # Write type marker
                buffer[pos] = TYPE_STR
                pos += 1
                
                # Copy string bytes
                memcpy(&buffer[pos], str_data, str_len)
                pos += str_len
                
                # Write separator
                buffer[pos] = SEPARATOR
                pos += 1
        
        return result
    
    def decode(self, bytes encoded):
        """Decode binary data back to original tuple key.
        
        Args:
            encoded: Previously encoded binary key
            
        Returns:
            Original tuple key
            
        Raises:
            DecodeError: If data is invalid or corrupted
        """
        if not encoded:
            raise DecodeError("Empty encoded key")
        
        cdef const unsigned char* data = <const unsigned char*>PyBytes_AS_STRING(encoded)
        cdef Py_ssize_t data_len = PyBytes_GET_SIZE(encoded)
        cdef Py_ssize_t pos = 0
        
        cdef list result = []
        cdef unsigned char type_marker
        cdef int64_t int_val
        cdef Py_ssize_t str_start, str_end
        cdef bytes str_bytes
        cdef str decoded_str
        
        while pos < data_len:
            # Read type marker
            if pos >= data_len:
                raise DecodeError("Unexpected end of data while reading type marker")
            
            type_marker = data[pos]
            pos += 1
            
            if type_marker == TYPE_INT:
                # Check we have enough bytes for integer
                if pos + 8 > data_len:
                    raise DecodeError(
                        f"Insufficient bytes for integer at offset {pos - 1}"
                    )
                
                # Decode integer
                int_val = decode_integer_inline(&data[pos])
                result.append(int_val)
                pos += 8
                
                # Check separator
                if pos >= data_len or data[pos] != SEPARATOR:
                    raise DecodeError(
                        f"Missing separator after integer at position {pos}"
                    )
                pos += 1
                
            elif type_marker == TYPE_STR:
                # Find next separator
                str_start = pos
                str_end = -1
                
                while pos < data_len:
                    if data[pos] == SEPARATOR:
                        str_end = pos
                        break
                    pos += 1
                
                if str_end == -1:
                    raise DecodeError(
                        f"Missing separator after string at position {str_start - 1}"
                    )
                
                # Decode UTF-8 string
                str_bytes = encoded[str_start:str_end]
                try:
                    decoded_str = PyUnicode_DecodeUTF8(
                        PyBytes_AS_STRING(str_bytes),
                        PyBytes_GET_SIZE(str_bytes),
                        NULL  # Use default error handling (strict)
                    )
                    result.append(decoded_str)
                except UnicodeDecodeError as e:
                    raise DecodeError(f"Invalid UTF-8 in encoded string: {e}")
                
                pos = str_end + 1
                
            else:
                raise DecodeError(
                    f"Invalid type marker at position {pos - 1}: 0x{type_marker:02x}"
                )
        
        return tuple(result)


__all__ = ['BinaryKeyCodec', 'IntegerOverflowError', 'EncodeError', 'DecodeError']
