# Chapter 32: Snippets & Quick Reference

## Overview

This chapter is your go-to reference for Frappe/ERPNext development — server-side Python patterns, client-side JavaScript patterns, API usage, database utilities, keyboard shortcuts, and useful tools.

---

## 1. Server-Side Python Snippets

### Reading Data

```python
import frappe
from frappe import _

# Get single field value
value = frappe.db.get_value("Customer", "CUST-001", "customer_name")

# Get multiple fields as tuple
name, group, territory = frappe.db.get_value(
    "Customer", "CUST-001",
    ["customer_name", "customer_group", "territory"]
)

# Get multiple fields as dict
customer = frappe.db.get_value(
    "Customer", "CUST-001",
    ["customer_name", "credit_limit", "territory"],
    as_dict=True
)
print(customer.customer_name)

# Get full document
doc = frappe.get_doc("Sales Order", "SO-0001")
print(doc.customer, doc.grand_total)

# Get document as dict
doc_dict = frappe.get_doc("Sales Order", "SO-0001").as_dict()

# Get single DocType value
setting = frappe.db.get_single_value("System Settings", "enable_scheduler")

# Check existence
exists = frappe.db.exists("Customer", {"customer_name": "ABC Corp"})

# Count documents
count = frappe.db.count("Sales Order", {"customer": "CUST-001", "docstatus": 1})
```

### Writing Data

```python
# Create new document
doc = frappe.new_doc("Customer")
doc.update({
    "customer_name": "ABC Corp",
    "customer_group": "Commercial",
    "territory": "All Territories",
})
doc.insert(ignore_permissions=True)
print(doc.name)  # e.g., "CUST-0001"

# Update single field (skips validations)
doc = frappe.get_doc("Sales Order", "SO-0001")
doc.db_set("status", "Completed")

# Update multiple fields (skips validations)
doc.db_set({
    "status": "Completed",
    "delivery_status": "Delivered",
})

# Update with validations
frappe.db.set_value("Customer", "CUST-001", {"credit_limit": 100000})

# Load, update, save (full validation)
doc = frappe.get_doc("Sales Order", "SO-0001")
doc.status = "Completed"
doc.save(ignore_permissions=True)

# Delete document
frappe.delete_doc("Customer", "CUST-001", ignore_permissions=True)
```

### Querying Data

```python
# SQL query
data = frappe.db.sql("""
    SELECT customer, SUM(grand_total) as total
    FROM `tabSales Order`
    WHERE docstatus = 1
        AND posting_date BETWEEN %(from_date)s AND %(to_date)s
    GROUP BY customer
    ORDER BY total DESC
""", {"from_date": "2024-01-01", "to_date": "2024-12-31"}, as_dict=True)

# get_all with filters
orders = frappe.get_all(
    "Sales Order",
    filters={
        "customer": "CUST-001",
        "status": ["in", ["Draft", "To Deliver"]],
        "docstatus": ["!=", 2],
    },
    fields=["name", "posting_date", "grand_total"],
    order_by="posting_date desc",
    limit=10,
)

# get_list (respects permissions)
orders = frappe.get_list(
    "Sales Order",
    filters={"docstatus": 1},
    fields=["name", "customer", "grand_total"],
    page_length=20,
    start=0,
)

# pluck (get single field as list)
customer_names = frappe.get_all("Customer", pluck="name")
```

### Child Tables

```python
# Get child table data without loading parent
items = frappe.get_all(
    "Sales Order Item",
    filters={"parent": "SO-0001", "parenttype": "Sales Order"},
    fields=["item_code", "qty", "rate", "amount"],
    order_by="idx",
)

# Loop through child table
doc = frappe.get_doc("Sales Order", "SO-0001")
for row in doc.get("items"):
    print(row.item_code, row.qty, row.rate)
    row.qty = row.qty * 2  # Modify
doc.save()

# Append new row
doc = frappe.get_doc("Sales Order", "SO-0001")
doc.append("items", {
    "item_code": "ITEM-001",
    "qty": 10,
    "rate": 100,
})
doc.save()

# Remove rows
doc = frappe.get_doc("Sales Order", "SO-0001")
to_remove = [row for row in doc.items if row.qty == 0]
for row in to_remove:
    doc.remove(row)
doc.save()
```

### Messages and Logging

```python
# Show message to user
frappe.msgprint(_("Order created successfully"))
frappe.msgprint(_("Warning!"), indicator="orange", title=_("Warning"))
frappe.msgprint(_("Error!"), indicator="red", title=_("Error"))

# Throw error (stops execution + rollback)
frappe.throw(_("Customer is required"))
frappe.throw(_("Credit limit exceeded for {0}").format(customer), title=_("Credit Error"))

# Log error
try:
    risky_operation()
except Exception:
    frappe.log_error(title="Operation Failed", message=frappe.get_traceback())

# Show alert (non-blocking)
frappe.publish_realtime("msgprint", {"message": "Background job done"}, user=frappe.session.user)
```

