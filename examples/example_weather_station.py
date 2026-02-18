"""Weather station — reactive multi-shape monitoring.

Station     -> sensor readings (PV, persistent, observable)
Dashboard   -> live counters (PV)

Two subtrees race in parallel:
  feed   -> writes sensor data in a loop
  react  -> prints on every change, cancelled when feed completes

Flows: Seq, ForRange, If, Race, Delay, Print (from everybase.abc)
Reactive: ReactWhile (from everyshape)
"""

from __future__ import annotations

import everypv as pv
from everybase.abc.flows import Delay, ForRange, If, Print, Race, Seq
from everyshape import Shape
from everyshape.flows import ReactWhile


# ---- Shapes ----


class Station(Shape):
    """Sensor readings (PV substrate — observable)."""

    temperature = pv.FloatRef.slot()
    wind_speed = pv.FloatRef.slot()


class Dashboard(Shape):
    """Live counters (PV substrate)."""

    warnings = pv.IntRef.slot()


# ---- Config ----

N_READINGS = 15
TEMP_DRIFT = 1.4
WIND_DRIFT = 2.5
TEMP_WARN = 32.0
WIND_WARN = 45.0


# ---- Tree ----

station = Seq(
    # Monitor
    Race(
        # Producer: seed + generate sensor data
        Seq(
            Station.temperature.set(18.0),
            Station.wind_speed.set(10.0),
            Dashboard.warnings.set(0),
            ForRange(
                0,
                N_READINGS,
                Seq(
                    Station.temperature.set(Station.temperature + TEMP_DRIFT),
                    Station.wind_speed.set(Station.wind_speed + WIND_DRIFT),
                    Delay(0.02),
                ),
            ),
        ),
        # Consumer: react to temperature
        ReactWhile(
            Station.temperature.on_change(),
            Station.temperature < 50.0,
            If(
                Station.temperature > TEMP_WARN,
                Seq(
                    Dashboard.warnings.set(Dashboard.warnings + 1),
                    Print("TEMP", Station.temperature),
                ),
            ),
        ),
        # Consumer: react to wind
        ReactWhile(
            Station.wind_speed.on_change(),
            Station.wind_speed < 80.0,
            If(
                Station.wind_speed > WIND_WARN,
                Seq(
                    Dashboard.warnings.set(Dashboard.warnings + 1),
                    Print("WIND", Station.wind_speed),
                ),
            ),
        ),
    ),
    # Dashboard
    Print("Temp", Station.temperature),
    Print("Wind", Station.wind_speed),
    Print("Warnings", Dashboard.warnings),
)


# ---- Run ----


async def main():
    from tkv.tkv.storage import StorageProtocol

    from everybase import Context
    from everypv.adapters.codecs import TextCodec as Codec
    from everypv.adapters.observers.in_memory import InMemoryObserver
    from everypv.adapters.storages.textdb import TextStorage as Storage

    observer = InMemoryObserver(codec=Codec())
    observer.connect()
    with Storage(".db-weather", codec=Codec(), observer=observer) as storage:
        ctx = Context().with_handle(StorageProtocol, storage)

        tree = pv.auto_atomic(station)
        await tree.execute(ctx)
    observer.disconnect()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
