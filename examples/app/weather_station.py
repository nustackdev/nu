"""Weather station -- reactive multi-shape monitoring.

A producer writes sensor readings in a loop while two reactive consumers race
alongside it, reacting to each change and updating a dashboard. Shapes live on
the virtuals substrate, so leaf ``.on_change()`` yields a live subscription.

``nu.Delay(0.02)`` in the producer loop is a bare wait -- a childless delay
flow, no body.
"""

from __future__ import annotations

import asyncio

import nu
import nu.virtuals as v
from virtuals import Navigator
from virtuals.tkv.storage import TransactionProtocol


# ---- Shapes ----


class Station(nu.Shape):
    """Sensor readings (virtuals substrate -- observable)."""

    temperature = v.FloatRef.slot()
    wind_speed = v.FloatRef.slot()


class Dashboard(nu.Shape):
    """Live counters (virtuals substrate)."""

    warnings = v.IntRef.slot()


# ---- Config ----

N_READINGS = 15
TEMP_DRIFT = 1.4
WIND_DRIFT = 2.5
TEMP_WARN = 32.0
WIND_WARN = 45.0


# ---- Tree ----


def build_tree() -> nu.Nu:
    """Build the full tree.

    Kept as a function (not a module constant) so the module imports cleanly --
    the reactive subtree only touches ``.on_change()`` when this runs.
    """
    return nu.Sequential(
        # Monitor
        nu.Race(
            # Producer: seed + generate sensor data
            nu.Sequential(
                Station.temperature.set(18.0),
                Station.wind_speed.set(10.0),
                Dashboard.warnings.set(0),
                nu.ForRangeDo(
                    0,
                    N_READINGS,
                    nu.Sequential(
                        Station.temperature.set(Station.temperature + TEMP_DRIFT),
                        Station.wind_speed.set(Station.wind_speed + WIND_DRIFT),
                        nu.Delay(0.02),
                    ),
                ),
            ),
            # Consumer: react to temperature
            nu.ReactWhile(
                Station.temperature.on_change(),
                Station.temperature < 50.0,
                nu.IfDo(
                    Station.temperature > TEMP_WARN,
                    nu.Sequential(
                        Dashboard.warnings.set(Dashboard.warnings + 1),
                        nu.print("TEMP", Station.temperature),
                    ),
                ),
            ),
            # Consumer: react to wind
            nu.ReactWhile(
                Station.wind_speed.on_change(),
                Station.wind_speed < 80.0,
                nu.IfDo(
                    Station.wind_speed > WIND_WARN,
                    nu.Sequential(
                        Dashboard.warnings.set(Dashboard.warnings + 1),
                        nu.print("WIND", Station.wind_speed),
                    ),
                ),
            ),
        ),
        # Dashboard
        nu.print("Temp", Station.temperature),
        nu.print("Wind", Station.wind_speed),
        nu.print("Warnings", Dashboard.warnings),
    )


# ---- Run ----


async def main() -> None:
    # Ephemeral: every run reseeds Station/Dashboard from scratch, so no
    # on-disk persistence is needed -- memory_storage keeps this on the
    # virtuals substrate (real observer, real .on_change()) without a backend.
    with v.memory_storage() as storage:
        nav = Navigator(storage)
        with storage.transaction() as tx:
            ctx = nu.Context().bind(Navigator, nav).bind(TransactionProtocol, tx)
            tree = v.tree.auto_flow_atomic(build_tree())
            await nu.arun(tree, ctx)


if __name__ == "__main__":
    asyncio.run(main())
