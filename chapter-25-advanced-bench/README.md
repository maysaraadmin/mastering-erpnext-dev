# Chapter 25: Advanced Bench — Commands, Architecture, and Process Management

## What is Bench?

**Bench** is Frappe's CLI tool that provides a unified way to manage Frappe applications, sites, and development workflows. It wraps multiple tools and services that power the Frappe ecosystem.

Key capabilities:
- Site management (create, backup, restore, manage multiple sites)
- App management (install, update, manage Frappe applications)
- Development tools (build assets, watch files, run servers)
- Database operations
- Testing framework
- Deployment

---

## Why Bench is Unix-Only

Bench is designed exclusively for Unix-like systems (Linux, macOS, FreeBSD) because:

- **Process forking**: Unix's efficient process creation model
- **Symbolic links**: Used for asset management
- **File permissions**: Proper security model
- **Shell environment**: Bash/Zsh scripting, environment variables
- **Package managers**: apt, brew, yum — Windows uses different systems

---

## What Happens When You Run `bench start`

When you run `bench start`, Frappe uses **Honcho** (a Python process manager inspired by Heroku's Foreman) to read the `Procfile` and start all services simultaneously.

### The 6 Processes

#### 1. Redis Cache (`redis_cache`)
```bash
redis_cache: redis-server config/redis_cache.conf
```
- Port: 13000 (configurable)
- Stores: user sessions, page cache, API response cache, rate limiting counters

#### 2. Redis Queue (`redis_queue`)
```bash
redis_queue: redis-server config/redis_queue.conf
```
- Port: 11000 (configurable)
- Manages: background job queues, scheduled task data, inter-process communication, job status tracking

#### 3. Web Server
```bash
web: bench serve --port 8000
```
- **Development**: Werkzeug's built-in server (auto-reload, debugging, single-threaded)
- **Production**: Gunicorn with multiple worker processes

Frappe is a **WSGI app** — it follows the WSGI protocol (Web Server Gateway Interface), the standard bridge between Python web apps and web servers.

```python
# From frappe/app.py
from werkzeug.serving import run_simple

def serve(port=8000, ...):
    run_simple(
        "0.0.0.0",
        int(port),
        application,      # WSGI application
        use_reloader=True,
        use_debugger=True,
        threaded=False,   # Single-threaded for development
    )
```

#### 4. SocketIO (Real-time)
```bash
socketio: node apps/frappe/socketio.js
```
- Provides WebSocket-based live updates
- Used for notifications, chats, progress indicators
- Architecture: `Client ↔ SocketIO Server ↔ Redis Queue ↔ Web Server`
- The Python web server publishes events to Redis; the Node.js SocketIO server subscribes and pushes to clients

#### 5. Task Scheduler
```bash
schedule: bench schedule
```
- Checks: "Is it time to run this task?"
- When scheduled time comes, puts the job into Redis Queue
- Workers then execute the job
- The scheduler only **enqueues** — it does not execute

#### 6. File Watcher (Development Only)
```bash
watch: bench watch
```
- Monitors Python, JS/Vue, CSS/SCSS, config file changes
- Auto-reloads server or rebuilds assets
- **Disabled in production** — in production you must manually restart after pulling updates

### Background Workers
```bash
worker: bench worker 1>> logs/worker.log 2>> logs/error.log
```
- Processes jobs from Redis queues using **RQ (Redis Queue)**
- Queue types: `default`, `long`, `short`, `email`
- Multiple workers can run in parallel

```bash
# Specialized workers
worker: bench worker --queue default
worker-long: bench worker --queue long
worker-email: bench worker --queue email
```

### Where is the Database?

There is **no database process** in the Procfile. MariaDB/MySQL runs as its own independent service — Bench only connects to it. Each site gets its own database.

### Why Honcho?

Without Honcho, you'd need to open multiple terminal windows and run each service manually. Honcho gives you:
- **Centralized management**: one command starts everything
- **Unified logging**: all logs in one terminal with color-coded prefixes (`[web]`, `[redis_cache]`, etc.)
- **Process coordination**: services start in the right order
- **Graceful shutdown**: stopping `bench start` shuts down all processes together

---

## Custom Bench Commands

### What Are They?

Custom bench commands are your own CLI tools built on top of Frappe's bench. Instead of only using built-in commands, you can create new ones — like clearing a specific cache, generating reports, or listing all sites.

They're great for:
- Automating repetitive tasks
- Simplifying long console queries
- Giving your team handy shortcuts
- Sharing tools — anyone who installs your app gets the commands automatically

### How Command Discovery Works

Frappe automatically scans installed apps for a `commands.py` file:

```python
# From frappe/utils/bench_helper.py
def get_app_commands(app: str) -> dict:
    ret = {}
    try:
        app_command_module = importlib.import_module(f"{app}.commands")
    except ModuleNotFoundError:
        return ret
    
    for command in getattr(app_command_module, "commands", []):
        ret[command.name] = command
    return ret
```

### File Structure

```
apps/your_app/
├── your_app/
│   ├── __init__.py
│   └── commands.py    ← Commands go here
├── setup.py
└── pyproject.toml
```

**NOT** in `apps/your_app/your_app/frappe/commands/commands.py`.

### Creating Your First Command

```python
# apps/my_app/my_app/commands.py
import click
from frappe.commands import pass_context

@click.command('hello')
@pass_context
def hello(context):
    """Say hello from My App"""
    click.echo("Hello from My Custom App!")

# This list is the discovery mechanism — Frappe reads it automatically
commands = [hello]
```

```bash
bench install-app my_app
bench hello
# Output: Hello from My Custom App!
```

> You don't need to restart the server. Bench loads commands immediately after you create `commands.py` with `commands = []`.

### Command with Options and Site Context

```python
@click.command('user-info')
@click.option('--user', '-u', default='Administrator', help='Username to get info for')
@pass_context
def user_info(context, user):
    """Get user information"""
    import frappe
    
    try:
        user_doc = frappe.get_doc('User', user)
        click.echo(f"User: {user_doc.full_name}")
        click.echo(f"Email: {user_doc.email}")
        click.echo(f"Enabled: {user_doc.enabled}")
    except frappe.DoesNotExistError:
        click.echo(f"User '{user}' not found")

commands = [user_info]
```

### Database Query Command

```python
@click.command('custom-query')
@click.option('--query', required=True, help='SQL query to execute')
@click.option('--limit', default=10, help='Limit results')
@pass_context
def custom_query(context, query, limit):
    """Execute custom database query"""
    import frappe
    
    try:
        result = frappe.db.sql(query, as_dict=True)
        click.echo(f"Found {len(result)} records.")
        for i, row in enumerate(result[:limit]):
            click.echo(f"Row {i+1}: {row}")
        if len(result) > limit:
            click.echo(f"... and {len(result) - limit} more records")
    except Exception as e:
        click.echo(f"Error: {str(e)}")

commands = [custom_query]
```

### Command Groups (Subcommands)

```python
@click.group()
def my_app():
    """My App management commands"""
    pass

@my_app.command('create')
@click.option('--name', required=True)
def create(name):
    """Create something"""
    click.echo(f"Creating {name}")

@my_app.command('list')
def list_items():
    """List items"""
    click.echo("Listing items")

commands = [my_app]
```

```bash
bench my-app create --name test
bench my-app list
```

### Organizing Commands Across Files

```python
# commands/db_commands.py
db_commands = [backup_db, restore_db]

# commands/file_commands.py
file_commands = [process_files, cleanup_files]

# commands.py
from .commands.db_commands import db_commands
from .commands.file_commands import file_commands

commands = db_commands + file_commands
```

### Error Handling in Commands

```python
@click.command('safe-operation')
@pass_context
def safe_operation(context):
    import frappe
    
    try:
        result = frappe.db.sql("SELECT * FROM tabUser", as_dict=True)
        click.echo(f"Success: {len(result)} users found")
    except frappe.DatabaseError as e:
        click.echo(f"Database error: {str(e)}", err=True)
        raise click.Abort()
    except Exception as e:
        click.echo(f"Unexpected error: {str(e)}", err=True)
        raise click.Abort()

commands = [safe_operation]
```

### `@pass_context` vs `@get_site_context`

- `@pass_context` — passes basic Frappe context; for commands that don't need database access
- `@get_site_context` — ensures site context is properly initialized; for commands that need to access site data

---

## Bench Command Reference

### Site Management
```bash
bench new-site mysite.local                    # Create new site
bench new-site mysite.local --install-app erpnext
bench use mysite.local                         # Set default site
bench drop-site oldsite.local --no-backup --force
bench reinstall --admin-password newpass123
bench migrate                                  # Run patches + schema updates
bench migrate --skip-failing
```

### App Management
```bash
bench get-app https://github.com/frappe/erpnext
bench get-app erpnext --branch version-16
bench install-app erpnext
bench uninstall-app custom-app --yes
bench list-apps
bench list-apps --format json
```

### Development
```bash
bench start                    # Start all services
bench serve --port 8001        # Start web server only
bench watch                    # Watch and compile assets
bench build                    # Compile JS/CSS assets
bench build --app erpnext --production
bench console                  # Interactive Python console
bench console --autoreload
```

### Database
```bash
bench mariadb                  # MariaDB console
bench db-console               # Auto-detect DB type
bench add-database-index --doctype "User" --column "email"
bench describe-database-table --doctype "User"
```

### Cache & Sessions
```bash
bench clear-cache
bench clear-website-cache
bench destroy-all-sessions --reason "Maintenance"
```

### User Management
```bash
bench add-user user@example.com --first-name "John" --add-role "System Manager"
bench set-password user@example.com newpassword123
bench set-admin-password newadminpass --logout-all-sessions
bench disable-user user@example.com
```

### Backup & Restore
```bash
bench backup
bench backup --with-files --compress
bench restore backup.sql
bench restore backup.sql --with-public-files public.tar --with-private-files private.tar
bench restore backup.sql --admin-password newpass --force
```

### Testing
```bash
bench run-tests
bench run-tests --app erpnext
bench run-tests --doctype "User" --coverage
bench run-tests --test "test_user_creation" --failfast
bench run-ui-tests erpnext --headless --parallel
```

### Utilities
```bash
bench execute "frappe.get_doc('User', 'Administrator')"
bench execute "myapp.utils.process_data" --kwargs "{'param1': 'value1'}"
bench browse --user Administrator
bench make-app /path/to/apps myapp
bench create-patch
```

### Configuration
```bash
bench set-config db_host localhost
bench set-config smtp_server smtp.gmail.com
bench set-config --global bench_branch version-16
bench show-config
bench show-config --format json
```

### Production & System
```bash
bench setup production
bench setup supervisor
bench setup nginx
bench setup redis
bench setup procfile
bench doctor                   # Diagnose system issues
bench version                  # Show versions
bench update                   # Update all apps
bench update --app erpnext --branch version-16
```

---

## Backup and Restore Guide

### Creating Backups

```bash
# Basic backup (database only)
bench backup

# Full backup with files
bench backup --with-files --compress

# Backup specific DocTypes
bench backup --include "User,Sales Invoice"

# Backup to custom path
bench backup --backup-path /backups/
```

### Restoring Backups

```bash
# Restore database only
bench restore /path/to/backup.sql

# Restore with files
bench restore backup.sql \
  --with-public-files public.tar \
  --with-private-files private.tar

# Force restore (overwrite existing)
bench restore backup.sql --admin-password newpass --force
```

### Best Practices

1. **Always backup before** `bench migrate`, `bench update`, or any major change
2. **Test restores** on a staging server — a backup you've never tested is not a backup
3. **Automate backups** using the scheduler or cron
4. **Store backups offsite** — S3, Google Drive, etc.
5. **Encrypt sensitive backups** using `--encryption-key`

---

## Production Setup with Gunicorn

By default, `bench start` uses Werkzeug (single-threaded, development only). For production:

```bash
# Configure workers in common_site_config.json
bench set-config gunicorn_workers 4
bench set-config webserver_port 8000

# Set up production (configures Gunicorn + Supervisor + Nginx)
bench setup production
```

Recommended workers: `2 × CPU cores + 1`

---

## Quick Reference Cheat Sheet

```bash
# Most used commands
bench start                    # Start everything
bench migrate                  # Apply patches + schema
bench build                    # Rebuild JS/CSS
bench clear-cache              # Clear all caches
bench backup                   # Create backup
bench console                  # Python REPL with Frappe context
bench doctor                   # Check system health
bench version                  # Show versions
```
