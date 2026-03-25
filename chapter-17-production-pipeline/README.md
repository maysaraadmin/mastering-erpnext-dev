# Chapter 17: The Production Pipeline - Deployment & Monitoring

## 🎯 Learning Objectives

By the end of this chapter, you will master:
- **Setting up production** Bench architecture with best practices
- **Implementing security** hardening for production environments
- **Creating robust** backup and disaster recovery strategies
- **Achieving zero-downtime** deployment techniques
- **Managing patches** and migrations safely
- **Implementing comprehensive** monitoring and alerting

## 📚 Chapter Topics

### 17.1 Production Bench Architecture

**Understanding Production Architecture**

```python
# production/architecture.py - Production architecture configuration

"""
Production Frappe Architecture Components:

1. Load Balancer (Nginx)
   - SSL termination
   - Static asset serving
   - Request routing
   - Rate limiting

2. Web Servers (Gunicorn)
   - Application serving
   - Worker processes
   - Request handling
   - Error handling

3. Database Server (MariaDB/MySQL)
   - Data persistence
   - Query optimization
   - Replication
   - Backup management

4. Cache Layer (Redis)
   - Session storage
   - Query caching
   - Background jobs
   - Real-time features

5. File Storage
   - Local filesystem
   - Cloud storage (S3)
   - CDN integration
   - Backup storage

6. Monitoring Stack
   - Application monitoring
   - Database monitoring
   - System monitoring
   - Log aggregation
"""

class ProductionArchitecture:
    """Production architecture configuration and validation"""
    
    REQUIRED_COMPONENTS = {
        'nginx': 'Web server and load balancer',
        'gunicorn': 'Application server',
        'mariadb': 'Database server',
        'redis': 'Cache and session storage',
        'supervisor': 'Process management',
        'cron': 'Scheduled tasks'
    }
    
    RECOMMENDED_SPECS = {
        'small': {
            'cpu': '2 cores',
            'ram': '4GB',
            'storage': '50GB SSD',
            'concurrent_users': '10-25'
        },
        'medium': {
            'cpu': '4 cores',
            'ram': '8GB',
            'storage': '100GB SSD',
            'concurrent_users': '25-100'
        },
        'large': {
            'cpu': '8 cores',
            'ram': '16GB',
            'storage': '200GB SSD',
            'concurrent_users': '100-500'
        },
        'enterprise': {
            'cpu': '16+ cores',
            'ram': '32GB+',
            'storage': '500GB+ SSD',
            'concurrent_users': '500+'
        }
    }
    
    @classmethod
    def validate_production_setup(cls, bench_path):
        """Validate production bench setup"""
        
        validation_results = {
            'status': 'pending',
            'checks': [],
            'recommendations': [],
            'errors': []
        }
        
        # Check required components
        for component, description in cls.REQUIRED_COMPONENTS.items():
            check_result = cls._check_component(component, bench_path)
            validation_results['checks'].append(check_result)
            
            if not check_result['status']:
                validation_results['errors'].append(f"Missing {component}: {description}")
        
        # Check system resources
        resource_check = cls._check_system_resources()
        validation_results['checks'].append(resource_check)
        
        # Check security configuration
        security_check = cls._check_security_configuration(bench_path)
        validation_results['checks'].append(security_check)
        
        # Check backup configuration
        backup_check = cls._check_backup_configuration(bench_path)
        validation_results['checks'].append(backup_check)
        
        # Overall status
        if validation_results['errors']:
            validation_results['status'] = 'failed'
        elif any(check['status'] == 'warning' for check in validation_results['checks']):
            validation_results['status'] = 'warning'
        else:
            validation_results['status'] = 'passed'
        
        return validation_results
    
    @classmethod
    def _check_component(cls, component, bench_path):
        """Check if component is properly installed and configured"""
        
        try:
            if component == 'nginx':
                return cls._check_nginx()
            elif component == 'gunicorn':
                return cls._check_gunicorn(bench_path)
            elif component == 'mariadb':
                return cls._check_mariadb()
            elif component == 'redis':
                return cls._check_redis()
            elif component == 'supervisor':
                return cls._check_supervisor()
            elif component == 'cron':
                return cls._check_cron()
            else:
                return {'component': component, 'status': 'unknown', 'message': 'Unknown component'}
        
        except Exception as e:
            return {
                'component': component,
                'status': 'error',
                'message': f"Check failed: {str(e)}"
            }
    
    @classmethod
    def _check_nginx(cls):
        """Check Nginx configuration"""
        
        import subprocess
        
        try:
            # Check if nginx is running
            result = subprocess.run(['systemctl', 'is-active', 'nginx'], 
                                  capture_output=True, text=True)
            
            if result.stdout.strip() != 'active':
                return {
                    'component': 'nginx',
                    'status': 'failed',
                    'message': 'Nginx is not running'
                }
            
            # Check configuration
            config_result = subprocess.run(['nginx', '-t'], 
                                         capture_output=True, text=True)
            
            if config_result.returncode != 0:
                return {
                    'component': 'nginx',
                    'status': 'failed',
                    'message': 'Nginx configuration error',
                    'details': config_result.stderr
                }
            
            return {
                'component': 'nginx',
                'status': 'passed',
                'message': 'Nginx is running and configured correctly'
            }
        
        except FileNotFoundError:
            return {
                'component': 'nginx',
                'status': 'failed',
                'message': 'Nginx is not installed'
            }
    
    @classmethod
    def _check_gunicorn(cls, bench_path):
        """Check Gunicorn configuration"""
        
        try:
            # Check if gunicorn processes are running
            import psutil
            
            gunicorn_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if 'gunicorn' in proc.info['name'] or any('gunicorn' in arg for arg in proc.info['cmdline'] or []):
                        gunicorn_processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if not gunicorn_processes:
                return {
                    'component': 'gunicorn',
                    'status': 'failed',
                    'message': 'No Gunicorn processes found'
                }
            
            # Check configuration file
            config_file = os.path.join(bench_path, 'config', 'gunicorn.conf.py')
            if not os.path.exists(config_file):
                return {
                    'component': 'gunicorn',
                    'status': 'warning',
                    'message': 'Gunicorn config file not found'
                }
            
            return {
                'component': 'gunicorn',
                'status': 'passed',
                'message': f'Gunicorn running with {len(gunicorn_processes)} processes'
            }
        
        except ImportError:
            return {
                'component': 'gunicorn',
                'status': 'warning',
                'message': 'psutil not available for process checking'
            }
    
    @classmethod
    def _check_mariadb(cls):
        """Check MariaDB/MySQL configuration"""
        
        try:
            import frappe
            
            # Test database connection
            frappe.db.commit()
            
            # Check database version
            version = frappe.db.sql("SELECT VERSION() as version", as_dict=True)[0]
            
            # Check important configuration
            config_checks = []
            
            # Check innodb_buffer_pool_size
            buffer_pool = frappe.db.sql("SHOW VARIABLES LIKE 'innodb_buffer_pool_size'", as_dict=True)
            if buffer_pool:
                buffer_size_mb = int(buffer_pool[0]['Value']) / (1024 * 1024)
                config_checks.append(f"Buffer pool: {buffer_size_mb:.0f}MB")
            
            # Check max_connections
            max_conn = frappe.db.sql("SHOW VARIABLES LIKE 'max_connections'", as_dict=True)
            if max_conn:
                config_checks.append(f"Max connections: {max_conn[0]['Value']}")
            
            return {
                'component': 'mariadb',
                'status': 'passed',
                'message': f'MariaDB {version["version"]} running',
                'details': config_checks
            }
        
        except Exception as e:
            return {
                'component': 'mariadb',
                'status': 'failed',
                'message': f'Database connection failed: {str(e)}'
            }
    
    @classmethod
    def _check_redis(cls):
        """Check Redis configuration"""
        
        try:
            import redis
            
            # Test Redis connection
            r = redis.Redis(host='localhost', port=6379, db=0)
            r.ping()
            
            # Get Redis info
            info = r.info()
            
            checks = [
                f"Version: {info.get('redis_version', 'unknown')}",
                f"Memory: {info.get('used_memory_human', 'unknown')}",
                f"Connected clients: {info.get('connected_clients', 'unknown')}"
            ]
            
            return {
                'component': 'redis',
                'status': 'passed',
                'message': 'Redis is running and accessible',
                'details': checks
            }
        
        except ImportError:
            return {
                'component': 'redis',
                'status': 'warning',
                'message': 'Redis Python client not installed'
            }
        
        except Exception as e:
            return {
                'component': 'redis',
                'status': 'failed',
                'message': f'Redis connection failed: {str(e)}'
            }
    
    @classmethod
    def _check_system_resources(cls):
        """Check system resources"""
        
        try:
            import psutil
            
            # CPU info
            cpu_count = psutil.cpu_count()
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory info
            memory = psutil.virtual_memory()
            
            # Disk info
            disk = psutil.disk_usage('/')
            
            recommendations = []
            
            # Check CPU usage
            if cpu_percent > 80:
                recommendations.append('High CPU usage detected')
            
            # Check memory usage
            if memory.percent > 80:
                recommendations.append('High memory usage detected')
            
            # Check disk space
            if disk.percent > 80:
                recommendations.append('Low disk space')
            
            status = 'passed' if not recommendations else 'warning'
            
            return {
                'component': 'system_resources',
                'status': status,
                'message': f'CPU: {cpu_count} cores ({cpu_percent}% used), Memory: {memory.percent}% used, Disk: {disk.percent}% used',
                'recommendations': recommendations
            }
        
        except ImportError:
            return {
                'component': 'system_resources',
                'status': 'warning',
                'message': 'psutil not available for resource monitoring'
            }
    
    @classmethod
    def _check_security_configuration(cls, bench_path):
        """Check security configuration"""
        
        security_issues = []
        
        try:
            # Check if developer mode is disabled
            site_config = os.path.join(bench_path, 'sites', 'common_site_config.json')
            
            if os.path.exists(site_config):
                with open(site_config, 'r') as f:
                    config = json.load(f)
                
                if config.get('developer_mode'):
                    security_issues.append('Developer mode is enabled in production')
                
                if not config.get('maintenance_mode', False):
                    # Check if maintenance mode can be enabled
                    pass
            
            # Check file permissions
            bench_permissions = oct(os.stat(bench_path).st_mode)[-3:]
            if bench_permissions != '755':
                security_issues.append(f'Incorrect bench permissions: {bench_permissions}')
            
            # Check for sensitive files in web root
            sensitive_files = ['.env', 'site_config.json']
            for sensitive_file in sensitive_files:
                for root, dirs, files in os.walk(bench_path):
                    if sensitive_file in files:
                        file_path = os.path.join(root, sensitive_file)
                        if 'public' in file_path or 'www' in file_path:
                            security_issues.append(f'Sensitive file accessible via web: {file_path}')
            
            status = 'passed' if not security_issues else 'warning'
            
            return {
                'component': 'security',
                'status': status,
                'message': f'Security check completed',
                'issues': security_issues
            }
        
        except Exception as e:
            return {
                'component': 'security',
                'status': 'error',
                'message': f'Security check failed: {str(e)}'
            }
    
    @classmethod
    def _check_backup_configuration(cls, bench_path):
        """Check backup configuration"""
        
        backup_checks = []
        
        try:
            # Check if backup directory exists
            backup_dir = os.path.join(bench_path, 'sites', 'backups')
            if not os.path.exists(backup_dir):
                backup_checks.append('Backup directory does not exist')
            else:
                # Check backup directory permissions
                backup_perms = oct(os.stat(backup_dir).st_mode)[-3:]
                if backup_perms not in ['755', '750']:
                    backup_checks.append(f'Incorrect backup directory permissions: {backup_perms}')
            
            # Check for recent backups
            if os.path.exists(backup_dir):
                backup_files = [f for f in os.listdir(backup_dir) if f.endswith('.sql.gz') or f.endswith('.tar.gz')]
                if backup_files:
                    # Get latest backup file
                    latest_backup = max([os.path.join(backup_dir, f) for f in backup_files], key=os.path.getctime)
                    backup_age = (time.time() - os.path.getctime(latest_backup)) / 3600  # hours
                    
                    if backup_age > 48:  # 48 hours
                        backup_checks.append(f'Last backup is {backup_age:.1f} hours old')
                else:
                    backup_checks.append('No backup files found')
            
            # Check cron jobs for backup
            try:
                cron_result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
                if 'backup' not in cron_result.stdout.lower():
                    backup_checks.append('No backup cron job found')
            except:
                backup_checks.append('Could not check cron jobs')
            
            status = 'passed' if not backup_checks else 'warning'
            
            return {
                'component': 'backup',
                'status': status,
                'message': 'Backup configuration checked',
                'issues': backup_checks
            }
        
        except Exception as e:
            return {
                'component': 'backup',
                'status': 'error',
                'message': f'Backup check failed: {str(e)}'
            }

# Production setup validation command
def validate_production_environment(bench_path):
    """Validate production environment setup"""
    
    print("=== Production Environment Validation ===\n")
    
    validation = ProductionArchitecture.validate_production_setup(bench_path)
    
    print(f"Overall Status: {validation['status'].upper()}\n")
    
    # Show detailed results
    for check in validation['checks']:
        status_icon = {
            'passed': '✓',
            'warning': '⚠',
            'failed': '✗',
            'error': '❌'
        }.get(check['status'], '?')
        
        print(f"{status_icon} {check['component']}: {check['message']}")
        
        if check.get('details'):
            for detail in check['details']:
                print(f"    - {detail}")
        
        if check.get('issues'):
            for issue in check['issues']:
                print(f"    ⚠ {issue}")
        
        if check.get('recommendations'):
            for rec in check['recommendations']:
                print(f"    → {rec}")
        
        print()
    
    # Show errors
    if validation['errors']:
        print("ERRORS:")
        for error in validation['errors']:
            print(f"  ✗ {error}")
        print()
    
    # Recommendations
    if validation['recommendations']:
        print("RECOMMENDATIONS:")
        for rec in validation['recommendations']:
            print(f"  → {rec}")
        print()
    
    return validation
```