### Document Lifecycle Hooks

```python
class SalesOrder(Document):
    def before_insert(self):
        if not self.delivery_date:
            self.delivery_date = frappe.utils.add_days(frappe.utils.today(), 7)

    def validate(self):
        old_doc = self.get_doc_before_save()
        if old_doc and self.customer != old_doc.customer and self.docstatus == 1:
            frappe.throw(_("Cannot change customer after submission"))

    def on_submit(self):
        self.notify_warehouse()

    def on_cancel(self):
        self.reverse_stock_entries()

    def after_insert(self):
        frappe.sendmail(
            recipients=["manager@company.com"],
            subject=f"New Order: {self.name}",
            message=f"Order {self.name} created for {self.customer}",
        )
```

### Configuration

```python
# Get site config
developer_mode = frappe.get_site_config().get("developer_mode", 0)

# Get/set defaults
default_currency = frappe.defaults.get_default("currency")
frappe.defaults.set_default("currency", "USD")

# User context
frappe.session.user          # Current user email
frappe.session.user_fullname # Current user full name
frappe.get_roles()           # Current user roles
frappe.get_roles("user@example.com")  # Specific user roles

# Switch user context (use carefully)
original_user = frappe.session.user
frappe.set_user("Administrator")
# ... do admin operations ...
frappe.set_user(original_user)

# Field precision
doc = frappe.get_doc("Sales Order", "SO-0001")
precision = doc.precision("grand_total") or 2
rounded = frappe.utils.flt(123.456, precision)
```

### Background Jobs

```python
# Enqueue a background job
frappe.enqueue(
    "myapp.tasks.process_orders",
    queue="long",
    timeout=3600,
    customer="CUST-001",
    from_date="2024-01-01",
)

# Enqueue with deduplication
frappe.enqueue(
    "myapp.tasks.sync_inventory",
    queue="short",
    job_id="sync_inventory_daily",  # Prevents duplicate jobs
    enqueue_after_commit=True,
)

# The task function
def process_orders(customer, from_date):
    orders = frappe.get_all("Sales Order", filters={"customer": customer})
    for order in orders:
        # process each order
        pass
    frappe.db.commit()
```

### Caching

```python
# Redis cache (shared across workers)
frappe.cache.set_value("my_key", {"data": "value"}, expires_in_sec=300)
cached = frappe.cache.get_value("my_key")
frappe.cache.delete_value("my_key")

# User-specific cache
frappe.cache.hset("user_data", frappe.session.user, {"pref": "dark_mode"})
user_data = frappe.cache.hget("user_data", frappe.session.user)
frappe.cache.hdel("user_data", frappe.session.user)

# Clear all cache
frappe.clear_cache()
frappe.clear_website_cache()
```

---

## 2. Client-Side JavaScript Snippets

### Form Operations

```javascript
// Get/set field values
let customer = frm.doc.customer;
frm.set_value("customer", "CUST-001");
frm.set_value({ customer: "CUST-001", delivery_date: "2024-12-31" });

// Show/hide fields
frm.toggle_display("discount_amount", true);
frm.toggle_display(["field1", "field2"], false);

// Enable/disable fields
frm.toggle_enable("customer", frm.doc.docstatus === 0);

// Make mandatory
frm.toggle_reqd("delivery_date", true);

// Set field property
frm.set_df_property("customer", "read_only", 1);
frm.set_df_property("items", "cannot_add_rows", 1);

// Refresh fields
frm.refresh_field("items");
frm.refresh_fields(["items", "grand_total"]);

// Trigger field event
frm.trigger("customer");

// Reload document
frm.reload_doc();

// Save
frm.save();
frm.save("Submit");
frm.save("Cancel");

// Add custom button
frm.add_custom_button(__("My Action"), function() {
    // action
}, __("Group Name"));

// Remove custom button
frm.remove_custom_button(__("My Action"), __("Group Name"));

// Disable save button
frm.disable_save();
frm.enable_save();

// Make form read-only
frm.set_read_only();
```

### API Calls

```javascript
// Standard call
frappe.call({
    method: "myapp.api.my_function",
    args: { param1: "value1" },
    freeze: true,
    freeze_message: __("Processing..."),
    callback: function(r) {
        if (r.message) {
            console.log(r.message);
        }
    },
    error: function(r) {
        frappe.msgprint(__("Error occurred"));
    },
});

// Promise-based
const result = await frappe.xcall("myapp.api.my_function", { param1: "value1" });

// DB shortcuts
frappe.db.get_value("Customer", "CUST-001", "credit_limit", (r) => {
    console.log(r.credit_limit);
});

frappe.db.get_doc("Customer", "CUST-001").then((doc) => {
    console.log(doc.customer_name);
});

frappe.db.get_list("Sales Order", {
    filters: { customer: "CUST-001", docstatus: 1 },
    fields: ["name", "grand_total"],
    limit: 10,
}).then((list) => console.log(list));

frappe.db.exists("Customer", "CUST-001").then((exists) => {
    if (!exists) frappe.throw(__("Customer not found"));
});

frappe.db.count("Sales Order", { customer: "CUST-001" }).then((count) => {
    console.log(`${count} orders`);
});
```

