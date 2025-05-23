from __future__ import annotations

from .base import StatePath

__all__ = [
    "DataPath",
    "StructPath",
]


class DataPath(StatePath):
    @property
    def root_marker(self) -> str:
        """
        Get the root marker for the path.

        Returns:
            str: Root marker for the path
        """
        return self.DATA_ROOT_MARKER


class StructPath(StatePath):
    @property
    def root_marker(self) -> str:
        """
        Get the root marker for the path.

        Returns:
            str: Root marker for the path
        """
        return self.STRUCT_ROOT_MARKER
