# Chapter 33: Interview Preparation Guide

## 🎯 Learning Objectives

By the end of this chapter, you will be prepared for:

- **Junior Developer** positions (1-2 years experience)
- **Senior Developer** positions (3+ years experience)  
- **Technical Lead** roles requiring Frappe expertise
- **ERPNext Consultant** interviews
- **Framework Architecture** discussions

## 📚 Chapter Topics

### 33.1 Junior Developer Questions (1-14)

**1. What is the Frappe Framework, and how is it different from traditional web frameworks?**

**Answer:** Frappe is a metadata-driven, full-stack framework that uses DocTypes to define both data structure and behavior. Unlike traditional frameworks that separate database models, API endpoints, and UI components, Frappe generates all three from a single DocType definition.

**Key Differences:**
- **Traditional**: Separate models.py, views.py, urls.py, serializers.py
- **Frappe**: Single DocType definition generates database table, REST API, and UI
- **Metadata-driven**: Configuration over code for common operations
- **Built-in features**: Permissions, workflows, audit trails included

**2. What are DocTypes in Frappe? How do you create one?**

**Answer:** A DocType is a metadata definition that describes a document type in Frappe. It defines fields, permissions, relationships, and behavior.

**Creating a DocType:**
```python
# Method 1: Programmatically
doctype = {
    "doctype": "DocType",
    "name": "Custom Document",
    "module": "Custom App",
    "fields": [
        {"fieldname": "title", "fieldtype": "Data", "label": "Title", "reqd": 1},
        {"fieldname": "status", "fieldtype": "Select", "options": "Active\nInactive"}
    ]
}

# Method 2: Using bench command
bench new-doctype "Custom Document"
```

**3. What is the difference between a DocType and a Document in Frappe?**

**Answer:** 
- **DocType**: The blueprint/template that defines structure and behavior
- **Document**: An actual instance/record of that DocType

**Analogy:** DocType is like a class in OOP, Document is like an object instance.

**4. What is the difference between a DocType and a Custom Field in Frappe?**

**Answer:**
- **DocType**: Complete document definition with full lifecycle
- **Custom Field**: Additional field added to existing DocType without modifying core

**Use Cases:**
- Custom Field: Add extra field to standard ERPNext DocType
- DocType: Create entirely new document type

**5. What is a Frappe Hook, and why is it used?**

**Answer:** Hooks are extension points that allow apps to execute code at specific events or integrate with Frappe's core functionality.

**Types of Hooks:**
```python
# hooks.py
doc_events = {
    "Sales Order": {
        "validate": "my_app.utils.validate_sales_order",
        "on_submit": "my_app.utils.create_delivery"
    }
}

app_include_js = "/assets/my_app/js/custom.js"
app_include_css = "/assets/my_app/css/custom.css"
```

**6. How would you implement a custom API in Frappe?**

**Answer:** Use `@frappe.whitelist()` decorator to create REST endpoints:

```python
# api.py
import frappe
from frappe import _

@frappe.whitelist()
def get_customer_orders(customer_id):
    """Get all orders for a customer"""
    if not frappe.has_permission("Sales Order", "read"):
        frappe.throw(_("Not permitted"), frappe.PermissionError)
    
    return frappe.get_all("Sales Order", 
        filters={"customer": customer_id},
        fields=["name", "transaction_date", "grand_total", "status"]
    )

# Call from client
frappe.call({
    method: "my_app.api.get_customer_orders",
    args: {customer_id: "CUST-001"},
    callback: function(r) {
        console.log(r.message);
    }
});
```

**7. How does Role-Based Permission work in Frappe?**

**Answer:** Frappe uses a hierarchical permission system:

**Permission Levels:**
- **Role**: Collection of permissions (e.g., "Sales Manager", "System Manager")
- **Permission Level**: 0 (Read), 1 (Write), 2 (Create), 3 (Submit), 4 (Cancel), 5 (Amend)
- **DocType Permissions**: Define which roles can access which DocTypes
- **Row-Level Permissions**: Restrict access to specific records

**Example:**
```python
# Permission setup in DocType
{
    "permissions": [
        {
            "role": "Sales Manager",
            "read": 1,
            "write": 1,
            "create": 1,
            "submit": 1
        }
    ]
}
```

**8. Explain the concept of workflow in Frappe.**

**Answer:** Workflows define state transitions and business rules for documents:

