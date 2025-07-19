from loomiverse.hfq.apps import HFQAppSpec
from loomiverse.hfq.services import DataStreamSpec

from loomicore.spec import ProxySpec
from loomidistributed.launcher.multiprocessing import MultiprocessingLauncherSpec
from loomidistributed.rpc.rpyc import RPyCUnixClientSpec, RPyCUnixConnectionSpec, RPyCUnixServerSpec
from loomidistributed.runtime import RuntimeSpec
from loomistd.codec.msgpack import MsgpackCodecSpec
from loomistd.kv.lmdb import LMDBStorageSpec
from loomistd.state import StateSpec

# ======================= #
# === Configure state === #
# ======================= #

state_spec = StateSpec(
    storage=LMDBStorageSpec(codec=MsgpackCodecSpec()),
).with_value_at("storage", "path", value=".db")

proxy_client_state_spec = RPyCUnixClientSpec(
    connection=RPyCUnixConnectionSpec(socket_path="/tmp/hfq_state.sock")
)
proxy_host_state_spec = RPyCUnixServerSpec(socket_path="/tmp/hfq_state.sock")

proxy_launcher_state_spec = MultiprocessingLauncherSpec(host=proxy_host_state_spec)

proxy_state_spec = ProxySpec(
    inner_spec=state_spec,
    client_spec=proxy_client_state_spec,
)

proxy_launchable_state_spec = ProxySpec(
    inner_spec=state_spec,
    client_spec=proxy_client_state_spec,
    launcher_spec=proxy_launcher_state_spec,
)

# ========================= #
# === Configure runtime === #
# ========================= #

# Create fleet of workers - each with their own launcher
num_workers = 4
fleet_worker_specs = []
for i in range(1, num_workers + 1):
    fleet_worker_specs.append(
        ProxySpec(
            inner_spec=HFQAppSpec(
                state=proxy_state_spec,
                name=f"worker_{i}",
                data_stram=DataStreamSpec(),
            ),
            client_spec=RPyCUnixClientSpec(
                connection=RPyCUnixConnectionSpec(socket_path=f"/tmp/hfq_worker_{i}.sock")
            ),
            launcher_spec=MultiprocessingLauncherSpec(
                host=RPyCUnixServerSpec(socket_path=f"/tmp/hfq_worker_{i}.sock")
            ),
        )
    )

runtime_spec = RuntimeSpec(
    fleet=tuple(fleet_worker_specs),
)

# ===================== #
# === Configure app === #
# ===================== #

app_spec = HFQAppSpec(
    state=proxy_state_spec,
    name=f"app",
    data_stram=DataStreamSpec(),
)
