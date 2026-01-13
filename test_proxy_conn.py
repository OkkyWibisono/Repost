import urllib.request
import json
import os
from pathlib import Path

CONFIG_FILE = Path("config.json")

def test_proxy():
    if not CONFIG_FILE.exists():
        print("config.json not found")
        return

    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)

    proxy_cfg = config.get("proxy", {})
    host = proxy_cfg.get("host")
    port = proxy_cfg.get("port")
    user = proxy_cfg.get("username")
    pw = proxy_cfg.get("password")

    if not host:
        print("No proxy host configured")
        return

    proxy_url = f"http://{user}:{pw}@{host}:{port}"
    print(f"Testing proxy: http://{host}:{port} (auth hidden)")

    try:
        proxy_handler = urllib.request.ProxyHandler({'http': proxy_url, 'https': proxy_url})
        opener = urllib.request.build_opener(proxy_handler)
        # Try to reach a simple site
        response = opener.open("http://www.google.com", timeout=10)
        print(f"Success! Status: {response.status}")
    except Exception as e:
        print(f"Proxy test failed: {e}")

if __name__ == "__main__":
    test_proxy()