**Key Components:**
- **States**: Document status (Draft, Pending, Approved, Rejected)
- **Transitions**: Allowed moves between states
- **Actions**: What happens during transitions
- **Conditions**: Rules for when transitions are allowed

**Example:**
```python
# Workflow Definition
workflow = {
    "document_type": "Leave Application",
    "states": [
        {"state": "Draft", "allowed_roles": ["Employee"]},
        {"state": "Pending Approval", "allowed_roles": ["Leave Manager"]},
        {"state": "Approved", "allowed_roles": ["Leave Manager"]},
        {"state": "Rejected", "allowed_roles": ["Leave Manager"]}
    ],
    "transitions": [
        {"from_state": "Draft", "to_state": "Pending Approval", "action": "Submit"},
        {"from_state": "Pending Approval", "to_state": "Approved", "action": "Approve"},
        {"from_state": "Pending Approval", "to_state": "Rejected", "action": "Reject"}
    ]
}
```

**9. What is the purpose of the `bench` command in Frappe?**

**Answer:** Bench is Frappe's command-line tool for managing apps, sites, and development workflows:

**Key Commands:**
```bash
# Site Management
bench new-site mysite.localhost
bench --site mysite.localhost migrate
bench --site mysite.localhost backup

# App Management  
bench new-app my_custom_app
bench get-app erpnext
bench install-app my_custom_app

# Development
bench start
bench build
bench watch

# Database
bench --site mysite.localhost console
bench --site mysite.localhost mariadb
```

**10. How does Frappe manage database migrations?**

**Answer:** Through patches and automatic schema management:

**Migration Process:**
1. **Patches.txt**: Lists migration scripts in execution order
2. **Patch Scripts**: Python files that modify database schema
3. **Auto-execution**: Patches run automatically during `bench migrate`
4. **Version Tracking**: Each patch records its execution

**Example Patch:**
```python
# patches/v1_0/add_customer_credit_limit.py
import frappe

def execute():
    """Add credit_limit field to Customer"""
    frappe.db.add_column("Customer", "credit_limit", "Decimal(18,2)")
    frappe.db.commit()
```

**11. What is a patch in Frappe?**

**Answer:** A patch is a Python script that modifies database schema or data during version upgrades:

**Types of Patches:**
- **Schema Patches**: Add columns, tables, indexes
- **Data Patches**: Migrate data, fix inconsistencies
- **Custom Patches**: Business logic updates

**12. How would you handle data migration in Frappe from an external system to ERPNext?**

**Answer:** Use a combination of tools and approaches:

**Migration Strategy:**
1. **Data Import**: Use CSV/Excel import for basic data
2. **Custom Scripts**: Write migration scripts for complex transformations
3. **API Integration**: Use REST APIs for real-time sync
4. **Data Validation**: Validate imported data before commit

**Example Migration Script:**
```python
def migrate_customers():
    """Migrate customers from legacy system"""
    legacy_data = get_legacy_customers()
    
    for customer in legacy_data:
        try:
            doc = frappe.get_doc({
                "doctype": "Customer",
                "customer_name": customer["name"],
                "email": customer["email"],
                "customer_group": "Commercial"
            })
            doc.insert(ignore_permissions=True)
        except Exception as e:
            frappe.log_error(f"Failed to migrate customer: {e}")
    
    frappe.db.commit()
```

**13. What do you know about Fixtures?**

**Answer:** Fixtures are configuration data that gets exported and imported with apps:

**Types of Fixtures:**
- **DocTypes**: Document structure definitions
- **Custom Fields**: Field definitions
- **Roles & Permissions**: Access control
- **Workflows**: Business process definitions
- **Print Formats**: Template definitions

**Usage:**
```bash
# Export fixtures
bench --site mysite.localhost export-fixtures

# Import fixtures  
bench --site mysite.localhost import-fixtures
```

**14. What do you know about Property Setter?**

**Answer:** Property Setter allows runtime modification of DocType properties without changing core code:

**Use Cases:**
- Hide fields based on conditions
- Change field labels dynamically
- Modify field properties
- Set default values

**Example:**
```python
# Hide field for specific role
frappe.db.set_value("Property Setter", 
    None, "property", "hidden", 
    {
        "doctype_or_field": "DocField",
        "doc_type": "Sales Order", 
        "field_name": "delivery_date",
        "property": "hidden",
        "property_type": "Check",
        "value": "1"
    }
)
```