### Dialogs

```javascript
// Confirm
frappe.confirm(__("Are you sure?"), () => { /* yes */ }, () => { /* no */ });

// Prompt
frappe.prompt(
    { label: __("Reason"), fieldtype: "Small Text", reqd: 1 },
    (values) => console.log(values.value),
    __("Enter Reason")
);

// Full dialog
let d = new frappe.ui.Dialog({
    title: __("My Dialog"),
    fields: [
        { label: __("Name"), fieldname: "name", fieldtype: "Data", reqd: 1 },
        { label: __("Date"), fieldname: "date", fieldtype: "Date" },
        { fieldtype: "Column Break" },
        { label: __("Notes"), fieldname: "notes", fieldtype: "Small Text" },
    ],
    primary_action_label: __("Submit"),
    primary_action: function(values) {
        console.log(values);
        d.hide();
    },
});
d.show();

// Get/set dialog values
d.set_value("name", "John");
let name = d.get_value("name");
```

### Notifications

```javascript
// Message popup
frappe.msgprint(__("Operation completed"));
frappe.msgprint({ message: __("Success"), indicator: "green", title: __("Done") });

// Toast notification
frappe.show_alert({ message: __("Saved"), indicator: "green" });
frappe.show_alert({ message: __("Warning"), indicator: "orange" }, 5); // 5 seconds

// Throw error
frappe.throw(__("This field is required"));

// Progress indicator
frappe.show_progress(__("Processing"), 50, 100, __("Half done"));
frappe.hide_progress();
```

### Utilities

```javascript
// Date utilities
frappe.datetime.get_today()                    // "2024-01-15"
frappe.datetime.now_datetime()                 // "2024-01-15 10:30:00"
frappe.datetime.add_days("2024-01-15", 7)      // "2024-01-22"
frappe.datetime.add_months("2024-01-15", 1)    // "2024-02-15"
frappe.datetime.str_to_obj("2024-01-15")       // Date object
frappe.datetime.obj_to_str(new Date())         // "2024-01-15"

// Number formatting
format_currency(1500, "USD")                   // "$1,500.00"
frappe.utils.fmt_money(1500, 2, "USD")
frappe.format(1500, { fieldtype: "Currency" })

// String utilities
frappe.utils.to_title_case("hello world")      // "Hello World"
frappe.utils.strip_html("<b>Hello</b>")        // "Hello"
frappe.utils.truncate("Long text...", 50)

// URL utilities
frappe.utils.get_url()                         // Current site URL
frappe.utils.get_form_link("Customer", "CUST-001")

// Copy to clipboard
frappe.utils.copy_to_clipboard("text to copy");

// Open URL
window.open(frappe.utils.get_form_link("Sales Order", "SO-0001"), "_blank");
```

---

## 3. API Reference

### REST API Endpoints

```bash
# Authentication
POST /api/method/login
  body: { usr: "user@example.com", pwd: "password" }

# RPC calls
POST /api/method/{dotted.path.to.function}
  body: { param1: "value1" }

# Resource CRUD
GET    /api/resource/{DocType}                    # List
POST   /api/resource/{DocType}                    # Create
GET    /api/resource/{DocType}/{name}             # Read
PUT    /api/resource/{DocType}/{name}             # Update
DELETE /api/resource/{DocType}/{name}             # Delete

# Run doc method
POST /api/method/run_doc_method
  body: { dt: "Sales Order", dn: "SO-0001", method: "approve" }
```

### Token Authentication

```bash
# Generate API keys in UI: User → API Access → Generate Keys

# Use in requests
curl -X GET "https://site.com/api/resource/Customer" \
  -H "Authorization: token api_key:api_secret"
```

```python
import requests

headers = {"Authorization": "token api_key:api_secret"}
response = requests.get("https://site.com/api/resource/Customer", headers=headers)
data = response.json()
```

### Rate Limiting

```python
from frappe.rate_limiter import rate_limit

@frappe.whitelist(allow_guest=True)
@rate_limit(limit=5, seconds=60)
def send_otp(mobile):
    """Limited to 5 requests per minute"""
    pass

@frappe.whitelist()
@rate_limit(key="email", limit=10, seconds=3600)
def create_account(email):
    """10 per hour per email"""
    pass
```

### Version-Compatible Import

