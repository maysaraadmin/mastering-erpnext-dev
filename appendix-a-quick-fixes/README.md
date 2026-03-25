# Appendix A: Quick Fix Guides

## 🎯 Purpose

This appendix provides quick solutions to common Frappe/ERPNext issues that developers frequently encounter. These are practical, tested solutions that can be implemented immediately to resolve problems and get your system running smoothly.

## 📚 Quick Fix Categories

### A.1 Common Frappe Issues

#### Issue: "Site does not exist" Error

**Symptoms:**
- Getting "Site does not exist" error when accessing site
- Site not showing in bench sites list

**Quick Fix:**
```bash
# Check if site exists
bench --site your-site.local doctor

# Recreate site if missing
bench new-site your-site.local

# Or restore from backup
bench --site your-site.local restore --with-files /path/to/backup.sql.gz
```

#### Issue: Migration Failed - Duplicate Entry

**Symptoms:**
- Migration failing with duplicate key error
- Patch execution stopped midway

**Quick Fix:**
```bash
# Check what failed
bench --site your-site.local migrate

# Check duplicate records
bench --site your-site.local console

# In console:
frappe.db.sql("SELECT name, COUNT(*) as count FROM `tabUser` GROUP BY name HAVING count > 1")

# Remove duplicates (example for User table)
frappe.db.sql("""
    DELETE u1 FROM `tabUser` u1
    INNER JOIN `tabUser` u2 
    WHERE u1.name > u2.name AND u1.email = u2.email
""")

# Continue migration
bench --site your-site.local migrate
```

#### Issue: Background Jobs Not Running

**Symptoms:**
- Scheduled tasks not executing
- Email notifications not sending
- Reports stuck in queue

**Quick Fix:**
```bash
# Check worker status
bench doctor

# Restart workers
bench restart

# Clear job queue
bench --site your-site.local console

# In console:
from frappe.queues import get_queue
queue = get_queue('default')
queue.empty()

# Check scheduler
bench --site your-site.local scheduler status

# Enable scheduler if disabled
bench --site your-site.local enable-scheduler
```

#### Issue: Redis Connection Failed

**Symptoms:**
- Cache errors in logs
- Slow page loading
- Session issues

**Quick Fix:**
```bash
# Check Redis status
redis-cli ping

# Restart Redis
sudo systemctl restart redis

# Clear Redis cache
redis-cli flushall

# Check Redis configuration
redis-cli config get maxmemory
redis-cli config get save
```

### A.2 Database Issues

#### Issue: Database Connection Timeout

**Symptoms:**
- "Too many connections" error
- Slow database responses
- Connection refused errors

**Quick Fix:**
```bash
# Check current connections
bench --site your-site.local mariadb

# In MariaDB:
SHOW PROCESSLIST;
SHOW STATUS LIKE 'Threads_connected';

# Kill long-running queries
KILL <process-id>;

# Increase connections temporarily
SET GLOBAL max_connections = 500;

# Restart services
bench restart
```

#### Issue: Slow Query Performance

**Symptoms:**
- Reports taking minutes to load
- API timeouts
- High CPU usage

**Quick Fix:**
```bash
# Enable slow query log
bench --site your-site.local console

# In console:
frappe.db.sql("SET GLOBAL slow_query_log = 'ON'");
frappe.db.sql("SET GLOBAL long_query_time = 2");

# Check slow queries
tail -f /var/log/mysql/mysql-slow.log

# Add indexes for common queries
bench --site your-site.local console

# Example: Add index for Sales Order reports
frappe.db.sql("CREATE INDEX idx_so_date_status ON `tabSales Order`(posting_date, docstatus, company)");
```

#### Issue: Database Corruption

**Symptoms:**
- Table doesn't exist errors
- Data inconsistency
- Crash on specific operations

**Quick Fix:**
```bash
# Check table integrity
bench --site your-site.local mariadb

# In MariaDB:
CHECK TABLE `tabSales Order`;
REPAIR TABLE `tabSales Order`;

# For severe corruption:
bench --site your-site.local backup
bench --site your-site.local restore --with-files /path/to/latest/backup.sql.gz
```

### A.3 Frontend Issues

#### Issue: White Screen on Login

**Symptoms:**
- Blank page after login
- JavaScript errors in console
- Loading spinner stuck

**Quick Fix:**
```bash
# Clear browser cache and cookies
# In browser: Ctrl+Shift+Delete

# Clear Frappe cache
bench clear-cache
bench build

# Check for JavaScript errors
# Open browser developer tools (F12) and check Console tab

# Rebuild assets
bench build --app your_app
```

#### Issue: Form Fields Not Loading

**Symptoms:**
- Form fields not appearing
- Loading indicator stuck
- Data not populating

**Quick Fix:**
```bash
# Check DocType definition
bench --site your-site.local console

# In console:
doc = frappe.get_doc('Your DocType', 'doc-name')
print(doc.as_dict())

# Check custom scripts
bench --site your-site.local reload-doc

# Clear cache and rebuild
bench clear-cache
bench build
```

