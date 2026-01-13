# Medusa Setup Guide

Step-by-step guide to install and run Medusa on your local machine.

## Prerequisites

Before starting, ensure you have the following installed:

| Software | Version | Download |
|----------|---------|----------|
| Python | 3.10+ | https://python.org/downloads |
| Node.js | 18+ | https://nodejs.org |
| Google Chrome | Latest | https://google.com/chrome |

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/medusa.git
cd medusa
```

### 2. Create Python Virtual Environment

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Node.js Dependencies

```bash
cd js
npm install
cd ..
```

### 5. Configure the Application

Copy the example config and edit with your credentials:

```bash
# Windows
copy config.example.json config.json

# macOS/Linux
cp config.example.json config.json
```

Edit `config.json` with your settings:

```json
{
   "agent_id": "your-agent-id",
   "api_endpoint": "http://localhost:8888",
   "redis": {
      "host": "localhost",
      "port": 6379,
      "db": 0,
      "password": null
   },
   "accounts": {
      "twitter": {
         "username": "your_username",
         "password": "your_password",
         "status": "not_logged_in"
      }
   }
}
```

## Running the Application

### Development Mode (HTTP Polling)

**Terminal 1** - Start the fake API server:
```bash
.\venv\Scripts\activate   # Windows
pip install fastapi uvicorn
python fake_api.py
```

**Terminal 2** - Start the automation:
```bash
.\venv\Scripts\activate   # Windows
python main.py --polling
```

**Terminal 3** (Optional) - Start the Dev GUI:
```bash
.\venv\Scripts\activate   # Windows
python dev_gui.py
```

### Production Mode (Celery + Redis)

Requires Redis server running.

```bash
# Start as Celery worker
python main.py --celery
```

## Development GUI

The Dev GUI (`dev_gui.py`) provides a terminal-style interface for testing tasks:

```bash
python dev_gui.py
```

Features:
- Select platform (x, instagram, tiktok)
- Select task (likepost, comment, login, etc.)
- Fill in parameters
- Send tasks to the automation

## Project Structure

```
medusa/
├── main.py              # Entry point
├── browser.py           # Chrome/CDP management
├── config.json          # Configuration (create from example)
├── config.py            # Config file management
├── fake_api.py          # Development API server
├── dev_gui.py           # Development GUI
├── stealth.py           # Anti-detection scripts
├── action/
│   ├── x/               # Twitter/X automation
│   │   ├── login.py
│   │   ├── login_detection.py
│   │   └── likes/
│   │       └── likepost.py
│   ├── instagram/       # Instagram automation
│   ├── mouse/           # Human-like mouse movement
│   ├── pageload/        # Page load detection
│   └── tab_switcher.py  # Tab management
├── js/
│   ├── package.json
│   └── locate.js        # Puppeteer element location
└── .medusa_browser_data/ # Chrome profile (auto-created)
```

## Common Commands

```bash
# Run in polling mode (default)
python main.py

# Run as Celery worker
python main.py --celery

# Launch in new terminal window
python main.py --new-window

# Show help
python main.py --help

# Test login detection
python action/x/login_detection.py

# Test stealth mode
python test_stealth.py
```

## Troubleshooting

### Chrome not found
Ensure Chrome is installed in the default location:
- Windows: `C:\Program Files\Google\Chrome\Application\chrome.exe`
- macOS: `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`

### CDP connection failed
- Check if Chrome is running with `--remote-debugging-port=9222`
- Kill existing Chrome processes and try again

### PyAutoGUI not clicking correctly
- Check your display scaling (DPI) settings
- Run with admin privileges on Windows

### Module not found errors
- Ensure virtual environment is activated
- Run `pip install -r requirements.txt` again

## Task Format

Tasks sent via API follow this format:

```json
{
   "platform": "x",
   "task": "likepost",
   "enabled": true,
   "params": {
      "username": "target_user",
      "post": "text to match in the post"
   }
}
```

### Available Tasks

| Task | Parameters | Description |
|------|------------|-------------|
| `login` | - | Login to platform |
| `logout` | - | Logout from platform |
| `likepost` | `username`, `post` | Like a specific post |
| `comment` | `username`, `post`, `comment` | Comment on a post |
| `findpost` | `username`, `post` | Find and navigate to a post |
| `search` | `query` | Search for content |
| `navigate` | `url` | Navigate to URL |

## Security Notes

- Never commit `config.json` with real credentials
- Use `.gitignore` to exclude sensitive files
- Browser data is stored in `.medusa_browser_data/` (excluded from git)
