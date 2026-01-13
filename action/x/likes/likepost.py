"""
Like post automation for X (Twitter).
Finds a post and clicks the like button.
"""

import sys
import json
import time
import random
import uuid
import re
import pyautogui
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from browser import DEFAULT_DEBUG_PORT, get_element_coordinates_node, get_cdp_session
from action.x.findpost import findpost
from action.mouse.initial import human_move_with_overshoot
from action.tab_switcher import get_all_tabs, switch_to_tab
from action.pageload import wait_for_network_idle


# Selectors
TWEET_ARTICLE_SELECTOR = 'article[data-testid="tweet"]'
LIKE_BUTTON_SELECTOR = 'button[data-testid="like"]'


def strip_emojis(text: str) -> str:
    """
    Remove emojis and other unicode symbols from text.

    Args:
        text: Input text potentially containing emojis

    Returns:
        Text with emojis removed
    """
    # Pattern to match emojis and other unicode symbols
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002702-\U000027B0"  # dingbats
        "\U000024C2-\U0001F251"  # enclosed characters
        "\U0001F900-\U0001F9FF"  # supplemental symbols
        "\U0001FA00-\U0001FA6F"  # chess symbols
        "\U0001FA70-\U0001FAFF"  # symbols and pictographs extended-A
        "\U00002600-\U000026FF"  # misc symbols
        "\U00002700-\U000027BF"  # dingbats
        "\U0001F700-\U0001F77F"  # alchemical symbols
        "\U0001F780-\U0001F7FF"  # geometric shapes extended
        "\U0001F800-\U0001F8FF"  # supplemental arrows-C
        "\U0001FA00-\U0001FA6F"  # chess symbols extended
        "\U00002300-\U000023FF"  # misc technical
        "\U00002B50-\U00002B55"  # stars
        "\U0000200D"             # zero width joiner
        "\U0000FE0F"             # variation selector
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub("", text).strip()

# Memory file path
MEMORY_FILE = Path(__file__).parent.parent.parent.parent / "memory.json"


def get_current_url(port: int = DEFAULT_DEBUG_PORT) -> str | None:
    """
    Get the current page URL via CDP.

    Args:
        port: CDP debug port

    Returns:
        Current URL or None if failed
    """
    try:
        cdp = get_cdp_session(port)
        response = cdp.send("Runtime.evaluate", {
            "expression": "window.location.href"
        })
        if "result" in response and "result" in response["result"]:
            return response["result"]["result"].get("value")
    except Exception as e:
        print(f"Failed to get current URL: {e}")
    return None


def save_task_memory(
    task_type: str,
    username: str,
    post_content: str,
    url: str,
    status: str = "success"
) -> bool:
    """
    Save task memory to memory.json.

    Args:
        task_type: Type of task (e.g., "likepost")
        username: Target username
        post_content: Post content snippet
        url: URL of the post
        status: Task status

    Returns:
        True if saved successfully, False otherwise
    """
    task_id = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()

    task_entry = {
        "taskId": task_id,
        "timestamp": timestamp,
        "taskType": task_type,
        "username": username,
        "postContent": post_content,
        "url": url,
        "status": status
    }

    try:
        # Load existing memory or create new
        if MEMORY_FILE.exists():
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    memory = json.loads(content)
                else:
                    memory = {"tasks": []}
        else:
            memory = {"tasks": []}

        # Ensure tasks array exists
        if "tasks" not in memory:
            memory["tasks"] = []

        # Add new task entry
        memory["tasks"].append(task_entry)

        # Save back to file
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(memory, f, indent=2, ensure_ascii=False)

        print(f"Task memory saved: {task_id}")
        return True

    except Exception as e:
        print(f"Failed to save task memory: {e}")
        return False


