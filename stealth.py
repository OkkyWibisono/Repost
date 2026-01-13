"""
Browser stealth mode - mask automation detection.
Injects scripts via CDP to hide webdriver and modify navigator properties.
"""

import json
import urllib.request
from typing import Optional


def get_stealth_scripts() -> list[str]:
    """
    Get list of JavaScript scripts to inject for stealth mode.

    Returns:
        List of JavaScript code strings to execute
    """
    scripts = []

    # 1. Override navigator.webdriver (CRITICAL - must be undefined, not false)
    scripts.append("""
        // Normal browsers have navigator.webdriver = undefined (not false!)
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });
    """)

    # 2. Override navigator.plugins and navigator.mimeTypes
    scripts.append("""
        // Make plugins array look real
        Object.defineProperty(navigator, 'plugins', {
            get: () => [
                {
                    0: {type: "application/pdf", suffixes: "pdf", description: "Portable Document Format"},
                    description: "Portable Document Format",
                    filename: "internal-pdf-viewer",
                    length: 1,
                    name: "Chrome PDF Plugin"
                },
                {
                    0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format"},
                    description: "Portable Document Format",
                    filename: "internal-pdf-viewer",
                    length: 1,
                    name: "Chrome PDF Viewer"
                },
                {
                    0: {type: "application/x-nacl", suffixes: "", description: "Native Client Executable"},
                    1: {type: "application/x-pnacl", suffixes: "", description: "Portable Native Client Executable"},
                    description: "Native Client",
                    filename: "internal-nacl-plugin",
                    length: 2,
                    name: "Native Client"
                }
            ],
        });

        Object.defineProperty(navigator, 'mimeTypes', {
            get: () => [
                {type: "application/pdf", suffixes: "pdf", description: "Portable Document Format"},
                {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format"},
                {type: "application/x-nacl", suffixes: "", description: "Native Client Executable"},
                {type: "application/x-pnacl", suffixes: "", description: "Portable Native Client Executable"}
            ],
        });
    """)

    # 3. Override chrome runtime
    scripts.append("""
        // Make chrome.runtime look real
        if (!window.chrome) {
            window.chrome = {};
        }
        if (!window.chrome.runtime) {
            window.chrome.runtime = {};
        }

        Object.defineProperty(window.chrome.runtime, 'connect', {
            get: () => undefined,
        });

        Object.defineProperty(window.chrome.runtime, 'sendMessage', {
            get: () => undefined,
        });
    """)

    # 4. Override permissions
    scripts.append("""
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({state: Notification.permission}) :
                originalQuery(parameters)
        );
    """)

    # 5. Override languages to look more natural
    scripts.append("""
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en'],
        });
    """)

    # 6. Override platform if needed
    scripts.append("""
        // Keep the original platform but make it configurable
        const originalPlatform = navigator.platform;
        Object.defineProperty(navigator, 'platform', {
            get: () => originalPlatform || 'Win32',
        });
    """)

    # 7. Remove automation-related properties from window
    scripts.append("""
        // Remove webdriver from window
        delete window.webdriver;

        // Remove common automation flags
        delete window._Selenium_IDE_Recorder;
        delete window._selenium;
        delete window.__webdriver_script_fn;
        delete window.__driver_evaluate;
        delete window.__webdriver_evaluate;
        delete window.__selenium_evaluate;
        delete window.__fxdriver_evaluate;
        delete window.__driver_unwrapped;
        delete window.__webdriver_unwrapped;
        delete window.__selenium_unwrapped;
        delete window.__fxdriver_unwrapped;
        delete window.__webdriver_script_func;
        delete window.__webdriver_script_function;
    """)

    # 8. Override hardwareConcurrency to a realistic value
    scripts.append("""
        Object.defineProperty(navigator, 'hardwareConcurrency', {
            get: () => 4,
        });
    """)

    # 9. Override deviceMemory to a realistic value
    scripts.append("""
        Object.defineProperty(navigator, 'deviceMemory', {
            get: () => 8,
        });
    """)

    # 10. Override connection properties
    scripts.append("""
        if (navigator.connection) {
            Object.defineProperty(navigator.connection, 'rtt', {
                get: () => 50,
            });
        }
    """)

    # 11. Override screen resolution to match common resolutions
    scripts.append("""
        // Make screen properties look realistic
        Object.defineProperty(screen, 'availWidth', {
            get: () => screen.width,
        });

        Object.defineProperty(screen, 'availHeight', {
            get: () => screen.height - 40, // Account for taskbar
        });
    """)

    # 12. Spoof timezone
    scripts.append("""
        // Keep original timezone but make it configurable
        const originalTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;

        // Override timezone offset if needed
        // const originalGetTimezoneOffset = Date.prototype.getTimezoneOffset;
        // Date.prototype.getTimezoneOffset = function() {
        //     return 300; // EST offset, customize as needed
        // };
    """)

    # 13. Hide automation in iframe checks
    scripts.append("""
        // Prevent iframe detection
        Object.defineProperty(HTMLIFrameElement.prototype, 'contentWindow', {
            get: function() {
                return window;
            }
        });
    """)

    # 14. Override toString methods to hide proxy
    scripts.append("""
        // Make all our overrides undetectable
        const originalToString = Function.prototype.toString;
        Function.prototype.toString = function() {
            if (this === navigator.webdriver.get ||
                this === navigator.plugins.get ||
                this === navigator.languages.get) {
                return 'function get() { [native code] }';
            }
            return originalToString.call(this);
        };
    """)

    return scripts


