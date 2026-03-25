# Chapter 3: Anatomy of an App

## 🎯 Learning Objectives

By the end of this chapter, you will master:

- **How** Frappe's app architecture enables modular development
- **Why** hooks are the central integration point for framework functionality
- **When** to use different hook types for optimal performance
- **How** the patch system manages database schema evolution
- **Advanced fixture patterns** for configuration management
- **Performance optimization** of app structure and asset loading

## 📚 Chapter Topics

### 3.1 Understanding Frappe's App Architecture

**The Modular Design Philosophy**

Frappe's app architecture is built around the principle of **loose coupling, high cohesion**. Each app is a self-contained unit that can:

1. **Define its own data models** through DocTypes
2. **Implement business logic** through controllers and hooks
3. **Provide user interfaces** through templates and assets
4. **Integrate with other apps** through well-defined interfaces

**Why This Architecture Works for Business Applications:**

```python
# App loading sequence (simplified)
class AppLoader:
    def __init__(self):
        self.loaded_apps = {}
        self.hooks_registry = {}
        self.routes_registry = {}
    
    def load_app(self, app_name):
        # 1. Load app metadata
        app_meta = self.load_app_metadata(app_name)
        
        # 2. Register hooks
        self.register_hooks(app_meta)
        
        # 3. Load modules
        self.load_modules(app_meta)
        
        # 4. Register routes
        self.register_routes(app_meta)
        
        # 5. Initialize app
        self.initialize_app(app_meta)
        
        self.loaded_apps[app_name] = app_meta
    
    def register_hooks(self, app_meta):
        """Register all hooks from the app"""
        hooks_file = os.path.join(app_meta.app_path, 'hooks.py')
        if os.path.exists(hooks_file):
            exec(open(hooks_file).read())
            # Hooks are now available in global hooks_registry
```

**The App Registry System:**

```python
# How Frappe manages multiple apps
class AppRegistry:
    def __init__(self):
        self.apps = {}
        self.active_apps = set()
        self.module_map = {}
    
    def get_app(self, app_name):
        """Get app metadata by name"""
        if app_name not in self.apps:
            self.apps[app_name] = self.load_app(app_name)
        return self.apps[app_name]
    
    def get_module_app(self, module_name):
        """Find which app owns a module"""
        return self.module_map.get(module_name)
    
    def get_apps_for_module(self, module_name):
        """Get all apps that contain a module"""
        return [app for app in self.active_apps 
                if module_name in app.modules]
```

#### Advanced App Structure Patterns

**Multi-App Architecture:**
```
frappe-bench/
├── apps/
│   ├── frappe/                    # Core framework
│   │   ├── frappe/
│   │   │   ├── model/          # ORM, Document classes
│   │   │   ├── utils/          # Utilities
│   │   │   └── www/           # Web framework
│   │   └── public/           # Frontend assets
│   ├── erpnext/                  # Business application
│   │   ├── erpnext/
│   │   │   ├── selling/       # Sales module
│   │   │   ├── stock/         # Inventory module
│   │   │   └── hr/           # HR module
│   │   └── public/
│   └── my_custom_app/           # Your custom app
│       ├── my_custom_app/
│       │   ├── core/           # Core functionality
│       │   ├── integrations/   # Third-party integrations
│       │   └── reports/        # Custom reports
```

**Plugin Architecture:**
```python
# Apps can extend each other through hooks
class PluginArchitecture:
    def __init__(self):
        self.plugins = {}
        self.extensions = {}
    
    def register_plugin(self, plugin_name, plugin_class):
        """Register a plugin class"""
        self.plugins[plugin_name] = plugin_class
        
        # Plugin can extend existing functionality
        if hasattr(plugin_class, 'extend_doctype'):
            for doctype in plugin_class.extend_doctype:
                self.extend_doctype(doctype, plugin_class)
        
        if hasattr(plugin_class, 'override_controller'):
            for controller in plugin_class.override_controller:
                self.override_controller(controller, plugin_class)
```

#### Performance Considerations

**Lazy Loading Strategy:**
```python
# Frappe loads apps and modules on-demand
class LazyAppLoader:
    def __init__(self):
        self._loaded_modules = {}
        self._module_cache = {}
    
    def get_module(self, module_name):
        """Load module only when needed"""
        if module_name not in self._loaded_modules:
            self._loaded_modules[module_name] = importlib.import_module(module_name)
        return self._loaded_modules[module_name]
    
    def get_doctype_class(self, doctype):
        """Get doctype class with caching"""
        cache_key = f"doctype_class_{doctype}"
        if cache_key not in self._module_cache:
            app_name = self.get_app_for_doctype(doctype)
            module = self.get_module(f"{app_name}.{app_name}")
            self._module_cache[cache_key] = getattr(module, doctype)
        return self._module_cache[cache_key]
```