#### Issue: Print Format Not Working

**Symptoms:**
- Print preview blank
- PDF generation failed
- Format not applied

**Quick Fix:**
```bash
# Check print format exists
bench --site your-site.local console

# In console:
frappe.get_doc('Print Format', 'Your Format')

# Rebuild print formats
bench build

# Check Jinja syntax
bench --site your-site.local console

# Test print format
frappe.get_print('Your DocType', 'doc-name', 'Your Format')
```

### A.4 Performance Issues

#### Issue: Site Running Slow

**Symptoms:**
- Page loading taking >10 seconds
- High memory usage
- CPU spikes

**Quick Fix:**
```bash
# Check system resources
free -h
top
htop

# Check Frappe processes
ps aux | grep frappe

# Clear cache
bench clear-cache

# Check background jobs
bench --site your-site.local show-jobs

# Restart services
bench restart

# Optimize database
bench --site your-site.local mariadb

# In MariaDB:
OPTIMIZE TABLE `tabSales Order`;
OPTIMIZE TABLE `tabPurchase Order`;
```

#### Issue: Memory Exhaustion

**Symptoms:**
- Out of memory errors
- Services crashing
- Swap space full

**Quick Fix:**
```bash
# Check memory usage
free -h
ps aux --sort=-%mem | head

# Clear Redis cache
redis-cli flushall

# Reduce worker count
bench config workers_per_process 2
bench setup supervisor
bench restart

# Increase swap space
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### A.5 File and Upload Issues

#### Issue: File Upload Failed

**Symptoms:**
- Upload stuck at 100%
- File not appearing
- Permission denied errors

**Quick Fix:**
```bash
# Check file permissions
ls -la sites/your-site.local/public/files/

# Fix permissions
sudo chown -R frappe:frappe sites/your-site.local/public/files/
sudo chmod -R 755 sites/your-site.local/public/files/

# Check disk space
df -h

# Increase upload limit
bench --site your-site.local set-config max_file_size 52428800  # 50MB
```

#### Issue: Backup Failed

**Symptoms:**
- Backup process hanging
- Incomplete backup files
- Permission denied

**Quick Fix:**
```bash
# Check backup directory
ls -la sites/your-site.local/private/backups/

# Fix permissions
sudo chown -R frappe:frappe sites/your-site.local/private/backups/

# Check disk space
df -h

# Manual backup
bench --site your-site.local backup --with-files

