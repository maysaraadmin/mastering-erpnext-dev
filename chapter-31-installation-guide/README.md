# Chapter 31: Installation Guide — Frappe, ERPNext & Docker

## Overview

This chapter covers all installation methods: bare-metal Ubuntu setup, Docker production deployment, Docker development containers (devcontainers), and app boilerplate initialization.

---

## 1. Bare-Metal Installation (Ubuntu)

### Prerequisites

```bash
# 1. Update system
sudo apt-get update -y
sudo apt-get upgrade -y
sudo reboot

# 2. Install Git
sudo apt-get install git

# 3. Install Python
sudo apt-get install python3-dev python3.10-dev python3-setuptools python3-pip python3-distutils
sudo apt-get install python3.10-venv
sudo apt-get install software-properties-common

# 4. Install MariaDB
sudo apt install mariadb-server mariadb-client
sudo mysql_secure_installation
```

When running `mysql_secure_installation`:
```
Enter current password for root: (leave empty)
Switch to unix_socket authentication [Y/n]: Y
Change the root password? [Y/n]: Y
Remove anonymous users? [Y/n]: Y
Disallow root login remotely? [Y/n]: N
Remove test database? [Y/n]: Y
Reload privilege tables? [Y/n]: Y
```

```bash
# 5. Configure MariaDB for UTF8
sudo nano /etc/mysql/my.cnf
```

Add at the end of `/etc/mysql/my.cnf`:
```ini
[mysqld]
character-set-client-handshake = FALSE
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci

[mysql]
default-character-set = utf8mb4
```

```bash
sudo service mysql restart

# 6. Install Redis
sudo apt-get install redis-server

# 7. Install other dependencies
sudo apt-get install xvfb libfontconfig wkhtmltopdf
sudo apt-get install libmysqlclient-dev
sudo apt install curl

# 8. Install Node.js via NVM
curl https://raw.githubusercontent.com/creationix/nvm/master/install.sh | bash
source ~/.profile
nvm install 18

# 9. Install NPM and Yarn
sudo apt-get install npm
sudo npm install -g yarn

# 10. Install Frappe Bench
sudo pip3 install frappe-bench
```

### Initialize Bench and Create Site

```bash
# Initialize bench (replace version-16 with your target version)
bench init --frappe-branch version-16 frappe-bench
cd /home/frappe-user/frappe-bench

# Create new site
bench new-site mysite.local

# Enable scheduler
bench --site mysite.local enable-scheduler

# Disable maintenance mode
bench --site mysite.local set-maintenance-mode off

# Enable server scripts
bench --site mysite.local set-config server_script_enabled true

# Enable developer mode (development only)
bench set-config -g developer_mode true

# Add site to hosts (local dev)
bench --site mysite.local add-to-hosts

# Start server
bench start
```

Access at: `http://mysite.local:8000` or `http://localhost:8000`

### Install ERPNext

```bash
bench get-app erpnext --branch version-16
bench --site mysite.local install-app erpnext
bench --site mysite.local migrate
```

---

## 2. Docker Production Deployment (frappe_docker)

### Quick Start with pwd.yml

```bash
# Clone frappe_docker
git clone https://github.com/frappe/frappe_docker
cd frappe_docker

# Start with the default configuration
docker compose -f pwd.yml up -d

# Monitor site creation
docker logs frappe_docker-create-site-1 -f
```

Access at: `http://localhost:8080`

### Custom App Docker Image

**Step 1: Create apps.json**

```json
[
  {
    "url": "https://github.com/frappe/erpnext",
    "branch": "version-16"
  },
  {
    "url": "https://github.com/your-username/your-custom-app",
    "branch": "main"
  }
]
```

For private repos:
```json
[
  {
    "url": "https://YOUR_PAT@github.com/your-org/private-app.git",
    "branch": "main"
  }
]
```

**Step 2: Build the image**

```bash
# Encode apps.json
export APPS_JSON_BASE64=$(base64 -w 0 apps.json)

# Verify encoding
echo -n ${APPS_JSON_BASE64} | base64 -d > apps-test.json
cat apps-test.json

# Build image
docker build \
  --no-cache \
  --progress=plain \
  --build-arg FRAPPE_BRANCH=version-16 \
  --build-arg APPS_JSON_BASE64=$APPS_JSON_BASE64 \
  --file images/layered/Containerfile \
  --tag your-dockerhub-username/frappe-custom:latest \
  .
```

