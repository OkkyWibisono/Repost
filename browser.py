import os
import subprocess
import platform
import json
import time
import urllib.request
from typing import Tuple, Optional

DEFAULT_DEBUG_PORT = 9222


class CDPSession:
    """
    CDP WebSocket session manager.
    Maintains a single connection that can be reused across functions.
    """
    _instance: Optional["CDPSession"] = None
    _ws = None
    _message_id: int = 0
    _port: int = DEFAULT_DEBUG_PORT

    def __new__(cls, port: int = DEFAULT_DEBUG_PORT):
        """Singleton pattern - reuse existing connection."""
        if cls._instance is None or cls._port != port:
            cls._instance = super().__new__(cls)
            cls._port = port
            cls._ws = None
            cls._message_id = 0
        return cls._instance

    def connect(self) -> bool:
        """Connect to CDP WebSocket if not already connected."""
        if self._ws is not None:
            try:
                # Check if connection is still alive
                self._ws.ping()
                return True
            except:
                self._ws = None

        ws_url = get_cdp_websocket_url(self._port)
        if not ws_url:
            print("Could not get CDP WebSocket URL")
            return False

        try:
            from websocket import create_connection
            self._ws = create_connection(ws_url, timeout=30)
            print(f"Connected to CDP WebSocket")
            return True
        except Exception as e:
            print(f"Failed to connect to CDP: {e}")
            return False

    def disconnect(self):
        """Close the WebSocket connection."""
        if self._ws:
            try:
                self._ws.close()
            except:
                pass
            self._ws = None

    def send(self, method: str, params: dict = None) -> dict:
        """
        Send a CDP command and return the response.

        Args:
            method: CDP method name (e.g., "DOM.getDocument")
            params: Method parameters

        Returns:
            Response dictionary
        """
        if not self._ws:
            if not self.connect():
                return {"error": "Not connected"}

        self._message_id += 1
        msg = {"id": self._message_id, "method": method}
        if params:
            msg["params"] = params

        try:
            self._ws.send(json.dumps(msg))
            while True:
                response = json.loads(self._ws.recv())
                # Skip events, wait for our response
                if response.get("id") == self._message_id:
                    return response
        except Exception as e:
            print(f"CDP command failed: {e}")
            return {"error": str(e)}

    def get_element_coordinates(self, selector: str = None, data_testid: str = None) -> Optional[Tuple[int, int]]:
        """
        Get the center coordinates of an element.

        Args:
            selector: CSS selector
            data_testid: data-testid attribute value

        Returns:
            (x, y) center coordinates or None if not found
        """
        if not self.connect():
            return None

        # Build the selector
        if data_testid:
            css_selector = f'[data-testid="{data_testid}"]'
        elif selector:
            css_selector = selector
        else:
            print("Must provide selector or data_testid")
            return None

        # Get the document
        doc_response = self.send("DOM.getDocument")
        if "error" in doc_response or "result" not in doc_response:
            print(f"Failed to get document: {doc_response}")
            return None

        root_node_id = doc_response["result"]["root"]["nodeId"]

        # Find the element
        query_response = self.send("DOM.querySelector", {
            "nodeId": root_node_id,
            "selector": css_selector
        })

        if "error" in query_response or "result" not in query_response:
            print(f"Failed to query selector: {query_response}")
            return None

        node_id = query_response["result"]["nodeId"]
        if node_id == 0:
            print(f"Element not found: {css_selector}")
            return None

        # Get the bounding box
        box_response = self.send("DOM.getBoxModel", {"nodeId": node_id})

        if "error" in box_response or "result" not in box_response:
            print(f"Failed to get box model: {box_response}")
            return None

        box_model = box_response["result"]["model"]
        # content is an array of points: [x1, y1, x2, y2, x3, y3, x4, y4]
        content = box_model["content"]

        # Calculate center from the 4 corner points
        x_coords = [content[i] for i in range(0, 8, 2)]
        y_coords = [content[i] for i in range(1, 8, 2)]

        center_x = int(sum(x_coords) / 4)
        center_y = int(sum(y_coords) / 4)

        return (center_x, center_y)

    def click_element(self, selector: str = None, data_testid: str = None) -> bool:
        """
        Click an element using CDP DOM click (no mouse movement).

        Args:
            selector: CSS selector
            data_testid: data-testid attribute value

        Returns:
            True if clicked successfully
        """
        if not self.connect():
            return False

        # Build the selector
        if data_testid:
            css_selector = f'[data-testid="{data_testid}"]'
        elif selector:
            css_selector = selector
        else:
            return False

        # Use JavaScript to click the element
        js_code = f'document.querySelector(\'{css_selector}\').click()'
        response = self.send("Runtime.evaluate", {"expression": js_code})

        return "error" not in response


