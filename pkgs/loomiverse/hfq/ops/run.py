from loomi.evaluator.context import Context
from loomidistributed.runtime import Runtime
from loomiverse.hfq.apps import HFQApp
from loomiverse.hfq.specs import app_spec, runtime_spec
from loomix.logging import setup_logging

setup_logging(".logs", log_level=20)


def main():
    with HFQApp(app_spec) as app:
        with Runtime(runtime_spec) as runtime:
            expr = app.define()
            expr.evaluate(runtime, Context(expr))


if __name__ == "__main__":
    main()
