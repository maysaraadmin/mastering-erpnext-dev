# Chapter 37: Production vs Development Mode

## 🎯 Learning Objectives

By the end of this chapter, you will master:
- **Understanding the differences** between production and development modes
- **When to use each mode** for optimal development workflow
- **Security implications** of different modes
- **Performance characteristics** and optimizations
- **Configuration management** for different environments
- **Debugging capabilities** in each mode
- **Best practices** for mode transitions and deployment
- **Monitoring and logging** strategies for production

## 📚 Chapter Topics

### 37.1 Understanding Development vs Production Modes

**Core Concept**

Frappe applications can run in two primary modes: **Development Mode** and **Production Mode**. Each mode serves different purposes and has distinct characteristics that affect security, performance, and user experience.

#### Development Mode

**Purpose:** Designed for development, testing, and debugging
**Characteristics:**
- **Verbose error messages** with full stack traces
- **Asset bundling disabled** for faster development
- **Database queries logged** for debugging
- **Hot reloading** enabled for rapid development
- **Developer tools** and debugging interfaces accessible
- **Relaxed security** settings for easier testing

**When to Use:**
- Active development and feature creation
- Debugging and troubleshooting
- Testing new functionality
- Development environments and staging
- Learning and experimentation

#### Production Mode

**Purpose:** Optimized for live production deployment
**Characteristics:**
- **Minimal error messages** for security
- **Asset bundling enabled** for performance
- **Database query logging disabled**
- **Caching enabled** for speed
- **Security hardening** applied
- **Performance optimizations** active

**When to Use:**
- Live production environments
- Customer-facing applications
- Performance-critical deployments
- Security-sensitive environments
- Production staging environments

---

### 37.2 Mode Configuration and Setup

#### Configuration Files

**site_config.json**
```json
{
    "developer_mode": 1,
    "maintenance_mode": 0,
    "serve": true,
    "db_name": "your_database",
    "db_password": "your_password",
    "redis_cache": "redis://localhost:13000",
    "redis_queue": "redis://localhost:13001",
    "redis_socketio": "redis://localhost:13002",
    "socketio_port": 9000,
    "file_watcher_port": 6787,
    "scheduler_enabled": true,
    "background_workers": 1,
    "gunicorn_workers": 4,
    "max_request_size": 10485760,
    "rate_limit": {
        "method": {
            "login": {
                "limit": 5,
                "reset": "hour"
            }
        }
    }
}
```

**Development Mode Configuration**
```json
{
    "developer_mode": 1,
    "serve": true,
    "file_watcher_port": 6787,
    "live_reload": true,
    "frappe_user": "Administrator",
    "allow_cors": "*",
    "debug": true,
    "logging": {
        "level": "DEBUG",
        "console": true,
        "file": true
    }
}
```

**Production Mode Configuration**
```json
{
    "developer_mode": 0,
    "serve": false,
    "maintenance_mode": 0,
    "gunicorn_workers": 4,
    "background_workers": 2,
    "scheduler_enabled": true,
    "redis_cache": "redis://localhost:13000",
    "redis_queue": "redis://localhost:13001",
    "redis_socketio": "redis://localhost:13002",
    "allow_cors": ["https://yourdomain.com"],
    "max_request_size": 10485760,
    "logging": {
        "level": "INFO",
        "console": false,
        "file": true
    }
}
```

#### Environment Variables

**Development Environment**
```bash
# .env.development
FRAPPE_ENV=development
DEVELOPER_MODE=1
DEBUG=1
REDIS_CACHE=redis://localhost:13000
REDIS_QUEUE=redis://localhost:13001
REDIS_SOCKETIO=redis://localhost:13002
DB_HOST=localhost
DB_PORT=3306
DB_NAME=your_dev_db
```

**Production Environment**
```bash
# .env.production
FRAPPE_ENV=production
DEVELOPER_MODE=0
DEBUG=0
REDIS_CACHE=redis://prod-cache:13000
REDIS_QUEUE=redis://prod-queue:13001
REDIS_SOCKETIO=redis://prod-socketio:13002
DB_HOST=prod-db
DB_PORT=3306
DB_NAME=your_prod_db
```

