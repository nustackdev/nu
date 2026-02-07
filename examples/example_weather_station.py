"""Weather station — reactive multi-substrate monitoring.

Station (PV)     -> sensor readings (persistent, observable)
Dashboard (dict) -> live counters (fast, ephemeral)

Two subtrees race in parallel:
  feed   -> writes sensor data in a loop
  react  -> prints on every change, cancelled when feed completes

Flows: Seq, ForRange, If, Race, ReactWhile, Delay, Print
"""

from __future__ import annotations

import eb_dict as mem
import eb_flow as f
import eb_pv as pv
from eb_shape import Shape


# ---- Shapes ----


class Station(Shape):
    """Sensor readings (PV substrate — observable)."""

    temperature = pv.FloatRef.slot()
    wind_speed = pv.FloatRef.slot()


class Dashboard(Shape):
    """Live counters (dict substrate — fast, ephemeral)."""

    warnings = mem.IntRef.slot()


# ---- Config ----

N_READINGS = 15
TEMP_DRIFT = 1.4
WIND_DRIFT = 2.5
TEMP_WARN = 32.0
WIND_WARN = 45.0


# ---- Tree ----

station = f.Seq(
    # Monitor
    f.Race(
        # Producer: seed + generate sensor data
        f.Seq(
            Station.temperature.set(18.0),
            Station.wind_speed.set(10.0),
            Dashboard.warnings.set(0),
            f.ForRange(
                0,
                N_READINGS,
                f.Seq(
                    Station.temperature.set(Station.temperature + TEMP_DRIFT),
                    Station.wind_speed.set(Station.wind_speed + WIND_DRIFT),
                    f.Delay(0.02),
                ),
            ),
        ),
        # Consumer: react to temperature
        f.ReactWhile(
            Station.temperature.on_change(),
            Station.temperature < 50.0,
            f.If(
                Station.temperature > TEMP_WARN,
                f.Seq(
                    Dashboard.warnings.set(Dashboard.warnings + 1),
                    f.Print("TEMP", Station.temperature),
                ),
            ),
        ),
        # Consumer: react to wind
        f.ReactWhile(
            Station.wind_speed.on_change(),
            Station.wind_speed < 80.0,
            f.If(
                Station.wind_speed > WIND_WARN,
                f.Seq(
                    Dashboard.warnings.set(Dashboard.warnings + 1),
                    f.Print("WIND", Station.wind_speed),
                ),
            ),
        ),
    ),
    # Dashboard
    f.Print("Temp", Station.temperature),
    f.Print("Wind", Station.wind_speed),
    f.Print("Warnings", Dashboard.warnings),
)


# ---- Run ----


async def main():
    from tkv.tkv.storage import StorageProtocol

    from eb_pv.adapters.codecs import TextCodec as Codec
    from eb_pv.adapters.observers.in_memory import InMemoryObserver
    from eb_pv.adapters.storages.textdb import TextStorage as Storage
    from eb_pv.views import DictView
    from everybase import Context

    display: dict = {}
    observer = InMemoryObserver(codec=Codec())
    observer.connect()
    with Storage(".db-weather", codec=Codec(), observer=observer) as storage:
        ctx = (
            Context()
            .with_handle(dict, display, shape=Dashboard)
            .with_handle(StorageProtocol, storage, shape=Station)
        )

        tree = pv.auto_atomic(station, Station, DictView)
        await tree.execute(ctx)
    observer.disconnect()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