```python
# Handle API path changes between Frappe versions
try:
    from frappe.api.v1 import get_request_form_data
except ImportError:
    from frappe.api import get_request_form_data

@frappe.whitelist()
def my_endpoint():
    data = get_request_form_data()
    return data
```

---

## 4. Database Utilities

### Table Trimming

```bash
# Preview orphan columns (dry run)
bench --site mysite trim-tables --dry-run

# Execute trimming (with auto-backup)
bench --site mysite trim-tables

# Skip backup (not recommended)
bench --site mysite trim-tables --no-backup
```

```python
from frappe.model.meta import trim_table, trim_tables

# Check orphans for one DocType
orphans = trim_table("Customer", dry_run=True)
print(f"Orphan columns: {orphans}")

# Remove orphans
trim_table("Customer", dry_run=False)

# Trim all tables
result = trim_tables(dry_run=False)

# Check row size
row_size = frappe.db.get_row_size("Customer")
print(f"Row size: {row_size} bytes / 65535 max")

# Check utilization %
from frappe.core.doctype.doctype.doctype import get_row_size_utilization
pct = get_row_size_utilization("Customer")
print(f"Row size utilization: {pct}%")
```

### Row Size Management

The MySQL/MariaDB 65KB row size limit applies to VARCHAR columns (Data, Link, Select fields). TEXT fields only use 10 bytes in-row.

```python
# Change Data field to Text to save row space
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

make_property_setter("Customer", "description", "fieldtype", "Text", "Data")
frappe.db.sql("ALTER TABLE `tabCustomer` MODIFY `description` TEXT")
```

**Field type row size impact:**
| Field Type | MySQL Type | In-Row Bytes |
|---|---|---|
| Data, Link, Select | VARCHAR(140) | 140-142 |
| Text, Small Text | TEXT | 10 |
| Long Text | LONGTEXT | 12 |
| Int | INT | 4 |
| Currency, Float | DECIMAL | ~8 |

### Useful SQL Queries

```python
# Get all custom fields for a DocType
frappe.db.sql("""
    SELECT fieldname, label, fieldtype
    FROM `tabCustom Field`
    WHERE dt = 'Customer'
    ORDER BY idx
""", as_dict=True)

# Find documents modified today
frappe.db.sql("""
    SELECT name, modified_by
    FROM `tabSales Order`
    WHERE DATE(modified) = CURDATE()
    ORDER BY modified DESC
""", as_dict=True)

# Get Singles table value
frappe.db.sql("""
    SELECT value FROM `tabSingles`
    WHERE doctype = 'System Settings' AND field = 'country'
""")

# Bulk update with safety
frappe.db.sql("""
    UPDATE `tabCustomer`
    SET customer_group = 'Commercial'
    WHERE customer_group = 'Old Group'
        AND disabled = 0
""")
frappe.db.commit()
```

---

## 5. Bench Commands Reference

```bash
# Site management
bench new-site mysite.local
bench drop-site mysite.local
bench use mysite.local
bench list-sites
bench backup
bench backup-all-sites
bench restore /path/to/backup.sql.gz

# App management
bench get-app erpnext --branch version-16
bench get-app https://github.com/user/app.git
bench install-app appname --site mysite.local
bench uninstall-app appname --site mysite.local
bench remove-app appname

# Development
bench start
bench migrate
bench migrate --skip-failing
bench clear-cache
bench clear-website-cache
bench build
bench build --app myapp
bench watch  # Watch for JS/CSS changes
bench new-app myapp
bench new-doctype "My DocType" --app myapp

# Database
bench console
bench mariadb
bench execute "frappe.db.sql('SELECT 1')"
bench --site mysite run-patch myapp.patches.v1_0.my_patch

# Production
bench setup production frappe-user
bench setup nginx
bench setup supervisor
bench restart
bench update
bench update --reset --apps myapp

# Utilities
bench version
bench doctor
bench set-config key value
bench set-config -g developer_mode true
bench enable-scheduler
bench disable-scheduler
bench trim-tables --dry-run
bench export-fixtures
bench import-doc /path/to/file.json
bench export-doc DocType name
```

---

## 6. Keyboard Shortcuts

### Frappe Desk Shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl+S` | Save current form |
| `Ctrl+Z` | Undo last change |
| `Ctrl+F` | Search in list |
| `Ctrl+G` | Go to module |
| `Ctrl+J` | Jump to document |
| `Ctrl+K` | Open command palette |
| `Ctrl+/` | Toggle sidebar |
| `Alt+Left` | Go back |
| `Alt+Right` | Go forward |
| `Escape` | Close dialog/modal |

### Custom Shortcuts

```javascript
// Register custom shortcut
frappe.ui.keys.add_shortcut({
    shortcut: "ctrl+shift+a",
    action: function() {
        // Your action
        frappe.msgprint(__("Custom shortcut triggered"));
    },
    description: __("My Custom Action"),
    page: "Form",
    ignore_inputs: false,
});

// List all shortcuts
frappe.ui.keys.get_all_shortcuts();
```

