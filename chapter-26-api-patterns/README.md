# Chapter 26: API Patterns — Requests, Responses, and Error Handling

## How `frappe.call()` Works Behind the Scenes

`frappe.call()` is the bridge between JavaScript and Python in Frappe. When you call `frm.call('method_name')`, Frappe:
1. Takes your current document data
2. Creates a Document object on the server using `frappe.get_doc()`
3. Executes your whitelisted method on that object
4. Returns the result

This is why Postman gives "Method not found" when calling a DocType method directly — Postman needs to use the `run_doc_method` endpoint with the complete document data structure.

### The Flow

```
Client JavaScript → frappe.call() → HTTP Request
    → run_doc_method() creates document object
    → doc.run_method() executes your method
    → Response → Client
```

### Client-Side Syntax

```javascript
// Basic call
frappe.call({
    method: "your_app.module.function",
    args: { param1: "value1" },
    callback: function(response) {
        console.log(response.message);
    }
});

// Form method call
frm.call('calculate_total', { multiplier: 1.5 })
    .then(function(response) {
        frm.set_value('field_name', response.message);
    });

// Promise-based (modern)
async function executeMethod() {
    const response = await frappe.xcall('method_path', { param1: 'value1' });
    console.log(response);
}
```

### Server-Side: Whitelisting

All methods callable from the client **must** be whitelisted:

```python
class YourDocType(Document):
    @frappe.whitelist()
    def calculate_total(self, multiplier=1):
        """Called from JavaScript via frm.call()"""
        result = self.base_amount * multiplier
        self.total = result
        return result

    def private_method(self):
        # This CANNOT be called from client
        pass
```

### Standalone Whitelisted Functions

```python
# In your module file
@frappe.whitelist()
def get_exchange_rate(from_currency, to_currency, date=None):
    """Callable from JavaScript via frappe.call()"""
    # Your logic here
    return rate
```

### Calling via Postman

#### Call a DocType method
```http
POST /api/method/run_doc_method
Content-Type: application/json
Authorization: token api_key:api_secret

{
    "method": "calculate_tax",
    "dt": "Sales Invoice",
    "dn": "SI-2024-00001",
    "args": { "tax_rate": 0.1 }
}
```

#### Call a module function
```http
POST /api/method/your_app.utils.get_exchange_rate
Content-Type: application/json
Authorization: token api_key:api_secret

{
    "from_currency": "USD",
    "to_currency": "EUR"
}
```

---

## Controlling the API Response Body

By default, Frappe wraps return values in a `message` field:
```python
def my_api():
    return "Hello World"
# Response: {"message": "Hello World"}
```

To control the response structure fully, use `frappe.local.response`:

```python
@frappe.whitelist()
def custom_api():
    data = {"status": "success", "items": [...]}
    
    frappe.local.response["http_status_code"] = 200
    frappe.local.response["data"] = data
    frappe.local.response.pop("message", None)  # Remove default wrapper
```

### `frappe.local.response` vs `frappe.response`

- `frappe.local.response` — the actual response dictionary (thread-local, per-request)
- `frappe.response` — a `LocalProxy` shortcut that points to `frappe.local.response`

Both work identically:
```python
frappe.response["message"] = "Hello"
frappe.local.response["message"] = "Hello"  # Same thing
```

### Response Types

```python
# JSON (default)
frappe.local.response["type"] = "json"

# File download
frappe.local.response["type"] = "download"
frappe.local.response["filename"] = "report.pdf"
frappe.local.response["filecontent"] = pdf_content

# Redirect
frappe.local.response["type"] = "redirect"
frappe.local.response["location"] = "/app/success-page"
```

### HTTP Status Codes

```python
frappe.local.response["http_status_code"] = 200  # Success
frappe.local.response["http_status_code"] = 400  # Bad Request
frappe.local.response["http_status_code"] = 401  # Unauthorized
frappe.local.response["http_status_code"] = 403  # Forbidden
frappe.local.response["http_status_code"] = 404  # Not Found
frappe.local.response["http_status_code"] = 500  # Server Error
```

---

## `frappe.msgprint` vs `frappe.throw`

### `frappe.msgprint`

Frappe's core message display system. Works across web browser, API calls, and CLI.

```python
frappe.msgprint("Operation completed successfully", indicator="green")
frappe.msgprint("Warning: check your data", indicator="orange")
frappe.msgprint("Error occurred", indicator="red")
```

### `frappe.throw`

A convenience wrapper around `msgprint` specifically for raising exceptions with user-friendly messages:

```python
frappe.throw("Username is required")                          # Raises ValidationError (HTTP 417)
frappe.throw("Access denied", frappe.PermissionError)         # HTTP 403
frappe.throw("User not found", frappe.DoesNotExistError)      # HTTP 404
frappe.throw("Invalid data", frappe.ValidationError, title="Validation Failed")
```

### The Complete Flow

When you call `frappe.throw("User not found", DoesNotExistError)`:
1. `frappe.throw` calls `frappe.msgprint` with `raise_exception=DoesNotExistError`
2. `msgprint` creates a message object and stores it in the global message log
3. `msgprint` creates a `DoesNotExistError` instance with the message
4. `msgprint` raises the exception
5. Frappe's global handler catches it, determines it's a 404, formats the response
6. Response includes both error details and the user message

### Frappe's Exception Hierarchy

```python
ValidationError      # HTTP 417 — default for frappe.throw()
AuthenticationError  # HTTP 401
PermissionError      # HTTP 403
DoesNotExistError    # HTTP 404 (inherits ValidationError)
NameError            # HTTP 409
SessionStopped       # HTTP 503
```