def inject_stealth_scripts(port: int = 9222) -> bool:
    """
    Inject stealth scripts into the browser via CDP.
    Must be called after browser launches but before navigating to target page.

    CRITICAL: Even with --disable-blink-features=AutomationControlled,
    some Chrome versions still leak navigator.webdriver = true.
    This function uses Page.addScriptToEvaluateOnNewDocument to inject
    the override BEFORE any page scripts run.

    Args:
        port: CDP debug port

    Returns:
        True if injection successful, False otherwise
    """
    try:
        # Get WebSocket URL
        with urllib.request.urlopen(f"http://localhost:{port}/json") as response:
            tabs = json.loads(response.read().decode())
            if not tabs:
                print("No tabs found for stealth injection")
                return False
            ws_url = tabs[0].get("webSocketDebuggerUrl")

        if not ws_url:
            print("Could not get WebSocket URL for stealth injection")
            return False

        # Connect to WebSocket
        from websocket import create_connection
        ws = create_connection(ws_url, timeout=10)

        # Get stealth scripts
        scripts = get_stealth_scripts()

        # Combine all scripts into one
        combined_script = "\n".join(scripts)

        # Inject using Page.addScriptToEvaluateOnNewDocument
        # This ensures the script runs before any page scripts
        message_id = 1
        command = {
            "id": message_id,
            "method": "Page.addScriptToEvaluateOnNewDocument",
            "params": {
                "source": combined_script
            }
        }

        ws.send(json.dumps(command))
        response = ws.recv()
        result = json.loads(response)

        ws.close()

        if "error" in result:
            print(f"Error injecting stealth scripts: {result['error']}")
            return False

        print("✓ Stealth scripts injected successfully")
        print(f"  - navigator.webdriver = undefined")
        print(f"  - Plugins/MimeTypes overridden")
        print(f"  - Automation properties removed")
        print(f"  - {len(scripts)} protection scripts loaded")

        # Also inject immediately for current page (backup/aggressive)
        immediate_override = """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
        """

        message_id += 1
        immediate_command = {
            "id": message_id,
            "method": "Runtime.evaluate",
            "params": {
                "expression": immediate_override
            }
        }

        ws = create_connection(ws_url, timeout=10)
        ws.send(json.dumps(immediate_command))
        ws.recv()
        ws.close()

        print("✓ Immediate override applied to current page")

        return True

    except Exception as e:
        print(f"Failed to inject stealth scripts: {e}")
        return False


def verify_stealth(port: int = 9222) -> dict:
    """
    Verify stealth mode is working by checking navigator properties.

    Args:
        port: CDP debug port

    Returns:
        Dictionary with verification results
    """
    try:
        from websocket import create_connection

        # Get WebSocket URL
        with urllib.request.urlopen(f"http://localhost:{port}/json") as response:
            tabs = json.loads(response.read().decode())
            if not tabs:
                return {"error": "No tabs found"}
            ws_url = tabs[0].get("webSocketDebuggerUrl")

        if not ws_url:
            return {"error": "Could not get WebSocket URL"}

        ws = create_connection(ws_url, timeout=10)

        # Check navigator.webdriver
        checks = {
            "webdriver": "navigator.webdriver",
            "plugins_length": "navigator.plugins.length",
            "languages": "JSON.stringify(navigator.languages)",
            "chrome_runtime": "typeof window.chrome !== 'undefined' && typeof window.chrome.runtime !== 'undefined'",
            "automation_flag": "window.__webdriver_evaluate || window.__selenium_evaluate || window._Selenium_IDE_Recorder"
        }

        results = {}
        message_id = 1

        for key, expression in checks.items():
            command = {
                "id": message_id,
                "method": "Runtime.evaluate",
                "params": {
                    "expression": expression,
                    "returnByValue": True
                }
            }

            ws.send(json.dumps(command))
            response = ws.recv()
            result = json.loads(response)

            if "result" in result and "result" in result["result"]:
                results[key] = result["result"]["result"].get("value")

            message_id += 1

        ws.close()

        return results

    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    # Test stealth injection
    print("Testing stealth script injection...")
    print("=" * 50)

    # Note: Browser must be running with CDP enabled
    success = inject_stealth_scripts()

    if success:
        print("\nVerifying stealth mode...")
        print("-" * 50)
        verification = verify_stealth()

        print("\nVerification Results:")
        for key, value in verification.items():
            print(f"  {key}: {value}")
