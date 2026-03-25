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


---

## 📌 Addendum: Controlling API Response Body in Frappe

### The Two Response Objects

`frappe.local.response` is the actual response object (thread-local dictionary).
`frappe.response` is a LocalProxy shortcut to `frappe.local.response`.

These are equivalent:
```python
frappe.response["message"] = "Hello"
frappe.local.response["message"] = "Hello"
```

### Default Behavior

By default, Frappe wraps return values in a `message` field:

```python
@frappe.whitelist()
def my_api():
    return "Hello World"
# Response: {"message": "Hello World"}
```

### Custom Response Structure

```python
@frappe.whitelist()
def custom_api():
    try:
        result = {"status": "success", "data": [...]}
        
        frappe.local.response["http_status_code"] = 200
        frappe.local.response["result"] = result
        frappe.local.response.pop("message", None)  # Remove default wrapper
        
    except Exception as e:
        frappe.local.response["http_status_code"] = 500
        frappe.local.response["error"] = str(e)
        frappe.local.response.pop("message", None)
```

### HTTP Status Codes

```python
frappe.local.response["http_status_code"] = 200  # Success
frappe.local.response["http_status_code"] = 400  # Bad Request
frappe.local.response["http_status_code"] = 401  # Unauthorized
frappe.local.response["http_status_code"] = 403  # Forbidden
frappe.local.response["http_status_code"] = 404  # Not Found
frappe.local.response["http_status_code"] = 500  # Internal Server Error
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

# CSV
frappe.local.response["type"] = "csv"

# PDF
frappe.local.response["type"] = "pdf"
```

### Common Patterns

```python
# Pattern 1: Standard Frappe response (auto-wrapped in "message")
@frappe.whitelist()
def get_items():
    return frappe.get_all("Item", fields=["name", "item_name"])
# Response: {"message": [{"name": "ITEM-001", ...}]}

# Pattern 2: Custom JSON structure
@frappe.whitelist()
def get_items_custom():
    items = frappe.get_all("Item", fields=["name", "item_name"])
    frappe.local.response["http_status_code"] = 200
    frappe.local.response["items"] = items
    frappe.local.response["total"] = len(items)
    frappe.local.response.pop("message", None)
# Response: {"items": [...], "total": 5}

# Pattern 3: Error response
@frappe.whitelist()
def api_with_validation():
    if not frappe.form_dict.get("required_field"):
        frappe.local.response["http_status_code"] = 400
        frappe.local.response["error"] = "Required field is missing"
        frappe.local.response.pop("message", None)
        return

# Pattern 4: File download
@frappe.whitelist()
def download_report():
    pdf_content = generate_pdf()
    frappe.local.response["type"] = "download"
    frappe.local.response["filename"] = "report.pdf"
    frappe.local.response["filecontent"] = pdf_content
```

### The LocalProxy Pattern

`frappe.response` is a `LocalProxy` — a lazy accessor that provides thread-safe access to thread-local data. Each HTTP request gets its own isolated `frappe.local`, preventing data leakage between concurrent requests.

```python
# Verify the types
print(type(frappe.response))        # <class 'werkzeug.local.LocalProxy'>
print(type(frappe.local.response))  # <class 'frappe.types.frappedict._dict'>
```

### Frappe API Patterns

```python
# Whitelisted method (accessible via /api/method/)
@frappe.whitelist()
def my_method():
    return "result"

# Allow guest access
@frappe.whitelist(allow_guest=True)
def public_api():
    return "public data"

# REST API for DocTypes (automatic)
# GET    /api/resource/Customer
# POST   /api/resource/Customer
# GET    /api/resource/Customer/CUST-001
# PUT    /api/resource/Customer/CUST-001
# DELETE /api/resource/Customer/CUST-001

# Call via JavaScript
frappe.call({
    method: "my_app.api.my_method",
    args: {param: "value"},
    callback: function(r) {
        console.log(r.message);
    }
});

// Or with xcall (returns Promise)
frappe.xcall("my_app.api.my_method", {param: "value"}).then(result => {
    console.log(result);
});
```


---

## 📌 Addendum: Frappe API — REST vs RPC, Authentication, and Architecture

### REST vs RPC: The Core Distinction

Frappe supports two primary API styles:

| API Style | Mindset | URL Pattern | Use When |
|-----------|---------|-------------|----------|
| REST | Working with "things" (nouns) | `/api/resource/DocType` | Standard CRUD on DocTypes |
| RPC | Performing "actions" (verbs) | `/api/method/function_name` | Custom business logic |

**Decision tree:**
```
Do you need real-time updates?
├─ YES → WebSocket (frappe.publish_realtime)
└─ NO → Continue...
    Are you doing CRUD on a DocType?
    ├─ YES → REST (/api/resource/DocType)
    └─ NO → RPC (/api/method/function_name)
```

### API Versioning

