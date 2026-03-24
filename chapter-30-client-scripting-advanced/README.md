# Chapter 30: Advanced Client-Side Scripting

## Overview

Client scripts in Frappe run in the browser and control form behavior, UI interactions, and user experience. This chapter covers advanced patterns including child table scripting, dynamic UI, custom dialogs, form overrides, and the full client-side API.

---

## 1. Form Events Reference

```javascript
// All standard form events
frappe.ui.form.on("Sales Order", {
    // Triggered when form is first loaded
    onload: function(frm) {
        frm.set_query("customer", function() {
            return { filters: { disabled: 0 } };
        });
    },

    // Triggered when form is refreshed (after save, load, etc.)
    refresh: function(frm) {
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button(__("Create Invoice"), function() {
                frappe.model.open_mapped_doc({
                    method: "erpnext.selling.doctype.sales_order.sales_order.make_sales_invoice",
                    frm: frm,
                });
            }, __("Create"));
        }
    },

    // Field change events
    customer: function(frm) {
        if (frm.doc.customer) {
            frappe.db.get_value("Customer", frm.doc.customer, "credit_limit", (r) => {
                frm.set_value("credit_limit", r.credit_limit);
            });
        }
    },

    // Before save
    before_save: function(frm) {
        if (!frm.doc.delivery_date) {
            frappe.throw(__("Delivery date is required"));
        }
    },

    // After save
    after_save: function(frm) {
        frappe.show_alert({ message: __("Saved"), indicator: "green" });
    },

    // Before submit
    before_submit: function(frm) {
        return frappe.confirm(__("Are you sure you want to submit?"));
    },

    // On submit
    on_submit: function(frm) {
        frappe.msgprint(__("Order submitted successfully"));
    },

    // Before cancel
    before_cancel: function(frm) {
        return frappe.confirm(__("Cancel this order?"));
    },

    // Timeline refresh
    timeline_refresh: function(frm) {
        // Custom timeline actions
    },
});
```

---

## 2. Dynamic UI Control

```javascript
frappe.ui.form.on("Sales Order", {
    refresh: function(frm) {
        // Show/hide fields
        frm.toggle_display("discount_amount", frm.doc.apply_discount_on === "Grand Total");

        // Enable/disable fields
        frm.toggle_enable("customer", frm.doc.docstatus === 0);

        // Make field mandatory dynamically
        frm.toggle_reqd("delivery_date", frm.doc.order_type === "Sales");

        // Set field value
        frm.set_value("status", "Draft");

        // Set multiple values
        frm.set_value({
            "status": "Draft",
            "delivery_date": frappe.datetime.add_days(frappe.datetime.get_today(), 7),
        });

        // Scroll to field
        frm.scroll_to_field("grand_total");

        // Focus on field
        frm.get_field("customer").input.focus();
    },

    order_type: function(frm) {
        // Conditional field visibility
        const is_maintenance = frm.doc.order_type === "Maintenance";
        frm.toggle_display(["maintenance_date", "maintenance_schedule"], is_maintenance);
        frm.toggle_reqd("maintenance_date", is_maintenance);
    },
});
```

---

## 3. Field Validation

```javascript
frappe.ui.form.on("Sales Order", {
    grand_total: function(frm) {
        if (frm.doc.grand_total < 0) {
            frappe.msgprint({
                title: __("Invalid Amount"),
                message: __("Grand total cannot be negative"),
                indicator: "red",
            });
            frm.set_value("grand_total", 0);
        }
    },

    delivery_date: function(frm) {
        if (frm.doc.delivery_date < frm.doc.transaction_date) {
            frappe.msgprint(__("Delivery date cannot be before order date"));
            frm.set_value("delivery_date", frm.doc.transaction_date);
        }
    },

    customer: function(frm) {
        if (!frm.doc.customer) return;

        // Async validation
        frappe.call({
            method: "frappe.client.get_value",
            args: {
                doctype: "Customer",
                filters: { name: frm.doc.customer },
                fieldname: ["disabled", "credit_limit"],
            },
            callback: function(r) {
                if (r.message && r.message.disabled) {
                    frappe.msgprint(__("This customer is disabled"));
                    frm.set_value("customer", "");
                }
            },
        });
    },
});
```