```
apps/
└── my_custom_app/
    ├── my_custom_app/           # Main app package
    │   ├── __init__.py
    │   ├── hooks.py            # App hooks and configuration
    │   ├── modules.txt         # Module definitions
    │   ├── patches.txt         # Database patches
    │   ├── permissions.json    # Default permissions
    │   ├── setup.py            # Package setup
    │   ├── api.py              # Custom API endpoints
    │   ├── utils.py            # Utility functions
    │   ├── overrides.py        # Framework overrides
    │   ├── uninstall.py        # Cleanup on uninstall
    │   ├── my_custom_app/      # Main module
    │   │   ├── __init__.py
    │   │   ├── doctype/        # DocType definitions
    │   │   ├── page/           # Custom pages
    │   │   ├── report/         # Custom reports
    │   │   ├── dashboard_chart/ # Dashboard charts
    │   │   ├── data_migration/ # Data migration scripts
    │   │   ├── templates/      # Jinja templates
    │   │   └── web_template/   # Web templates
    │   ├── config/             # Configuration files
    │   │   └── desktop.json    # Desktop icons
    │   ├── public/             # Static assets
    │   │   ├── js/             # JavaScript files
    │   │   ├── css/            # CSS files
    │   │   ├── images/         # Images
    │   │   └── less/           # LESS stylesheets
    │   └── templates/          # Email/Jinja templates
    │       ├── emails/         # Email templates
    │       └── includes/       # Reusable templates
    ├── requirements.txt        # Python dependencies
    ├── package.json           # Node.js dependencies
    ├── yarn.lock              # Yarn lock file
    └── build.json             # Build configuration
```

#### Key Files Explained

**`__init__.py` (Root)**
```python
# App metadata
__version__ = "1.0.0"
__author__ = "Your Name"
__license__ = "MIT"
__description__ = "Custom ERPNext Application"

# App configuration
app_name = "my_custom_app"
app_title = "My Custom App"
app_publisher = "Your Company"
app_description = "A custom application for ERPNext"
app_icon = "octicon octicon-file-code"
app_color = "grey"
app_version = "1.0.0"
app_homepage = "https://github.com/your-username/my_custom_app"

# Included apps
includes_in_desktop = True

# Required apps (dependencies)
required_apps = ["frappe"]
```

### 3.2 Mastering hooks.py: The Central Integration Point

**Why Hooks Are Critical for Frappe Development**

Hooks are the **primary mechanism** for integrating your custom app with the Frappe framework. They allow you to:

1. **Intercept framework events** at specific points in the request lifecycle
2. **Extend functionality** without modifying core code
3. **Implement cross-app communication** through well-defined interfaces
4. **Optimize performance** by choosing the right hook for the job

#### Understanding Hook Execution Order

**Hook Priority System:**
```python
# Frappe processes hooks in a specific order
class HookExecutionOrder:
    # 1. Early hooks (before any processing)
    BEFORE_REQUEST = 1
    BEFORE_DB_COMMIT = 2
    
    # 2. Document hooks (during document processing)
    BEFORE_INSERT = 10
    VALIDATE = 20
    BEFORE_SAVE = 30
    ON_UPDATE = 40
    ON_SUBMIT = 50
    ON_CANCEL = 60
    
    # 3. Late hooks (after processing)
    AFTER_UPDATE = 70
    AFTER_SUBMIT = 80
    AFTER_CANCEL = 90
    AFTER_DB_COMMIT = 100
```

**Hook Performance Considerations:**
```python
# Different hooks have different performance characteristics
performance_analysis = {
    "doc_events": {
        "frequency": "High - every document operation",
        "impact": "Medium - single document",
        "optimization": "Keep logic minimal, use caching"
    },
    "scheduler_events": {
        "frequency": "Low - scheduled intervals",
        "impact": "High - can affect all data",
        "optimization": "Batch operations, error handling"
    },
    "ui_hooks": {
        "frequency": "High - every page load",
        "impact": "Low - client-side only",
        "optimization": "Minimize JavaScript, use CSS"
    }
}
```

#### Advanced Hook Patterns

**1. Document Event Hooks with Performance Optimization**

