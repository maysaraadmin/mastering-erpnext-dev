# -*- coding: utf-8 -*-
"""
Debugging Utilities
Chapter 14: Debugging Like a Pro

Practical debugging helpers for use in bench console and custom apps.
Run interactively: bench --site <sitename> console
"""

import frappe
import json
import time
import traceback


# =============================================================================
# BENCH CONSOLE QUICK HELPERS
# Usage: bench --site dev.local console
#        >>> from debug_utils import doc, sql, perms, inspect_doctype
# =============================================================================

def doc(doctype, name):
    """Quick document fetch. Usage: doc('Customer', 'CUST-00001')"""
    return frappe.get_doc(doctype, name)


def sql(query, params=None):
    """Quick SQL execution. Usage: sql('SELECT * FROM tabCustomer LIMIT 5')"""
    return frappe.db.sql(query, params or (), as_dict=True)


def perms(doctype, name=None):
    """Check current user's permissions for a DocType."""
    return {
        'read':   frappe.has_permission(doctype, 'read',   name),
        'write':  frappe.has_permission(doctype, 'write',  name),
        'create': frappe.has_permission(doctype, 'create', name),
        'delete': frappe.has_permission(doctype, 'delete', name),
        'submit': frappe.has_permission(doctype, 'submit', name),
        'cancel': frappe.has_permission(doctype, 'cancel', name),
    }


# =============================================================================
# DOCTYPE INSPECTION
# =============================================================================

def inspect_doctype(doctype):
    """
    Print a comprehensive summary of a DocType.
    
    Usage:
        bench --site dev.local console
        >>> from debug_utils import inspect_doctype
        >>> inspect_doctype('Asset')
    """
    print(f"\n=== DocType: {doctype} ===")

    meta = frappe.get_meta(doctype)
    print(f"Module   : {meta.module}")
    print(f"Custom   : {bool(meta.custom)}")
    print(f"Submittable: {bool(meta.is_submittable)}")

    print(f"\n--- Fields ({len(meta.fields)}) ---")
    for f in meta.fields[:15]:
        reqd = " [required]" if f.reqd else ""
        print(f"  {f.fieldname:<30} {f.fieldtype:<20} {f.label}{reqd}")
    if len(meta.fields) > 15:
        print(f"  ... and {len(meta.fields) - 15} more")

    print(f"\n--- Record Count ---")
    print(f"  Total   : {frappe.db.count(doctype)}")
    print(f"  Draft   : {frappe.db.count(doctype, {'docstatus': 0})}")
    print(f"  Submitted: {frappe.db.count(doctype, {'docstatus': 1})}")
    print(f"  Cancelled: {frappe.db.count(doctype, {'docstatus': 2})}")

    print(f"\n--- Recent 5 Records ---")
    recent = frappe.get_all(doctype,
        fields=['name', 'creation', 'owner'],
        order_by='creation desc',
        limit=5
    )
    for r in recent:
        print(f"  {r.name}  |  {r.creation}  |  {r.owner}")


# =============================================================================
# USER / SESSION DEBUGGING
# =============================================================================

def debug_user(user=None):
    """
    Print roles and permissions for a user.
    
    Usage:
        >>> debug_user()                    # current session user
        >>> debug_user('admin@example.com') # specific user
    """
    user = user or frappe.session.user
    print(f"\n=== User: {user} ===")

    u = frappe.db.get_value('User', user, ['full_name', 'user_type', 'enabled'], as_dict=True)
    if not u:
        print("  User not found.")
        return

    print(f"  Full Name : {u.full_name}")
    print(f"  Type      : {u.user_type}")
    print(f"  Enabled   : {bool(u.enabled)}")

    roles = frappe.get_roles(user)
    print(f"\n--- Roles ({len(roles)}) ---")
    for r in sorted(roles):
        print(f"  - {r}")

    user_perms = frappe.get_user_permissions(user)
    if user_perms:
        print(f"\n--- User Permissions ---")
        for allow_type, values in user_perms.items():
            print(f"  {allow_type}: {list(values.keys())[:5]}")
    else:
        print("\n  No User Permissions defined (full access within roles).")


