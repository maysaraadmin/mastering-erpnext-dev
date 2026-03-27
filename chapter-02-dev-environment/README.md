# Chapter 2: The Professional Dev Environment

## 🎯 Learning Objectives

By the end of this chapter, you will master:

- **Why** Bench uses a multi-site architecture for development workflow
- **How** Bench commands work internally and when to use each
- **Professional Git workflow** for Frappe app development
- **Debugging and troubleshooting** techniques for complex issues
- **Performance optimization** of development environment
- **Production-ready** setup practices for team collaboration

## 📚 Chapter Topics

### 2.1 Understanding Bench Architecture

**Why Bench Uses Multi-Site Architecture**

Bench's multi-site architecture is a deliberate design choice that enables professional development workflows:

```python
# Bench's internal architecture (simplified)
class Bench:
    def __init__(self, bench_path):
        self.bench_path = bench_path
        self.sites_path = os.path.join(bench_path, 'sites')
        self.apps_path = os.path.join(bench_path, 'apps')
        self.config = self.load_bench_config()
    
    def get_sites(self):
        """Returns all sites in this bench"""
        return [d for d in os.listdir(self.sites_path) 
                if os.path.isdir(os.path.join(self.sites_path, d))]
    
    def use_site(self, site_name):
        """Set active site for operations"""
        self.active_site = site_name
        self.site_config = self.load_site_config(site_name)
```

**The Professional Development Workflow:**

| Environment | Purpose | Database | Configuration |
|-------------|---------|----------|---------------|
| **dev.local** | Active development | Separate | Developer mode enabled |
| **test.local** | Feature testing | Separate | Test data fixtures |
| **staging.local** | Pre-production | Separate | Production-like config |
| **prod.local** | Production | Separate | Production settings |

**Why This Architecture Works:**

1. **Isolation**: Each site has its own database and configuration
2. **Consistency**: Same codebase runs across all environments
3. **Safety**: Development doesn't affect testing or production
4. **Portability**: Easy to move between environments

#### Advanced Installation Strategies

**Production-Grade Setup:**
```bash
# 1. Create dedicated system user
sudo useradd -m -s /bin/bash frappe
sudo usermod -aG sudo frappe

# 2. Set up proper permissions
sudo chown -R frappe:frappe /opt/frappe
chmod 755 /opt/frappe

# 3. Install with production flags
bench init /opt/frappe/frappe-bench \
    --frappe-branch version-15 \
    --python python3.10 \
    --apps_path /opt/frappe/apps
```

**Docker-Based Development (for team consistency):**
```yaml
# docker-compose.dev.yml
version: '3.8'
services:
  frappe-dev:
    build:
      context: .
      dockerfile: Dockerfile.dev
    volumes:
      - ./apps:/home/frappe/apps
      - ./sites:/home/frappe/sites
      - ./config:/home/frappe/config
    environment:
      - FRAPPE_ENV=development
      - FRAPPE_LOG_LEVEL=DEBUG
    ports:
      - "8000:8000"
      - "9000:9000"
```

#### Understanding Bench's Internal Commands

**What Happens When You Run `bench new-app`:**

```python
# Simplified version of bench's new-app logic
def new_app(app_name, **kwargs):
    # 1. Validate app name
    if not re.match(r'^[a-zA-Z0-9_]+$', app_name):
        raise ValueError("Invalid app name")
    
    # 2. Create app directory structure
    app_path = create_app_structure(app_name)
    
    # 3. Generate standard files
    create_standard_files(app_path, app_name)
    
    # 4. Create Python package structure
    create_package_structure(app_path, app_name)
    
    # 5. Initialize Git repository
    init_git_repo(app_path)
    
    # 6. Add to bench's apps registry
    register_app_in_bench(app_name)
    
    return app_path
```

**What Happens When You Run `bench new-site`:**

```python
def new_site(site_name, **kwargs):
    # 1. Generate unique database name
    db_name = generate_db_name(site_name)
    
    # 2. Create database and user
    create_database(db_name, site_name)
    
    # 3. Install Frappe framework
    install_frappe_framework(site_name)
    
    # 4. Create site configuration
    create_site_config(site_name, db_name)
    
    # 5. Set up default admin user
    create_admin_user(site_name, kwargs.get('admin_password'))
    
    # 6. Initialize site data
    initialize_site_data(site_name)
    
    return site_name
```

### 2.2 Bench Commands Deep Dive

