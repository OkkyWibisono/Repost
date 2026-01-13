"""
Celery tasks for Medusa agent.
Tasks that can be called remotely from the central application.
"""

from celery import Task
from celery_config import app
import importlib
from typing import Optional


# Import existing task validation and execution logic from main
from main import VALID_PLATFORMS, VALID_TASKS, validate_task, execute_task


class MedusaTask(Task):
    """Base task class with error handling."""

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Log task failure."""
        print(f"Task {task_id} failed: {exc}")
        super().on_failure(exc, task_id, args, kwargs, einfo)

    def on_success(self, retval, task_id, args, kwargs):
        """Log task success."""
        print(f"Task {task_id} succeeded with result: {retval}")
        super().on_success(retval, task_id, args, kwargs)


@app.task(base=MedusaTask, bind=True, name="medusa.execute_task")
def execute_medusa_task(self, platform: str, task: str, params: dict = None) -> dict:
    """
    Execute a Medusa task remotely via Celery.

    Args:
        platform: Platform name (e.g., "x", "instagram")
        task: Task name (e.g., "login", "post", "like")
        params: Task parameters (optional)

    Returns:
        dict with status and message:
        {
            "success": bool,
            "message": str,
            "task_id": str,
            "platform": str,
            "task": str
        }
    """
    if params is None:
        params = {}

    print("=" * 50)
    print(f"Received Celery task: {platform}.{task}")
    print(f"Task ID: {self.request.id}")
    print(f"Params: {params}")
    print("=" * 50)

    # Build task dict
    task_dict = {
        "platform": platform,
        "task": task,
        "enabled": True,
        "params": params
    }

    # Validate task
    if not validate_task(task_dict):
        return {
            "success": False,
            "message": f"Invalid task: {platform}.{task}",
            "task_id": self.request.id,
            "platform": platform,
            "task": task
        }

    # Execute task
    try:
        result = execute_task(task_dict)
        return {
            "success": result,
            "message": f"Task {platform}.{task} executed successfully" if result else f"Task {platform}.{task} failed",
            "task_id": self.request.id,
            "platform": platform,
            "task": task
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Task execution error: {str(e)}",
            "task_id": self.request.id,
            "platform": platform,
            "task": task
        }


@app.task(base=MedusaTask, bind=True, name="medusa.health_check")
def health_check(self) -> dict:
    """
    Health check task to verify agent is responsive.

    Returns:
        dict with agent status
    """
    from config import load_config
    config = load_config()

    return {
        "status": "healthy",
        "agent_id": config.get("agent_id", "unknown"),
        "task_id": self.request.id
    }


@app.task(base=MedusaTask, bind=True, name="medusa.check_login_status")
def check_login_status(self, platform: str = "x") -> dict:
    """
    Check login status for a platform.

    Args:
        platform: Platform name (default: "x")

    Returns:
        dict with login status
    """
    from config import get_account

    account = get_account(platform)

    if not account:
        return {
            "success": False,
            "message": f"No account configured for platform: {platform}",
            "platform": platform,
            "status": None
        }

    return {
        "success": True,
        "message": f"Login status for {platform}",
        "platform": platform,
        "status": account.get("status"),
        "last_active": account.get("last_active")
    }


@app.task(base=MedusaTask, bind=True, name="medusa.update_config")
def update_config(self, updates: dict) -> dict:
    """
    Update agent configuration remotely.

    Args:
        updates: Dictionary of config updates to apply

    Returns:
        dict with update status

    Example:
        updates = {
            "api_endpoint": "https://new-api.example.com",
            "accounts.twitter.username": "newuser"
        }
    """
    from config import load_config, save_config

    try:
        config = load_config()

        # Apply updates (supports nested keys with dot notation)
        for key, value in updates.items():
            if "." in key:
                # Handle nested keys like "accounts.twitter.username"
                keys = key.split(".")
                current = config
                for k in keys[:-1]:
                    if k not in current:
                        current[k] = {}
                    current = current[k]
                current[keys[-1]] = value
            else:
                config[key] = value

        save_config(config)

        return {
            "success": True,
            "message": "Configuration updated successfully",
            "updates": updates
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to update config: {str(e)}",
            "updates": updates
        }


# Register tasks for auto-discovery
__all__ = [
    "execute_medusa_task",
    "health_check",
    "check_login_status",
    "update_config"
]
