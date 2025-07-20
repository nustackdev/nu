import time

from loomiverse.hfq.apps import HFQApp
from loomiverse.hfq.services import UIService
from loomiverse.hfq.specs import app_spec, ui_spec

from loomi import Context
from loomix.logging import setup_logging

setup_logging(".logs", log_level=20)


def main():
    with HFQApp(app_spec) as app, UIService(ui_spec) as ui_service:
        start_time = time.perf_counter()

        app.evaluate(app.define(), Context(None))

        elapsed_time = time.perf_counter() - start_time
        print(f"Total execution time: {elapsed_time:.4f} seconds")


if __name__ == "__main__":
    main()
