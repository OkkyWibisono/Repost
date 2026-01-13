import sys
import time
import random
import json
import pyautogui
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from browser import launch_chrome, DEFAULT_DEBUG_PORT, get_cdp_session, get_element_coordinates_node
from action.mouse.initial import initialize as mouse_init, human_move_with_overshoot, random_idle_movement
from action.tiktok.login_detection import detect_login
from action.pageload import wait_for_network_idle

URL = "https://www.tiktok.com/login"
# Note: TikTok selectors are dynamic and may change. 
# These are best-effort selectors based on common structures.

def login(**params) -> bool:
    """
    TikTok login flow:
    1. Open browser
    2. Navigate to tiktok.com/login
    3. Initial mouse movement
    4. Check login status
    5. Perform login steps (Phone/Email/Username flow)
    
    Returns:
        True if logged in, False otherwise
    """
    print("=" * 50)
    print("TikTok Login Flow")
    print("=" * 50)
    print("Opening browser and navigating to tiktok.com/login...")
    
    root_dir = Path(__file__).parent.parent.parent
    user_data_dir = str(root_dir / ".medusa_browser_data")
    launch_chrome(url=URL, profile="Default", user_data_dir=user_data_dir, debug_port=DEFAULT_DEBUG_PORT)

    print("Waiting for page to fully load...")
    if wait_for_network_idle():
        print("Page loaded successfully")
    else:
        print("Page load timeout, continuing anyway...")

    print("-" * 50)
    mouse_init()

    print("-" * 50)
    print("Checking login status...")
    is_logged_in = detect_login()

    print("=" * 50)
    if is_logged_in:
        print("Logged In")
        print("=" * 50)
        return True

    print("Not Logged In - Attempting login flow...")
    print("-" * 50)

    # Note: TikTok's login flow varies significantly (QR code, Phone, Email/Username).
    # We will attempt to select "Use phone / email / username" and then "Log in with email or username".
    
    # Selector for "Use phone / email / username" link/button
    # Usually the first option in the list
    params = params or {}
    
    # Attempt to find the "Use phone / email / username" option
    # Generic text search or specific class structures might be needed
    print("Please manually interact with the login page if automation fails.")
    print("TikTok login has high bot detection resilience.")
    
    # For now, we wait for manual login or user to implement specific selectors
    # as TikTok requires solving CAPTCHAs which cannot be easily automated.
    
    # We will poll for login status for a while
    max_retries = 60  # Wait up to 60 seconds for manual login
    print(f"Waiting up to {max_retries} seconds for login to complete...")
    
    for i in range(max_retries):
        if detect_login(update_config=False):
            print("\nLogin detected!")
            detect_login(update_config=True) # Update config now
            return True
        
        time.sleep(1)
        if i % 5 == 0:
            print(f"Waiting... ({i}/{max_retries})")

    print("\nLogin timeout or failed.")
    return False

if __name__ == "__main__":
    login()