**Nginx Production Configuration**

```nginx
# production/nginx/nginx.conf - Production Nginx configuration

# User and worker processes
user www-data;
worker_processes auto;
pid /run/nginx.pid;
include /etc/nginx/modules-enabled/*.conf;

# Events configuration
events {
    worker_connections 1024;
    multi_accept on;
    use epoll;
}

# HTTP configuration
http {
    # Basic settings
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    server_tokens off;

    # Include mime types
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # SSL settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_ecdh_curve secp384r1;
    ssl_session_timeout 10m;
    ssl_session_cache shared:SSL:10m;
    ssl_session_tickets off;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Logging
    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;

    # Gzip compression
    gzip on;
    gzip_vary on;
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

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=1r/s;

    # Upstream configuration
    upstream frappe_backend {
        least_conn;
        server 127.0.0.1:8000 max_fails=3 fail_timeout=30s;
        # Add more servers for load balancing
        # server 127.0.0.1:8001 max_fails=3 fail_timeout=30s;
        keepalive 32;
    }

    # Main server block
    server {
        listen 80;
        server_name your-domain.com www.your-domain.com;
        
        # Redirect to HTTPS
        return 301 https://$server_name$request_uri;
    }

    # HTTPS server block
    server {
        listen 443 ssl http2;
        server_name your-domain.com www.your-domain.com;

        # SSL configuration
        ssl_certificate /etc/ssl/certs/your-domain.crt;
        ssl_certificate_key /etc/ssl/private/your-domain.key;
        ssl_trusted_certificate /etc/ssl/certs/your-domain-chain.crt;

        # Root directory
        root /var/www/html;
        index index.html;

        # Security
        client_max_body_size 100M;
        client_body_buffer_size 128k;
        client_header_buffer_size 1k;
        large_client_header_buffers 4 4k;

        # Static file serving with caching
        location ~* ^/assets/ {
            alias /path/to/your/bench/sites/assets/;
            expires 1y;
            add_header Cache-Control "public, immutable";
            add_header X-Content-Type-Options nosniff;
            
            # Gzip for static files
            gzip_static on;
        }

        # Public files
        location ~* ^/public/ {
            alias /path/to/your/bench/sites/;
            expires 1y;
            add_header Cache-Control "public";
        }

        # Frappe application
        location / {
            proxy_pass http://frappe_backend;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-Host $host;
            proxy_set_header X-Forwarded-Port $server_port;
            
            # Timeouts
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
            
            # Buffer settings
            proxy_buffering on;
            proxy_buffer_size 4k;
            proxy_buffers 8 4k;
            proxy_busy_buffers_size 8k;
            
            # HTTP/1.1 support
            proxy_http_version 1.1;
            proxy_set_header Connection "";
        }

        # API rate limiting
        location ~* ^/api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://frappe_backend;
            include /etc/nginx/proxy_params;
        }

        # Login rate limiting
        location ~* ^/login {
            limit_req zone=login burst=5 nodelay;
            proxy_pass http://frappe_backend;
            include /etc/nginx/proxy_params;
        }

        # Socket.io for real-time features
        location /socket.io/ {
            proxy_pass http://frappe_backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Health check endpoint
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }

        # Deny access to sensitive files
        location ~ /\. {
            deny all;
            access_log off;
            log_not_found off;
        }

        location ~ ~$ {
            deny all;
            access_log off;
            log_not_found off;
        }
    }
}
```

### 17.2 Security Hardening

**Comprehensive Security Configuration**

