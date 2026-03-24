# Chapter 28: DevOps and Deployment

## Developer Mode vs Production Mode

### What is `developer_mode`?

A setting in `site_config.json` or `common_site_config.json`:

```json
{ "developer_mode": 1 }   // Development
{ "developer_mode": 0 }   // Production (default)
```

This controls system behavior — NOT how you run Frappe.

### Key Differences

| Feature | Developer Mode | Production Mode |
|---------|---------------|-----------------|
| Asset Minification | Disabled (faster builds) | Enabled (smaller files) |
| Error Tracebacks | Full details shown | Hidden from users |
| Edit Standard DocTypes | Allowed | Read-only |
| Export to JSON files | Automatic | Disabled |
| File Watching | Enabled | Disabled |
| Live Reload | Available | Disabled |
| Performance | Slower | Faster |
| Security | Low | High |

### How to Switch

```bash
# Enable developer mode
bench --site your-site set-config developer_mode 1

# Disable (production)
bench --site your-site set-config developer_mode 0

# Restart after changing
bench restart
```

### Running Frappe: Two Ways

1. **`bench start`** — for development on your local machine
   - Starts all services in your terminal
   - Works well with `developer_mode = 1`
   - Easy to stop with Ctrl+C

2. **nginx + supervisor** — for production servers
   - nginx handles web traffic
   - supervisor keeps processes running 24/7
   - More stable for real users

> Never enable `developer_mode` on a live public site.

---

## Production Setup

### Prerequisites

- Working Frappe Bench installation
- User with sudo privileges
- Domain name pointing to your server (for SSL)
- Ubuntu/Debian

### Step 1: Enable Production Mode

```bash
# Configure production (nginx + supervisor)
sudo bench setup production [frappe-user]

# Generate nginx config
bench setup nginx

# Configure supervisor
bench setup supervisor
bench setup socketio
bench setup redis

# Apply changes
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl restart all

# Fix file permissions
sudo usermod -aG [frappe-user] www-data
sudo systemctl restart nginx
```

### Step 2: Add Domain and SSL

```bash
# Associate domain with site
bench setup add-domain --site mysite.local example.com

# Enable DNS-based multitenancy (required for multiple domains)
bench config dns_multitenant on

# Regenerate nginx config
bench setup nginx
sudo service nginx restart

# Install Certbot (Let's Encrypt)
sudo snap install core
sudo snap refresh core
sudo apt remove -y certbot
sudo snap install --classic certbot
sudo ln -sf /snap/bin/certbot /usr/bin/certbot

# Generate SSL certificate
sudo certbot --nginx

# Test auto-renewal
sudo certbot renew --dry-run
```

### Step 3: Configure SSL in site_config.json (optional)

```json
{
    "domains": [
        {
            "domain": "example.com",
            "ssl_certificate": "/etc/letsencrypt/live/example.com/fullchain.pem",
            "ssl_certificate_key": "/etc/letsencrypt/live/example.com/privkey.pem"
        }
    ]
}
```

### Recommended Production Config

```json
{
    "developer_mode": 0,
    "live_reload": false,
    "restart_supervisor_on_update": true,
    "serve_default_site": true
}
```

### Switching Back to Development

```bash
bench disable-production
# Or manually:
rm config/supervisor.conf
rm config/nginx.conf
sudo service nginx stop
sudo service supervisor stop
bench setup procfile
bench start
```

---

## Encryption Key System

### What is the Encryption Key?

A 32-byte base64-encoded key stored in `site_config.json` that Frappe uses to encrypt/decrypt sensitive data:

- API keys and secrets
- Email passwords
- Payment gateway credentials
- Encrypted backup files

```json
{
    "encryption_key": "bhbhjhjdfjhjfbvjhfvbkfdsbkbsbdfhksbkbd="
}
```

### User Passwords vs Encrypted Passwords

| Aspect | User Passwords | Service Passwords |
|--------|----------------|-------------------|
| Storage | Hashed (bcrypt) | Encrypted (AES) |
| Retrieval | Cannot be retrieved | Can be decrypted |
| Uses encryption_key | No | Yes |
| Purpose | Authentication | Service connections |

```python
# User passwords — hashed, cannot be retrieved
hashPwd = passlibctx.hash(pwd)  # bcrypt/pbkdf2

# Service passwords — encrypted, can be decrypted
encrypted_pwd = encrypt(pwd)  # Uses encryption_key
decrypted_pwd = decrypt(encrypted_pwd)  # Needs same key
```

### Critical: Migration and Backups

**The encryption key is tied to all encrypted data in the database.** If you migrate a site without the original key, all encrypted values become unreadable.

```bash
# Correct migration — preserve the key
cp sites/old-site/site_config.json sites/new-site/

# Restore with encryption key
bench --site new-site restore backup.sql --encryption-key "original_key"
```

**What happens without the original key:**
- `bench migrate` succeeds (schema changes only)
- But at runtime: "Encryption key is invalid!" when trying to send email, use APIs, etc.

### Key Rules

1. **Always backup `site_config.json`** with your database backup
2. **Never change `encryption_key`** without proper migration procedures
3. **If lost, encrypted data cannot be recovered** — only option is to re-enter credentials
4. **User login passwords are safe** — they're hashed, not encrypted

