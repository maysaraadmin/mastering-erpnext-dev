# Chapter 27: Real-Time Updates, UI Patterns, and Form Interactions

## Real-Time Updates with SocketIO

Frappe uses SocketIO (WebSocket protocol) to push updates from the server to all connected clients without requiring a page refresh.

### Architecture

```
Client ↔ SocketIO Server ↔ Redis Queue ↔ Web Server
```

The Python web server publishes events to Redis Queue. The Node.js SocketIO server subscribes to Redis and pushes events to clients in real time.

### Server-Side: Publishing Events

```python
@frappe.whitelist()
def refresh_status(doc_type, doc_name):
    """Publish a real-time event to all connected clients."""
    event_name = f"refresh_{doc_type.lower()}"
    frappe.publish_realtime(
        event=event_name,
        message={
            "message": f"{doc_type} status refreshed!",
            "doc_name": doc_name
        }
    )
```

### Client-Side: Listening for Events

```javascript
// Listen for real-time events
frappe.realtime.on("refresh_invoice", function(data) {
    // Only update if this is the document currently open
    if (cur_frm.doc.name === data.doc_name) {
        cur_frm.reload_doc();
    }
});
```

### Triggering Events on Document Save

```javascript
frappe.ui.form.on('Sales Invoice', {
    after_save: function(frm) {
        frappe.call({
            method: 'your_app.utils.refresh_status',
            args: {
                doc_type: frm.doctype,
                doc_name: frm.docname
            }
        });
    }
});
```

### Common Real-Time Use Cases

- **Collaborative workflows**: Notify team members about updates to shared tasks
- **Status tracking**: Automatically update UI when document status changes
- **Notifications**: Alert users about new messages, approvals, or system events
- **Progress indicators**: Show background job progress in real time

---

## Form Guard: Preventing Data Loss

Protect users from accidentally losing unsaved changes.

### Implementation

```javascript
// your_app/public/js/form_guard.js
(function() {
    'use strict';
    
    function attachUnloadGuard(frm) {
        clearUnloadGuard();
        window.onbeforeunload = function(e) {
            try {
                if (frm && frm.is_dirty && frm.is_dirty()) {
                    e.preventDefault();
                    e.returnValue = "";
                    return "";
                }
            } catch (err) {
                console.warn("Form guard error:", err);
            }
        };
    }
    
    function clearUnloadGuard() {
        if (window.onbeforeunload) {
            window.onbeforeunload = null;
        }
    }
    
    // Apply to ALL DocTypes using wildcard
    frappe.ui.form.on('*', {
        onload(frm) {
            clearUnloadGuard();  // Clear stale guard from previous form
        },
        refresh(frm) {
            attachUnloadGuard(frm);  // Attach for current form
        },
        after_save(frm) { clearUnloadGuard(); },
        on_submit(frm) { clearUnloadGuard(); },
        on_cancel(frm) { clearUnloadGuard(); }
    });
    
    // Logout confirmation
    function setupLogoutConfirmation() {
        const originalLogout = frappe.ui.toolbar.logout;
        frappe.ui.toolbar.logout = function() {
            frappe.confirm(
                __('Are you sure you want to logout?'),
                () => { window.location.href = '/?cmd=logout'; },
                () => { frappe.show_alert(__('Logout cancelled'), 'info'); }
            );
        };
    }
    
    frappe.ready(() => { setupLogoutConfirmation(); });
})();
```

### Register in hooks.py

```python
app_include_js = [
    "/assets/your_app/js/form_guard.js"
]
```

### Key Points

- `frappe.ui.form.on('*', ...)` applies to ALL DocTypes — it appends to the event pipeline, not overrides
- Clear the guard in `onload` to prevent stale warnings when switching forms
- Attach in `refresh` because it runs whenever the form is shown
- Modern browsers ignore custom text for `beforeunload` — they show a generic message (browser security feature)

---

## Custom Buttons

### Basic Syntax

```javascript
frm.add_custom_button(label, callback, group);
```

### Examples

```javascript
frappe.ui.form.on("Lead", {
    refresh: function(frm) {
        // Simple button
        if (!frm.is_new() && !frm.doc.is_customer) {
            frm.add_custom_button(__("Create Customer"), function() {
                frappe.model.open_mapped_doc({
                    method: "your_app.crm.lead.make_customer",
                    frm: frm
                });
            }, __("Create"));
        }
        
        // Multiple buttons in groups
        frm.add_custom_button(__("Customer"), fn, __("Create"));
        frm.add_custom_button(__("Opportunity"), fn, __("Create"));
        frm.add_custom_button(__("Gantt Chart"), fn, __("View"));
        
        // Button with confirmation
        frm.add_custom_button(__("Delete"), function() {
            frappe.confirm(__("Are you sure?"), function() {
                // Delete logic
            });
        });
    }
});
```