---

## 7. Useful Frappe Tools

### frappe.utils

```python
# Date/time
frappe.utils.today()                    # "2024-01-15"
frappe.utils.now()                      # "2024-01-15 10:30:00"
frappe.utils.now_datetime()             # datetime object
frappe.utils.getdate("2024-01-15")      # date object
frappe.utils.add_days("2024-01-15", 7)  # "2024-01-22"
frappe.utils.add_months("2024-01-15", 1)
frappe.utils.date_diff("2024-01-31", "2024-01-01")  # 30
frappe.utils.get_first_day("2024-01-15")  # "2024-01-01"
frappe.utils.get_last_day("2024-01-15")   # "2024-01-31"

# Numbers
frappe.utils.flt(123.456, 2)            # 123.46
frappe.utils.cint("123")               # 123
frappe.utils.cstr(123)                 # "123"
frappe.utils.money_in_words(1500)      # "One Thousand Five Hundred"

# Strings
frappe.utils.strip_html("<b>Hello</b>")  # "Hello"
frappe.utils.truncate("Long text", 10)   # "Long text..."
frappe.utils.to_markdown("<b>Hello</b>") # "**Hello**"

# Validation
frappe.utils.validate_email_address("user@example.com")  # True/False
frappe.utils.validate_url("https://example.com")

# File/path
frappe.utils.get_site_path()
frappe.utils.get_files_path()
frappe.get_site_base_path()
```

### frappe.logger

```python
# Get logger
logger = frappe.logger("myapp", allow_site=True, file_count=50)

# Log levels
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical message")

# With context
logger.info(f"Processing order {order_name} for {customer}")
```

### Email

```python
# Send email
frappe.sendmail(
    recipients=["user@example.com"],
    subject="Subject",
    message="<p>HTML message</p>",
    attachments=[{
        "fname": "report.pdf",
        "fcontent": pdf_content,
    }],
    delayed=False,  # Send immediately
)

# Send using template
frappe.sendmail(
    recipients=["user@example.com"],
    template="my_email_template",
    args={"name": "John", "order": "SO-0001"},
)
```

### Real-time Events

```python
# Server → Client
frappe.publish_realtime(
    event="my_event",
    message={"data": "value"},
    user=frappe.session.user,
    # room="all"  # Broadcast to all
)
```

```javascript
// Client listener
frappe.realtime.on("my_event", function(data) {
    console.log(data);
    frappe.show_alert({ message: data.message, indicator: "green" });
});

// Unsubscribe
frappe.realtime.off("my_event");
```

---

## 8. Common Patterns

### Idempotent Patch

```python
# patches/v2_0/add_default_values.py
import frappe

def execute():
    """Add default values to existing records — safe to run multiple times"""
    frappe.db.sql("""
        UPDATE `tabCustomer`
        SET customer_group = 'Commercial'
        WHERE customer_group IS NULL OR customer_group = ''
    """)
    frappe.db.commit()
```

### Bulk Operation with Progress

```python
def bulk_update_customers():
    customers = frappe.get_all("Customer", pluck="name")
    total = len(customers)

    for i, name in enumerate(customers):
        try:
            doc = frappe.get_doc("Customer", name)
            doc.custom_field = compute_value(doc)
            doc.save(ignore_permissions=True)

            if i % 100 == 0:
                frappe.db.commit()
                print(f"Progress: {i}/{total}")
        except Exception:
            frappe.log_error(f"Failed: {name}", frappe.get_traceback())

    frappe.db.commit()
    print(f"Done: {total} customers updated")
```

### Safe Document Creation

```python
def create_or_update_customer(customer_name, email):
    existing = frappe.db.exists("Customer", {"customer_name": customer_name})

    if existing:
        doc = frappe.get_doc("Customer", existing)
        doc.email_id = email
        doc.save(ignore_permissions=True)
        return doc.name
    else:
        doc = frappe.new_doc("Customer")
        doc.customer_name = customer_name
        doc.email_id = email
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        return doc.name
```

### Consistent API Response

```python
@frappe.whitelist()
def my_api_endpoint(param1, param2=None):
    try:
        result = do_something(param1, param2)
        return {
            "success": True,
            "data": result,
            "message": "Operation completed",
        }
    except frappe.ValidationError as e:
        return {"success": False, "error": str(e), "type": "validation"}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "API Error")
        frappe.throw(_("An unexpected error occurred"))
```

---

## 9. Debugging Tips