---

## 4. API Calls from Client Scripts

```javascript
// Standard frappe.call
frappe.call({
    method: "myapp.api.get_customer_data",
    args: { customer: frm.doc.customer },
    freeze: true,
    freeze_message: __("Loading..."),
    callback: function(r) {
        if (r.message) {
            frm.set_value("credit_limit", r.message.credit_limit);
        }
    },
    error: function(r) {
        frappe.msgprint(__("Failed to load customer data"));
    },
});

// Promise-based with frappe.xcall
async function loadCustomerData(customer) {
    try {
        const data = await frappe.xcall("myapp.api.get_customer_data", { customer });
        return data;
    } catch (err) {
        frappe.msgprint(__("Error: {0}", [err.message]));
    }
}

// frappe.db shortcuts
frappe.db.get_value("Customer", frm.doc.customer, "credit_limit", (r) => {
    console.log(r.credit_limit);
});

frappe.db.get_doc("Customer", frm.doc.customer).then((doc) => {
    console.log(doc.customer_name);
});

frappe.db.get_list("Sales Order", {
    filters: { customer: frm.doc.customer, docstatus: 1 },
    fields: ["name", "grand_total"],
    limit: 10,
}).then((orders) => {
    console.log(orders);
});

frappe.db.exists("Customer", frm.doc.customer).then((exists) => {
    if (!exists) frappe.throw(__("Customer not found"));
});
```

---

## 5. Custom Dialogs

```javascript
// Simple confirm dialog
frappe.confirm(
    __("Are you sure you want to proceed?"),
    function() {
        // On Yes
        frappe.msgprint(__("Confirmed!"));
    },
    function() {
        // On No (optional)
        frappe.msgprint(__("Cancelled"));
    }
);

// Prompt dialog (single input)
frappe.prompt(
    { label: __("Reason"), fieldtype: "Small Text", reqd: 1 },
    function(values) {
        console.log(values.value);
    },
    __("Enter Reason"),
    __("Submit")
);

// Full dialog with multiple fields
let d = new frappe.ui.Dialog({
    title: __("Create Delivery"),
    fields: [
        {
            label: __("Delivery Date"),
            fieldname: "delivery_date",
            fieldtype: "Date",
            reqd: 1,
            default: frappe.datetime.add_days(frappe.datetime.get_today(), 3),
        },
        {
            label: __("Warehouse"),
            fieldname: "warehouse",
            fieldtype: "Link",
            options: "Warehouse",
            reqd: 1,
        },
        { fieldtype: "Column Break" },
        {
            label: __("Notes"),
            fieldname: "notes",
            fieldtype: "Small Text",
        },
    ],
    primary_action_label: __("Create"),
    primary_action: function(values) {
        frappe.call({
            method: "myapp.api.create_delivery",
            args: {
                sales_order: frm.doc.name,
                delivery_date: values.delivery_date,
                warehouse: values.warehouse,
                notes: values.notes,
            },
            callback: function(r) {
                if (r.message) {
                    frappe.msgprint(__("Delivery {0} created", [r.message]));
                    d.hide();
                    frm.reload_doc();
                }
            },
        });
    },
});

d.show();

// Access dialog fields
d.set_value("warehouse", "Main Warehouse");
let warehouse = d.get_value("warehouse");
```

---

## 6. Child Table (Child DocType) Scripting

### Python/JS Interaction