---

### 37.3 Security Differences

#### Development Mode Security

**Relaxed Security Settings:**
- **SQL queries visible** in error messages
- **Full stack traces** exposed
- **Debug information** accessible
- **File uploads** less restricted
- **API endpoints** more permissive
- **Cross-origin requests** broadly allowed

**Security Implications:**
```python
# Development mode - SQL queries visible
frappe.db.sql("SELECT * FROM `tabCustomer` WHERE name = %s", ("CUST-001",))
# If error occurs, full SQL query shown in response

# Error response in development mode
{
    "exc_type": "ProgrammingError",
    "exception": "SELECT * FROM `tabCustomer` WHERE name = 'CUST-001'",
    "message": "Table 'your_db.tabCustomer' doesn't exist",
    "traceback": "Full stack trace visible..."
}
```

#### Production Mode Security

**Enhanced Security Settings:**
- **SQL queries hidden** from error messages
- **Generic error messages** only
- **Debug interfaces** disabled
- **File upload restrictions** enforced
- **API rate limiting** active
- **CORS restrictions** enforced

**Security Implementation:**
```python
# Production mode - SQL queries hidden
frappe.db.sql("SELECT * FROM `tabCustomer` WHERE name = %s", ("CUST-001",))
# If error occurs, generic message only

# Error response in production mode
{
    "exc_type": "InternalServerError",
    "message": "An error occurred while processing your request",
    "indicator": "red"
}
```

#### Security Configuration

**Security Headers in Production**
```python
# hooks.py - Add security headers
app_include_js = "/assets/your_app/js/security.js"

# Security middleware
def add_security_headers(response):
    if not frappe.conf.developer_mode:
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000'
        response.headers['Content-Security-Policy'] = "default-src 'self'"
    return response
```

**File Upload Security**
```python
# Enhanced file validation in production
def validate_file_upload(file_doc):
    if not frappe.conf.developer_mode:
        # Strict file type validation
        allowed_types = ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'jpg', 'png']
        file_extension = file_doc.file_name.split('.')[-1].lower()
        
        if file_extension not in allowed_types:
            frappe.throw(f"File type .{file_extension} is not allowed")
        
        # File size validation
        max_size = 5 * 1024 * 1024  # 5MB
        if file_doc.file_size > max_size:
            frappe.throw("File size exceeds maximum allowed size")
```

---

### 37.4 Performance Characteristics

#### Development Mode Performance

**Performance Characteristics:**
- **No asset bundling** - individual files loaded
- **No caching** - fresh data on every request
- **Debug logging enabled** - additional overhead
- **Hot reloading active** - continuous monitoring
- **Database queries logged** - performance impact
- **No compression** - larger response sizes

**Development Mode Benchmarks:**
```python
# Asset loading in development mode
<script src="/assets/your_app/js/file1.js"></script>
<script src="/assets/your_app/js/file2.js"></script>
<script src="/assets/your_app/js/file3.js"></script>
<!-- 3 separate HTTP requests, no compression -->

# Database query logging
frappe.db.sql("SELECT * FROM `tabCustomer`")  # Logged and displayed
# Query execution time: ~50ms with logging overhead
```

#### Production Mode Performance

**Performance Optimizations:**
- **Asset bundling enabled** - combined and minified files
- **Caching active** - Redis for data and assets
- **Debug logging disabled** - reduced overhead
- **Compression enabled** - gzip responses
- **Database pooling** - optimized connections
- **Background workers** - async processing

**Production Mode Benchmarks:**
```python
# Asset loading in production mode
<script src="/assets/your_app/js/bundle.min.js?v=12345"></script>
<!-- 1 HTTP request, minified and compressed -->

# Database query optimization
frappe.db.sql("SELECT * FROM `tabCustomer`")  # Not logged
# Query execution time: ~20ms without logging overhead
```

#### Performance Monitoring