---

## Global Exception Handling System

Frappe's WSGI application wraps every request in a global try-catch:

```python
@Request.application
def application(request):
    try:
        # All request processing
        init_request(request)
        validate_auth()
        # Route to handler...
    except HTTPException as e:
        return e  # Let Werkzeug handle HTTP exceptions
    except Exception as e:
        response = handle_exception(e)  # Global handler
    finally:
        if rollback:
            frappe.db.rollback()  # Always rollback on errors
```

### Context-Aware Error Responses

- **API/AJAX requests** → JSON error response
- **Web requests** → HTML error page
- **401 errors** → "Session Expired" page
- **403 errors** → "Not Permitted" page
- **404 errors** → "Not Found" page
- **500 errors** → Server error with traceback (dev) or generic message (prod)

### Development vs Production

```python
# Development: full traceback shown
# Production: traceback hidden, generic message shown
if frappe.conf.developer_mode:
    response["traceback"] = traceback.format_exc()
```

---

## Unified API Response System

For consistent API responses across all endpoints, use a decorator pattern:

### Exception Classes

```python
# exceptions.py
import frappe

class APIException(Exception):
    http_status_code = 500
    error_code = "INTERNAL_SERVER_ERROR"
    message = "An unexpected error occurred"
    
    def __init__(self, message=None, **kwargs):
        if not message:
            try:
                self.message = self.__class__.message.format(**kwargs)
            except (KeyError, IndexError):
                self.message = self.__class__.message
        else:
            self.message = message
        super().__init__(self.message)
    
    def to_dict(self):
        response = {
            "success": False,
            "http_status": self.http_status_code,
            "error_code": self.error_code,
            "message": self.message
        }
        if frappe.conf.developer_mode:
            import traceback
            response["traceback"] = traceback.format_exc()
        return response
    
    def respond(self):
        frappe.local.response.update(self.to_dict())
        frappe.local.response['http_status_code'] = self.http_status_code


class MissingFieldError(APIException):
    http_status_code = 400
    error_code = "400-001"
    message = "Field {placeholder} is required"


class MethodNotAllowedError(APIException):
    http_status_code = 405
    error_code = "405-001"
    message = "Method not allowed. Expected {expected_method} but received {actual_method}"


class UserNotFoundError(APIException):
    http_status_code = 404
    error_code = "404-001"
    message = "User with ID {user_id} not found"
```

### The `api_response_normalizer` Decorator

```python
# api.py
from functools import wraps
from .exceptions import APIException, MethodNotAllowedError

def api_response_normalizer(request_method=None, success_message=None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Validate HTTP method if specified
                if request_method:
                    actual = getattr(frappe.request, 'method', '').upper()
                    if actual and actual != request_method.upper():
                        raise MethodNotAllowedError(
                            expected_method=request_method,
                            actual_method=actual
                        )
                
                result = func(*args, **kwargs)
                
                # Build success response
                frappe.local.response.update({
                    "success": True,
                    "message": success_message or "Request completed successfully",
                    "data": result
                })
                frappe.local.response["http_status_code"] = 200
                
            except APIException as e:
                frappe.local.response.update(e.to_dict())
                frappe.local.response["http_status_code"] = e.http_status_code
            except Exception as e:
                api_exc = APIException(str(e))
                frappe.local.response.update(api_exc.to_dict())
                frappe.local.response["http_status_code"] = 500
        
        return wrapper
    return decorator
```

### Usage Examples

```python
@frappe.whitelist()
@api_response_normalizer(request_method="POST")
def create_user():
    data = frappe.form_dict
    
    if not data.get('username'):
        raise MissingFieldError(placeholder="username")
    
    if not data.get('email'):
        raise MissingFieldError(placeholder="email")
    
    # Create user logic...
    return {"id": 1, "username": data['username']}
```

**Success response:**
```json
{
    "success": true,
    "message": "Request completed successfully",
    "data": {"id": 1, "username": "john"}
}
```

**Error response (missing field):**
```json
{
    "success": false,
    "http_status": 400,
    "error_code": "400-001",
    "message": "Field username is required"
}
```

**Error response (wrong method):**
```json
{
    "success": false,
    "http_status": 405,
    "error_code": "405-001",
    "message": "Method not allowed. Expected POST but received GET"
}
```

### Custom Exception with Additional Data

```python
class ValidationError(APIException):
    http_status_code = 422
    error_code = "422-001"
    message = "Validation failed"
    
    def __init__(self, message=None, errors=None, **kwargs):
        super().__init__(message, **kwargs)
        self.errors = errors or []
    
    def to_dict(self):
        response = super().to_dict()
        if self.errors:
            response['errors'] = self.errors
        return response

# Usage
raise ValidationError(
    errors=[
        {"field": "email", "message": "Invalid email format"},
        {"field": "password", "message": "Password too short"}
    ]
)
```

---

## Best Practices

1. **Always whitelist** methods that need to be called from the client
2. **Use `frappe.throw`** for user-facing errors, not bare `raise`
3. **Use specific exception types** — `DoesNotExistError` for 404, `PermissionError` for 403
4. **Control response structure** with `frappe.local.response` for custom APIs
5. **Remove the default `message` wrapper** when building custom response structures
6. **Use the decorator pattern** for consistent API responses across endpoints
7. **Never expose tracebacks** in production — use `frappe.conf.developer_mode` check
