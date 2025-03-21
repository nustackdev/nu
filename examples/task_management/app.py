import asyncio
from datetime import datetime
from pathlib import Path

from services import TaskService
from specs import state_spec, tasks_service_spec

from loomi import AsyncApp, UseModel, UseService, UseState
from loomi.logging import setup_logging
from loomistd.state import State

setup_logging(Path(".logs"), log_level=20)


class TaskManagementApp(AsyncApp):
    # Services
    task_service = UseService(TaskService)
    st: State = UseState(State)

    # State
    tasks = UseModel(st, dict[str, dict])

    async def initialize_users(self):
        """Initialize some users in the system"""
        for user_id in ["user1", "user2", "user3"]:
            await self.task_service.user_service.add_user(user_id)

    async def create_sample_tasks(self):
        """Create some sample tasks"""
        tasks = [
            ("TASK-1", "Implement new feature"),
            ("TASK-2", "Fix critical bug"),
            ("TASK-3", "Update documentation"),
        ]

        current_tasks = {}
        for task_id, description in tasks:
            if await self.task_service.create_task(task_id, description):
                current_tasks[task_id] = {
                    "description": description,
                    "created_at": datetime.now().isoformat(),
                    "status": "assigned",
                }

        # Store tasks in state
        await self.tasks.set(current_tasks)

    async def complete_random_task(self):
        """Complete a task to demonstrate workload updates"""
        current_tasks = await self.tasks.get() or {}
        if current_tasks:
            task_id = next(iter(current_tasks.keys()))
            await self.task_service.complete_task(task_id, "user1")

            # Update task state
            current_tasks[task_id]["status"] = "completed"
            await self.tasks.set(current_tasks)

    async def show_system_status(self):
        """Display current system status"""
        print("\nSystem Status:")
        print("-" * 50)

        # Show user workloads
        print("User Workloads:")
        for user_id in ["user1", "user2", "user3"]:
            workload = await self.task_service.user_service.get_user_workload(user_id)
            print(f"  {user_id}: {workload} tasks")

        # Show task status
        print("\nTask Status:")
        tasks = await self.tasks.get() or {}
        for task_id, task_info in tasks.items():
            print(f"  {task_id}: {task_info['status']} - {task_info['description']}")

    def demo_runner(self):
        """Run a demonstration of the task management system"""
        return self.sequence(
            self.function(self.initialize_users),
            self.function(self.create_sample_tasks),
            self.function(self.show_system_status),
            self.function(self.complete_random_task),
            self.function(self.show_system_status),
        )


async def main():
    async with TaskManagementApp(
        task_service_spec=tasks_service_spec,
        st_spec=state_spec,
    ) as app:
        await app.execute(app.demo_runner())


if __name__ == "__main__":
    asyncio.run(main())
