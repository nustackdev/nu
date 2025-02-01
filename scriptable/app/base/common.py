class AppCommonBase:
    def __init__(self):
        pass

    @property
    def key(self) -> str:
        return str(id(self))[:12]


__all__ = [
    "AppCommonBase",
]