Frappe supports two API versions:

**V1 (Legacy):**
```
GET    /api/resource/<DocType>              # List
POST   /api/resource/<DocType>              # Create
GET    /api/resource/<DocType>/<name>       # Read
PUT    /api/resource/<DocType>/<name>       # Update
DELETE /api/resource/<DocType>/<name>       # Delete
GET    /api/method/<method_path>            # Call function
POST   /api/method/<method_path>            # Call function
```

**V2 (Current — better structured responses):**
```
GET    /api/v2/document/<DocType>                        # List
POST   /api/v2/document/<DocType>                        # Create
GET    /api/v2/document/<DocType>/<name>                 # Read
PATCH  /api/v2/document/<DocType>/<name>                 # Partial update
DELETE /api/v2/document/<DocType>/<name>                 # Delete
GET    /api/v2/document/<DocType>/<name>/copy            # Copy
GET    /api/v2/doctype/<DocType>/meta                    # Get metadata
GET    /api/v2/doctype/<DocType>/count                   # Count
GET    /api/v2/method/<method_path>                      # Call function
```

### Authentication Methods

**1. Session (Cookie-based)** — automatic for web requests:
```bash
curl -X POST "http://localhost:8000/api/method/login" \
  -d "usr=Administrator&pwd=admin" -c cookies.txt
curl -X GET "http://localhost:8000/api/resource/User" -b cookies.txt
```

**2. API Key (Token-based)** — generate from User document:
```bash
curl -X GET "http://localhost:8000/api/resource/User" \
  -H "Authorization: token api_key:api_secret"
```

**3. OAuth Bearer Token:**
```bash
curl -X GET "http://localhost:8000/api/resource/User" \
  -H "Authorization: Bearer <access_token>"
```

**4. Custom auth hooks:**
```python
# hooks.py
auth_hooks = ["my_app.auth.validate_custom_auth"]
```

### Filter Syntax

```bash
# Simple filter
?filters=[["User", "enabled", "=", 1]]

# Multiple filters (AND)
?filters=[["User", "enabled", "=", 1], ["User", "user_type", "=", "System User"]]

# JSON shorthand
?filters={"enabled": 1}
?filters={"enabled": ["!=", 0]}
```

Operators: `=`, `!=`, `>`, `<`, `>=`, `<=`, `like`, `not like`, `in`, `not in`, `is`, `is not`, `between`

### Pagination and Sorting

```bash
?fields=["name", "email", "full_name"]
?order_by=creation desc
?limit_start=0          # Offset
?limit_page_length=20   # Page size
?group_by=customer
```

### WebSocket (Real-time)

Frappe uses Socket.IO for real-time communication:

```python
# Server → Client
frappe.publish_realtime(
    event="my_event",
    message={"data": "value"},
    user=frappe.session.user
)

# Progress updates
frappe.publish_progress(
    percent=50,
    title="Processing",
    description="Halfway done"
)
```

```javascript
// Client listener
frappe.realtime.on("my_event", function(data) {
    console.log(data);
});
frappe.realtime.off("my_event");  // Unsubscribe
```

### Clean API Architecture

For maintainable APIs, separate concerns:

```
my_app/
├── api/
│   ├── v1/
│   │   ├── customers.py    # HTTP layer (request/response)
│   │   └── orders.py
│   └── v2/
│       └── orders.py
├── services/
│   ├── customer_service.py # Business logic (reusable)
│   └── order_service.py
├── utils/
│   └── validators.py       # Validation helpers
└── exceptions/
    └── api_exceptions.py   # Custom exceptions
```

Benefits: business logic in `services/` can be called from APIs, background jobs, and scheduled tasks without duplication.

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
    """10 per hour per unique email"""
    pass
```

### Version-Compatible Import

```python
# Handle API path changes between Frappe versions
try:
    from frappe.api.v1 import get_request_form_data
except ImportError:
    from frappe.api import get_request_form_data
```

### What Frappe Does NOT Support Natively

| Protocol | Support |
|----------|---------|
| REST (HTTP/JSON) | Native |
| RPC (HTTP/JSON) | Native |
| WebSocket (Socket.IO) | Native |
| GraphQL | Not supported (requires custom app) |
| gRPC | Not supported (requires custom app) |


---

## 📌 Addendum: Web Form API — Complete Reference

### What is `frappe.web_form`?

The `frappe.web_form` object is the main tool for controlling web forms (public-facing forms). It's built from three classes: `Layout → FieldGroup → WebForm`.

### Key Difference from Desk Forms

Web Forms use `frappe.ui.FieldGroup` instead of `frappe.ui.form.Form`. This means:
- Custom scripts from DocType **do not run** in Web Forms
- `get_query` filters defined in form scripts **don't apply**
- `fetch_from` functionality **doesn't work** for guest users (no API access)

### Core Methods

```javascript
// Field access
frappe.web_form.get_field("customer")          // Field object
frappe.web_form.get_input("customer")          // jQuery input element
frappe.web_form.has_field("customer")          // Boolean