```python
# Print to bench console
print("Debug:", frappe.as_json(data))

# Log to error log
frappe.log_error("Debug Info", frappe.as_json(data))

# Check what's in frappe.local
print(dir(frappe.local))

# Inspect document
doc = frappe.get_doc("Sales Order", "SO-0001")
print(frappe.as_json(doc.as_dict()))

# Check permissions
print(frappe.has_permission("Sales Order", "read", "SO-0001"))
print(frappe.get_roles())

# Check hooks
print(frappe.get_hooks("doc_events"))

# Reload DocType meta
frappe.clear_cache(doctype="Sales Order")
meta = frappe.get_meta("Sales Order", cached=False)
```

```javascript
// Browser console debugging
console.log(frm.doc);
console.log(frappe.boot);
console.log(frappe.session);
console.log(frappe.defaults.get_defaults());

// Check form state
console.log(frm.is_new());
console.log(frm.is_dirty());
console.log(frm.doc.docstatus);

// Inspect field
console.log(frm.get_field("customer"));
console.log(frm.fields_dict["customer"]);
```


---

## 📌 Addendum: Interview Questions, API Deep Dive, and Advanced Reference

### Frappe/ERPNext Interview Questions

#### Junior Level

**Q: What is the Frappe Framework?**
A: A full-stack, meta-driven web framework built on Python (backend) and JavaScript (frontend). Unlike Django/Flask, it's metadata-first — you define application structure through DocTypes rather than writing explicit models, views, and controllers. Every DocType automatically gets REST APIs, auto-generated UI, role-based permissions, and workflows.

**Q: What is the difference between a DocType and a Document?**
A: DocType = the schema/blueprint (like a class definition). Document = an instance of a DocType (like an object instance). DocType metadata is stored in `tabDocType`; Documents are stored in `tab{DocType Name}`.

**Q: What is the Singles table?**
A: Single DocTypes (like System Settings) store their data in `tabSingles` as key-value pairs instead of having their own table. Access with `frappe.db.get_single_value("System Settings", "field_name")`.

**Q: What are Fixtures?**
A: Predefined data records exported from a site and bundled with an app. They enable version-controlled configuration management. Common fixture types: Custom Fields, Property Setters, Client Scripts, Print Formats, Roles, Workflows.

```python
# hooks.py
fixtures = [
    "Custom Field",
    "Property Setter",
    {"dt": "Role", "filters": [["name", "in", ["Custom Role 1"]]]},
]
```

```bash
bench export-fixtures  # Creates JSON files in fixtures/
```

**Q: What is a Property Setter?**
A: A DocType that overrides properties of standard DocTypes and fields without modifying core code. Stored in `tabProperty Setter`, applied at runtime via `apply_property_setters()`. Survives framework updates.

Common properties: `reqd`, `hidden`, `read_only`, `label`, `default`, `options`, `allow_on_submit`.

#### Senior Level

**Q: What is the difference between Redis cache and local cache in Frappe?**
A: Redis cache is shared across all workers and processes (persistent across requests). Local cache is per-process/per-request (thread-local, faster but not shared). Use Redis for data that needs to be shared; use local cache for request-scoped data.

**Q: What is the architecture of Frappe?**
A: Frappe follows a meta-driven MVT-like pattern:
- Model: DocType definitions + Python controllers
- View: Auto-generated forms/lists + Jinja templates
- Controller: Python controller classes + hooks

More accurately described as **meta-driven MVC** — the metadata (DocType JSON) drives everything.

**Q: Is Frappe MVC or MVT?**
A: Neither purely. It's meta-driven. The DocType definition acts as both model and view configuration. The Python controller is the controller. Jinja templates handle web views. The framework auto-generates most of the view layer from metadata.

**Q: How does Frappe handle database transactions?**
A: Frappe wraps every request in a transaction. On success, it commits. On any unhandled exception, it rolls back. You can manually commit with `frappe.db.commit()` for long-running operations. Use `frappe.db.rollback()` to explicitly rollback.

**Q: How does Frappe implement multi-tenancy?**
A: Each site gets its own database. The `frappe.local.site` variable determines which database to connect to. Bench manages multiple sites, each with its own `site_config.json`. A single Frappe process can serve multiple sites.

**Q: What are anti-patterns in Frappe?**
A: 
- Modifying core files directly (breaks on upgrade)
- Using `frappe.db.sql()` when ORM methods exist (bypasses permissions)
- Not using `frappe.db.commit()` in long loops (memory issues)
- Calling `frappe.get_doc()` in a loop without caching (N+1 queries)
- Using `ignore_permissions=True` in user-facing code (security risk)

**Q: How to move customizations between sites without manual migration?**
A: Use Fixtures. Export with `bench export-fixtures`, commit to git, install on target site with `bench install-app` or `bench migrate`.

**Q: Why does changing a field type to Float cause errors?**
A: Frappe performs type casting at the ORM level. If existing records contain `""` (empty string) and the field is now `Float`, Python's `float("")` raises `ValueError`. Fix: write a `[pre_model_sync]` patch to convert empty strings to `0` before changing the field type.

