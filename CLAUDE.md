# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Medusa is a Python-based browser automation system that uses PyAutoGUI for mouse/keyboard control and Chrome DevTools Protocol (CDP) for browser interaction. It's designed to run as an agent on virtual machines, executing tasks from an API or local task file.

## Key Architecture

### Main Execution Flow
The system follows a state-machine-like flow orchestrated by `main.py`:

1. **Browser Launch** (`browser.py`): Launches Chrome with CDP enabled on port 9222
2. **X Login Detection** (`action/x/login_detection.py`): Checks authentication via CDP cookies
3. **Random Idle Mouse Movements**: (`action/mouse/initial/initial.py`): Bezier curves, easing functions, jitter, overshoot
4. **Task Execution**: Loads platform-specific modules dynamically based on task type
5. **Task Distribution**: Two modes available:
   - **HTTP Polling Mode** (default): Polls API endpoint every 5 seconds *(development only)*
   - **Celery Worker Mode**: Listens to Redis broker for distributed task queue *(production)*

### Module Structure
- `main.py`: Entry point, orchestrates login detection and task polling loop
- `browser.py`: Chrome management and CDP communication via WebSocket singleton
- `config.py`: Config file management (accounts, credentials, status tracking)
- `action/{platform}/{task}.py`: Platform-specific task implementations

### Task System
Tasks are dynamically loaded using importlib:
- Format: `action.{platform}.{task}` (e.g., `action.x.login`, `action.instagram.navigate`)
- Valid platforms: `x`, `instagram`
- Valid tasks: `login`, `maintain`, `search`, `post`, `comment`, `reply`, `like`, `destroy`, `logout`, `navigate`
- Tasks can return `True` to signal success/keep browser running, or `False` for failure

### CDP Integration
The codebase uses two approaches for element interaction:

1. **Python CDP** (`browser.py` - `CDPSession` singleton):
   - WebSocket-based direct CDP communication
   - Methods: `send()`, `get_element_coordinates()`, `click_element()`
   - Used for basic DOM queries and interactions

2. **Node.js + Puppeteer** (`js/locate.js`):
   - More reliable for coordinate calculation with DPI scaling
   - Returns viewport coordinates + window metrics for PyAutoGUI conversion
   - Preferred method: `get_element_coordinates_node()` in `browser.py:421`

### Human-Like Automation
- `action/mouse/initial/initial.py`: Bezier curves, easing functions, jitter, overshoot
- All mouse movements use randomization for human-like behavior
- Typing includes variable delays (0.05-0.6s per character)

### Stealth Mode (Anti-Detection)
Enabled by default to avoid bot detection:

**Chrome Flags:**
- `--disable-blink-features=AutomationControlled` - Removes navigator.webdriver
- `--exclude-switches=enable-automation` - Disables automation extension
- `--disable-infobars` - Removes "Chrome is being controlled" message

**Script Injection (`stealth.py`):**
- `navigator.webdriver = false` - Primary detection bypass
- Realistic `navigator.plugins` and `navigator.mimeTypes`
- `window.chrome.runtime` object spoofing
- Removal of automation properties (`__webdriver_evaluate`, `_selenium`, etc.)
- Hardware properties normalization (hardwareConcurrency, deviceMemory)
- Uses `Page.addScriptToEvaluateOnNewDocument` to inject before page scripts run

**Disable Stealth Mode:**
```python
launch_chrome(url="https://example.com", stealth_mode=False)
```

### Page Load Detection
- `action/pageload/wait.py`: Network idle detection via CDP
- Monitors `Network.requestWillBeSent`, `Network.loadingFinished/Failed` events
- Default: 30s timeout, 0.5s idle time (configurable via `PageLoadConfig`)

### Configuration System
- `config.json`: Stores agent_id, API endpoint, Redis config, proxy, accounts (credentials + cookies + status)
- Status tracking: `logged_in` / `not_logged_in` auto-updated by login detection
- Platform mapping: `"x"` → `"twitter"` in config (see `config.py:7-13`)

### Celery Integration
The system supports distributed task management via Celery + Redis:

**Architecture:**
- `celery_config.py`: Celery app configuration with Redis broker/backend
- `celery_tasks.py`: Task definitions callable from central application
- Agent-specific queues: `medusa.{agent_id}` (e.g., `medusa.vm-001`)
- Each agent listens only to its own queue for targeted task assignment

**Available Tasks:**
1. `medusa.execute_task` - Execute platform task (login, post, like, etc.)
2. `medusa.health_check` - Verify agent responsiveness
3. `medusa.check_login_status` - Check login status for platform
4. `medusa.update_config` - Remotely update agent configuration