```python
# production/security/hardening.py - Security hardening implementation

import os
import json
import subprocess
import hashlib
import secrets
from pathlib import Path

class SecurityHardener:
    """Comprehensive security hardening for production"""
    
    SECURITY_CHECKLIST = {
        'system_security': {
            'firewall_configured': 'Firewall rules are properly configured',
            'fail2ban_enabled': 'Fail2ban is running for intrusion prevention',
            'automatic_updates': 'Security updates are automatically applied',
            'ssh_hardening': 'SSH is properly secured',
            'user_permissions': 'User permissions follow principle of least privilege'
        },
        'application_security': {
            'developer_mode_disabled': 'Developer mode is disabled in production',
            'maintenance_mode_configurable': 'Maintenance mode can be enabled',
            'file_permissions': 'File permissions are secure',
            'sensitive_files_protected': 'Sensitive files are not web-accessible',
            'csrf_protection': 'CSRF protection is enabled'
        },
        'database_security': {
            'strong_passwords': 'Database uses strong passwords',
            'limited_access': 'Database access is limited to application',
            'encryption_enabled': 'Data encryption is enabled where appropriate',
            'backup_encryption': 'Backups are encrypted',
            'audit_logging': 'Database audit logging is enabled'
        },
        'network_security': {
            'ssl_certificates': 'Valid SSL certificates are installed',
            'https_only': 'HTTPS is enforced',
            'security_headers': 'Security headers are properly configured',
            'rate_limiting': 'Rate limiting is implemented',
            'ddos_protection': 'DDoS protection measures are in place'
        }
    }
    
    def __init__(self, bench_path):
        self.bench_path = Path(bench_path)
        self.security_report = {
            'status': 'pending',
            'checks': [],
            'vulnerabilities': [],
            'recommendations': []
        }
    
    def harden_system(self):
        """Apply comprehensive security hardening"""
        
        print("Starting security hardening...")
        
        # 1. System security
        self._harden_system_security()
        
        # 2. Application security
        self._harden_application_security()
        
        # 3. Database security
        self._harden_database_security()
        
        # 4. Network security
        self._harden_network_security()
        
        # 5. File permissions
        self._secure_file_permissions()
        
        # 6. Monitoring and logging
        self._setup_security_monitoring()
        
        print("Security hardening completed")
        return self.security_report
    
    def _harden_system_security(self):
        """Harden system-level security"""
        
        print("Hardening system security...")
        
        # Configure firewall
        self._configure_firewall()
        
        # Setup fail2ban
        self._setup_fail2ban()
        
        # Harden SSH
        self._harden_ssh()
        
        # Configure automatic updates
        self._configure_automatic_updates()
        
        # Create security user
        self._create_security_user()
    
    def _configure_firewall(self):
        """Configure UFW firewall"""
        
        try:
            # Enable UFW
            subprocess.run(['ufw', '--force', 'enable'], check=True)
            
            # Allow essential services
            essential_ports = [
                ('ssh', 22),
                ('http', 80),
                ('https', 443)
            ]
            
            for service, port in essential_ports:
                subprocess.run(['ufw', 'allow', f'{port}/{service}'], check=True)
            
            # Deny other ports
            subprocess.run(['ufw', 'default', 'deny', 'incoming'], check=True)
            subprocess.run(['ufw', 'default', 'allow', 'outgoing'], check=True)
            
            self.security_report['checks'].append({
                'component': 'firewall',
                'status': 'passed',
                'message': 'UFW firewall configured and enabled'
            })
            
        except subprocess.CalledProcessError as e:
            self.security_report['vulnerabilities'].append({
                'component': 'firewall',
                'severity': 'high',
                'message': f'Failed to configure firewall: {str(e)}'
            })
    
    def _setup_fail2ban(self):
        """Setup fail2ban for intrusion prevention"""
        
        try:
            # Install fail2ban
            subprocess.run(['apt-get', 'update'], check=True)
            subprocess.run(['apt-get', 'install', '-y', 'fail2ban'], check=True)
            
            # Create fail2ban configuration
            fail2ban_config = """
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3
backend = systemd

[sshd]
enabled = true
port = ssh
logpath = %(sshd_log)s

[nginx-http-auth]
enabled = true
port = http,https
logpath = /var/log/nginx/error.log

[nginx-limit-req]
enabled = true
port = http,https
logpath = /var/log/nginx/error.log
"""
            
            config_path = '/etc/fail2ban/jail.local'
            with open(config_path, 'w') as f:
                f.write(fail2ban_config)
            
            # Restart fail2ban
            subprocess.run(['systemctl', 'restart', 'fail2ban'], check=True)
            subprocess.run(['systemctl', 'enable', 'fail2ban'], check=True)
            
            self.security_report['checks'].append({
                'component': 'fail2ban',
                'status': 'passed',
                'message': 'Fail2ban configured and enabled'
            })
            
        except subprocess.CalledProcessError as e:
            self.security_report['vulnerabilities'].append({
                'component': 'fail2ban',
                'severity': 'medium',
                'message': f'Failed to setup fail2ban: {str(e)}'
            })
    
    def _harden_ssh(self):
        """Harden SSH configuration"""
        
        try:
            ssh_config = """
# SSH Security Configuration
Port 22
Protocol 2
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys
PermitEmptyPasswords no
ChallengeResponseAuthentication no
UsePAM yes
X11Forwarding no
PrintMotd no
PrintLastLog yes
TCPKeepAlive yes
UsePrivilegeSeparation yes
Subsystem sftp /usr/lib/openssh/sftp-server
MaxAuthTries 3
MaxSessions 10
ClientAliveInterval 300
ClientAliveCountMax 2
"""
            
            config_path = '/etc/ssh/sshd_config.d/security.conf'
            with open(config_path, 'w') as f:
                f.write(ssh_config)
            
            # Restart SSH
            subprocess.run(['systemctl', 'restart', 'ssh'], check=True)
            
            self.security_report['checks'].append({
                'component': 'ssh',
                'status': 'passed',
                'message': 'SSH configuration hardened'
            })
            
        except subprocess.CalledProcessError as e:
            self.security_report['vulnerabilities'].append({
                'component': 'ssh',
                'severity': 'high',
                'message': f'Failed to harden SSH: {str(e)}'
            })
    
    def _configure_automatic_updates(self):
        """Configure automatic security updates"""
        
        try:
            # Install unattended-upgrades
            subprocess.run(['apt-get', 'install', '-y', 'unattended-upgrades'], check=True)
            
            # Configure automatic updates
            update_config = """
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}";
    "${distro_id}:${distro_codename}-security";
    "${distro_id}ESMApps:${distro_codename}-apps-security";
};

Unattended-Upgrade::Automatic-Reboot "false";
Unattended-Upgrade::Remove-Unused-Dependencies "true";
Unattended-Upgrade::Automatic-Reboot-Time "02:00";
"""
            
            config_path = '/etc/apt/apt.conf.d/50unattended-upgrades'
            with open(config_path, 'w') as f:
                f.write(update_config)
            
            # Enable automatic updates
            with open('/etc/apt/apt.conf.d/20auto-upgrades', 'w') as f:
                f.write('APT::Periodic::Update-Package-Lists "1";\n')
                f.write('APT::Periodic::Download-Upgradeable-Packages "1";\n')
                f.write('APT::Periodic::AutocleanInterval "7";\n')
                f.write('APT::Periodic::Unattended-Upgrade "1";\n')
            
            self.security_report['checks'].append({
                'component': 'automatic_updates',
                'status': 'passed',
                'message': 'Automatic security updates configured'
            })
            
        except subprocess.CalledProcessError as e:
            self.security_report['vulnerabilities'].append({
                'component': 'automatic_updates',
                'severity': 'medium',
                'message': f'Failed to configure automatic updates: {str(e)}'
            })
    
    def _harden_application_security(self):
        """Harden Frappe application security"""
        
        print("Hardening application security...")
        
        # Update site configuration
        self._secure_site_config()
        
        # Secure file permissions
        self._secure_application_files()
        
        # Configure security headers
        self._configure_security_headers()
        
        # Setup CSRF protection
        self._setup_csrf_protection()
    
    def _secure_site_config(self):
        """Secure site configuration"""
        
        common_config_path = self.bench_path / 'sites' / 'common_site_config.json'
        
        try:
            # Load existing config
            if common_config_path.exists():
                with open(common_config_path, 'r') as f:
                    config = json.load(f)
            else:
                config = {}
            
            # Apply security settings
            security_config = {
                'developer_mode': 0,
                'maintenance_mode': 0,  # Can be enabled when needed
                'serve_local': 0,
                'allow_signup': 0,
                'disable_signup': 1,
                'restrict_domain': 'your-domain.com',
                'enable_signup': 0,
                'disable_password_reset': 0,
                'restrict_password_reset': 1,
                'hide_standard_menu': 1,
                'loggers': {
                    'frappe': {
                        'level': 'INFO',
                        'log_to_file': True,
                        'filter': 'allow',
                        'handlers': ['frappe']
                    }
                }
            }
            
            config.update(security_config)
            
            # Write updated config
            with open(common_config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            self.security_report['checks'].append({
                'component': 'site_config',
                'status': 'passed',
                'message': 'Site configuration secured'
            })
            
        except Exception as e:
            self.security_report['vulnerabilities'].append({
                'component': 'site_config',
                'severity': 'high',
                'message': f'Failed to secure site config: {str(e)}'
            })
    
    def _secure_application_files(self):
        """Secure application file permissions"""
        
        try:
            # Set bench permissions
            bench_path_str = str(self.bench_path)
            
            # Directory permissions
            subprocess.run(['chmod', '-R', '755', bench_path_str], check=True)
            
            # Secure sensitive files
            sensitive_files = [
                'site_config.json',
                '.env',
                'Procfile'
            ]
            
            for site_dir in self.bench_path.glob('sites/*/'):
                for sensitive_file in sensitive_files:
                    file_path = site_dir / sensitive_file
                    if file_path.exists():
                        subprocess.run(['chmod', '600', str(file_path)], check=True)
            
            # Secure logs directory
            logs_dir = self.bench_path / 'logs'
            if logs_dir.exists():
                subprocess.run(['chmod', '-R', '750', str(logs_dir)], check=True)
            
            self.security_report['checks'].append({
                'component': 'file_permissions',
                'status': 'passed',
                'message': 'Application file permissions secured'
            })
            
        except subprocess.CalledProcessError as e:
            self.security_report['vulnerabilities'].append({
                'component': 'file_permissions',
                'severity': 'medium',
                'message': f'Failed to secure file permissions: {str(e)}'
            })
    
    def _harden_database_security(self):
        """Harden database security"""
        
        print("Hardening database security...")
        
        try:
            import frappe
            
            # Generate strong database passwords
            new_password = self._generate_strong_password()
            
            # Update database user password
            frappe.db.sql("SET PASSWORD = PASSWORD(%s)", (new_password,))
            
            # Update site config with new password
            self._update_database_password(new_password)
            
            # Create limited database user for application
            self._create_limited_db_user()
            
            self.security_report['checks'].append({
                'component': 'database_security',
                'status': 'passed',
                'message': 'Database security hardened'
            })
            
        except Exception as e:
            self.security_report['vulnerabilities'].append({
                'component': 'database_security',
                'severity': 'high',
                'message': f'Failed to harden database: {str(e)}'
            })
    
    def _generate_strong_password(self, length=32):
        """Generate strong password"""
        
        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        return password
    
    def _create_limited_db_user(self):
        """Create limited database user for application"""
        
        # This would create a new database user with limited privileges
        # Implementation depends on specific requirements
        pass
    
    def _harden_network_security(self):
        """Harden network security"""
        
        print("Hardening network security...")
        
        # SSL certificate validation
        self._validate_ssl_certificates()
        
        # Security headers configuration
        self._configure_security_headers()
        
        # Rate limiting setup
        self._setup_rate_limiting()
    
    def _validate_ssl_certificates(self):
        """Validate SSL certificates"""
        
        # Check SSL certificate validity and configuration
        pass
    
    def _configure_security_headers(self):
        """Configure security headers in Nginx"""
        
        # This would update Nginx configuration with security headers
        pass
    
    def _setup_rate_limiting(self):
        """Setup rate limiting"""
        
        # This would configure rate limiting rules
        pass
    
    def _setup_security_monitoring(self):
        """Setup security monitoring and alerting"""
        
        print("Setting up security monitoring...")
        
        # Setup log monitoring
        self._setup_log_monitoring()
        
        # Setup intrusion detection
        self._setup_intrusion_detection()
        
        # Setup security alerts
        self._setup_security_alerts()
    
    def _setup_log_monitoring(self):
        """Setup security log monitoring"""
        
        # Configure log monitoring for security events
        pass
    
    def _setup_intrusion_detection(self):
        """Setup intrusion detection system"""
        
        # Configure intrusion detection rules
        pass
    
    def _setup_security_alerts(self):
        """Setup security alerting"""
        
        # Configure security alert notifications
        pass
    
    def generate_security_report(self):
        """Generate comprehensive security report"""
        
        # Calculate overall security score
        total_checks = len(self.security_report['checks'])
        passed_checks = len([c for c in self.security_report['checks'] if c['status'] == 'passed'])
        
        if total_checks > 0:
            security_score = (passed_checks / total_checks) * 100
        else:
            security_score = 0
        
        # Categorize vulnerabilities
        vulnerabilities = self.security_report['vulnerabilities']
        high_vulns = [v for v in vulnerabilities if v['severity'] == 'high']
        medium_vulns = [v for v in vulnerabilities if v['severity'] == 'medium']
        low_vulns = [v for v in vulnerabilities if v['severity'] == 'low']
        
        report = {
            'security_score': security_score,
            'total_checks': total_checks,
            'passed_checks': passed_checks,
            'vulnerabilities': {
                'high': len(high_vulns),
                'medium': len(medium_vulns),
                'low': len(low_vulns),
                'total': len(vulnerabilities)
            },
            'recommendations': self.security_report['recommendations'],
            'status': 'secure' if security_score >= 90 else 'vulnerable' if security_score >= 70 else 'critical'
        }
        
        return report

# Security hardening command
def harden_production_server(bench_path):
    """Harden production server security"""
    
    print("=== Production Server Security Hardening ===\n")
    
    hardener = SecurityHardener(bench_path)
    hardener.harden_system()
    
    report = hardener.generate_security_report()
    
    print(f"\nSecurity Score: {report['security_score']:.1f}%")
    print(f"Status: {report['status'].upper()}")
    print(f"Checks Passed: {report['passed_checks']}/{report['total_checks']}")
    
    if report['vulnerabilities']['total'] > 0:
        print(f"\nVulnerabilities Found:")
        print(f"  High: {report['vulnerabilities']['high']}")
        print(f"  Medium: {report['vulnerabilities']['medium']}")
        print(f"  Low: {report['vulnerabilities']['low']}")
    
    if report['recommendations']:
        print(f"\nRecommendations:")
        for rec in report['recommendations']:
            print(f"  → {rec}")
    
    return report
```

