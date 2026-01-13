import json
import importlib
import os
import sys
import time
import urllib.request
from pathlib import Path
from action.tab_switcher import create_and_switch_to_new_tab
from action.x.login_detection import detect_login
from action.mouse.initial import random_idle_movement
from browser import launch_chrome, DEFAULT_DEBUG_PORT
from action.pageload import wait_for_network_idle

TASK_FILE = Path(__file__).parent / "task.json"
CONFIG_FILE = Path(__file__).parent / "config.json"
URL = "https://x.com"

VALID_PLATFORMS = ["x", "instagram", "tiktok"]
VALID_TASKS = [
    "login",
    "maintain",
    "search",
    "post",
    "comment",
    "reply",
    "likepost",
    "destroy",
    "logout",
    "navigate",
    "findpost",
]


def load_config() -> dict:
    """Load config.json file."""
    if not CONFIG_FILE.exists():
        print(f"Config file not found: {CONFIG_FILE}")
        return {}

    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)

    return config


def fetch_task_from_api() -> dict | None:
    """
    Fetch task from API endpoint.

    Returns:
        Task dictionary or None if no task available or error occurred
    """
    config = load_config()
    api_endpoint = config.get("api_endpoint")

    if not api_endpoint:
        print("No API endpoint configured in config.json")
        return None

    agent_id = config.get("agent_id", "unknown")

    try:
        # Construct the full URL with agent_id as query parameter
        url = f"{api_endpoint}/tasks?agent_id={agent_id}"

        req = urllib.request.Request(url)
        req.add_header('Content-Type', 'application/json')

        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())

                # API should return task object or None/empty
                if data and isinstance(data, dict):
                    print(f"Received task from API: {data.get('task', 'unknown')}")
                    return data
                else:
                    return None
            else:
                print(f"API returned status code: {response.status}")
                return None

    except urllib.error.HTTPError as e:
        if e.code == 404:
            # No task available - this is normal
            return None
        else:
            print(f"API HTTP error: {e.code} - {e.reason}")
            return None
    except urllib.error.URLError as e:
        print(f"API connection error: {e.reason}")
        return None
    except Exception as e:
        print(f"Error fetching task from API: {e}")
        return None


def load_task() -> dict | None:
    """Load task from task.json file."""
    if not TASK_FILE.exists():
        print(f"Task file not found: {TASK_FILE}")
        return None

    with open(TASK_FILE, "r") as f:
        task = json.load(f)

    return task


def validate_task(task: dict) -> bool:
    """Validate task structure."""
    if not task.get("enabled", False):
        print("Task is disabled")
        return False

    platform = task.get("platform")
    if platform not in VALID_PLATFORMS:
        print(f"Invalid platform: {platform}. Valid: {VALID_PLATFORMS}")
        return False

    task_name = task.get("task")
    if task_name not in VALID_TASKS:
        print(f"Invalid task: {task_name}. Valid: {VALID_TASKS}")
        return False

    return True


def execute_task(task: dict) -> bool:
    """
    Execute the task by loading the appropriate platform module.

    Returns:
        True if the task indicates to keep browser running, False otherwise
    """
    platform = task["platform"]
    task_name = task["task"]
    params = task.get("params", {})

    # Try task-specific module first (e.g., action.x.login)
    # Fall back to navigate module if not found
    module_paths = [
        f"action.{platform}.{task_name}",  # e.g., action.x.login
        f"action.{platform}.navigate",      # fallback
    ]

    module = None
    for module_path in module_paths:
        try:
            module = importlib.import_module(module_path)
            print(f"Loaded module: {module_path}")
            break
        except ModuleNotFoundError:
            continue

    if module is None:
        print(f"No module found for {platform}.{task_name}")
        return False

    try:
        if hasattr(module, task_name):
            func = getattr(module, task_name)
            print(f"Executing: {platform}.{task_name}")
            result = func(**params)

            # If the function returns True (e.g., successful login), keep browser running
            if result is True:
                return True

        else:
            print(f"Function '{task_name}' not found in module")

    except Exception as e:
        print(f"Error executing task: {e}")

    return False