**Development Mode Monitoring**
```python
# Development performance monitoring
def log_query_performance():
    if frappe.conf.developer_mode:
        queries = frappe.local.db_queries
        for query in queries:
            print(f"Query: {query['query']}")
            print(f"Time: {query['time']}ms")
            print(f"Rows: {query['rows']}")
            print("-" * 50)

# Memory usage monitoring
def monitor_memory_usage():
    if frappe.conf.developer_mode:
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        print(f"Memory Usage: {memory_info.rss / 1024 / 1024:.2f} MB")
```

**Production Mode Monitoring**
```python
# Production performance monitoring
def log_performance_metrics():
    if not frappe.conf.developer_mode:
        # Log to production monitoring system
        metrics = {
            'response_time': frappe.local.response_time,
            'memory_usage': get_memory_usage(),
            'cpu_usage': get_cpu_usage(),
            'active_users': get_active_users_count()
        }
        
        # Send to monitoring service
        send_to_monitoring_service(metrics)

# Database performance monitoring
def monitor_database_performance():
    if not frappe.conf.developer_mode:
        slow_queries = frappe.db.get_slow_queries()
        for query in slow_queries:
            if query['execution_time'] > 1000:  # > 1 second
                log_slow_query(query)
```

---

### 37.5 Asset Management and Optimization

#### Development Mode Assets

**Asset Characteristics:**
- **Individual files** served separately
- **No minification** or compression
- **Source maps** included for debugging
- **Hot reloading** enabled
- **Cache busting** disabled

**Asset Pipeline in Development:**
```python
# Development asset pipeline
class DevelopmentAssetPipeline:
    def __init__(self):
        self.watcher = FileWatcher()
        self.compiler = AssetCompiler()
        
    def watch_assets(self):
        """Watch for file changes and recompile"""
        self.watcher.watch([
            "assets/js/**/*.js",
            "assets/css/**/*.css",
            "assets/scss/**/*.scss"
        ], self.on_file_change)
    
    def on_file_change(self, file_path):
        """Handle file changes"""
        if file_path.endswith('.scss'):
            self.compiler.compile_scss(file_path)
        elif file_path.endswith('.js'):
            self.compiler.compile_js(file_path)
        
        # Trigger hot reload
        self.trigger_reload()
    
    def get_asset_url(self, asset_path):
        """Get development asset URL"""
        return f"/assets/{asset_path}?v={int(time.time())}"
```

#### Production Mode Assets

**Asset Characteristics:**
- **Bundled files** combined and minified
- **Compression enabled** (gzip)
- **Source maps** excluded
- **Versioned URLs** for cache busting
- **CDN integration** possible

**Asset Pipeline in Production:**
```python
# Production asset pipeline
class ProductionAssetPipeline:
    def __init__(self):
        self.bundler = AssetBundler()
        self.minifier = AssetMinifier()
        self.compressor = AssetCompressor()
        
    def build_assets(self):
        """Build production assets"""
        # Bundle JavaScript files
        js_bundles = self.bundler.bundle_js([
            "assets/js/app.js",
            "assets/js/components.js",
            "assets/js/utils.js"
        ])
        
        # Bundle CSS files
        css_bundles = self.bundler.bundle_css([
            "assets/css/app.css",
            "assets/css/components.css"
        ])
        
        # Minify bundles
        for bundle in js_bundles + css_bundles:
            self.minifier.minify(bundle)
        
        # Compress for serving
        for bundle in js_bundles + css_bundles:
            self.compressor.compress(bundle)
    
    def get_asset_url(self, asset_path):
        """Get production asset URL with version"""
        version = self.get_asset_version(asset_path)
        return f"/assets/{asset_path}?v={version}"
```

---

### 37.6 Database Configuration

#### Development Database

**Database Settings:**
- **Query logging enabled**
- **No connection pooling**
- **Slow query monitoring**
- **Development database** separate from production
- **Frequent migrations** during development