### 33.2 Senior Developer Questions (15-26)

**15. What is the difference between Redis cache and local cache in Frappe?**

**Answer:** 
- **Redis Cache**: Shared across multiple workers, persistent, suitable for production
- **Local Cache**: Process-specific, faster but not shared, suitable for development

**Cache Hierarchy:**
1. **Redis**: Global cache (mem_cache, def_query_builder)
2. **Local**: In-process cache (request-specific data)
3. **Database**: Source of truth

**16. What is the difference between Frappe and ERPNext?**

**Answer:**
- **Frappe**: The underlying framework for building applications
- **ERPNext**: The ERP application built on Frappe framework

**Relationship:**
- Frappe provides: ORM, UI framework, permissions, workflows
- ERPNext provides: Accounting, Inventory, HR, CRM modules
- Other Frappe apps: Healthcare, Education, eCommerce

**17. What do you know about bench commands? What commands do you know about?**

**Answer:** Comprehensive command suite for Frappe development:

**Essential Commands:**
```bash
# Development
bench start              # Start development server
bench build             # Build assets
bench watch             # Watch for changes

# Database
bench migrate           # Run migrations
bench --site site db backup     # Backup database
bench --site site db restore     # Restore database

# Apps
bench new-app app_name  # Create new app
bench get-app app_name  # Install existing app
bench install-app app_name # Install app on site

# Utilities
bench doctor            # Check system health
bench --site site console       # Python console
bench --site site mariadb       # Database shell
```

**18. What is the architecture of Frappe and bench?**

**Answer:** Multi-layered architecture:

**Frappe Framework Architecture:**
- **Core**: Database layer, ORM, permissions
- **API**: REST endpoints, real-time updates
- **UI**: Desk interface, form builder
- **Apps**: Modular application system

**Bench Architecture:**
- **Multi-site**: Single codebase, multiple sites
- **App isolation**: Each app in separate folder
- **Shared resources**: Common libraries, frameworks
- **Environment management**: Virtual environment per bench

**19. How does Frappe handle database transactions? Explain commit and rollback.**

**Answer:** Frappe provides transaction management at multiple levels:

**Transaction Methods:**
```python
# Manual transaction control
frappe.db.begin()     # Start transaction
frappe.db.commit()    # Commit changes
frappe.db.rollback()  # Rollback changes

# Savepoints for nested transactions
frappe.db.savepoint("sp1")
frappe.db.rollback_to_savepoint("sp1")
frappe.db.release_savepoint("sp1")

# Document-level transactions
doc = frappe.get_doc("Sales Order", "SO-001")
doc.submit()  # Automatic transaction management
```

**Transaction Rules:**
- Each HTTP request wrapped in transaction
- Auto-commit on successful request
- Auto-rollback on exception
- Write limits enforced (default 1000 writes per transaction)

**20. What are the different types of hooks in Frappe?**

**Answer:** Comprehensive hook system for extensibility:

**Hook Categories:**
```python
# Document Events
doc_events = {
    "Sales Order": {
        "validate": "my_app.validate_so",
        "on_submit": "my_app.submit_so"
    }
}

# UI Hooks
app_include_js = "/assets/my_app/js/custom.js"
app_include_css = "/assets/my_app/css/custom.css"
boot_session = "my_app.boot_session"

# Scheduler Events
scheduler_events = {
    "daily": ["my_app.daily_task"],
    "weekly": ["my_app.weekly_task"]
}

# Database Hooks
before_insert = "my_app.before_insert"
after_insert = "my_app.after_insert"

# Permission Hooks
has_permission = "my_app.check_permission"
permission_query_conditions = "my_app.permission_filter"
```

**21. How do you optimize performance in Frappe applications?**

**Answer:** Multi-level optimization approach:

**Database Optimization:**
```python
# Use specific fields instead of *
frappe.get_all("Sales Order", fields=["name", "grand_total"])

# Use indexes properly
frappe.db.sql("CREATE INDEX idx_customer ON `tabSales Order`(customer)")

# Bulk operations
frappe.db.bulk_insert("Sales Order Item", items_data)
```

**Cache Optimization:**
```python
# Use cache for frequently accessed data
cache_key = "customer_rates"
customer_rates = frappe.cache().get(cache_key)
if not customer_rates:
    customer_rates = get_customer_rates()
    frappe.cache().set(cache_key, customer_rate, expires_in_sec=3600)
```