**Task Routing:**
- Tasks routed to specific agents via queue name: `medusa.{agent_id}`
- Central app sends tasks by specifying target agent's queue
- Workers use `pool="solo"` for Windows compatibility (avoids multiprocessing issues)
- Single concurrency (one task at a time) to prevent browser conflicts

## Common Development Commands

### Running the Application
```bash
# Activate virtual environment (Windows)
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run in HTTP polling mode (default)
python main.py
# OR
python main.py --polling

# Run as Celery worker (distributed task queue)
python main.py --celery

# Show help
python main.py --help
```

### Testing Individual Tasks
```bash
# Test login flow
python action/x/login.py

# Test login detection
python action/x/login_detection.py

# Test stealth mode (anti-detection)
python test_stealth.py

# Test without stealth mode (for comparison)
python test_stealth.py --no-stealth
```

### Node.js Dependencies
```bash
cd js
npm install  # Install puppeteer-core
```

### Python Dependencies
```bash
# Install from requirements.txt
pip install -r requirements.txt

# Or install core dependencies manually
pip install pyautogui websocket-client websockets "celery[redis]"
```

### Celery Development
```bash
# Test Celery configuration
python celery_config.py

# Run worker directly (alternative to main.py --celery)
celery -A celery_config worker --loglevel=info --pool=solo -Q medusa.vm-001

# Monitor tasks in real-time
celery -A celery_config events

# Test sending tasks from central app
python example_central_app.py
```

## Critical Implementation Details

### Element Location Strategy
Always use `get_element_coordinates_node()` (Node.js/Puppeteer) for element coordinates because:
- Handles DPI scaling correctly (physical vs logical pixels)
- Accounts for browser UI height (toolbar, tabs)
- Returns screen coordinates ready for PyAutoGUI

Formula (see `browser.py:487-500`):
```python
final_x = (screen_x + border_width + x_viewport) * dpr
final_y = (screen_y + ui_height + y_viewport) * dpr
```

### Login Flow Pattern (X/Twitter)
1. Detect login status via cookies (`auth_token`, `ct0`)
2. Click sign-in button with randomized offset
3. Enter username → press Escape (dismiss autofill) → click Next
4. Enter password with variable delays → click Login
5. Handle optional 2FA modal close
6. Update `config.json` status

### Task Development Pattern
New tasks should:
1. Create file: `action/{platform}/{task_name}.py`
2. Define function: `def {task_name}(**params) -> bool:`
3. Return `True` for success (keeps browser open), `False` for failure
4. Use `wait_for_network_idle()` after navigation
5. Randomize click positions: `offset_x = random.randint(-40, 40)`
6. Use `human_move_with_overshoot()` for mouse movement

### Browser State Management
- Browser data stored in `.medusa_browser_data/` (separate from system Chrome)
- CDP singleton maintains single WebSocket connection (auto-reconnect on disconnect)
- Tab switching: `action/tab_switcher.py` creates new tabs via CDP

## API Integration

### Development vs Production

| Mode | Use Case | Scaling |
|------|----------|---------|
| HTTP Polling + `fake_api.py` | Local development/testing | Poor (1000 VMs = 200 req/s constant load) |
| Celery + Redis | Production deployment | Excellent (push-based, near-zero idle load) |

**Important:** `fake_api.py` is a local development stub only. For production with multiple VMs, always use Celery mode (`python main.py --celery`).

### HTTP Polling Mode (Development Only)
- **File:** `fake_api.py` - Simple FastAPI task queue for local testing
- Endpoint: `{api_endpoint}/tasks?agent_id={agent_id}`
- Returns: Task dict or None/404 if no task available
- Poll interval: 5 seconds (see `main.py:257`)
- Idle behavior: After 2 seconds without task, create blank tab
- **Not suitable for production** - polling creates constant server load that doesn't scale

### Celery Mode (Production)
**Configuration (config.json):**
```json
{
  "agent_id": "vm-001",
  "redis": {
    "host": "localhost",
    "port": 6379,
    "db": 0,
    "password": null
  }
}
```

**Sending Tasks from Central Application:**
```python
from celery import Celery

app = Celery(broker="redis://localhost:6379/0")

# Send task to specific agent
app.send_task(
    "medusa.execute_task",
    args=["x", "login", {}],
    queue="medusa.vm-001"
)
```

**Task Result Format:**
```json
{
  "success": true,
  "message": "Task x.login executed successfully",
  "task_id": "uuid-here",
  "platform": "x",
  "task": "login"
}
```

### Task Format (Both Modes)
```json
{
  "platform": "x",
  "task": "login",
  "enabled": true,
  "params": {}
}
```

## Windows-Specific Notes
- Uses `tasklist`/`taskkill` for Chrome process management
- Chrome paths checked: `%ProgramFiles%`, `%ProgramFiles(x86)%`, `%LocalAppData%`
- PyAutoGUI expects physical pixels on high-DPI displays
