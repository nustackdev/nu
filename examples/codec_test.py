#!/usr/bin/env python3
"""Calculator service example using Invisibles over NetKit."""

from __future__ import annotations

import logging


logging.basicConfig(level=logging.INFO)


# ============================================================================
# Main
# ============================================================================


def main():
    from rwtup.binary_codec import BinaryKeyCodec
    from rwtup.string_codec import StringKeyCodec

    string_codec = StringKeyCodec()
    binary_codec = BinaryKeyCodec()

    key = ("user", -49999, "settings")
    encoded_str = string_codec.encode(key)
    decoded_str = string_codec.decode(encoded_str)
    assert decoded_str == key
    print(f"String Codec: {key} -> {encoded_str} -> {decoded_str}")
    encoded_bin = binary_codec.encode(key)
    decoded_bin = binary_codec.decode(encoded_bin)
    assert decoded_bin == key
    print(f"Binary Codec: {key} -> {encoded_bin} -> {decoded_bin}")

    assert binary_codec.encode((11, "a")) < binary_codec.encode((11, "v"))

    a = {1: 2, (1, 2, [1, 2]): 3}


class A:
    pass


def codec():
    from redwood.codec import BinaryCodec, BinaryCodecSpec, TextCodec, TextCodecSpec

    class A:
        pass

    with BinaryCodec(BinaryCodecSpec()) as codec:
        key = ("users", 42, "profile")
        value = {"name": "Alice", "age": 30}
        encoded_key = codec.encode_key(key)
        encoded_value = codec.encode_value(value)
        print(f"Encoded key: {encoded_key}")
        print(f"Encoded value: {encoded_value}")
        assert key == codec.decode_key(encoded_key)
        assert value == codec.decode_value(encoded_value)

    with TextCodec(TextCodecSpec()) as codec:
        key = ("users", 42, "profile")
        value = 12
        encoded_key = codec.encode_key(key)
        encoded_value = codec.encode_value(value)
        print(f"Encoded key: {encoded_key}")
        print(f"Encoded value: {encoded_value}")
        assert key == codec.decode_key(encoded_key)
        assert value == codec.decode_value(encoded_value)


def storage():
    from redwood.codec import BinaryCodecSpec
    from redwood.storage.lmdb_storage import LMDBStorage, LMDBStorageSpec

    with LMDBStorage(
        LMDBStorageSpec(
            codec=BinaryCodecSpec(),
        )
    ) as storage:
        storage.set(("users", 1), {"name": "Alice"})
        storage.set(("users", 2), {"name": "Bob"})
        print("User 1:", storage.get(("users", 1)))
        print("User 2:", storage.get(("users", 2)))
        # storage.delete(("users", 1))
        try:
            print("User 1:", storage.get(("users", 1)))
        except Exception as e:
            print("Error fetching user 1:", e)


if __name__ == "__main__":
    storage()