```javascript
// Listen to child table events
frappe.ui.form.on("Sales Order Item", {
    // When a row is added
    items_add: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        row.warehouse = frm.doc.set_warehouse;
        frm.refresh_field("items");
    },

    // When a row is removed
    items_remove: function(frm, cdt, cdn) {
        frm.trigger("calculate_totals");
    },

    // Field change in child row
    item_code: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (!row.item_code) return;

        frappe.db.get_value("Item", row.item_code, ["item_name", "description", "stock_uom"], (r) => {
            frappe.model.set_value(cdt, cdn, {
                item_name: r.item_name,
                description: r.description,
                uom: r.stock_uom,
            });
        });
    },

    qty: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        frappe.model.set_value(cdt, cdn, "amount", row.qty * row.rate);
        frm.trigger("calculate_totals");
    },

    rate: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        frappe.model.set_value(cdt, cdn, "amount", row.qty * row.rate);
    },
});
```

### Child Table Philosophy

```javascript
// CDT = Child DocType name (e.g., "Sales Order Item")
// CDN = Child Document Name (unique row identifier)

// Get row data
let row = locals[cdt][cdn];

// Set value in child row
frappe.model.set_value(cdt, cdn, "fieldname", value);

// Set multiple values
frappe.model.set_value(cdt, cdn, {
    qty: 10,
    rate: 100,
    amount: 1000,
});

// Add a new row
let new_row = frm.add_child("items");
new_row.item_code = "ITEM-001";
new_row.qty = 5;
frm.refresh_field("items");

// Remove a row
frm.get_field("items").grid.get_row(cdn).remove();

// Get all rows
let all_rows = frm.doc.items;

// Loop through rows
frm.doc.items.forEach((row) => {
    console.log(row.item_code, row.qty);
});

// Filter rows
let filtered = frm.doc.items.filter((row) => row.qty > 0);
```

---

## 7. List View Customization

```javascript
// myapp/public/js/sales_order_list.js
frappe.listview_settings["Sales Order"] = {
    // Add indicator colors
    get_indicator: function(doc) {
        if (doc.status === "Completed") return [__("Completed"), "green", "status,=,Completed"];
        if (doc.status === "Cancelled") return [__("Cancelled"), "red", "status,=,Cancelled"];
        if (doc.status === "Draft") return [__("Draft"), "orange", "status,=,Draft"];
        return [__(doc.status), "blue"];
    },

    // Add custom buttons to list
    onload: function(listview) {
        listview.page.add_action_item(__("Bulk Approve"), function() {
            let selected = listview.get_checked_items();
            if (!selected.length) {
                frappe.msgprint(__("Please select at least one order"));
                return;
            }
            frappe.call({
                method: "myapp.api.bulk_approve_orders",
                args: { orders: selected.map((d) => d.name) },
                callback: function() {
                    listview.refresh();
                },
            });
        });
    },

    // Format columns
    formatters: {
        grand_total: function(value, df, doc) {
            return `<b>${format_currency(value, doc.currency)}</b>`;
        },
    },

    // Add row buttons
    button: {
        show: function(doc) {
            return doc.docstatus === 1 && doc.status !== "Completed";
        },
        get_label: function() {
            return __("Complete");
        },
        get_description: function(doc) {
            return __("Mark {0} as completed", [doc.name]);
        },
        action: function(doc) {
            frappe.call({
                method: "myapp.api.complete_order",
                args: { order: doc.name },
                callback: function() {
                    cur_list.refresh();
                },
            });
        },
    },
};
```

---

## 8. Make Form Read-Only

```javascript
frappe.ui.form.on("Sales Order", {
    refresh: function(frm) {
        // Make entire form read-only based on condition
        if (frm.doc.status === "Completed") {
            frm.set_read_only();
            frm.disable_save();
        }

        // Make specific fields read-only
        if (frm.doc.docstatus === 1) {
            frm.set_df_property("customer", "read_only", 1);
            frm.set_df_property("delivery_date", "read_only", 1);
        }

        // Make child table read-only
        frm.set_df_property("items", "read_only", frm.doc.docstatus !== 0);
    },
});
```

