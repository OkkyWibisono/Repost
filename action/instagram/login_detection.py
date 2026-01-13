"""
Instagram login detection via CDP cookies.
"""

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

# Instagram authentication cookies
AUTH_COOKIES = ["sessionid", "ds_user_id"]
URL = "https://instagram.com"


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

    cookies = await get_cookies_for_domain(ws_url, "instagram.com")
    return check_auth_cookies(cookies)


def detect_login(port: int = DEFAULT_DEBUG_PORT) -> bool:
    """
    Detect if user is logged into Instagram.

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


def check_login(port: int = DEFAULT_DEBUG_PORT) -> None:
    """Check login status and print result."""
    if detect_login(port):
        print("Logged In")
    else:
        print("Not Logged In")


if __name__ == "__main__":
    import time

    # Launch Chrome with debug port and navigate to Instagram
    print("Launching Chrome with CDP enabled...")
    process = launch_chrome(url=URL, debug_port=DEFAULT_DEBUG_PORT)

    # Wait for Chrome to start and page to load
    print("Waiting for page to load...")
    time.sleep(5)

    # Check login status
    check_login()