def find_post_text_element(post_text: str, port: int = DEFAULT_DEBUG_PORT) -> tuple | None:
    """
    Find the span element containing the matching post text using JavaScript.
    Specifically targets the tweetText container to avoid clicking images.

    Args:
        post_text: The post text to search for
        port: CDP debug port

    Returns:
        (x, y) coordinates of the element center, or None if not found
    """
    # Escape quotes in the text for JavaScript
    escaped_text = post_text.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n")

    # JavaScript emoji regex pattern (built separately to avoid f-string conflicts)
    emoji_regex = r"/[\uD800-\uDBFF][\uDC00-\uDFFF]|[\u2600-\u27BF]|[\uFE00-\uFE0F]|[\u200D]/gu"

    # JavaScript to find the tweetText div and get its bounding rect
    js_code = f"""
    (function() {{
        const searchText = '{escaped_text}'.trim();

        // Remove emojis from text (handles surrogate pairs and common emoji ranges)
        function stripEmojis(text) {{
            // Remove surrogate pairs (emoji), variation selectors, and zero-width joiner
            return text.replace({emoji_regex}, '').replace(/\\s+/g, ' ');
        }}

        // Normalize whitespace: collapse all whitespace (spaces, newlines, tabs) into single spaces
        // Also strip emojis for comparison
        function normalizeText(text) {{
            return stripEmojis(text).trim().toLowerCase();
        }}

        const normalizedSearch = normalizeText(searchText);

        // First, find the tweetText div that contains matching text
        const tweetTexts = document.querySelectorAll('article[data-testid="tweet"] div[data-testid="tweetText"]');

        for (const tweetText of tweetTexts) {{
            const fullText = tweetText.textContent.trim();
            const normalizedFull = normalizeText(fullText);

            // Check if this tweetText contains our search text (with normalized whitespace, emojis stripped)
            if (normalizedFull.includes(normalizedSearch) || normalizedSearch.includes(normalizedFull)) {{
                // Get the bounding rect of the tweetText div itself (not the span)
                const rect = tweetText.getBoundingClientRect();

                // Click at the LEFT side of the text to avoid any images on the right
                return {{
                    found: true,
                    x: rect.left + 50,  // 50px from left edge
                    y: rect.top + rect.height / 2,  // vertically centered
                    text: fullText.substring(0, 50)
                }};
            }}
        }}
        return {{ found: false, availableTexts: Array.from(tweetTexts).map(t => normalizeText(t.textContent).substring(0, 80)) }};
    }})()
    """

    try:
        cdp = get_cdp_session(port)
        response = cdp.send("Runtime.evaluate", {
            "expression": js_code,
            "returnByValue": True
        })

        if "result" in response and "result" in response["result"]:
            result = response["result"]["result"].get("value", {})
            if result.get("found"):
                x = result["x"]
                y = result["y"]
                print(f"Found matching text: '{result.get('text', '')[:40]}...'")
                return (int(x), int(y))
            else:
                # Debug: show what texts are available on page
                available = result.get("availableTexts", [])
                if available:
                    print(f"Available tweet texts on page ({len(available)} found):")
                    for i, text in enumerate(available[:3]):  # Show first 3
                        print(f"  [{i}]: '{text}...'")

        print(f"Could not find post text: '{post_text[:40]}...'")
        return None

    except Exception as e:
        print(f"Error finding post text element: {e}")
        return None


