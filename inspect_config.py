import json
from pathlib import Path

CONFIG_FILE = Path("config.json")

def inspect_config():
    if not CONFIG_FILE.exists():
        print("config.json not found")
        return

    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)

    proxy = config.get("proxy", {})
    print("Proxy Config:")
    for k, v in proxy.items():
        if v is None:
            print(f"  {k}: None")
        else:
            s = str(v)
            print(f"  {k}: '{s}' (len: {len(s)}, starts_with_space: {s.startswith(' ')}, ends_with_space: {s.endswith(' ')})")

if __name__ == "__main__":
    inspect_config()
