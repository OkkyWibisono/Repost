"""
Find post automation for X (Twitter).
Searches for a specific post by username and content snippet.
"""

import sys
import time
import random
import pyautogui
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from browser import DEFAULT_DEBUG_PORT, get_element_coordinates_node
from action.tab_switcher import get_all_tabs, switch_to_tab
from action.mouse.initial import human_move_with_overshoot
from action.typing.type import human_type
from action.pageload import wait_for_network_idle


# Search box element selector
SEARCH_BOX_SELECTOR = '[data-testid="SearchBox_Search_Input"]'


def find_x_tab(port: int = DEFAULT_DEBUG_PORT) -> str | None:
    """
    Find the X.com tab and return its ID.

    Args:
        port: CDP debug port

    Returns:
        Tab ID if found, None otherwise
    """
    tabs = get_all_tabs(port=port)

    for tab in tabs:
        url = tab.get("url", "")
        # Check if it's an X.com tab (x.com or x.com/home)
        if "x.com" in url or "twitter.com" in url:
            print(f"Found X tab: {url}")
            return tab.get("id")

    print("No X.com tab found")
    return None


def switch_to_x_tab(port: int = DEFAULT_DEBUG_PORT) -> bool:
    """
    Switch to the X.com tab.

    Args:
        port: CDP debug port

    Returns:
        True if switched successfully, False otherwise
    """
    tab_id = find_x_tab(port=port)

    if tab_id is None:
        return False

    return switch_to_tab(tab_id, port=port)


def click_search_box(port: int = DEFAULT_DEBUG_PORT) -> bool:
    """
    Find and click the search box element.

    Args:
        port: CDP debug port

    Returns:
        True if clicked successfully, False otherwise
    """
    print("Looking for search box...")

    coords = get_element_coordinates_node(
        selector=SEARCH_BOX_SELECTOR,
        port=port
    )

    if coords is None:
        print("Could not find search box")
        return False

    target_x, target_y = coords

    # Randomize click position within the search box
    offset_x = random.randint(-50, 50)
    offset_y = random.randint(-5, 5)
    final_x = target_x + offset_x
    final_y = target_y + offset_y

    print(f"Found search box at ({target_x}, {target_y})")
    print(f"Randomized click position: ({final_x}, {final_y})")

    # Move mouse with human-like movement
    print("Moving mouse to search box...")
    human_move_with_overshoot(final_x, final_y, overshoot_chance=0.25)

    # Small pause before clicking
    time.sleep(0.1 + 0.2 * random.random())

    # Click the search box
    print("Clicking search box...")
    pyautogui.click()

    # Wait for search box to be focused
    time.sleep(0.3 + 0.2 * random.random())

    return True


def findpost(username: str, post: str, **params) -> bool:
    """
    Find a post by searching for username and post content.

    Flow:
    1. Switch to X.com tab
    2. Click the search box
    3. Type search query: from:{username} "{post}"
    4. Press Enter to search

    Args:
        username: X/Twitter username (without @)
        post: First 16 characters of the post content

    Returns:
        True if search executed successfully, False otherwise
    """
    print("=" * 50)
    print("Find Post Automation")
    print("=" * 50)
    print(f"Username: {username}")
    print(f"Post snippet: {post}")
    print("-" * 50)

    # Step 1: Switch to X.com tab
    print("\nStep 1: Switching to X.com tab...")
    if not switch_to_x_tab(port=DEFAULT_DEBUG_PORT):
        print("Failed to switch to X.com tab")
        return False

    print("Switched to X.com tab")

    # Wait for tab to be active
    time.sleep(0.5 + 0.3 * random.random())

    # Step 2: Click the search box
    print("\nStep 2: Clicking search box...")
    if not click_search_box(port=DEFAULT_DEBUG_PORT):
        print("Failed to click search box")
        return False

    print("Search box clicked")

    # Wait for search box to be ready
    time.sleep(0.3 + 0.2 * random.random())

    # Step 3: Type the search query
    print("\nStep 3: Typing search query...")

    # Build search query: from:{username} "{post}"
    search_query = f'from:{username} "{post}"'
    print(f"Query: {search_query}")

    # Type with human-like delays (0.25-0.6s per character)
    human_type(search_query, min_delay=0.25, max_delay=0.6)

    # Small pause after typing
    time.sleep(0.5 + 0.3 * random.random())

    # Step 4: Press Enter to search
    print("\nStep 4: Pressing Enter to search...")
    pyautogui.press('enter')

    print("\nSearch initiated!")
    print("=" * 50)

    # Wait for search results to load
    print("\nWaiting for search results...")
    if wait_for_network_idle():
        print("Search results loaded")
    else:
        print("Search results load timeout, continuing anyway...")

    return True


if __name__ == "__main__":
    # Test with example parameters
    print("Testing findpost automation...")
    print("Starting in 3 seconds...")
    time.sleep(3)

    # Example: Search for a post
    result = findpost(
        username="elonmusk",
        post="Who's building ov"  # First 16 chars
    )

    if result:
        print("\n✓ Find post automation completed successfully")
    else:
        print("\n✗ Find post automation failed")
