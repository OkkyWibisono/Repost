"""
Human-like typing utilities.
Provides typing functions with randomized delays to mimic human behavior.
"""

import pyautogui
import random
import time
from typing import Optional


# Disable pyautogui pause for manual timing control
pyautogui.PAUSE = 0


def human_type(
    text: str,
    min_delay: float = 0.3,
    max_delay: float = 0.8,
    mistake_chance: float = 0.0
) -> None:
    """
    Type text with human-like timing.

    Each character is typed with a random delay between min_delay and max_delay.
    Optionally introduces typos that are corrected.

    Args:
        text: The text to type
        min_delay: Minimum delay between characters (seconds)
        max_delay: Maximum delay between characters (seconds)
        mistake_chance: Probability of making a typo (0.0 to 1.0)
    """
    print(f"Typing: {text[:30]}{'...' if len(text) > 30 else ''}")

    for i, char in enumerate(text):
        # Occasional typo simulation (optional)
        if mistake_chance > 0 and random.random() < mistake_chance:
            # Type a wrong character
            wrong_char = random.choice('abcdefghijklmnopqrstuvwxyz')
            pyautogui.write(wrong_char, _pause=False)
            time.sleep(random.uniform(0.1, 0.3))

            # Delete it
            pyautogui.press('backspace')
            time.sleep(random.uniform(0.1, 0.2))

        # Type the correct character
        pyautogui.write(char, _pause=False)

        # Random delay between characters
        if i < len(text) - 1:  # No delay after last character
            delay = random.uniform(min_delay, max_delay)
            time.sleep(delay)

    print(f"Typing complete ({len(text)} characters)")


def type_text(
    text: str,
    speed: str = "slow"
) -> None:
    """
    Type text with predefined speed profiles.

    Args:
        text: The text to type
        speed: Speed profile - "slow" (0.5-1.2s), "medium" (0.1-0.3s), "fast" (0.05-0.15s)
    """
    speed_profiles = {
        "slow": (0.5, 1.2),      # Human-like slow typing
        "medium": (0.1, 0.3),    # Normal typing
        "fast": (0.05, 0.15),    # Fast typing
        "very_slow": (0.8, 1.5), # Very deliberate typing
    }

    min_delay, max_delay = speed_profiles.get(speed, (0.5, 1.2))
    human_type(text, min_delay=min_delay, max_delay=max_delay)


def type_search_query(username: str, post_content: str) -> None:
    """
    Type a search query in the format: from:{username} "{post_content}"

    Args:
        username: Twitter/X username (without @)
        post_content: First 16 characters of the post content
    """
    # Build the search query
    search_query = f'from:{username} "{post_content}"'

    print(f"Search query: {search_query}")

    # Type with slow human-like speed
    human_type(search_query, min_delay=0.5, max_delay=1.2)


if __name__ == "__main__":
    # Test typing
    print("Testing human-like typing...")
    print("=" * 50)

    # Wait before starting
    print("Starting in 3 seconds...")
    time.sleep(3)

    # Test slow typing
    human_type("Hello World!", min_delay=0.5, max_delay=1.2)

    print("\nDone!")
