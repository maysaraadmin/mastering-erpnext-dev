# Chapter 22: Patches and Migrations

## What is a Patch in Frappe?

A patch is a tiny Python script that:
1. Runs automatically during migrations (`bench migrate`)
2. Fixes or updates database schema or data
3. Gets recorded so it **only runs once** — even if you run `bench migrate` 1000 times

Frappe opens it once, reads it, runs the `execute()` function, and logs it as "done."

---

## When to Write a Patch

Patches are used when you make a change in existing functionality and want to update instances already running ERPNext. They are **never run twice** and **never run on a new site**.

**Classic example**: Renaming the "School" module to "Education". On a new site, the DocType is already named "Education". On an older site, you need a patch to rename it.

### Real-life use cases:
- Add a unique constraint to two fields in a DocType
- Update old customer names to match new rules
- Remove test data from a live site
- Migrate values from an old field to a new one
- Add a missing column or update field types

---

## How to Write a Patch

### Step 1: Create the patch file

```python
# File: your_app/patches/v1_0/add_unique_booking_constraint.py
import frappe

def execute():
    frappe.db.add_unique("Booking", ["customer", "booking_date"])
```

**Rules:**
- The function **must** be named `execute` — this is how `bench migrate` detects it
- Use versioned folder names like `v1_0/` for clarity and maintenance

### Step 2: Register in `patches.txt`

```text
your_app.patches.v1_0.add_unique_booking_constraint
```

### Step 3: Run migration

```bash
bench --site yoursite migrate
```

This checks which patches haven't been applied yet (based on the **Patch Log**) and executes them safely.

---

## How Frappe Prevents Re-Running Patches

Once a patch runs, Frappe logs it in the **Patch Log** DocType. Even if you run `bench migrate` a hundred times, it won't run again — unless you manually delete the entry from Patch Log.

---

## More Patch Examples

### Data migration patch

```python
# your_app/patches/v2_0/migrate_customer_names.py
import frappe

def execute():
    # Rename all customers with old prefix
    frappe.db.sql("""
        UPDATE `tabCustomer`
        SET customer_name = CONCAT('NEW_', customer_name)
        WHERE customer_name NOT LIKE 'NEW_%'
    """)
    frappe.db.commit()
```

### Field value migration

```python
# your_app/patches/v2_1/move_field_values.py
import frappe

def execute():
    # Move data from old_field to new_field
    frappe.db.sql("""
        UPDATE `tabSales Invoice`
        SET new_field = old_field
        WHERE new_field IS NULL AND old_field IS NOT NULL
    """)
    frappe.db.commit()
```

### Schema change patch

```python
# your_app/patches/v3_0/add_index_to_sales_invoice.py
import frappe

def execute():
    if not frappe.db.has_index("Sales Invoice", "customer_posting_date"):
        frappe.db.add_index("Sales Invoice", ["customer", "posting_date"])
```

### Conditional patch (safe to re-run)

```python
# your_app/patches/v3_1/set_default_status.py
import frappe

def execute():
    frappe.db.sql("""
        UPDATE `tabAsset`
        SET status = 'Active'
        WHERE status IS NULL OR status = ''
    """)
    frappe.db.commit()
```

---

## Patch File Organization

```
your_app/
├── patches/
│   ├── __init__.py
│   ├── v1_0/
│   │   ├── __init__.py
│   │   └── add_unique_booking_constraint.py
│   ├── v2_0/
│   │   ├── __init__.py
│   │   └── migrate_customer_names.py
│   └── v3_0/
│       ├── __init__.py
│       └── add_index_to_sales_invoice.py
└── patches.txt
```

### patches.txt ordering matters

```text
# patches.txt — order is important, top runs first
your_app.patches.v1_0.add_unique_booking_constraint
your_app.patches.v2_0.migrate_customer_names
your_app.patches.v3_0.add_index_to_sales_invoice
```

---

## Best Practices

1. **Always test on staging** before running on production
2. **Always backup** your database before production migrations
3. **Keep patches well-named** — `v1_0/fix_duplicate_emails.py` is better than `patch1.py`
4. **If a patch fails**, fix it and re-run after clearing it from the Patch Log
5. **Use `frappe.db.commit()`** after DML operations (UPDATE/INSERT/DELETE)
6. **Make patches idempotent** when possible — safe to run even if somehow triggered twice

---

## Interview Q&A

**Q: What is a patch in Frappe?**
A: A Python script used to apply database changes, fix issues, or modify data after an update. Defined in `patches.txt`, each patch runs exactly once per site.

**Q: When would you use a patch script?**
A: Adding new fields to existing DocTypes, migrating data from one format to another, fixing data inconsistencies, or applying schema changes to live sites.

**Q: How do you handle data migrations when upgrading ERPNext?**
A: Write patch scripts, always take a database backup first, test in staging, and review release notes for breaking changes.

**Q: How does Frappe know not to re-run a patch?**
A: It logs the patch module path in the **Patch Log** DocType. On subsequent `bench migrate` runs, already-logged patches are skipped.
