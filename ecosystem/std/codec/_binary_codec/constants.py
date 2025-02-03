from struct import Struct

# Spec constants
MAX_DEPTH = 100
MAX_COLLECTION_SIZE = 1_000_000
MAX_STR_SIZE = 10 * 1024 * 1024  # 10MB
PATH_SEPARATOR = b"\xfe"

# Type markers as integers for faster comparison
TYPE_NONE = 0
TYPE_TRUE = 1
TYPE_FALSE = 2
TYPE_INT = 3
TYPE_FLOAT = 4
TYPE_STR = 5
TYPE_BYTES = 6
TYPE_LIST = 7
TYPE_DICT = 8
TYPE_END = 9

# Convert to bytes only once
TYPE_MARKERS = {
    TYPE_NONE: b"\x00",
    TYPE_TRUE: b"\x01",
    TYPE_FALSE: b"\x02",
    TYPE_INT: b"\x03",
    TYPE_FLOAT: b"\x04",
    TYPE_STR: b"\x05",
    TYPE_BYTES: b"\x06",
    TYPE_LIST: b"\x07",
    TYPE_DICT: b"\x08",
    TYPE_END: b"\x09",
}

# Pre-compiled struct formats
INT64_STRUCT = Struct(">q")  # big-endian int64
UINT32_STRUCT = Struct(">I")  # big-endian uint32
DOUBLE_STRUCT = Struct(">d")  # big-endian double
