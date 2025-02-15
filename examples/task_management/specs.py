from pathlib import Path

from services import NotificationService, TaskService, UserService

from loomi import Spec
from loomistd.codec.json import JSONCodec
from loomistd.observer.in_memory import InMemoryObserver
from loomistd.state import State
from loomistd.storage.file_storage import FileStorage

# --- Base storage and state setup --- #

json_codec_spec = Spec(factory=JSONCodec, name="json_codec")

storage_spec = Spec(
    factory=FileStorage,
    name="task_storage",
    mode="write",
    path=Path("./.state/tasks"),
    _codec=json_codec_spec,
)

observer_spec = Spec(
    factory=InMemoryObserver,
    name="task_observer",
    _codec=json_codec_spec,
)

state_spec = Spec(
    factory=State,
    name="task_state",
    _storage=storage_spec,
    _observer=observer_spec,
)

# --- Service specs --- #

notification_service_spec = Spec(name="Notifications", factory=NotificationService)

user_service_spec = Spec(name="Users", factory=UserService)

tasks_service_spec = Spec(
    name="Tasks",
    factory=TaskService,
    notification_service=notification_service_spec,
    user_service=user_service_spec,
)