# =============================================================================
# QUERY PERFORMANCE PROFILING
# =============================================================================

def profile_query(query, params=None, runs=3):
    """
    Run a SQL query multiple times and report timing.
    
    Usage:
        >>> profile_query("SELECT COUNT(*) FROM `tabSales Order` WHERE docstatus=1")
    """
    times = []
    result = None

    for i in range(runs):
        start = time.time()
        result = frappe.db.sql(query, params or (), as_dict=True)
        times.append(time.time() - start)

    avg = sum(times) / len(times)
    print(f"\n=== Query Profile ({runs} runs) ===")
    print(f"  Avg  : {avg*1000:.2f} ms")
    print(f"  Min  : {min(times)*1000:.2f} ms")
    print(f"  Max  : {max(times)*1000:.2f} ms")
    print(f"  Rows : {len(result) if result else 0}")

    # EXPLAIN
    try:
        explain = frappe.db.sql(f"EXPLAIN {query}", params or (), as_dict=True)
        print(f"\n--- EXPLAIN ---")
        for row in explain:
            print(f"  type={row.get('type')}  key={row.get('key')}  "
                  f"rows={row.get('rows')}  Extra={row.get('Extra')}")
    except Exception as e:
        print(f"  EXPLAIN failed: {e}")

    return result


# =============================================================================
# DOCUMENT DIFF — WHAT CHANGED?
# =============================================================================

def diff_doc(doctype, name):
    """
    Show which fields differ between the in-memory doc and the database.
    Useful for understanding what a save() call will actually change.
    
    Usage:
        >>> d = doc('Asset', 'ASSET-GEN-000001')
        >>> d.status = 'In Use'
        >>> diff_doc('Asset', d.name)   # shows status changed
    """
    db_doc = frappe.get_doc(doctype, name)
    mem_doc = frappe.get_doc(doctype, name)  # fresh copy

    print(f"\n=== Document Diff: {doctype} {name} ===")
    print("  (comparing DB values — modify mem_doc then call diff manually)")

    changes = {}
    for field in db_doc.meta.fields:
        fn = field.fieldname
        db_val = db_doc.get(fn)
        mem_val = mem_doc.get(fn)
        if db_val != mem_val:
            changes[fn] = {'db': db_val, 'mem': mem_val}

    if changes:
        for fn, vals in changes.items():
            print(f"  {fn}: {vals['db']!r} → {vals['mem']!r}")
    else:
        print("  No differences found.")

    return changes


# =============================================================================
# HOOK TRACING — WHAT HOOKS FIRE FOR A DOCTYPE?
# =============================================================================

def trace_hooks(doctype):
    """
    List all hooks registered for a DocType (doc_events).
    
    Usage:
        >>> trace_hooks('Sales Order')
    """
    print(f"\n=== Hooks for: {doctype} ===")

    all_hooks = frappe.get_hooks('doc_events') or {}

    # Check both exact match and wildcard '*'
    for key in [doctype, '*']:
        events = all_hooks.get(key, {})
        if events:
            print(f"\n  [{key}]")
            for event, handlers in events.items():
                for handler in (handlers if isinstance(handlers, list) else [handlers]):
                    print(f"    {event:<20} → {handler}")

    if not any(k in all_hooks for k in [doctype, '*']):
        print("  No doc_events hooks found.")


# =============================================================================
# SAFE EVAL FOR CONSOLE EXPERIMENTS
# =============================================================================

def try_run(fn, *args, **kwargs):
    """
    Run a function and print the result or traceback without crashing the console.
    
    Usage:
        >>> try_run(frappe.get_doc, 'Asset', 'DOES-NOT-EXIST')
    """
    try:
        result = fn(*args, **kwargs)
        print(f"  ✓ Result: {result}")
        return result
    except Exception:
        print(f"  ✗ Error:")
        traceback.print_exc()
        return None
