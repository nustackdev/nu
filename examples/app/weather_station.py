"""Weather station -- reactive multi-shape monitoring.

Station     -> sensor readings (virtuals, persistent, observable)
Dashboard   -> live counters (virtuals)

Two subtrees race in parallel:
  feed   -> writes sensor data in a loop
  react  -> prints on every change, cancelled when feed completes

Flows: Sequential, ForRangeDo, IfDo, Race, DelayedDo, print (from nu.flows / nu.core.io)
Reactive: ReactWhile (from nu.flows)

Reactivity: ``.on_change()`` on virtuals leaf refs is wired via
:class:`nu.core.reactive.OnPrimitiveChangeQuery`, and the collection refs
(Dict/List/Set/Shape/ShapesDict/ShapesList) are all at the Reactive tier of the
shape blueprint -- their ``on_change()`` / ``on_child_change`` /
``on_children_change`` / ``on_descendants_change`` land as the matching
``nu.core.reactive`` queries. A leaf subscription resolves to a live virtuals
``Subscription`` and receives real change notifications after commit + observer
flush.

FIXME (composition laws, model-side): v2 laws currently reject
``Race(producer, ReactWhile, ReactWhile)`` because Race is a Strategy demanding
mutating children while ReactWhile is a StreamQuery. Also
``DelayedDo(delay, Noop())`` fails ``flow_body_is_mutator`` since Noop is a
scalar_query. Running this example end-to-end waits on either a law relaxation
for reactive stream branches inside strategies, or a "stream sink" adapter that
counts as a mutator. The reactive substrate itself is ready.
"""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

import nu.virtuals as v
from nu import Context, arun
from nu.core import Noop
from nu.core.io import print as nu_print
from nu.domains.shape import Shape
from nu.flows import DelayedDo, ForRangeDo, IfDo, Race, ReactWhile, Sequential
from nu.virtuals.presets import text_storage
from virtuals import Navigator
from virtuals.tkv.storage import TransactionProtocol


# ---- Shapes ----


class Station(Shape):
    """Sensor readings (virtuals substrate -- observable)."""

    temperature = v.FloatRef.slot()
    wind_speed = v.FloatRef.slot()


class Dashboard(Shape):
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

    Kept as a function (not a module-level constant) so the module imports
    cleanly on a nu build where virtuals ``on_change()`` is not yet wired --
    the reactive subtree only touches ``.on_change()`` when the function runs.
    """
    return Sequential(
        # Monitor
        Race(
            # Producer: seed + generate sensor data
            Sequential(
                Station.temperature.store(18.0),
                Station.wind_speed.store(10.0),
                Dashboard.warnings.store(0),
                ForRangeDo(
                    0,
                    N_READINGS,
                    Sequential(
                        Station.temperature.store(Station.temperature + TEMP_DRIFT),
                        Station.wind_speed.store(Station.wind_speed + WIND_DRIFT),
                        DelayedDo(0.02, Noop()),
                    ),
                ),
            ),
            # Consumer: react to temperature
            ReactWhile(
                Station.temperature.on_change(),
                Station.temperature < 50.0,
                IfDo(
                    Station.temperature > TEMP_WARN,
                    Sequential(
                        Dashboard.warnings.store(Dashboard.warnings + 1),
                        nu_print("TEMP", Station.temperature),
                    ),
                ),
            ),
            # Consumer: react to wind
            ReactWhile(
                Station.wind_speed.on_change(),
                Station.wind_speed < 80.0,
                IfDo(
                    Station.wind_speed > WIND_WARN,
                    Sequential(
                        Dashboard.warnings.store(Dashboard.warnings + 1),
                        nu_print("WIND", Station.wind_speed),
                    ),
                ),
            ),
        ),
        # Dashboard
        nu_print("Temp", Station.temperature),
        nu_print("Wind", Station.wind_speed),
        nu_print("Warnings", Dashboard.warnings),
    )


# ---- Run ----


async def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db_path = str(Path(tmp) / "weather")
        with text_storage(db_path) as storage:
            nav = Navigator(storage)
            with storage.transaction() as tx:
                ctx = (
                    Context()
                    .bind(Navigator, nav)
                    .bind(TransactionProtocol, tx)
                )
                tree = v.auto_atomic(build_tree())
                await arun(tree, ctx)


if __name__ == "__main__":
    asyncio.run(main())