def run() -> None:
    """Main run loop - detects login, executes login if needed, then polls for tasks from API."""
    print("=" * 50)
    print("MEDUSA Task Runner")
    print("=" * 50)

    # Step 1: Launch browser and navigate to X
    print("\nLaunching browser and navigating to X...")
    root_dir = Path(__file__).parent
    user_data_dir = str(root_dir / ".medusa_browser_data")
    launch_chrome(url=URL, profile="Default", user_data_dir=user_data_dir, debug_port=DEFAULT_DEBUG_PORT)

    # Wait for page to load
    print("Waiting for page to fully load...")
    if wait_for_network_idle():
        print("Page loaded successfully")
    else:
        print("Page load timeout, continuing anyway...")

    # Step 2: Detect login status
    print("\n" + "=" * 50)
    print("Detecting login status...")
    print("=" * 50)
    is_logged_in = detect_login(port=DEFAULT_DEBUG_PORT, update_config=True)

    if not is_logged_in:
        # Step 3a: Not logged in - execute login task
        print("\n" + "-" * 50)
        print("Not logged in. Executing login task...")
        print("-" * 50)

        task = load_task()
        if task is None:
            print("No task.json found. Cannot proceed with login.")
            return

        # Force task to be login
        task["platform"] = "x"
        task["task"] = "login"
        task["enabled"] = True

        if not validate_task(task):
            print("Login task validation failed.")
            return

        keep_running = execute_task(task)

        if not keep_running:
            print("Login failed or completed without success. Browser will close.")
            return

        print("\n" + "=" * 50)
        print("Login successful!")
        print("=" * 50)

    else:
        # Step 3b: Already logged in - do random mouse movement
        print("\n" + "=" * 50)
        print("Already logged in!")
        print("=" * 50)

        print("\nPerforming random mouse movement for 3 seconds...")
        random_idle_movement(duration=3.0)
        print("Mouse movement complete")

        # Create new tab and switch to it
        print("\nCreating new tab...")
        if create_and_switch_to_new_tab(url="about:blank"):
            print("Successfully created and switched to new tab")
            print("X tab remains open in background\n")
        else:
            print("Failed to create/switch tab\n")

    # Step 4: Enter polling loop
    print("\n" + "=" * 50)
    print("Entering task polling loop...")
    print("Browser will remain open")
    print("=" * 50 + "\n")

    # Task polling loop
    poll_interval = 5  # seconds between API polls
    idle_counter = 0
    idle_tab_created = is_logged_in  # Skip creating idle tab if already logged in (we already created one)

    while True:
        try:
            # Fetch task from API
            print(f"Polling API for tasks... (idle count: {idle_counter})")
            api_task = fetch_task_from_api()

            if api_task:
                # Task received from API
                print("\n" + "-" * 50)
                print(f"New task received: {api_task.get('task')}")
                print("-" * 50)

                if validate_task(api_task):
                    execute_task(api_task)
                    idle_counter = 0  # Reset idle counter after executing task
                else:
                    print("Invalid task received from API")

            else:
                # No task available
                idle_counter += 1
                print(f"No task available (idle: {idle_counter})")

                # After 2 seconds of no task, create new tab and switch to it (if not already created)
                if idle_counter == 1 and not idle_tab_created:  # First time no task
                    print("\nNo task for 2 seconds. Creating new tab...")
                    time.sleep(2)

                    if create_and_switch_to_new_tab(url="about:blank"):
                        print("Successfully created and switched to new tab")
                        print("Previous platform tab remains open\n")
                        idle_tab_created = True
                    else:
                        print("Failed to create/switch tab\n")

            # Wait before next poll
            time.sleep(poll_interval)

        except KeyboardInterrupt:
            print("\n\nTask polling interrupted by user")
            print("Browser will remain open")
            break
        except Exception as e:
            print(f"\nError in polling loop: {e}")
            print("Continuing to poll...")
            time.sleep(poll_interval)


