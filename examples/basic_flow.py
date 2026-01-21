"""Basic Everybase example - Counter."""

from everyshape import Shape

import everybase as e


# =============================================
# Shapes
# =============================================


class Counter(Shape):
    """Simple counter state."""

    value = e.slot.IntSlot()
    name = e.slot.StrSlot()


class S(Shape):
    """App state."""

    counter = e.slot.ShapeSlot(Counter)
    nums = e.slot.ListSlot(int)
    mmap = e.slot.DictSlot(int)


# =============================================
# Flows
# =============================================

update_flow = e.flow.Sequence(
    e.flow.Print("Starting..."),
    S.counter.value.set(0),
    S.counter.value.set(S.counter.value.get() + 10),
    S.counter.value.set(S.counter.value.get() * 2),
    e.flow.Print("Done!"),
)

observe_flow = e.flow.ReactWhile(
    S.counter.value.on_change(),
    S.counter.value.get() < 20,
    e.flow.Seq(e.flow.Print("Change detected {}", S.counter.value.get())),
)

main_flow = e.flow.Seq(
    e.flow.Print("Init"),
    S.counter.name.set("mycounter"),
    S.counter.value.set(0),
    e.flow.Print("Init done: {}", S.counter.extract()),
    e.flow.Parallel(e.flow.Delay(0.1, update_flow), observe_flow),
)


# =============================================
# Execution
# =============================================


async def main():
    from everybase.top import regular_provider, text_storage

    with text_storage(".db12") as storage:
        await main_flow.start_flow(regular_provider(storage))


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