**Development Database Configuration:**
```python
# Development database configuration
development_db_config = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '',
    'database': 'your_dev_db',
    'charset': 'utf8mb4',
    'log_queries': True,
    'slow_query_log': True,
    'long_query_time': 1.0,  # Log queries > 1 second
    'max_connections': 100,
    'innodb_buffer_pool_size': '256M'
}
```

#### Production Database

**Database Settings:**
- **Query logging disabled** for performance
- **Connection pooling** enabled
- **Optimized configuration**
- **Production database** with backups
- **Stable migrations** only

**Production Database Configuration:**
```python
# Production database configuration
production_db_config = {
    'host': 'prod-db-host',
    'port': 3306,
    'user': 'prod_user',
    'password': 'secure_password',
    'database': 'your_prod_db',
    'charset': 'utf8mb4',
    'log_queries': False,
    'slow_query_log': False,
    'max_connections': 500,
    'innodb_buffer_pool_size': '2G',
    'innodb_log_file_size': '256M',
    'query_cache_size': '64M'
}
```

#### Database Migration Strategy

**Development Migrations:**
```python
# Development migration strategy
class DevelopmentMigrationManager:
    def run_migrations(self):
        """Run all pending migrations"""
        migrations = self.get_pending_migrations()
        
        for migration in migrations:
            try:
                self.run_migration(migration)
                self.mark_migration_complete(migration)
                print(f"Migration {migration} completed successfully")
            except Exception as e:
                print(f"Migration {migration} failed: {e}")
                # In development, continue with other migrations
                continue
    
    def rollback_migration(self, migration_name):
        """Rollback a specific migration"""
        migration = self.get_migration(migration_name)
        migration.rollback()
        self.mark_migration_rolled_back(migration_name)
```

**Production Migrations:**
```python
# Production migration strategy
class ProductionMigrationManager:
    def run_migrations(self):
        """Run migrations with safety checks"""
        # Create backup before migrations
        self.create_database_backup()
        
        migrations = self.get_pending_migrations()
        
        for migration in migrations:
            try:
                # Test migration on staging first
                self.test_migration_on_staging(migration)
                
                # Run migration with monitoring
                self.run_migration_with_monitoring(migration)
                self.mark_migration_complete(migration)
                
                # Verify migration success
                self.verify_migration_success(migration)
                
            except Exception as e:
                # Rollback on failure
                self.rollback_migration(migration.name)
                self.restore_database_backup()
                raise e
    
    def verify_migration_success(self, migration):
        """Verify migration completed successfully"""
        # Run data integrity checks
        self.run_data_integrity_checks()
        
        # Verify application functionality
        self.run_smoke_tests()
        
        # Check performance impact
        self.check_performance_impact()
```

---

### 37.7 Caching Strategies

#### Development Mode Caching

**Caching Characteristics:**
- **Minimal caching** for development
- **Cache disabled** for most operations
- **Short cache times** for enabled caches
- **Cache debugging** information available

**Development Cache Configuration:**
```python
# Development cache settings
development_cache_config = {
    'redis_cache': {
        'host': 'localhost',
        'port': 13000,
        'db': 0,
        'ttl': 300,  # 5 minutes
        'enabled': True
    },
    'memory_cache': {
        'enabled': True,
        'max_size': 100,  # Small cache for development
        'ttl': 60  # 1 minute
    },
    'query_cache': {
        'enabled': False  # Disabled for debugging
    }
}
```

#### Production Mode Caching

**Caching Characteristics:**
- **Aggressive caching** for performance
- **Multiple cache layers** (Redis, memory, CDN)
- **Long cache times** for static content
- **Cache warming** strategies

**Production Cache Configuration:**
```python
# Production cache settings
production_cache_config = {
    'redis_cache': {
        'host': 'prod-cache-cluster',
        'port': 13000,
        'db': 0,
        'ttl': 3600,  # 1 hour
        'enabled': True,
        'cluster_mode': True
    },
    'memory_cache': {
        'enabled': True,
        'max_size': 10000,  # Large cache for production
        'ttl': 1800  # 30 minutes
    },
    'query_cache': {
        'enabled': True,
        'ttl': 600  # 10 minutes
    },
    'cdn_cache': {
        'enabled': True,
        'ttl': 86400  # 24 hours
    }
}
```

