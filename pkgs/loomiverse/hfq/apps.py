from __future__ import annotations

import math
import time

import attrs

from loomi.app.app import SyncApp
from loomi.app.expressions import Expression, Function, Parallel, Sequence
from loomi.attach import Attach
from loomi.evaluator.context import Context
from loomi.spec import ResourceSpec, Spec
from loomiverse.hfq.services import DataStream


class HFQApp(SyncApp):
    data_stram: DataStream = Attach()

    def start(self, context: Context):
        """
        Start the application.
        This method is called when the app is started.
        """
        print("🚀 HFQApp started")

    def ingest_stream(self, context: Context):
        """
        Ingest data from the stream.
        This method is called to ingest data from the stream.
        """
        i = 0
        while i < 100:
            i += 1
            candle = self.data_stram.get_candle()
            with self.state.state.at("canldes").with_list_view() as candles:
                candles.append(candle)
            time.sleep(0.1)

    def execute_trade(self, context: Context):
        """
        Perform a trade operation.
        This method is called to perform a trade operation.
        """
        i = 0
        while i < 100:
            i += 1
            with self.state.state.at("trades").with_list_view() as trades:
                trades.append(
                    {
                        "timestamp": time.time(),
                        "price": round(100 + math.sin(time.time()) * 10, 2),
                        "volume": round(1 + math.cos(time.time()) * 0.5, 2),
                    }
                )
            time.sleep(0.1)

    def finish(self, context: Context):
        """
        Finish the application.
        This method is called when the app is finished.
        """
        print("✅ HFQApp finished")

    def define(self) -> Expression:
        return Sequence(
            Function(self.start),
            Parallel(
                Function(self.ingest_stream),
                Function(self.execute_trade),
            ),
            Function(self.finish),
        )


@attrs.define(frozen=True, slots=True, kw_only=True)
class HFQAppSpec(ResourceSpec):
    name: str = "main_app"
    factory: type = HFQApp
    state: Spec
    data_stram: Spec
