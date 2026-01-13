# Ubuntu 22.04 VPS Setup Guide (Headless)

Complete guide to deploy Medusa browser automation on a headless Ubuntu VPS.

## Prerequisites

- Ubuntu 22.04 LTS (fresh install)
- Root or sudo access
- Minimum 2GB RAM, 2 CPU cores recommended

---

## Step 1: System Update

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git wget curl unzip
```

## Step 2: Install Virtual Display (Xvfb) and VNC

```bash
# Install Xvfb and X11 dependencies for PyAutoGUI
sudo apt install -y xvfb x11-utils x11-xserver-utils \
    libxtst6 libxkbcommon0 libxrandr2 libxcomposite1 \
    libxdamage1 libxfixes3 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libgbm1 libasound2 libpangocairo-1.0-0 \
    libgtk-3-0 libxss1 fonts-liberation

# Install scrot (screenshot tool needed by PyAutoGUI)
sudo apt install -y scrot

# Install python3-tk (needed by PyAutoGUI)
sudo apt install -y python3-tk

# Install x11vnc to view the virtual display remotely
sudo apt install -y x11vnc
```

## Step 3: Install Python 3.10+

```bash
# Python 3.10 comes with Ubuntu 22.04
sudo apt install -y python3 python3-pip python3-venv python3-dev

# Verify
python3 --version
```

## Step 4: Install Node.js 18.x

```bash
# Add NodeSource repository
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -

# Install Node.js
sudo apt install -y nodejs

# Verify
node --version
npm --version
```

## Step 5: Install Google Chrome

```bash
# Download and install Chrome
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install -y ./google-chrome-stable_current_amd64.deb
rm google-chrome-stable_current_amd64.deb

# Verify
google-chrome --version
```

## Step 6: Clone the App

```bash
cd /root
git clone https://github.com/anplusdre/medusa.git
cd medusa
```

## Step 7: Set Up Python Environment

```bash
cd /root/medusa

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

## Step 8: Set Up Node.js Dependencies

```bash
cd /root/medusa/js
npm install
```

## Step 9: Configure the App

Edit `config.json` with your settings:

```bash
nano /root/medusa/config.json
```

Full config example:

```json
{
  "agent_id": "vm-001",
  "api_endpoint": "http://localhost:8000",
  "proxy": {
    "host": "your-proxy-host.com",
    "port": 8080,
    "username": "proxy-username",
    "password": "proxy-password"
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

**Note:** Leave `proxy.host` empty if not using a proxy.

## Step 10: Start Virtual Display and VNC

```bash
# Create Xauthority file (required)
touch /root/.Xauthority

# Kill any existing Xvfb
pkill Xvfb 2>/dev/null || true
rm -f /tmp/.X99-lock

# Start Xvfb with access control disabled
Xvfb :99 -screen 0 1920x1080x24 -ac &

# Set display environment variable
export DISPLAY=:99

# Verify display works
xdpyinfo | head -5

# Start VNC server to view the display remotely
x11vnc -display :99 -forever -nopw -listen 0.0.0.0 &
```

**Connect from your laptop:** Use a VNC viewer (RealVNC, TightVNC) and connect to `your-vps-ip:5900`

## Step 11: Run the App

```bash
cd /root/medusa
source venv/bin/activate
export DISPLAY=:99

# Run the app
python main.py --polling
```

Watch the Chrome browser in your VNC viewer!

---

## Quick Start Script

Create `/root/medusa/start.sh`:

```bash
#!/bin/bash
set -e

APP_DIR="/root/medusa"
DISPLAY_NUM=":99"

cd "$APP_DIR"
source venv/bin/activate

# Create Xauthority if missing
touch /root/.Xauthority

# Kill existing processes
pkill Xvfb 2>/dev/null || true
pkill x11vnc 2>/dev/null || true
rm -f /tmp/.X99-lock

# Start virtual display
Xvfb $DISPLAY_NUM -screen 0 1920x1080x24 -ac &
export DISPLAY=$DISPLAY_NUM

# Wait for Xvfb to initialize
sleep 2

# Verify display
if ! xdpyinfo >/dev/null 2>&1; then
    echo "ERROR: Xvfb failed to start"
    exit 1
fi

# Start VNC server
x11vnc -display $DISPLAY_NUM -forever -nopw -listen 0.0.0.0 &

echo "Display $DISPLAY_NUM ready"
echo "VNC available on port 5900"
echo "Starting Medusa..."

# Run app
python main.py --polling
```

Make it executable and run:

```bash
chmod +x /root/medusa/start.sh
/root/medusa/start.sh
```

---

## Run as Systemd Service (Production)

Create `/etc/systemd/system/medusa.service`:

```ini
[Unit]
Description=Medusa Browser Automation
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/medusa
Environment=DISPLAY=:99
Environment=HOME=/root

ExecStartPre=-/usr/bin/pkill -9 Xvfb
ExecStartPre=-/usr/bin/pkill -9 x11vnc
ExecStartPre=-/bin/rm -f /tmp/.X99-lock
ExecStartPre=/usr/bin/touch /root/.Xauthority
ExecStartPre=/usr/bin/Xvfb :99 -screen 0 1920x1080x24 -ac
ExecStartPre=/bin/sleep 2
ExecStartPre=/usr/bin/x11vnc -display :99 -forever -nopw -listen 0.0.0.0 -bg

ExecStart=/root/medusa/venv/bin/python main.py --polling

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable medusa
sudo systemctl start medusa

# Check status
sudo systemctl status medusa

# View logs
sudo journalctl -u medusa -f
```

---

## Run fake_api for Development

In a separate terminal/screen session:

```bash
cd /root/medusa
source venv/bin/activate
python fake_api.py
```

This starts the local task API on port 8000.

---

## Troubleshooting

### PyAutoGUI: No display / KeyError: 'DISPLAY'

```bash
# Always set DISPLAY before running
export DISPLAY=:99

# Check if Xvfb is running
ps aux | grep Xvfb
```

### Xlib.error.XauthError: ~/.Xauthority not found

```bash
touch /root/.Xauthority
```

### Server is already active for display 99

```bash
pkill Xvfb
rm -f /tmp/.X99-lock
Xvfb :99 -screen 0 1920x1080x24 -ac &
```

### Chrome: Running as root without --no-sandbox

This is already handled in `browser.py`. If you see this error, pull the latest code:

```bash
cd /root/medusa
git pull
```

### Chrome fails to launch

```bash
# Check Chrome dependencies
ldd $(which google-chrome) | grep "not found"

# Run Chrome manually to see errors
DISPLAY=:99 google-chrome --no-sandbox --disable-gpu https://google.com
```

### Cannot connect to VNC

```bash
# Check if x11vnc is running
ps aux | grep x11vnc

# Restart it
pkill x11vnc
x11vnc -display :99 -forever -nopw -listen 0.0.0.0 &

# Check firewall (allow port 5900)
sudo ufw allow 5900
```

### Port 9222 already in use (CDP)

```bash
# Kill existing Chrome
pkill -f chrome
```

---

## Optional: Install Redis (for Celery Production Mode)

```bash
sudo apt install -y redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Verify
redis-cli ping  # Should return PONG
```

Then run with Celery mode:

```bash
python main.py --celery
```
