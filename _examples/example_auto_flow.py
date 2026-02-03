"""E2E Demo: auto_atomic — no manual Atomic wrapping."""

from __future__ import annotations

import every_pv as e
from every_pv.views import DictView
from everybase import Context, Flow, Term


# --- Shapes ---


class AppState(e.Shape):
    name = e.StrRef.slot()
    age = e.IntRef.slot()


# --- Minimal concrete Flows ---


class Print(Flow):
    """Print a child term's result."""

    def __init__(self, label: str, child: Term):
        super().__init__(child)
        self.label = label

    async def execute(self, ctx) -> None:
        value = await self.children[0].execute(ctx)
        print(f"  [{self.label}] {value!r}")


class Seq(Flow):
    """Sequential execution flow."""

    pass


# --- Minimal concrete apps ---


demos = [
    Seq(
        AppState.name.set("Alice"),
        AppState.age.set(30),
    ),
    Seq(
        Print("name", AppState.name.get()),
        Print("age", AppState.age.get()),
    ),
    Seq(
        AppState.age.set(31),
        Print("name", AppState.name.get()),
        Print("age", AppState.age.get()),
    ),
]

# --- Run ---


async def main():
    from tkv.tkv.storage import StorageProtocol

    from every_pv.adapters.codecs import TextCodec as Codec
    from every_pv.adapters.storages.textdb import TextStorage as Storage

    with Storage(".db", codec=Codec()) as storage:
        ctx = Context().with_handle(StorageProtocol, storage, shape=AppState)
        for i in range(len(demos)):
            # Get the tree
            tree = demos[i]
            # Add atomicity
            tree = e.auto_atomic(tree, AppState, DictView)
            # Add other features
            ...
            # Execute the tree
            await tree.execute(ctx)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
