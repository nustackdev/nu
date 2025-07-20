import time

from loomiverse.hfq.apps import HFQApp
from loomiverse.hfq.services import UIService
from loomiverse.hfq.specs import app_spec, runtime_spec, ui_spec

from loomi.evaluator.context import Context
from loomidistributed.runtime import Runtime
from loomix.logging import setup_logging

setup_logging(".logs", log_level=20)


def main():
    with HFQApp(app_spec) as app:
        with Runtime(runtime_spec) as runtime:
            with UIService(ui_spec) as ui_service:
                start_time = time.perf_counter()

                expr = app.define()
                expr.evaluate(runtime, Context(expr))

                elapsed_time = time.perf_counter() - start_time
                print(f"Total execution time: {elapsed_time:.4f} seconds")


if __name__ == "__main__":
    main()
