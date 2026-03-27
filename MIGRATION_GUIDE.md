# Migration Guide: ERPNext v14 → v15 → v16

## Version Compatibility Overview

This guide helps you migrate your ERPNext/Frappe applications between versions.

### v14 → v15 Breaking Changes

| Area | v14 Pattern | v15 Pattern | Migration Steps |
|------|-------------|------------|-----------------|
| **Cache API** | `frappe.cache().get(key)` | `frappe.cache.get_value(key)` | Update cache calls |
| **User Companies** | `frappe.get_user_companies()` | Query `User Permission` directly | Replace with direct query |
| **Background Jobs** | `now=True` | `enqueue_after_commit` | Update job enqueue calls |
| **Request IP** | `frappe.local.request_ip` | `frappe.local.request.remote_addr` | Update IP access |

### v15 → v16 Breaking Changes

| Area | v15 Pattern | v16 Pattern | Migration Steps |
|------|-------------|------------|-----------------|
| **Bulk Operations** | Individual inserts | `frappe.db.bulk_insert()` | Use bulk operations |
| **Type Hints** | Optional | Recommended | Add type hints |
| **Rate Limiting** | Manual | `frappe.utils.rate_limiter` | Use built-in limiter |
| **Performance** | Basic | Enhanced monitoring | Add performance tracking |

### Migration Script Template

```python
# Migration script for v14 → v15
def migrate_v14_to_v15():
    """Migrate cache API calls"""
    
    # Update cache calls
    old_pattern = "frappe.cache().get("
    new_pattern = "frappe.cache.get_value("
    
    # Find and replace in your codebase
    # Use tools like grep or IDE find/replace
    
    # Update background jobs
    # frappe.enqueue(task, now=True) → frappe.enqueue_after_commit(task)
    
    print("Migration completed!")
```

### Testing Migration

```bash
# Test migration on development site
bench --site dev.local migrate
bench --site dev.local run-tests --app your_app

# Verify functionality
bench --site dev.local console
>>> # Test your custom functions
```

## Common Migration Issues

1. **Cache API Changes** - Most common breaking change
2. **Import Path Changes** - Some utilities moved
3. **Method Signatures** - Parameters changed in some functions

## Best Practices

1. **Backup First** - Always backup before migration
2. **Test on Dev** - Never migrate production directly
3. **Update Dependencies** - Check app compatibility
4. **Run Tests** - Ensure all tests pass after migration
