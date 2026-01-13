"""
Celery configuration for Medusa agent.
Connects to central Redis broker for task distribution.
"""

from celery import Celery
from pathlib import Path
import json

# Load config to get Redis connection details
CONFIG_FILE = Path(__file__).parent / "config.json"


def load_config() -> dict:
    """Load configuration from config.json."""
    if not CONFIG_FILE.exists():
        return {}

    with open(CONFIG_FILE, "r") as f:
        return json.load(f)


def get_redis_url() -> str:
    """
    Get Redis URL from config.json.

    Expected config format:
    {
        "redis": {
            "host": "localhost",
            "port": 6379,
            "db": 0,
            "password": null
        }
    }

    Returns:
        Redis connection URL
    """
    config = load_config()
    redis_config = config.get("redis", {})

    host = redis_config.get("host", "localhost")
    port = redis_config.get("port", 6379)
    db = redis_config.get("db", 0)
    password = redis_config.get("password")

    if password:
        return f"redis://:{password}@{host}:{port}/{db}"
    else:
        return f"redis://{host}:{port}/{db}"


def get_agent_id() -> str:
    """Get agent_id from config.json."""
    config = load_config()
    return config.get("agent_id", "unknown")


# Create Celery app
app = Celery(
    "medusa",
    broker=get_redis_url(),
    backend=get_redis_url(),
    include=["celery_tasks"]
)

# Celery configuration
app.conf.update(
    # Task execution settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Task result settings
    result_expires=3600,  # Results expire after 1 hour
    result_backend_transport_options={"master_name": "mymaster"},

    # Worker settings
    worker_prefetch_multiplier=1,  # Only fetch one task at a time
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks

    # Task routing (route tasks to specific agent queues)
    task_default_queue=f"medusa.{get_agent_id()}",
    task_default_exchange=f"medusa.{get_agent_id()}",
    task_default_routing_key=f"medusa.{get_agent_id()}",

    # Task execution options
    task_acks_late=True,  # Acknowledge task after completion
    task_reject_on_worker_lost=True,  # Reject task if worker dies

    # Time limits
    task_soft_time_limit=300,  # 5 minutes soft limit
    task_time_limit=600,  # 10 minutes hard limit
)


if __name__ == "__main__":
    # Test configuration
    print("Celery Configuration:")
    print(f"Broker: {app.conf.broker_url}")
    print(f"Backend: {app.conf.result_backend}")
    print(f"Agent ID: {get_agent_id()}")
    print(f"Default Queue: {app.conf.task_default_queue}")
