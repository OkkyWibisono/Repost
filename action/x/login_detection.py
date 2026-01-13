import sys
import json
import asyncio
from pathlib import Path

try:
    import websockets
except ImportError:
    print("Please install websockets: pip install websockets")
    sys.exit(1)

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from browser import launch_chrome, get_cdp_websocket_url, is_cdp_available, DEFAULT_DEBUG_PORT
from config import get_account, update_account_status

# X authentication cookies
AUTH_COOKIES = ["auth_token", "ct0"]
URL = "https://x.com"
PLATFORM = "x"


async def get_cookies_for_domain(ws_url: str, domain: str) -> list[dict]:
    """Get cookies for a specific domain via CDP WebSocket."""
    async with websockets.connect(ws_url) as ws:
        # Send CDP command to get cookies
        command = {
            "id": 1,
            "method": "Network.getCookies",
            "params": {"urls": [f"https://{domain}", f"https://www.{domain}"]}
        }
        await ws.send(json.dumps(command))

        response = await ws.recv()
        result = json.loads(response)

        if "result" in result and "cookies" in result["result"]:
            return result["result"]["cookies"]
        return []


def check_auth_cookies(cookies: list[dict]) -> bool:
    """Check if authentication cookies are present."""
    cookie_names = {cookie.get("name") for cookie in cookies}
    return any(auth_cookie in cookie_names for auth_cookie in AUTH_COOKIES)


async def detect_login_async(port: int = DEFAULT_DEBUG_PORT) -> bool:
    """Async login detection."""
    ws_url = get_cdp_websocket_url(port)
    if not ws_url:
        print("Could not get CDP WebSocket URL")
        return False

    cookies = await get_cookies_for_domain(ws_url, "x.com")
    return check_auth_cookies(cookies)


def get_config_status() -> str | None:
    """Get current login status from config.json."""
    account = get_account(PLATFORM)
    if account:
        return account.get("status")
    return None


def detect_login_cookies(port: int = DEFAULT_DEBUG_PORT) -> bool:
    """
    Detect login status via CDP cookies only.

    Args:
        port: CDP remote debugging port

    Returns:
        True if logged in, False otherwise
    """
    if not is_cdp_available(port):
        print(f"CDP not available on port {port}")
        print("Make sure Chrome is running with --remote-debugging-port flag")
        return False

    return asyncio.run(detect_login_async(port))


def detect_login(port: int = DEFAULT_DEBUG_PORT, update_config: bool = True) -> bool:
    """
    Detect if user is logged into X.

    Flow:
    1. Check config.json status first
    2. Check cookies via CDP
    3. If config is not_logged_in but cookies show logged_in, update config
    4. If status matches, don't update config

    Args:
        port: CDP remote debugging port
        update_config: Whether to update config.json if status changed

    Returns:
        True if logged in, False otherwise
    """
    # Step 1: Check config.json status
    config_status = get_config_status()
    print(f"Config status: {config_status or 'not set'}")

    # Step 2: Check cookies via CDP
    cookies_logged_in = detect_login_cookies(port)
    print(f"Cookies status: {'logged_in' if cookies_logged_in else 'not_logged_in'}")

    # Step 3: Compare and update if needed
    if update_config:
        if config_status == "not_logged_in" and cookies_logged_in:
            # Config says not logged in, but cookies show logged in - update config
            print("Status changed: not_logged_in -> logged_in")
            update_account_status(PLATFORM, "logged_in")
        elif config_status == "logged_in" and not cookies_logged_in:
            # Config says logged in, but cookies show not logged in - update config
            print("Status changed: logged_in -> not_logged_in")
            update_account_status(PLATFORM, "not_logged_in")
        elif config_status is None or config_status == "":
            # No status set, set it based on cookies
            new_status = "logged_in" if cookies_logged_in else "not_logged_in"
            print(f"Setting initial status: {new_status}")
            update_account_status(PLATFORM, new_status)
        else:
            # Status matches, no update needed
            print("Status unchanged")

    return cookies_logged_in


def check_login(port: int = DEFAULT_DEBUG_PORT) -> None:
    """Check login status and print result."""
    if detect_login(port):
        print("Logged In")
    else:
        print("Not Logged In")


def launch_and_check(init_mouse: bool = True) -> bool:
    """
    Launch browser, initialize mouse, and check login status.

    Args:
        init_mouse: Whether to initialize mouse movement

    Returns:
        True if logged in, False otherwise
    """
    import time
    from action.mouse.initial import initialize as mouse_init

    # Launch Chrome with debug port and navigate to X
    print("Launching Chrome with CDP enabled...")
    launch_chrome(url=URL, debug_port=DEFAULT_DEBUG_PORT)

    # Wait for Chrome to start and page to load
    print("Waiting for page to load...")
    time.sleep(4)

    # Initialize mouse with human-like movement
    if init_mouse:
        mouse_init()

    # Check login status
    is_logged_in = detect_login()
    if is_logged_in:
        print("Logged In")
    else:
        print("Not Logged In")

    return is_logged_in


if __name__ == "__main__":
    launch_and_check()