**Step 3: Push to Docker Hub**

```bash
# Login (use Personal Access Token, not password)
docker login -u your-dockerhub-username

# Push
docker push your-dockerhub-username/frappe-custom:latest
```

**Step 4: Run with custom image**

Edit `pwd.yml` — replace all `frappe/erpnext:v16.x.x` with your image:
```yaml
image: your-dockerhub-username/frappe-custom:latest
```

Update the site creation command:
```yaml
command: >-
  --install-app erpnext --install-app your_custom_app
```

```bash
docker compose -f pwd.yml up -d
```

---

## 3. Docker Compose Deep Dive

### Understanding the Frappe Stack

Frappe requires these services working together:

```
┌─────────────────────────────────────────────────────┐
│  frappe_docker services                             │
├─────────────────────────────────────────────────────┤
│  frontend    → Nginx (port 8080) + static files     │
│  backend     → Gunicorn (Python app server)         │
│  websocket   → Socket.IO (real-time)                │
│  queue-short → Background worker (short jobs)       │
│  queue-long  → Background worker (long jobs)        │
│  scheduler   → Cron-like task scheduler             │
│  db          → MariaDB                              │
│  redis-cache → Redis (caching)                      │
│  redis-queue → Redis (job queue)                    │
└─────────────────────────────────────────────────────┘
```

### Minimal docker-compose.yml

```yaml
version: "3.8"

x-customizable-image: &customizable_image
  image: ${CUSTOM_IMAGE:-frappe/erpnext}:${CUSTOM_TAG:-v16.0.0}
  restart: ${RESTART_POLICY:-unless-stopped}

x-backend-defaults: &backend_defaults
  <<: *customizable_image
  volumes:
    - sites:/home/frappe/frappe-bench/sites
    - logs:/home/frappe/frappe-bench/logs

services:
  configurator:
    <<: *backend_defaults
    restart: on-failure
    entrypoint: ["bash", "-c"]
    command: >
      ls -1 apps > sites/apps.txt;
      bench set-config -g db_host $DB_HOST;
      bench set-config -g redis_cache "redis://$REDIS_CACHE";
      bench set-config -g redis_queue "redis://$REDIS_QUEUE";
      bench set-config -g redis_socketio "redis://$REDIS_QUEUE";
    environment:
      DB_HOST: ${DB_HOST:-db}
      REDIS_CACHE: ${REDIS_CACHE:-redis-cache:6379}
      REDIS_QUEUE: ${REDIS_QUEUE:-redis-queue:6379}
    depends_on:
      db:
        condition: service_healthy

  backend:
    <<: *backend_defaults
    depends_on:
      configurator:
        condition: service_completed_successfully

  frontend:
    <<: *customizable_image
    command: nginx-entrypoint.sh
    environment:
      BACKEND: backend:8000
      SOCKETIO: websocket:9000
      FRAPPE_SITE_NAME_HEADER: ${FRAPPE_SITE_NAME_HEADER:-$$host}
    volumes:
      - sites:/home/frappe/frappe-bench/sites
    ports:
      - "${HTTP_PUBLISH_PORT:-8080}:8080"
    depends_on:
      - backend
      - websocket

  websocket:
    <<: *backend_defaults
    command: node /home/frappe/frappe-bench/apps/frappe/socketio.js

  queue-short:
    <<: *backend_defaults
    command: bench worker --queue short,default

  queue-long:
    <<: *backend_defaults
    command: bench worker --queue long,default,short

  scheduler:
    <<: *backend_defaults
    command: bench schedule

  db:
    image: mariadb:10.6
    healthcheck:
      test: mysqladmin ping -h localhost --password=${DB_PASSWORD:-123}
      interval: 1s
      retries: 20
    environment:
      MYSQL_ROOT_PASSWORD: ${DB_PASSWORD:-123}
    volumes:
      - db-data:/var/lib/mysql

  redis-cache:
    image: redis:6.2-alpine

  redis-queue:
    image: redis:6.2-alpine

volumes:
  db-data:
  sites:
  logs:
```

### Key Docker Compose Concepts

**Dependency conditions:**
- `service_started` — container started (default)
- `service_healthy` — healthcheck passed
- `service_completed_successfully` — ran and exited 0

