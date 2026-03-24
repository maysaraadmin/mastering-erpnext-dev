# Chapter 24: Monkey Patching — Override Core Without Touching It

## What is Monkey Patching?

**Monkey patching** = change a core method, function, or class **without touching the core source files**.

In Python, functions and methods are first-class objects that can be reassigned at runtime:

```python
# Original function in some_module.py
def original_function():
    return "original behavior"

# Your override
def enhanced_function():
    return "enhanced behavior"

# Monkey patch — replace the original
import some_module
some_module.original_function = enhanced_function
```

---

## When to Use Monkey Patching

### Good use cases:
- **Bug fixes** — fix issues in core Frappe or third-party apps without waiting for upstream updates
- **Feature enhancement** — add functionality to existing methods
- **Integration requirements** — modify behavior for specific business needs
- **Temporary workarounds** — quick fixes while waiting for proper solutions

### Avoid when:
- **Simple customizations** — use Frappe's built-in customization features instead
- **DocType modifications** — use Custom Fields, Custom Scripts, or DocType inheritance
- **UI changes** — use Client Scripts or Custom Apps with proper UI extensions
- **Performance critical paths** — monkey patching adds overhead

---

## Frappe-Specific Override Methods

### Method 1: Hook-Based Overrides (Recommended)

#### Document Events
```python
# hooks.py
doc_events = {
    "User": {
        "before_save": "custom_app.overrides.user_overrides.before_save",
        "after_insert": "custom_app.overrides.user_overrides.after_insert"
    },
    "*": {
        "on_update": "custom_app.overrides.global_overrides.on_update"
    }
}
```

#### Whitelisted Method Overrides
```python
# hooks.py
override_whitelisted_methods = {
    "frappe.desk.doctype.event.event.get_events": "custom_app.overrides.event_overrides.get_events"
}
```

#### DocType Class Overrides
```python
# hooks.py
override_doctype_class = {
    "User": "custom_app.overrides.CustomUser"
}

# custom_app/overrides.py
from frappe.core.doctype.user.user import User

class CustomUser(User):
    def validate(self):
        super().validate()
        # Your custom validation logic
        if self.email and not self.email.endswith('@company.com'):
            frappe.throw("Only company emails are allowed")
```

### Method 2: Boot Session Overrides

For core function overrides applied system-wide:

```python
# hooks.py
boot_session = "custom_app.overrides.apply_core_overrides"

# custom_app/overrides.py
def apply_core_overrides():
    import frappe.utils
    
    # Store original
    frappe.utils._original_get_url = frappe.utils.get_url
    
    # Replace with enhanced version
    frappe.utils.get_url = enhanced_get_url

def enhanced_get_url(*args, **kwargs):
    result = frappe.utils._original_get_url(*args, **kwargs)
    # Additional processing
    return result
```

### Method 3: App Installation Hooks

```python
# hooks.py
after_app_install = "custom_app.overrides.apply_overrides"
before_app_uninstall = "custom_app.overrides.restore_overrides"

# custom_app/overrides.py
def apply_overrides():
    override_core_functions()
    override_third_party_functions()

def restore_overrides():
    restore_core_functions()
    restore_third_party_functions()
```

---

## Implementation Patterns

### Pattern 1: Simple Function Replacement

```python
import frappe.utils

def apply_overrides():
    # Always store original before replacing
    if not hasattr(frappe.utils, '_original_cint'):
        frappe.utils._original_cint = frappe.utils.cint
    
    frappe.utils.cint = enhanced_cint

def enhanced_cint(value, default=0):
    """Enhanced version with better error handling"""
    try:
        return frappe.utils._original_cint(value, default)
    except Exception as e:
        frappe.logger().warning(f"cint conversion failed: {e}")
        return default
```

### Pattern 2: Method Decoration

```python
def apply_overrides():
    import frappe.model.document
    
    original_save = frappe.model.document.Document.save
    
    def enhanced_save(self, *args, **kwargs):
        frappe.logger().info(f"Saving document: {self.doctype} - {self.name}")
        return original_save(self, *args, **kwargs)
    
    frappe.model.document.Document.save = enhanced_save
```

### Pattern 3: Class Method Override

```python
def apply_overrides():
    from frappe.core.doctype.user.user import User
    
    User._original_validate = User.validate
    
    def enhanced_validate(self):
        self._original_validate()
        # Add custom validation
        if self.email and not self.email.endswith('@company.com'):
            frappe.throw("Only company emails are allowed")
    
    User.validate = enhanced_validate
```

### Pattern 4: Security Enhancement

```python
def apply_security_overrides():
    import frappe.auth
    
    original_check_password = frappe.auth.check_password
    frappe.auth._original_check_password = original_check_password
    
    def enhanced_check_password(user, pwd, doctype='User', fieldname='password'):
        if is_suspicious_login(user):
            frappe.throw("Login temporarily blocked")
        return frappe.auth._original_check_password(user, pwd, doctype, fieldname)
    
    frappe.auth.check_password = enhanced_check_password
```

