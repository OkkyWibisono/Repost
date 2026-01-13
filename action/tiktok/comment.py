import time
import random
from pathlib import Path
import sys
import json

# Add project root to path for imports if needed
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from browser import get_cdp_session, DEFAULT_DEBUG_PORT
from action.pageload import wait_for_network_idle

def type_real_keys(sess, text: str):
    """
    Simulates real typing via CDP (background safe).
    Sends 'char' events which are usually sufficient for text input,
    but we can add keyDown/keyUp if needed.
    """
    print(f"Typing '{text}' character-by-character...")
    for char in text:
        # Simulate key press
        sess.send("Input.dispatchKeyEvent", {
            "type": "keyUp",
            "text": char,
            "unmodifiedText": char,
            "key": char
        })
        sess.send("Input.dispatchKeyEvent", {
            "type": "char",
            "text": char
        })
        time.sleep(random.uniform(0.02, 0.05))

def comment(username: str, comment_text: str, **params) -> bool:
    """
    Comment on a TikTok video using pure CDP with character-by-character typing.
    Background safe.
    """
    print(f"Starting comment action for @{username}")
    
    url = params.get("url") or params.get("video_url")
    if not url:
        print("❌ No video URL provided")
        return False
        
    sess = get_cdp_session(DEFAULT_DEBUG_PORT)
    if not sess.connect():
        print("❌ Could not connect to browser")
        return False

    # 1. Navigate
    print(f"Navigating to {url}")
    sess.send("Page.navigate", {"url": url})
    time.sleep(2)
    wait_for_network_idle()
    time.sleep(3) 

    # 2. Locate Comment Box
    print("Locating comment box...")
    
    INPUT_SELECTORS = [
        '[contenteditable="true"]',
        '.public-DraftEditor-content',
        '[data-e2e="comment-input"]',
        'div[role="textbox"]'
    ]
    
    ICON_SELECTORS = [
        '[data-e2e="comment-icon"]',
        'button[aria-label*="comments"]',
        '[data-e2e="browse-comment"]',
        '.css-1asnt3f-ButtonActionItem'
    ]
    
    found_selector = None
    
    def find_input():
        for sel in INPUT_SELECTORS:
            # We need to ensure it's visible and focused
            found = sess.send("Runtime.evaluate", {
                "expression": f"""
                (function(){{
                    const el = document.querySelector('{sel}');
                    if(!el || el.offsetParent === null) return false;
                    el.focus(); 
                    return true;
                }})()
                """,
                "returnByValue": True
            }).get("result", {}).get("result", {}).get("value")
            if found: return sel
        return None

    # Retry loop with drawer opening
    for attempt in range(4):
        print(f"Attempt {attempt+1}: Finding input...")
        found_selector = find_input()
        if found_selector:
            print(f"✅ Found comment input: {found_selector}")
            break
            
        print("⚠️ Input not found. Checking for comment icon to open drawer...")
        for icon_sel in ICON_SELECTORS:
            clicked = sess.send("Runtime.evaluate", {
                "expression": f"document.querySelector('{icon_sel}')?.click() || false",
                "returnByValue": True
            }).get("result", {}).get("result", {}).get("value")
            if clicked:
                print(f"Clicked icon: {icon_sel}")
                time.sleep(2)
                break
        time.sleep(2)

    if not found_selector:
        print("❌ Comment box not found after retries")
        return False

    # 3. Insert Text (Character by Character)
    # First, clear existing text if any (safety)
    sess.send("Runtime.evaluate", {
        "expression": f"document.querySelector('{found_selector}').innerText = '';"
    })
    
    # Focus again
    sess.send("Runtime.evaluate", {
        "expression": f"document.querySelector('{found_selector}').focus();"
    })
    
    # TYPE IT
    type_real_keys(sess, comment_text)
    
    # 4. Post
    time.sleep(1)
    print("Clicking Post...")
    
    posted = False
    for _ in range(10):
        clicked = sess.send("Runtime.evaluate", {
            "expression": """
            (function(){
                const btns = document.querySelectorAll('button, [role="button"]');
                for(const b of btns){
                    const t = (b.innerText||'').toLowerCase();
                    if(t.includes('post') || t.includes('kirim')){
                        // Check if disabled attribute exists or class contains disabled
                        const disabled = b.disabled || b.getAttribute('aria-disabled') === 'true' || b.classList.contains('disabled');
                        
                        // Color check is good but sometimes flaky. 
                        // If it's NOT disabled, we assume it's good to click.
                        if(!disabled){
                            b.click();
                            return true;
                        }
                    }
                }
                return false;
            })()
            """,
            "returnByValue": True
        }).get("result", {}).get("result", {}).get("value")
        
        if clicked:
            print("✅ Post button clicked")
            posted = True
            break
        
        print("Waiting for Post button to enable...")
        time.sleep(0.5)

    if not posted:
        print("⚠️ Post button not clicked. Trying Enter key...")
        sess.send("Input.dispatchKeyEvent", {"type":"keyDown","key":"Enter","code":"Enter"})
        sess.send("Input.dispatchKeyEvent", {"type":"keyUp","key":"Enter","code":"Enter"})

    time.sleep(2)
    return True