#### Cache Management

**Cache Warming Strategies:**
```python
# Production cache warming
class ProductionCacheWarmer:
    def warm_cache(self):
        """Warm up production cache"""
        # Cache frequently accessed data
        self.cache_master_data()
        self.cache_user_sessions()
        self.cache_frequently_used_queries()
        self.cache_static_assets()
        
    def cache_master_data(self):
        """Cache master data (customers, items, etc.)"""
        master_doctypes = ['Customer', 'Item', 'Supplier', 'Account']
        
        for doctype in master_doctypes:
            data = frappe.db.get_all(doctype, fields=['name', 'modified'])
            cache_key = f"master_data_{doctype}"
            frappe.cache().set_value(cache_key, data, expires_in_sec=3600)
    
    def cache_user_sessions(self):
        """Cache active user sessions"""
        active_users = frappe.db.get_all('User', 
            filters={'enabled': 1, 'last_login': ['>', frappe.utils.add_days(frappe.utils.nowdate(), -7)]},
            fields=['name', 'user_image', 'user_type']
        )
        
        cache_key = "active_users"
        frappe.cache().set_value(cache_key, active_users, expires_in_sec=1800)
```

---

### 37.8 Error Handling and Logging

#### Development Mode Error Handling

**Error Characteristics:**
- **Detailed error messages** with full context
- **Stack traces** visible to developers
- **SQL queries** shown in errors
- **Debug information** included
- **Error logging** to console and file

**Development Error Handler:**
```python
# Development error handler
class DevelopmentErrorHandler:
    def handle_exception(self, exc_type, exc_value, traceback):
        """Handle exceptions in development mode"""
        error_info = {
            'exc_type': str(exc_type.__name__),
            'exception': str(exc_value),
            'traceback': ''.join(traceback.format_tb(traceback)),
            'user': frappe.session.user,
            'form_dict': frappe.local.form_dict,
            'request_url': frappe.request.url,
            'sql_queries': frappe.local.db_queries
        }
        
        # Log to console
        print(f"ERROR: {error_info}")
        
        # Log to file
        frappe.log_error(error_info, "Development Error")
        
        # Return detailed error response
        frappe.local.response.update({
            'exc_type': error_info['exc_type'],
            'exception': error_info['exception'],
            'traceback': error_info['traceback'],
            'sql_queries': error_info['sql_queries']
        })
```

#### Production Mode Error Handling

**Error Characteristics:**
- **Generic error messages** for security
- **No stack traces** exposed
- **SQL queries** hidden
- **Minimal debug information**
- **Structured logging** to monitoring systems

**Production Error Handler:**
```python
# Production error handler
class ProductionErrorHandler:
    def handle_exception(self, exc_type, exc_value, traceback):
        """Handle exceptions in production mode"""
        error_info = {
            'exc_type': str(exc_type.__name__),
            'exception': str(exc_value),
            'user': frappe.session.user,
            'request_url': frappe.request.url,
            'timestamp': frappe.utils.now(),
            'severity': self.get_error_severity(exc_type, exc_value)
        }
        
        # Log to monitoring system
        self.log_to_monitoring_system(error_info)
        
        # Log to file (without sensitive info)
        safe_error_info = self.sanitize_error_info(error_info)
        frappe.log_error(safe_error_info, "Production Error")
        
        # Return generic error response
        frappe.local.response.update({
            'exc_type': 'InternalServerError',
            'exception': 'An error occurred while processing your request',
            'indicator': 'red'
        })
    
    def sanitize_error_info(self, error_info):
        """Remove sensitive information from error logs"""
        sanitized = error_info.copy()
        sanitized.pop('form_dict', None)  # Remove form data
        sanitized.pop('traceback', None)  # Remove stack trace
        return sanitized
    
    def get_error_severity(self, exc_type, exc_value):
        """Determine error severity for monitoring"""
        if exc_type in [PermissionError, AuthenticationError]:
            return 'warning'
        elif exc_type in [DatabaseError, TimeoutError]:
            return 'critical'
        else:
            return 'error'
```