### 17.3 Backup and Disaster Recovery

**Comprehensive Backup Strategy**

```python
# production/backup/backup_manager.py - Comprehensive backup management

import os
import subprocess
import datetime
import gzip
import shutil
import json
import boto3
from pathlib import Path
from frappe.utils import now_datetime, add_to_date

class BackupManager:
    """Comprehensive backup and disaster recovery management"""
    
    def __init__(self, bench_path, config=None):
        self.bench_path = Path(bench_path)
        self.config = config or self._load_backup_config()
        self.backup_dir = self.bench_path / 'sites' / 'backups'
        self.backup_dir.mkdir(exist_ok=True)
    
    def _load_backup_config(self):
        """Load backup configuration"""
        
        default_config = {
            'database': {
                'enabled': True,
                'compression': True,
                'retention_days': 30,
                'encryption': True
            },
            'files': {
                'enabled': True,
                'include_public_files': True,
                'include_private_files': True,
                'compression': True,
                'retention_days': 30
            },
            'cloud_storage': {
                'enabled': False,
                'provider': 's3',
                'bucket': '',
                'region': 'us-east-1',
                'retention_days': 90
            },
            'schedule': {
                'daily_backup': True,
                'weekly_backup': True,
                'monthly_backup': True,
                'daily_time': '02:00',
                'weekly_day': 'sunday',
                'monthly_day': 1
            },
            'notifications': {
                'email_enabled': True,
                'slack_enabled': False,
                'email_recipients': [],
                'slack_webhook': ''
            }
        }
        
        config_file = self.bench_path / 'backup_config.json'
        if config_file.exists():
            with open(config_file, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        
        return default_config
    
    def create_backup(self, backup_type='daily'):
        """Create comprehensive backup"""
        
        timestamp = now_datetime().strftime('%Y%m%d_%H%M%S')
        backup_info = {
            'timestamp': timestamp,
            'type': backup_type,
            'files': {},
            'status': 'in_progress',
            'start_time': now_datetime(),
            'size': 0
        }
        
        try:
            print(f"Starting {backup_type} backup...")
            
            # 1. Database backup
            if self.config['database']['enabled']:
                db_backup = self._create_database_backup(timestamp)
                backup_info['files']['database'] = db_backup
            
            # 2. Files backup
            if self.config['files']['enabled']:
                files_backup = self._create_files_backup(timestamp)
                backup_info['files']['files'] = files_backup
            
            # 3. Configuration backup
            config_backup = self._create_configuration_backup(timestamp)
            backup_info['files']['config'] = config_backup
            
            # 4. Calculate total size
            backup_info['size'] = self._calculate_backup_size(backup_info['files'])
            
            # 5. Upload to cloud if enabled
            if self.config['cloud_storage']['enabled']:
                self._upload_to_cloud(backup_info)
            
            # 6. Create backup manifest
            self._create_backup_manifest(backup_info)
            
            backup_info['status'] = 'completed'
            backup_info['end_time'] = now_datetime()
            
            print(f"Backup completed successfully. Size: {backup_info['size']:.2f} MB")
            
            # Send notification
            self._send_backup_notification(backup_info, success=True)
            
            return backup_info
            
        except Exception as e:
            backup_info['status'] = 'failed'
            backup_info['error'] = str(e)
            backup_info['end_time'] = now_datetime()
            
            print(f"Backup failed: {str(e)}")
            
            # Send failure notification
            self._send_backup_notification(backup_info, success=False)
            
            raise
    
    def _create_database_backup(self, timestamp):
        """Create database backup"""
        
        print("Creating database backup...")
        
        # Get database configuration
        db_config = self._get_database_config()
        
        # Create database dump
        dump_file = self.backup_dir / f"database_{timestamp}.sql"
        
        mysqldump_cmd = [
            'mysqldump',
            f'--host={db_config["host"]}',
            f'--user={db_config["user"]}',
            f'--password={db_config["password"]}',
            '--single-transaction',
            '--routines',
            '--triggers',
            '--all-databases'
        ]
        
        try:
            with open(dump_file, 'w') as f:
                subprocess.run(mysqldump_cmd, stdout=f, check=True)
            
            # Compress if enabled
            if self.config['database']['compression']:
                compressed_file = self._compress_file(dump_file)
                os.remove(dump_file)
                dump_file = compressed_file
            
            # Encrypt if enabled
            if self.config['database']['encryption']:
                encrypted_file = self._encrypt_file(dump_file)
                os.remove(dump_file)
                dump_file = encrypted_file
            
            backup_info = {
                'file': str(dump_file.name),
                'size': os.path.getsize(dump_file) / (1024 * 1024),  # MB
                'compressed': self.config['database']['compression'],
                'encrypted': self.config['database']['encryption']
            }
            
            print(f"Database backup created: {dump_file.name}")
            return backup_info
            
        except subprocess.CalledProcessError as e:
            raise Exception(f"Database backup failed: {str(e)}")
    
    def _create_files_backup(self, timestamp):
        """Create files backup"""
        
        print("Creating files backup...")
        
        files_info = {
            'public_files': {},
            'private_files': {}
        }
        
        # Backup public files
        if self.config['files']['include_public_files']:
            public_backup = self._backup_directory(
                'public_files',
                self.bench_path / 'sites' / 'assets',
                timestamp
            )
            files_info['public_files'] = public_backup
        
        # Backup private files
        if self.config['files']['include_private_files']:
            private_backup = self._backup_directory(
                'private_files',
                self.bench_path / 'sites' / 'private',
                timestamp
            )
            files_info['private_files'] = private_backup
        
        return files_info
    
    def _backup_directory(self, name, source_dir, timestamp):
        """Backup a directory"""
        
        if not source_dir.exists():
            return {'status': 'skipped', 'reason': 'Directory does not exist'}
        
        backup_file = self.backup_dir / f"{name}_{timestamp}.tar"
        
        try:
            # Create tar archive
            shutil.make_archive(
                str(backup_file.with_suffix('')),
                'tar',
                str(source_dir.parent),
                source_dir.name
            )
            
            backup_file = backup_file.with_suffix('.tar')
            
            # Compress if enabled
            if self.config['files']['compression']:
                compressed_file = self._compress_file(backup_file)
                os.remove(backup_file)
                backup_file = compressed_file
            
            backup_info = {
                'file': str(backup_file.name),
                'size': os.path.getsize(backup_file) / (1024 * 1024),  # MB
                'compressed': self.config['files']['compression']
            }
            
            print(f"Files backup created: {backup_file.name}")
            return backup_info
            
        except Exception as e:
            return {'status': 'failed', 'error': str(e)}
    
    def _create_configuration_backup(self, timestamp):
        """Backup configuration files"""
        
        print("Creating configuration backup...")
        
        config_files = [
            'site_config.json',
            'common_site_config.json',
            'Procfile',
            'requirements.txt'
        ]
        
        config_backup_dir = self.backup_dir / f"config_{timestamp}"
        config_backup_dir.mkdir(exist_ok=True)
        
        backed_up_files = []
        
        for site_dir in self.bench_path.glob('sites/*/'):
            for config_file in config_files:
                source_file = site_dir / config_file
                if source_file.exists():
                    dest_file = config_backup_dir / f"{site_dir.name}_{config_file}"
                    shutil.copy2(source_file, dest_file)
                    backed_up_files.append(str(dest_file.name))
        
        # Create archive
        archive_file = self.backup_dir / f"config_{timestamp}.tar"
        shutil.make_archive(
            str(archive_file.with_suffix('')),
            'tar',
            str(config_backup_dir.parent),
            config_backup_dir.name
        )
        
        # Cleanup
        shutil.rmtree(config_backup_dir)
        
        backup_info = {
            'file': str(archive_file.with_suffix('.tar.gz').name),
            'size': os.path.getsize(archive_file.with_suffix('.tar.gz')) / (1024 * 1024),
            'files_count': len(backed_up_files)
        }
        
        print(f"Configuration backup created: {backup_info['file']}")
        return backup_info
    
    def _compress_file(self, file_path):
        """Compress a file using gzip"""
        
        compressed_path = Path(str(file_path) + '.gz')
        
        with open(file_path, 'rb') as f_in:
            with gzip.open(compressed_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        return compressed_path
    
    def _encrypt_file(self, file_path):
        """Encrypt a file (simplified implementation)"""
        
        # In production, use proper encryption like GPG
        encrypted_path = Path(str(file_path) + '.encrypted')
        
        # For demonstration, just copy the file
        shutil.copy2(file_path, encrypted_path)
        
        return encrypted_path
    
    def _calculate_backup_size(self, backup_files):
        """Calculate total backup size"""
        
        total_size = 0
        
        for category, files in backup_files.items():
            if isinstance(files, dict):
                for file_info in files.values():
                    if isinstance(file_info, dict) and 'size' in file_info:
                        total_size += file_info['size']
            elif isinstance(files, dict) and 'size' in files:
                total_size += files['size']
        
        return total_size
    
    def _upload_to_cloud(self, backup_info):
        """Upload backup to cloud storage"""
        
        if not self.config['cloud_storage']['enabled']:
            return
        
        print("Uploading backup to cloud storage...")
        
        try:
            if self.config['cloud_storage']['provider'] == 's3':
                self._upload_to_s3(backup_info)
            # Add other cloud providers as needed
            
            print("Cloud upload completed")
            
        except Exception as e:
            print(f"Cloud upload failed: {str(e)}")
            # Don't fail the backup if cloud upload fails
    
    def _upload_to_s3(self, backup_info):
        """Upload backup to AWS S3"""
        
        import boto3
        
        s3_config = self.config['cloud_storage']
        
        s3_client = boto3.client(
            's3',
            region_name=s3_config['region']
            # Add AWS credentials configuration
        )
        
        # Upload each file
        for category, files in backup_info['files'].items():
            if isinstance(files, dict):
                for file_info in files.values():
                    if isinstance(file_info, dict) and 'file' in file_info:
                        file_path = self.backup_dir / file_info['file']
                        s3_key = f"backups/{category}/{file_info['file']}"
                        
                        s3_client.upload_file(
                            str(file_path),
                            s3_config['bucket'],
                            s3_key
                        )
    
    def _create_backup_manifest(self, backup_info):
        """Create backup manifest file"""
        
        manifest_file = self.backup_dir / f"manifest_{backup_info['timestamp']}.json"
        
        with open(manifest_file, 'w') as f:
            json.dump(backup_info, f, indent=2, default=str)
    
    def _send_backup_notification(self, backup_info, success=True):
        """Send backup notification"""
        
        if not self.config['notifications']['email_enabled']:
            return
        
        try:
            import frappe
            
            subject = f"Backup {'Success' if success else 'Failed'} - {backup_info['type']}"
            
            message = f"""
Backup Status: {'Success' if success else 'Failed'}
Backup Type: {backup_info['type']}
Timestamp: {backup_info['timestamp']}
Size: {backup_info['size']:.2f} MB
Duration: {(backup_info['end_time'] - backup_info['start_time']).total_seconds():.2f} seconds
"""
            
            if not success:
                message += f"Error: {backup_info.get('error', 'Unknown error')}\n"
            
            # Send email
            frappe.sendmail(
                recipients=self.config['notifications']['email_recipients'],
                subject=subject,
                message=message
            )
            
        except Exception as e:
            print(f"Failed to send notification: {str(e)}")
    
    def restore_backup(self, backup_timestamp):
        """Restore from backup"""
        
        print(f"Starting restore from backup: {backup_timestamp}")
        
        # Load backup manifest
        manifest_file = self.backup_dir / f"manifest_{backup_timestamp}.json"
        
        if not manifest_file.exists():
            raise Exception(f"Backup manifest not found: {backup_timestamp}")
        
        with open(manifest_file, 'r') as f:
            backup_info = json.load(f)
        
        try:
            # 1. Restore database
            if 'database' in backup_info['files']:
                self._restore_database(backup_info['files']['database'])
            
            # 2. Restore files
            if 'files' in backup_info['files']:
                self._restore_files(backup_info['files']['files'])
            
            # 3. Restore configuration
            if 'config' in backup_info['files']:
                self._restore_configuration(backup_info['files']['config'])
            
            print("Restore completed successfully")
            
        except Exception as e:
            print(f"Restore failed: {str(e)}")
            raise
    
    def _restore_database(self, db_backup_info):
        """Restore database from backup"""
        
        print("Restoring database...")
        
        backup_file = self.backup_dir / db_backup_info['file']
        
        # Decrypt if needed
        if db_backup_info.get('encrypted'):
            backup_file = self._decrypt_file(backup_file)
        
        # Decompress if needed
        if db_backup_info.get('compressed'):
            backup_file = self._decompress_file(backup_file)
        
        # Get database configuration
        db_config = self._get_database_config()
        
        # Restore database
        mysql_cmd = [
            'mysql',
            f'--host={db_config["host"]}',
            f'--user={db_config["user"]}',
            f'--password={db_config["password"]}'
        ]
        
        with open(backup_file, 'r') as f:
            subprocess.run(mysql_cmd, stdin=f, check=True)
        
        print("Database restore completed")
    
    def cleanup_old_backups(self):
        """Clean up old backups based on retention policy"""
        
        print("Cleaning up old backups...")
        
        retention_days = self.config['database']['retention_days']
        cutoff_date = add_to_date(now_datetime(), days=-retention_days)
        
        cleaned_files = []
        
        for backup_file in self.backup_dir.glob('*'):
            if backup_file.is_file():
                file_time = datetime.datetime.fromtimestamp(backup_file.stat().st_mtime)
                
                if file_time < cutoff_date:
                    backup_file.unlink()
                    cleaned_files.append(str(backup_file.name))
        
        print(f"Cleaned up {len(cleaned_files)} old backup files")
        return cleaned_files
    
    def _get_database_config(self):
        """Get database configuration"""
        
        # Load from site config
        site_config = self.bench_path / 'sites' / 'common_site_config.json'
        
        if site_config.exists():
            with open(site_config, 'r') as f:
                config = json.load(f)
                return {
                    'host': config.get('db_host', 'localhost'),
                    'user': config.get('db_name', 'root'),
                    'password': config.get('db_password', '')
                }
        
        # Default configuration
        return {
            'host': 'localhost',
            'user': 'root',
            'password': ''
        }

# Backup management commands
def create_scheduled_backup(bench_path, backup_type='daily'):
    """Create scheduled backup"""
    
    backup_manager = BackupManager(bench_path)
    return backup_manager.create_backup(backup_type)

def restore_from_backup(bench_path, backup_timestamp):
    """Restore from backup"""
    
    backup_manager = BackupManager(bench_path)
    return backup_manager.restore_backup(backup_timestamp)

def cleanup_old_backups(bench_path):
    """Clean up old backups"""
    
    backup_manager = BackupManager(bench_path)
    return backup_manager.cleanup_old_backups()
```