---

## 9. Override Client Script Hooks

```javascript
// Override an existing client script method
// In your custom app's JS file (loaded via app_include_js or doctype_js)

// Save original handler
const _original_refresh = frappe.ui.form.handlers["Sales Order"]["refresh"];

// Override with your version
frappe.ui.form.on("Sales Order", {
    refresh: function(frm) {
        // Call original first
        if (_original_refresh) {
            _original_refresh.forEach((fn) => fn(frm));
        }
        // Add your custom logic
        frm.add_custom_button(__("My Custom Action"), function() {
            // custom action
        });
    },
});
```

---

## 10. Creating Related Documents

```javascript
// Create a related document from a form button
frappe.ui.form.on("Sales Order", {
    refresh: function(frm) {
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button(__("Create Purchase Order"), function() {
                frappe.model.open_mapped_doc({
                    method: "myapp.api.make_purchase_order",
                    frm: frm,
                });
            }, __("Create"));
        }
    },
});
```

```python
# myapp/api.py
@frappe.whitelist()
def make_purchase_order(source_name, target_doc=None):
    from frappe.model.mapper import get_mapped_doc

    def set_missing_values(source, target):
        target.supplier = frappe.db.get_value("Item", source.items[0].item_code, "default_supplier")

    return get_mapped_doc(
        "Sales Order",
        source_name,
        {
            "Sales Order": {
                "doctype": "Purchase Order",
                "field_map": {
                    "name": "sales_order",
                    "transaction_date": "transaction_date",
                },
            },
            "Sales Order Item": {
                "doctype": "Purchase Order Item",
                "field_map": {
                    "item_code": "item_code",
                    "qty": "qty",
                    "rate": "rate",
                },
            },
        },
        target_doc,
        set_missing_values,
    )
```

---

## 11. Form Field `$wrapper` and Custom HTML

```javascript
frappe.ui.form.on("Sales Order", {
    refresh: function(frm) {
        // Access field wrapper to inject custom HTML
        let field = frm.get_field("customer");
        let $wrapper = field.$wrapper;

        // Add custom element after field
        $wrapper.find(".control-value").after(
            `<div class="custom-info text-muted small">
                Customer since: ${frm.doc.customer_creation_date || "N/A"}
            </div>`
        );

        // Render custom HTML in a HTML field
        frm.get_field("custom_html_field").$wrapper.html(`
            <div class="frappe-card">
                <h5>Summary</h5>
                <p>Total Items: ${frm.doc.items ? frm.doc.items.length : 0}</p>
                <p>Grand Total: ${format_currency(frm.doc.grand_total)}</p>
            </div>
        `);
    },
});
```

---

## 12. Quick Entry Dialog Customization

```javascript
// Customize the quick entry dialog for a DocType
frappe.ui.form.on("Customer", {
    onload: function(frm) {
        // This runs when quick entry dialog opens
        if (frm.is_new()) {
            frm.set_value("customer_group", "Commercial");
            frm.set_value("territory", frappe.defaults.get_default("territory"));
        }
    },
});

// Programmatically open quick entry
frappe.new_doc("Customer", {
    customer_name: "New Customer",
    customer_group: "Commercial",
});
```

---

## 13. Refresh Operations

```javascript
// Reload the current document
frm.reload_doc();

// Refresh a specific field
frm.refresh_field("items");
frm.refresh_field("grand_total");

// Refresh multiple fields
["items", "taxes", "grand_total"].forEach((f) => frm.refresh_field(f));

// Refresh entire form
frm.refresh();

// Trigger a field event programmatically
frm.trigger("customer");
frm.trigger("calculate_totals");

// Refresh list view
if (cur_list) cur_list.refresh();
```

---

## 14. Comment Feature