```python
# In hooks.py - Optimized document event handling
doc_events = {
    "Sales Order": {
        "validate": "my_app.sales_order.validate_sales_order",
        "before_save": "my_app.sales_order.calculate_totals",
        "on_update": "my_app.sales_order.update_customer_tier",
        "on_submit": "my_app.sales_order.create_deliveries",
        "on_cancel": "my_app.sales_order.cancel_deliveries",
        "after_submit": "my_app.sales_order.send_notifications"
    }
}

# Optimized validation with caching
def validate_sales_order(doc, method):
    """Optimized sales order validation"""
    # Cache expensive calculations
    cache_key = f"so_validation_{doc.name}"
    
    if hasattr(frappe.local, cache_key):
        cached_result = getattr(frappe.local, cache_key)
        if cached_result.get('valid') is not None:
            return cached_result['result']
    
    # Perform validation
    result = perform_validation(doc)
    
    # Cache result for 5 minutes
    setattr(frappe.local, cache_key, {'valid': True, 'result': result})
    
    return result

def perform_validation(doc):
    """Actual validation logic"""
    # Expensive validation logic here
    pass
```

**2. Scheduler Hooks for Background Processing**

```python
# In hooks.py - Background job management
scheduler_events = {
    "daily": [
        "my_app.reports.generate_daily_sales_report",
        "my_app.maintenance.archive_old_records",
        "my_app.notifications.send_daily_digest"
    ],
    "hourly": [
        "my_app.inventory.check_stock_levels",
        "my_app.sync.process_pending_orders"
    ],
    "cron": {
        "0 2 * * *": ["my_app.tasks.nightly_backup"],
        "0 */6 * * *": ["my_app.tasks.sync_external_data"],
        "30 9 * * 1": ["my_app.tasks.monthly_reporting"]
    }
}

# Robust background job implementation
def generate_daily_sales_report():
    """Generate daily sales report with error handling"""
    try:
        # Check if already running
        if frappe.cache().get("daily_report_running"):
            frappe.logger.info("Daily report already running, skipping")
            return
        
        frappe.cache().set("daily_report_running", True, expires_in_sec=300)
        
        # Generate report
        report_data = collect_sales_data()
        report_file = create_report_file(report_data)
        
        # Send notifications
        send_report_notifications(report_file)
        
        # Log completion
        frappe.logger.info(f"Daily report generated: {report_file}")
        
    except Exception as e:
        frappe.log_error(f"Daily report generation failed: {str(e)}")
        # Send error notification
        send_error_notification(str(e))
    finally:
        frappe.cache().delete("daily_report_running")
```

**3. UI Hooks for Client-Side Integration**

```python
# In hooks.py - Client-side asset management
app_include_js = "/assets/my_app/js/app.js"
app_include_css = "/assets/my_app/css/app.css"

# Conditional asset loading
def get_app_include_js():
    """Load JavaScript based on context"""
    if frappe.session.user:
        return "/assets/my_app/js/user_specific.js"
    return "/assets/my_app/js/public.js"

# Dynamic form customization
custom_script = {
    "Sales Order": "my_app.public.js.sales_order_enhancements",
    "Customer": "my_app.public.js.customer_validation",
    "Item": "my_app.public.js.item_pricing_calculator"
}
```

#### Hook Performance Optimization

**1. Hook Debouncing:**
```python
# Prevent hook execution spam
import time
from functools import wraps

def debounce_hook(timeout=300):
    """Decorator to debounce hook execution"""
    def decorator(func):
        last_called = {}
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = f"{func.__name__}_{hash(str(args))}"
            now = time.time()
            
            if key in last_called and (now - last_called[key]) < timeout:
                return  # Skip execution
            
            last_called[key] = now
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Usage in hooks.py
@debounce_hook(timeout=300)
def expensive_calculation(doc):
    """Expensive calculation with debouncing"""
    # Expensive logic here
    pass
```

**2. Hook Error Handling:**
```python
# Robust hook error handling
def safe_hook_execution(hook_name, hook_function):
    """Decorator for safe hook execution"""
    def wrapper(*args, **kwargs):
        try:
            return hook_function(*args, **kwargs)
        except Exception as e:
            # Log error but don't break the flow
            frappe.log_error(f"Hook {hook_name} failed: {str(e)}")
            
            # Return default value if applicable
            if hook_name.startswith("validate_"):
                return False
            elif hook_name.startswith("calculate_"):
                return 0
            return None
    return wrapper

# Usage
@safe_hook_execution("validate_sales_order")
def validate_sales_order(doc):
    # Validation logic
    pass
```