**Restart policies:**
- `unless-stopped` — restart unless manually stopped (recommended)
- `on-failure` — restart only on failure (for one-time jobs like configurator)
- `always` — always restart

**Volume types:**
- Named volumes (`sites:`) — Docker-managed, portable, for production
- Bind mounts (`./sites:/path`) — host directory, for development

---

## 4. Dev Containers (VS Code)

Dev Containers let you develop inside a Docker container with VS Code, giving everyone the same environment.

### Setup

```bash
# 1. Clone frappe_docker
git clone https://github.com/frappe/frappe_docker.git
cd frappe_docker

# 2. Copy devcontainer config
cp -R devcontainer-example .devcontainer
cp -R development/vscode-example development/.vscode

# 3. Open in VS Code
code .
```

In VS Code:
1. Install extension: `ms-vscode-remote.remote-containers`
2. Press `Ctrl+Shift+P` → `Dev Containers: Reopen in Container`
3. Wait 5-10 minutes for first build

### Inside the Container

```bash
# Initialize bench
bench init --skip-redis-config-generation frappe-bench
cd frappe-bench

# Configure connections
bench set-config -g db_host mariadb
bench set-config -g redis_cache redis://redis-cache:6379
bench set-config -g redis_queue redis://redis-queue:6379
bench set-config -g redis_socketio redis://redis-queue:6379

# Create site
bench new-site \
  --db-root-password 123 \
  --admin-password admin \
  --mariadb-user-host-login-scope=% \
  mysite.localhost

# Install ERPNext
bench get-app erpnext
bench --site mysite.localhost install-app erpnext

# Start server
bench start
```

Access at: `http://development.localhost:8000`

### devcontainer.json Reference

```json
{
  "name": "Frappe Bench",
  "dockerComposeFile": "./docker-compose.yml",
  "service": "frappe",
  "workspaceFolder": "/workspace/development",
  "shutdownAction": "stopCompose",
  "remoteUser": "frappe",
  "forwardPorts": [8000, 9000, 6787],
  "mounts": [
    "source=${localEnv:HOME}${localEnv:USERPROFILE}/.ssh,target=/home/frappe/.ssh,type=bind,consistency=cached"
  ],
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.python",
        "ms-vscode.live-server",
        "mtxr.sqltools",
        "visualstudioexptteam.vscodeintellicode"
      ],
      "settings": {
        "terminal.integrated.defaultProfile.linux": "bash",
        "debug.node.autoAttach": "disabled"
      }
    }
  }
}
```

### Common Dev Container Errors

**`NameError: name 'null' is not defined`**
```bash
bench clear-cache
# Or try a different browser
```

**`Cannot find module 'superagent'`**
```bash
bench setup requirements
```

**`ValueError: id must not contain ":"`**
```bash
# Update to latest Frappe version
bench update --reset
```

---

## 5. App Boilerplate Setup

### Create New App

```bash
bench new-app your-app-name
# Fill in: title, description, publisher, email, license
```

### Professional App Structure

```
your_app/
├── your_app/
│   ├── __init__.py          # Version + constants import
│   ├── hooks.py             # Frappe hooks
│   ├── constants.py         # App constants
│   ├── modules.txt          # Module list
│   ├── patches.txt          # Migration patches
│   ├── api/
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── main.py
│   ├── public/
│   │   ├── js/
│   │   ├── css/
│   │   └── images/branding/
│   │       ├── logo.png
│   │       └── favicon.png
│   ├── templates/
│   ├── translations/
│   │   └── ar.csv
│   └── utils/
│       └── install.py
├── setup.py
├── requirements.txt
├── CHANGELOG.md
└── README.md
```

### `__init__.py`

```python
from .constants import *

__version__ = "0.1.0"
```

### `constants.py`

```python
APP_NAME = "Your App Name"
APP_VERSION = "0.1.0"

ERRORS = {
    "no_permission": "Insufficient permissions",
    "not_found": "Record not found",
}

DEFAULT_PAGE_SIZE = 20
MAX_UPLOAD_SIZE = 10485760  # 10MB
API_VERSION = "v1"
```

### `setup.py`

```python
from setuptools import setup, find_packages
from your_app import __version__ as version

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

setup(
    name="your_app",
    version=version,
    description="Your app description",
    author="Your Organization",
    author_email="your@email.com",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires,
)
```

### `utils/install.py`