#### Understanding Command Categories

**Architecture Commands:**
```bash
# These commands modify the bench structure
bench init <bench-name>              # Initialize new bench
bench new-app <app-name>             # Create new app
bench get-app <app-url>              # Install app from repository
bench remove-app <app-name>          # Remove app from bench
```

**Site Management Commands:**
```bash
# These commands operate on specific sites
bench new-site <site-name>           # Create new site
bench use <site-name>                # Switch active site
bench --site <site-name> <command>    # Run command on specific site
bench drop-site <site-name>          # Delete site
```

**Development Commands:**
```bash
# These commands manage the development server
bench start                          # Start all services
bench restart                        # Restart all services
bench stop                           # Stop all services
bench --site <site-name> watch       # Watch for file changes
```

#### Advanced Command Usage

**Performance-Optimized App Development:**
```bash
# Install app with specific branch and options
bench get-app https://github.com/frappe/erpnext \
    --branch version-15 \
    --resolve-dependencies \
    --verbose

# Update with specific strategy
bench update --patch --no-backup --skip-app-restore

# Migrate with performance options
bench --site dev.local migrate \
    --skip-failing \
    --rebuild-website
```

**Production-Grade Site Management:**
```bash
# Create site with production settings
bench new-site prod.local \
    --admin-password "$(openssl rand -base64 32)" \
    --db-root-password "$(openssl rand -base64 32)" \
    --mariadb-root-username frappe \
    --mariadb-root-password "$(openssl rand -base64 32)"

# Backup with compression
bench --site prod.local backup \
    --compress \
    --with-files \
    --backup-path /backups/$(date +%Y%m%d)

# Restore with verification
bench --site prod.local restore \
    /backups/20231210_prod_local_20231210_120001.sql \
    --with-migrate
```

#### Understanding Command Internals

**How `bench start` Works:**
```python
# Simplified version of bench start logic
def start():
    # 1. Check system requirements
    check_system_requirements()
    
    # 2. Start Redis services
    start_redis_services()
    
    # 3. Start database service
    start_database_service()
    
    # 4. Start web server
    start_web_server()
    
    # 5. Start background workers
    start_background_workers()
    
    # 6. Start SocketIO server
    start_socketio_server()
    
    # 7. Verify all services are running
    verify_services_health()
```

**How `bench migrate` Works:**
```python
def migrate(site=None, app=None):
    # 1. Get list of pending migrations
    migrations = get_pending_migrations(site, app)
    
    # 2. Sort migrations by dependencies
    sorted_migrations = sort_by_dependencies(migrations)
    
    # 3. Execute migrations in order
    for migration in sorted_migrations:
        execute_migration(migration, site)
        
        # 4. Update migration status
        update_migration_status(migration, site)
    
    # 5. Rebuild assets if needed
    if assets_need_rebuild():
        rebuild_assets()
```

#### Troubleshooting with Bench Commands

**Debug Mode for Commands:**
```bash
# Enable verbose output
bench --verbose start

# Enable debug logging
bench --debug migrate

# Check what commands are available
bench --help

# Get detailed error information
bench --traceback new-site test.local
```

**Performance Analysis:**
```bash
# Time command execution
time bench --site dev.local migrate

# Monitor resource usage during command
bench --site dev.local start &
bench --site dev.local doctor
```

#### Custom Bench Commands

**Creating Custom Bench Commands:**
```python
# In your app's hooks.py
def after_app_install(app_name):
    """Custom command run after app installation"""
    if app_name == "my_custom_app":
        # Run custom setup
        setup_custom_features()

# Create custom bench command
@frappe.whitelist()
def custom_bench_command():
    """Custom bench command accessible via API"""
    return {
        "status": "success",
        "message": "Custom bench command executed"
    }
```

**Extending Bench Functionality:**
```bash
# Create custom bench script
cat > custom_bench.sh << 'EOF'
#!/bin/bash
# Custom bench operations

case "$1" in
    "setup-dev")
        bench new-site dev.local --admin-password admin
        bench --site dev.local install-app erpnext
        bench --site dev.local set-config developer_mode 1
        ;;
    "setup-test")
        bench new-site test.local --admin-password admin
        bench --site test.local install-app erpnext
        bench --site test.local set-config developer_mode 0
        ;;
    *)
        echo "Usage: $0 {setup-dev|setup-test}"
        exit 1
        ;;
esac
EOF

chmod +x custom_bench.sh
./custom_bench.sh setup-dev
```