### 17.4 Zero-Downtime Deployment

**Advanced Deployment Strategies**

```python
# production/deployment/zero_downtime.py - Zero-downtime deployment implementation

import os
import subprocess
import time
import json
import shutil
from pathlib import Path
from frappe.utils import now_datetime

class ZeroDowntimeDeployer:
    """Zero-downtime deployment manager"""
    
    def __init__(self, bench_path, config=None):
        self.bench_path = Path(bench_path)
        self.config = config or self._load_deployment_config()
        self.deployment_log = []
    
    def _load_deployment_config(self):
        """Load deployment configuration"""
        
        default_config = {
            'strategy': 'blue_green',  # blue_green, rolling, canary
            'health_check': {
                'enabled': True,
                'endpoint': '/health',
                'timeout': 30,
                'retries': 3
            },
            'rollback': {
                'enabled': True,
                'automatic': True,
                'threshold': 5  # failures before rollback
            },
            'backup': {
                'before_deploy': True,
                'after_deploy': False
            },
            'maintenance': {
                'enabled': False,
                'duration': 300  # seconds
            },
            'notifications': {
                'slack_webhook': '',
                'email_recipients': []
            }
        }
        
        config_file = self.bench_path / 'deployment_config.json'
        if config_file.exists():
            with open(config_file, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        
        return default_config
    
    def deploy(self, version=None):
        """Execute zero-downtime deployment"""
        
        deployment_id = now_datetime().strftime('%Y%m%d_%H%M%S')
        
        deployment_info = {
            'id': deployment_id,
            'version': version or 'latest',
            'strategy': self.config['strategy'],
            'status': 'in_progress',
            'start_time': now_datetime(),
            'steps': [],
            'rollback_available': False
        }
        
        try:
            print(f"Starting zero-downtime deployment: {deployment_id}")
            
            # Pre-deployment checks
            self._pre_deployment_checks(deployment_info)
            
            # Create backup if enabled
            if self.config['backup']['before_deploy']:
                self._create_deployment_backup(deployment_info)
            
            # Execute deployment strategy
            if self.config['strategy'] == 'blue_green':
                self._blue_green_deployment(deployment_info)
            elif self.config['strategy'] == 'rolling':
                self._rolling_deployment(deployment_info)
            elif self.config['strategy'] == 'canary':
                self._canary_deployment(deployment_info)
            
            # Post-deployment verification
            self._post_deployment_verification(deployment_info)
            
            deployment_info['status'] = 'completed'
            deployment_info['end_time'] = now_datetime()
            
            print(f"Deployment completed successfully: {deployment_id}")
            
            # Send notification
            self._send_deployment_notification(deployment_info, success=True)
            
            return deployment_info
            
        except Exception as e:
            deployment_info['status'] = 'failed'
            deployment_info['error'] = str(e)
            deployment_info['end_time'] = now_datetime()
            
            print(f"Deployment failed: {str(e)}")
            
            # Automatic rollback if enabled
            if self.config['rollback']['automatic'] and deployment_info.get('rollback_available'):
                print("Initiating automatic rollback...")
                self._rollback_deployment(deployment_info)
            
            # Send failure notification
            self._send_deployment_notification(deployment_info, success=False)
            
            raise
    
    def _pre_deployment_checks(self, deployment_info):
        """Perform pre-deployment checks"""
        
        print("Performing pre-deployment checks...")
        
        checks = [
            self._check_disk_space,
            self._check_database_connection,
            self._check_dependencies,
            self._check_permissions,
            self._validate_configuration
        ]
        
        for check in checks:
            result = check()
            deployment_info['steps'].append({
                'step': f"pre_check_{check.__name__}",
                'status': 'passed' if result['success'] else 'failed',
                'message': result['message'],
                'timestamp': now_datetime()
            })
            
            if not result['success']:
                raise Exception(f"Pre-deployment check failed: {result['message']}")
        
        print("Pre-deployment checks completed")
    
    def _check_disk_space(self):
        """Check available disk space"""
        
        disk_usage = shutil.disk_usage(self.bench_path)
        free_space_gb = disk_usage.free / (1024**3)
        
        if free_space_gb < 5:  # Require at least 5GB free space
            return {
                'success': False,
                'message': f'Insufficient disk space: {free_space_gb:.2f}GB available'
            }
        
        return {
            'success': True,
            'message': f'Disk space OK: {free_space_gb:.2f}GB available'
        }
    
    def _check_database_connection(self):
        """Check database connectivity"""
        
        try:
            import frappe
            frappe.db.commit()
            
            return {
                'success': True,
                'message': 'Database connection OK'
            }
        
        except Exception as e:
            return {
                'success': False,
                'message': f'Database connection failed: {str(e)}'
            }
    
    def _check_dependencies(self):
        """Check deployment dependencies"""
        
        # Check for required tools
        required_tools = ['git', 'bench', 'npm', 'node']
        
        for tool in required_tools:
            try:
                subprocess.run([tool, '--version'], check=True, capture_output=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                return {
                    'success': False,
                    'message': f'Required tool not found: {tool}'
                }
        
        return {
            'success': True,
            'message': 'All dependencies satisfied'
        }
    
    def _check_permissions(self):
        """Check file permissions"""
        
        # Check if we can write to bench directory
        test_file = self.bench_path / '.deployment_test'
        
        try:
            test_file.touch()
            test_file.unlink()
            
            return {
                'success': True,
                'message': 'File permissions OK'
            }
        
        except Exception as e:
            return {
                'success': False,
                'message': f'Permission error: {str(e)}'
            }
    
    def _validate_configuration(self):
        """Validate deployment configuration"""
        
        # Validate essential configuration
        required_settings = ['strategy', 'health_check']
        
        for setting in required_settings:
            if setting not in self.config:
                return {
                    'success': False,
                    'message': f'Missing required configuration: {setting}'
                }
        
        return {
            'success': True,
            'message': 'Configuration validation passed'
        }
    
    def _blue_green_deployment(self, deployment_info):
        """Execute blue-green deployment strategy"""
        
        print("Executing blue-green deployment...")
        
        # Identify current environment (blue)
        current_env = self._get_current_environment()
        new_env = 'green' if current_env == 'blue' else 'blue'
        
        # Setup new environment
        self._setup_environment(new_env, deployment_info)
        
        # Deploy to new environment
        self._deploy_to_environment(new_env, deployment_info)
        
        # Health check on new environment
        if self._health_check_environment(new_env):
            # Switch traffic to new environment
            self._switch_traffic(new_env, deployment_info)
            
            # Keep old environment for rollback
            deployment_info['rollback_environment'] = current_env
            deployment_info['rollback_available'] = True
            
            print(f"Traffic switched to {new_env} environment")
        else:
            raise Exception(f"Health check failed for {new_env} environment")
    
    def _rolling_deployment(self, deployment_info):
        """Execute rolling deployment strategy"""
        
        print("Executing rolling deployment...")
        
        # Get list of application servers
        servers = self._get_application_servers()
        
        # Deploy to servers one by one
        for i, server in enumerate(servers):
            print(f"Deploying to server {i+1}/{len(servers)}: {server}")
            
            # Remove server from load balancer
            self._remove_from_load_balancer(server)
            
            # Deploy to server
            self._deploy_to_server(server, deployment_info)
            
            # Health check
            if self._health_check_server(server):
                # Add server back to load balancer
                self._add_to_load_balancer(server)
                print(f"Server {server} deployed and healthy")
            else:
                # Rollback this server
                self._rollback_server(server)
                raise Exception(f"Health check failed for server {server}")
    
    def _canary_deployment(self, deployment_info):
        """Execute canary deployment strategy"""
        
        print("Executing canary deployment...")
        
        # Start with small percentage of traffic
        canary_percentage = 10
        
        while canary_percentage <= 50:
            print(f"Deploying canary with {canary_percentage}% traffic")
            
            # Deploy canary
            self._deploy_canary(canary_percentage, deployment_info)
            
            # Monitor for specified duration
            time.sleep(300)  # 5 minutes
            
            # Check metrics
            if self._check_canary_metrics():
                print(f"Canary deployment successful at {canary_percentage}%")
                canary_percentage += 10
            else:
                raise Exception("Canary deployment metrics check failed")
        
        # Full deployment
        self._promote_canary_to_production(deployment_info)
    
    def _setup_environment(self, env_name, deployment_info):
        """Setup new deployment environment"""
        
        print(f"Setting up {env_name} environment...")
        
        env_path = self.bench_path / f"{env_name}_env"
        
        if env_path.exists():
            shutil.rmtree(env_path)
        
        # Clone current environment
        shutil.copytree(self.bench_path, env_path, ignore=shutil.ignore_patterns('sites/*/backups'))
        
        # Update configuration for new environment
        self._update_environment_config(env_path, env_name)
        
        deployment_info['steps'].append({
            'step': f'setup_{env_name}_environment',
            'status': 'completed',
            'message': f'{env_name.capitalize()} environment setup completed',
            'timestamp': now_datetime()
        })
    
    def _deploy_to_environment(self, env_name, deployment_info):
        """Deploy application to specific environment"""
        
        print(f"Deploying to {env_name} environment...")
        
        env_path = self.bench_path / f"{env_name}_env"
        
        # Update apps
        subprocess.run(['bench', 'update'], cwd=env_path, check=True)
        
        # Run migrations
        subprocess.run(['bench', '--site', 'all', 'migrate'], cwd=env_path, check=True)
        
        # Build assets
        subprocess.run(['bench', 'build'], cwd=env_path, check=True)
        
        deployment_info['steps'].append({
            'step': f'deploy_to_{env_name}',
            'status': 'completed',
            'message': f'Deployment to {env_name} completed',
            'timestamp': now_datetime()
        })
    
    def _health_check_environment(self, env_name):
        """Perform health check on environment"""
        
        if not self.config['health_check']['enabled']:
            return True
        
        print(f"Performing health check on {env_name} environment...")
        
        # Switch to environment temporarily for health check
        original_env = os.environ.get('FRAPPE_ENV')
        os.environ['FRAPPE_ENV'] = env_name
        
        try:
            # Perform health check
            health_result = self._perform_health_check()
            
            return health_result['success']
        
        finally:
            # Restore original environment
            if original_env:
                os.environ['FRAPPE_ENV'] = original_env
            elif 'FRAPPE_ENV' in os.environ:
                del os.environ['FRAPPE_ENV']
    
    def _perform_health_check(self):
        """Perform application health check"""
        
        try:
            import requests
            
            endpoint = f"http://localhost:8000{self.config['health_check']['endpoint']}"
            timeout = self.config['health_check']['timeout']
            
            response = requests.get(endpoint, timeout=timeout)
            
            if response.status_code == 200:
                return {'success': True, 'message': 'Health check passed'}
            else:
                return {'success': False, 'message': f'Health check failed: HTTP {response.status_code}'}
        
        except Exception as e:
            return {'success': False, 'message': f'Health check error: {str(e)}'}
    
    def _switch_traffic(self, target_env, deployment_info):
        """Switch traffic to target environment"""
        
        print(f"Switching traffic to {target_env} environment...")
        
        # Update load balancer configuration
        self._update_load_balancer_config(target_env)
        
        # Reload Nginx
        subprocess.run(['systemctl', 'reload', 'nginx'], check=True)
        
        deployment_info['steps'].append({
            'step': 'switch_traffic',
            'status': 'completed',
            'message': f'Traffic switched to {target_env}',
            'timestamp': now_datetime()
        })
    
    def _rollback_deployment(self, deployment_info):
        """Rollback failed deployment"""
        
        print("Initiating deployment rollback...")
        
        if not deployment_info.get('rollback_available'):
            print("Rollback not available")
            return
        
        rollback_env = deployment_info.get('rollback_environment')
        
        if rollback_env:
            # Switch traffic back to previous environment
            self._switch_traffic(rollback_env, deployment_info)
            
            print(f"Rollback completed: traffic switched to {rollback_env}")
        else:
            print("Rollback environment not specified")
    
    def _post_deployment_verification(self, deployment_info):
        """Perform post-deployment verification"""
        
        print("Performing post-deployment verification...")
        
        # Final health check
        health_result = self._perform_health_check()
        
        if not health_result['success']:
            raise Exception("Post-deployment health check failed")
        
        # Verify application functionality
        self._verify_application_functionality(deployment_info)
        
        deployment_info['steps'].append({
            'step': 'post_deployment_verification',
            'status': 'completed',
            'message': 'Post-deployment verification passed',
            'timestamp': now_datetime()
        })
    
    def _verify_application_functionality(self, deployment_info):
        """Verify core application functionality"""
        
        # Test critical application features
        critical_tests = [
            self._test_user_login,
            self._test_database_operations,
            self._test_api_endpoints
        ]
        
        for test in critical_tests:
            result = test()
            
            if not result['success']:
                raise Exception(f"Application functionality test failed: {result['message']}")
    
    def _test_user_login(self):
        """Test user login functionality"""
        
        try:
            import frappe
            
            # Test login with admin user
            frappe.local.login_manager.login('Administrator', 'admin')
            
            return {
                'success': True,
                'message': 'User login test passed'
            }
        
        except Exception as e:
            return {
                'success': False,
                'message': f'User login test failed: {str(e)}'
            }
    
    def _test_database_operations(self):
        """Test database operations"""
        
        try:
            import frappe
            
            # Test database read operation
            frappe.db.count('User')
            
            return {
                'success': True,
                'message': 'Database operations test passed'
            }
        
        except Exception as e:
            return {
                'success': False,
                'message': f'Database operations test failed: {str(e)}'
            }
    
    def _test_api_endpoints(self):
        """Test API endpoints"""
        
        try:
            import requests
            
            # Test API endpoint
            response = requests.get('http://localhost:8000/api/version', timeout=10)
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'message': 'API endpoints test passed'
                }
            else:
                return {
                    'success': False,
                    'message': f'API test failed: HTTP {response.status_code}'
                }
        
        except Exception as e:
            return {
                'success': False,
                'message': f'API test error: {str(e)}'
            }
    
    def _send_deployment_notification(self, deployment_info, success=True):
        """Send deployment notification"""
        
        # Implementation for sending notifications
        pass

# Deployment commands
def deploy_application(bench_path, strategy='blue_green', version=None):
    """Deploy application with zero downtime"""
    
    config = {'strategy': strategy}
    deployer = ZeroDowntimeDeployer(bench_path, config)
    return deployer.deploy(version)

def rollback_deployment(bench_path, deployment_id):
    """Rollback deployment"""
    
    # Implementation for rollback
    pass
```