### `frm.custom_make_buttons`

Maps DocType names to custom button labels for the "Make" button:

```javascript
frappe.ui.form.on("Material Request", {
    setup: function(frm) {
        frm.custom_make_buttons = {
            "Stock Entry": "Issue Material",
            "Purchase Order": "Purchase Order",
            "Work Order": "Work Order",
        };
    },
    
    refresh: function(frm) {
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button(__("Issue Material"), function() {
                frm.events.make_stock_entry(frm);
            }, __("Create"));
        }
    }
});
```

Priority order when `make_new()` is called:
1. `frm.make_methods[doctype]` (highest)
2. `frm.custom_make_buttons[doctype]` (medium)
3. Default behavior (lowest)

---

## Dialogs

### Basic Dialog

```javascript
const dialog = new frappe.ui.Dialog({
    title: __("Select Customer"),
    fields: [
        {
            fieldtype: "Link",
            label: __("Customer"),
            options: "Customer",
            fieldname: "customer",
            reqd: 1
        }
    ],
    primary_action: function({ customer }) {
        // Use customer value
        dialog.hide();
    },
    primary_action_label: __("Select")
});

dialog.show();
```

### Dialog with Multiple Fields

```javascript
const dialog = new frappe.ui.Dialog({
    title: __("Create Link"),
    fields: [
        {
            fieldtype: "Link",
            label: __("Customer"),
            options: "Customer",
            fieldname: "customer",
            reqd: 1
        },
        { fieldtype: "Column Break" },
        {
            fieldtype: "Date",
            label: __("Date"),
            fieldname: "date",
            default: frappe.datetime.get_today()
        }
    ],
    primary_action: function(values) {
        frappe.call({
            method: "create_link",
            args: values,
            callback: function() { dialog.hide(); }
        });
    }
});

dialog.show();
```

### Dialog with Table

```javascript
const dialog = new frappe.ui.Dialog({
    title: __("Select Items"),
    fields: [
        {
            fieldname: "items",
            fieldtype: "Table",
            fields: [
                { fieldtype: "Check", fieldname: "select", in_list_view: 1 },
                { fieldtype: "Link", fieldname: "item_code", options: "Item", in_list_view: 1 },
                { fieldtype: "Float", fieldname: "qty", in_list_view: 1 }
            ],
            data: items_data
        }
    ],
    primary_action: function(values) {
        const selected = values.items.filter(item => item.select);
        // Process selected items
        dialog.hide();
    }
});

dialog.show();
```

### `frappe.prompt` (Quick Input Dialog)

```javascript
frappe.prompt([
    {
        fieldname: "new_name",
        label: __("New Name"),
        fieldtype: "Data",
        reqd: 1
    }
], function(values) {
    frappe.call({
        method: "rename_document",
        args: { old_name: frm.doc.name, new_name: values.new_name },
        callback: function() { frm.reload_doc(); }
    });
}, __("Rename Document"), __("Rename"));
```

### Dialog Best Practices

- Mark required fields with `reqd: 1`
- Provide default values where sensible
- Always call `dialog.hide()` after successful action
- Handle errors in the callback
- Use `__()` for all user-facing strings (translation)

---

## Notifications

Frappe Notifications are automated messaging rules that send emails, SMS, Slack messages, or system notifications when document events occur.

### Creating a Notification

Navigate to: Setup → Email → Notification → New

Required fields:
- Document Type
- Event (New, Save, Submit, Cancel, Value Change, Days Before, Days After, Method)
- Channel (Email, SMS, Slack, System Notification)
- Subject
- Message (Jinja2 template)
- Recipients

### Events

| Event | Trigger | Use Case |
|-------|---------|----------|
| New | after_insert | Welcome emails, confirmations |
| Save | on_update | General updates |
| Submit | on_submit | Submission confirmations |
| Cancel | on_cancel | Cancellation notices |
| Value Change | on_change | Status change alerts |
| Days Before | Scheduler (daily) | Reminders |
| Days After | Scheduler (daily) | Follow-ups |
| Method | Method execution | Custom triggers |

### Conditions

```python
# Simple field comparison
doc.status == "Open"

# Multiple conditions
doc.status == "Open" and doc.priority == "High"

# Date comparison
doc.due_date == nowdate()

# List check
doc.status in ["Open", "Pending", "In Progress"]

# Child table check
len(doc.items) > 0
```

### Jinja Templates

