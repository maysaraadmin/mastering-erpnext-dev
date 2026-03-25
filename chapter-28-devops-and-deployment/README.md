# Chapter 28: DevOps and Deployment

## 🎯 Learning Objectives

By the end of this chapter, you will master:
- **Container-based deployment** using Docker and Docker Compose
- **Production configuration** and security hardening
- **CI/CD pipelines** for automated deployment
- **Monitoring and logging** in production environments
- **Backup and disaster recovery** strategies
- **Performance optimization** for production workloads

## 📚 Chapter Topics

### 28.1 Developer Mode vs Production Mode

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
# Enable production mode
bench --site site1.local set-config developer_mode 0

# Enable development mode
bench --site site1.local set-config developer_mode 1
```

### 28.2 Docker-based Deployment

## Introduction to Docker

### What is Docker?

Docker is a platform that packages applications and dependencies into lightweight, portable containers. Containers include everything needed to run an application: code, runtime, system tools, libraries, and settings.

### Docker vs Traditional Virtualization

| Aspect | Virtual Machines | Docker Containers |
|---------|------------------|-------------------|
| **OS Kernel** | Separate kernel per VM | Shared host kernel |
| **Resource Usage** | Heavy (1-2GB RAM per VM) | Lightweight (50-100MB per container) |
| **Startup Time** | Minutes | Seconds |
| **Portability** | Limited | Highly portable |

### Frappe Docker Architecture

Frappe applications use a multi-container approach:

```yaml
# Typical Frappe Docker setup
services:
  # Backend: Frappe/ERPNext application
  frappe:
    image: frappe/erpnext:v15
    volumes:
      - sites:/home/frappe/frappe-bench/sites
      - apps:/home/frappe/frappe-bench/apps
  
  # Database: MariaDB/PostgreSQL
  db:
    image: mariadb:10.6
    environment:
      MYSQL_ROOT_PASSWORD: root_password
  
  # Cache: Redis
  redis-cache:
    image: redis:6.2-alpine
    command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
  
  # Queue: Redis
  redis-queue:
    image: redis:6.2-alpine
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
  
  # Frontend: Nginx reverse proxy
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
```

## Creating Your First Frappe Dockerfile

### Basic Dockerfile for Custom Frappe App

```dockerfile
# Multi-stage build for production optimization
FROM frappe/erpnext:v15 AS builder

# Set working directory
WORKDIR /home/frappe/frappe-bench

# Copy custom app
COPY my_custom_app /home/frappe/frappe-bench/apps/my_custom_app

# Install app dependencies
RUN bench build --app my_custom_app

# Production stage
FROM frappe/erpnext:v15

WORKDIR /home/frappe/frappe-bench

# Copy built assets from builder stage
COPY --from=builder /home/frappe/frappe-bench/sites /home/frappe/frappe-bench/sites
COPY --from=builder /home/frappe/frappe-bench/apps/my_custom_app /home/frappe/frappe-bench/apps/my_custom_app

# Set permissions
RUN chown -R frappe:frappe /home/frappe/frappe-bench

USER frappe

# Expose port
EXPOSE 8000

# Start command
CMD ["bench", "start"]
```

### Advanced Dockerfile with Optimization

```dockerfile
FROM frappe/erpnext:v15 AS base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Development stage
FROM base AS development

WORKDIR /home/frappe/frappe-bench

# Enable development mode
ENV DEVELOPER_MODE=1

# Copy source code
COPY . .

# Install dependencies
RUN bench setup requirements --dev
RUN bench build

# Production stage
FROM base AS production

WORKDIR /home/frappe/frappe-bench

# Copy only necessary files
COPY --from=development /home/frappe/frappe-bench/sites /home/frappe/frappe-bench/sites
COPY --from=development /home/frappe/frappe-bench/apps /home/frappe/frappe-bench/apps

# Production settings
ENV DEVELOPER_MODE=0
ENV MAINTENANCE_MODE=0

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/api/method/version || exit 1

USER frappe

EXPOSE 8000

CMD ["bench", "serve", "--port=8000", "--no-reload"]
```

## Docker Compose for Production

### Complete Production Docker Compose

```yaml
version: '3.8'

