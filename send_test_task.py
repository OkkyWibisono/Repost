import requests
import json
import time
import argparse
import importlib
import sys
from pathlib import Path

API_URL = "http://localhost:8888/tasks"


def send_task():
    # Example task for TikTok likepost
    task = {
        "platform": "tiktok",
        "task": "likepost",
        "params": {
            "url": "https://www.tiktok.com/@azurafamily_/video/7589215021557878034"
        }
    }
    # task = {
    #     "platform": "tiktok",
    #     "task": "share",
    #     "params": {
    #         "url": "https://www.tiktok.com/@azurafamily_/video/7589215021557878034"
    #     }
    # }
    # task = {
    #     "platform": "tiktok",
    #     "task": "comment",
    #     "params": {
    #         "username": "azurafamily_",
    #         "url": "https://www.tiktok.com/@azurafamily_/video/7589582924832443666",
    #         "comment_text": "Lucuu banget adenya"
    #     }
    # }

    try:
        print(f"Sending task to {API_URL}...")
        print(json.dumps(task, indent=2))

        response = requests.post(API_URL, json=task)

        if response.status_code == 200:
            print("\nSuccess! Task queued.")
            print(f"Response: {response.json()}")
        else:
            print(f"\nFailed. Status code: {response.status_code}")
            print(f"Response: {response.text}")

    except requests.exceptions.ConnectionError:
        print(f"\nError: Could not connect to {API_URL}")
        print("Make sure 'python fake_api.py' is running in a separate terminal!")


def run_mock_like_test():
    """Run a safe mocked runtime test for `action.tiktok.likepost.likepost`.
    This will NOT move the mouse nor interact with a real browser.
    """
    sys.path.insert(0, str(Path(__file__).parent))
    lp = importlib.reload(importlib.import_module('action.tiktok.likepost'))

    class MockCDP:
        def __init__(self, aria):
            self.aria = aria

        def send(self, method, params=None):
            return {"result": {"result": {"value": {"found": True, "aria": self.aria, "className": "", "inner": ""}}}}

    # Prepare a helper to apply mocks
    def setup(aria_value):
        calls = []
        # Patch CDP
        lp.get_cdp_session = lambda port=lp.DEFAULT_DEBUG_PORT: MockCDP(aria_value)
        # Patch tab switcher to avoid real CDP calls
        try:
            import action.tab_switcher as _ts
            _ts.create_and_switch_to_new_tab = lambda url, port=lp.DEFAULT_DEBUG_PORT: True
        except Exception:
            pass
        # Patch element locator to always find like button
        lp.get_element_coordinates_node = lambda selector, port=lp.DEFAULT_DEBUG_PORT: (600, 400)
        # Patch movement and mouse functions to record calls instead of moving
        lp.human_move_with_overshoot = lambda *a, **k: calls.append(('move', a))
        lp.mouse_init = lambda: calls.append('mouse_init')
        lp.wait_for_network_idle = lambda: True
        # Patch pyautogui in module namespace
        lp.pyautogui.click = lambda: calls.append('click')
        lp.pyautogui.doubleClick = lambda: calls.append('double')
        lp.pyautogui.size = lambda: (1920, 1080)
        # Prevent handle_captcha from blocking
        lp.handle_captcha = lambda port=lp.DEFAULT_DEBUG_PORT: None
        return calls, lp

    print('--- Test A: Not liked (aria=false) -> should click')
    calls, lp = setup('false')
    res = lp.likepost('someuser', url='https://www.tiktok.com/@azurafamily_/video/7589582924832443666')
    print('result:', res)
    print('calls:', calls)

    print('\n--- Test B: Already liked (aria=true) -> should skip click')
    calls2, lp2 = setup('true')
    res2 = lp2.likepost('someuser', url='https://www.tiktok.com/@azurafamily_/video/7589582924832443666')
    print('result:', res2)
    print('calls:', calls2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--mock-like', action='store_true', help='Run a safe mocked likepost test locally')
    args = parser.parse_args()

    if args.mock_like:
        from pathlib import Path
        run_mock_like_test()
    else:
        send_task()
