import nu


class Counter(nu.Shape):
    value: nu.v.IntRef


class Dashboard(nu.ui.Page):
    count: nu.ui.TextRef


class App(nu.ui.Index):
    pages = nu.ui.Pages({"/": Dashboard})


app = nu.With(
    nu.v.presets.rocksdb_navigator(".dbtest"),
    nu.ui.nudle.server(
        nu.v.auto_flow_atomic(
            nu.ReactForever(
                Counter.value.on_change(),
                Dashboard.count.set(Counter.value),
            ),
        ),
    ),
    body=(
        nu.IfDo(Counter.value.missing(), Counter.value.set(0))
        >> nu.ForeverDo(
            Counter.value.inc() >> nu.Delay(1.0),
        )
    ),
)

if __name__ == "__main__":
    import asyncio

    asyncio.run(nu.arun(nu.v.auto_flow_atomic(app)))