**3. Hook Performance Monitoring:**
```python
# Hook performance monitoring
import time
import frappe

class HookPerformanceMonitor:
    def __init__(self):
        self.metrics = {}
    
    def monitor_hook(self, hook_name):
        """Decorator to monitor hook performance"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                
                try:
                    result = func(*args, **kwargs)
                    success = True
                    error = None
                except Exception as e:
                    result = None
                    success = False
                    error = str(e)
                
                end_time = time.time()
                duration = end_time - start_time
                
                # Record metrics
                self.record_metrics(hook_name, duration, success, error)
                
                return result
            return wrapper
        return decorator
    
    def record_metrics(self, hook_name, duration, success, error):
        """Record hook performance metrics"""
        if hook_name not in self.metrics:
            self.metrics[hook_name] = {
                'total_calls': 0,
                'total_time': 0,
                'failures': 0,
                'avg_time': 0
            }
        
        metrics = self.metrics[hook_name]
        metrics['total_calls'] += 1
        metrics['total_time'] += duration
        metrics['avg_time'] = metrics['total_time'] / metrics['total_calls']
        
        if not success:
            metrics['failures'] += 1
        
        # Log slow hooks
        if duration > 1.0:  # 1 second threshold
            frappe.logger.warning(f"Slow hook: {hook_name} took {duration:.2f}s")
        
        # Log failing hooks
        if not success:
            frappe.logger.error(f"Hook failed: {hook_name} - {error}")

# Usage
monitor = HookPerformanceMonitor()

@monitor.monitor_hook("validate_sales_order")
def validate_sales_order(doc):
    # Validation logic
    pass
```

#### Advanced Hook Techniques

**1. Conditional Hook Registration:**
```python
# In hooks.py - Conditional hook registration
def register_hooks():
    """Register hooks based on configuration"""
    
    # Only register scheduler events if enabled
    if frappe.db.get_single_value("System Settings", "enable_scheduler"):
        scheduler_events.update({
            "daily": ["my_app.tasks.daily_maintenance"],
            "weekly": ["my_app.tasks.weekly_cleanup"]
        })
    
    # Only register UI hooks in development mode
    if frappe.conf.developer_mode:
        app_include_js += ",/assets/my_app/js/dev.js"
        custom_script.update({
            "Sales Order": "my_app.public.js.dev_enhancements"
        })

# Register hooks dynamically
register_hooks()
```

**2. Hook Dependencies:**
```python
# In hooks.py - Hook dependency management
doc_events = {
    "Sales Order": {
        "validate": "my_app.sales_order.validate_sales_order",
        "before_save": "my_app.sales_order.calculate_totals",
        # Hook that depends on validation result
        "on_submit": "my_app.sales_order.create_deliveries"
    }
}

# Ensure calculate_totals runs after validation
def validate_sales_order(doc, method):
    """Sales order validation"""
    # Perform validation
    if not doc.customer:
        frappe.throw("Customer is required")
    
    # Store validation result for other hooks
    doc._validation_passed = True

def create_deliveries(doc, method):
    """Create deliveries only if validation passed"""
    if not getattr(doc, '_validation_passed', False):
        frappe.throw("Cannot create deliveries for invalid order")
    
    # Create deliveries
    create_delivery_records(doc)
```

**3. Cross-App Communication:**
```python
# In hooks.py - Cross-app integration
app_include_js = "/assets/my_app/js/integration.js"

# Whitelist methods for cross-app communication
whitelisted_methods = [
    "my_app.integrations.get_customer_data",
    "my_app.integrations.update_inventory",
    "my_app.integrations.sync_with_external_system"
]

# Integration hooks
integration_hooks = {
    "external_system": {
        "on_update": "my_app.integrations.handle_external_update",
        "on_submit": "my_app.integrations.notify_external_system"
    }
}
```

#### Hook Debugging and Troubleshooting

**Hook Debugging Tools:**
```python
# In hooks.py - Hook debugging utilities
def debug_hooks():
    """Enable hook debugging"""
    # Add debugging to all hooks
    import frappe
    
    original_hooks = {}
    
    def debug_wrapper(hook_name, hook_function):
        original_hooks[hook_name] = hook_function
        
        @wraps(hook_function)
        def wrapper(*args, **kwargs):
            frappe.logger.info(f"Executing hook: {hook_name}")
            frappe.logger.info(f"Args: {args}")
            frappe.logger.info(f"Kwargs: {kwargs}")
            
            result = hook_function(*args, **kwargs)
            
            frappe.logger.info(f"Hook {hook_name} completed")
            return result
        return wrapper
    
    # Wrap all doc_events
    for doctype, events in doc_events.items():
        for event, handler in events.items():
            doc_events[doctype][event] = debug_wrapper(f"{doctype}_{event}", handler)
    
    # Wrap scheduler events
    for frequency, events in scheduler_events.items():
        for i, handler in enumerate(events):
            scheduler_events[frequency][i] = debug_wrapper(f"{frequency}_{i}", handler)

# Enable debugging in development
if frappe.conf.developer_mode:
    debug_hooks()
```

