import sys
import time
import random
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from browser import launch_chrome, DEFAULT_DEBUG_PORT, get_cdp_session, get_element_coordinates_node
from action.pageload import wait_for_network_idle

# TikTok Selectors
# Note: These selectors are subject to change
PROFILE_VIDEO_SELECTOR = '[data-e2e="user-post-item"] a'  # Selector for video thumbnails on profile
LIKE_BUTTON_SELECTOR = '[data-e2e="like-icon"]'      # Selector for like icon on video page
MODAL_CLOSE_SELECTOR = '[data-e2e="modal-close-inner-button"]'

def likepost(username: str = None, **params) -> bool:
    """
    Like a user's latest post on TikTok.

    Flow:
    1. Navigate to user profile: tiktok.com/@{username}
    2. Click the first video in the list
    3. Click the like button
    
    Args:
        username: TikTok username (without @)
        
    Returns:
        True if successful, False otherwise
    """
    print("=" * 50)
    print("TikTok Like Post Automation")
    print("=" * 50)
    url = params.get("url")
    
    if not username and not url:
        print("❌ Error: Either username or url must be provided")
        return False
    
    if url:
        print(f"Direct video URL provided: {url}")
        print("-" * 50)
        
        # Step 1: Navigate directly to video
        print(f"\nStep 1: Navigating to video: {url}")
        from action.tab_switcher import create_and_switch_to_new_tab
        if not create_and_switch_to_new_tab(url=url, port=DEFAULT_DEBUG_PORT):
            print("Failed to navigate to video URL")
            return False
            
        print("Waiting for video page to load...")
        if wait_for_network_idle():
            print("Page loaded")
        else:
            print("Page load timeout, continuing anyway...")
            
        time.sleep(2)
        handle_captcha(port=DEFAULT_DEBUG_PORT)
        
        
        # Skip Step 2 (Finding video) since we are already on it
        print("\nStep 2: Skipped (Direct URL used)")
        
    else:
        print(f"Target Username: {username}")
        print("-" * 50)

        # Step 1: Navigate to user profile
        url = f"https://www.tiktok.com/@{username}"
        print(f"\nStep 1: Navigating to profile: {url}")
        
        # Use create_and_switch_to_new_tab for reliable navigation
        from action.tab_switcher import create_and_switch_to_new_tab
        if not create_and_switch_to_new_tab(url=url, port=DEFAULT_DEBUG_PORT):
            print("Failed to navigate to profile")
            return False
        
        print("Waiting for profile to load...")
        if wait_for_network_idle():
            print("Page loaded")
        else:
            print("Page load timeout, continuing anyway...")
            
        time.sleep(2) # Extra wait for dynamic content
        handle_captcha(port=DEFAULT_DEBUG_PORT) # Check for captcha after load
        

        # Step 2: Click the first video
        print("\nStep 2: Looking for latest video...")
        
        # Try multiple selectors for video
        VIDEO_SELECTORS = [
            '[data-e2e="user-post-item"] a',
            '[data-e2e="user-post-item"]',
            'a[href*="/video/"]'
        ]
        
        js_click_video = f"""
        (function() {{
            const selectors = {json.dumps(VIDEO_SELECTORS)};
            for (const sel of selectors) {{
                const el = document.querySelector(sel);
                if (el) {{
                    el.scrollIntoView({{behavior: 'instant', block: 'center'}});
                    el.click();
                    return true;
                }}
            }}
            return false;
        }})()
        """
        
        
        cdp = get_cdp_session(DEFAULT_DEBUG_PORT)
        
        print("Clicking video (JS)...")
        success = cdp.send("Runtime.evaluate", {"expression": js_click_video, "returnByValue": True}).get("result", {}).get("result", {}).get("value")

        if not success:
            print("Could not find any videos on this profile.")
            return False
        
        # Wait for video modal/page to load
        print("Waiting for video player to load...")
        time.sleep(3) # Wait for animation/modal
        wait_for_network_idle()
        handle_captcha(port=DEFAULT_DEBUG_PORT) # Check for captcha after opening video

    # Step 3: Click Like button
    print("\nStep 3: Looking for Like button...")
    
    # Use CDP to both detect and click (No-UI approach)
    cdp = get_cdp_session(DEFAULT_DEBUG_PORT)
    js_click = f"""
    (function() {{
        const sel = '{LIKE_BUTTON_SELECTOR}';
        const el = document.querySelector(sel);
        if (!el) return {{status: "not_found"}};
        
        // Check if already liked
        const parentBtn = el.closest('button');
        const isLiked = (parentBtn && parentBtn.getAttribute('aria-pressed') === 'true') || 
                        (el.getAttribute('aria-pressed') === 'true');
        
        if (isLiked) {{
            return {{status: "already_liked"}};
        }}
        
        // Click using JS
        (parentBtn || el).click();
        return {{status: "clicked"}};
    }})()
    """
    
    try:
        resp = cdp.send("Runtime.evaluate", {"expression": js_click, "returnByValue": True})
        result = resp.get("result", {}).get("result", {}).get("value", {})
        status = result.get("status")

        if status == "already_liked":
            print("Like button already active (already liked). Skipping click to avoid unlike.")
        elif status == "clicked":
            print("Successfully clicked Like button (JS).")
        elif status == "not_found":
            print("Could not find Like button.")
            return False
        else:
            print(f"Unexpected status from Like check: {status}")
            return False

    except Exception as e:
        print(f"Error performing No-UI Like: {e}")
        return False

    print("\nLike action performed (No-UI).")
    time.sleep(1)

    print("\n" + "=" * 50)
    print("TikTok Like Post Completed")
    print("=" * 50)
    
    return True

def handle_captcha(port: int = DEFAULT_DEBUG_PORT) -> None:
    """
    Check for captcha and wait for manual solution.
    """
    cdp = get_cdp_session(port)
    
    # Selectors for various TikTok captchas
    CAPTCHA_SELECTORS = [
        '[data-e2e="captcha-verify-container"]',
        '#captcha_container',
        '.captcha_verify_container',
        'input[placeholder="Enter what you hear"]'
    ]
    
    def _is_present():
        js = f"(function(){{ return ({json.dumps(CAPTCHA_SELECTORS)}).some(sel => !!document.querySelector(sel)); }})()"
        try:
            resp = cdp.send("Runtime.evaluate", {"expression": js, "returnByValue": True})
            return resp.get("result", {}).get("result", {}).get("value", False)
        except:
            return False
            
    if _is_present():
        print("\n" + "!" * 50)
        print("CAPTCHA DETECTED!")
        print("Automatic solving is risky. Please solve the slider manually.")
        print("Script is paused until captcha disappears...")
        print("!" * 50 + "\n")
        
        # Wait loop
        while _is_present():
            time.sleep(2)
            print(".", end="", flush=True)
            
        print("\nCaptcha solved/disappeared! Resuming...")
        time.sleep(2) # Wait a bit for page to settle

if __name__ == "__main__":
    # Test
    likepost("tiktok")