**Query Optimization:**
```python
# Use EXISTS instead of IN for subqueries
frappe.db.sql("""
    SELECT so.name FROM `tabSales Order` so
    WHERE EXISTS (
        SELECT 1 FROM `tabSales Order Item` soi 
        WHERE soi.parent = so.name AND soi.item_code = %s
    )
""", item_code)
```

**22. What is the purpose of the `frappe.local` object?**

**Answer:** Thread-local storage for request-specific data:

**Common Uses:**
```python
# Request information
frappe.local.request_ip      # Client IP
frappe.local.request_url     # Request URL
frappe.local.site            # Current site name

# Database connection
frappe.local.db              # Database instance
frappe.local.redis           # Redis connection

# User context
frappe.local.user            # Current user
frappe.local.session_user   # Session user

# Form context (in forms)
frappe.local.form_dict      # Form data
frappe.local.doc            # Current document
```

**23. How does Frappe handle real-time updates?**

**Answer:** Real-time updates via WebSockets and Redis:

**Architecture:**
1. **WebSocket Server**: Handles real-time connections
2. **Redis Pub/Sub**: Message broadcasting
3. **Client-side**: Socket.IO integration
4. **Event System**: Document change notifications

**Implementation:**
```python
# Server-side event emission
frappe.publish_realtime('event_name', data, user='user@example.com')

# Client-side listening
frappe.realtime.on('event_name', function(data) {
    console.log('Received:', data);
});
```

**24. What are the different types of fields available in Frappe?**

**Answer:** Comprehensive field type system:

**Basic Fields:**
- **Data**: Single line text
- **Text**: Multi-line text
- **Int**: Integer numbers
- **Float**: Decimal numbers
- **Currency**: Monetary values
- **Date**: Date picker
- **Datetime**: Date and time
- **Select**: Dropdown options
- **Link**: Reference to other DocType
- **Table**: Child table

**Advanced Fields:**
- **HTML**: Rich text content
- **Code**: Syntax-highlighted code
- **JSON**: JSON data structure
- **Geolocation**: Latitude/longitude
- **Signature**: Digital signature
- **Barcode**: Barcode generation
- **QR Code**: QR code generation

**Special Fields:**
- **Attach**: File uploads
- **Image**: Image uploads
- **Password**: Encrypted passwords
- **Read Only**: Display-only fields
- **Hidden**: Non-visible fields

**25. How do you create custom reports in Frappe?**

**Answer:** Multiple approaches for custom reports:

**Script Reports:**
```python
# report.py
import frappe

def execute(filters=None):
    columns = [
        {"label": "Customer", "fieldname": "customer", "fieldtype": "Link", "options": "Customer"},
        {"label": "Total Sales", "fieldname": "total_sales", "fieldtype": "Currency"}
    ]
    
    data = frappe.db.sql("""
        SELECT customer, SUM(grand_total) as total_sales
        FROM `tabSales Order`
        WHERE docstatus = 1
        GROUP BY customer
    """, as_dict=True)
    
    return columns, data
```

**Query Reports:**
```python
# Simple SQL-based report
frappe.get_doc({
    "doctype": "Report",
    "name": "Sales Summary",
    "report_name": "Sales Summary",
    "report_type": "Query Report",
    "query": "SELECT customer, SUM(grand_total) FROM `tabSales Order` WHERE docstatus = 1 GROUP BY customer"
})
```

**26. What is the difference between `frappe.get_doc` and `frappe.get_all`?**

**Answer:** Different data retrieval methods:

**frappe.get_doc():**
- Returns single document object
- Includes all fields and methods
- Can modify and save
- Higher memory usage

```python
doc = frappe.get_doc("Sales Order", "SO-001")
doc.customer = "New Customer"
doc.save()
```

**frappe.get_all():**
- Returns list of dictionaries
- Only specified fields
- Read-only access
- Lower memory usage

```python
orders = frappe.get_all("Sales Order", 
    fields=["name", "customer", "grand_total"],
    filters={"docstatus": 1}
)
```

### 33.3 Expert Level Questions (27+)

**27. How does Frappe handle multi-tenancy?**

**Answer:** Site-based multi-tenancy architecture:

**Multi-tenancy Features:**
- **Site Isolation**: Each site has separate database
- **Shared Code**: Single Frappe installation serves multiple sites
- **Resource Sharing**: Apps shared across sites
- **Configuration**: Site-specific settings

