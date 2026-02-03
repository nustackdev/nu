"""E2E Demo: every_pv with Shapes and Slots."""

from __future__ import annotations

import every_pv as e
from every_pv.views import DictView
from everybase import Context, Flow, Term


# --- Shape ---


class AppState(e.Shape):
    name = e.StrRef.slot()
    age = e.IntRef.slot()


# --- Minimal concrete nodes (not in everyabc — defined per app) ---


class Print(Flow):
    """Print a child term's result. Returns the value."""

    def __init__(self, label: str, child: Term):
        super().__init__(child)
        self.label = label

    def with_children(self, *children):
        if children == self._children:
            return self
        return Print(self.label, *children)

    async def execute(self, ctx) -> None:
        value = await self.children[0].execute(ctx)
        print(f"  [{self.label}] {value!r}")


class Seq(Flow):
    """Sequential execution flow."""

    pass


async def main():
    from tkv.tkv.storage import StorageProtocol

    from every_pv.adapters.codecs import TextCodec as Codec
    from every_pv.adapters.storages.textdb import TextStorage as Storage

    with Storage(".db", codec=Codec()) as storage:
        ctx = Context().with_handle(StorageProtocol, storage, shape=AppState)

        await e.Atomic(
            AppState,
            DictView,
            Seq(
                AppState.name.set("Alice"),
                AppState.age.set(30),
            ),
        ).execute(ctx)

        await e.Atomic(
            AppState,
            DictView,
            Seq(
                Print("name", AppState.name.get()),
                Print("age", AppState.age.get()),
            ),
        ).execute(ctx)

        await e.Atomic(
            AppState,
            DictView,
            Seq(
                AppState.age.set(31),
                Print("name", AppState.name.get()),
                Print("age", AppState.age.get()),
            ),
        ).execute(ctx)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