---

### 37.9 Deployment and Mode Transitions

#### Development to Production Workflow

**Pre-Deployment Checklist:**
```python
# Pre-deployment validation
class PreDeploymentValidator:
    def validate_deployment_readiness(self):
        """Validate system is ready for production deployment"""
        checks = [
            self.check_developer_mode_disabled,
            self.check_security_settings,
            self.check_asset_compilation,
            self.check_database_migrations,
            self.check_cache_configuration,
            self.check_monitoring_setup,
            self.check_backup_system
        ]
        
        results = []
        for check in checks:
            result = check()
            results.append(result)
        
        return all(results), results
    
    def check_developer_mode_disabled(self):
        """Ensure developer mode is disabled"""
        if frappe.conf.developer_mode:
            return False, "Developer mode is still enabled"
        return True, "Developer mode is disabled"
    
    def check_security_settings(self):
        """Validate security settings"""
        checks = [
            self.check_cors_settings,
            self.check_file_upload_restrictions,
            self.check_api_rate_limiting,
            self.check_ssl_configuration
        ]
        
        return all(check[0] for check in checks), "Security settings validated"
    
    def check_asset_compilation(self):
        """Verify assets are compiled for production"""
        # Check if production bundles exist
        required_bundles = [
            'assets/js/bundle.min.js',
            'assets/css/bundle.min.css'
        ]
        
        for bundle in required_bundles:
            if not os.path.exists(bundle):
                return False, f"Missing production bundle: {bundle}"
        
        return True, "Production assets compiled"
```

#### Environment-Specific Configurations

**Configuration Management:**
```python
# Environment configuration manager
class EnvironmentConfigManager:
    def __init__(self, environment='development'):
        self.environment = environment
        self.config = self.load_config()
    
    def load_config(self):
        """Load environment-specific configuration"""
        config_file = f"config/{self.environment}.json"
        
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        # Override with environment variables
        self.apply_env_overrides(config)
        
        return config
    
    def apply_env_overrides(self, config):
        """Apply environment variable overrides"""
        env_mappings = {
            'FRAPPE_DB_HOST': 'db_host',
            'FRAPPE_DB_PORT': 'db_port',
            'FRAPPE_REDIS_CACHE': 'redis_cache'
        }
        
        for env_var, config_key in env_mappings.items():
            if os.environ.get(env_var):
                config[config_key] = os.environ[env_var]
    
    def get_database_config(self):
        """Get database configuration for current environment"""
        return self.config.get('database', {})
    
    def get_cache_config(self):
        """Get cache configuration for current environment"""
        return self.config.get('cache', {})
```

#### Deployment Automation

**Automated Deployment Script:**
```bash
#!/bin/bash
# deploy.sh - Automated deployment script

set -e

ENVIRONMENT=${1:-production}
BACKUP_DIR="/backups/$(date +%Y%m%d_%H%M%S)"

echo "Starting deployment to $ENVIRONMENT environment..."

# Create backup
echo "Creating database backup..."
mkdir -p $BACKUP_DIR
bench --site your_site.db backup --with-files --backup-path $BACKUP_DIR

# Switch to production mode
echo "Switching to production mode..."
bench config set developer_mode 0
bench config set maintenance_mode 1

# Build production assets
echo "Building production assets..."
bench build --production

# Run database migrations
echo "Running database migrations..."
bench --site your_site.db migrate

# Clear cache
echo "Clearing cache..."
bench --site your_site.db clear-cache

# Restart services
echo "Restarting services..."
bench restart

# Disable maintenance mode
echo "Disabling maintenance mode..."
bench config set maintenance_mode 0

# Verify deployment
echo "Verifying deployment..."
bench --site your_site.db doctor

echo "Deployment completed successfully!"
```

---

### 37.10 Monitoring and Maintenance

#### Development Monitoring