### 2.3 Understanding Bench Directory Structure

```
frappe-bench/
├── apps/                    # Installed applications
│   ├── frappe/             # Frappe framework
│   ├── erpnext/           # ERPNext application
│   └── my_custom_app/      # Your custom apps
├── sites/                  # Site configurations
│   ├── site1.local/       # Site-specific files
│   │   ├── private/       # Private files
│   │   ├── public/        # Public files
│   │   └── site_config.json
│   └── assets/            # Shared assets
├── config/                # Bench configuration
│   ├── bench_config.json
│   ├── nginx.conf
│   └── supervisor.conf
├── logs/                  # Application logs
├── env/                   # Python virtual environment
└── redis/                 # Redis configuration
```

#### Key Files Explained

**`bench_config.json`**
```json
{
    "auto_update": false,
    "background_workers": 1,
    "dns_multitenant": false,
    "frappe_user": "frappe",
    "live_site": "your-site.com",
    "mail_server": "smtp.gmail.com",
    "maintenance_mode": 0,
    "max_file_size": 10485760,
    "redis_cache": "redis://localhost:13000",
    "redis_queue": "redis://localhost:13001",
    "restart_supervisor_on_update": false,
    "serve_default_site": true,
    "shallow_clone": true,
    "socketio_port": 9000,
    "update_bench_on_update": true,
    "webserver_port": 8000,
    "worker_count": 2
}
```

**`sites/site1.local/site_config.json`**
```json
{
    "db_name": "1bd2e3294da19198",
    "db_password": "your_password",
    "db_type": "mariadb",
    "enable_scheduler": true,
    "maintenance_mode": 0,
    "root_login": "administrator",
    "root_password": "your_admin_password"
}
```

### 2.4 Git Integration

#### Setting Up Version Control

**Initialize Git in Your App:**
```bash
cd apps/my_custom_app
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/your-username/my_custom_app.git
git push -u origin main
```

**Best Practices:**
```bash
# Create .gitignore
echo "env/" >> .gitignore
echo "sites/" >> .gitignore
echo "logs/" >> .gitignore

# Branch strategy
git checkout -b feature/new-doctype
git commit -am "Add new doctype"
git checkout main
git merge feature/new-doctype
```

### 2.5 Multiple Site Management

#### Development Workflow

**Create Development Sites:**
```bash
# Development site
bench new-site dev.local
bench --site dev.local install-app erpnext

# Testing site
bench new-site test.local
bench --site test.local install-app erpnext

# Staging site
bench new-site staging.local
bench --site staging.local install-app erpnext
```

**Site-Specific Configuration:**
```bash
# Switch between sites
bench use dev.local
bench use test.local

# Run commands on specific site
bench --site dev.local console
bench --site test.local migrate
```

#### Database Management

**Database Connections:**
```python
# In bench console
frappe.db.get_value('User', 'Administrator', 'email')
frappe.get_all('DocType', filters={'module': 'Core'})
```

**Backup and Restore:**
```bash
# Backup site
bench --site dev.local backup --with-files

# Restore from backup
bench --site dev.local restore /path/to/backup.sql
```

### 2.6 VS Code Configuration

#### Recommended Extensions

```json
{
    "recommendations": [
        "ms-python.python",
        "ms-python.flake8",
        "ms-python.black-formatter",
        "bradlc.vscode-tailwindcss",
        "formulahendry.auto-rename-tag",
        "ms-vscode.vscode-json",
        "redhat.vscode-yaml"
    ]
}
```

#### Workspace Settings

**`.vscode/settings.json`:**
```json
{
    "python.defaultInterpreterPath": "./env/bin/python",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "editor.formatOnSave": true,
    "files.exclude": {
        "**/__pycache__": true,
        "**/node_modules": true,
        "**/env": true
    },
    "search.exclude": {
        "**/env": true,
        "**/node_modules": true
    }
}
```

**`.vscode/launch.json`:**
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Bench Console",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/env/bin/bench",
            "args": ["--site", "dev.local", "console"],
            "console": "integratedTerminal",
            "cwd": "${workspaceFolder}"
        }
    ]
}
```

#### Debugging Setup

**Python Debugging:**
```python
# In your custom app code
import frappe
import pdb; pdb.set_trace()  # Breakpoint

