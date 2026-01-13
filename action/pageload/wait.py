"""
Page load waiting utilities using CDP network idle detection.
"""

import json
import time
import threading
from dataclasses import dataclass
from websocket import create_connection, WebSocketTimeoutException

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from browser import get_cdp_websocket_url, DEFAULT_DEBUG_PORT


@dataclass
class PageLoadConfig:
    """
    Configuration for page load waiting.
    Other modules can modify these values to customize timeout behavior.
    """
    timeout: float = 30.0  # Maximum time to wait for page load (seconds)
    idle_time: float = 0.5  # Time with no network activity to consider idle (seconds)
    poll_interval: float = 0.1  # Interval to check network status (seconds)


# Global config instance that other files can import and modify
config = PageLoadConfig()


def wait_for_network_idle(
    timeout: float = None,
    idle_time: float = None,
    port: int = DEFAULT_DEBUG_PORT
) -> bool:
    """
    Wait until the page is fully loaded by detecting network idle via CDP.

    Network idle is detected when there are no pending network requests
    for a specified duration.

    Args:
        timeout: Maximum wait time in seconds. Uses config.timeout if None.
        idle_time: Time with no network activity to consider idle. Uses config.idle_time if None.
        port: CDP debug port.

    Returns:
        True if network became idle, False if timeout occurred.
    """
    timeout = timeout if timeout is not None else config.timeout
    idle_time = idle_time if idle_time is not None else config.idle_time

    ws_url = get_cdp_websocket_url(port)
    if not ws_url:
        print("Could not get CDP WebSocket URL. Is Chrome running with --remote-debugging-port?")
        return False

    try:
        ws = create_connection(ws_url, timeout=timeout)
    except Exception as e:
        print(f"Failed to connect to CDP WebSocket: {e}")
        return False

    pending_requests = set()
    last_activity_time = time.time()
    message_id = 0
    result = {"idle": False, "error": None}
    stop_event = threading.Event()

    def send_command(method: str, params: dict = None) -> int:
        nonlocal message_id
        message_id += 1
        msg = {"id": message_id, "method": method}
        if params:
            msg["params"] = params
        ws.send(json.dumps(msg))
        return message_id

    def receive_messages():
        nonlocal last_activity_time
        while not stop_event.is_set():
            try:
                ws.settimeout(config.poll_interval)
                response = ws.recv()
                data = json.loads(response)

                method = data.get("method", "")
                params = data.get("params", {})

                if method == "Network.requestWillBeSent":
                    request_id = params.get("requestId")
                    if request_id:
                        pending_requests.add(request_id)
                        last_activity_time = time.time()

                elif method in ("Network.loadingFinished", "Network.loadingFailed"):
                    request_id = params.get("requestId")
                    if request_id:
                        pending_requests.discard(request_id)
                        last_activity_time = time.time()

                elif method == "Page.loadEventFired":
                    last_activity_time = time.time()

            except WebSocketTimeoutException:
                continue
            except Exception as e:
                if not stop_event.is_set():
                    result["error"] = str(e)
                break

    try:
        # Enable Network and Page domains
        send_command("Network.enable")
        send_command("Page.enable")

        # Start receiving messages in background
        receiver_thread = threading.Thread(target=receive_messages, daemon=True)
        receiver_thread.start()

        start_time = time.time()

        while True:
            elapsed = time.time() - start_time
            if elapsed >= timeout:
                print(f"Timeout waiting for network idle after {timeout}s")
                break

            time_since_activity = time.time() - last_activity_time
            if len(pending_requests) == 0 and time_since_activity >= idle_time:
                result["idle"] = True
                break

            time.sleep(config.poll_interval)

        stop_event.set()

    finally:
        try:
            send_command("Network.disable")
            send_command("Page.disable")
        except:
            pass
        ws.close()

    if result["error"]:
        print(f"Error during network idle wait: {result['error']}")
        return False

    return result["idle"]


def wait_for_page_load(
    timeout: float = None,
    port: int = DEFAULT_DEBUG_PORT
) -> bool:
    """
    Wait for the page load event via CDP.

    This waits for the Page.loadEventFired event, which fires when
    the load event is dispatched.

    Args:
        timeout: Maximum wait time in seconds. Uses config.timeout if None.
        port: CDP debug port.

    Returns:
        True if load event fired, False if timeout occurred.
    """
    timeout = timeout if timeout is not None else config.timeout

    ws_url = get_cdp_websocket_url(port)
    if not ws_url:
        print("Could not get CDP WebSocket URL. Is Chrome running with --remote-debugging-port?")
        return False

    try:
        ws = create_connection(ws_url, timeout=timeout)
    except Exception as e:
        print(f"Failed to connect to CDP WebSocket: {e}")
        return False

    message_id = 0

    def send_command(method: str, params: dict = None) -> int:
        nonlocal message_id
        message_id += 1
        msg = {"id": message_id, "method": method}
        if params:
            msg["params"] = params
        ws.send(json.dumps(msg))
        return message_id

    try:
        send_command("Page.enable")

        start_time = time.time()
        while True:
            elapsed = time.time() - start_time
            if elapsed >= timeout:
                print(f"Timeout waiting for page load after {timeout}s")
                return False

            try:
                ws.settimeout(config.poll_interval)
                response = ws.recv()
                data = json.loads(response)

                if data.get("method") == "Page.loadEventFired":
                    return True

            except WebSocketTimeoutException:
                continue
            except Exception as e:
                print(f"Error waiting for page load: {e}")
                return False

    finally:
        try:
            send_command("Page.disable")
        except:
            pass
        ws.close()


def set_timeout(timeout: float) -> None:
    """
    Set the global page load timeout.

    Args:
        timeout: Timeout in seconds.
    """
    config.timeout = timeout


def set_idle_time(idle_time: float) -> None:
    """
    Set the network idle detection time.

    Args:
        idle_time: Time in seconds with no network activity to consider idle.
    """
    config.idle_time = idle_time
