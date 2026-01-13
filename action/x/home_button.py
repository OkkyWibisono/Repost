"""
Home button click automation for X (Twitter).
Clicks the home button to navigate back to the home timeline.
"""

import sys
import time
import random
import pyautogui
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from browser import DEFAULT_DEBUG_PORT, get_element_coordinates_node
from action.mouse.initial import human_move_with_overshoot


# Home button selector
# Element: <a href="/home" aria-label="Home" role="link" data-testid="AppTabBar_Home_Link">
HOME_BUTTON_SELECTOR = 'a[data-testid="AppTabBar_Home_Link"]'


def click_home(port: int = DEFAULT_DEBUG_PORT) -> bool:
    """
    Find and click the home button.

    Args:
        port: CDP debug port

    Returns:
        True if clicked successfully, False otherwise
    """
    print("Looking for home button...")

    coords = get_element_coordinates_node(
        selector=HOME_BUTTON_SELECTOR,
        port=port
    )

    if coords is None:
        print("Could not find home button")
        return False

    target_x, target_y = coords

    # Randomize click position within the button
    offset_x = random.randint(-20, 20)
    offset_y = random.randint(-5, 5)
    final_x = target_x + offset_x
    final_y = target_y + offset_y

    print(f"Found home button at ({target_x}, {target_y})")
    print(f"Randomized click position: ({final_x}, {final_y})")

    # Move mouse with human-like movement
    print("Moving mouse to home button...")
    human_move_with_overshoot(final_x, final_y, overshoot_chance=0.25)

    # Small pause before clicking
    time.sleep(0.1 + 0.2 * random.random())

    # Click the home button
    print("Clicking home button...")
    pyautogui.click()

    # Wait for navigation
    time.sleep(0.5 + 0.3 * random.random())

    print("Home button clicked successfully")
    return True


if __name__ == "__main__":
    # Test the home button click
    print("Testing home button click...")
    print("Starting in 3 seconds...")
    time.sleep(3)

    if click_home():
        print("\n[OK] Home button clicked successfully")
    else:
        print("\n[FAIL] Failed to click home button")
