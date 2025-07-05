from __future__ import annotations

from .manager import ResolutionManager

# Global service instance
_resolution_manager: ResolutionManager | None = None


def get_resolution_manager() -> ResolutionManager:
    """
    Get the global resolution manager instance.

    This function initializes the resolution manager if it hasn't been created yet.
    It ensures that there is a single instance of the resolution manager throughout
    the application lifecycle.
    """
    global _resolution_manager
    if _resolution_manager is None:
        _resolution_manager = ResolutionManager()
    return _resolution_manager
