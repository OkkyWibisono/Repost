import sys
import time
import random
import json
import pyautogui
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from browser import launch_chrome, DEFAULT_DEBUG_PORT, get_cdp_session, get_element_coordinates_node
from action.mouse.initial import initialize as mouse_init, human_move_with_overshoot, random_idle_movement
from action.x.login_detection import detect_login
from action.pageload import wait_for_network_idle

URL = "https://x.com"
SIGN_IN_BUTTON_TESTID = "loginButton"


def login(**params) -> bool:
    """
    X login flow:
    1. Open browser
    2. Navigate to x.com
    3. Initial mouse movement
    4. Check login status (also updates config.json if status changed)
    5. Print result

    Returns:
        True if logged in, False otherwise
    """
    # Step 1 & 2: Open browser and navigate to x.com
    print("=" * 50)
    print("X Login Flow")
    print("=" * 50)
    print("Opening browser and navigating to x.com...")
    # Use a separate user data directory to avoid conflicts with main Chrome instance
    root_dir = Path(__file__).parent.parent.parent
    user_data_dir = str(root_dir / ".medusa_browser_data")
    launch_chrome(url=URL, profile="Default", user_data_dir=user_data_dir, debug_port=DEFAULT_DEBUG_PORT)

    # Wait for page to load using CDP network idle detection
    print("Waiting for page to fully load...")
    if wait_for_network_idle():
        print("Page loaded successfully")
    else:
        print("Page load timeout, continuing anyway...")

    # Step 3: Initial mouse movement
    print("-" * 50)
    mouse_init()

    # Step 4: Check login status (updates config.json if status changed)
    print("-" * 50)
    print("Checking login status...")
    is_logged_in = detect_login()

    # Step 5: Handle login status
    print("=" * 50)
    if is_logged_in:
        print("Logged In")
        print("=" * 50)
        return True

    # Not logged in - click the Sign In button
    print("Not Logged In - Looking for Sign In button...")
    print("-" * 50)

    coords = get_element_coordinates_node(selector=f'[data-testid="{SIGN_IN_BUTTON_TESTID}"]', port=DEFAULT_DEBUG_PORT)

    if coords is None:
        print("Could not find Sign In button")
        print("=" * 50)
        return False

    target_x, target_y = coords

    # Randomize click position within button area
    offset_x = random.randint(-40, 40)
    offset_y = random.randint(-10, 10)
    final_x = target_x + offset_x
    final_y = target_y + offset_y

    print(f"Found Sign In button at ({target_x}, {target_y})")
    print(f"Randomized click position: ({final_x}, {final_y})")

    # Move mouse to Sign In button with human-like movement
    print("Moving mouse to Sign In button...")
    human_move_with_overshoot(final_x, final_y, overshoot_chance=0.25)

    # Small pause before clicking (human-like)
    time.sleep(0.1 + 0.2 * random.random())

    # Click the button
    print("Clicking Sign In button...")
    pyautogui.click()

    print("=" * 50)
    print("Clicked Sign In button - waiting for login page...")
    print("=" * 50)

    # Wait for login page to load
    # Wait for login page to load
    wait_for_network_idle()

    # Step 6: Enter username
    print("-" * 50)
    print("Looking for username input...")
    
    # Use the robust selector provided by user context
    USERNAME_INPUT_SELECTOR = 'input[autocomplete="username"]'
    
    username_coords = get_element_coordinates_node(selector=USERNAME_INPUT_SELECTOR, port=DEFAULT_DEBUG_PORT)
    
    if username_coords is None:
        print("Could not find username input")
        return False
        
    target_x, target_y = username_coords

    # Randomize click position within input area
    offset_x = random.randint(-40, 40)
    offset_y = random.randint(-8, 8)
    final_x = target_x + offset_x
    final_y = target_y + offset_y

    print(f"Found username input at ({target_x}, {target_y})")
    print(f"Randomized click position: ({final_x}, {final_y})")

    print("Moving mouse to username input...")
    human_move_with_overshoot(final_x, final_y, overshoot_chance=0.25)
    
    time.sleep(0.1 + 0.2 * random.random())
    
    print("Clicking username input...")
    pyautogui.click()

    print("Waiting 1.5 seconds...")
    time.sleep(1.5)

    # Step 7: Type username
    print("\n" + "-" * 50)
    print("Typing username...")

    # Read config to get username
    config_path = root_dir / "config.json"
    with open(config_path, 'r') as f:
        config = json.load(f)

    username = config['accounts']['twitter']['username']
    print(f"Username: {username}")

    # Type username with human-like delays
    for char in username:
        pyautogui.write(char)
        time.sleep(0.05 + 0.1 * random.random())

    print("Username typed successfully")

    # Dismiss autofill suggestions by pressing Escape
    time.sleep(0.3)
    pyautogui.press('escape')
    print("Dismissed autofill suggestions")

    time.sleep(0.5 + 0.5 * random.random())

    # Step 8: Click Next button
    print("\n" + "-" * 50)
    print("Looking for Next button...")

    # Use a selector for the Next button - it's the button immediately after the username input container
    NEXT_BUTTON_SELECTOR = '.r-1mmae3n + button'

    next_coords = get_element_coordinates_node(selector=NEXT_BUTTON_SELECTOR, port=DEFAULT_DEBUG_PORT)

    if next_coords is None:
        print("Could not find Next button")
        return False

    target_x, target_y = next_coords

    # Randomize click position within button area
    # Offset by ±40px horizontally and ±10px vertically from center
    offset_x = random.randint(-40, 40)
    offset_y = random.randint(-10, 10)
    final_x = target_x + offset_x
    final_y = target_y + offset_y

    print(f"Found Next button at ({target_x}, {target_y})")
    print(f"Randomized click position: ({final_x}, {final_y})")

    print("Moving mouse to Next button...")
    human_move_with_overshoot(final_x, final_y, overshoot_chance=0.25)

    time.sleep(0.1 + 0.2 * random.random())

    print("Clicking Next button...")
    pyautogui.click()

    print("==" * 25)
    print("Clicked Next button - waiting for password page...")
    print("==" * 25)

    # Wait for password page to load
    wait_for_network_idle()

    # Step 9: Enter password
    print("\n" + "-" * 50)
    print("Looking for password input...")

    PASSWORD_INPUT_SELECTOR = 'input[autocomplete="current-password"]'

    password_coords = get_element_coordinates_node(selector=PASSWORD_INPUT_SELECTOR, port=DEFAULT_DEBUG_PORT)

    if password_coords is None:
        print("Could not find password input")
        return False

    target_x, target_y = password_coords

    # Randomize click position within input area
    offset_x = random.randint(-40, 40)
    offset_y = random.randint(-8, 8)
    final_x = target_x + offset_x
    final_y = target_y + offset_y

    print(f"Found password input at ({target_x}, {target_y})")
    print(f"Randomized click position: ({final_x}, {final_y})")

    print("Moving mouse to password input...")
    human_move_with_overshoot(final_x, final_y, overshoot_chance=0.25)

    time.sleep(0.1 + 0.2 * random.random())

    print("Clicking password input...")
    pyautogui.click()

    # Wait before typing password (0.8 - 1.5 seconds)
    wait_time = 0.8 + 0.7 * random.random()
    print(f"Waiting {wait_time:.2f} seconds before typing...")
    time.sleep(wait_time)

    # Step 10: Type password
    print("\n" + "-" * 50)
    print("Typing password...")

    password = config['accounts']['twitter']['password']
    print(f"Password length: {len(password)} characters")

    # Type password with human-like variable delays (0.1 - 0.6 seconds)
    for i, char in enumerate(password):
        pyautogui.write(char)
        char_delay = 0.1 + 0.5 * random.random()
        if i < len(password) - 1:  # Don't delay after last character
            time.sleep(char_delay)

    print("Password typed successfully")

    # Wait after typing password (0.7 - 1.2 seconds)
    wait_time = 0.7 + 0.5 * random.random()
    print(f"Waiting {wait_time:.2f} seconds...")
    time.sleep(wait_time)

    # Step 11: Click Log in button
    print("\n" + "-" * 50)
    print("Looking for Log in button...")

    LOGIN_BUTTON_SELECTOR = '[data-testid="LoginForm_Login_Button"]'

    login_coords = get_element_coordinates_node(selector=LOGIN_BUTTON_SELECTOR, port=DEFAULT_DEBUG_PORT)

    if login_coords is None:
        print("Could not find Log in button")
        return False

    target_x, target_y = login_coords

    # Randomize click position within button area
    offset_x = random.randint(-40, 40)
    offset_y = random.randint(-10, 10)
    final_x = target_x + offset_x
    final_y = target_y + offset_y

    print(f"Found Log in button at ({target_x}, {target_y})")
    print(f"Randomized click position: ({final_x}, {final_y})")

    print("Moving mouse to Log in button...")
    human_move_with_overshoot(final_x, final_y, overshoot_chance=0.25)

    time.sleep(0.1 + 0.2 * random.random())

    print("Clicking Log in button...")
    pyautogui.click()

    print("==" * 25)
    print("Clicked Log in button - waiting for page load...")
    print("==" * 25)

    # Wait for page to load
    if wait_for_network_idle():
        print("Page loaded successfully")
    else:
        print("Page load timeout, continuing anyway...")

    # Step 12: Check for and close two-factor authentication modal (if present)
    print("\n" + "-" * 50)
    print("Checking for two-factor authentication modal...")

    CLOSE_MODAL_SELECTOR = '[data-testid="app-bar-close"]'
    modal_close_coords = get_element_coordinates_node(selector=CLOSE_MODAL_SELECTOR, port=DEFAULT_DEBUG_PORT)

    if modal_close_coords is not None:
        print("Two-factor authentication modal detected!")
        target_x, target_y = modal_close_coords

        # Randomize click position within button area
        offset_x = random.randint(-10, 10)
        offset_y = random.randint(-10, 10)
        final_x = target_x + offset_x
        final_y = target_y + offset_y

        print(f"Found close button at ({target_x}, {target_y})")
        print(f"Randomized click position: ({final_x}, {final_y})")

        print("Moving mouse to close button...")
        human_move_with_overshoot(final_x, final_y, overshoot_chance=0.25)

        time.sleep(0.1 + 0.2 * random.random())

        print("Clicking close button...")
        pyautogui.click()

        print("Modal closed successfully")

        # Wait briefly after closing modal
        time.sleep(0.5 + 0.3 * random.random())
    else:
        print("No two-factor authentication modal detected")

    # Step 13: Post-login mouse movement
    print("\n" + "-" * 50)
    print("Performing post-login mouse movement...")
    random_idle_movement(duration=1.5)
    print("Post-login mouse movement complete")

    print("\n" + "=" * 50)
    print("Login flow completed")
    print("=" * 50)

    return True


if __name__ == "__main__":
    login()