# Verify backup
ls -la sites/your-site.local/private/backups/*.sql.gz
```

### A.6 Email Issues

#### Issue: Emails Not Sending

**Symptoms:**
- Outgoing emails stuck
- SMTP connection errors
- Email queue not processing

**Quick Fix:**
```bash
# Check email queue
bench --site your-site.local show-outgoing-emails

# Test email configuration
bench --site your-site.local email-test

# Check email settings
bench --site your-site.local console

# In console:
print(frappe.get_doc('Email Account', 'Default'))

# Restart workers
bench restart

# Check logs
tail -f sites/your-site.local/logs/email.log
```

### A.7 API and Integration Issues

#### Issue: API Calls Failing

**Symptoms:**
- 403 Forbidden errors
- API timeout
- Invalid token errors

**Quick Fix:**
```bash
# Check API permissions
bench --site your-site.local console

# In console:
from frappe.permissions import get_roles
print(get_roles())

# Check API key
frappe.get_doc('API Key', 'your-api-key')

# Regenerate API key
bench --site your-site.local generate-api-key

# Check rate limiting
bench --site your-site.local console

# Clear rate limit cache
frappe.cache().delete_keys('*rate_limit*')
```

### A.8 Development Environment Issues

#### Issue: Bench Start Failed

**Symptoms:**
- Services not starting
- Port conflicts
- Permission errors

**Quick Fix:**
```bash
# Check what's using port 8000
sudo netstat -tlnp | grep :8000

# Kill conflicting process
sudo kill -9 <pid>

# Check permissions
ls -la config/
sudo chown -R frappe:frappe config/

# Start bench
bench start

# Check status
bench doctor
```

#### Issue: App Installation Failed

**Symptoms:**
- App not installing
- Dependency conflicts
- Migration errors

**Quick Fix:**
```bash
# Check app compatibility
bench get-app --branch version-14 your_app

# Force reinstall
bench --site your-site.local uninstall-app your_app
bench --site your-site.local install-app your_app

# Check dependencies
bench setup requirements

# Manual migration
bench --site your-site.local migrate --patch your_app_patches
```

### A.9 Security Issues

#### Issue: Permission Errors

**Symptoms:**
- Access denied errors
- Role not working
- Permission query failing

**Quick Fix:**
```bash
# Check user roles
bench --site your-site.local console

# In console:
user = frappe.get_doc('User', 'your-email@example.com')
print([role.role for role in user.roles])

# Reset permissions
frappe.clear_cache()
frappe.reload_doc('DocType', 'User', 'permissions')

# Check role permissions
role = frappe.get_doc('Role', 'System Manager')
print(role.permissions)
```

#### Issue: Login Issues

**Symptoms:**
- Can't login with correct password
- Session expired immediately
- Two-factor authentication problems

**Quick Fix:**
```bash
# Reset password
bench --site your-site.local reset-password user@example.com

# Clear session cache
redis-cli flushall

# Check session settings
bench --site your-site.local console

# In console:
print(frappe.local.session.get('session_expiry'))

# Reset two-factor authentication
bench --site your-site.local console

# In console:
user = frappe.get_doc('User', 'user@example.com')
user.enable_two_factor_auth = 0
user.save()
```

### A.10 Docker and Container Issues

#### Issue: Container Not Starting

**Symptoms:**
- Docker container failing to start
- Port binding errors
- Volume mounting issues

**Quick Fix:**
```bash
# Check Docker status
sudo systemctl status docker

# Check container logs
docker logs frappe-app

# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Check volume mounts
docker inspect frappe-app | grep Mounts
```

#### Issue: Database Connection in Docker

**Symptoms:**
- Can't connect to database
- Connection refused errors
- Network issues

**Quick Fix:**
```bash
# Check network
docker network ls
docker network inspect frappe_default

# Restart database container
docker-compose restart db

# Check database logs
docker logs frappe-db

# Test connection
docker-compose exec frappe-app bench --site site1.local doctor
```

---

## 🎯 **Preventive Measures**

### **Regular Maintenance Tasks**

**Daily:**
- Monitor system resources
- Check error logs
- Verify backup completion
- Monitor job queue

**Weekly:**
- Clean up temporary files
- Check disk space usage
- Review slow queries
- Update security patches

**Monthly:**
- Database optimization
- Performance baseline review
- Security audit
- Backup verification

### **Monitoring Scripts**

**Basic Health Check:**
```bash
#!/bin/bash
# health_check.sh

echo "=== Frappe Health Check ==="
echo "Date: $(date)"
echo ""

# Check services
echo "Services Status:"
bench doctor
echo ""

# Check resources
echo "System Resources:"
free -h
echo ""

# Check disk space
echo "Disk Usage:"
df -h
echo ""

# Check recent errors
echo "Recent Errors:"
tail -n 20 sites/*/logs/*.log | grep -i error
echo ""

# Check job queue
echo "Job Queue:"
bench --site your-site.local show-jobs | tail -n 10
```

**Automated Alerts:**
```python
# monitor.py
import frappe
import psutil
import requests

def check_system_health():
    alerts = []
    
    # Check CPU
    cpu_percent = psutil.cpu_percent(interval=1)
    if cpu_percent > 80:
        alerts.append(f"High CPU usage: {cpu_percent}%")
    
    # Check Memory
    memory = psutil.virtual_memory()
    if memory.percent > 85:
        alerts.append(f"High memory usage: {memory.percent}%")
    
    # Check Disk
    disk = psutil.disk_usage('/')
    if (disk.used / disk.total) * 100 > 90:
        alerts.append(f"Low disk space: {(disk.used / disk.total) * 100:.1f}%")
    
    # Check Frappe services
    try:
        response = requests.get('http://localhost:8000/api/method/version', timeout=5)
        if response.status_code != 200:
            alerts.append("Frappe application not responding")
    except:
        alerts.append("Frappe application unreachable")
    
    # Send alerts (example: email, Slack, etc.)
    if alerts:
        send_alerts(alerts)

def send_alerts(alerts):
    """Send alerts to monitoring system"""
    for alert in alerts:
        print(f"ALERT: {alert}")
        # Add your alerting logic here
```

---

## 🎯 **Emergency Procedures**

### **Complete System Recovery**

**When to use:** System completely unresponsive

**Steps:**
```bash
# 1. Force restart services
sudo systemctl restart mysql
sudo systemctl restart redis
bench restart

# 2. Check system status
bench doctor

# 3. Clear all caches
redis-cli flushall
bench clear-cache

# 4. Verify database integrity
bench --site your-site.local mariadb
CHECK TABLE `tabUser`;

# 5. Run full migration
bench --site your-site.local migrate

# 6. Test basic functionality
bench --site your-site.local console
frappe.get_doc('User', 'Administrator')
```

### **Database Recovery**

**When to use:** Database corruption suspected

**Steps:**
```bash
# 1. Stop all services
bench stop

# 2. Backup current state
cp -r sites/your-site.local/database sites/your-site.local/database.backup

# 3. Restore from last known good backup
bench --site your-site.local restore --with-files /path/to/backup.sql.gz

# 4. Verify data integrity
bench --site your-site.local doctor

# 5. Restart services
bench start
```

---

**💡 Pro Tip:** Keep this appendix bookmarked for quick reference. Most issues can be resolved with these quick fixes before needing deeper troubleshooting. Always backup before applying fixes that modify data.
