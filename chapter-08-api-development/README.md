# Chapter 8: API Development and Integration Mastery

## 🎯 Learning Objectives

By the end of this chapter, you will master:

- **How** Frappe's REST API architecture handles requests and responses
- **Why** different API patterns have specific performance characteristics
- **When** to use whitelisted methods vs direct database access
- **How** API authentication and authorization work internally
- **Advanced patterns** for building scalable API integrations
- **Performance optimization** techniques for high-volume API operations
- **Unified error handling** for consistent API responses
- **Integration requests** for external API logging and monitoring

## 📚 Chapter Topics

### 8.1 Understanding Frappe's API Architecture

**The API Request-Response Pipeline**

Frappe's API system is a sophisticated RESTful framework that handles authentication, authorization, data validation, and response formatting. Understanding its internal architecture is crucial for building high-performance, secure integrations.

#### How API Requests Are Processed

```python
# Simplified version of Frappe's API request processing
class APIRequestProcessor:
    def __init__(self):
        self.request_handlers = {}
        self.middleware_stack = []
        self.rate_limiter = RateLimiter()
        self.auth_manager = AuthenticationManager()
        self.response_formatter = ResponseFormatter()
        self.performance_monitor = APIPerformanceMonitor()
        self.error_handler = UnifiedErrorHandler()
        
        # Initialize middleware
        self.initialize_middleware()
        
        # Register routes
        self.register_routes()
    
    def initialize_middleware(self):
        """Initialize API middleware stack"""
        # Authentication middleware
        self.middleware_stack.append(AuthenticationMiddleware())
        
        # Authorization middleware
        self.middleware_stack.append(AuthorizationMiddleware())
        
        # Rate limiting middleware
        self.middleware_stack.append(RateLimitingMiddleware())
        
        # Request validation middleware
        self.middleware_stack.append(RequestValidationMiddleware())
        
        # Response formatting middleware
        self.middleware_stack.append(ResponseFormattingMiddleware())
    
    def register_routes(self):
        """Register API routes"""
        # Resource routes
        self.request_handlers['GET /api/resource/{doctype}'] = self.get_resource_list
        self.request_handlers['POST /api/resource/{doctype}'] = self.create_resource
        self.request_handlers['GET /api/resource/{doctype}/{name}'] = self.get_resource
        self.request_handlers['PUT /api/resource/{doctype}/{name}'] = self.update_resource
        self.request_handlers['DELETE /api/resource/{doctype}/{name}'] = self.delete_resource
        
        # Method routes
        self.request_handlers['POST /api/method/{method}'] = self.call_whitelisted_method
        
        # Custom routes
        self.request_handlers['GET /api/custom/{endpoint}'] = self.handle_custom_endpoint
    
    def process_request(self, request):
        """Process incoming API request"""
        start_time = time.time()
        
        try:
            # Parse request
            parsed_request = self.parse_request(request)
            
            # Apply middleware
            processed_request = self.apply_middleware(parsed_request)
            
            # Route request
            response = self.route_request(processed_request)
            
            # Format response
            formatted_response = self.response_formatter.format(response)
            
            # Track performance
            processing_time = time.time() - start_time
            self.performance_monitor.track_request(
                endpoint=parsed_request.endpoint,
                method=parsed_request.method,
                processing_time=processing_time,
                status=response.status_code
            )
            
            return formatted_response
            
        except APIException as e:
            # Handle API exceptions
            return self.handle_api_exception(e, start_time)
        except Exception as e:
            # Handle unexpected exceptions
            return self.handle_unexpected_exception(e, start_time)
    
    def parse_request(self, request):
        """Parse incoming request"""
        parsed = ParsedRequest()
        
        # Extract method
        parsed.method = request.method
        parsed.endpoint = request.path
        parsed.headers = dict(request.headers)
        parsed.body = request.get_data(as_text=True)
        parsed.query_params = request.args.to_dict()
        
        # Parse JSON body
        if parsed.body and parsed.headers.get('Content-Type') == 'application/json':
            try:
                parsed.data = json.loads(parsed.body)
            except json.JSONDecodeError:
                raise APIException("Invalid JSON in request body", 400)
        
        # Extract user from headers
        parsed.user = self.extract_user_from_headers(parsed.headers)
        
        return parsed
    
    def apply_middleware(self, request):
        """Apply middleware stack to request"""
        processed_request = request
        
        for middleware in self.middleware_stack:
            try:
                processed_request = middleware.process(processed_request)
            except MiddlewareException as e:
                raise APIException(f"Middleware error: {str(e)}", 401)
        
        return processed_request
    
    def route_request(self, request):
        """Route request to appropriate handler"""
        # Find matching route
        handler = self.find_handler(request.method, request.endpoint)
        
        if not handler:
            raise APIException("Endpoint not found", 404)
        
        # Execute handler
        try:
            return handler(request)
        except Exception as e:
            raise APIException(f"Handler error: {str(e)}", 500)
    
    def find_handler(self, method, endpoint):
        """Find appropriate handler for method and endpoint"""
        # Direct match
        key = f"{method} {endpoint}"
        if key in self.request_handlers:
            return self.request_handlers[key]
        
        # Pattern matching
        for pattern, handler in self.request_handlers.items():
            if self.match_pattern(pattern, method, endpoint):
                return handler
        
        return None
    
    def match_pattern(self, pattern, method, endpoint):
        """Match endpoint pattern"""
        pattern_method, pattern_endpoint = pattern.split(' ', 1)
        
        if pattern_method != method:
            return False
        
        # Convert pattern to regex
        regex_pattern = pattern_endpoint.replace('{', '(?P<').replace('}', '>[^/]+)')
        regex_pattern = f"^{regex_pattern}$"
        
        match = re.match(regex_pattern, endpoint)
        return match is not None
    
    def get_resource_list(self, request):
        """Handle GET /api/resource/{doctype}"""
        doctype = self.extract_doctype_from_endpoint(request.endpoint)
        
        # Validate permissions
        if not self.auth_manager.has_permission(request.user, doctype, 'read'):
            raise APIException("Permission denied", 403)
        
        # Parse query parameters
        filters = request.query_params.get('filters', '{}')
        fields = request.query_params.get('fields', '["*"]')
        limit = int(request.query_params.get('limit', 20))
        start = int(request.query_params.get('start', 0))
        order_by = request.query_params.get('order_by', 'modified desc')
        
        try:
            filters_dict = json.loads(filters)
            fields_list = json.loads(fields)
        except json.JSONDecodeError:
            raise APIException("Invalid filters or fields parameter", 400)
        
        # Query database
        docs = frappe.get_all(
            doctype,
            filters=filters_dict,
            fields=fields_list,
            limit=limit,
            start=start,
            order_by=order_by
        )
        
        return APIResponse(
            data=docs,
            message=f"Retrieved {len(docs)} {doctype} records"
        )
    
    def create_resource(self, request):
        """Handle POST /api/resource/{doctype}"""
        doctype = self.extract_doctype_from_endpoint(request.endpoint)
        
        # Validate permissions
        if not self.auth_manager.has_permission(request.user, doctype, 'create'):
            raise APIException("Permission denied", 403)
        
        # Validate request data
        if not request.data:
            raise APIException("Request body is required", 400)
        
        # Create document
        try:
            doc = frappe.get_doc(request.data)
            doc.insert()
            
            return APIResponse(
                data=doc.as_dict(),
                message=f"{doctype} created successfully"
            )
        except Exception as e:
            raise APIException(f"Failed to create {doctype}: {str(e)}", 400)
    
    def get_resource(self, request):
        """Handle GET /api/resource/{doctype}/{name}"""
        doctype, name = self.extract_doctype_and_name(request.endpoint)
        
        # Validate permissions
        if not self.auth_manager.has_permission(request.user, doctype, 'read'):
            raise APIException("Permission denied", 403)
        
        # Get document
        try:
            doc = frappe.get_doc(doctype, name)
            return APIResponse(
                data=doc.as_dict(),
                message=f"{doctype} retrieved successfully"
            )
        except Exception as e:
            raise APIException(f"Failed to retrieve {doctype}: {str(e)}", 404)
    
    def update_resource(self, request):
        """Handle PUT /api/resource/{doctype}/{name}"""
        doctype, name = self.extract_doctype_and_name(request.endpoint)
        
        # Validate permissions
        if not self.auth_manager.has_permission(request.user, doctype, 'write'):
            raise APIException("Permission denied", 403)
        
        # Validate request data
        if not request.data:
            raise APIException("Request body is required", 400)
        
        # Update document
        try:
            doc = frappe.get_doc(doctype, name)
            
            # Update fields
            for field, value in request.data.items():
                if field in doc:
                    doc.set(field, value)
            
            doc.save()
            
            return APIResponse(
                data=doc.as_dict(),
                message=f"{doctype} updated successfully"
            )
        except Exception as e:
            raise APIException(f"Failed to update {doctype}: {str(e)}", 400)
    
    def delete_resource(self, request):
        """Handle DELETE /api/resource/{doctype}/{name}"""
        doctype, name = self.extract_doctype_and_name(request.endpoint)
        
        # Validate permissions
        if not self.auth_manager.has_permission(request.user, doctype, 'delete'):
            raise APIException("Permission denied", 403)
        
        # Delete document
        try:
            frappe.delete_doc(doctype, name)
            
            return APIResponse(
                message=f"{doctype} deleted successfully"
            )
        except Exception as e:
            raise APIException(f"Failed to delete {doctype}: {str(e)}", 400)
    
    def call_whitelisted_method(self, request):
        """Handle POST /api/method/{method}"""
        method_name = self.extract_method_from_endpoint(request.endpoint)
        
        # Validate method is whitelisted
        if not self.is_whitelisted_method(method_name):
            raise APIException("Method not whitelisted", 403)
        
        # Execute method
        try:
            args = request.data or {}
            result = frappe.call(method_name, **args)
            
            return APIResponse(
                data=result,
                message=f"Method {method_name} executed successfully"
            )
        except Exception as e:
            raise APIException(f"Method execution failed: {str(e)}", 500)
    
    def extract_doctype_from_endpoint(self, endpoint):
        """Extract doctype from endpoint"""
        parts = endpoint.split('/')
        if len(parts) >= 4 and parts[2] == 'resource':
            return parts[3]
        return None
    
    def extract_doctype_and_name(self, endpoint):
        """Extract doctype and name from endpoint"""
        parts = endpoint.split('/')
        if len(parts) >= 5 and parts[2] == 'resource':
            return parts[3], parts[4]
        return None, None
    
    def extract_method_from_endpoint(self, endpoint):
        """Extract method name from endpoint"""
        parts = endpoint.split('/')
        if len(parts) >= 4 and parts[2] == 'method':
            return parts[3]
        return None
    
    def extract_user_from_headers(self, headers):
        """Extract user from request headers"""
        # Check for API key
        api_key = headers.get('X-API-Key')
        api_secret = headers.get('X-API-Secret')
        
        if api_key and api_secret:
            return self.auth_manager.authenticate_with_api_key(api_key, api_secret)
        
        # Check for session token
        session_token = headers.get('Authorization')
        if session_token and session_token.startswith('Bearer '):
            return self.auth_manager.authenticate_with_token(session_token[7:])
        
        # Check for basic auth
        auth_header = headers.get('Authorization')
        if auth_header and auth_header.startswith('Basic '):
            return self.auth_manager.authenticate_with_basic(auth_header[6:])
        
        return None
    
    def handle_api_exception(self, exception, start_time):
        """Handle API exceptions"""
        processing_time = time.time() - start_time
        
        self.performance_monitor.track_error(
            endpoint=exception.endpoint or 'unknown',
            method=exception.method or 'unknown',
            processing_time=processing_time,
            error=str(exception)
        )
        
        return APIResponse(
            success=False,
            message=exception.message,
            error_code=exception.code
        )
    
    def handle_unexpected_exception(self, exception, start_time):
        """Handle unexpected exceptions"""
        processing_time = time.time() - start_time
        
        self.performance_monitor.track_error(
            endpoint='unknown',
            method='unknown',
            processing_time=processing_time,
            error=str(exception)
        )
        
        return APIResponse(
            success=False,
            message="Internal server error",
            error_code=500
        )
```

