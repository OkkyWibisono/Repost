"""
CDP-based element finding and coordinate extraction.
"""

import json
import time
from typing import Tuple, Optional
from websocket import create_connection, WebSocketTimeoutException

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from browser import get_cdp_websocket_url, DEFAULT_DEBUG_PORT


def get_element_coordinates(
    selector: str,
    selector_type: str = "css",
    port: int = DEFAULT_DEBUG_PORT,
    timeout: float = 10.0
) -> Optional[Tuple[int, int]]:
    """
    Get the center coordinates of an element using CDP.

    Args:
        selector: CSS selector, XPath, or data-testid value
        selector_type: Type of selector - "css", "xpath", or "testid"
        port: CDP debug port
        timeout: Maximum time to wait for element

    Returns:
        Tuple of (x, y) center coordinates, or None if not found
    """
    ws_url = get_cdp_websocket_url(port)
    if not ws_url:
        print("Could not get CDP WebSocket URL")
        return None

    try:
        ws = create_connection(ws_url, timeout=timeout)
    except Exception as e:
        print(f"Failed to connect to CDP WebSocket: {e}")
        return None

    message_id = 0

    def send_command(method: str, params: dict = None) -> dict:
        nonlocal message_id
        message_id += 1
        msg = {"id": message_id, "method": method}
        if params:
            msg["params"] = params
        ws.send(json.dumps(msg))

        # Wait for response with matching id
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                ws.settimeout(1.0)
                response = ws.recv()
                data = json.loads(response)
                if data.get("id") == message_id:
                    return data
            except WebSocketTimeoutException:
                continue
        return {"error": {"message": "Timeout waiting for response"}}

    try:
        # Enable DOM domain
        send_command("DOM.enable")

        # Build the appropriate selector
        if selector_type == "testid":
            css_selector = f'[data-testid="{selector}"]'
        elif selector_type == "xpath":
            # For XPath, we need to use a different approach
            css_selector = None
        else:
            css_selector = selector

        # Get document root
        doc_response = send_command("DOM.getDocument")
        if "error" in doc_response:
            print(f"Error getting document: {doc_response['error']}")
            return None

        root_node_id = doc_response.get("result", {}).get("root", {}).get("nodeId")
        if not root_node_id:
            print("Could not get document root")
            return None

        # Find the element
        if css_selector:
            query_response = send_command("DOM.querySelector", {
                "nodeId": root_node_id,
                "selector": css_selector
            })
        else:
            # XPath query
            query_response = send_command("DOM.performSearch", {
                "query": selector
            })
            if "result" in query_response:
                search_id = query_response["result"].get("searchId")
                if search_id and query_response["result"].get("resultCount", 0) > 0:
                    results = send_command("DOM.getSearchResults", {
                        "searchId": search_id,
                        "fromIndex": 0,
                        "toIndex": 1
                    })
                    node_ids = results.get("result", {}).get("nodeIds", [])
                    if node_ids:
                        query_response = {"result": {"nodeId": node_ids[0]}}

        if "error" in query_response:
            print(f"Error querying element: {query_response['error']}")
            return None

        node_id = query_response.get("result", {}).get("nodeId")
        if not node_id:
            print(f"Element not found: {selector}")
            return None

        # Get the box model for coordinates
        box_response = send_command("DOM.getBoxModel", {"nodeId": node_id})
        if "error" in box_response:
            print(f"Error getting box model: {box_response['error']}")
            return None

        box_model = box_response.get("result", {}).get("model", {})
        content = box_model.get("content", [])

        if len(content) < 8:
            print("Invalid box model data")
            return None

        # content is [x1, y1, x2, y2, x3, y3, x4, y4] for the 4 corners
        # Calculate center point
        x_coords = [content[0], content[2], content[4], content[6]]
        y_coords = [content[1], content[3], content[5], content[7]]

        center_x = int(sum(x_coords) / 4)
        center_y = int(sum(y_coords) / 4)

        return (center_x, center_y)

    finally:
        try:
            send_command("DOM.disable")
        except:
            pass
        ws.close()


def find_and_get_coordinates(
    selectors: list,
    port: int = DEFAULT_DEBUG_PORT,
    timeout: float = 10.0
) -> Optional[Tuple[int, int]]:
    """
    Try multiple selectors and return coordinates of the first match.

    Args:
        selectors: List of (selector, selector_type) tuples
        port: CDP debug port
        timeout: Maximum time to wait

    Returns:
        Tuple of (x, y) center coordinates, or None if none found
    """
    for selector, selector_type in selectors:
        coords = get_element_coordinates(selector, selector_type, port, timeout)
        if coords:
            return coords
    return None