```python
import frappe

def after_install():
    set_app_logo()
    set_system_settings()
    set_navbar_settings()

def after_migrate():
    set_app_logo()
    set_system_settings()

def set_app_logo():
    app_logo = frappe.get_hooks("app_logo_url")[-1]
    frappe.db.set_single_value("Navbar Settings", "app_logo", app_logo)

def set_system_settings():
    settings = frappe.get_doc("System Settings")
    settings.session_expiry = "12:00"
    settings.save()

def set_navbar_settings():
    settings = frappe.get_doc("Navbar Settings")
    settings.logo_width = "35"
    settings.save()
```

### `hooks.py` branding section

```python
app_logo_url = "/assets/your_app/images/branding/logo.png"

website_context = {
    "favicon": "/assets/your_app/images/branding/favicon.png",
    "splash_image": "/assets/your_app/images/branding/logo.png",
}

after_install = "your_app.utils.install.after_install"
after_migrate = "your_app.utils.install.after_migrate"
```

### Git Workflow

```bash
# Initial commit to dev branch
git add .
git commit -m "feat: initial project setup"
git branch -M dev
git remote add upstream https://github.com/your-org/your-app.git
git push upstream dev

# Create staging branch
git checkout -b staging
git push upstream staging
```

**Branch strategy:**
```
dev → staging → main
```
- `dev`: active development
- `staging`: QA/testing
- `main`: production-ready

---

## 6. Disabling Onboarding

New users often get redirected to onboarding even when disabled in System Settings. This is because Frappe has multiple onboarding layers.

### Complete Disable

```python
# In your app's install.py or a patch
import frappe

def disable_all_onboarding():
    # 1. System-wide toggle
    frappe.db.set_single_value("System Settings", "enable_onboarding", 0)

    # 2. Clear per-user status
    users = frappe.get_all("User", filters={"enabled": 1}, pluck="name")
    for user in users:
        frappe.db.set_value("User", user, "onboarding_status", "{}")
        frappe.cache.hdel("bootinfo", user)

    # 3. Mark all module onboardings complete
    for module in frappe.get_all("Module Onboarding", pluck="name"):
        frappe.db.set_value("Module Onboarding", module, "is_complete", 1)

    # 4. Disable form tours
    for tour in frappe.get_all("Form Tour", pluck="name"):
        frappe.db.set_value("Form Tour", tour, "ui_tour", 0)

    frappe.db.commit()
```

### Hook for New Users

```python
# hooks.py
doc_events = {
    "User": {
        "after_insert": "your_app.utils.user.disable_user_onboarding"
    }
}
```

```python
# your_app/utils/user.py
def disable_user_onboarding(doc, method):
    if not doc.enabled:
        return
    frappe.db.set_value("User", doc.name, "onboarding_status", "{}")
    frappe.cache.hdel("bootinfo", doc.name)
    frappe.db.commit()
```

### SQL Approach

```sql
-- Disable system onboarding
UPDATE `tabSingles`
SET `value` = '0'
WHERE `doctype` = 'System Settings' AND `field` = 'enable_onboarding';

-- Clear all user onboarding status
UPDATE `tabUser` SET `onboarding_status` = '{}' WHERE `enabled` = 1;

-- Mark all module onboardings complete
UPDATE `tabModule Onboarding` SET `is_complete` = 1;
```

---

## 7. After Container Restart (frappe_docker)

Apps and Python paths can be lost after container restart. Fix with:

```powershell
# Windows PowerShell (fix-after-restart.ps1)
docker exec -u root frappe_docker-backend-1 `
    pip install -e /home/frappe/frappe-bench/apps/your_app

docker exec frappe_docker-backend-1 `
    bench --site frontend migrate

docker restart frappe_docker-backend-1 frappe_docker-queue-short-1 frappe_docker-queue-long-1
```

---

## Quick Reference

| Task | Command |
|---|---|
| Create site | `bench new-site mysite.local` |
| Install app | `bench --site mysite install-app appname` |
| Migrate | `bench --site mysite migrate` |
| Clear cache | `bench --site mysite clear-cache` |
| Build assets | `bench build` |
| Start dev server | `bench start` |
| Run tests | `bench --site mysite run-tests appname` |
| Backup | `bench --site mysite backup` |
| Console | `bench --site mysite console` |
| Enable dev mode | `bench set-config -g developer_mode true` |
| List sites | `bench list-sites` |
| Drop site | `bench drop-site mysite.local` |
