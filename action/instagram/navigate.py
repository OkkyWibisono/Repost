"""
Instagram navigation and actions.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from browser import launch_chrome

URL = "https://instagram.com"


def navigate(**params) -> None:
    """Navigate to Instagram."""
    print(f"Opening Instagram...")
    launch_chrome(url=URL)


def login(**params) -> None:
    """Navigate to Instagram login page."""
    print("Opening Instagram login page...")
    launch_chrome(url=f"{URL}/accounts/login")


def logout(**params) -> None:
    """Navigate to Instagram logout."""
    print("Opening Instagram...")
    launch_chrome(url=URL)


def search(**params) -> None:
    """Navigate to Instagram explore/search."""
    print("Opening Instagram explore...")
    launch_chrome(url=f"{URL}/explore")


def post(**params) -> None:
    """Navigate to Instagram (for posting)."""
    print("Opening Instagram...")
    launch_chrome(url=URL)


def maintain(**params) -> None:
    """Maintain session - just navigate to home."""
    print("Opening Instagram home...")
    launch_chrome(url=URL)


def comment(**params) -> None:
    """Navigate to Instagram (for commenting)."""
    launch_chrome(url=URL)


def reply(**params) -> None:
    """Navigate to Instagram (for replying)."""
    launch_chrome(url=URL)


def like(**params) -> None:
    """Navigate to Instagram (for liking)."""
    launch_chrome(url=URL)


def destroy(**params) -> None:
    """Navigate to Instagram settings."""
    launch_chrome(url=f"{URL}/accounts/edit")