#### Authentication and Authorization System

```python
# API authentication and authorization
class AuthenticationManager:
    def __init__(self):
        self.api_keys = {}
        self.session_tokens = {}
        self.rate_limits = {}
        self.permission_cache = {}
    
    def authenticate_with_api_key(self, api_key, api_secret):
        """Authenticate using API key and secret"""
        # Validate API key
        if not self.validate_api_key(api_key, api_secret):
            raise APIException("Invalid API key or secret", 401)
        
        # Get user from API key
        user = self.get_user_from_api_key(api_key)
        
        if not user:
            raise APIException("API key not found", 401)
        
        # Check rate limits
        self.check_rate_limits(user, 'api_key')
        
        return user
    
    def authenticate_with_token(self, token):
        """Authenticate using session token"""
        # Validate token
        if not self.validate_token(token):
            raise APIException("Invalid token", 401)
        
        # Get user from token
        user = self.get_user_from_token(token)
        
        if not user:
            raise APIException("Token not found", 401)
        
        # Check rate limits
        self.check_rate_limits(user, 'token')
        
        return user
    
    def authenticate_with_basic(self, auth_string):
        """Authenticate using basic auth"""
        try:
            # Decode base64
            import base64
            decoded = base64.b64decode(auth_string).decode('utf-8')
            
            # Split username and password
            username, password = decoded.split(':', 1)
            
            # Validate credentials
            if not self.validate_credentials(username, password):
                raise APIException("Invalid credentials", 401)
            
            # Check rate limits
            self.check_rate_limits(username, 'basic')
            
            return username
            
        except Exception:
            raise APIException("Invalid basic auth format", 401)
    
    def validate_api_key(self, api_key, api_secret):
        """Validate API key and secret"""
        # Check in database
        key_doc = frappe.db.get_value('API Key', {'api_key': api_key}, ['api_secret', 'user'])
        
        if not key_doc:
            return False
        
        stored_secret, user = key_doc
        
        # Compare secrets (using constant-time comparison)
        return secrets.compare_digest(stored_secret.encode(), api_secret.encode())
    
    def validate_token(self, token):
        """Validate session token"""
        # Check in cache
        if token in self.session_tokens:
            token_data = self.session_tokens[token]
            
            # Check expiration
            if token_data['expires_at'] > time.time():
                return True
            else:
                # Remove expired token
                del self.session_tokens[token]
                return False
        
        # Check in database
        token_doc = frappe.db.get_value('Session Token', {'token': token}, ['expires_at'])
        
        if not token_doc:
            return False
        
        expires_at = token_doc
        
        # Check expiration
        if expires_at > time.time():
            # Cache token
            self.session_tokens[token] = {
                'expires_at': expires_at,
                'user': frappe.db.get_value('Session Token', {'token': token}, 'user')
            }
            return True
        else:
            # Remove expired token
            frappe.delete_doc('Session Token', token)
            return False
    
    def validate_credentials(self, username, password):
        """Validate user credentials"""
        try:
            user = frappe.auth.authenticate(username, password)
            return user is not None
        except Exception:
            return False
    
    def get_user_from_api_key(self, api_key):
        """Get user from API key"""
        return frappe.db.get_value('API Key', {'api_key': api_key}, 'user')
    
    def get_user_from_token(self, token):
        """Get user from token"""
        if token in self.session_tokens:
            return self.session_tokens[token]['user']
        
        return frappe.db.get_value('Session Token', {'token': token}, 'user')
    
    def has_permission(self, user, doctype, permission):
        """Check if user has permission for doctype"""
        cache_key = f"{user}_{doctype}_{permission}"
        
        # Check cache
        if cache_key in self.permission_cache:
            return self.permission_cache[cache_key]
        
        # Check permissions
        has_perm = frappe.has_permission(doctype, permission, user=user)
        
        # Cache result
        self.permission_cache[cache_key] = has_perm
        
        return has_perm
    
    def check_rate_limits(self, user, auth_type):
        """Check rate limits for user"""
        key = f"{user}_{auth_type}"
        
        # Get rate limit settings
        rate_limit = self.get_rate_limit(user, auth_type)
        
        if not rate_limit:
            return
        
        # Check current usage
        current_usage = self.rate_limits.get(key, {
            'count': 0,
            'reset_time': time.time() + rate_limit['window']
        })
        
        # Reset window if expired
        if current_usage['reset_time'] <= time.time():
            current_usage = {
                'count': 0,
                'reset_time': time.time() + rate_limit['window']
            }
        
        # Check limit
        if current_usage['count'] >= rate_limit['limit']:
            raise APIException("Rate limit exceeded", 429)
        
        # Increment usage
        current_usage['count'] += 1
        self.rate_limits[key] = current_usage
    
    def get_rate_limit(self, user, auth_type):
        """Get rate limit for user and auth type"""
        # Default rate limits
        default_limits = {
            'api_key': {'limit': 1000, 'window': 3600},  # 1000 requests per hour
            'token': {'limit': 500, 'window': 3600},       # 500 requests per hour
            'basic': {'limit': 100, 'window': 3600}        # 100 requests per hour
        }
        
        # Get user-specific limits
        user_limits = frappe.db.get_value('User', user, 'api_rate_limits')
        
        if user_limits:
            try:
                limits = json.loads(user_limits)
                return limits.get(auth_type, default_limits.get(auth_type))
            except json.JSONDecodeError:
                pass
        
        return default_limits.get(auth_type)
```

#### Response Formatting System

