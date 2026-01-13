"""
Tab switching utilities for browser control.
Provides functions to create new tabs and switch between them using CDP.
"""

import json
import time
import urllib.request
from typing import Optional, List
from websocket import create_connection


DEFAULT_DEBUG_PORT = 9222


def get_cdp_websocket_url(port: int = DEFAULT_DEBUG_PORT, tab_index: int = 0) -> Optional[str]:
    """
    Get the WebSocket URL for a specific tab.

    Args:
        port: CDP debug port
        tab_index: Index of the tab (0 = first tab)

    Returns:
        WebSocket URL or None if not found
    """
    try:
        with urllib.request.urlopen(f"http://localhost:{port}/json") as response:
            tabs = json.loads(response.read().decode())
            if tabs and len(tabs) > tab_index:
                return tabs[tab_index].get("webSocketDebuggerUrl")
    except Exception as e:
        print(f"Error getting WebSocket URL: {e}")
        return None
    return None


def get_all_tabs(port: int = DEFAULT_DEBUG_PORT) -> List[dict]:
    """
    Get all open tabs.

    Args:
        port: CDP debug port

    Returns:
        List of tab information dictionaries
    """
    try:
        with urllib.request.urlopen(f"http://localhost:{port}/json") as response:
            tabs = json.loads(response.read().decode())
            return tabs
    except Exception as e:
        print(f"Error getting tabs: {e}")
        return []


def create_new_tab(port: int = DEFAULT_DEBUG_PORT, url: str = "about:blank") -> Optional[dict]:
    """
    Create a new tab in the browser.

    Args:
        port: CDP debug port
        url: URL to open in the new tab (default: about:blank)

    Returns:
        Tab information dictionary or None if failed
    """
    try:
        # Use CDP HTTP API to create new tab
        req = urllib.request.Request(
            f"http://localhost:{port}/json/new?{url}",
            method='PUT'
        )
        with urllib.request.urlopen(req) as response:
            tab_info = json.loads(response.read().decode())
            print(f"Created new tab: {tab_info.get('id', 'unknown')}")
            return tab_info
    except Exception as e:
        print(f"Error creating new tab: {e}")
        return None


def switch_to_tab(tab_id: str, port: int = DEFAULT_DEBUG_PORT) -> bool:
    """
    Switch focus to a specific tab.

    Args:
        tab_id: The tab ID to switch to
        port: CDP debug port

    Returns:
        True if successful, False otherwise
    """
    try:
        # Activate the tab using CDP HTTP API
        req = urllib.request.Request(
            f"http://localhost:{port}/json/activate/{tab_id}",
            method='PUT'
        )
        with urllib.request.urlopen(req) as response:
            result = response.read().decode()
            print(f"Switched to tab: {tab_id}")
            return True
    except Exception as e:
        print(f"Error switching to tab: {e}")
        return False


def create_and_switch_to_new_tab(port: int = DEFAULT_DEBUG_PORT, url: str = "about:blank") -> bool:
    """
    Create a new tab and immediately switch focus to it.

    Args:
        port: CDP debug port
        url: URL to open in the new tab

    Returns:
        True if successful, False otherwise
    """
    print("Creating new tab...")
    tab_info = create_new_tab(port=port, url=url)

    if tab_info is None:
        print("Failed to create new tab")
        return False

    # Small delay to ensure tab is ready
    time.sleep(0.3)

    tab_id = tab_info.get('id')
    if tab_id:
        print(f"Switching focus to new tab...")
        return switch_to_tab(tab_id, port=port)

    return False


def close_tab(tab_id: str, port: int = DEFAULT_DEBUG_PORT) -> bool:
    """
    Close a specific tab.

    Args:
        tab_id: The tab ID to close
        port: CDP debug port

    Returns:
        True if successful, False otherwise
    """
    try:
        req = urllib.request.Request(
            f"http://localhost:{port}/json/close/{tab_id}",
            method='PUT'
        )
        with urllib.request.urlopen(req) as response:
            result = response.read().decode()
            print(f"Closed tab: {tab_id}")
            return True
    except Exception as e:
        print(f"Error closing tab: {e}")
        return False


if __name__ == "__main__":
    # Test the tab switcher
    print("Testing tab switcher...")
    print(f"Current tabs: {len(get_all_tabs())}")

    # Create and switch to new tab
    if create_and_switch_to_new_tab(url="https://www.google.com"):
        print("Successfully created and switched to new tab")
    else:
        print("Failed to create/switch tab")

    time.sleep(2)
    print(f"Current tabs: {len(get_all_tabs())}")