**Development Monitoring Tools:**
```python
# Development monitoring tools
class DevelopmentMonitor:
    def monitor_performance(self):
        """Monitor performance in development"""
        metrics = {
            'response_time': self.get_average_response_time(),
            'memory_usage': self.get_memory_usage(),
            'sql_queries': self.get_sql_query_count(),
            'cache_hit_rate': self.get_cache_hit_rate()
        }
        
        print("Development Performance Metrics:")
        for metric, value in metrics.items():
            print(f"  {metric}: {value}")
    
    def monitor_errors(self):
        """Monitor errors in development"""
        recent_errors = frappe.get_all('Error Log',
            filters={'creation': ['>', frappe.utils.add_hours(frappe.utils.now(), -1)]},
            fields=['creation', 'exception', 'method']
        )
        
        if recent_errors:
            print(f"Recent errors ({len(recent_errors)}):")
            for error in recent_errors:
                print(f"  {error.creation}: {error.exception}")
```

#### Production Monitoring

**Production Monitoring Setup:**
```python
# Production monitoring system
class ProductionMonitor:
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager()
        self.health_checker = HealthChecker()
    
    def monitor_system_health(self):
        """Monitor overall system health"""
        health_checks = [
            self.check_database_health,
            self.check_redis_health,
            self.check_disk_space,
            self.check_memory_usage,
            self.check_cpu_usage,
            self.check_response_times
        ]
        
        results = {}
        for check in health_checks:
            try:
                result = check()
                results[check.__name__] = result
            except Exception as e:
                results[check.__name__] = {'status': 'error', 'message': str(e)}
        
        return results
    
    def check_database_health(self):
        """Check database health"""
        try:
            # Test database connection
            frappe.db.sql("SELECT 1")
            
            # Check slow queries
            slow_queries = frappe.db.get_slow_queries(limit=10)
            
            # Check connection pool
            active_connections = frappe.db.get_active_connections()
            
            return {
                'status': 'healthy',
                'slow_queries': len(slow_queries),
                'active_connections': active_connections
            }
        except Exception as e:
            return {'status': 'unhealthy', 'message': str(e)}
    
    def setup_alerts(self):
        """Setup production alerts"""
        alerts = [
            {
                'name': 'High Error Rate',
                'condition': 'error_rate > 0.05',
                'severity': 'critical',
                'action': 'send_notification'
            },
            {
                'name': 'High Response Time',
                'condition': 'avg_response_time > 2000',
                'severity': 'warning',
                'action': 'send_notification'
            },
            {
                'name': 'Low Memory',
                'condition': 'memory_usage > 0.9',
                'severity': 'critical',
                'action': 'restart_services'
            }
        ]
        
        for alert in alerts:
            self.alert_manager.create_alert(alert)
```

---

## 🎯 **Mode Selection Best Practices Summary**

### **When to Use Development Mode**
- **Active Development**: When actively coding and testing new features
- **Debugging**: When troubleshooting issues and need detailed error information
- **Learning**: When learning Frappe and experimenting with functionality
- **Testing**: When running unit tests and integration tests
- **Prototyping**: When quickly building and iterating on new ideas

### **When to Use Production Mode**
- **Live Deployment**: For customer-facing production environments
- **Performance Testing**: When measuring application performance
- **Security Testing**: When testing security measures and configurations
- **Staging Environment**: For final testing before production deployment
- **Production Staging**: For pre-production validation

### **Mode Transition Guidelines**
- **Always test** in development before deploying to production
- **Create backups** before switching to production mode
- **Verify configuration** settings are appropriate for the target environment
- **Monitor performance** after mode transitions
- **Document changes** for team visibility

### **Security Considerations**
- **Never expose** development mode to the public internet
- **Use different databases** for development and production
- **Implement proper authentication** even in development
- **Regular security audits** of production configurations
- **Monitor access logs** for suspicious activity

---

**💡 Pro Tip**: Always maintain separate configurations for development and production environments. Use environment variables and configuration management tools to ensure consistency across deployments while maintaining appropriate security and performance settings for each environment.