def run_celery_worker() -> None:
    """
    Run Medusa as a Celery worker.
    Listens for tasks from central Redis broker instead of polling HTTP API.
    """
    print("=" * 50)
    print("MEDUSA Celery Worker Mode")
    print("=" * 50)

    # Step 1: Launch browser and navigate to X
    print("\nLaunching browser and navigating to X...")
    root_dir = Path(__file__).parent
    user_data_dir = str(root_dir / ".medusa_browser_data")
    launch_chrome(url=URL, profile="Default", user_data_dir=user_data_dir, debug_port=DEFAULT_DEBUG_PORT)

    # Wait for page to load
    print("Waiting for page to fully load...")
    if wait_for_network_idle():
        print("Page loaded successfully")
    else:
        print("Page load timeout, continuing anyway...")

    # Step 2: Detect login status
    print("\n" + "=" * 50)
    print("Detecting login status...")
    print("=" * 50)
    is_logged_in = detect_login(port=DEFAULT_DEBUG_PORT, update_config=True)

    if not is_logged_in:
        # Step 3a: Not logged in - execute login task
        print("\n" + "-" * 50)
        print("Not logged in. Executing login task...")
        print("-" * 50)

        task = load_task()
        if task is None:
            print("No task.json found. Cannot proceed with login.")
            return

        # Force task to be login
        task["platform"] = "x"
        task["task"] = "login"
        task["enabled"] = True

        if not validate_task(task):
            print("Login task validation failed.")
            return

        keep_running = execute_task(task)

        if not keep_running:
            print("Login failed or completed without success. Browser will close.")
            return

        print("\n" + "=" * 50)
        print("Login successful!")
        print("=" * 50)

    else:
        # Step 3b: Already logged in - do random mouse movement
        print("\n" + "=" * 50)
        print("Already logged in!")
        print("=" * 50)

        print("\nPerforming random mouse movement for 3 seconds...")
        random_idle_movement(duration=3.0)
        print("Mouse movement complete")

        # Create new tab and switch to it
        print("\nCreating new tab...")
        if create_and_switch_to_new_tab(url="about:blank"):
            print("Successfully created and switched to new tab")
            print("X tab remains open in background\n")
        else:
            print("Failed to create/switch tab\n")

    # Step 4: Start Celery worker
    print("\n" + "=" * 50)
    print("Starting Celery worker...")
    print("Listening for tasks from Redis broker")
    print("Browser will remain open")
    print("=" * 50 + "\n")

    # Import celery app and start worker
    try:
        from celery_config import app, get_agent_id
        from celery.bin import worker

        config = load_config()
        agent_id = config.get("agent_id", "unknown")
        queue_name = f"medusa.{agent_id}"

        print(f"Agent ID: {agent_id}")
        print(f"Queue: {queue_name}")
        print(f"Broker: {app.conf.broker_url}")
        print("\nPress Ctrl+C to stop worker\n")

        # Create and start worker
        worker_instance = worker.worker(app=app)
        worker_instance.run(
            loglevel="info",
            queues=[queue_name],
            concurrency=1,  # Process one task at a time
            pool="solo"  # Use solo pool for Windows compatibility
        )

    except KeyboardInterrupt:
        print("\n\nCelery worker stopped by user")
        print("Browser will remain open")
    except ImportError as e:
        print(f"\n\nError: Celery not properly installed: {e}")
        print("Run: pip install celery[redis]")
    except Exception as e:
        print(f"\n\nError starting Celery worker: {e}")
        import traceback
        traceback.print_exc()


def launch_in_new_window(mode: str = "polling"):
    """
    Relaunch main.py in a new terminal window.

    Args:
        mode: The mode to run in (polling or celery)
    """
    import subprocess

    script_dir = Path(__file__).resolve().parent
    venv_activate = script_dir / "venv" / "Scripts" / "activate.bat"
    mode_arg = "--celery" if mode == "celery" else "--polling"

    # Build command: activate venv, then run main.py
    if venv_activate.exists():
        cmd = f'start "Medusa" cmd /k "cd /d {script_dir} && {venv_activate} && python main.py {mode_arg}"'
    else:
        # Fallback if no venv
        cmd = f'start "Medusa" cmd /k "cd /d {script_dir} && python main.py {mode_arg}"'

    print(f"Launching in new window: {mode} mode")
    subprocess.Popen(cmd, shell=True)
    print("New window launched. You can close this terminal.")
    sys.exit(0)


if __name__ == "__main__":
    # Parse command line arguments
    mode = "polling"  # Default mode
    new_window = False

    args = [a.lower() for a in sys.argv[1:]]

    for arg in args:
        if arg in ["--celery", "-c", "celery"]:
            mode = "celery"
        elif arg in ["--polling", "-p", "polling"]:
            mode = "polling"
        elif arg in ["--new-window", "-w", "window"]:
            new_window = True
        elif arg in ["--help", "-h", "help"]:
            print("Medusa Task Runner")
            print("\nUsage:")
            print("  python main.py [options] [mode]")
            print("\nModes:")
            print("  --polling, -p    Run in HTTP API polling mode (default)")
            print("  --celery, -c     Run as Celery worker listening to Redis")
            print("\nOptions:")
            print("  --new-window, -w  Launch in a new terminal window")
            print("  --help, -h        Show this help message")
            print("\nExamples:")
            print("  python main.py --polling")
            print("  python main.py --celery")
            print("  python main.py -w              # polling in new window")
            print("  python main.py -w --celery     # celery in new window")
            sys.exit(0)
        else:
            print(f"Unknown argument: {arg}")
            print("Use --help for usage information")
            sys.exit(1)

    # Launch in new window if requested
    if new_window:
        launch_in_new_window(mode)

    # Run in selected mode
    if mode == "celery":
        run_celery_worker()
    else:
        run()
