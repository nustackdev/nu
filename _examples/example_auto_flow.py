"""E2E Demo: auto_atomic — no manual Atomic wrapping."""

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
    """Print a child term's result."""

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

        # Pure topology — no Atomic wrapping needed.
        # auto_atomic injects Atomic spans around Term-only subtrees.

        await e.auto_atomic(
            Seq(
                AppState.name.set("Alice"),
                AppState.age.set(30),
            ),
            AppState,
            DictView,
        ).execute(ctx)

        await e.auto_atomic(
            Seq(
                Print("name", AppState.name.get()),
                Print("age", AppState.age.get()),
            ),
            AppState,
            DictView,
        ).execute(ctx)

        await e.auto_atomic(
            Seq(
                AppState.age.set(31),
                Print("name", AppState.name.get()),
                Print("age", AppState.age.get()),
            ),
            AppState,
            DictView,
        ).execute(ctx)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