---

## Docker and Containerization

### Why Docker for Frappe?

- **Consistency**: Same environment in dev, staging, and production
- **Isolation**: Multiple Frappe versions on the same machine
- **Portability**: Build once, run anywhere
- **Scalability**: Run more containers when traffic increases

### Key Docker Concepts

**Image** = read-only template (blueprint)
**Container** = running instance of an image

```bash
# Image stored on disk
docker images
# REPOSITORY          TAG       IMAGE ID       SIZE
# frappe/erpnext      v16       abc123         1.2GB

# Container running from image
docker ps
# CONTAINER ID   IMAGE                STATUS
# def456         frappe/erpnext:v16   Up 2 hours
```

### Dockerfile for Frappe

```dockerfile
# Use specific versions for reproducible builds
ARG PYTHON_VERSION=3.11.6
ARG DEBIAN_BASE=bookworm
FROM python:${PYTHON_VERSION}-slim-${DEBIAN_BASE} AS base

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PATH=/home/frappe/.local/bin:$PATH

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        git \
        mariadb-client \
        libmariadb-dev \
        wkhtmltopdf \
    && rm -rf /var/lib/apt/lists/*

# Create frappe user
RUN useradd -ms /bin/bash frappe
USER frappe
WORKDIR /home/frappe

# Install bench
RUN pip install frappe-bench

# Initialize bench
ARG FRAPPE_BRANCH=version-16
RUN bench init --frappe-branch=${FRAPPE_BRANCH} frappe-bench

WORKDIR /home/frappe/frappe-bench

EXPOSE 8000
CMD ["bench", "serve", "--port", "8000"]
```

### Layer Caching Best Practice

```dockerfile
# Bad — changes to any file invalidate pip install cache
COPY . /app/
RUN pip install -r requirements.txt

# Good — requirements change rarely, code changes often
COPY requirements.txt /app/
RUN pip install -r requirements.txt
COPY . /app/
```

### `.dockerignore`

```
.git
.gitignore
*.md
.env
.env.*
node_modules
__pycache__
*.pyc
.vscode/
*.log
```

### ARG vs ENV

```dockerfile
# ARG: Build-time only (not available when container runs)
ARG FRAPPE_BRANCH=version-16
RUN bench init --frappe-branch=${FRAPPE_BRANCH} ...

# ENV: Available at runtime
ENV DB_HOST=localhost
ENV DB_PORT=3306
```

### Multi-Stage Build

```dockerfile
# Stage 1: Build
FROM python:3.11-slim AS builder
RUN pip install --user frappe-bench
# ... build steps

# Stage 2: Production (smaller final image)
FROM python:3.11-slim AS production
COPY --from=builder /home/frappe/.local /home/frappe/.local
# Only copy what's needed for runtime
```

---

## Common Issues and Fixes

### `bench start` crashes — Port Conflicts

```bash
# Redis ports already in use
# Error: TCP listening socket on 127.0.0.1:11000 is already in use

# Find what's using the ports
sudo lsof -i :11000
sudo lsof -i :13000

# Kill conflicting processes
sudo kill <PID1> <PID2>

# Clear cache and restart
bench --site your-site clear-cache
bench --site your-site clear-website-cache
bench start
```

### `bench start` crashes — Corrupted Cache

```bash
bench --site your-site clear-cache
bench --site your-site clear-website-cache
bench start
```

### `NameError: name 'null' is not defined`

```bash
bench clear-cache
# Or try a different browser
```

### Missing Node module error

```bash
bench setup requirements
```

### `ValueError: id must not contain ":"`

Update to latest Frappe version, or manually fix `create_job_id` in `frappe/utils/backgroundjobs.py`:

```python
def create_job_id(job_id=None):
    if not job_id:
        job_id = str(uuid4())
    else:
        job_id = job_id.replace(":", "|")
    return f"{frappe.local.site}||{job_id}"
```

### "Encryption key is invalid!" after restore

```bash
# Copy original site_config.json from backup
cp backup/site_config.json sites/your-site/site_config.json
bench restart
```

---

## Expose Frappe with ngrok (Development)

For testing webhooks or sharing your local dev environment:

```bash
# Install ngrok
# https://ngrok.com/download

# Expose port 8000
ngrok http 8000

# You'll get a public URL like:
# https://abc123.ngrok.io → http://localhost:8000
```

Update your site config to allow the ngrok domain:

```bash
bench --site your-site set-config host_name "https://abc123.ngrok.io"
```

---

## Webhooks

Webhooks allow external systems to notify your Frappe instance when events occur.

### Creating a Webhook

Navigate to: Setup → Integrations → Webhook → New

Required fields:
- DocType
- Document Event (Submit, Save, etc.)
- Request URL (the endpoint to call)
- Request Method (POST)

### Webhook Payload

```json
{
    "doctype": "Sales Order",
    "name": "SO-2024-00001",
    "status": "Submitted",
    "customer": "CUST-001",
    "grand_total": 5000
}
```

### Security: Webhook Secret

Add a secret to verify the webhook came from your Frappe instance:

```python
import hmac
import hashlib

def verify_webhook(payload, signature, secret):
    expected = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
```