**Hook Performance Analysis:**
```python
# In hooks.py - Performance analysis utilities
def analyze_hook_performance():
    """Analyze hook performance over time"""
    import time
    from collections import defaultdict
    
    performance_data = defaultdict(list)
    
    def analyze_wrapper(hook_name, hook_function):
        @wraps(hook_function)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = hook_function(*args, **kwargs)
                success = True
                error = None
            except Exception as e:
                result = None
                success = False
                error = str(e)
            
            end_time = time.time()
            duration = end_time - start_time
            
            performance_data[hook_name].append({
                'duration': duration,
                'success': success,
                'error': error,
                'timestamp': end_time
            })
            
            return result
        return wrapper
    
    # Wrap all hooks temporarily
    # (This would be done in a development environment)
    
    return performance_data

# Generate performance report
def generate_performance_report():
    """Generate hook performance report"""
    data = analyze_hook_performance()
    
    report = "# Hook Performance Report\n\n"
    
    for hook_name, calls in data.items():
        if not calls:
            continue
        
        total_calls = len(calls)
        total_time = sum(call['duration'] for call in calls)
        avg_time = total_time / total_calls
        failures = sum(1 for call in calls if not call['success'])
        
        report += f"## {hook_name}\n"
        report += f"- Total Calls: {total_calls}\n"
        report += f"- Total Time: {total_time:.2f}s\n"
        report += f"- Average Time: {avg_time:.3f}s\n"
        report += f"- Failures: {failures}\n"
        report += f"- Success Rate: {((total_calls - failures) / total_calls) * 100:.1f}%\n\n"
    
    # Write report to file
    with open('hook_performance_report.md', 'w') as f:
        f.write(report)
    
    frappe.logger.info("Hook performance report generated")
```

### 3.3 modules.txt Organization

The `modules.txt` file defines the modules within your app and their organization.

```txt
# Standard format
Module Name,Module Icon,Color,Label

# Examples
My Custom App,octicon octicon-package,green,My Custom App
Asset Management,octicon octicon-package,blue,Asset Management
Reports,octicon octicon-graph,orange,Reports
Settings,octicon octicon-gear,grey,Settings
```

#### Module Structure

Each module creates its own directory structure:

```
my_custom_app/
├── my_custom_app/
│   ├── __init__.py
│   ├── doctype/
│   ├── page/
│   └── report/
├── asset_management/
│   ├── __init__.py
│   ├── doctype/
│   ├── page/
│   └── report/
├── reports/
│   ├── __init__.py
│   └── report/
└── settings/
    ├── __init__.py
    └── page/
```

### 3.4 patches.txt and the Patch System

Patches manage database schema changes over time.

```txt
# Format: patch_version:description
2023-01-01:add_custom_fields.py:Add custom fields to Sales Order
2023-01-15:update_customer_data.py:Update customer data structure
2023-02-01:remove_deprecated_fields.py:Remove deprecated fields
```

#### Creating Patches

```python
# patches/2023-01-01/add_custom_fields.py

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def execute():
    """Add custom fields to Sales Order"""
    
    custom_fields = {
        "Sales Order": [
            {
                "fieldname": "custom_priority",
                "label": "Priority",
                "fieldtype": "Select",
                "options": "Low\nMedium\nHigh",
                "insert_after": "customer",
                "depends_on": "eval:doc.docstatus == 0"
            },
            {
                "fieldname": "custom_notes",
                "label": "Custom Notes",
                "fieldtype": "Text Editor",
                "insert_after": "terms_and_conditions"
            }
        ]
    }
    
    create_custom_fields(custom_fields)
    frappe.db.commit()
```

### 3.5 Fixtures Folder

Fixtures allow you to export and import configuration data.

#### Common Fixture Types

```python
# fixtures/custom_fields.json
[
    {
        "doctype": "Custom Field",
        "name": "Sales Order-custom_priority",
        "dt": "Sales Order",
        "fieldname": "custom_priority",
        "label": "Priority",
        "fieldtype": "Select",
        "options": "Low\nMedium\nHigh",
        "insert_after": "customer"
    }
]

# fixtures/role_profiles.json
[
    {
        "doctype": "Role Profile",
        "name": "Custom Manager",
        "role": "Custom Manager",
        "roles": [
            {"role": "Sales Manager"},
            {"role": "Custom User"}
        ]
    }
]

# fixtures/property_setters.json
[
    {
        "doctype": "Property Setter",
        "name": "Sales Order-label-customer-Client",
        "doc_type": "Sales Order",
        "property": "label",
        "property_type": "Data",
        "value": "Client",
        "field_name": "customer"
    }
]
```

#### Exporting Fixtures

```bash
# Export specific DocTypes
bench --site dev.local export-fixtures

# Export all fixtures
bench --site dev.local export-fixtures --all

# Export specific fixtures
bench --site dev.local export-doc "Custom Field"
```

### 3.6 Public Directory

The `public` directory contains static assets served to the browser.

#### JavaScript Organization

