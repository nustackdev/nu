import datetime
import random

import attrs

from loomi.service import SyncService
from loomi.spec import ResourceSpec


class DataStream(SyncService):
    """
    Data ingestion service that processes and stores data.

    This service is responsible for ingesting data, processing it, and storing the results.
    It can be extended to implement specific data processing logic.
    """

    def get_candle(self):
        # Generate random candle data
        timestamp = datetime.datetime.now()
        open_price = round(random.uniform(100, 200), 2)
        high_price = round(open_price * random.uniform(1, 1.05), 2)
        low_price = round(open_price * random.uniform(0.95, 1), 2)
        close_price = round(random.uniform(low_price, high_price), 2)
        volume = round(random.uniform(1000, 10000), 2)

        return {
            "timestamp": timestamp,
            "open": open_price,
            "high": high_price,
            "low": low_price,
            "close": close_price,
            "volume": volume,
        }


@attrs.define(frozen=True, slots=True, kw_only=True)
class DataStreamSpec(ResourceSpec):
    """
    Specification for the HFQ application.

    This spec defines the application and its resources.
    """

    name: str = "DataStream"
    factory: type[DataStream] = DataStream