```python
# API response formatting
class ResponseFormatter:
    def __init__(self):
        self.formats = {
            'json': self.format_json,
            'xml': self.format_xml,
            'csv': self.format_csv
        }
    
    def format(self, response, format_type='json'):
        """Format response according to requested format"""
        formatter = self.formats.get(format_type, self.format_json)
        return formatter(response)
    
    def format_json(self, response):
        """Format response as JSON"""
        return {
            'success': response.success,
            'message': response.message,
            'data': response.data,
            'error_code': getattr(response, 'error_code', None),
            'timestamp': time.time()
        }
    
    def format_xml(self, response):
        """Format response as XML"""
        import xml.etree.ElementTree as ET
        
        root = ET.Element('response')
        
        # Add success
        success_elem = ET.SubElement(root, 'success')
        success_elem.text = str(response.success)
        
        # Add message
        message_elem = ET.SubElement(root, 'message')
        message_elem.text = response.message
        
        # Add data
        if response.data:
            data_elem = ET.SubElement(root, 'data')
            self._dict_to_xml(response.data, data_elem)
        
        # Add error code
        if hasattr(response, 'error_code'):
            error_elem = ET.SubElement(root, 'error_code')
            error_elem.text = str(response.error_code)
        
        # Add timestamp
        timestamp_elem = ET.SubElement(root, 'timestamp')
        timestamp_elem.text = str(time.time())
        
        return ET.tostring(root, encoding='unicode')
    
    def format_csv(self, response):
        """Format response as CSV"""
        import csv
        import io
        
        if not response.data:
            return "No data available"
        
        # Handle different data types
        if isinstance(response.data, list):
            if len(response.data) == 0:
                return "No data available"
            
            # Get headers from first item
            if isinstance(response.data[0], dict):
                headers = list(response.data[0].keys())
                
                output = io.StringIO()
                writer = csv.DictWriter(output, fieldnames=headers)
                writer.writeheader()
                
                for item in response.data:
                    writer.writerow(item)
                
                return output.getvalue()
            else:
                # Simple list
                output = io.StringIO()
                writer = csv.writer(output)
                writer.writerow(['value'])
                
                for item in response.data:
                    writer.writerow([item])
                
                return output.getvalue()
        
        elif isinstance(response.data, dict):
            # Single item
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=list(response.data.keys()))
            writer.writeheader()
            writer.writerow(response.data)
            
            return output.getvalue()
        
        return "Unsupported data format for CSV"
    
    def _dict_to_xml(self, data, parent_element):
        """Convert dictionary to XML"""
        if isinstance(data, dict):
            for key, value in data.items():
                child = ET.SubElement(parent_element, key)
                self._dict_to_xml(value, child)
        elif isinstance(data, list):
            for item in data:
                child = ET.SubElement(parent_element, 'item')
                self._dict_to_xml(item, child)
        else:
            parent_element.text = str(data)

# API response class
class APIResponse:
    def __init__(self, success=True, message="", data=None, status_code=200):
        self.success = success
        self.message = message
        self.data = data
        self.status_code = status_code

# API exception class
class APIException(Exception):
    def __init__(self, message, code=500, endpoint=None, method=None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.endpoint = endpoint
        self.method = method

# Middleware exception class
class MiddlewareException(Exception):
    pass

# Parsed request class
class ParsedRequest:
    def __init__(self):
        self.method = None
        self.endpoint = None
        self.headers = {}
        self.body = None
        self.data = None
        self.query_params = {}
        self.user = None
```

### 8.2 Building Whitelisted API Methods

#### Creating Secure API Methods

```python
# Whitelisted API method examples
@frappe.whitelist()
def get_customer_balance(customer):
    """Get customer balance with validation"""
    # Validate input
    if not customer:
        frappe.throw("Customer is required")
    
    # Check if customer exists
    if not frappe.db.exists("Customer", customer):
        frappe.throw("Customer not found")
    
    # Get balance
    balance = frappe.db.get_value("Customer", customer, "outstanding_balance")
    
    return {
        "customer": customer,
        "balance": balance,
        "currency": frappe.db.get_default("currency")
    }

@frappe.whitelist()
def calculate_shipping_cost(items, shipping_address):
    """Calculate shipping cost with complex logic"""
    # Validate inputs
    if not items or not isinstance(items, list):
        frappe.throw("Items list is required")
    
    if not shipping_address:
        frappe.throw("Shipping address is required")
    
    # Get shipping zone
    shipping_zone = get_shipping_zone(shipping_address)
    
    # Calculate total weight
    total_weight = 0
    total_value = 0
    
    for item in items:
        if not item.get("item_code") or not item.get("qty"):
            continue
        
        # Get item details
        item_doc = frappe.get_doc("Item", item["item_code"])
        
        # Calculate weight and value
        weight = item_doc.weight_per_unit * item["qty"]
        value = item_doc.standard_rate * item["qty"]
        
        total_weight += weight
        total_value += value
    
    # Get shipping rates
    shipping_rates = get_shipping_rates(shipping_zone)
    
    # Calculate cost based on weight and value
    weight_cost = total_weight * shipping_rates.get("rate_per_kg", 0)
    value_cost = total_value * shipping_rates.get("rate_per_value", 0)
    
    # Apply minimum charge
    min_charge = shipping_rates.get("minimum_charge", 0)
    total_cost = max(weight_cost + value_cost, min_charge)
    
    return {
        "shipping_zone": shipping_zone,
        "total_weight": total_weight,
        "total_value": total_value,
        "shipping_cost": total_cost,
        "currency": frappe.db.get_default("currency")
    }

@frappe.whitelist()
def create_sales_invoice_from_order(sales_order):
    """Create sales invoice from sales order"""
    # Validate input
    if not sales_order:
        frappe.throw("Sales order is required")
    
    # Check if sales order exists
    if not frappe.db.exists("Sales Order", sales_order):
        frappe.throw("Sales order not found")
    
    # Check if invoice already exists
    existing_invoice = frappe.db.get_value("Sales Invoice", 
                                          {"sales_order": sales_order, "docstatus": ["!=", 2]}, 
                                          "name")
    if existing_invoice:
        frappe.throw(f"Sales Invoice {existing_invoice} already exists for this order")
    
    # Get sales order
    order_doc = frappe.get_doc("Sales Order", sales_order)
    
    # Check if order is submitted
    if order_doc.docstatus != 1:
        frappe.throw("Sales order must be submitted before creating invoice")
    
    # Create invoice
    invoice = frappe.new_doc("Sales Invoice")
    
    # Copy customer and billing details
    invoice.customer = order_doc.customer
    invoice.customer_name = order_doc.customer_name
    invoice.posting_date = frappe.utils.nowdate()
    invoice.due_date = frappe.utils.add_to_date(frappe.utils.nowdate(), days=30)
    
    # Copy items
    for item in order_doc.items:
        invoice_item = invoice.append("items", {})
        invoice_item.item_code = item.item_code
        invoice_item.item_name = item.item_name
        invoice_item.description = item.description
        invoice_item.qty = item.qty
        invoice_item.rate = item.rate
        invoice_item.amount = item.amount
        
        # Copy delivery details
        if hasattr(item, 'delivered_qty'):
            invoice_item.qty = item.delivered_qty
            invoice_item.amount = invoice_item.qty * invoice_item.rate
    
    # Calculate totals
    invoice.calculate_taxes_and_totals()
    
    # Save invoice
    invoice.insert()
    
    return {
        "invoice": invoice.name,
        "message": "Sales invoice created successfully"
    }

@frappe.whitelist()
def get_item_stock(item_code, warehouse=None):
    """Get item stock information"""
    # Validate input
    if not item_code:
        frappe.throw("Item code is required")
    
    # Check if item exists
    if not frappe.db.exists("Item", item_code):
        frappe.throw("Item not found")
    
    # Get stock balance
    if warehouse:
        stock_balance = frappe.db.get_value("Bin", {"item_code": item_code, "warehouse": warehouse}, "actual_qty")
        stock_balance = stock_balance or 0
    else:
        # Get total stock across all warehouses
        stock_balance = frappe.db.sql("""
            SELECT SUM(actual_qty) as total_stock
            FROM `tabBin`
            WHERE item_code = %s
        """, (item_code,), as_dict=True)
        
        stock_balance = stock_balance[0].total_stock if stock_balance else 0
    
    # Get item details
    item_doc = frappe.get_doc("Item", item_code)
    
    return {
        "item_code": item_code,
        "item_name": item_doc.item_name,
        "stock_balance": stock_balance,
        "stock_uom": item_doc.stock_uom,
        "warehouse": warehouse,
        "last_updated": frappe.utils.now()
    }

@frappe.whitelist()
def bulk_update_item_prices(items, price_list):
    """Bulk update item prices"""
    # Validate inputs
    if not items or not isinstance(items, list):
        frappe.throw("Items list is required")
    
    if not price_list:
        frappe.throw("Price list is required")
    
    # Check if price list exists
    if not frappe.db.exists("Price List", price_list):
        frappe.throw("Price list not found")
    
    # Start transaction
    frappe.db.begin()
    
    try:
        updated_items = []
        
        for item_data in items:
            item_code = item_data.get("item_code")
            new_price = item_data.get("price")
            
            if not item_code or new_price is None:
                continue
            
            # Check if item exists
            if not frappe.db.exists("Item", item_code):
                continue
            
            # Update or create price
            price_name = frappe.db.get_value("Item Price", 
                                           {"item_code": item_code, "price_list": price_list}, 
                                           "name")
            
            if price_name:
                # Update existing price
                price_doc = frappe.get_doc("Item Price", price_name)
                price_doc.price_list_rate = new_price
                price_doc.save()
            else:
                # Create new price
                price_doc = frappe.new_doc("Item Price")
                price_doc.item_code = item_code
                price_doc.price_list = price_list
                price_doc.price_list_rate = new_price
                price_doc.insert()
            
            updated_items.append({
                "item_code": item_code,
                "price": new_price
            })
        
        # Commit transaction
        frappe.db.commit()
        
        return {
            "updated_items": updated_items,
            "message": f"Updated {len(updated_items)} item prices"
        }
        
    except Exception as e:
        # Rollback transaction
        frappe.db.rollback()
        frappe.throw(f"Failed to update item prices: {str(e)}")

# Helper functions
def get_shipping_zone(address):
    """Get shipping zone for address"""
    # This is a simplified example
    # In real implementation, you would have complex logic to determine shipping zones
    
    if "USA" in address or "United States" in address:
        return "USA"
    elif "Canada" in address:
        return "Canada"
    elif "Europe" in address:
        return "Europe"
    else:
        return "International"

def get_shipping_rates(shipping_zone):
    """Get shipping rates for zone"""
    # This is a simplified example
    # In real implementation, you would fetch from database or external service
    
    rates = {
        "USA": {
            "rate_per_kg": 5.0,
            "rate_per_value": 0.01,
            "minimum_charge": 10.0
        },
        "Canada": {
            "rate_per_kg": 7.0,
            "rate_per_value": 0.015,
            "minimum_charge": 15.0
        },
        "Europe": {
            "rate_per_kg": 8.0,
            "rate_per_value": 0.02,
            "minimum_charge": 20.0
        },
        "International": {
            "rate_per_kg": 12.0,
            "rate_per_value": 0.03,
            "minimum_charge": 30.0
        }
    }
    
    return rates.get(shipping_zone, rates["International"])
```