# Or use frappe logger
frappe.logger().debug("Debug message")
```

**JavaScript Debugging:**
```javascript
// In client scripts
console.log("Debug:", frm.doc);
debugger; // Browser breakpoint
```

## 🛠️ Practical Exercises

### Exercise 2.1: Complete Bench Setup

1. Install Bench on your system
2. Create a new bench
3. Install ERPNext
4. Create a development site
5. Verify all services are running

### Exercise 2.2: App Development Workflow

1. Create a new custom app
2. Initialize Git repository
3. Create a simple DocType
4. Commit and push changes
5. Test on multiple sites

### Exercise 2.3: VS Code Configuration

1. Install recommended extensions
2. Configure workspace settings
3. Set up debugging configuration
4. Test Python and JavaScript debugging

## 🚀 Common Issues & Solutions

### Installation Issues

**Problem:** Permission denied during installation
```bash
# Solution: Use virtual environment or proper permissions
sudo pip3 install frappe-bench
# OR
python3 -m venv venv
source venv/bin/activate
pip install frappe-bench
```

**Problem:** Redis connection failed
```bash
# Solution: Check Redis service
sudo systemctl status redis
sudo systemctl start redis
```

### Development Issues

**Problem:** Site not accessible
```bash
# Solution: Check bench status
bench doctor
bench restart
```

**Problem:** Migration failures
```bash
# Solution: Check for conflicts
bench --site dev.local migrate
# If fails, check logs
tail -f logs/worker.log
```

---

## 📌 Addendum: Testing the Book's Code with frappe_docker

If you already have ERPNext running via [frappe_docker](https://github.com/frappe/frappe_docker), use the scripts in `environment/` to install and test all three project apps without touching your bench setup.

### Step 1 — Find your container and site name

```bash
# List running containers — look for the 'backend' service
docker ps --format "table {{.Names}}\t{{.Status}}"

# Find your site name (usually 'frontend' in frappe_docker)
docker exec backend bash -c \
    "ls /home/frappe/frappe-bench/sites | grep -v assets | grep -v apps.txt"
```

### Step 2 — Install all three apps

```bash
# From the repo root:
bash environment/install-book-apps.sh frontend backend
```

This copies the app source, pip-installs it, registers it in bench, runs `install-app`, and migrates.

### Step 3 — Run the test suite

```bash
# All apps:
bash environment/run-tests.sh frontend backend

# One app only:
bash environment/run-tests.sh frontend backend asset_management_app
```

### Step 4 — Interactive testing via bench console

```bash
bash environment/console.sh frontend backend
```

Inside the console you can test any chapter's code directly:

```python
# Chapter 6 — ORM examples
frappe.get_all('Asset', filters={'status': 'In Stock'}, fields=['name', 'asset_name'])

# Chapter 5 — Controller
doc = frappe.get_doc('Asset', 'ASSET-00001')
doc.calculate_depreciation()

# Chapter 13 — Vendor Portal API (simulate a request)
from vendor_portal_app.vendor_portal.api.vendor import authenticate
result = authenticate(vendor_code='V-001', password='test')
```

### Sync code changes without reinstalling

After editing any Python file locally, sync it into the container and restart workers:

```bash
# Sync one app
docker cp projects/asset_management/asset_management_app/. \
    backend:/home/frappe/frappe-bench/apps/asset_management_app/

# Restart workers to pick up changes
docker exec backend bash -c \
    "cd /home/frappe/frappe-bench && bench restart"
```

---

## 📖 Further Reading

- [Bench Documentation](https://frappeframework.com/docs/user/en/bench)
- [Development Setup Guide](https://frappeframework.com/docs/user/en/development/setup)
- [VS Code for Frappe Development](https://frappeframework.com/docs/user/en/development/vscode-setup)

## 🎯 Chapter Summary

A professional development environment is crucial for productive ERPNext development. Key takeaways:

- **Bench** is the command-line tool for managing Frappe applications
- **Multiple sites** allow proper development workflow
- **Git integration** ensures version control and collaboration
- **VS Code setup** provides optimal development experience
- **Understanding directory structure** helps in troubleshooting

---

**Next Chapter**: Understanding the anatomy of a Frappe application.

---

## 📌 Addendum: First 10 Commands Every Frappe Developer Should Know

```bash
# 1. Start the development server (foreground, all services)
bench start

# 2. Serve only the web process on a specific port (no workers/scheduler)
#    Use this when you only need HTTP responses and want a lighter process.
bench serve --port 8000