```javascript
// Add a comment from client script
frappe.call({
    method: "frappe.desk.form.utils.add_comment",
    args: {
        reference_doctype: frm.doctype,
        reference_name: frm.docname,
        content: "Order reviewed and approved",
        comment_email: frappe.session.user,
        comment_by: frappe.session.user_fullname,
    },
    callback: function() {
        frm.reload_doc();
    },
});
```

```python
# From server side
doc = frappe.get_doc("Sales Order", "SO-0001")
doc.add_comment("Comment", "Order reviewed and approved")
```

---

## 15. Custom Jinja Filters

```python
# myapp/jinja_filters.py
def format_phone(value):
    """Format phone number: 1234567890 → (123) 456-7890"""
    if not value:
        return ""
    digits = "".join(filter(str.isdigit, str(value)))
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    return value

def currency_words(value, currency="USD"):
    """Convert number to words: 1500 → One Thousand Five Hundred"""
    # Implementation
    pass

def truncate_text(value, length=50):
    """Truncate text to given length"""
    if not value:
        return ""
    return value[:length] + "..." if len(value) > length else value
```

```python
# hooks.py
jinja = {
    "filters": [
        "myapp.jinja_filters.format_phone",
        "myapp.jinja_filters.currency_words",
        "myapp.jinja_filters.truncate_text",
    ]
}
```

```html
<!-- Use in print format or web template -->
{{ doc.phone | format_phone }}
{{ doc.grand_total | currency_words }}
{{ doc.description | truncate_text(100) }}
```

---

## 16. Language Toggle in Navbar

```python
# hooks.py
app_include_js = ["/assets/myapp/js/language_toggle.js"]
```

```javascript
// myapp/public/js/language_toggle.js
$(document).on("toolbar_setup", function() {
    const languages = [
        { code: "en", label: "English" },
        { code: "ar", label: "العربية" },
    ];

    const current_lang = frappe.boot.lang || "en";

    let dropdown_items = languages.map((lang) => `
        <li>
            <a class="dropdown-item" href="#" data-lang="${lang.code}">
                ${lang.label} ${current_lang === lang.code ? "✓" : ""}
            </a>
        </li>
    `).join("");

    $(".navbar-nav").append(`
        <li class="nav-item dropdown">
            <a class="nav-link dropdown-toggle" data-toggle="dropdown" href="#">
                🌐 ${current_lang.toUpperCase()}
            </a>
            <ul class="dropdown-menu">${dropdown_items}</ul>
        </li>
    `);

    $(document).on("click", "[data-lang]", function(e) {
        e.preventDefault();
        const lang = $(this).data("lang");
        frappe.call({
            method: "frappe.client.set_value",
            args: {
                doctype: "User",
                name: frappe.session.user,
                fieldname: "language",
                value: lang,
            },
            callback: function() {
                window.location.reload();
            },
        });
    });
});
```

---

## 17. Keyboard Shortcuts

```javascript
// Register custom keyboard shortcuts
frappe.ui.keys.add_shortcut({
    shortcut: "ctrl+shift+s",
    action: function() {
        if (cur_frm) {
            cur_frm.save();
        }
    },
    description: __("Save current form"),
    page: "Form",
    ignore_inputs: false,
});

// Remove a shortcut
frappe.ui.keys.remove_shortcut("ctrl+shift+s");

// List all shortcuts
console.log(frappe.ui.keys.get_all_shortcuts());
```

---

## Best Practices

1. **Use `frm.trigger()` instead of calling functions directly** — keeps event chain intact
2. **Always check `frm.doc.docstatus`** before showing action buttons
3. **Use `frappe.xcall()` for async/await** instead of callback hell
4. **Debounce expensive operations** in field change handlers
5. **Use `locals[cdt][cdn]`** to access child row data in child table events
6. **Never use `cur_frm` inside form event handlers** — use the `frm` parameter
7. **Use `frm.set_df_property()`** for dynamic field property changes
8. **Clean up event listeners** if you add them manually to avoid memory leaks