**Q: What are Web Forms in Frappe?**
A: Public-facing forms that allow non-logged-in users (or users without desk access) to submit data. Built on top of DocTypes, they generate a web page with a form that creates documents on submission.

**Q: What are Server Scripts in Frappe?**
A: Python scripts stored in the database (not files) that can be attached to document events or API endpoints. Useful for customizations that don't require a full custom app. Managed via the Server Script DocType.

### Frappe API — Complete Reference

#### Built-in Client Methods

```python
# frappe.client module (accessible via /api/method/frappe.client.*)
frappe.client.get_list(doctype, fields, filters, limit_start, limit_page_length)
frappe.client.get(doctype, name)
frappe.client.get_value(doctype, filters, fieldname)
frappe.client.insert(doc)
frappe.client.save(doc)
frappe.client.delete(doctype, name)
frappe.client.submit(doc)
frappe.client.cancel(doctype, name)
```

#### Response Format Comparison

**V1:**
```json
{"message": <data>}
```

**V2:**
```json
{"data": <data>, "message_log": []}
```

**Error V1:**
```json
{"exc_type": "ValidationError", "exception": "...traceback..."}
```

**Error V2:**
```json
{"errors": [{"type": "ValidationError", "message": "..."}]}
```

#### Calling DocType Methods via Postman

```http
POST /api/method/run_doc_method
Content-Type: application/json
Authorization: token api_key:api_secret

{
    "method": "calculate_tax",
    "dt": "Sales Invoice",
    "dn": "SI-2024-00001",
    "args": {"tax_rate": 0.1}
}
```

### Decorators in Frappe

#### `@frappe.whitelist()`

Registers a Python function as an HTTP endpoint. Without this decorator, the function cannot be called from the client.

```python
@frappe.whitelist()
def my_function(param1, param2=None):
    return {"result": param1}

# Options:
@frappe.whitelist(allow_guest=True)   # No authentication required
@frappe.whitelist(methods=["POST"])   # Restrict HTTP methods
```

#### `@property` in DocType Controllers

```python
class SalesOrder(Document):
    @property
    def total_items(self):
        """Computed property — not stored in DB"""
        return len(self.items)
    
    @property
    def is_overdue(self):
        return self.delivery_date < frappe.utils.today() and self.docstatus == 1
```

Properties are computed on access, not stored. Useful for derived values that don't need persistence.

#### `@frappe.rate_limit()`

```python
@frappe.whitelist(allow_guest=True)
@frappe.rate_limit(limit=10, seconds=60)
def public_endpoint():
    pass
```

### Database Table Trimming

Over time, DocType fields get removed but their database columns remain (Frappe never drops columns automatically for safety). Use `trim-tables` to clean up orphan columns.

```bash
# Preview what would be removed (safe — no changes)
bench --site mysite trim-tables --dry-run

# Execute trimming (creates backup first)
bench --site mysite trim-tables

# Skip backup (not recommended)
bench --site mysite trim-tables --no-backup
```

```python
from frappe.model.meta import trim_table, trim_tables

# Check orphans for one DocType
orphans = trim_table("Customer", dry_run=True)
print(f"Orphan columns: {orphans}")

# Remove orphans
trim_table("Customer", dry_run=False)

# Trim all tables
trim_tables(dry_run=False)
```

**When to use:** After removing fields from DocTypes, after major ERPNext upgrades, when hitting the MySQL 65KB row size limit.

**Row size limit:** MySQL/MariaDB has a 65KB per-row limit for VARCHAR columns. `Data`, `Link`, and `Select` fields use VARCHAR(140) which counts toward this limit. `Text` fields only use 10 bytes in-row.

```python
# Check row size utilization
from frappe.core.doctype.doctype.doctype import get_row_size_utilization
pct = get_row_size_utilization("Customer")
print(f"Row size utilization: {pct}%")
```

### Frappe Architecture Summary

```
Browser (JavaScript)
    ↓ frappe.call() / REST API
Nginx (reverse proxy)
    ↓
Gunicorn (WSGI workers) ← Production
Werkzeug (dev server)   ← Development
    ↓
Frappe WSGI App (frappe/app.py)
    ↓
Request Handler → Permission Check → Controller → Database
    ↓
MariaDB (per-site database)
    ↑
Redis Cache (shared) + Redis Queue (background jobs)
    ↑
Background Workers (RQ) + Scheduler
    ↑
Socket.IO (Node.js) ← Real-time events
```


---

## 10. Developer Mode vs Production Mode

### What `developer_mode` Controls

`developer_mode` is a setting in `sites/common_site_config.json` or `sites/[site]/site_config.json`. It has nothing to do with how you run Frappe (`bench start` vs nginx/supervisor) — it only controls behavior.