# bench start  vs  bench serve
# ─────────────────────────────
# bench start   → starts gunicorn + Redis workers + scheduler + socket.io
#                 Use for full local development (background jobs, real-time)
# bench serve   → starts gunicorn only
#                 Use for quick API testing or when workers are not needed

# 3. Open an interactive Python console with full Frappe context loaded
bench --site dev.local console
# Inside the console:
# >>> frappe.get_doc('Customer', 'CUST-00001')
# >>> frappe.db.count('Sales Order')

# 4. Run all pending database migrations (after pulling new code or adding fields)
bench --site dev.local migrate

# 5. Clear all caches (Redis + file-based)
bench --site dev.local clear-cache

# 6. Clear website cache only (useful after template changes)
bench --site dev.local clear-website-cache

# 7. Restart all background workers and the web server
bench restart

# 8. Rebuild JS/CSS assets (required after editing public/ files)
bench build --app my_custom_app

# 9. Run the test suite for a specific app
bench --site dev.local run-tests --app my_custom_app

# 10. Execute a one-off Python function (useful for data fixes)
bench --site dev.local execute my_custom_app.utils.fix_data
```

### Key Concepts

- `bench start` is your daily driver — it wires up all services via `Procfile`.
- `bench serve` is a lightweight alternative when you only need HTTP (no background jobs).
- Always run `bench migrate` after pulling upstream changes that include schema updates.
- `bench clear-cache` is the first thing to try when you see stale data or unexpected UI behaviour.
- `bench restart` is needed after changing `hooks.py` or Python files that are cached by gunicorn workers.


---

## Addendum: Source Article Insights

### Frappe Installation: Step-by-Step

The complete installation sequence for Ubuntu/Debian:

```bash
# 1. Update system
sudo apt-get update -y && sudo apt-get upgrade -y

# 2. Install Git
sudo apt-get install git

# 3. Install Python
sudo apt-get install python3-dev python3.10-dev python3-setuptools python3-pip python3-distutils
sudo apt-get install python3.10-venv
sudo apt-get install software-properties-common

# 4. Install MariaDB
sudo apt install mariadb-server mariadb-client
sudo mysql_secure_installation
# Prompts: unix_socket=Y, change root password=Y, remove anonymous=Y,
#          disallow remote root=N, remove test db=Y, reload privileges=Y

# 5. Configure MariaDB for utf8mb4
sudo nano /etc/mysql/my.cnf
# Add at end of file:
# [mysqld]
# character-set-client-handshake = FALSE
# character-set-server = utf8mb4
# collation-server = utf8mb4_unicode_ci
# [mysql]
# default-character-set = utf8mb4
sudo service mysql restart

# 6. Install Redis
sudo apt-get install redis-server

# 7. Install wkhtmltopdf and other packages
sudo apt-get install xvfb libfontconfig wkhtmltopdf
sudo apt-get install libmysqlclient-dev

# 8. Install Node.js via nvm
curl https://raw.githubusercontent.com/creationix/nvm/master/install.sh | bash
source ~/.profile
nvm install 18
sudo apt-get install npm
sudo npm install -g yarn

# 9. Install Frappe Bench
sudo pip3 install frappe-bench

# 10. Initialize bench
bench init --frappe-branch version-15 frappe-bench
cd frappe-bench

# 11. Create a site
bench new-site mysite.local
bench --site mysite.local enable-scheduler
bench --site mysite.local set-maintenance-mode off
bench --site mysite.local set-config server_script_enabled true

# 12. Enable developer mode (dev machines only)
bench set-config -g developer_mode true