services:
  # Frappe Application
  frappe:
    image: frappe/erpnext:v15
    container_name: frappe-app
    restart: unless-stopped
    environment:
      - FRAPPE_SITE=site1.local
      - MYSQL_ROOT_PASSWORD=admin
      - REDIS_CACHE=redis-cache:6379
      - REDIS_QUEUE=redis-queue:6379
    volumes:
      - ./sites:/home/frappe/frappe-bench/sites:rw
      - ./apps:/home/frappe/frappe-bench/apps:rw
      - frappe-logs:/home/frappe/frappe-bench/logs
      - frappe-backup:/home/frappe/frappe-bench/sites/site1.local/private/backups
    depends_on:
      - db
      - redis-cache
      - redis-queue
    networks:
      - frappe-network
    ports:
      - "8000:8000"

  # Database
  db:
    image: mariadb:10.6
    container_name: frappe-db
    restart: unless-stopped
    environment:
      - MYSQL_ROOT_PASSWORD=admin
      - MYSQL_USER=frappe
      - MYSQL_PASSWORD=frappe
      - MYSQL_DATABASE=frappe
    volumes:
      - db-data:/var/lib/mysql
      - ./mysql/my.cnf:/etc/mysql/conf.d/frappe.cnf:ro
    networks:
      - frappe-network
    command: --default-authentication-plugin=mysql_native_password

  # Redis Cache
  redis-cache:
    image: redis:6.2-alpine
    container_name: frappe-cache
    restart: unless-stopped
    volumes:
      - redis-cache-data:/data
    networks:
      - frappe-network
    command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru

  # Redis Queue
  redis-queue:
    image: redis:6.2-alpine
    container_name: frappe-queue
    restart: unless-stopped
    volumes:
      - redis-queue-data:/data
    networks:
      - frappe-network
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru

  # Nginx Reverse Proxy
  nginx:
    image: nginx:alpine
    container_name: frappe-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/sites:/etc/nginx/sites-available:ro
      - ./ssl:/etc/nginx/ssl:ro
      - frappe-logs:/var/log/nginx
    depends_on:
      - frappe
    networks:
      - frappe-network

  # Background Worker
  worker:
    image: frappe/erpnext:v15
    container_name: frappe-worker
    restart: unless-stopped
    environment:
      - FRAPPE_SITE=site1.local
      - MYSQL_ROOT_PASSWORD=admin
      - REDIS_CACHE=redis-cache:6379
      - REDIS_QUEUE=redis-queue:6379
    volumes:
      - ./sites:/home/frappe/frappe-bench/sites:rw
      - ./apps:/home/frappe/frappe-bench/apps:rw
      - frappe-logs:/home/frappe/frappe-bench/logs
    depends_on:
      - db
      - redis-cache
      - redis-queue
    networks:
      - frappe-network
    command: bench worker

volumes:
  db-data:
    driver: local
  redis-cache-data:
    driver: local
  redis-queue-data:
    driver: local
  frappe-logs:
    driver: local
  frappe-backup:
    driver: local

networks:
  frappe-network:
    driver: bridge
```

### Environment Configuration

```bash
# .env file
FRAPPE_VERSION=v15
SITE_NAME=erp.example.com
MYSQL_ROOT_PASSWORD=your_secure_password
MYSQL_PASSWORD=your_mysql_password
REDIS_PASSWORD=your_redis_password

# SSL Configuration
SSL_CERT_PATH=./ssl/cert.pem
SSL_KEY_PATH=./ssl/key.pem

