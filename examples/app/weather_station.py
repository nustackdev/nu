"""Weather station -- reactive multi-shape monitoring.

A producer writes sensor readings in a loop while two reactive consumers race
alongside it, reacting to each change and updating a dashboard. Shapes live on
the virtuals substrate, so leaf ``.on_change()`` yields a live subscription.

Note: ``DelayedDo(0.02, nu.Noop())`` still fails ``flow_body_is_mutator`` (a
flow body must mutate; Noop does not) -- the last gap before this runs end to
end, pending the effect-only Command model. The reactive flows validate now.
"""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

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


def build_tree() -> object:
    """Build the full tree.

    Kept as a function (not a module constant) so the module imports cleanly --
    the reactive subtree only touches ``.on_change()`` when this runs.
    """
    return nu.Sequential(
        # Monitor
        nu.Race(
            # Producer: seed + generate sensor data
            nu.Sequential(
                Station.temperature.store(18.0),
                Station.wind_speed.store(10.0),
                Dashboard.warnings.store(0),
                nu.ForRangeDo(
                    0,
                    N_READINGS,
                    nu.Sequential(
                        Station.temperature.store(Station.temperature + TEMP_DRIFT),
                        Station.wind_speed.store(Station.wind_speed + WIND_DRIFT),
                        nu.DelayedDo(0.02, nu.Noop()),
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
                        Dashboard.warnings.store(Dashboard.warnings + 1),
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
                        Dashboard.warnings.store(Dashboard.warnings + 1),
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
    with tempfile.TemporaryDirectory() as tmp:
        db_path = str(Path(tmp) / "weather")
        with v.text_storage(db_path) as storage:
            nav = Navigator(storage)
            with storage.transaction() as tx:
                ctx = nu.Context().bind(Navigator, nav).bind(TransactionProtocol, tx)
                tree = v.auto_atomic(build_tree())
                await nu.arun(tree, ctx)


if __name__ == "__main__":
    asyncio.run(main())