# Global CDP session instance
_cdp_session: Optional[CDPSession] = None


def get_cdp_session(port: int = DEFAULT_DEBUG_PORT) -> CDPSession:
    """Get or create the global CDP session."""
    global _cdp_session
    if _cdp_session is None or _cdp_session._port != port:
        _cdp_session = CDPSession(port)
    return _cdp_session


def get_chrome_path() -> str:
    """Get the Chrome executable path based on OS."""
    if platform.system() == "Windows":
        paths = [
            os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
        ]
        for path in paths:
            if os.path.exists(path):
                return path
    elif platform.system() == "Darwin":
        return "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    else:
        return "google-chrome"

    raise FileNotFoundError("Chrome executable not found")


def get_user_data_dir() -> str:
    """Get the default Chrome user data directory."""
    if platform.system() == "Windows":
        return os.path.expandvars(r"%LocalAppData%\Google\Chrome\User Data")
    elif platform.system() == "Darwin":
        return os.path.expanduser("~/Library/Application Support/Google/Chrome")
    else:
        return os.path.expanduser("~/.config/google-chrome")


def _sanitize_proxy_for_chrome(proxy: str) -> tuple[str, bool]:
    """
    Sanitize a proxy string for use with Chrome's --proxy-server flag.

    Removes embedded credentials (username:password@) because Chrome's
    --proxy-server does not support including credentials in the value.

    Returns a tuple of (sanitized_proxy, credentials_removed_flag).
    """
    if not proxy:
        return (proxy, False)

    try:
        # Simple detection: if proxy contains '@', credentials are likely present
        if "@" in proxy:
            # Try to parse URL-like proxies: scheme://user:pass@host:port
            from urllib.parse import urlparse

            parsed = urlparse(proxy)
            scheme = parsed.scheme or ""
            host = parsed.hostname or ""
            port = parsed.port or ""

            if host and port:
                if scheme:
                    return (f"{scheme}://{host}:{port}", True)
                else:
                    return (f"{host}:{port}", True)

            # Fallback: strip credentials manually
            try:
                without_creds = proxy.split("@", 1)[1]
                return (without_creds, True)
            except Exception:
                return (proxy, False)

        # No credentials present; return as-is
        return (proxy, False)
    except Exception:
        return (proxy, False)


def kill_chrome() -> bool:
    """
    Kill all Chrome processes.

    Returns:
        True if any processes were killed, False otherwise.
    """
    if platform.system() == "Windows":
        result = subprocess.run(
            ["taskkill", "/F", "/IM", "chrome.exe"],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    else:
        result = subprocess.run(
            ["pkill", "-f", "chrome"],
            capture_output=True,
            text=True
        )
        return result.returncode == 0


def is_chrome_running() -> bool:
    """Check if Chrome is currently running."""
    if platform.system() == "Windows":
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq chrome.exe"],
            capture_output=True,
            text=True
        )
        return "chrome.exe" in result.stdout.lower()
    else:
        result = subprocess.run(
            ["pgrep", "-f", "chrome"],
            capture_output=True,
            text=True
        )
        return result.returncode == 0