#### Advanced API Method Patterns

```python
# Advanced API method patterns
@frappe.whitelist()
def complex_business_logic(parameters):
    """Complex business logic with multiple steps"""
    # Validate parameters
    required_params = ['customer', 'items', 'payment_terms']
    for param in required_params:
        if not parameters.get(param):
            frappe.throw(f"{param} is required")
    
    # Step 1: Validate customer
    customer = parameters['customer']
    if not frappe.db.exists("Customer", customer):
        frappe.throw("Customer not found")
    
    # Step 2: Validate items
    items = parameters['items']
    for item in items:
        if not frappe.db.exists("Item", item['item_code']):
            frappe.throw(f"Item {item['item_code']} not found")
        
        # Check stock
        stock = frappe.db.get_value("Bin", {"item_code": item['item_code']}, "actual_qty")
        if stock < item.get('qty', 0):
            frappe.throw(f"Insufficient stock for item {item['item_code']}")
    
    # Step 3: Calculate pricing
    pricing = calculate_complex_pricing(items, customer)
    
    # Step 4: Apply business rules
    business_rules = apply_business_rules(pricing, parameters)
    
    # Step 5: Generate result
    result = {
        'pricing': pricing,
        'business_rules': business_rules,
        'recommendations': generate_recommendations(pricing, business_rules)
    }
    
    return result

@frappe.whitelist()
def batch_operation(operations):
    """Batch multiple operations in a single call"""
    # Validate operations
    if not operations or not isinstance(operations, list):
        frappe.throw("Operations list is required")
    
    # Start transaction
    frappe.db.begin()
    
    try:
        results = []
        
        for operation in operations:
            op_type = operation.get('type')
            op_data = operation.get('data')
            
            if op_type == 'create_customer':
                result = create_customer_operation(op_data)
            elif op_type == 'create_item':
                result = create_item_operation(op_data)
            elif op_type == 'update_price':
                result = update_price_operation(op_data)
            else:
                result = {'error': f'Unknown operation type: {op_type}'}
            
            results.append(result)
        
        # Commit transaction
        frappe.db.commit()
        
        return {
            'results': results,
            'success_count': len([r for r in results if 'error' not in r]),
            'error_count': len([r for r in results if 'error' in r])
        }
        
    except Exception as e:
        # Rollback transaction
        frappe.db.rollback()
        frappe.throw(f"Batch operation failed: {str(e)}")

@frappe.whitelist()
def async_operation(operation_type, parameters):
    """Start async operation and return job ID"""
    # Validate operation type
    valid_operations = ['generate_report', 'process_data', 'send_emails']
    if operation_type not in valid_operations:
        frappe.throw(f"Invalid operation type: {operation_type}")
    
    # Create job
    job_id = frappe.generate_hash(length=10)
    
    # Enqueue job
    frappe.enqueue(
        f'my_app.api.process_{operation_type}',
        queue='default',
        job_id=job_id,
        parameters=parameters
    )
    
    return {
        'job_id': job_id,
        'status': 'queued',
        'message': f'{operation_type} operation queued for processing'
    }

@frappe.whitelist()
def get_job_status(job_id):
    """Get status of async job"""
    # Get job from queue
    job = frappe.get_doc('RQ Job', job_id)
    
    if not job:
        frappe.throw("Job not found")
    
    return {
        'job_id': job_id,
        'status': job.status,
        'created_at': job.creation,
        'started_at': job.started_at,
        'ended_at': job.ended_at,
        'result': job.result if job.status == 'finished' else None,
        'error': job.error if job.status == 'failed' else None
    }

# Operation helpers
def calculate_complex_pricing(items, customer):
    """Calculate complex pricing based on multiple factors"""
    pricing = {}
    
    # Get customer pricing rules
    customer_pricing = frappe.db.get_value("Customer", customer, "pricing_rule")
    
    # Get item prices
    for item in items:
        item_code = item['item_code']
        qty = item.get('qty', 1)
        
        # Base price
        base_price = frappe.db.get_value("Item", item_code, "standard_rate")
        
        # Apply customer-specific pricing
        if customer_pricing:
            customer_price = frappe.db.get_value("Item Price", 
                                               {"item_code": item_code, "price_list": customer_pricing}, 
                                               "price_list_rate")
            if customer_price:
                base_price = customer_price
        
        # Apply quantity discounts
        discounted_price = apply_quantity_discount(base_price, qty)
        
        # Apply seasonal discounts
        seasonal_price = apply_seasonal_discount(discounted_price, item_code)
        
        pricing[item_code] = {
            'base_price': base_price,
            'discounted_price': discounted_price,
            'seasonal_price': seasonal_price,
            'final_price': seasonal_price,
            'total_price': seasonal_price * qty
        }
    
    return pricing

def apply_business_rules(pricing, parameters):
    """Apply business rules to pricing"""
    rules = {}
    
    # Minimum order value
    total_value = sum(item['total_price'] for item in pricing.values())
    min_order_value = frappe.db.get_single_value("Selling Settings", "min_order_value")
    
    if total_value < min_order_value:
        rules['min_order_warning'] = f"Order value {total_value} is below minimum {min_order_value}"
    
    # Credit limit check
    customer = parameters['customer']
    credit_limit = frappe.db.get_value("Customer", customer, "credit_limit")
    current_balance = frappe.db.get_value("Customer", customer, "outstanding_balance")
    
    if credit_limit and (current_balance + total_value) > credit_limit:
        rules['credit_limit_warning'] = "Order exceeds customer credit limit"
    
    # Payment terms validation
    payment_terms = parameters.get('payment_terms')
    if payment_terms:
        terms_doc = frappe.get_doc("Payment Terms", payment_terms)
        if terms_doc.due_date_based_on == "Delivery Date" and total_value > 10000:
            rules['payment_terms_warning'] = "High-value orders require advance payment"
    
    return rules

def generate_recommendations(pricing, rules):
    """Generate recommendations based on pricing and rules"""
    recommendations = []
    
    # Upsell recommendations
    total_value = sum(item['total_price'] for item in pricing.values())
    if total_value < 5000:
        recommendations.append({
            'type': 'upsell',
            'message': 'Add more items to qualify for free shipping',
            'target_value': 5000
        })
    
    # Payment recommendations
    if 'credit_limit_warning' in rules:
        recommendations.append({
            'type': 'payment',
            'message': 'Consider advance payment to avoid credit limit issues'
        })
    
    # Bulk order recommendations
    if len(pricing) > 10:
        recommendations.append({
            'type': 'bulk',
            'message': 'Consider bulk pricing for large orders'
        })
    
    return recommendations
```

### 8.3 API Performance Optimization

#### Caching Strategies

```python
# API caching strategies
class APICacheManager:
    def __init__(self):
        self.cache = frappe.cache()
        self.cache_ttl = {
            'customer_data': 300,      # 5 minutes
            'item_data': 600,          # 10 minutes
            'pricing_data': 1800,      # 30 minutes
            'stock_data': 60,          # 1 minute
            'reports': 3600            # 1 hour
        }
    
    def get_cached_data(self, key, data_type):
        """Get cached data"""
        cache_key = f"api:{data_type}:{key}"
        
        # Try to get from cache
        cached_data = self.cache.get(cache_key)
        
        if cached_data:
            return json.loads(cached_data)
        
        return None
    
    def set_cached_data(self, key, data_type, data):
        """Set cached data"""
        cache_key = f"api:{data_type}:{key}"
        ttl = self.cache_ttl.get(data_type, 300)
        
        # Convert to JSON and cache
        json_data = json.dumps(data, default=str)
        self.cache.set(cache_key, json_data, expires_in_sec=ttl)
    
    def invalidate_cache(self, key, data_type):
        """Invalidate cached data"""
        cache_key = f"api:{data_type}:{key}"
        self.cache.delete(cache_key)
    
    def invalidate_pattern(self, pattern):
        """Invalidate cache by pattern"""
        # This would require Redis pattern matching
        # For simplicity, we'll clear all cache
        self.cache.clear()

# Cached API method
@frappe.whitelist()
def get_customer_data_cached(customer):
    """Get customer data with caching"""
    cache_manager = APICacheManager()
    
    # Try to get from cache
    cached_data = cache_manager.get_cached_data(customer, 'customer_data')
    
    if cached_data:
        return cached_data
    
    # Get from database
    customer_doc = frappe.get_doc("Customer", customer)
    
    data = {
        'customer': customer,
        'customer_name': customer_doc.customer_name,
        'customer_group': customer_doc.customer_group,
        'territory': customer_doc.territory,
        'credit_limit': customer_doc.credit_limit,
        'outstanding_balance': customer_doc.outstanding_balance,
        'cached': False
    }
    
    # Cache the data
    cache_manager.set_cached_data(customer, 'customer_data', data)
    
    return data

# Cache invalidation in hooks
def on_customer_update(doc, method):
    """Invalidate customer cache when customer is updated"""
    cache_manager = APICacheManager()
    cache_manager.invalidate_cache(doc.name, 'customer_data')

def on_item_update(doc, method):
    """Invalidate item cache when item is updated"""
    cache_manager = APICacheManager()
    cache_manager.invalidate_cache(doc.name, 'item_data')
    cache_manager.invalidate_pattern('pricing_data')
```

