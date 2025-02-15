from loomi import AsyncService, Attach


class NotificationService(AsyncService):
    """Handles notifications for task updates"""

    async def notify_task_assignment(self, task_id: str, user_id: str):
        print(f"Notification: Task {task_id} assigned to user {user_id}")

    async def notify_task_completion(self, task_id: str):
        print(f"Notification: Task {task_id} has been completed")

    async def post_initialize(self):
        print("Notification service initialized")


class UserService(AsyncService):
    """Manages user operations and workload tracking"""

    _user_workloads: dict[str, int] = {}

    async def add_user(self, user_id: str) -> None:
        self._user_workloads[user_id] = 0
        print(f"User {user_id} added to the system")

    async def get_user_workload(self, user_id: str) -> int:
        return self._user_workloads.get(user_id, 0)

    async def update_user_workload(self, user_id: str, delta: int) -> None:
        current = await self.get_user_workload(user_id)
        self._user_workloads[user_id] = max(0, current + delta)

    async def get_least_loaded_user(self) -> str | None:
        if not self._user_workloads:
            return None
        return min(self._user_workloads.items(), key=lambda x: x[1])[0]


class TaskService(AsyncService):
    """Manages task operations with user assignment and notifications"""

    notification_service = Attach(NotificationService)
    user_service = Attach(UserService)

    async def create_task(self, task_id: str, description: str) -> bool:
        # Auto-assign to least loaded user
        user_id = await self.user_service.get_least_loaded_user()
        if not user_id:
            print(f"Cannot create task {task_id}: No users available")
            return False

        await self.user_service.update_user_workload(user_id, 1)
        await self.notification_service.notify_task_assignment(task_id, user_id)
        print(f"Task {task_id} created: {description}")
        return True

    async def complete_task(self, task_id: str, user_id: str) -> None:
        await self.user_service.update_user_workload(user_id, -1)
        await self.notification_service.notify_task_completion(task_id)
        print(f"Task {task_id} completed by user {user_id}")

    async def post_initialize(self) -> None:
        print("Task service initialized")