# Backup Configuration
BACKUP_SCHEDULE=0 2 * * *
BACKUP_RETENTION_DAYS=30
```

## Production Nginx Configuration

### Nginx Conf for Frappe

```nginx
# /etc/nginx/nginx.conf
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging format
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    # Performance optimizations
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=1r/s;

    # Include site configurations
    include /etc/nginx/sites-enabled/*;
}
```

### Site Configuration

```nginx
# /etc/nginx/sites-available/erp.example.com
server {
    listen 80;
    server_name erp.example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name erp.example.com;

    # SSL configuration
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Root directory
    root /home/frappe/frappe-bench/sites;
    index index.html;

    # Security
    client_max_body_size 50M;
    client_body_buffer_size 128k;

    # Frappe specific locations
    location / {
        proxy_pass http://frappe:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $server_name;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
        send_timeout 600s;
    }

    # Rate limiting for API
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://frappe:8000;
        # ... same proxy settings as above
    }

    # Rate limiting for login
    location /login {
        limit_req zone=login burst=5 nodelay;
        proxy_pass http://frappe:8000;
        # ... same proxy settings as above
    }

    # Static files
    location /assets/ {
        alias /home/frappe/frappe-bench/sites/assets/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Health check
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
```

### 28.3 Production Security Hardening

## Security Configuration

### Site Security Settings

```python
# site_config.json
{
    "developer_mode": 0,
    "maintenance_mode": 0,
    "disable_signup": 1,
    "restrict_domain_setup": 1,
    "enable_two_factor_auth": 1,
    "force_two_factor_auth": 0,
    "session_expiry": 14400,
    "allow_password_reset": 1,
    "password_reset_expiry": 3600,
    "restrict_ip_login": 0,
    "allowed_ips": [],
    "enable captcha": 1,
    "backup_limit": 5,
    "auto_account_deletion": 0,
    "suspend_auto_account_deletion": 0
}
```

### Database Security

```sql
-- Create dedicated database user
CREATE USER 'frappe'@'%' IDENTIFIED BY 'strong_password';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, ALTER, INDEX ON `frappe_%`.* TO 'frappe'@'%';
FLUSH PRIVILEGES;

-- Remove test database
DROP DATABASE IF EXISTS test;

-- Remove anonymous users
DELETE FROM mysql.user WHERE User='';
FLUSH PRIVILEGES;
```

### Firewall Configuration

```bash
# UFW firewall rules
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

### SSL/TLS Configuration

```bash
# Generate SSL certificate with Let's Encrypt
certbot --nginx -d erp.example.com

# Auto-renewal setup
echo "0 12 * * * /usr/bin/certbot renew --quiet" | crontab -
```

### 28.4 Monitoring and Logging

## Application Monitoring

### Health Check Script

```python
# health_check.py
import requests
import sys
import time

def check_health():
    """Check application health"""
    try:
        # Check main application
        response = requests.get('http://localhost:8000/api/method/version', timeout=10)
        if response.status_code != 200:
            return False, "Application not responding"
        
        # Check database connectivity
        import frappe
        frappe.init('site1.local')
        frappe.connect()
        frappe.db.sql("SELECT 1")
        frappe.destroy()
        
        return True, "All systems healthy"
    except Exception as e:
        return False, str(e)

if __name__ == "__main__":
    healthy, message = check_health()
    if not healthy:
        print(f"UNHEALTHY: {message}")
        sys.exit(1)
    else:
        print(f"HEALTHY: {message}")
        sys.exit(0)
```

### Prometheus Metrics

```python
# metrics.py
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import frappe

# Define metrics
REQUEST_COUNT = Counter('frappe_requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('frappe_request_duration_seconds', 'Request duration')
ACTIVE_USERS = Gauge('frappe_active_users', 'Number of active users')
DB_CONNECTIONS = Gauge('frappe_db_connections', 'Database connections')

@REQUEST_DURATION.time()
def track_request():
    """Track request metrics"""
    REQUEST_COUNT.labels(method='GET', endpoint='/api/method/version').inc()
    ACTIVE_USERS.set(len(frappe.db.get_all('User', filters={'enabled': 1})))
    DB_CONNECTIONS.set(frappe.db.connection_pool_size)

# Start metrics server
start_http_server(8001)
```

### Log Management

```yaml
# docker-compose.logging.yml
version: '3.8'

services:
  frappe:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
    
  # ELK Stack for log aggregation
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:7.15.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    volumes:
      - elasticsearch-data:/usr/share/elasticsearch/data

  logstash:
    image: docker.elastic.co/logstash/logstash:7.15.0
    volumes:
      - ./logstash/pipeline:/usr/share/logstash/pipeline:ro
    depends_on:
      - elasticsearch

  kibana:
    image: docker.elastic.co/kibana/kibana:7.15.0
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    depends_on:
      - elasticsearch

volumes:
  elasticsearch-data:
```

### 28.5 Backup and Disaster Recovery

## Automated Backup Strategy

### Backup Script

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/home/frappe/backups"
SITE_NAME="site1.local"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Create backup directory
mkdir -p $BACKUP_DIR

# Database backup
bench --site $SITE_NAME backup --with-files --backup-path $BACKUP_DIR

# Compress old backups
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -exec gzip {} \;

# Remove old backups
find $BACKUP_DIR -name "*" -mtime +$RETENTION_DAYS -delete

# Upload to cloud storage (optional)
if command -v aws &> /dev/null; then
    aws s3 sync $BACKUP_DIR s3://my-frappe-backups/$SITE_NAME/
fi

echo "Backup completed: $DATE"
```

### Cron Job Configuration

```bash
# Add to crontab
# Daily backup at 2 AM
0 2 * * * /home/frappe/backup.sh >> /var/log/frappe-backup.log 2>&1

# Weekly database optimization
0 3 * * 0 /home/frappe/optimize_db.sh >> /var/log/frappe-maintenance.log 2>&1

# Monthly log rotation
0 4 1 * * /home/frappe/rotate_logs.sh >> /var/log/frappe-maintenance.log 2>&1
```

### Disaster Recovery Plan

```bash
#!/bin/bash
# disaster_recovery.sh

SITE_NAME="site1.local"
BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

# Stop services
docker-compose down

# Restore database
bench --site $SITE_NAME restore --with-files $BACKUP_FILE

# Start services
docker-compose up -d

# Verify restoration
bench --site $SITE_NAME doctor

echo "Disaster recovery completed"
```

### 28.6 Performance Optimization

## Production Performance Tuning

### Database Optimization

```sql
-- MySQL configuration optimizations
[mysqld]
# Memory settings
innodb_buffer_pool_size = 2G
innodb_log_file_size = 256M
innodb_log_buffer_size = 16M

# Connection settings
max_connections = 200
max_connect_errors = 1000

# Query cache
query_cache_type = 1
query_cache_size = 256M

# Slow query log
slow_query_log = 1
slow_query_log_file = /var/log/mysql/slow.log
long_query_time = 2

# InnoDB settings
innodb_file_per_table = 1
innodb_flush_log_at_trx_commit = 2
innodb_flush_method = O_DIRECT
```

### Redis Optimization

```conf
# redis.conf
# Memory settings
maxmemory 512mb
maxmemory-policy allkeys-lru

# Persistence settings
save 900 1
save 300 10
save 60 10000

# Network settings
tcp-keepalive 60
timeout 300

# Performance settings
tcp-backlog 511
databases 16
```

### Application Caching

```python
# cache_manager.py
import frappe
from functools import wraps

def cache_result(expiration=3600):
    """Decorator to cache function results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            result = frappe.cache().get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            frappe.cache().set(cache_key, result, expires_in_sec=expiration)
            
            return result
        return wrapper
    return decorator

@cache_result(expiration=1800)
def get_customer_sales(customer):
    """Get customer sales data with caching"""
    return frappe.get_all("Sales Order", 
        filters={"customer": customer, "docstatus": 1},
        fields=["name", "grand_total", "transaction_date"]
    )
```

### 28.7 CI/CD Pipeline

## GitHub Actions Workflow

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      mariadb:
        image: mariadb:10.6
        env:
          MYSQL_ROOT_PASSWORD: root
        options: >-
          --health-cmd="mysqladmin ping"
          --health-interval=10s
          --health-timeout=5s
          --health-retries=3
      
      redis:
        image: redis:6.2
        options: >-
          --health-cmd="redis-cli ping"
          --health-interval=10s
          --health-timeout=5s
          --health-retries=3

    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Cache pip dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        bench --site test_site install-app erpnext
        bench --site test_site migrate
        bench --site test_site run-tests --app my_custom_app
    
    - name: Run linting
      run: |
        flake8 my_custom_app
        black --check my_custom_app

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2
    
    - name: Login to Container Registry
      uses: docker/login-action@v2
      with:
        registry: ghcr.io
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Build and push Docker image
      uses: docker/build-push-action@v4
      with:
        context: .
        push: true
        tags: ghcr.io/${{ github.repository }}:latest
        cache-from: type=gha
        cache-to: type=gha,mode=max

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - name: Deploy to production
      uses: appleboy/ssh-action@v0.1.5
      with:
        host: ${{ secrets.PROD_HOST }}
        username: ${{ secrets.PROD_USER }}
        key: ${{ secrets.PROD_SSH_KEY }}
        script: |
          cd /opt/frappe
          docker-compose pull
          docker-compose up -d
          docker system prune -f
```

---

## 🎯 **Best Practices Summary**

### **Security**
- Use HTTPS everywhere
- Implement rate limiting
- Regular security updates
- Principle of least privilege

### **Performance**
- Enable caching at all levels
- Optimize database queries
- Use CDN for static assets
- Monitor resource usage

### **Reliability**
- Automated backups
- Health checks
- Monitoring and alerting
- Disaster recovery plan

### **Scalability**
- Horizontal scaling with containers
- Load balancing
- Database optimization
- Caching strategies

---

**💡 Pro Tip**: Always test deployment procedures in staging before applying to production. Document rollback procedures and practice disaster recovery scenarios regularly.

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


---

## Addendum: Source Article Insights

### Production Setup Overview

Frappe production mode uses three key components:
- **Nginx** — reverse proxy, serves static files
- **Supervisor** — manages Gunicorn, Socket.IO, and worker processes
- **Redis** — caching and job queuing

```bash
# Full production setup sequence (run as frappe user, not root)

# 1. Setup production (configures Nginx, Supervisor, log rotation)
sudo bench setup production [frappe-user]

# 2. Generate Nginx config
bench setup nginx

# 3. Setup remaining services
bench setup supervisor
bench setup socketio
bench setup redis

# 4. Apply and restart
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl restart all

# 5. Fix web server permissions
sudo usermod -aG [frappe-user] www-data
sudo systemctl restart nginx

# Verify all processes are running
sudo supervisorctl status
```

---

### Domain and SSL Configuration

```bash
# Associate domain with site
bench setup add-domain --site mysite.localhost example.com

# Install Certbot
sudo snap install --classic certbot
sudo ln -sf /snap/bin/certbot /usr/bin/certbot

# Enable DNS multitenancy (required for custom domains)
bench config dns_multitenant on

# Regenerate Nginx config
bench setup nginx
sudo service nginx restart

# Get SSL certificate (interactive)
sudo certbot --nginx

# Test auto-renewal
sudo certbot renew --dry-run

# Regenerate Nginx after cert
bench setup nginx
sudo service nginx restart
```

**site_config.json with SSL paths:**

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

---

### Exposing Local Dev with ngrok

ngrok tunnels external traffic to your local Frappe instance — essential for testing webhooks and payment gateway callbacks.

```bash
cd frappe-bench/
bench pip install pyngrok

# Store authtoken (get from https://dashboard.ngrok.com/authtokens)
bench --site mysite set-config ngrok_authtoken YOUR_TOKEN
bench --site mysite set-config http_port 8000

# Start bench first
bench start

# In another terminal, start the tunnel
bench --site mysite ngrok --bind-tls
# → Public URL: https://abc123.ngrok.io
```

**Manual ngrok (alternative):**

```bash
ngrok authtoken YOUR_TOKEN  # one-time setup
ngrok http 8000
```

**Free plan limitations:** Random subdomain each restart, bandwidth limits. For stable URLs, use Cloudflare Tunnel (free, no limits).

---

### Docker Deployment

**Building a custom image with your app:**

```bash
# 1. Create apps.json listing all apps to include
cat > apps.json << 'EOF'
[
  {"url": "https://github.com/frappe/erpnext", "branch": "version-15"},
  {"url": "https://github.com/myorg/my-custom-app", "branch": "main"}
]
EOF

# 2. Encode to base64
export APPS_JSON_BASE64=$(base64 -w 0 apps.json)

# 3. Clone frappe_docker
git clone https://github.com/frappe/frappe_docker
cd frappe_docker

# 4. Build image
docker build \
  --no-cache \
  --progress=plain \
  --build-arg FRAPPE_BRANCH=version-15 \
  --build-arg APPS_JSON_BASE64=$APPS_JSON_BASE64 \
  --file images/layered/Containerfile \
  --tag myorg/my-frappe-app:latest \
  .

# 5. Push to Docker Hub
docker login -u myorg  # use Personal Access Token as password
docker push myorg/my-frappe-app:latest
```

**Running with Docker Compose:**

```yaml
# compose.yaml — minimal production setup
services:
  configurator:
    image: myorg/my-frappe-app:latest
    restart: on-failure
    entrypoint: ["bash", "-c"]
    command: >
      bench set-config -g db_host $DB_HOST;
      bench set-config -g redis_cache "redis://$REDIS_CACHE";
      bench set-config -g redis_queue "redis://$REDIS_QUEUE";
    environment:
      DB_HOST: db
      REDIS_CACHE: redis-cache:6379
      REDIS_QUEUE: redis-queue:6379
    volumes:
      - sites:/home/frappe/frappe-bench/sites
    depends_on:
      db:
        condition: service_healthy

  backend:
    image: myorg/my-frappe-app:latest
    restart: unless-stopped
    volumes:
      - sites:/home/frappe/frappe-bench/sites
    depends_on:
      configurator:
        condition: service_completed_successfully

  frontend:
    image: myorg/my-frappe-app:latest
    command: nginx-entrypoint.sh
    environment:
      BACKEND: backend:8000
      SOCKETIO: websocket:9000
      FRAPPE_SITE_NAME_HEADER: $host
    volumes:
      - sites:/home/frappe/frappe-bench/sites
    ports:
      - "8080:8080"
    depends_on:
      - backend

  websocket:
    image: myorg/my-frappe-app:latest
    command: node /home/frappe/frappe-bench/apps/frappe/socketio.js
    volumes:
      - sites:/home/frappe/frappe-bench/sites

  queue-short:
    image: myorg/my-frappe-app:latest
    command: bench worker --queue short,default
    volumes:
      - sites:/home/frappe/frappe-bench/sites

  scheduler:
    image: myorg/my-frappe-app:latest
    command: bench schedule
    volumes:
      - sites:/home/frappe/frappe-bench/sites

  db:
    image: mariadb:10.6
    environment:
      MYSQL_ROOT_PASSWORD: ${DB_PASSWORD:-admin}
    healthcheck:
      test: mysqladmin ping -h localhost --password=${DB_PASSWORD:-admin}
      interval: 1s
      retries: 20
    volumes:
      - db-data:/var/lib/mysql

  redis-cache:
    image: redis:6.2-alpine

  redis-queue:
    image: redis:6.2-alpine

volumes:
  sites:
  db-data:
```

```bash
# Start everything
docker compose up -d

# Monitor site creation
docker logs frappe_container-create-site-1 -f

# Check all services
docker compose ps
```

---

### Dev Container Setup for Local Development

Dev Containers give every developer an identical environment without installing anything locally.

```bash
# One-time setup
git clone https://github.com/frappe/frappe_docker.git
cd frappe_docker
cp -R devcontainer-example .devcontainer
cp -R development/vscode-example development/.vscode
code .
# Ctrl+Shift+P → "Dev Containers: Reopen in Container"
```

**Inside the container:**

```bash
bench init --skip-redis-config-generation frappe-bench
cd frappe-bench

bench set-config -g db_host mariadb
bench set-config -g redis_cache redis://redis-cache:6379
bench set-config -g redis_queue redis://redis-queue:6379
bench set-config -g redis_socketio redis://redis-queue:6379

bench new-site \
  --db-root-password 123 \
  --admin-password admin \
  --mariadb-user-host-login-scope=% \
  development.localhost

bench start
# Access at http://development.localhost:8000
```

**Daily workflow:**
1. Open VS Code → navigate to `frappe_docker`
2. `Ctrl+Shift+P` → "Dev Containers: Reopen in Container"
3. Open terminal → `bench start`
4. To stop: `Ctrl+Shift+P` → "Dev Containers: Reopen Folder Locally"
