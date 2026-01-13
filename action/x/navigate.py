import sys
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from browser import launch_chrome, DEFAULT_DEBUG_PORT
from action.mouse.initial import initialize as mouse_init

URL = "https://x.com"
PAGE_LOAD_WAIT = 3  # seconds to wait for page load


def _launch_and_init(url: str, wait: float = PAGE_LOAD_WAIT) -> None:
    """Launch browser, wait for page load, and initialize mouse."""
    launch_chrome(url=url, debug_port=DEFAULT_DEBUG_PORT)
    print(f"Waiting {wait}s for page to load...")
    time.sleep(wait)
    mouse_init()


def navigate(**params) -> None:
    """Navigate to X.com"""
    print("Opening X (Twitter)...")
    _launch_and_init(URL)


def login(**params) -> None:
    """Navigate to X login page."""
    print("Opening X login page...")
    _launch_and_init(f"{URL}/login")


def logout(**params) -> None:
    """Navigate to X logout."""
    print("Opening X logout...")
    _launch_and_init(f"{URL}/logout")


def search(**params) -> None:
    """Navigate to X search."""
    query = params.get("query", "")
    if query:
        print(f"Searching X for: {query}")
        _launch_and_init(f"{URL}/search?q={query}")
    else:
        print("Opening X explore...")
        _launch_and_init(f"{URL}/explore")


def post(**params) -> None:
    """Navigate to X compose."""
    print("Opening X compose...")
    _launch_and_init(f"{URL}/compose/tweet")


def maintain(**params) -> None:
    """Maintain session - just navigate to home."""
    print("Opening X home...")
    _launch_and_init(URL)


def comment(**params) -> None:
    """Navigate to X (for commenting)."""
    print("Opening X for commenting...")
    _launch_and_init(URL)


def reply(**params) -> None:
    """Navigate to X (for replying)."""
    print("Opening X for replying...")
    _launch_and_init(URL)


def like(**params) -> None:
    """Navigate to X (for liking)."""
    print("Opening X for liking...")
    _launch_and_init(URL)


def destroy(**params) -> None:
    """Navigate to X settings."""
    print("Opening X settings...")
    _launch_and_init(f"{URL}/settings")
