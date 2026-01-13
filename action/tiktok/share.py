import time
import random
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from browser import get_cdp_session, DEFAULT_DEBUG_PORT
from action.pageload import wait_for_network_idle
from action.tiktok.login_detection import detect_login

def share(url: str, **params) -> bool:
    """
    Automates sharing a TikTok video by clicking the share button and clicking 'Repost'.
    """
    print(f"Starting share action for video: {url}")
    
    # Check login status first
    if not detect_login(port=DEFAULT_DEBUG_PORT):
        print("❌ Error: You must be logged in to repost a video.")
        return False

    sess = get_cdp_session(DEFAULT_DEBUG_PORT)
    if not sess.connect():
        print("❌ Could not connect to browser")
        return False

    # 1. Navigate to video URL
    print(f"Navigating to {url}...")
    sess.send("Page.navigate", {"url": url})
    time.sleep(2)
    wait_for_network_idle()
    time.sleep(3)

    # 2. Click Share Button
    # Selector researched: button[aria-label*="Share video"]
    print("Clicking Share button...")
    script_click_share = """
    (function(){
        const shareBtn = document.querySelector('button[aria-label*="Share video"]') || 
                         document.querySelector('button[aria-label*="Bagikan"]');
        if (shareBtn) {
            shareBtn.scrollIntoView({ behavior: 'instant', block: 'center' });
            shareBtn.click();
            return true;
        }
        return false;
    })()
    """
    success = sess.send("Runtime.evaluate", {
        "expression": script_click_share,
        "returnByValue": True
    }).get("result", {}).get("result", {}).get("value")

    if not success:
        print("❌ Share button not found")
        return False
    
    time.sleep(1.5)

    # 3. Click 'Repost'
    # Selector researched: div[data-e2e="share-repost"] (contains "Repost")
    print("Clicking 'Repost'...")
    script_click_repost = """
    (function(){
        // The Repost button is typically the first item in the share menu
        const repostBtn = document.querySelector('[data-e2e="share-repost"]');
        if (repostBtn) {
            repostBtn.click();
            return true;
        }
        
        // Fallback: search for elements with 'Repost' text
        const items = Array.from(document.querySelectorAll('div, p, span, button'));
        const fallbackBtn = items.find(el => {
            const text = el.textContent.trim().toLowerCase();
            return (text === 'repost' || text === 'repost video' || text === 'bagikan ulang') && 
                   el.offsetParent !== null;
        });
        
        if (fallbackBtn) {
            // Find clickable container or click directly
            let clickable = fallbackBtn;
            while (clickable && clickable.tagName !== 'BODY') {
                if (clickable.tagName === 'BUTTON' || clickable.getAttribute('role') === 'button' || (clickable.getAttribute('data-e2e') && clickable.getAttribute('data-e2e').includes('share-repost'))) {
                    break;
                }
                clickable = clickable.parentElement;
            }
            (clickable || fallbackBtn).click();
            return true;
        }
        return false;
    })()
    """
    success = sess.send("Runtime.evaluate", {
        "expression": script_click_repost,
        "returnByValue": True
    }).get("result", {}).get("result", {}).get("value")

    if not success:
        print("❌ 'Repost' button not found")
        return False

    print("✅ Repost action triggered successfully")
    time.sleep(3)
    return True

if __name__ == "__main__":
    # Test call
    share("https://www.tiktok.com/@azurafamily_/video/7589582924832443666")