def launch_chrome(
    url: str = None,
    profile: str = "Default",
    debug_port: int = DEFAULT_DEBUG_PORT,
    force_restart: bool = True,
    user_data_dir: str = None,
    stealth_mode: bool = True,
    proxy: str = None
) -> subprocess.Popen:
    """
    Launch Chrome with the current user's browser profile.

    Args:
        url: URL to navigate to (optional)
        profile: Profile directory name (default: "Default")
        debug_port: Remote debugging port for CDP (default: 9222)
        force_restart: If Chrome is running without CDP, restart it (default: True)
        user_data_dir: Custom user data directory (optional)
        stealth_mode: Enable stealth mode (navigator.webdriver=false, etc.) (default: True)
        proxy: Proxy server (e.g., "http://host:port" or "socks5://host:port")
               If None, reads from config.json

    Returns:
        Popen object for the Chrome process
    """
    chrome_path = get_chrome_path()

    # Load proxy from config if not provided
    if proxy is None:
        try:
            from config import load_config
            config = load_config()
            proxy_config = config.get("proxy", {})
            if proxy_config.get("host"):
                proxy_host = proxy_config["host"]
                proxy_port = proxy_config.get("port", 8080)
                proxy_user = proxy_config.get("username", "")
                proxy_pass = proxy_config.get("password", "")
                if proxy_user and proxy_pass:
                    proxy = f"http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}"
                else:
                    proxy = f"http://{proxy_host}:{proxy_port}"
        except Exception as e:
            print(f"Could not load proxy from config: {e}")

    # Choose user_data_dir after proxy is determined so we can use a temporary
    # profile when no proxy is configured (avoids inherited system/profile proxy settings).
    if user_data_dir is None:
        if proxy is None:
            import tempfile
            user_data_dir = tempfile.mkdtemp()
            print(f"No proxy configured and no user_data_dir specified — using temporary profile: {user_data_dir}")
        else:
            user_data_dir = get_user_data_dir()

    # Check if CDP is already available (Chrome running with debug flag)
    if is_cdp_available(debug_port):
        print(f"CDP already available on port {debug_port}")

        # Inject stealth scripts if enabled
        if stealth_mode:
            from stealth import inject_stealth_scripts
            inject_stealth_scripts(debug_port)

        if url:
            # Navigate to URL in existing tab via CDP
            print(f"Navigating to: {url}")
            _navigate_via_cdp(url, debug_port)
        return None

    # Check if Chrome is running without CDP
    if is_chrome_running():
        if force_restart:
            print("Chrome is running without CDP. Restarting with debugging enabled...")
            kill_chrome()
            time.sleep(1)  # Wait for Chrome to fully close
        else:
            print("Warning: Chrome is running without CDP. CDP features will not work.")

    args = [
        chrome_path,
        f"--user-data-dir={user_data_dir}",
        f"--profile-directory={profile}",
        f"--remote-debugging-port={debug_port}",
        "--remote-allow-origins=*",
        "--start-maximized",
        "--no-sandbox",  # Required when running as root on Linux
    ]

    # Add proxy if configured
    if proxy:
        sanitized_proxy, creds_removed = _sanitize_proxy_for_chrome(proxy)
        if creds_removed:
            print("Warning: Chrome does not support embedding credentials in --proxy-server; credentials were removed.")

        # Only add if we have a sanitized value
        if sanitized_proxy:
            args.append(f"--proxy-server={sanitized_proxy}")
            print(f"Using proxy: {sanitized_proxy}")
    else:
        # Ensure Chrome doesn't use any system proxy settings when no proxy is configured
        # This helps avoid ERR_PROXY_CONNECTION_FAILED when an unwanted system proxy is present.
        args.append("--no-proxy-server")
        print("No proxy configured — launching with --no-proxy-server")

    # Add stealth mode flags
    if stealth_mode:
        args.extend([
            "--disable-blink-features=AutomationControlled",
            "--exclude-switches=enable-automation",
            "--disable-infobars",
            "--disable-dev-shm-usage",
            "--blink-settings=imagesEnabled=false",
        ])

    if url:
        args.append(url)

    print(f"Launching Chrome with profile: {profile}")
    print(f"User data dir: {user_data_dir}")
    print(f"Debug port: {debug_port}")
    if url:
        print(f"Navigating to: {url}")

    process = subprocess.Popen(args)
    
    # Wait for CDP to be available
    print("Waiting for Chrome to start...")
    start_time = time.time()
    while time.time() - start_time < 10:  # 10 second timeout
        if is_cdp_available(debug_port):
            print(f"Chrome is ready and CDP is available on port {debug_port}")

            # Inject stealth scripts before navigation
            if stealth_mode:
                print("Injecting stealth scripts...")
                from stealth import inject_stealth_scripts
                inject_stealth_scripts(debug_port)

            if url:
                 print(f"Navigating to: {url}")
                 # Add a small delay for browser to be truly ready for navigation
                 time.sleep(1)
                 _navigate_via_cdp(url, debug_port)
            return process
        time.sleep(0.5)

    print(f"Warning: Chrome launched but CDP port {debug_port} is not responding after 10s")
    return process


def _navigate_via_cdp(url: str, port: int = DEFAULT_DEBUG_PORT) -> bool:
    """Navigate to URL via CDP in existing browser."""
    import urllib.parse

    ws_url = get_cdp_websocket_url(port)
    if not ws_url:
        return False

    try:
        from websocket import create_connection
        ws = create_connection(ws_url, timeout=5)
        ws.send(json.dumps({
            "id": 1,
            "method": "Page.navigate",
            "params": {"url": url}
        }))
        ws.recv()  # Wait for response
        ws.close()
        return True
    except Exception as e:
        print(f"Failed to navigate via CDP: {e}")
        return False