```json
{ "developer_mode": 1 }
```

| Feature | Developer Mode | Production Mode |
|---|---|---|
| Edit standard DocTypes | ✅ Allowed | ❌ Read-only |
| Auto-export to JSON files | ✅ Yes | ❌ No |
| Full error tracebacks | ✅ Shown | ❌ Hidden |
| Asset minification | ❌ Disabled | ✅ Enabled |
| File watching / live reload | ✅ Available | ❌ Disabled |
| Network always online | ✅ Yes | ❌ Real check |
| Dormant site check | ❌ Disabled | ✅ Enabled |

### Enable/Disable

```bash
# Enable for all sites
bench set-config developer_mode 1 -g

# Enable for specific site
bench --site mysite set-config developer_mode 1

# Disable (production)
bench --site mysite set-config developer_mode 0
```

### Running Frappe: Two Ways

- `bench start` — for local development. Easy to restart, supports live reload.
- `nginx + supervisor` — for production. Runs 24/7, handles real traffic.

You can run `developer_mode = 1` with nginx/supervisor on a dev server, but never do this on a live public site.

**Simple rule:**
- Develop locally → `bench start` + `developer_mode = 1`
- Deploy to production → nginx/supervisor + `developer_mode = 0`

---

## 11. Standard vs Custom in Frappe

### The Core Distinction

- **Standard** = lives in source code (app files). Visible to all sites that install the app.
- **Custom** = lives in the database of a specific site. Only that site sees it.

### From the Apps Perspective

Frappe is the standard core. When you run `bench new-app`, you create a custom app. ERPNext is "standard" from your custom app's perspective (if you depend on it), but "custom" from Frappe's perspective.

### From the Sites Perspective

Each site is a separate client with its own database. Anything you create on a site (DocType, Report, Web Form, Custom Field) is **custom** by default — stored only in that site's database.

### Making Something Standard (Source Code)

To make a customization visible to all sites:

1. Enable **Developer Mode**
2. Log in as **Administrator**
3. Depending on the object:
   - **DocType** → uncheck the "Custom?" checkbox
   - **Report** → set "Is Standard?" to Yes
   - **Web Form** → set "Is Standard?" to Yes
   - **Web Pages / Custom Fields** → export as **Fixtures** (JSON files), applied via `bench migrate`

### Quick Reference

```
Standard → Source code → All sites see it
Custom   → Database    → Only that site sees it
```

---

## 12. Quick Testing Tips

### Test Translations

```bash
bench --site mysite console
```

```python
frappe.lang = "ar"
frappe.local.lang = "ar"
frappe._("hello")  # Returns Arabic translation if it exists
```

### Test Patches

```bash
bench execute myapp.patches.v1_0.my_patch.execute
```

The path is the same as what you'd put in `patches.txt`.

### Test Scheduled Events

```bash
bench trigger-scheduler-event myapp.scheduler.tasks.daily_backup
```

### Test Notifications

```python
# In bench console
from frappe.email.doctype.notification.notification import trigger_daily_alerts
trigger_daily_alerts()
```

### Run Tests for a DocType

```bash
bench --site mysite run-tests --doctype "Sales Order" --skip-test-records
bench --site mysite run-tests --doctype "Sales Order" --test test_submit --skip-test-records
```

### View Background Worker Output

```bash
bench worker --queue long
bench worker --queue short
bench worker --queue default
```

### Render Email Queue Message

```python
# In bench console
import email
from email import policy

raw = frappe.db.get_value("Email Queue", "your-email-queue-name", "message")
msg = email.message_from_string(raw, policy=policy.default)
print("Subject:", msg["subject"])
for part in msg.walk():
    if part.get_content_type() == "text/html":
        print(part.get_content())
```

---

## 13. Useful Built-in Tools

### Permission Inspector

URL: `/app/permission-inspector`

Debug why a user has or doesn't have a specific permission. Shows all roles, all matching rules, and why access was granted or denied.

### Role Permission Manager

URL: `/app/permission-manager`

Review and manage permissions for a role on a DocType. Add, modify, or remove permission rules.

### System Console

URL: `/app/system-console`

Run Python code or SQL queries directly from the browser. Check the "Commit" checkbox to persist database changes; otherwise changes are rolled back.

### Impersonate User

URL: `/app/user/<user-name>` → click "Impersonate"

Lets an admin log in as another user without knowing their password. Useful for testing. The impersonated user is notified.

### Permitted Documents For User

Report → "Permitted Documents For User"

Shows only the documents a specific user can access. Useful for testing User Permissions configuration.

### Commit App (Third-Party)

```bash
bench get-app --branch main The-commit-company/commit
bench --site mysite install-app commit
```

Then visit `/commit`. Provides:
- API explorer — lists and lets you test every API in your system
- ERD diagram — draws your database schema
- Bench commands cheat sheet
