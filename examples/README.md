# Loomi Examples

This directory contains example applications built with Loomi to help you get started.

### Task Management System
An example showing how to build a task tracking application using Loomi's service and app architecture. 

It demonstrates:
- Service composition and dependencies
- Basic application implementation
- State management and tasks exceution

The example includes three loomi services and one app:
- `TaskService`: Manages task lifecycle
- `UserService`: Handles user workload tracking
- `NotificationService`: Handles system notifications
- `TaskManagementApp`: The main app that integrates the services to provide a cohesive task management experience

Check out `/examples/task_management` to see it in action.

## Running Examples

Each example can be run directly from its directory:
```bash
cd examples/task_management
python app.py
```