def click_post_text(post_text: str, port: int = DEFAULT_DEBUG_PORT) -> bool:
    """
    Find and click the span containing the matching post text.

    Args:
        post_text: The post text to match
        port: CDP debug port

    Returns:
        True if clicked successfully, False otherwise
    """
    print(f"Looking for post text: '{post_text[:40]}...'")

    # Find the element with matching text
    coords = find_post_text_element(post_text, port=port)

    if coords is None:
        print("Could not find matching post text")
        return False

    # Need to convert viewport coords to screen coords
    # Get window metrics
    try:
        cdp = get_cdp_session(port)
        metrics_response = cdp.send("Runtime.evaluate", {
            "expression": "JSON.stringify({screenX: window.screenX, screenY: window.screenY, outerHeight: window.outerHeight, innerHeight: window.innerHeight, outerWidth: window.outerWidth, innerWidth: window.innerWidth, dpr: window.devicePixelRatio})",
            "returnByValue": True
        })

        if "result" in metrics_response and "result" in metrics_response["result"]:
            metrics = json.loads(metrics_response["result"]["result"].get("value", "{}"))
            dpr = metrics.get("dpr", 1.0)
            screen_x = metrics.get("screenX", 0)
            screen_y = metrics.get("screenY", 0)
            outer_height = metrics.get("outerHeight", 0)
            inner_height = metrics.get("innerHeight", 0)
            outer_width = metrics.get("outerWidth", 0)
            inner_width = metrics.get("innerWidth", 0)

            ui_height = outer_height - inner_height
            border_width = (outer_width - inner_width) / 2

            viewport_x, viewport_y = coords
            target_x = int((screen_x + border_width + viewport_x) * dpr)
            target_y = int((screen_y + ui_height + viewport_y) * dpr)
        else:
            target_x, target_y = coords
    except Exception as e:
        print(f"Error getting window metrics: {e}")
        target_x, target_y = coords

    # Randomize click position slightly
    offset_x = random.randint(-5, 5)
    offset_y = random.randint(-3, 3)
    final_x = target_x + offset_x
    final_y = target_y + offset_y

    print(f"Found post text at ({target_x}, {target_y})")
    print(f"Randomized click position: ({final_x}, {final_y})")

    # Move mouse with human-like movement
    print("Moving mouse to post text...")
    human_move_with_overshoot(final_x, final_y, overshoot_chance=0.25)

    # Small pause before clicking
    time.sleep(0.1 + 0.2 * random.random())

    # Click the post text
    print("Clicking post text...")
    pyautogui.click()

    return True


def scroll_down(amount: int = 300, port: int = DEFAULT_DEBUG_PORT) -> None:
    """
    Scroll down the page by a specified amount.

    Args:
        amount: Pixels to scroll down
        port: CDP debug port
    """
    try:
        cdp = get_cdp_session(port)
        cdp.send("Runtime.evaluate", {
            "expression": f"window.scrollBy(0, {amount})"
        })
        print(f"Scrolled down {amount}px")
        time.sleep(0.5 + 0.3 * random.random())
    except Exception as e:
        print(f"Error scrolling: {e}")


def click_like_button(port: int = DEFAULT_DEBUG_PORT, max_scroll_attempts: int = 3) -> bool:
    """
    Find and click the like button. Scrolls down if button is out of frame.

    Args:
        port: CDP debug port
        max_scroll_attempts: Maximum number of scroll attempts to find the button

    Returns:
        True if clicked successfully, False otherwise
    """
    print("Looking for like button...")

    coords = None
    scroll_attempts = 0

    # Try to find the like button, scrolling if needed
    while coords is None and scroll_attempts <= max_scroll_attempts:
        coords = get_element_coordinates_node(
            selector=LIKE_BUTTON_SELECTOR,
            port=port
        )

        if coords is None:
            if scroll_attempts < max_scroll_attempts:
                print(f"Like button not in view, scrolling down (attempt {scroll_attempts + 1}/{max_scroll_attempts})...")
                scroll_down(amount=random.randint(250, 400), port=port)
                scroll_attempts += 1
            else:
                print("Could not find like button after scrolling")
                return False

    if coords is None:
        print("Could not find like button")
        return False

    target_x, target_y = coords

    # Randomize click position
    offset_x = random.randint(-10, 10)
    offset_y = random.randint(-5, 5)
    final_x = target_x + offset_x
    final_y = target_y + offset_y

    print(f"Found like button at ({target_x}, {target_y})")
    print(f"Randomized click position: ({final_x}, {final_y})")

    # Move mouse with human-like movement
    print("Moving mouse to like button...")
    human_move_with_overshoot(final_x, final_y, overshoot_chance=0.25)

    # Small pause before clicking
    time.sleep(0.1 + 0.2 * random.random())

    # Click the like button
    print("Clicking like button...")
    pyautogui.click()

    return True


def find_blank_tab(port: int = DEFAULT_DEBUG_PORT) -> str | None:
    """
    Find a blank/empty tab and return its ID.

    Args:
        port: CDP debug port

    Returns:
        Tab ID if found, None otherwise
    """
    tabs = get_all_tabs(port=port)

    for tab in tabs:
        url = tab.get("url", "")
        # Check for blank/empty tabs
        if url in ("about:blank", "chrome://newtab/", ""):
            print(f"Found blank tab: {url}")
            return tab.get("id")

    print("No blank tab found")
    return None


