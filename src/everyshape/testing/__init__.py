"""Testing utilities for everyshape.

This module provides reusable test infrastructure for packages that implement
everyshape protocols. Import compliance test suites to verify your implementations.

Example:
    ```python
    from everyshape.testing import (
        StorageProtocolCompliance,
        ObserverCompliance,
        KeyCodecCompliance,
    )


    class TestMyStorage(StorageProtocolCompliance):
        @pytest.fixture
        def storage(self):
            db = MyStorage()
            db.open()
            yield db
            db.close()


    class TestMyObserver(ObserverCompliance):
        @pytest.fixture
        def observable_storage(self):
            return MyObservableStorage()


    class TestMyCodec(KeyCodecCompliance):
        @pytest.fixture
        def codec(self):
            return MyKeyCodec()
    ```
"""

from everyshape.testing.codec_compliance import (
    KeyCodecCompliance,
    ValueCodecCompliance,
)
from everyshape.testing.observer_compliance import (
    ObserverCompliance,
    RegistryCompliance,
    SubscriptionCompliance,
)
from everyshape.testing.storage_compliance import StorageProtocolCompliance


__all__ = [  # noqa: RUF022
    # Storage
    "StorageProtocolCompliance",
    # Observer
    "ObserverCompliance",
    "RegistryCompliance",
    "SubscriptionCompliance",
    # Codec
    "KeyCodecCompliance",
    "ValueCodecCompliance",
]