### Pattern 5: Decorator-Based Override

```python
def create_override_decorator(original_func):
    def decorator(enhancement_func):
        def wrapper(*args, **kwargs):
            result = enhancement_func(*args, **kwargs)
            if result is not None:
                return result
            return original_func(*args, **kwargs)
        return wrapper
    return decorator

import frappe.utils
original_cint = frappe.utils.cint

@create_override_decorator(original_cint)
def enhanced_cint(value, default=0):
    if isinstance(value, str) and value.startswith('SPECIAL_'):
        return int(value.replace('SPECIAL_', ''))
    return None  # Let original handle it

frappe.utils.cint = enhanced_cint
```

### Pattern 6: Context Manager (Temporary Override)

```python
from contextlib import contextmanager

@contextmanager
def temporary_override(module, function_name, new_function):
    original = getattr(module, function_name)
    setattr(module, function_name, new_function)
    try:
        yield
    finally:
        setattr(module, function_name, original)

# Usage — custom behavior active only in this block
with temporary_override(frappe.utils, 'cint', custom_cint):
    result = frappe.utils.cint("123")
```

---

## Common Use Cases

### Fix a third-party app bug

```python
def apply_bug_fixes():
    try:
        import third_party_app.utils
        
        third_party_app.utils._original_buggy_function = third_party_app.utils.buggy_function
        
        def fixed_function(*args, **kwargs):
            if not args or not isinstance(args[0], str):
                return None
            return third_party_app.utils._original_buggy_function(*args, **kwargs)
        
        third_party_app.utils.buggy_function = fixed_function
        
    except ImportError:
        pass  # Third-party app not installed
```

### Add logging to core functions

```python
import time

def add_logging_overrides():
    import frappe.model.document
    
    original_insert = frappe.model.document.Document.insert
    
    def logged_insert(self, *args, **kwargs):
        start_time = time.time()
        try:
            result = original_insert(self, *args, **kwargs)
            duration = time.time() - start_time
            frappe.logger().info(f"Document inserted: {self.doctype} - {self.name} ({duration:.2f}s)")
            return result
        except Exception as e:
            frappe.logger().error(f"Document insert failed: {self.doctype} - {e}")
            raise
    
    frappe.model.document.Document.insert = logged_insert
```

---

## Best Practices

### 1. Always backup original functions
```python
# Good
if not hasattr(module, '_original_function'):
    module._original_function = module.function

# Bad — direct replacement without backup
module.function = new_function
```

### 2. Implement proper error handling
```python
def apply_overrides():
    try:
        import target_module
        target_module.function = enhanced_function
        frappe.logger().info("Successfully applied override")
    except ImportError:
        frappe.logger().warning("Target module not found")
    except Exception as e:
        frappe.logger().error(f"Failed to apply override: {e}")
```

### 3. Provide restoration functions
```python
def restore_overrides():
    try:
        import target_module
        if hasattr(target_module, '_original_function'):
            target_module.function = target_module._original_function
            delattr(target_module, '_original_function')
    except Exception as e:
        frappe.logger().error(f"Failed to restore override: {e}")
```

### 4. Document your overrides thoroughly
```python
def enhanced_function(*args, **kwargs):
    """
    Enhanced version of original_module.function
    
    Changes:
    - Added input validation
    - Improved error handling
    - Added logging
    
    Original: original_module.function
    """
    pass
```

### 5. Use conditional overrides
```python
def apply_overrides():
    if frappe.conf.get('enable_custom_overrides'):
        apply_user_overrides()
    
    if 'third_party_app' in frappe.get_installed_apps():
        apply_third_party_overrides()
```

---

## Troubleshooting

### Override not applied
```python
# Problem: Override applied too late
# Solution: Use boot_session hook
boot_session = "custom_app.overrides.apply_overrides"
```

### Circular import
```python
# Problem: Importing module causes circular dependency
# Solution: Import inside function, not at module level
def apply_overrides():
    import target_module  # Import here
    target_module.function = enhanced_function
```

### Override conflicts (multiple apps)
```python
def apply_overrides():
    import target_module
    
    # Check if already overridden by another app
    if hasattr(target_module.function, '__name__'):
        if 'enhanced' in target_module.function.__name__:
            frappe.logger().warning("Function already overridden by another app")
            return
    
    target_module.function = enhanced_function
```

---

## Summary

Monkey patching is powerful but should be used carefully. Always prefer Frappe's built-in customization methods. When you must monkey patch:

- Always backup original functions
- Use proper error handling
- Document your changes completely (the next developer will need it)
- Provide restoration mechanisms for when the app is uninstalled
- Test thoroughly, especially in production-like environments
