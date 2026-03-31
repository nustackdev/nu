"""Weather station — reactive multi-shape monitoring.

Station     -> sensor readings (PV, persistent, observable)
Dashboard   -> live counters (PV)

Two subtrees race in parallel:
  feed   -> writes sensor data in a loop
  react  -> prints on every change, cancelled when feed completes

Flows: Seq, ForRange, If, Race, Delay, Print (from nu.abc)
Reactive: ReactWhile (from nu.shape)
"""

from __future__ import annotations

import nu_virtuals as ebv
from nu.abc.flows import Delay, ForRange, If, Print, Race, Seq
from nu.shape import Shape
from nu.shape.flows import ReactWhile


# ---- Shapes ----


class Station(Shape):
    """Sensor readings (PV substrate — observable)."""

    temperature = ebv.FloatRef.slot()
    wind_speed = ebv.FloatRef.slot()


class Dashboard(Shape):
    """Live counters (PV substrate)."""

    warnings = ebv.IntRef.slot()


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
            Station.temperature.store(18.0),
            Station.wind_speed.store(10.0),
            Dashboard.warnings.store(0),
            ForRange(
                0,
                N_READINGS,
                Seq(
                    Station.temperature.store(Station.temperature + TEMP_DRIFT),
                    Station.wind_speed.store(Station.wind_speed + WIND_DRIFT),
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
                    Dashboard.warnings.store(Dashboard.warnings + 1),
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
                    Dashboard.warnings.store(Dashboard.warnings + 1),
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
    from virtuals.tkv.storage import StorageProtocol

    from nu_virtuals.presets import text_storage
    from nu import Context

    with text_storage(".db-weather") as storage:
        ctx = Context().bind(storage, StorageProtocol)

        tree = ebv.auto_atomic(station)
        await tree.execute(ctx)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