#### Batch Operations and Pagination

```python
# Batch operations and pagination
@frappe.whitelist()
def get_paginated_data(doctype, page=1, page_length=20, filters=None, fields=None):
    """Get paginated data with performance optimization"""
    # Validate inputs
    if not frappe.db.exists("DocType", doctype):
        frappe.throw(f"DocType {doctype} not found")
    
    # Parse filters and fields
    try:
        filters_dict = json.loads(filters) if filters else {}
        fields_list = json.loads(fields) if fields else ['*']
    except json.JSONDecodeError:
        frappe.throw("Invalid filters or fields JSON")
    
    # Calculate offset
    offset = (page - 1) * page_length
    
    # Get total count
    total_count = frappe.db.count(doctype, filters=filters_dict)
    
    # Get data
    data = frappe.get_all(
        doctype,
        filters=filters_dict,
        fields=fields_list,
        limit=page_length,
        start=offset,
        order_by="modified desc"
    )
    
    # Calculate pagination info
    total_pages = (total_count + page_length - 1) // page_length
    has_next = page < total_pages
    has_prev = page > 1
    
    return {
        'data': data,
        'pagination': {
            'page': page,
            'page_length': page_length,
            'total_count': total_count,
            'total_pages': total_pages,
            'has_next': has_next,
            'has_prev': has_prev
        }
    }

@frappe.whitelist()
def bulk_create_records(doctype, records):
    """Bulk create records with performance optimization"""
    # Validate inputs
    if not frappe.db.exists("DocType", doctype):
        frappe.throw(f"DocType {doctype} not found")
    
    if not records or not isinstance(records, list):
        frappe.throw("Records list is required")
    
    # Validate records
    valid_records = []
    for record in records:
        if not record.get('name'):
            record['name'] = frappe.generate_hash(length=10)
        
        record['doctype'] = doctype
        valid_records.append(record)
    
    # Use bulk insert
    try:
        frappe.db.bulk_insert(doctype, valid_records)
        
        return {
            'success': True,
            'created_count': len(valid_records),
            'message': f"Created {len(valid_records)} {doctype} records"
        }
        
    except Exception as e:
        frappe.throw(f"Bulk insert failed: {str(e)}")

@frappe.whitelist()
def bulk_update_records(doctype, updates):
    """Bulk update records with performance optimization"""
    # Validate inputs
    if not frappe.db.exists("DocType", doctype):
        frappe.throw(f"DocType {doctype} not found")
    
    if not updates or not isinstance(updates, list):
        frappe.throw("Updates list is required")
    
    # Start transaction
    frappe.db.begin()
    
    try:
        updated_count = 0
        
        for update in updates:
            name = update.get('name')
            if not name:
                continue
            
            # Remove name from update data
            update_data = {k: v for k, v in update.items() if k != 'name'}
            
            if not update_data:
                continue
            
            # Update record
            frappe.db.set_value(doctype, name, update_data)
            updated_count += 1
        
        # Commit transaction
        frappe.db.commit()
        
        return {
            'success': True,
            'updated_count': updated_count,
            'message': f"Updated {updated_count} {doctype} records"
        }
        
    except Exception as e:
        # Rollback transaction
        frappe.db.rollback()
        frappe.throw(f"Bulk update failed: {str(e)}")
```

## 🛠️ Practical Exercises

### Exercise 8.1: Build a Complete API Endpoint

Create a complete API endpoint with:
- Authentication and authorization
- Input validation
- Error handling
- Response formatting
- Performance optimization

### Exercise 8.2: Implement Caching Strategy

Implement caching for:
- Frequently accessed data
- Complex calculations
- External API responses
- Cache invalidation

### Exercise 8.3: Batch Operations

Implement batch operations for:
- Bulk record creation
- Bulk record updates
- Performance optimization
- Error handling

## 🚀 Best Practices

### API Design

- **Use RESTful principles** for consistent API design
- **Implement proper authentication** and authorization
- **Validate all inputs** before processing
- **Provide clear error messages** with proper status codes
- **Use caching** for frequently accessed data

### Performance Optimization

- **Use bulk operations** for multiple records
- **Implement pagination** for large result sets
- **Cache expensive operations** appropriately
- **Monitor API performance** regularly
- **Optimize database queries** for API endpoints

### Security

- **Validate all inputs** to prevent injection attacks
- **Use HTTPS** for all API communications
- **Implement rate limiting** to prevent abuse
- **Audit API access** and usage
- **Keep API keys** secure and rotate regularly

## 📖 Further Reading