```
public/
├── js/
│   ├── app.js              # App-wide JavaScript
│   ├── desk.js             # Desk-specific scripts
│   ├── forms/              # Form-specific scripts
│   │   ├── sales_order.js
│   │   └── customer.js
│   ├── utils/              # Utility functions
│   │   ├── helpers.js
│   │   └── validators.js
│   └── components/         # Reusable components
│       ├── custom_dialog.js
│       └── data_table.js
```

#### CSS Organization

```
public/
├── css/
│   ├── app.css             # App-wide styles
│   ├── desk.css            # Desk-specific styles
│   ├── forms/              # Form-specific styles
│   │   ├── sales_order.css
│   │   └── customer.css
│   ├── components/         # Component styles
│   └── print/              # Print format styles
```

### 3.7 Templates Directory

The `templates` directory contains Jinja templates for various purposes.

#### Email Templates

```html
<!-- templates/emails/custom_notification.html -->
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <h2 style="color: #333;">{{ subject }}</h2>
    
    <p>Hello {{ recipient_name }},</p>
    
    <p>{{ message }}</p>
    
    {% if doc %}
    <div style="background: #f5f5f5; padding: 15px; margin: 15px 0;">
        <h3>Document Details</h3>
        <p><strong>Document Type:</strong> {{ doc.doctype }}</p>
        <p><strong>Name:</strong> {{ doc.name }}</p>
        <p><strong>Status:</strong> {{ doc.status }}</p>
    </div>
    {% endif %}
    
    <p>Best regards,<br>{{ sender_name }}</p>
</div>
```

#### Web Templates

```html
<!-- templates/includes/custom_header.html -->
<header class="custom-header">
    <div class="container">
        <div class="logo">
            <img src="{{ app_logo }}" alt="{{ app_name }}">
        </div>
        <nav class="main-nav">
            <ul>
                <li><a href="/home">Home</a></li>
                <li><a href="/about">About</a></li>
                <li><a href="/contact">Contact</a></li>
            </ul>
        </nav>
    </div>
</header>
```

## 🛠️ Practical Exercises

### Exercise 3.1: Create a Complete App Structure

1. Create a new app with proper structure
2. Set up `hooks.py` with various hooks
3. Create `modules.txt` with multiple modules
4. Add fixtures for configuration

### Exercise 3.2: Implement Hooks

1. Create document event handlers
2. Set up scheduled tasks
3. Add custom navigation items
4. Implement API endpoints

### Exercise 3.3: Manage Database Changes

1. Create a patch to add custom fields
2. Export and import fixtures
3. Test patch execution
4. Verify data integrity

## 🚀 Best Practices

### File Organization

- **Keep related files together** in module directories
- **Use descriptive naming** for files and functions
- **Separate concerns** between UI, business logic, and data access
- **Document your hooks** with comments explaining their purpose

### Hook Management

- **Minimize hook usage** to only necessary integrations
- **Use descriptive function names** for hook handlers
- **Handle errors gracefully** in hook functions
- **Test hooks thoroughly** in different scenarios

### Patch Management

- **Use semantic versioning** for patch naming
- **Write backward-compatible patches** when possible
- **Test patches on staging** before production
- **Document patch dependencies** and execution order

## 📖 Further Reading

