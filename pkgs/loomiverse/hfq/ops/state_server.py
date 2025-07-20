from loomiverse.hfq.specs import proxy_host_state_spec, state_spec

from loomidistributed.rpc.rpyc import RPyCUnixServer
from loomistd.state import StateService
from loomix.logging import setup_logging

setup_logging(".logs", log_level=20)


def main():
    with StateService(state_spec) as state_service:
        with RPyCUnixServer(proxy_host_state_spec) as server:
            print("State service and RPyC server started.")
            server.start()
            print("Server is stopped.")


if __name__ == "__main__":
    main()