def switch_to_blank_tab(port: int = DEFAULT_DEBUG_PORT) -> bool:
    """
    Switch to a blank/empty tab. Does NOT create one if none exists.

    Args:
        port: CDP debug port

    Returns:
        True if switched successfully, False otherwise
    """
    tab_id = find_blank_tab(port=port)

    if tab_id:
        return switch_to_tab(tab_id, port=port)

    print("No blank tab available to switch to")
    return False


def likepost(username: str, post: str, **params) -> bool:
    """
    Like a post by searching for it and clicking the like button.

    Flow:
    1. Run findpost to search for the post
    2. Wait for 5 seconds
    3. Click the matching post text to open it
    4. Wait for page load
    5. Click the like button
    6. Wait 3 seconds
    7. Copy the page URL
    8. Save task memory to memory.json
    9. Click home button to return to home
    10. Switch to blank tab

    Args:
        username: X/Twitter username (without @)
        post: Post content to match and click (emojis will be stripped)

    Returns:
        True if like executed successfully, False otherwise
    """
    # Strip emojis from input post text
    original_post = post
    post = strip_emojis(post)

    print("=" * 50)
    print("Like Post Automation")
    print("=" * 50)
    print(f"Username: {username}")
    print(f"Original post: {original_post}")
    print(f"Post (emojis stripped): {post}")
    print("-" * 50)

    # Step 1: Find the post using findpost
    print("\nStep 1: Finding the post...")
    if not findpost(username=username, post=post):
        print("Failed to find the post")
        return False

    print("Post search initiated")

    # Step 2: Wait for 5 seconds for results to load
    print("\nStep 2: Waiting 5 seconds for results...")
    time.sleep(5)

    # Step 3: Click the post text to open it (matches text from API command)
    print("\nStep 3: Clicking matching post text...")
    if not click_post_text(post, port=DEFAULT_DEBUG_PORT):
        print("Failed to click post text")
        return False

    print("Post text clicked")

    # Step 4: Wait for page load
    print("\nStep 4: Waiting for page to load...")
    if wait_for_network_idle():
        print("Page loaded")
    else:
        print("Page load timeout, continuing anyway...")

    # Step 5: Click the like button
    print("\nStep 5: Clicking like button...")
    if not click_like_button(port=DEFAULT_DEBUG_PORT):
        print("Failed to click like button")
        return False

    print("Like button clicked")

    # Step 6: Wait 3 seconds
    print("\nStep 6: Waiting 3 seconds...")
    time.sleep(3)

    # Step 7: Copy the page URL
    print("\nStep 7: Getting page URL...")
    page_url = get_current_url(port=DEFAULT_DEBUG_PORT)
    if page_url:
        print(f"Page URL: {page_url}")
    else:
        page_url = "unknown"
        print("Warning: Could not get page URL")

    # Step 8: Save task memory
    print("\nStep 8: Saving task memory...")
    save_task_memory(
        task_type="likepost",
        username=username,
        post_content=post,
        url=page_url,
        status="success"
    )

    # Step 9: Click home button to return to home
    print("\nStep 9: Clicking home button...")
    from action.x.home_button import click_home
    if not click_home(port=DEFAULT_DEBUG_PORT):
        print("Warning: Failed to click home button, continuing...")
    else:
        print("Navigated to home")

    # Wait for home page to load
    time.sleep(1 + 0.5 * random.random())

    # Step 10: Switch to blank tab
    print("\nStep 10: Switching to blank tab...")
    if not switch_to_blank_tab(port=DEFAULT_DEBUG_PORT):
        print("Warning: No blank tab to switch to")
    else:
        print("Switched to blank tab")

    print("\n" + "=" * 50)
    print("Like post automation completed!")
    print("=" * 50)

    return True


if __name__ == "__main__":
    # Test with example parameters
    print("Testing likepost automation...")
    print("Starting in 3 seconds...")
    time.sleep(3)

    # Example: Like a post
    result = likepost(
        username="elonmusk",
        post="Who's building ov"  # First 16 chars
    )

    if result:
        print("\n[OK] Like post automation completed successfully")
    else:
        print("\n[FAIL] Like post automation failed")