# 13. Add site to hosts and start
bench --site mysite.local add-to-hosts
bench start
```

---

### Bench Command Reference

Bench is Frappe's CLI tool — a wrapper around multiple services that power the ecosystem. It runs exclusively on Unix-like systems (Linux, macOS) due to process forking, symbolic links, and shell environment requirements.

**Site Management:**
```bash
bench new-site mysite.local                    # Create new site
bench new-site mysite.local --install-app erpnext  # Create + install app
bench use mysite.local                         # Set default site
bench drop-site mysite.local --no-backup       # Remove site
bench reinstall --admin-password newpass       # Wipe and reinstall
bench migrate                                  # Run DB migrations + patches
bench --site mysite.local add-to-hosts         # Add to /etc/hosts
```

**App Management:**
```bash
bench get-app https://github.com/frappe/erpnext  # Download app
bench get-app erpnext --branch version-15        # Specific branch
bench install-app erpnext                        # Install to current site
bench uninstall-app myapp --yes                  # Remove from site
bench list-apps                                  # List installed apps
```

**Development:**
```bash
bench start          # Start all services (dev)
bench serve          # Start web server only
bench watch          # Watch + compile assets
bench build          # Compile JS/CSS assets
bench build --app myapp --production  # Production build
bench console        # Interactive Python console
bench execute "frappe.get_doc('User', 'Administrator')"  # Run Python
```

**Database:**
```bash
bench mariadb                                    # MariaDB console
bench db-console                                 # Auto-detect DB type
bench add-database-index --doctype "User" --column "email"
bench describe-database-table --doctype "User"
```

**Cache & Users:**
```bash
bench clear-cache                                # Clear all caches
bench clear-website-cache                        # Website cache only
bench destroy-all-sessions --reason "Maintenance"
bench set-admin-password newpass --logout-all-sessions
bench add-user user@example.com --add-role "System Manager"
```

**Backup & Restore:**
```bash
bench backup --with-files --compress
bench restore backup.sql --with-public-files public.tar
bench restore backup.sql --admin-password newpass --force
```

**Testing:**
```bash
bench run-tests --app myapp
bench run-tests --doctype "Sales Invoice" --coverage
bench run-ui-tests myapp --headless
```

**Production Setup:**
```bash
bench setup production    # Configure nginx + supervisor
bench setup nginx         # Nginx config only
bench setup supervisor    # Supervisor config only
bench setup redis         # Redis config
bench doctor              # System health check
bench version             # Show all versions
bench update --app erpnext  # Update specific app
```

**Configuration:**
```bash
bench set-config db_host localhost
bench set-config redis_cache localhost:13000
bench set-config --global developer_mode true
bench show-config --format json
```

**Quick reference cheat sheet:**
```bash
# Daily dev workflow
bench start                    # Start everything
bench clear-cache              # Fix stale data/UI
bench migrate                  # After schema changes
bench restart                  # After hooks.py changes

# Troubleshooting
bench doctor                   # Check system health
bench clear-cache              # First thing to try
tail -f logs/frappe.log        # Watch logs
bench mariadb                  # Direct DB access
```

---

### What Happens When `bench start`

`bench start` uses **Honcho** (a Python process manager inspired by Heroku's Foreman) to read the `Procfile` and start all services simultaneously.

**The Procfile defines these processes:**

```
web:       bench serve --port 8000
redis_cache:  redis-server config/redis_cache.conf
redis_queue:  redis-server config/redis_queue.conf
socketio:  node apps/frappe/socketio.js
schedule:  bench schedule
worker:    bench worker
watch:     bench watch
```

**What each process does:**

| Process | Purpose | Notes |
|---------|---------|-------|
| `web` | HTTP server (Werkzeug in dev, Gunicorn in prod) | Port 8000 |
| `redis_cache` | Sessions, page cache, API response cache | Port 13000 |
| `redis_queue` | Background job queues, inter-process comms | Port 11000 |
| `socketio` | WebSocket real-time updates (Node.js) | Notifications, progress |
| `schedule` | Enqueues cron jobs into Redis queue | Does NOT execute jobs |
| `worker` | Executes jobs from Redis queue | RQ (Redis Queue) workers |
| `watch` | Watches files, rebuilds assets on change | Dev only |

**Key architecture insight — the database is NOT in the Procfile:**
```
MariaDB runs as its own independent system service.
Bench connects to it; it doesn't manage it.
Each site gets its own database.
```

**How SocketIO works (Python can't handle WebSockets directly):**
```
Client ←→ SocketIO Server (Node.js) ←→ Redis Queue ←→ Python Web Server
```
The Python server publishes events to Redis. The Node.js SocketIO server subscribes to Redis and pushes events to connected clients.

**Scheduler vs Worker distinction:**
```python
# Scheduler: only enqueues jobs at the right time
# Worker: actually executes the jobs

# Scheduler puts job in queue:
frappe.enqueue("myapp.tasks.send_report", queue="long")

# Worker picks it up and runs it:
# bench worker --queue long
```

**Production vs Development:**
- Dev: Werkzeug (single-threaded, auto-reload, debugger)
- Prod: Gunicorn (multi-process, no debugger)

```json
// common_site_config.json for production
{
  "gunicorn_workers": 17,
  "webserver_port": 8000
}
```

Configure production with: `bench setup production`
