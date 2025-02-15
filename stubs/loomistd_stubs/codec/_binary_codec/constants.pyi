from struct import Struct

__all__ = [
    "MAX_DEPTH",
    "MAX_COLLECTION_SIZE",
    "MAX_STR_SIZE",
    "PATH_SEPARATOR",
    "TYPE_NONE",
    "TYPE_TRUE",
    "TYPE_FALSE",
    "TYPE_INT",
    "TYPE_FLOAT",
    "TYPE_STR",
    "TYPE_BYTES",
    "TYPE_LIST",
    "TYPE_DICT",
    "TYPE_END",
    "TYPE_MARKERS",
    "INT64_STRUCT",
    "UINT32_STRUCT",
    "DOUBLE_STRUCT",
]

MAX_DEPTH: int
MAX_COLLECTION_SIZE: int
MAX_STR_SIZE: int
PATH_SEPARATOR: bytes
TYPE_NONE: int
TYPE_TRUE: int
TYPE_FALSE: int
TYPE_INT: int
TYPE_FLOAT: int
TYPE_STR: int
TYPE_BYTES: int
TYPE_LIST: int
TYPE_DICT: int
TYPE_END: int
TYPE_MARKERS: dict[int, bytes]
INT64_STRUCT: Struct
UINT32_STRUCT: Struct
DOUBLE_STRUCT: Struct
