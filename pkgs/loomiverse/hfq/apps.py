from __future__ import annotations

import random
import time

import attrs
from loomiverse.hfq.services import DataStream

from loomi import (
    Attach,
    Context,
    Expression,
    Function,
    Parallel,
    ResourceSpec,
    Sequence,
    Spec,
    SyncApp,
)


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
        for j in range(10):
            with self.state.state.at("canldes").with_list_view() as candles:
                for k in range(100):
                    candle = self.data_stram.get_candle()
                    candles.append(candle)
            print(f"Candles ingested: {k}")

    def execute_trade(self, context: Context):
        """
        Perform a trade operation.
        This method is called to perform a trade operation.
        """
        for j in range(10):
            with self.state.state.at("trades").with_list_view() as trades:
                for k in range(100):
                    trade = {
                        "timestamp": time.time(),
                        "price": round(100 + random.random() * 10, 2),
                        "volume": round(1 + random.random() * 0.5, 2),
                    }
                    trades.append(trade)
            print(f"Trades executed: {k}")

    def finish(self, context: Context):
        """
        Finish the application.
        This method is called when the app is finished.
        """
        print("✅ HFQApp finished")

    def define(self) -> Expression:
        return Sequence(
            Function(self.start),
            Sequence(
                *[
                    Parallel(
                        Function(self.execute_trade),
                        Function(self.ingest_stream),
                    )
                    for _ in range(10)
                ]
            ),
            Function(self.finish),
        )


@attrs.define(frozen=True, slots=True, kw_only=True)
class HFQAppSpec(ResourceSpec):
    name: str = "main_app"
    factory: type = HFQApp
    state: Spec
    data_stram: Spec