- [Frappe App Development Guide](https://frappeframework.com/docs/user/en/development/app-development)
- [Hooks Reference](https://frappeframework.com/docs/user/en/development/hooks)
- [Patch System Documentation](https://frappeframework.com/docs/user/en/development/patch-system)

## 🎯 Chapter Summary

Understanding app anatomy is crucial for effective Frappe development:

- **Structure matters** - Organize files logically within modules
- **Hooks are powerful** - Use them to integrate with the framework
- **Patches manage change** - Keep database schema evolution under control
- **Fixtures enable configuration** - Export and import settings easily
- **Assets complete the experience** - JavaScript, CSS, and templates enhance UX

---

**Next Chapter**: Advanced DocType design and metadata management.


---

## 📌 Addendum: pyproject.toml in Frappe v15 & the __init__.py Requirement

### pyproject.toml Transition (Frappe v15)

Frappe v15 moves away from `setup.py` toward the modern Python packaging standard using `pyproject.toml`.  If you scaffold a new app with `bench new-app` on v15 you will get a `pyproject.toml` instead of `setup.py`.

```toml
# pyproject.toml (Frappe v15 style)
[build-system]
requires = ["flit_core>=3.4,<4"]
build-backend = "flit_core.buildapi"

[project]
name = "my_custom_app"
version = "1.0.0"
description = "A custom ERPNext application"
requires-python = ">=3.10"
dependencies = [
    "frappe",
]

[project.urls]
Homepage = "https://github.com/your-org/my_custom_app"
```

If you are maintaining a v14 app and want to stay compatible with v15, add a `pyproject.toml` alongside your existing `setup.py` — bench will prefer `pyproject.toml` when present.

### __init__.py is Required in Every Package Directory

Every directory that Python needs to treat as a package **must** contain an `__init__.py` file, even if it is empty.  Missing `__init__.py` files are a common source of `ModuleNotFoundError` in Frappe apps.

```
my_custom_app/
├── my_custom_app/
│   ├── __init__.py          ← required
│   ├── hooks.py
│   ├── my_custom_app/       ← module directory
│   │   ├── __init__.py      ← required
│   │   └── doctype/
│   │       ├── __init__.py  ← required
│   │       └── my_doctype/
│   │           ├── __init__.py   ← required
│   │           ├── my_doctype.py
│   │           └── my_doctype.json
│   └── data_migration/
│       ├── __init__.py      ← required (even if empty)
│       └── import_data.py
```

A quick way to create missing `__init__.py` files across your app:

```bash
find apps/my_custom_app -type d -exec touch {}/__init__.py \;
```


---

## Addendum: Source Article Insights

### Professional App Boilerplate Setup

When you run `bench new-app your-app-name`, Frappe creates a skeleton. Here's the professional setup process to make it production-ready.

**Step 1: Create the app**
```bash
bench new-app your_app_name
# App Title: Your App Name
# App Description: Comprehensive description
# App Publisher: Your Organization
# App Email: contact@yourorg.com
# App License: MIT
```

**Step 2: Set up `setup.py` properly**
```python
from setuptools import setup, find_packages
from your_app import __version__ as version

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

setup(
    name="your_app_name",
    version=version,
    description="Your comprehensive app description",
    author="Your Organization",
    author_email="contact@yourorg.com",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires
)
```
`setup.py` is the identity card of your app — without it, dependencies won't install automatically, version tracking for patches may fail, and deployment won't work properly.

**Step 3: Version and constants**

Start at `0.1.0` not `0.0.1` — `0.0.x` signals "barely started", `0.1.0` signals "early but usable":

```python
# your_app/__init__.py
from .constants import *

__version__ = "0.1.0"
```

```python
# your_app/constants.py
APP_NAME = "Your App Name"
APP_VERSION = "0.1.0"

ERRORS = {
    "no_permission": "Insufficient permissions"
}

DEFAULT_PAGE_SIZE = 20
MAX_UPLOAD_SIZE = 10485760  # 10MB
API_VERSION = "v1"
DEFAULT_TIMEOUT = 30
```

Import via `__init__.py` so you can call constants directly:
```python
import my_app, frappe
frappe.throw(_(my_app.ERRORS.get("no_permission")))
```

**Step 4: `requirements.txt`**
```txt
# frappe -- https://github.com/frappe/frappe is installed via 'bench init'
# Add your app-specific dependencies here:
# requests>=2.28.0
# pandas>=1.5.0
```

**Step 5: Branding in `hooks.py`**
```python
# hooks.py
app_logo_url = "/assets/your_app/images/branding/logo.png"

website_context = {
    "favicon": "/assets/your_app/images/branding/favicon.png",
    "splash_image": "/assets/your_app/images/branding/logo.png"
}

# Installation hooks
after_migrate = "your_app.utils.install.after_migrate"
```

**Step 6: Installation automation**
```python
# your_app/utils/install.py
import frappe

def after_install():
    set_app_logo()
    set_system_settings()
    set_navbar_settings()
    set_website_settings()

def after_migrate():
    set_app_logo()
    set_system_settings()
    set_navbar_settings()
    set_website_settings()

def set_app_logo():
    app_logo = frappe.get_hooks("app_logo_url")[-1]
    frappe.db.set_single_value("Navbar Settings", "app_logo", app_logo)

def set_system_settings():
    settings = frappe.get_doc("System Settings")
    settings.session_expiry = "12:00"
    settings.login_with_email_link = False
    settings.allow_guests_to_upload_files = True
    settings.link_field_results_limit = 10
    settings.save()

def set_website_settings():
    settings = frappe.get_doc("Website Settings")
    settings.app_name = "Your App Name"
    settings.home_page = "login"
    settings.hide_footer_signup = True
    settings.save()
```

**Step 7: Directory structure**
```
your_app/
├── __init__.py              # Package init + version
├── hooks.py                 # Frappe hooks
├── constants.py             # App constants
├── modules.txt              # Module definitions
├── patches.txt              # Database patches
├── api/
│   └── v1/
│       ├── __init__.py
│       ├── auth.py
│       └── main.py
├── public/
│   └── images/
│       └── branding/
│           ├── favicon.png
│           └── logo.png
├── translations/
│   └── ar.csv               # Arabic translations
├── utils/
│   └── install.py           # Installation utilities
└── www/                     # Web pages
```

**Step 8: Git branching strategy**
```bash
# Initial push to dev branch
git add .
git commit -m "feat: initial project setup"
git branch -M dev
git remote add upstream <your-repo-url>
git push upstream dev

# Create staging branch
git checkout -b staging
git push upstream staging
```

Branch workflow: `dev → staging → main`
- `dev`: active development
- `staging`: QA/UAT testing
- `main`: production-ready code

Use `upstream` (not `origin`) to point to the central shared repository — `origin` is typically your personal fork.

---

### DocType Namespacing in Frappe

Frappe deliberately avoids traditional namespacing (like `hr.Employee`) in favor of short, clear names (`Employee`). This is a conscious design choice prioritizing simplicity.

**Why no traditional namespacing?**
```python
# Frappe's approach (simple)
frappe.get_doc("Employee", "EMP-001")
frappe.get_doc("Department", self.department)

# Traditional namespacing (more complex)
frappe.get_doc("hr.Employee", "EMP-001")
frappe.get_doc("hr.Department", self.department)
```

**How Frappe prevents conflicts without namespacing:**

1. **App Isolation** — each app is a separate entity with its own file structure:
```
apps/
  hr/hr/doctype/employee/employee.json    # module: "HR"
  payroll/payroll/doctype/employee/...    # module: "Payroll"
```

2. **Database-level uniqueness** — each DocType gets its own table:
```sql
CREATE TABLE `tabEmployee` (...);          -- From HR App
CREATE TABLE `tabPayrollEmployee` (...);   -- From Payroll App
```

3. **Site-level App Registry** — only installed apps can register DocTypes:
```python
# site_config.json
{"installed_apps": ["frappe", "erpnext", "hr"]}
```

**Critical rules:**
- You **cannot** have two DocTypes with the same name in two different apps installed on the **same site** — they'd both try to create `tabEmployee` and conflict
- You **can** have the same DocType name across different apps if they're installed on **different sites** — each site has its own isolated database
- Same rule applies to **module names** — module names must be unique per site

```python
# Runtime resolution: when you call frappe.get_doc("Employee", "EMP-001")
# Frappe:
# 1. Checks DocType cache (includes app metadata)
# 2. Verifies DocType exists in installed apps
# 3. Loads schema from DocType JSON
# 4. Queries tabEmployee
```

**Best practice for naming custom DocTypes:**
```python
# Prefix with app/domain context to avoid future conflicts
"HR Employee"        # Instead of just "Employee"
"Custom Task"        # Instead of just "Task"
"Project Customer"   # Instead of just "Customer"
```

**Multi-site architecture:**
```
site1.local → installed: [frappe, hr]      → has tabEmployee (HR schema)
site2.local → installed: [frappe, payroll] → has tabEmployee (Payroll schema)
# No conflict — completely isolated databases
```


---

## 📌 Addendum: How to Rename a Module in Frappe

Renaming a module requires changes in both the UI and the source code. Do all four steps — skipping any one causes "Module not found" errors.

### Step 1: Rename via Module Def (UI)

1. Go to **Module Def** from the Desk
2. Open the module you want to rename
3. Click **Rename**
4. If a module with the new name already exists, select **"Merge with existing"**
5. Confirm

### Step 2: Rename the Folder in Source Code

```
apps/your_app/your_app/old_module_name/
                          ↓
apps/your_app/your_app/new_module_name/
```

Use `snake_case` for the folder name.

### Step 3: Update DocType JSON Files

For every DocType under the renamed module, open its `.json` file and update the `"module"` field:

```
apps/your_app/your_app/new_module_name/doctype/your_doctype/your_doctype.json
```

```json
{
    "module": "New Module Name"
}
```

The `"module"` value must be **Title Case** (e.g., `"Parent Attachments"`), while the folder name is `snake_case` (e.g., `parent_attachments`).

### Step 4: Update `modules.txt`

```
apps/your_app/your_app/modules.txt
```

Add the new module name and remove the old one:

```txt
New Module Name
Other Module
```

### Step 5: Rebuild and Migrate

```bash
bench build
bench clear-cache
bench migrate
bench restart
```

### Common Mistakes

| Mistake | Result |
|---|---|
| Folder name doesn't match `modules.txt` | "Module not found" error |
| `"module"` field in JSON not updated | DocTypes appear under wrong module |
| Old module name left in `modules.txt` | Duplicate module entries |
| Skipping `bench migrate` | Database not synced with new module name |

### When a Patch Is Also Needed

If the module rename affects an **existing production site** (not a fresh install), write a patch to handle the rename for sites already running the old module name. See chapter 22 for the patch pattern.