// Values
frappe.web_form.get_value("customer")          // Single field value
frappe.web_form.set_value("customer", "CUST-001")  // Set value (returns Promise)
frappe.web_form.get_values()                   // All values as object
frappe.web_form.set_values({ customer: "CUST-001", date: "2024-01-01" })
frappe.web_form.clear()                        // Clear all fields

// Field properties
frappe.web_form.set_df_property("customer", "hidden", 1)
frappe.web_form.set_df_property("customer", "reqd", 1)
frappe.web_form.set_df_property("customer", "read_only", 1)

// Form actions
frappe.web_form.save()
frappe.web_form.delete_form()
frappe.web_form.discard_form()

// Events
frappe.web_form.on("customer", function(field, value) {
    // Runs when customer field changes
});
frappe.web_form.events.on("after_load", function() { });
frappe.web_form.events.on("after_save", function() { });
```

### Form State Properties

```javascript
frappe.web_form.is_new          // Creating new vs editing existing
frappe.web_form.in_edit_mode    // Edit mode
frappe.web_form.in_view_mode    // View-only mode
frappe.web_form.doc             // Current document data
frappe.web_form.doc_type        // Target DocType
frappe.web_form.name            // Web form name
frappe.web_form.fields_dict     // All fields by name
frappe.web_form.fields_list     // All fields in order
```

### Multi-Step Forms

```javascript
frappe.web_form.is_multi_step_form          // Boolean
frappe.web_form.current_section             // Current section index
frappe.web_form.page_breaks                 // jQuery page break elements
frappe.web_form.toggle_section()            // Move to next section
frappe.web_form.validate_section()          // Validate current section
frappe.web_form.is_next_section_empty(n)    // Check if section n is empty
```

### Common Patterns

```javascript
// Dynamic field visibility
frappe.web_form.on("status", function(field, value) {
    frappe.web_form.set_df_property("notes", "hidden", value !== "Rejected");
    frappe.web_form.set_df_property("notes", "reqd", value === "Rejected");
});

// Auto-fill from server
frappe.web_form.on("customer", function(field, value) {
    if (value) {
        frappe.call({
            method: "frappe.client.get_value",
            args: { doctype: "Customer", filters: { name: value }, fieldname: ["email_id", "phone"] },
            callback: (r) => {
                if (r.message) {
                    frappe.web_form.set_values({
                        email: r.message.email_id,
                        phone: r.message.phone
                    });
                }
            }
        });
    }
});

// Validation before save
frappe.web_form.on("submit", function() {
    let email = frappe.web_form.get_value("email");
    if (email && !frappe.utils.validate_email_address(email)) {
        frappe.msgprint("Invalid email");
        return false;
    }
});
```

### Fixing `fetch_from` in Web Forms

`fetch_from` doesn't work in Web Forms because they use `FieldGroup` instead of `Form`. Fix with a client script:

```javascript
frappe.ready(function() {
    setTimeout(setupChildTableFetchFrom, 2000);
});

function setupChildTableFetchFrom() {
    if (!frappe.web_form.fields_dict) return;

    Object.keys(frappe.web_form.fields_dict).forEach(fieldname => {
        const field = frappe.web_form.fields_dict[fieldname];
        if (field?.df?.fieldtype !== "Table" || !field.df.fields) return;

        const linkFields = field.df.fields.filter(f => f.fieldtype === "Link");
        linkFields.forEach(linkField => {
            const fetchFields = field.df.fields.filter(f =>
                f.fetch_from?.startsWith(linkField.fieldname + ".")
            );
            if (!fetchFields.length) return;

            const selector = `[data-fieldname="${fieldname}"]`;
            $(document).on("change blur", `${selector} input[data-fieldname="${linkField.fieldname}"]`, function() {
                const value = $(this).val()?.trim();
                const rowIndex = $(this).closest("[data-idx]").attr("data-idx");
                if (!value) return;

                const sourceFields = [...new Set(fetchFields.map(f => f.fetch_from.split(".")[1]))];
                frappe.call({
                    method: "frappe.client.get_value",
                    args: { doctype: linkField.options, fieldname: sourceFields.join(","), filters: { name: value } },
                    callback: (r) => {
                        if (r.message) {
                            fetchFields.forEach(ff => {
                                const src = ff.fetch_from.split(".")[1];
                                if (r.message[src]) {
                                    $(`${selector} [data-idx="${rowIndex}"] [data-fieldname="${ff.fieldname}"]`)
                                        .val(r.message[src]).trigger("change");
                                }
                            });
                        }
                    }
                });
            });
        });
    });
}
```

**Note:** This solution only works for logged-in users. Guest users typically don't have permission to call `frappe.client.get_value`.
