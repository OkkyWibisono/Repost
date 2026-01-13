# Celery + Redis Setup Guide

This guide explains how to set up Medusa with Celery and Redis for distributed task management.

## Overview

Medusa can run in two modes:
1. **HTTP Polling Mode** (default) - Polls an HTTP API endpoint every 5 seconds
2. **Celery Worker Mode** - Listens to Redis broker for real-time task distribution

## Prerequisites

### 1. Install Redis Server

**Windows:**
```bash
# Download Redis for Windows from:
# https://github.com/microsoftarchive/redis/releases

# Or use WSL2:
wsl --install
wsl
sudo apt update
sudo apt install redis-server
sudo service redis-server start
```

**Linux (Ubuntu):**
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis
sudo systemctl enable redis
```

**macOS:**
```bash
brew install redis
brew services start redis
```

### 2. Verify Redis is Running

```bash
redis-cli ping
# Should return: PONG
```

## Configuration

### 1. Update config.json

Add Redis configuration to your `config.json`:

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

**For remote Redis server:**
```json
{
  "agent_id": "vm-001",
  "redis": {
    "host": "redis.example.com",
    "port": 6379,
    "db": 0,
    "password": "your-redis-password"
  }
}
```

### 2. Install Python Dependencies

```bash
# Activate virtual environment
.\venv\Scripts\activate

# Install Celery with Redis support
pip install -r requirements.txt
```

## Running Medusa in Celery Mode

### Start as Celery Worker

```bash
python main.py --celery
```

This will:
1. Launch Chrome browser
2. Detect login status
3. Start Celery worker listening on queue: `medusa.{agent_id}`

### Alternative: Use Celery CLI directly

```bash
celery -A celery_config worker --loglevel=info --pool=solo -Q medusa.vm-001
```

**Note:** Use `--pool=solo` for Windows compatibility.

## Central Application Setup

### 1. Create Central Application

The central application sends tasks to Medusa agents. See `example_central_app.py` for a complete example.

**Basic Example:**

```python
from celery import Celery

# Connect to same Redis broker
app = Celery(
    "central",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

# Send task to specific agent
result = app.send_task(
    "medusa.execute_task",
    args=["x", "login", {}],
    queue="medusa.vm-001"  # Agent queue
)

# Wait for result
task_result = result.get(timeout=30)
print(task_result)
```

### 2. Available Tasks

#### Execute Platform Task
```python
result = app.send_task(
    "medusa.execute_task",
    args=["x", "post", {"text": "Hello World!"}],
    queue="medusa.vm-001"
)
```

#### Health Check
```python
result = app.send_task(
    "medusa.health_check",
    queue="medusa.vm-001"
)
```

#### Check Login Status
```python
result = app.send_task(
    "medusa.check_login_status",
    args=["x"],
    queue="medusa.vm-001"
)
```

#### Update Configuration
```python
result = app.send_task(
    "medusa.update_config",
    args=[{"api_endpoint": "https://new-api.com"}],
    queue="medusa.vm-001"
)
```

## Queue Naming Convention

Each Medusa agent listens to its own queue: `medusa.{agent_id}`

Examples:
- Agent `vm-001` → Queue `medusa.vm-001`
- Agent `vm-002` → Queue `medusa.vm-002`
- Agent `production-001` → Queue `medusa.production-001`

## Monitoring

### View Active Workers
```bash
celery -A celery_config inspect active
```

### View Registered Tasks
```bash
celery -A celery_config inspect registered
```

### Monitor Events in Real-time
```bash
celery -A celery_config events
```

### Check Queue Status
```bash
redis-cli
> LLEN medusa.vm-001  # Check queue length
> KEYS medusa.*       # List all Medusa queues
```

## Troubleshooting

### Worker Won't Start

**Error:** `ImportError: cannot import name 'celery_config'`
- **Solution:** Run from project root directory: `A:\medusa\`

**Error:** `kombu.exceptions.OperationalError: [Errno 10061] Connection refused`
- **Solution:** Ensure Redis server is running: `redis-cli ping`

### Tasks Not Executing

1. **Check worker is running:**
   ```bash
   celery -A celery_config inspect active
   ```

2. **Verify queue name matches agent_id:**
   - Agent ID in `config.json`: `vm-001`
   - Queue name should be: `medusa.vm-001`

3. **Check Redis connection:**
   ```bash
   redis-cli
   > PING
   ```

### Windows-Specific Issues

**Pool Errors:**
- Always use `--pool=solo` on Windows
- Celery multiprocessing pool has issues on Windows

**EventLoop Errors:**
- Use Python 3.8+ on Windows
- Run worker with `--pool=solo` flag

## Production Deployment

### Using Supervisor (Linux)

Create `/etc/supervisor/conf.d/medusa-worker.conf`:

```ini
[program:medusa-worker]
command=/path/to/venv/bin/python main.py --celery
directory=/path/to/medusa
user=medusa
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/medusa/worker.log
environment=DISPLAY=":0"
```

### Using systemd (Linux)

Create `/etc/systemd/system/medusa-worker.service`:

```ini
[Unit]
Description=Medusa Celery Worker
After=network.target redis.service

[Service]
Type=simple
User=medusa
WorkingDirectory=/path/to/medusa
Environment="DISPLAY=:0"
ExecStart=/path/to/venv/bin/python main.py --celery
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable medusa-worker
sudo systemctl start medusa-worker
sudo systemctl status medusa-worker
```

## Scaling

### Multiple Agents

Each agent runs independently with its own queue:

```bash
# Agent 1 (vm-001)
python main.py --celery

# Agent 2 (vm-002) - update config.json first
python main.py --celery
```

### Load Balancing

Send tasks to different agents from central app:

```python
agents = ["vm-001", "vm-002", "vm-003"]
tasks = [...]

for i, task in enumerate(tasks):
    agent = agents[i % len(agents)]  # Round-robin
    app.send_task(
        "medusa.execute_task",
        args=[task["platform"], task["task"], task["params"]],
        queue=f"medusa.{agent}"
    )
```

## Security

### Redis Authentication

Update `config.json`:
```json
{
  "redis": {
    "host": "localhost",
    "port": 6379,
    "db": 0,
    "password": "strong-password-here"
  }
}
```

### Redis ACL (Redis 6+)

```bash
# Create user for Medusa workers
redis-cli
> ACL SETUSER medusa on >password ~medusa.* +@all
```

### Network Security

- Use firewall rules to restrict Redis access
- Use TLS/SSL for Redis connections in production
- Consider VPN for multi-server deployments