- [Frappe REST API Documentation](https://frappeframework.com/docs/user/en/api/rest)
- [API Security Best Practices](https://owasp.org/www-project-api-security/)
- [REST API Design Guidelines](https://restfulapi.net/)
- [Database Performance Optimization](https://frappeframework.com/docs/user/en/development/database)

## 🎯 Chapter Summary

Mastering API development is essential for building integrations:

- **API Architecture** provides the foundation for scalable integrations
- **Whitelisted Methods** offer secure server-side functionality
- **Performance Optimization** ensures responsive API interactions
- **Security Best Practices** protect your applications and data
- **Caching Strategies** improve API performance and reduce load

---

**Next Chapter**: Advanced reporting and data visualization techniques.


---

## Addendum: Practical API Patterns from the Field

### REST vs RPC — The Core Decision

Frappe exposes two primary API styles. Choosing the right one matters:

| Style | URL Pattern | Use When |
|-------|-------------|----------|
| REST | `/api/resource/<DocType>` | Standard CRUD on a single DocType |
| RPC | `/api/method/<function>` | Custom logic, calculations, multi-step workflows |

**Quick decision tree:**
```
Need real-time updates? → WebSocket (frappe.publish_realtime)
Working with a DocType (CRUD)? → REST (/api/resource/DocType)
Custom logic / calculations? → RPC (/api/method/function_name)
```

### API Versioning

Frappe supports two API versions simultaneously:

```
/api/resource/<DocType>        # V1 (legacy, still works)
/api/v2/document/<DocType>     # V2 (structured responses, PATCH support)
```

V2 response format:
```json
// Success
{ "data": {...}, "message_log": [] }

// Error
{ "errors": [{ "type": "ValidationError", "message": "..." }] }
```

### Authentication Methods

```bash
# API Key (recommended for integrations)
curl -H "Authorization: token api_key:api_secret" \
  https://your-site.com/api/resource/Customer

# Session (browser-based)
curl -X POST https://your-site.com/api/method/login \
  -d "usr=admin&pwd=password" -c cookies.txt

curl -b cookies.txt https://your-site.com/api/resource/Customer

# OAuth Bearer
curl -H "Authorization: Bearer <access_token>" \
  https://your-site.com/api/resource/Customer
```

### Building Whitelisted Methods

```python
import frappe
from frappe.rate_limiter import rate_limit

# Basic whitelisted method
@frappe.whitelist()
def get_customer_summary(customer):
    if not frappe.db.exists("Customer", customer):
        frappe.throw("Customer not found", frappe.DoesNotExistError)

    return {
        "customer": customer,
        "total_orders": frappe.db.count("Sales Order", {"customer": customer, "docstatus": 1}),
        "outstanding": frappe.db.get_value("Customer", customer, "outstanding_amount") or 0
    }

# Restrict to POST only
@frappe.whitelist(methods=["POST"])
def create_order(customer, items):
    if not frappe.has_permission("Sales Order", "create"):
        frappe.throw("No permission", frappe.PermissionError)

    order = frappe.get_doc({
        "doctype": "Sales Order",
        "customer": customer,
        "items": items
    })
    order.insert()
    return {"order_id": order.name}

# Allow guest access (public endpoints)
@frappe.whitelist(allow_guest=True)
def get_public_catalog():
    return frappe.get_all("Item",
        filters={"is_sales_item": 1, "disabled": 0},
        fields=["name", "item_name", "standard_rate"],
        limit=100
    )

# Rate-limited endpoint
@frappe.whitelist(allow_guest=True)
@rate_limit(limit=5, seconds=60)
def send_otp(mobile):
    # Limited to 5 requests per minute
    return {"status": "OTP sent"}
```

### Consuming APIs from JavaScript

```javascript
// frappe.call — standard approach
frappe.call({
    method: 'myapp.api.get_customer_summary',
    args: { customer: 'CUST-001' },
    freeze: true,
    freeze_message: __('Loading...'),
    callback(r) {
        if (!r.exc) {
            console.log(r.message);
        }
    }
});

// frappe.xcall — async/await
async function loadSummary(customer) {
    try {
        const data = await frappe.xcall('myapp.api.get_customer_summary', { customer });
        return data;
    } catch (err) {
        frappe.msgprint(__('Failed to load summary'));
    }
}

// Fetch with CSRF token
const response = await fetch('/api/method/myapp.api.create_order', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-Frappe-CSRF-Token': frappe.csrf_token
    },
    body: JSON.stringify({ customer: 'CUST-001', items: [] })
});
const data = await response.json();
```

### Consuming APIs from Python (External)

```python
import requests

class FrappeClient:
    def __init__(self, base_url, api_key, api_secret):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"token {api_key}:{api_secret}"
        })

    def get_list(self, doctype, filters=None, fields=None, limit=20):
        params = {"limit_page_length": limit}
        if filters:
            import json
            params["filters"] = json.dumps(filters)
        if fields:
            params["fields"] = json.dumps(fields)

        r = self.session.get(f"{self.base_url}/api/resource/{doctype}", params=params)
        r.raise_for_status()
        return r.json()["message"]

    def call_method(self, method, **kwargs):
        r = self.session.post(f"{self.base_url}/api/method/{method}", json=kwargs)
        r.raise_for_status()
        return r.json().get("message")

# Usage
client = FrappeClient("https://your-site.com", "api_key", "api_secret")
customers = client.get_list("Customer", filters={"disabled": 0}, fields=["name", "customer_name"])
```

### Integration Request — Logging External API Calls

Always use `Integration Request` to log outbound API calls. It gives you a full audit trail and makes debugging trivial.

```python
from frappe.integrations.utils import create_request_log

def call_payment_gateway(payload, invoice_name):
    """Make external API call with full logging"""
    integration_request = create_request_log(
        data=payload,
        service_name="Payment Gateway",
        request_headers={"Authorization": "Bearer token"},
        reference_doctype="Sales Invoice",
        reference_docname=invoice_name
    )

    try:
        import requests
        response = requests.post(
            "https://api.payment-gateway.com/charge",
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        integration_request.handle_success(response.json())
        return response.json()

    except requests.exceptions.Timeout:
        integration_request.handle_failure({"error": "Request timeout"})
        raise
    except requests.exceptions.HTTPError as e:
        integration_request.handle_failure({
            "error": f"HTTP {e.response.status_code}: {e.response.text}"
        })
        raise
    except Exception as e:
        integration_request.handle_failure({"error": str(e)})
        raise
```

**Query failed integrations:**
```python
# Find all failed calls for a service
failed = frappe.get_all(
    "Integration Request",
    filters={"integration_request_service": "Payment Gateway", "status": "Failed"},
    fields=["name", "error", "reference_docname", "creation"]
)

# Retry a failed request
def retry_integration(request_name):
    doc = frappe.get_doc("Integration Request", request_name)
    doc.status = "Queued"
    doc.error = None
    doc.save()
    # Re-enqueue processing

# Clean up old logs
from frappe.query_builder.functions import Now
from frappe.query_builder import Interval

table = frappe.qb.DocType("Integration Request")
frappe.db.delete(table, filters=(
    (table.integration_request_service == "Payment Gateway") &
    (table.modified < (Now() - Interval(days=30)))
))
```

### Webhooks — Push vs Pull

Webhooks are the push counterpart to REST APIs. Instead of polling for changes, the sender POSTs data to your endpoint when an event occurs.

```
API (pull):     Your app → requests data → External service responds
Webhook (push): External service → POSTs data → Your endpoint
```

**Receiving a webhook in Frappe:**
```python
@frappe.whitelist(allow_guest=True)
def receive_webhook():
    """Endpoint that receives incoming webhooks"""
    import json

    # Parse the incoming payload
    payload = frappe.request.get_data()
    data = json.loads(frappe.safe_decode(payload))

    # Log it via Integration Request
    integration_request = create_request_log(
        data=data,
        service_name="GitHub Webhook",
        is_remote_request=0  # incoming, not outgoing
    )

    try:
        # Validate signature (important for security)
        signature = frappe.request.headers.get("X-Hub-Signature-256")
        if not validate_webhook_signature(payload, signature):
            frappe.throw("Invalid signature", frappe.AuthenticationError)

        # Process the event
        event_type = frappe.request.headers.get("X-GitHub-Event")
        process_github_event(event_type, data)

        integration_request.handle_success({"processed": True})
        return {"status": "ok"}

    except Exception as e:
        integration_request.handle_failure({"error": str(e)})
        raise

def validate_webhook_signature(payload, signature):
    import hmac, hashlib
    secret = frappe.conf.get("github_webhook_secret", "").encode()
    expected = "sha256=" + hmac.new(secret, payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature or "")
```

**Sending a webhook from Frappe:**
```python
# hooks.py — trigger on document events
doc_events = {
    "Sales Order": {
        "on_submit": "myapp.webhooks.notify_erp_system"
    }
}
```

```python
# myapp/webhooks.py
import frappe
import requests
from frappe.integrations.utils import create_request_log

def notify_erp_system(doc, method):
    payload = {
        "event": "sales_order_submitted",
        "order_id": doc.name,
        "customer": doc.customer,
        "total": doc.grand_total
    }

    webhook_url = frappe.conf.get("erp_webhook_url")
    if not webhook_url:
        return

    integration_request = create_request_log(
        data=payload,
        service_name="ERP Webhook",
        reference_doctype=doc.doctype,
        reference_docname=doc.name
    )

    try:
        r = requests.post(webhook_url, json=payload, timeout=10)
        r.raise_for_status()
        integration_request.handle_success(r.json())
    except Exception as e:
        integration_request.handle_failure({"error": str(e)})
        # Don't raise — webhook failure shouldn't block the submit
        frappe.log_error(f"Webhook failed: {e}", "ERP Webhook")
```

### Clean Architecture for APIs

Separate HTTP handling from business logic so your services can be reused from background jobs, scheduled tasks, and other APIs.

```
myapp/
├── api/
│   └── orders.py        # HTTP layer — request/response only
├── services/
│   └── order_service.py # Business logic — reusable
└── utils/
    └── validators.py    # Shared validation
```

```python
# api/orders.py — thin HTTP layer
@frappe.whitelist(methods=["POST"])
def create_order(customer, items, delivery_date=None):
    from myapp.services.order_service import OrderService
    from myapp.utils.validators import validate_customer

    validate_customer(customer)
    order = OrderService().create_order(customer, items, delivery_date)
    return {"success": True, "order_id": order.name}
```

```python
# services/order_service.py — reusable business logic
class OrderService:
    def create_order(self, customer, items, delivery_date=None):
        from frappe.utils import nowdate, add_days

        if not delivery_date:
            delivery_date = add_days(nowdate(), 7)

        self._validate_stock(items)

        order = frappe.get_doc({
            "doctype": "Sales Order",
            "customer": customer,
            "delivery_date": delivery_date,
            "items": items
        })
        order.insert()
        order.submit()
        return order

    def _validate_stock(self, items):
        for item in items:
            available = frappe.db.get_value("Bin",
                {"item_code": item["item_code"]}, "actual_qty") or 0
            if available < item["qty"]:
                frappe.throw(
                    f"Insufficient stock for {item['item_code']}. "
                    f"Available: {available}, Required: {item['qty']}"
                )
```

### Response Best Practices

```python
# Consistent response format
@frappe.whitelist()
def get_customer(customer_id):
    try:
        doc = frappe.get_doc("Customer", customer_id)
        return {"success": True, "data": doc.as_dict()}
    except frappe.DoesNotExistError:
        frappe.response.http_status_code = 404
        return {"success": False, "message": "Customer not found"}

# Pagination
@frappe.whitelist()
def list_customers(page=1, page_size=20):
    page, page_size = int(page), min(int(page_size), 100)
    start = (page - 1) * page_size

    data = frappe.get_all("Customer",
        fields=["name", "customer_name", "email_id"],
        start=start, page_length=page_size)
    total = frappe.db.count("Customer")

    return {
        "data": data,
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": (total + page_size - 1) // page_size
    }

# Caching expensive responses
@frappe.whitelist()
def get_dashboard_stats():
    cache_key = f"dashboard_stats_{frappe.session.user}"
    cached = frappe.cache().get_value(cache_key)
    if cached:
        return cached

    stats = {
        "total_customers": frappe.db.count("Customer"),
        "open_orders": frappe.db.count("Sales Order", {"status": "To Deliver and Bill"}),
    }
    frappe.cache().set_value(cache_key, stats, expires_in_sec=300)
    return stats
```

### CORS Configuration

```json
// site_config.json
{
    "allow_cors": ["https://app.example.com", "https://admin.example.com"]
}
```

### Rate Limiting Reference

```python
from frappe.rate_limiter import rate_limit

# Simple limit: 10 requests per hour
@frappe.whitelist()
@rate_limit(limit=10, seconds=3600)
def sensitive_endpoint():
    pass

# Key-based: limit per email parameter
@frappe.whitelist(allow_guest=True)
@rate_limit(key="email", limit=5, seconds=60)
def request_password_reset(email):
    pass
```

### 8.6 Unified API Error Handling System

**The Problem with Traditional Error Handling**

Traditional Frappe API error handling lacks consistency and structure. Developers face:
- **Inconsistent error formats** across different API endpoints
- **Poor error visibility** with generic messages that don't help debugging
- **No standardized HTTP status codes** for different error types
- **Mixed error handling approaches** leading to maintenance challenges
- **Limited debugging information** in production environments

**Our Solution: Unified Exception Handling System**

The API Exception Handling System provides a **unified approach** to error management for custom Frappe APIs:

```python
# your_app/api/exceptions.py
import frappe
from functools import wraps
import traceback
from typing import Dict, Any, Optional

class APIException(Exception):
    """Base exception class for all API errors"""
    
    def __init__(self, message: str, error_code: str = None, status_code: int = 400, 
                 details: Dict[str, Any] = None):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)

class ValidationError(APIException):
    """Validation error - 400"""
    def __init__(self, message: str, field: str = None, **kwargs):
        super().__init__(message, "VALIDATION_ERROR", 400, **kwargs)
        if field:
            self.details["field"] = field

class AuthenticationError(APIException):
    """Authentication error - 401"""
    def __init__(self, message: str = "Authentication required", **kwargs):
        super().__init__(message, "AUTHENTICATION_ERROR", 401, **kwargs)

class AuthorizationError(APIException):
    """Authorization error - 403"""
    def __init__(self, message: str = "Access denied", **kwargs):
        super().__init__(message, "AUTHORIZATION_ERROR", 403, **kwargs)

class NotFoundError(APIException):
    """Resource not found - 404"""
    def __init__(self, message: str = "Resource not found", resource: str = None, **kwargs):
        super().__init__(message, "NOT_FOUND", 404, **kwargs)
        if resource:
            self.details["resource"] = resource

class RateLimitError(APIException):
    """Rate limit exceeded - 429"""
    def __init__(self, message: str = "Rate limit exceeded", **kwargs):
        super().__init__(message, "RATE_LIMIT_ERROR", 429, **kwargs)

class ServerError(APIException):
    """Internal server error - 500"""
    def __init__(self, message: str = "Internal server error", **kwargs):
        super().__init__(message, "SERVER_ERROR", 500, **kwargs)

def handle_api_exceptions(func):
    """Decorator to handle API exceptions and return consistent responses"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except APIException as e:
            # Handle our custom API exceptions
            response = {
                "success": False,
                "error": {
                    "code": e.error_code,
                    "message": e.message,
                    "details": e.details
                }
            }
            
            # Add debug information in development
            if frappe.conf.developer_mode:
                response["error"]["traceback"] = traceback.format_exc()
            
            frappe.local.response = response
            frappe.local.response_type = "json"
            frappe.local.status_code = e.status_code
            
        except Exception as e:
            # Handle unexpected errors
            response = {
                "success": False,
                "error": {
                    "code": "UNEXPECTED_ERROR",
                    "message": "An unexpected error occurred",
                    "details": {}
                }
            }
            
            # Add debug information in development
            if frappe.conf.developer_mode:
                response["error"]["traceback"] = traceback.format_exc()
                response["error"]["original_error"] = str(e)
            
            frappe.local.response = response
            frappe.local.response_type = "json"
            frappe.local.status_code = 500
            
            # Log the error for debugging
            frappe.log_error(
                message=f"API Error in {func.__name__}: {str(e)}",
                title="API Exception",
                reference=frappe.form_dict
            )
    
    return wrapper

# Usage Examples
@frappe.whitelist()
@handle_api_exceptions
def create_customer(customer_data: Dict[str, Any]):
    """Create a new customer with unified error handling"""
    
    # Validate required fields
    required_fields = ["customer_name", "customer_group"]
    for field in required_fields:
        if not customer_data.get(field):
            raise ValidationError(f"Field '{field}' is required", field=field)
    
    # Check if customer already exists
    if frappe.db.exists("Customer", {"customer_name": customer_data["customer_name"]}):
        raise ValidationError("Customer with this name already exists", field="customer_name")
    
    # Check permissions
    if not frappe.has_permission("Customer", "create"):
        raise AuthorizationError("You don't have permission to create customers")
    
    try:
        # Create the customer
        customer = frappe.get_doc({
            "doctype": "Customer",
            **customer_data
        })
        customer.insert(ignore_permissions=True)
        
        return {
            "success": True,
            "data": {
                "name": customer.name,
                "customer_name": customer.customer_name,
                "creation": customer.creation
            }
        }
        
    except frappe.DuplicateEntryError:
        raise ValidationError("Customer with this name already exists", field="customer_name")
    except Exception as e:
        raise ServerError(f"Failed to create customer: {str(e)}")

@frappe.whitelist()
@handle_api_exceptions
def get_customer(customer_name: str):
    """Get customer details with unified error handling"""
    
    if not customer_name:
        raise ValidationError("Customer name is required", field="customer_name")
    
    customer = frappe.db.get_value("Customer", customer_name, ["name", "customer_name", "email", "phone"], as_dict=True)
    
    if not customer:
        raise NotFoundError("Customer not found", resource="Customer")
    
    return {
        "success": True,
        "data": customer
    }
```

### 8.7 Integration Request System

**What is Integration Request?**

**Integration Request** is a Frappe DocType designed to track, log, and manage external API calls and integrations. It serves as a centralized logging system for all outbound and inbound API requests, making it an essential tool for debugging, monitoring, and maintaining integrations with third-party services.

**Key Characteristics:**
- **Centralized Logging**: All API calls are logged in one place
- **Status Tracking**: Tracks the lifecycle of API requests (Queued → Authorized → Completed/Failed)
- **Error Handling**: Captures both successful responses and error details
- **Reference Linking**: Can be linked to specific documents that triggered the integration
- **Audit Trail**: Provides complete audit trail for compliance and debugging

**When to Use Integration Request**

### 1. **Payment Gateway Integrations**
- Stripe, PayPal, Razorpay, Paytm, M-Pesa
- Track payment attempts, successes, and failures
- Audit financial transactions

### 2. **Email/SMS Services**
- SendGrid, Twilio, AWS SES
- Monitor delivery status and failures
- Track communication costs

### 3. **Third-Party APIs**
- Google Maps, shipping providers, CRM systems
- Log API calls for debugging
- Monitor rate limits and quotas

### 4. **Webhook Processing**
- GitHub, Shopify, external systems
- Track incoming webhook processing
- Debug webhook failures

**Implementation Examples**

```python
# your_app/integrations/stripe_integration.py
import frappe
import stripe
from frappe.utils import now
import json

@frappe.whitelist()
def create_payment_intent(amount: int, currency: str = "usd", customer_id: str = None):
    """Create Stripe payment intent with integration logging"""
    
    # Create integration request for logging
    integration_request = frappe.get_doc({
        "doctype": "Integration Request",
        "integration_type": "Remote",
        "reference_doctype": "Sales Invoice",
        "reference_docname": customer_id,
        "request_url": "https://api.stripe.com/v1/payment_intents",
        "request_headers": json.dumps({
            "Authorization": f"Bearer {get_stripe_api_key()}",
            "Content-Type": "application/x-www-form-urlencoded"
        }),
        "request_data": json.dumps({
            "amount": amount * 100,  # Stripe uses cents
            "currency": currency,
            "customer": customer_id
        })
    })
    integration_request.insert(ignore_permissions=True)
    
    try:
        # Make API call to Stripe
        stripe.api_key = get_stripe_api_key()
        payment_intent = stripe.PaymentIntent.create(
            amount=amount * 100,
            currency=currency,
            customer=customer_id if customer_id else None
        )
        
        # Update integration request with success
        integration_request.status = "Completed"
        integration_request.response_data = json.dumps(payment_intent.to_dict())
        integration_request.output = json.dumps({
            "payment_intent_id": payment_intent.id,
            "client_secret": payment_intent.client_secret
        })
        integration_request.execution_time = frappe.utils.time_diff_in_seconds(
            frappe.utils.now(), integration_request.creation
        )
        integration_request.save(ignore_permissions=True)
        
        return {
            "success": True,
            "payment_intent_id": payment_intent.id,
            "client_secret": payment_intent.client_secret
        }
        
    except stripe.error.StripeError as e:
        # Update integration request with error
        integration_request.status = "Failed"
        integration_request.error = str(e)
        integration_request.save(ignore_permissions=True)
        
        raise Exception(f"Stripe API Error: {str(e)}")
    
    except Exception as e:
        # Update integration request with unexpected error
        integration_request.status = "Failed"
        integration_request.error = str(e)
        integration_request.save(ignore_permissions=True)
        
        raise Exception(f"Unexpected error: {str(e)}")

def get_stripe_api_key():
    """Get encrypted Stripe API key from system settings"""
    from frappe.utils.password import get_decrypted_password
    return get_decrypted_password("System Settings", "System Settings", "stripe_api_key")

@frappe.whitelist()
def handle_webhook(webhook_data: Dict[str, Any], event_type: str):
    """Handle Stripe webhook with integration logging"""
    
    # Create integration request for incoming webhook
    integration_request = frappe.get_doc({
        "doctype": "Integration Request",
        "integration_type": "Webhook",
        "request_url": "webhook/stripe",
        "request_data": json.dumps(webhook_data),
        "request_headers": json.dumps({"Stripe-Event": event_type})
    })
    integration_request.insert(ignore_permissions=True)
    
    try:
        # Process webhook based on event type
        if event_type == "payment_intent.succeeded":
            payment_intent = webhook_data["data"]["object"]
            # Update related invoice status
            invoice_name = payment_intent.get("metadata", {}).get("invoice_id")
            if invoice_name:
                invoice = frappe.get_doc("Sales Invoice", invoice_name)
                invoice.status = "Paid"
                invoice.save(ignore_permissions=True)
                frappe.db.commit()
        
        # Mark integration request as completed
        integration_request.status = "Completed"
        integration_request.output = json.dumps({"processed": True})
        integration_request.save(ignore_permissions=True)
        
        return {"success": True}
        
    except Exception as e:
        # Mark integration request as failed
        integration_request.status = "Failed"
        integration_request.error = str(e)
        integration_request.save(ignore_permissions=True)
        
        raise Exception(f"Webhook processing failed: {str(e)}")

# your_app/integrations/email_integration.py
@frappe.whitelist()
def send_email_via_sendgrid(to_email: str, subject: str, message: str, 
                           reference_doctype: str = None, reference_docname: str = None):
    """Send email via SendGrid with integration logging"""
    
    # Create integration request
    integration_request = frappe.get_doc({
        "doctype": "Integration Request",
        "integration_type": "Remote",
        "reference_doctype": reference_doctype,
        "reference_docname": reference_docname,
        "request_url": "https://api.sendgrid.com/v3/mail/send",
        "request_data": json.dumps({
            "personalizations": [{"to": [{"email": to_email}]}],
            "from": {"email": "noreply@yourcompany.com"},
            "subject": subject,
            "content": [{"type": "text/plain", "value": message}]
        })
    })
    integration_request.insert(ignore_permissions=True)
    
    try:
        # Send email via SendGrid API
        import sendgrid
        from sendgrid.helpers.mail import Mail
        
        sg = sendgrid.SendGridAPIClient(get_sendgrid_api_key())
        
        message = Mail(
            from_email="noreply@yourcompany.com",
            to_emails=to_email,
            subject=subject,
            html_content=message
        )
        
        response = sg.send(message)
        
        # Update integration request
        integration_request.status = "Completed"
        integration_request.response_data = json.dumps({
            "status_code": response.status_code,
            "headers": dict(response.headers)
        })
        integration_request.output = json.dumps({
            "message_id": response.headers.get("X-Message-Id"),
            "status": "sent"
        })
        integration_request.save(ignore_permissions=True)
        
        return {"success": True, "message_id": response.headers.get("X-Message-Id")}
        
    except Exception as e:
        integration_request.status = "Failed"
        integration_request.error = str(e)
        integration_request.save(ignore_permissions=True)
        
        raise Exception(f"SendGrid API Error: {str(e)}")

def get_sendgrid_api_key():
    """Get encrypted SendGrid API key"""
    from frappe.utils.password import get_decrypted_password
    return get_decrypted_password("System Settings", "System Settings", "sendgrid_api_key")

# Monitoring and Reporting
@frappe.whitelist()
def get_integration_stats(days: int = 30):
    """Get integration statistics for monitoring"""
    
    from_date = frappe.utils.add_days(frappe.utils.nowdate(), -days)
    
    stats = frappe.db.sql("""
        SELECT 
            integration_type,
            status,
            COUNT(*) as count,
            AVG(execution_time) as avg_execution_time
        FROM `tabIntegration Request`
        WHERE creation >= %s
        GROUP BY integration_type, status
        ORDER BY count DESC
    """, (from_date,), as_dict=True)
    
    return {
        "stats": stats,
        "summary": {
            "total_requests": sum(row.count for row in stats),
            "success_rate": calculate_success_rate(stats),
            "avg_execution_time": calculate_avg_time(stats)
        }
    }

def calculate_success_rate(stats):
    """Calculate success rate from integration stats"""
    total = sum(row.count for row in stats)
    successful = sum(row.count for row in stats if row.status == "Completed")
    return (successful / total * 100) if total > 0 else 0

def calculate_avg_time(stats):
    """Calculate average execution time"""
    completed_requests = [row for row in stats if row.status == "Completed" and row.avg_execution_time]
    if not completed_requests:
        return 0
    
    total_time = sum(row.avg_execution_time * row.count for row in completed_requests)
    total_requests = sum(row.count for row in completed_requests)
    return total_time / total_requests if total_requests > 0 else 0
```

**Integration Request Best Practices**

```python
# your_app/utils/integration_utils.py
import frappe
import json
import time
from functools import wraps
from typing import Dict, Any, Optional

def log_integration_request(integration_type: str, request_url: str, 
                           request_data: Dict[str, Any] = None,
                           reference_doctype: str = None,
                           reference_docname: str = None):
    """Decorator to automatically log integration requests"""
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create integration request
            integration_request = frappe.get_doc({
                "doctype": "Integration Request",
                "integration_type": integration_type,
                "request_url": request_url,
                "request_data": json.dumps(request_data or {}),
                "reference_doctype": reference_doctype,
                "reference_docname": reference_docname
            })
            integration_request.insert(ignore_permissions=True)
            
            start_time = time.time()
            
            try:
                # Execute the function
                result = func(*args, **kwargs)
                
                # Update with success
                integration_request.status = "Completed"
                integration_request.output = json.dumps(result)
                integration_request.execution_time = time.time() - start_time
                integration_request.save(ignore_permissions=True)
                
                return result
                
            except Exception as e:
                # Update with error
                integration_request.status = "Failed"
                integration_request.error = str(e)
                integration_request.execution_time = time.time() - start_time
                integration_request.save(ignore_permissions=True)
                
                raise
        
        return wrapper
    return decorator

# Usage example
@log_integration_request(
    integration_type="Remote",
    request_url="https://api.example.com/endpoint",
    reference_doctype="Sales Order",
    reference_docname="SO-2023-001"
)
def call_external_api(data: Dict[str, Any]):
    """Call external API with automatic logging"""
    # Your API call logic here
    pass

# Integration Request Cleanup
def cleanup_old_integration_requests(days: int = 90):
    """Clean up old integration requests to maintain performance"""
    
    cutoff_date = frappe.utils.add_days(frappe.utils.nowdate(), -days)
    
    # Delete old completed requests
    frappe.db.sql("""
        DELETE FROM `tabIntegration Request`
        WHERE creation < %s AND status = 'Completed'
    """, (cutoff_date,))
    
    # Archive old failed requests (optional)
    failed_requests = frappe.db.sql("""
        SELECT name FROM `tabIntegration Request`
        WHERE creation < %s AND status = 'Failed'
    """, (cutoff_date,))
    
    for request_name, in failed_requests:
        # Move to archive or delete based on your compliance requirements
        frappe.delete_doc("Integration Request", request_name)
    
    frappe.db.commit()
```

**Monitoring Integration Requests**

```python
# your_app/reports/integration_monitor.py
import frappe

def execute(filters=None):
    """Report for monitoring integration requests"""
    
    columns = [
        {"label": "Integration Type", "fieldname": "integration_type", "fieldtype": "Data"},
        {"label": "Status", "fieldname": "status", "fieldtype": "Data"},
        {"label": "Request URL", "fieldname": "request_url", "fieldtype": "Data"},
        {"label": "Reference", "fieldname": "reference", "fieldtype": "Data"},
        {"label": "Execution Time", "fieldname": "execution_time", "fieldtype": "Float"},
        {"label": "Creation", "fieldname": "creation", "fieldtype": "Datetime"},
        {"label": "Error", "fieldname": "error", "fieldtype": "Text"}
    ]
    
    conditions = []
    if filters.get("from_date"):
        conditions.append("creation >= %(from_date)s")
    if filters.get("to_date"):
        conditions.append("creation <= %(to_date)s")
    if filters.get("integration_type"):
        conditions.append("integration_type = %(integration_type)s")
    if filters.get("status"):
        conditions.append("status = %(status)s")
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    data = frappe.db.sql(f"""
        SELECT 
            integration_type,
            status,
            request_url,
            CONCAT(reference_doctype, ': ', reference_docname) as reference,
            execution_time,
            creation,
            error
        FROM `tabIntegration Request`
        WHERE {where_clause}
        ORDER BY creation DESC
        LIMIT 1000
    """, filters, as_dict=True)
    
    return columns, data
```

This unified approach to API development provides:

1. **Consistent Error Handling** - Standardized error responses across all endpoints
2. **Comprehensive Logging** - Complete audit trail of all external integrations
3. **Monitoring & Debugging** - Built-in tools for tracking API performance
4. **Production Ready** - Error handling and logging suitable for enterprise deployments
5. **Developer Friendly** - Clear error messages and debugging information

By implementing these patterns, your APIs will be more reliable, maintainable, and easier to debug in production environments.

When exceeded, Frappe returns `429 Too Many Requests` with headers:
```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 0
Retry-After: 3600
```