```jinja
{# Subject #}
Order {{ doc.name }} - {{ doc.status }}

{# Message body #}
<h3>Order Notification</h3>
<p>Dear Customer,</p>
<p>Your order <strong>{{ doc.name }}</strong> has been {{ doc.status }}.</p>

<h4>Order Details:</h4>
<ul>
    <li>Customer: {{ doc.customer }}</li>
    <li>Total: {{ doc.grand_total }}</li>
    <li>Date: {{ doc.transaction_date }}</li>
</ul>

{% if doc.status == "Open" and doc.priority == "High" %}
    <p style="color: red;">URGENT: High priority order!</p>
{% endif %}

{% for item in doc.items %}
    <li>{{ item.item_code }} - {{ item.quantity }} x {{ item.rate }}</li>
{% endfor %}

{% if comments %}
    <p>Last comment: {{ comments[-1].comment }} by {{ comments[-1].by }}</p>
{% endif %}
```

### Notification Lifecycle

Notifications are **skipped** when:
- `frappe.flags.in_import` is True and `frappe.flags.mute_emails` is True
- `frappe.flags.in_patch` is True
- `frappe.flags.in_install` is True
- Notification is disabled
- Condition evaluates to False
- For Value Change: value didn't actually change
- Notification already executed in this transaction

### Set Property After Alert

You can update a field after the notification is sent:

```
Set Property After Alert: notification_sent
Value: 1
```

This sets `doc.notification_sent = 1` after the notification fires, preventing duplicate sends.

---

## Common UI Patterns

### Reload document after action

```javascript
frappe.call({
    method: "your_app.module.do_something",
    args: { name: frm.doc.name },
    callback: function(r) {
        frm.reload_doc();
    }
});
```

### Show alert after action

```javascript
frappe.show_alert({
    message: __("Action completed successfully"),
    indicator: "green"
}, 5);
```

### Navigate to another form

```javascript
frappe.set_route("Form", "Customer", "CUST-001");
frappe.set_route("List", "User");
```

### Refresh a specific field

```javascript
frm.set_value("status", "Active");
frm.refresh_field("status");
```

### Disable/enable a field

```javascript
frm.set_df_property("field_name", "read_only", 1);
frm.set_df_property("field_name", "read_only", 0);
```


---

## 📌 Addendum: Adding Comments Programmatically

### `doc.add_comment()`

```python
doc = frappe.get_doc("Sales Order", "SO-0001")
comment = doc.add_comment("Comment", "Order reviewed and approved")
```

### Comment Types

| Type | Use Case |
|---|---|
| `Comment` | User notes, discussions |
| `Info` | System/integration logs |
| `Workflow` | Workflow state changes |
| `Assigned` | Task assignments |
| `Assignment Completed` | Assignment completion |
| `Attachment` | File uploads |
| `Attachment Removed` | File deletions |
| `Shared` / `Unshared` | Document sharing |
| `Bot` | Automated messages |
| `Edit` | Manual edit logs |
| `Created` / `Updated` / `Submitted` / `Cancelled` | Lifecycle events |

### Full Signature

```python
doc.add_comment(
    comment_type="Comment",   # Default
    text=None,                # Comment content (defaults to comment_type)
    comment_email=None,       # Defaults to frappe.session.user
    comment_by=None           # Display name
)
```

### Mentioning Users

```python
comment_text = '''
<span class="mention" data-id="john@example.com" data-value="John Doe" data-denotation-char="@">@John Doe</span>
Please review this order.
'''
doc.add_comment("Comment", comment_text)
```

Mentioned users receive a notification automatically.

### Practical Examples

```python
# Log integration activity
def sync_with_external_system(self):
    try:
        response = make_api_call(self.name)
        self.add_comment("Info", f"Synced successfully. Ref: {response.get('id')}")
    except Exception as e:
        self.add_comment("Info", f"Sync failed: {str(e)}")

# Log workflow change
def on_update(self):
    if self.has_value_changed("workflow_state"):
        old = self.get_doc_before_save().workflow_state
        self.add_comment("Workflow", f"State changed: {old} → {self.workflow_state}")

# Add comment as system user
doc.add_comment(
    comment_type="Info",
    text="Processed by background job",
    comment_email="system@example.com",
    comment_by="System"
)
```

### Retrieving Comments

```python
# Get all comments for a document
comments = frappe.get_all(
    "Comment",
    filters={"reference_doctype": "Sales Order", "reference_name": "SO-0001"},
    fields=["content", "comment_type", "comment_email", "creation"],
    order_by="creation desc"
)

# Get from cache (faster, last 100 only)
import json
doc = frappe.get_doc("Sales Order", "SO-0001")
cached = json.loads(doc.get("_comments") or "[]")
```

### From Client Side

```javascript
frappe.call({
    method: "frappe.desk.form.utils.add_comment",
    args: {
        reference_doctype: frm.doctype,
        reference_name: frm.docname,
        content: "Order reviewed",
        comment_email: frappe.session.user,
        comment_by: frappe.session.user_fullname,
    },
    callback: () => frm.reload_doc()
});
```

### Storage

Comments are stored in the `Comment` DocType. The parent document's `_comments` field caches the last 100 comments (first 100 chars each) for fast display. Real-time updates are pushed via Socket.IO.
