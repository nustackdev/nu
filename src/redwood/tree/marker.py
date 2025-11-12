"""Container type marker system.

This module implements the container type marking system that distinguishes
containers from primitive values in storage. Markers embed structure and
protocol information using Unicode Private Use Area characters for collision
resistance.

========================================================================

PURPOSE:
  Distinguishes container objects from primitive values using an
  embedded type marker that can be safely stored alongside data.

MARKER STRUCTURE:
┌──────────────────────────────────────────────────────────────────┐
│  Type Marker Tuple (4 elements)                                  │
├──────────────┬─────────────┬─────────────┬───────────────────────┤
│   Sentinel   │  Structure  │  Protocol   │      Sentinel         │
│   (string)   │    (enum)   │   (flags)   │      (string)         │
│              │             │             │                       │
│ "\ue000      │ Dict        │ 0x01 = Mut  │ "\ue000               │
│  \U000f0000" │ List        │             │  \U000f0000"          │
└──────────────┴─────────────┴─────────────┴───────────────────────┘
      [0]            [1]           [2]               [3]

SENTINEL CHARACTER COMPOSITION:
┌──────────────────────────────────────────────────────────────────┐
│ Unicode Private Use Area Marker (2 characters, 7 UTF-8 bytes)    │
├──────────────────────────────┬───────────────────────────────────┤
│  Character 1: U+E000         │  Character 2: U+F0000             │
│  * From BMP Private Use Area │  * From Supplementary PUA-A       │
│  * Range: U+E000 - U+F8FF    │  * Range: U+F0000 - U+FFFFD       │
│  * UTF-8: 3 bytes (EE 80 80) │  * UTF-8: 4 bytes (F4 8F 80 80)   │
└──────────────────────────────┴───────────────────────────────────┘

UNICODE PLANE LAYOUT:
┌──────────────────────────────────────────────────────────────────┐
│ Plane 0 (BMP) - Basic Multilingual Plane                         │
│  U+0000 ────────── Standard Characters ────────── U+DFFF         │
│  U+E000 ▓▓▓▓ Private Use Area (PUA) ▓▓▓▓ U+F8FF  ← 1st char      │
│  U+F900 ────────── More Standard ─────────────── U+FFFF          │
├──────────────────────────────────────────────────────────────────┤
│ Planes 1-14: Standard Assignments (Emoji, Historic, etc.)        │
├──────────────────────────────────────────────────────────────────┤
│ Plane 15 (SPUA-A) - Supplementary Private Use Area A             │
│  U+F0000 ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ U+FFFFD  ← 2nd char        │
│  65,534 Private Use Code Points                                  │
└──────────────────────────────────────────────────────────────────┘

COLLISION RESISTANCE:
  Layer 1 - Private Use Areas:
    - Never assigned to standard characters (Unicode Stability Policy)
    - Not used in any human writing system
    - No standard keyboard input or visual representation

  Layer 2 - Multi-Plane Strategy:
    - Spans two separate Unicode planes (Plane 0 + Plane 15)
    - Requires intentional dual-plane PUA usage to collide
    - Sentinel bookending (same marker at positions [0] and [3])

COLLISION PROBABILITY:
  The marker tuple contains a string combining PUA characters from
  two separate Unicode planes. This specific combination makes
  accidental collision VIRTUALLY IMPOSSIBLE.

USAGE:
  The marker is embedded in serialized container data to enable:
  - Type identification during deserialization
  - Distinction between containers and primitive values
  - Structure and protocol flag recovery
  - Safe coexistence with user data

MORE INFO:
  Unicode Standard - Private Use Areas
  https://www.unicode.org/faq/private_use.html
  https://en.wikipedia.org/wiki/Private_Use_Areas
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .types import ContainerProtocol, ContainerStructure


if TYPE_CHECKING:
    from redwood.types import Value


__all__ = [
    "MARKER_SENTINEL",
    "create_marker",
    "extract_marker",
    "is_marker",
    "validate_marker_compatibility",
]


# Sentinel composed of two Private Use Area characters from different planes
# U+E000 (BMP PUA) + U+F0000 (Supplementary PUA-A)
MARKER_SENTINEL = "\ue000\U000f0000"


def create_marker(
    structure: ContainerStructure,
    protocol: ContainerProtocol,
) -> tuple[str, ContainerStructure, int, str]:
    """Create a container type marker tuple.

    The marker embeds type information that can be stored alongside container
    data to enable type identification during deserialization.

    Args:
        structure: Container structure type (Dict/List/Set/etc)
        protocol: Container protocol flags (Mutable/Ordered/etc)

    Returns:
        Tuple containing: (sentinel, structure_enum, protocol_int, sentinel)
    """
    return (MARKER_SENTINEL, structure, protocol.value, MARKER_SENTINEL)


def extract_marker(value: Value) -> tuple[ContainerStructure, ContainerProtocol] | None:
    """Extract structure and protocol from a marker tuple.

    Validates the marker structure and extracts embedded type information.
    Returns None if the value is not a valid container marker.

    Args:
        value: Raw value from storage to parse as marker

    Returns:
        Tuple of (structure, protocol) if valid marker, None otherwise
    """
    # Validate basic structure
    if (
        type(value) is not tuple
        or len(value) != 4
        or value[0] != MARKER_SENTINEL
        or value[3] != MARKER_SENTINEL
    ):
        return None

    structure = ContainerStructure(value[1])  # type: ignore
    protocol = ContainerProtocol(value[2])
    return structure, protocol


def is_marker(value: Value) -> bool:
    """Quick check if value is a container marker.

    This is a fast boolean check without extracting the full marker data.

    Args:
        value: Value to check

    Returns:
        True if value is a valid container marker, False otherwise
    """
    return extract_marker(value) is not None


def validate_marker_compatibility(
    stored_marker: Value,
    expected_structure: ContainerStructure,
    expected_protocol: ContainerProtocol,
) -> bool:
    """Check if stored marker is compatible with expected type.

    Validates that a marker's structure matches exactly and protocol
    has at least one common flag with expectations.

    Args:
        stored_marker: Marker value from storage
        expected_structure: Required structure type
        expected_protocol: Required protocol flags (bitwise match)

    Returns:
        True if marker is compatible with expectations
    """
    marker_info = extract_marker(stored_marker)
    if marker_info is None:
        return False

    stored_structure, stored_protocol = marker_info

    # Structure must match exactly
    if stored_structure != expected_structure:
        return False

    # Protocol must have at least one common flag
    if not (expected_protocol & stored_protocol):
        return False

    return True