**Implementation:**
```bash
# Create multiple sites
bench new-site site1.localhost
bench new-site site2.localhost
bench new-site site3.localhost

# All sites share same apps
bench --site site1.localhost install-app erpnext
bench --site site2.localhost install-app erpnext
```

**28. What is the purpose of the `frappe.conf` file?**

**Answer:** Site-specific configuration file:

**Key Settings:**
```python
# Database configuration
db_host = "localhost"
db_port = 3306
db_name = "site1_db"

# Security settings
disable_signup = 1
integrate_apps = ["google"]

# Performance settings
max_file_size = 10485760  # 10MB
backup_limit = 5

# Developer settings
developer_mode = 1
serve = True
```

**29. How does Frappe handle background jobs?**

**Answer:** Redis-based job queue system:

**Job Types:**
- **Scheduled Jobs**: Cron-like scheduling
- **Background Jobs**: Long-running tasks
- **Real-time Jobs**: Immediate processing

**Implementation:**
```python
# Enqueue background job
frappe.enqueue(
    method="my_app.long_running_task",
    queue="default",
    timeout=600,
    is_async=True,
    job_name="Process Orders"
)

# Scheduled job in hooks.py
scheduler_events = {
    "daily": ["my_app.daily_sync"],
    "hourly": ["my_app.hourly_cleanup"]
}
```

**30. What are the different types of DocTypes in Frappe?**

**Answer:** Four main DocType categories:

**1. Document (Standard):**
- Multiple records
- Database table created
- Full CRUD operations

**2. Single:**
- Single record per DocType
- Stored in tabSingles table
- Used for configuration

**3. Child Table:**
- Linked to parent document
- No independent existence
- Embedded in parent form

**4. Setup:**
- System configuration
- Usually Single DocType
- Admin-level access

**31. How does Frappe handle permissions at the row level?**

**Answer:** Row-level permission system:

**Implementation Methods:**
```python
# Permission Query Conditions
permission_query_conditions = {
    "Sales Order": "(`tabSales Order`.owner = {user}) or (`tabSales Order`.customer in (select name from `tabCustomer` where owner = {user}))"
}

# has_permission hook
def has_permission(doctype, docname, ptype, user):
    if ptype == "read":
        doc = frappe.get_doc(doctype, docname)
        return doc.owner == user or frappe.has_role("Sales Manager", user)
    return False
```

**32. What is the purpose of the `frappe.db.set_value` vs `frappe.db.sql`?**

**Answer:** Different database operation methods:

**frappe.db.set_value():**
- High-level API
- Handles permissions
- Triggers hooks
- Auto-validation

```python
frappe.db.set_value("Customer", "CUST-001", "credit_limit", 50000)
```

**frappe.db.sql():**
- Low-level SQL execution
- Bypasses permissions
- No hooks triggered
- Manual validation required

```python
frappe.db.sql("UPDATE `tabCustomer` SET credit_limit = %s WHERE name = %s", (50000, "CUST-001"))
```

---

## 🎯 **Interview Preparation Tips**

### **Technical Preparation**
1. **Study the Source Code**: Understand core Frappe files
2. **Practice Examples**: Build small apps demonstrating concepts
3. **Know Version Differences**: v14 vs v15 vs v16 features
4. **Performance Knowledge**: Optimization techniques

### **Practical Assessment**
1. **Live Coding**: Be prepared to write DocType definitions
2. **Problem Solving**: Debug common Frappe issues
3. **Architecture Design**: Design solutions for business requirements
4. **Best Practices**: Follow Frappe coding standards

### **Questions to Ask Interviewer**
1. What Frappe version are you using?
2. How many sites/apps in your environment?
3. What are your biggest technical challenges?
4. What's your deployment strategy?

---

## 📚 **Additional Study Resources**

### **Core Documentation**
- Frappe Framework Documentation
- ERPNext User Guide
- API Reference Guide

### **Practice Projects**
- Build a custom CRM app
- Create integration with external APIs
- Implement complex workflows
- Optimize existing applications

### **Community Resources**
- Frappe Community Forum
- GitHub Discussions
- Frappe Discord Server
- Stack Overflow Questions

---

**💡 Pro Tip**: Focus on understanding *why* Frappe works the way it does, not just *how* to use it. Interviewers value architectural understanding over memorized commands.