def get_cdp_websocket_url(port: int = DEFAULT_DEBUG_PORT) -> str | None:
    """Get the WebSocket URL for CDP connection."""
    try:
        with urllib.request.urlopen(f"http://localhost:{port}/json") as response:
            tabs = json.loads(response.read().decode())
            if tabs:
                return tabs[0].get("webSocketDebuggerUrl")
    except Exception:
        return None
    return None


def get_cookies_via_cdp(port: int = DEFAULT_DEBUG_PORT) -> list[dict]:
    """
    Get all cookies from Chrome via CDP HTTP endpoint.

    Args:
        port: Remote debugging port

    Returns:
        List of cookie dictionaries
    """
    try:
        with urllib.request.urlopen(f"http://localhost:{port}/json") as response:
            tabs = json.loads(response.read().decode())

        if not tabs:
            return []

        return []
    except Exception as e:
        print(f"Error getting cookies: {e}")
        return []


def is_cdp_available(port: int = DEFAULT_DEBUG_PORT) -> bool:
    """Check if CDP is available on the given port."""
    try:
        with urllib.request.urlopen(f"http://localhost:{port}/json/version", timeout=2) as response:
            return response.status == 200
    except Exception:
        return False



def get_element_coordinates_node(selector: str, port: int = DEFAULT_DEBUG_PORT) -> Optional[Tuple[int, int]]:
    """
    Get element coordinates using Node.js and Puppeteer.
    
    Args:
        selector: CSS selector
        port: Debug port
        
    Returns:
        (x, y) tuple or None if not found
    """
    script_path = os.path.join(os.path.dirname(__file__), "js", "locate.js")
    
    # Check if node is available
    try:
        subprocess.run(["node", "-v"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: Node.js is not installed or not in PATH")
        return None

    try:
        result = subprocess.run(
            ["node", script_path, str(port), selector],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode != 0:
            print(f"Node script failed: {result.stderr}")
            return None
            
        try:
            data = json.loads(result.stdout)
            if "error" in data:
                print(f"Node script error: {data['error']}")
                return None
            
            # Extract metrics
            x_viewport = data["x"]
            y_viewport = data["y"]
            dpr = data.get("dpr", 1.0)
            screen_x = data.get("screenX", 0)
            screen_y = data.get("screenY", 0)
            outer_height = data.get("outerHeight", 0)
            inner_height = data.get("innerHeight", 0)
            
            # Calculate UI height (toolbar, tabs)
            # This is an approximation. On Windows, standard Chrome UI is often ~80-120px depending on scaling.
            # outerHeight includes window borders, but screenY is usually top-left of window inclusive of borders.
            # Content starts at screenY + ui_height.
            # ui_height ~= outerHeight - innerHeight.
            # However, this also includes bottom border and side borders in width.
            
            ui_height = outer_height - inner_height
            
            # Calculate final screen coordinates
            # Puppeteer viewport stats are in CSS pixels (logical).
            # window metrics (screenX, etc) are also often logical or physical depending on browser version,
            # but usually consistent with each other.
            # PyAutoGUI expects PHYSICAL coordinates on Windows if high-dpi aware, or logical if not.
            # Given previous logs showing 2560x1600 (Physical) and 1707x1067 (Logical), PyAutoGUI sees 
            # Physical pixels, so we must scale up from Logical.
            
            # Formula: (ScreenOffset + ElementOffset) * DPR
            
            final_x = int((screen_x + x_viewport) * dpr)
            final_y = int((screen_y + ui_height + y_viewport) * dpr)
            
            # Adjustment: innerHeight might not account for side borders exactly, so centering is safer?
            # actually usually: screenX + border_width + viewport_x.
            # Simplification: assume screenX is accurate for left edge of content area if maximized?
            # No, screenX is left edge of window.
            # Side border width approx: (outerWidth - innerWidth) / 2
            
            outer_width = data.get("outerWidth", 0)
            inner_width = data.get("innerWidth", 0)
            border_width = (outer_width - inner_width) / 2
            
            final_x = int((screen_x + border_width + x_viewport) * dpr)
            
            print(f"Coords: Viewport({x_viewport}, {y_viewport}) -> Screen({final_x}, {final_y}) [DPR: {dpr}]")
            
            return (final_x, final_y)
        except json.JSONDecodeError:
            print(f"Failed to parse Node script output: {result.stdout}")
            return None
            
    except Exception as e:
        print(f"Error calling Node script: {e}")
        return None


if __name__ == "__main__":
    launch_chrome()
