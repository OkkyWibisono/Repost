import json
from pathlib import Path
from datetime import datetime

CONFIG_FILE = Path(__file__).parent / "config.json"

PLATFORM_MAP = {
    "x": "twitter",
    "twitter": "twitter",
    "instagram": "instagram",
    "facebook": "facebook",
    "tiktok": "tiktok",
}


def load_config() -> dict:
    """Load configuration from config.json."""
    if not CONFIG_FILE.exists():
        return {}

    with open(CONFIG_FILE, "r") as f:
        return json.load(f)


def save_config(config: dict) -> None:
    """Save configuration to config.json."""
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=3)


def get_platform_key(platform: str) -> str:
    """Get the config.json key for a platform."""
    return PLATFORM_MAP.get(platform, platform)


def get_account(platform: str) -> dict | None:
    """Get account info for a platform."""
    config = load_config()
    platform_key = get_platform_key(platform)
    return config.get("accounts", {}).get(platform_key)


def update_account_status(platform: str, status: str) -> None:
    """
    Update the status of a platform account.

    Args:
        platform: Platform name (e.g., "x", "instagram")
        status: Status string (e.g., "logged_in", "not_logged_in")
    """
    config = load_config()
    platform_key = get_platform_key(platform)

    if "accounts" not in config:
        config["accounts"] = {}

    if platform_key not in config["accounts"]:
        config["accounts"][platform_key] = {}

    config["accounts"][platform_key]["status"] = status
    config["accounts"][platform_key]["last_active"] = datetime.now().isoformat()

    save_config(config)
    print(f"Updated {platform_key} status: {status}")


def update_account_cookies(platform: str, cookies: dict) -> None:
    """
    Update cookies for a platform account.

    Args:
        platform: Platform name
        cookies: Dictionary of cookie name -> value
    """
    config = load_config()
    platform_key = get_platform_key(platform)

    if "accounts" not in config:
        config["accounts"] = {}

    if platform_key not in config["accounts"]:
        config["accounts"][platform_key] = {}

    if "cookies" not in config["accounts"][platform_key]:
        config["accounts"][platform_key]["cookies"] = {}

    config["accounts"][platform_key]["cookies"].update(cookies)
    config["accounts"][platform_key]["last_active"] = datetime.now().isoformat()

    save_config(config)


if __name__ == "__main__":
    # Test
    print("Current config:")
    print(json.dumps(load_config(), indent=2))