## 🛠️ Practical Exercises

### Exercise 17.1: Production Environment Setup

1. Set up production Bench with all required components
2. Configure Nginx with SSL and security headers
3. Implement proper monitoring and logging
4. Validate production setup

### Exercise 17.2: Security Hardening

1. Implement comprehensive security hardening
2. Configure firewall and intrusion detection
3. Setup automated security updates
4. Generate security assessment report

### Exercise 17.3: Backup and Recovery

1. Implement automated backup strategy
2. Setup cloud backup storage
3. Test backup restoration process
4. Create disaster recovery plan

## 🤔 Thought Questions

1. How do you balance security with usability in production?
2. What are the trade-offs between different deployment strategies?
3. How do you ensure data consistency during zero-downtime deployments?
4. What monitoring metrics are most critical for production systems?

## 📖 Further Reading

- [Frappe Production Deployment Guide](https://frappeframework.com/docs/user/en/production-deployment)
- [Nginx Security Best Practices](https://www.nginx.com/blog/nginx-security-best-practices/)
- [Zero Downtime Deployment Patterns](https://martinfowler.com/articles/zero-downtime-deployments.html)

## 🎯 Chapter Summary

Production deployment requires comprehensive planning:

- **Architecture Design** ensures scalable and maintainable production setup
- **Security Hardening** protects against common threats and vulnerabilities
- **Backup Strategy** ensures data safety and disaster recovery capability
- **Zero-Downtime Deployment** maintains service availability during updates
- **Monitoring and Alerting** provides visibility into system health and performance
- **Automation** reduces human error and ensures consistent deployments

---

**Book Complete! 🎉**

You now have a comprehensive guide to mastering ERPNext development, from understanding the Frappe mindset to deploying production applications with enterprise-grade security and reliability.


---

## Addendum: Source Article Insights

### Production Server Setup

Production mode configures Frappe with Nginx (reverse proxy), Supervisor (process management), and Redis (caching/queuing). **Never run production setup on a local dev machine.**

```bash
# 1. Enable production mode (run as the frappe system user, not root)
sudo bench setup production [frappe-user]

# 2. Generate Nginx config
bench setup nginx
# If prompted to overwrite, type Yes

# 3. Configure Supervisor and services
bench setup supervisor
bench setup socketio
bench setup redis

# 4. Apply Supervisor changes
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl restart all

# 5. Fix file permissions for web server
sudo usermod -aG [frappe-user] www-data
sudo systemctl restart nginx
```

After this, your site is accessible at `http://[server-ip]`.

---

### SSL and Domain Setup

```bash
# 1. Associate domain with your site
bench setup add-domain --site [site-name] [your-domain.com]

# 2. Install Certbot (Let's Encrypt)
sudo apt update && sudo apt install -y snapd
sudo snap install core && sudo snap refresh core
sudo apt remove -y certbot
sudo snap install --classic certbot
sudo ln -sf /snap/bin/certbot /usr/bin/certbot

# 3. Enable DNS-based multitenancy (required for custom domains)
bench config dns_multitenant on

# 4. Regenerate Nginx config
bench setup nginx
sudo service nginx restart

# 5. Get SSL certificate
sudo certbot --nginx
# Enter domain and email when prompted

# 6. Test auto-renewal
sudo certbot renew --dry-run
```

**Optional: Specify SSL paths in site_config.json:**

```json
{
  "domains": [
    {
      "domain": "your-domain.com",
      "ssl_certificate": "/etc/letsencrypt/live/your-domain.com/fullchain.pem",
      "ssl_certificate_key": "/etc/letsencrypt/live/your-domain.com/privkey.pem"
    }
  ]
}
```

```bash
# Regenerate and reload after editing site_config.json
bench setup nginx
sudo service nginx restart
```

---

### Exposing Local Frappe with ngrok

ngrok creates a secure tunnel from a public URL to your local Frappe instance. Useful for testing webhooks, demos, and third-party integrations.

```bash
# 1. Navigate to bench directory
cd frappe-bench/

# 2. Install pyngrok in bench environment
bench pip install pyngrok

# 3. Get your authtoken from https://dashboard.ngrok.com/authtokens

# 4. Store authtoken in site config
bench --site [site-name] set-config ngrok_authtoken YOUR_TOKEN_HERE

# 5. Set the HTTP port
bench --site [site-name] set-config http_port 8000

# 6. Start bench (in one terminal)
bench start

# 7. Start ngrok tunnel (in another terminal)
bench --site [site-name] ngrok --bind-tls
# Output: Public URL: https://abc123.ngrok.io
```

**Manual ngrok (if bench command fails):**

```bash
# Authenticate once
ngrok authtoken YOUR_TOKEN_HERE

# Start tunnel manually
ngrok http 8000
```

**Alternatives to ngrok:** localtunnel, pagekite, Cloudflare Tunnel (free, no bandwidth limits).

---

### Dockerizing Frappe: Dockerfile Concepts

Docker packages your app and all dependencies into a portable container. Key concepts:

**Image vs Container:**
- Image = read-only blueprint (layers stacked on top of each other)
- Container = running instance of an image (adds a writable layer on top)

**Multi-stage Dockerfile for Frappe:**

```dockerfile
# Stage 1: Build stage
ARG PYTHON_VERSION=3.11.6
ARG DEBIAN_BASE=bookworm
FROM python:${PYTHON_VERSION}-slim-${DEBIAN_BASE} AS base

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        git curl wget \
        libmysqlclient-dev \
        wkhtmltopdf \
    && rm -rf /var/lib/apt/lists/*

# Create frappe user
RUN useradd -ms /bin/bash frappe
USER frappe
WORKDIR /home/frappe

# Install Node.js via nvm
ARG NODE_VERSION=18.18.2
ENV NVM_DIR=/home/frappe/.nvm
RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash \
    && . $NVM_DIR/nvm.sh \
    && nvm install ${NODE_VERSION} \
    && nvm use ${NODE_VERSION}

ENV PATH=${NVM_DIR}/versions/node/v${NODE_VERSION}/bin/:${PATH}

# Install bench
RUN pip install --user frappe-bench

ENV PATH=/home/frappe/.local/bin:$PATH

# Stage 2: App stage
FROM base AS app

ARG FRAPPE_BRANCH=version-15
ARG APPS_JSON_BASE64

# Initialize bench
RUN bench init --frappe-branch=${FRAPPE_BRANCH} --skip-redis-config-generation frappe-bench

WORKDIR /home/frappe/frappe-bench

# Install custom apps from apps.json
RUN if [ -n "${APPS_JSON_BASE64}" ]; then \
        echo "${APPS_JSON_BASE64}" | base64 -d > /tmp/apps.json; \
        bench get-app --resolve-deps /tmp/apps.json; \
    fi

EXPOSE 8000 9000

CMD ["bench", "start"]
```

**Build the image:**

```bash
# Encode apps.json
export APPS_JSON_BASE64=$(base64 -w 0 apps.json)

# Build
docker build \
  --build-arg FRAPPE_BRANCH=version-15 \
  --build-arg APPS_JSON_BASE64=$APPS_JSON_BASE64 \
  --tag mycompany/frappe-app:latest \
  .
```

**Layer caching best practice:** Put rarely-changing instructions first (system deps, Python packages), frequently-changing instructions last (app code). This way, editing your app code doesn't invalidate the expensive dependency layers.

---

### Docker Compose for Frappe

Frappe requires multiple services: backend (Gunicorn), frontend (Nginx), websocket (Socket.IO), workers, scheduler, MariaDB, and Redis.

```yaml
# compose.yaml
x-customizable-image: &customizable_image
  image: ${CUSTOM_IMAGE:-frappe/erpnext}:${CUSTOM_TAG:-version-15}
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
      bench set-config -g db_port $DB_PORT;
      bench set-config -g redis_cache "redis://$REDIS_CACHE";
      bench set-config -g redis_queue "redis://$REDIS_QUEUE";
      bench set-config -g redis_socketio "redis://$REDIS_QUEUE";
    depends_on:
      db:
        condition: service_healthy
      redis-cache:
        condition: service_started

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
      FRAPPE_SITE_NAME_HEADER: ${FRAPPE_SITE_NAME_HEADER:-$host}
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
      test: mysqladmin ping -h localhost --password=${DB_PASSWORD}
      interval: 1s
      retries: 20
    environment:
      MYSQL_ROOT_PASSWORD: ${DB_PASSWORD}
      MYSQL_DATABASE: ${DB_NAME:-frappe}
    volumes:
      - db-data:/var/lib/mysql

  redis-cache:
    image: redis:6.2-alpine

  redis-queue:
    image: redis:6.2-alpine

volumes:
  sites:
  logs:
  db-data:
```

**Startup order matters:** `db` → `redis` → `configurator` (runs once, sets up config) → `backend`/`websocket` → `frontend` → `workers`/`scheduler`.

**Key patterns:**
- `depends_on` with `condition: service_completed_successfully` ensures configurator finishes before backend starts
- `depends_on` with `condition: service_healthy` waits for MariaDB to be ready
- YAML anchors (`&backend_defaults`, `<<: *backend_defaults`) reduce repetition

---

### Dev Containers for Frappe Development

Dev Containers let you develop inside a Docker container using VS Code. Everyone on the team gets an identical environment.

**Setup:**

```bash
git clone https://github.com/frappe/frappe_docker.git
cd frappe_docker
cp -R devcontainer-example .devcontainer
cp -R development/vscode-example development/.vscode
code .
# Press Ctrl+Shift+P → "Dev Containers: Reopen in Container"
```

**Inside the container, initialize bench:**

```bash
bench init --skip-redis-config-generation frappe-bench
cd frappe-bench

# Point to Docker services (not localhost)
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

bench start
```

**`.devcontainer/devcontainer.json`:**

```json
{
  "name": "Frappe Bench",
  "dockerComposeFile": "./docker-compose.yml",
  "service": "frappe",
  "workspaceFolder": "/workspace/development",
  "remoteUser": "frappe",
  "forwardPorts": [8000, 9000, 6787],
  "shutdownAction": "stopCompose",
  "mounts": [
    "source=${localEnv:HOME}${localEnv:USERPROFILE}/.ssh,target=/home/frappe/.ssh,type=bind,consistency=cached"
  ],
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.python",
        "ms-vscode.live-server",
        "mtxr.sqltools"
      ],
      "settings": {
        "terminal.integrated.defaultProfile.linux": "bash",
        "debug.node.autoAttach": "disabled"
      }
    }
  }
}
```

**Building a custom Docker image with your app:**

```bash
# 1. Create apps.json
cat > apps.json << 'EOF'
[
  {"url": "https://github.com/frappe/erpnext", "branch": "version-15"},
  {"url": "https://github.com/myorg/my-app", "branch": "main"}
]
EOF

# 2. Encode it
export APPS_JSON_BASE64=$(base64 -w 0 apps.json)

# 3. Clone frappe_docker and build
git clone https://github.com/frappe/frappe_docker
cd frappe_docker
docker build \
  --build-arg FRAPPE_BRANCH=version-15 \
  --build-arg APPS_JSON_BASE64=$APPS_JSON_BASE64 \
  --file images/layered/Containerfile \
  --tag myorg/my-frappe-app:latest \
  .

# 4. Push to Docker Hub
docker push myorg/my-frappe-app:latest
```


---

## 📌 Addendum: App Release Process

### Branch Strategy

A typical Frappe app uses three long-lived branches:

```
dev  ←  staging  ←  release
```

- `dev` — active development, may be unstable
- `staging` — tested, pre-production code
- `release` — production-ready, tagged versions

### Step-by-Step Release Workflow

**Step 1: Merge staging → release (after QA + client approval)**

Create a PR from `staging` into `release` and merge it.

**Step 2: Update version and changelog**

```bash
git pull
git checkout release

# Edit CHANGELOG.md
```

```markdown
## [0.4.0] - 2025-09-06
- Added user login feature
- Fixed dashboard bug
```

**Step 3: Commit with a bump message**

```bash
git add CHANGELOG.md
git commit -m "chore(release): bump version to 0.4.0"
git push upstream release
```

The `chore(release): bump version` format follows [Conventional Commits](https://www.conventionalcommits.org/). Common prefixes: `feat`, `fix`, `chore`, `docs`, `refactor`.

**Step 4: Sync staging with release (rebase)**

```bash
git checkout staging
git rebase release
git push upstream staging
```

Rebase keeps history linear — no merge commits. Staging becomes an exact copy of release.

**Step 5: Sync dev with staging (not release)**

```bash
git checkout dev
git rebase staging
git push upstream dev
```

Dev rebases from staging (not release directly) because dev may have ongoing work not yet in release.

**Step 6: Create a GitHub Release**

1. Go to **GitHub → Releases → Draft a new release**
2. Create a tag matching the version (e.g., `v0.4.0`)
3. Paste the changelog content as the release description
4. Publish

### Building and Pushing Docker Images

After tagging a release, build a Docker image with the new version:

**Create `apps.json`:**

```json
[
  { "url": "https://github.com/frappe/erpnext", "branch": "version-15" },
  { "url": "https://YOUR_PAT@github.com/your-org/your-app.git", "branch": "release" }
]
```

**Build:**

```bash
export APPS_JSON_BASE64=$(base64 -w 0 apps.json)

git clone https://github.com/frappe/frappe_docker
cd frappe_docker

docker build \
  --no-cache \
  --build-arg FRAPPE_BRANCH=version-15 \
  --build-arg APPS_JSON_BASE64=$APPS_JSON_BASE64 \
  --file images/layered/Containerfile \
  --tag your-dockerhub-username/your-app:0.4.0 \
  --tag your-dockerhub-username/your-app:latest \
  .
```

**Push to Docker Hub:**

```bash
docker login -u your-dockerhub-username
docker push your-dockerhub-username/your-app:0.4.0
docker push your-dockerhub-username/your-app:latest
```

**Verify:**

```bash
docker images
# Visit: https://hub.docker.com/r/your-dockerhub-username/your-app
```

### Final State After Release

- `release`, `staging`, and `dev` share aligned history
- GitHub release is published and tagged
- Docker image is built and pushed to registry
- Production deployment can pull the new image
