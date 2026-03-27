# Common Pitfalls & Troubleshooting Guide

## 🚨 Common Pitfalls for ERPNext Developers

### 1. Cache API Version Conflicts

**Problem**: Using wrong cache API for your Frappe version

**Symptoms**:
```
AttributeError: 'RedisCacheWrapper' object has no attribute 'get'
AttributeError: module 'frappe.utils.caching' has no attribute 'cache'
```

**Solution**:
```python
# Version-compatible cache access
try:
    # v14 pattern
    value = frappe.cache().get(key)
    frappe.cache().setex(key, value, 3600)
except AttributeError:
    # v15+ pattern  
    value = frappe.cache.get_value(key)
    frappe.cache.set_value(key, value, expires_in_sec=3600)
```

**Prevention**: Always use version-compatible patterns in your code

---

### 2. N+1 Query Problem

**Problem**: Making database queries inside loops

**Symptoms**: Slow page loads, high database load

**Bad Code**:
```python
# DON'T DO THIS - N+1 queries
for item in sales_order.items:
    item_name = frappe.db.get_value('Item', item.item_code, 'item_name')
```

**Good Code**:
```python
# DO THIS - Single query
item_codes = [item.item_code for item in sales_order.items]
item_names = frappe.db.get_all('Item', 
    filters={'name': ['in', item_codes]}, 
    fields=['name', 'item_name'])
name_lookup = {item.name: item.item_name for item in item_names}

for item in sales_order.items:
    item.item_name = name_lookup.get(item.item_code)
```

---

### 3. Infinite Loop in Hooks

**Problem**: Hook methods triggering each other recursively

**Symptoms**: Maximum recursion depth exceeded, system hangs

**Bad Code**:
```python
# DON'T DO THIS - Can cause infinite loops
def on_update(self):
    self.update_related_document()

def update_related_document(self):
    # This triggers on_update again!
    related_doc.save()
```

**Good Code**:
```python
# DO THIS - Prevent recursion
def on_update(self):
    if not hasattr(frappe.flags, 'updating_related'):
        frappe.flags.updating_related = True
        try:
            self.update_related_document()
        finally:
            delattr(frappe.flags, 'updating_related')
```

---

### 4. Missing Transaction Rollback

**Problem**: Database changes not rolled back on error

**Symptoms**: Partial data corruption, inconsistent state

**Bad Code**:
```python
# DON'T DO THIS - No transaction management
def create_complex_document():
    doc1 = frappe.get_doc({...})
    doc1.insert()
    
    doc2 = frappe.get_doc({...})  
    doc2.insert()  # If this fails, doc1 remains!
```

**Good Code**:
```python
# DO THIS - Proper transaction management
def create_complex_document():
    frappe.db.begin()
    try:
        doc1 = frappe.get_doc({...})
        doc1.insert()
        
        doc2 = frappe.get_doc({...})
        doc2.insert()
        
        frappe.db.commit()
    except Exception as e:
        frappe.db.rollback()
        raise e
```

---

### 5. Client Script Timing Issues

**Problem**: Running scripts before DOM is ready

**Symptoms**: Scripts not working, undefined errors

**Bad Code**:
```javascript
// DON'T DO THIS - Runs too early
frappe.ui.form.on('Sales Order', {
    onload: function(frm) {
        // This might run before fields are ready
        frm.set_value('customer', 'CUST-001');
    }
});
```

**Good Code**:
```javascript
// DO THIS - Wait for proper initialization
frappe.ui.form.on('Sales Order', {
    refresh: function(frm) {
        // This runs after form is fully loaded
        if (frm.is_new() && !frm.customer) {
            frm.set_value('customer', 'CUST-001');
        }
    }
});
```

---

### 6. Permission Bypass in Custom APIs

**Problem**: Not checking permissions in whitelisted methods

**Symptoms**: Security vulnerability, unauthorized access

**Bad Code**:
```python
# DON'T DO THIS - No permission check
@frappe.whitelist()
def get_sensitive_data():
    return frappe.db.get_all('Sensitive DocType', fields=['*'])
```

**Good Code**:
```python
# DO THIS - Check permissions
@frappe.whitelist()
def get_sensitive_data():
    # Check if user has permission
    if not frappe.has_permission('Sensitive DocType', 'read'):
        frappe.throw('Not permitted', frappe.PermissionError)
    
    return frappe.db.get_all('Sensitive DocType', fields=['*'])
```

---

### 7. Memory Leaks in Long-running Processes

**Problem**: Not cleaning up resources in background jobs

**Symptoms**: Memory usage grows over time, system crashes

**Bad Code**:
```python
# DON'T DO THIS - Memory leak
@frappe.whitelist()
def process_large_dataset():
    all_data = frappe.db.get_all('Large Table', fields=['*'])
    for row in all_data:
        process_row(row)  # All data stays in memory
```

**Good Code**:
```python
# DO THIS - Process in batches
@frappe.whitelist()
def process_large_dataset():
    batch_size = 1000
    offset = 0
    
    while True:
        batch = frappe.db.get_all('Large Table', 
            fields=['*'], 
            limit=batch_size, 
            start=offset)
        
        if not batch:
            break
            
        for row in batch:
            process_row(row)
        
        offset += batch_size
        # Clear memory
        del batch
```

---

### 8. SQL Injection Vulnerabilities

**Problem**: Direct string interpolation in queries

**Symptoms**: Security vulnerability, data theft

**Bad Code**:
```python
# DON'T DO THIS - SQL injection risk
def get_user_data(user_email):
    query = f"SELECT * FROM `tabUser` WHERE email = '{user_email}'"
    return frappe.db.sql(query, as_dict=True)
```

**Good Code**:
```python
# DO THIS - Use parameterized queries
def get_user_data(user_email):
    query = "SELECT * FROM `tabUser` WHERE email = %s"
    return frappe.db.sql(query, (user_email,), as_dict=True)
```

---

## 🔧 Troubleshooting Checklist

### Performance Issues

- [ ] Check for N+1 queries
- [ ] Review cache usage
- [ ] Analyze slow queries in logs
- [ ] Check background job queue

### Data Integrity Issues

- [ ] Verify transaction boundaries
- [ ] Check validation logic
- [ ] Review hook dependencies
- [ ] Test rollback scenarios

### Security Issues

- [ ] Review permission checks
- [ ] Check for SQL injection
- [ ] Validate input sanitization
- [ ] Audit API access controls

### Memory Issues

- [ ] Monitor memory usage
- [ ] Check for circular references
- [ ] Review cleanup in finally blocks
- [ ] Test with large datasets

## 🚀 Prevention Strategies

1. **Code Review Guidelines**
   - Always check for version compatibility
   - Look for database queries in loops
   - Verify permission checks in APIs
   - Review transaction boundaries

2. **Testing Strategies**
   - Test with different Frappe versions
   - Include performance tests
   - Test error scenarios
   - Verify rollback behavior

3. **Monitoring Setup**
   - Monitor database query performance
   - Track memory usage
   - Log slow operations
   - Set up alerts for errors

## 📚 Additional Resources

- [Frappe Framework Documentation](https://frappeframework.com/docs)
- [Performance Best Practices](https://frappeframework.com/docs/user/en/best-practices/performance)
- [Security Guidelines](https://frappeframework.com/docs/user/en/security)
- [ERPNext Community Forum](https://discuss.frappe.io)
