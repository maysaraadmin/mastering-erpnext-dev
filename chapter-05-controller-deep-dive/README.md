# Chapter 5: The Controller – Document Class Deep Dive

## 🎯 Learning Objectives

By the end of this chapter, you will master:

- **How** the Document class internally manages state and database operations
- **Why** hook execution order is critical for data integrity and performance
- **When** to use different data access methods for optimal performance
- **How** database transactions work within the controller lifecycle
- **Advanced patterns** for preventing infinite loops and recursive operations
- **Performance optimization** techniques for complex controller logic

## 📚 Chapter Topics

### 5.1 Understanding Document Class Architecture

**The Document Class Internal Structure**

The Document class is the heart of Frappe's ORM system. Understanding its internal architecture is crucial for building high-performance applications and debugging complex issues.

> **📊 Visual Reference**: See the complete document lifecycle diagram in `resources/diagrams/document_lifecycle.md` for a comprehensive view of how documents flow through the system.

#### How Document Manages State

```python
# Simplified version of Frappe's Document class internals
class Document:
    """Internal Document class structure"""
    
    def __init__(self, doctype, name=None):
        # Core state management
        self.doctype = doctype
        self.name = name
        self.docstatus = 0  # 0=Draft, 1=Submitted, 2=Cancelled
        
        # Internal state tracking
        self._docdata = {}  # Document data
        self._original_data = {}  # Original data for change tracking
        self._dirty_fields = set()  # Changed fields
        self._in_transaction = False  # Transaction state
        self._validated = False  # Validation state
        self._hooks_executed = {}  # Track executed hooks
        
        # Performance optimization
        self._field_cache = {}  # Field metadata cache
        self._relationship_cache = {}  # Relationship cache
        self._validation_cache = {}  # Validation results cache
        
        # Load or initialize
        if name:
            self.load_from_db()
        else:
            self.initialize_new_document()
    
    def load_from_db(self):
        """Load document data from database with optimization"""
        # Check cache first
        cache_key = f"doc_{self.doctype}_{self.name}"
        cached_data = frappe.cache().get(cache_key)
        
        if cached_data:
            self._docdata = cached_data
            self._original_data = cached_data.copy()
            return
        
        # Load from database
        data = frappe.db.get_value(self.doctype, self.name, '*')
        if not data:
            raise frappe.DoesNotExistError(f"{self.doctype} {self.name} not found")
        
        self._docdata = data
        self._original_data = data.copy()
        
        # Cache for performance (5 minutes)
        frappe.cache().set(cache_key, data, expires_in_sec=300)
    
    def initialize_new_document(self):
        """Initialize new document with defaults"""
        # Load DocType metadata
        meta = frappe.get_doc('DocType', self.doctype)
        
        # Set default values
        for field in meta.get('fields', []):
            if field.get('default') and field.fieldname not in self._docdata:
                self._docdata[field.fieldname] = field.default
        
        # Set standard defaults
        self._docdata.update({
            'creation': frappe.utils.now(),
            'modified': frappe.utils.now(),
            'owner': frappe.session.user,
            'modified_by': frappe.session.user,
            'docstatus': 0,
            'idx': 0
        })
        
        self._original_data = self._docdata.copy()
```

#### Hook Execution Engine

**Simplified Hook Example (For Beginners)**

```python
# Simple controller with basic hooks - perfect for getting started
class SimpleAssetController(Document):
    def validate(self):
        """Called before saving - basic validation"""
        # Ensure asset name is provided
        if not self.asset_name:
            frappe.throw("Asset Name is required")
        
        # Ensure purchase amount is positive
        if self.purchase_amount <= 0:
            frappe.throw("Purchase Amount must be greater than 0")
    
    def before_save(self):
        """Called just before saving - calculate values"""
        # Set default status if not provided
        if not self.status:
            self.status = "Available"
    
    def on_update(self):
        """Called after saving - send notification"""
        # Simple notification when asset is updated
        frappe.msgprint(f"Asset {self.name} has been updated")
```

**Understanding Hook Order:**
1. `validate()` → Check data validity
2. `before_save()` → Prepare data for saving  
3. `on_update()` → Actions after successful save

This simple pattern covers 80% of common controller use cases!

---

**Advanced Hook Execution System**

```python
# Hook execution system with performance optimization
class HookExecutionEngine:
    """Manages hook execution order and performance"""
    
    def __init__(self, document):
        self.document = document
        self._hook_stack = []  # Track hook execution stack
        self._hook_performance = {}  # Performance metrics
        self._hook_dependencies = {}  # Hook dependencies
    
    def execute_hook(self, hook_name, *args, **kwargs):
        """Execute hook with performance monitoring and dependency management"""
        start_time = time.time()
        
        # Check if hook should be executed
        if not self.should_execute_hook(hook_name):
            return
        
        # Add to execution stack
        self._hook_stack.append(hook_name)
        
        try:
            # Check dependencies
            self.check_hook_dependencies(hook_name)
            
            # Execute hook
            hook_method = getattr(self.document, hook_name, None)
            if hook_method:
                result = hook_method(*args, **kwargs)
                
                # Track execution
                self._hook_executed[hook_name] = True
                
                return result
            else:
                self._hook_executed[hook_name] = False
                return None
                
        except Exception as e:
            # Log hook execution error
            frappe.log_error(f"Hook {hook_name} failed: {str(e)}")
            raise
        finally:
            # Remove from execution stack
            self._hook_stack.remove(hook_name)
            
            # Record performance
            execution_time = time.time() - start_time
            self._hook_performance[hook_name] = execution_time
            
            # Log slow hooks
            if execution_time > 1.0:  # 1 second threshold
                frappe.logger.warning(f"Slow hook: {hook_name} took {execution_time:.3f}s")
    
    def should_execute_hook(self, hook_name):
        """Determine if hook should be executed"""
        # Check if already executed
        if self._hook_executed.get(hook_name):
            return False
        
        # Check if in transaction
        if self.document._in_transaction and hook_name in ['validate', 'before_save']:
            return True
        
        # Check document state
        if hook_name in ['on_submit', 'after_submit'] and self.document.docstatus != 0:
            return True
        
        if hook_name in ['on_cancel', 'after_cancel'] and self.document.docstatus != 2:
            return True
        
        return True
    
    def check_hook_dependencies(self, hook_name):
        """Check and execute hook dependencies"""
        dependencies = self._hook_dependencies.get(hook_name, [])
        
        for dep in dependencies:
            if not self._hook_executed.get(dep):
                # Execute dependency first
                self.execute_hook(dep)

# Hook dependency definitions
hook_dependencies = {
    'before_submit': ['validate'],
    'on_submit': ['before_submit'],
    'after_submit': ['on_submit'],
    'before_cancel': ['validate'],
    'on_cancel': ['before_cancel'],
    'after_cancel': ['on_cancel']
}
```

#### Database Transaction Management

```python
# Transaction management within Document class
class TransactionManager:
    """Manages database transactions for Document operations"""
    
    def __init__(self, document):
        self.document = document
        self._transaction_active = False
        self._savepoints = []
        self._operations = []
    
    def begin_transaction(self):
        """Begin database transaction"""
        if self._transaction_active:
            return  # Already in transaction
        
        frappe.db.begin()
        self._transaction_active = True
        self._operations = []
        
        # Set document in transaction state
        self.document._in_transaction = True
    
    def commit_transaction(self):
        """Commit database transaction"""
        if not self._transaction_active:
            return
        
        try:
            # Validate before commit
            self.validate_before_commit()
            
            # Commit to database
            frappe.db.commit()
            
            # Clear transaction state
            self._transaction_active = False
            self.document._in_transaction = False
            self._savepoints = []
            
            # Update caches
            self.update_caches()
            
        except Exception as e:
            # Rollback on error
            self.rollback_transaction()
            raise
    
    def rollback_transaction(self):
        """Rollback database transaction"""
        if not self._transaction_active:
            return
        
        frappe.db.rollback()
        self._transaction_active = False
        self.document._in_transaction = False
        self._savepoints = []
        
        # Restore original data
        self.document._docdata = self.document._original_data.copy()
        self.document._dirty_fields.clear()
    
    def create_savepoint(self, name):
        """Create transaction savepoint"""
        if not self._transaction_active:
            raise Exception("Not in transaction")
        
        savepoint_name = f"sp_{name}"
        frappe.db.savepoint(savepoint_name)
        self._savepoints.append(savepoint_name)
        
        return savepoint_name
    
    def rollback_to_savepoint(self, name):
        """Rollback to specific savepoint"""
        if not self._transaction_active:
            raise Exception("Not in transaction")
        
        savepoint_name = f"sp_{name}"
        if savepoint_name not in self._savepoints:
            raise Exception(f"Savepoint {name} not found")
        
        frappe.db.rollback_to_savepoint(savepoint_name)
        
        # Remove savepoints after this one
        index = self._savepoints.index(savepoint_name)
        self._savepoints = self._savepoints[:index]
    
    def validate_before_commit(self):
        """Validate data before committing transaction"""
        # Check for validation errors
        if hasattr(self.document, '_validation_errors'):
            if self.document._validation_errors:
                raise Exception("Validation errors exist")
        
        # Check for required fields
        meta = frappe.get_doc('DocType', self.document.doctype)
        for field in meta.get('fields', []):
            if field.reqd and not self.document.get(field.fieldname):
                raise Exception(f"Required field {field.fieldname} is missing")
        
        # Check for data consistency
        self.check_data_consistency()
    
    def check_data_consistency(self):
        """Check data consistency across related data"""
        # Example: Check child table consistency
        if hasattr(self.document, 'items'):
            for item in self.document.get('items', []):
                if not item.get('item_code'):
                    raise Exception("Item code is required in child table")
                
                if not item.get('qty') or item.qty <= 0:
                    raise Exception("Quantity must be greater than 0")
    
    def update_caches(self):
        """Update caches after successful transaction"""
        # Clear document cache
        cache_key = f"doc_{self.document.doctype}_{self.document.name}"
        frappe.cache().delete(cache_key)
        
        # Clear related caches
        self.clear_related_caches()
        
        # Update search index
        self.update_search_index()
    
    def clear_related_caches(self):
        """Clear caches related to this document"""
        # Clear customer cache if this is a transaction
        if self.document.doctype == 'Sales Order':
            customer_cache_key = f"doc_Customer_{self.document.customer}"
            frappe.cache().delete(customer_cache_key)
    
    def update_search_index(self):
        """Update search index for document"""
        if hasattr(self.document, 'index_web_pages_for_search'):
            frappe.enqueue_doc('Website Route', 'update_index', 
                             doctype=self.document.doctype, 
                             docname=self.document.name)
```

#### Performance Optimization Strategies

```python
# Performance-optimized controller patterns
class OptimizedController(Document):
    """Performance-optimized document controller"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Performance tracking
        self._performance_metrics = {}
        self._query_count = 0
        self._cache_hits = 0
        self._cache_misses = 0
    
    def get_cached_value(self, fieldname, default=None):
        """Get cached value with performance tracking"""
        cache_key = f"field_{self.doctype}_{self.name}_{fieldname}"
        
        # Try cache first
        cached_value = frappe.cache().get(cache_key)
        if cached_value is not None:
            self._cache_hits += 1
            return cached_value
        
        # Cache miss - get from database
        value = self.get(fieldname, default)
        
        # Cache the value (5 minutes)
        frappe.cache().set(cache_key, value, expires_in_sec=300)
        self._cache_misses += 1
        
        return value
    
    def batch_get_values(self, fieldnames):
        """Batch get multiple field values efficiently"""
        # Check cache first
        cached_values = {}
        uncached_fields = []
        
        for fieldname in fieldnames:
            cache_key = f"field_{self.doctype}_{self.name}_{fieldname}"
            cached_value = frappe.cache().get(cache_key)
            
            if cached_value is not None:
                cached_values[fieldname] = cached_value
                self._cache_hits += 1
            else:
                uncached_fields.append(fieldname)
        
        # Get uncached fields from database
        if uncached_fields:
            db_values = frappe.db.get_value(self.doctype, self.name, uncached_fields)
            if db_values:
                # Handle single value vs multiple values
                if len(uncached_fields) == 1:
                    cached_values[uncached_fields[0]] = db_values
                    # Cache the value
                    cache_key = f"field_{self.doctype}_{self.name}_{uncached_fields[0]}"
                    frappe.cache().set(cache_key, db_values, expires_in_sec=300)
                else:
                    for i, fieldname in enumerate(uncached_fields):
                        if i < len(db_values):
                            cached_values[fieldname] = db_values[i]
                            # Cache the value
                            cache_key = f"field_{self.doctype}_{self.name}_{fieldname}"
                            frappe.cache().set(cache_key, db_values[i], expires_in_sec=300)
                
                self._cache_misses += 1
        
        return cached_values
    
    def optimized_child_table_query(self, child_table_name, fields=None, filters=None):
        """Optimized child table query with caching"""
        # Build cache key
        cache_key = f"child_{self.doctype}_{self.name}_{child_table_name}"
        if fields:
            cache_key += f"_fields_{','.join(fields)}"
        if filters:
            cache_key += f"_filters_{hash(str(filters))}"
        
        # Try cache first
        cached_data = frappe.cache().get(cache_key)
        if cached_data is not None:
            self._cache_hits += 1
            return cached_data
        
        # Build query
        query = f"""
            SELECT {','.join(fields or ['*'])}
            FROM `tab{child_table_name}`
            WHERE parent = %s
        """
        
        params = [self.name]
        
        if filters:
            for field, value in filters.items():
                query += f" AND {field} = %s"
                params.append(value)
        
        # Execute query
        self._query_count += 1
        data = frappe.db.sql(query, params, as_dict=True)
        
        # Cache the result (2 minutes for child tables)
        frappe.cache().set(cache_key, data, expires_in_sec=120)
        self._cache_misses += 1
        
        return data
    
    def track_performance(self, operation_name, execution_time):
        """Track performance metrics"""
        if operation_name not in self._performance_metrics:
            self._performance_metrics[operation_name] = {
                'total_time': 0,
                'call_count': 0,
                'avg_time': 0,
                'max_time': 0,
                'min_time': float('inf')
            }
        
        metrics = self._performance_metrics[operation_name]
        metrics['total_time'] += execution_time
        metrics['call_count'] += 1
        metrics['avg_time'] = metrics['total_time'] / metrics['call_count']
        metrics['max_time'] = max(metrics['max_time'], execution_time)
        metrics['min_time'] = min(metrics['min_time'], execution_time)
    
    def get_performance_report(self):
        """Get performance report"""
        report = {
            'query_count': self._query_count,
            'cache_hits': self._cache_hits,
            'cache_misses': self._cache_misses,
            'cache_hit_rate': self._cache_hits / (self._cache_hits + self._cache_misses) if (self._cache_hits + self._cache_misses) > 0 else 0,
            'operations': self._performance_metrics
        }
        
        return report
    
    def log_slow_operations(self, threshold=1.0):
        """Log operations that exceed threshold"""
        for operation, metrics in self._performance_metrics.items():
            if metrics['avg_time'] > threshold:
                frappe.logger.warning(
                    f"Slow operation detected: {operation} "
                    f"(avg: {metrics['avg_time']:.3f}s, "
                    f"calls: {metrics['call_count']})"
                )
```

### 5.2 Controller Hooks in Order

#### Initialization Hooks

```python
class CustomDocument(Document):
    def __init__(self, *args, **kwargs):
        """Called when document is instantiated"""
        super().__init__(*args, **kwargs)
        
        # Custom initialization
        self._custom_data = {}
        self._validation_errors = []
        
        # Load custom data if document exists
        if not self.is_new():
            self.load_custom_data()
    
    def load_custom_data(self):
        """Load custom data related to this document"""
        if hasattr(self, 'customer'):
            # Load customer-specific data
            pass
    
    def autoname(self):
        """Generate document name automatically"""
        if not self.name:
            # Custom naming logic
            if self.customer_type == "Government":
                self.name = f"GOV-{self.customer_name[:3].upper()}-{frappe.utils.random_string(4)}"
            else:
                self.name = f"COM-{self.customer_name[:3].upper()}-{frappe.utils.random_string(4)}"
```

#### Validation Hooks

```python
class CustomDocument(Document):
    def validate(self):
        """Main validation hook - called before save"""
        # Required field validation
        self.validate_required_fields()
        
        # Business logic validation
        self.validate_business_rules()
        
        # Data consistency validation
        self.validate_data_consistency()
        
        # Custom validation
        self.validate_custom_logic()
    
    def validate_required_fields(self):
        """Validate required fields"""
        required_fields = ['customer', 'transaction_date', 'items']
        
        for field in required_fields:
            if not self.get(field):
                frappe.throw(f"{field.title()} is required")
    
    def validate_business_rules(self):
        """Validate business rules"""
        # Example: Cannot create sales order for inactive customer
        if self.customer:
            customer_status = frappe.db.get_value('Customer', self.customer, 'status')
            if customer_status != 'Active':
                frappe.throw("Cannot create Sales Order for inactive customer")
        
        # Example: Validate transaction date
        if self.transaction_date and self.transaction_date > frappe.utils.today():
            frappe.throw("Transaction date cannot be in the future")
    
    def validate_data_consistency(self):
        """Validate data consistency across fields"""
        # Validate child table consistency
        for item in self.get('items', []):
            if item.qty <= 0:
                frappe.throw(f"Quantity must be greater than 0 for item {item.item_code}")
            
            if item.rate <= 0:
                frappe.throw(f"Rate must be greater than 0 for item {item.item_code}")
    
    def validate_custom_logic(self):
        """Custom validation logic"""
        # Example: Validate total amount
        total_amount = sum(item.qty * item.rate for item in self.get('items', []))
        if abs(total_amount - self.total_amount) > 0.01:
            frappe.throw("Total amount doesn't match sum of item amounts")
```

#### Pre-Save Hooks

```python
class CustomDocument(Document):
    def before_save(self):
        """Called before document is saved"""
        # Calculate derived fields
        self.calculate_totals()
        
        # Set default values
        self.set_default_values()
        
        # Format data
        self.format_data()
        
        # Audit trail
        self.add_audit_trail()
    
    def before_insert(self):
        """Called before new document is inserted"""
        # Set creation-specific values
        if self.is_new():
            self.creation_date = frappe.utils.now()
            self.created_by = frappe.session.user
            self.document_number = self.generate_document_number()
            
            # Initialize child table fields
            self.initialize_child_tables()
    
    def calculate_totals(self):
        """Calculate totals and derived values"""
        total_amount = 0
        total_quantity = 0
        
        for item in self.get('items', []):
            item.amount = item.qty * item.rate
            total_amount += item.amount
            total_quantity += item.qty
        
        self.total_amount = total_amount
        self.total_quantity = total_quantity
        self.net_total = total_amount - self.discount_amount
    
    def set_default_values(self):
        """Set default values"""
        if not self.transaction_date:
            self.transaction_date = frappe.utils.today()
        
        if not self.fiscal_year:
            self.fiscal_year = frappe.db.get_default('fiscal_year')
    
    def format_data(self):
        """Format data for consistency"""
        if self.customer_name:
            self.customer_name = self.customer_name.title()
        
        # Format phone numbers
        if self.phone:
            self.phone = ''.join(filter(str.isdigit, self.phone))
```

#### Save Hooks

```python
class CustomDocument(Document):
    def on_update(self):
        """Called after document is saved"""
        # Update related documents
        self.update_related_documents()
        
        # Send notifications
        self.send_notifications()
        
        # Update statistics
        self.update_statistics()
        
        # Log activity
        self.log_activity()
    
    def after_save(self):
        """Called after all save operations complete"""
        # Clear cache
        self.clear_cache()
        
        # Trigger webhooks
        self.trigger_webhooks()
        
        # Update search index
        self.update_search_index()
    
    def db_insert(self):
        """Custom database insert logic"""
        # Override for custom insert behavior
        if hasattr(self, 'custom_insert_logic'):
            self.perform_custom_insert()
        else:
            super().db_insert()
    
    def db_update(self):
        """Custom database update logic"""
        # Override for custom update behavior
        if hasattr(self, 'custom_update_logic'):
            self.perform_custom_update()
        else:
            super().db_update()
```

#### Submission Hooks

```python
class CustomDocument(Document):
    def before_submit(self):
        """Called before document submission"""
        # Validate submission requirements
        self.validate_submission_requirements()
        
        # Check permissions
        self.check_submit_permissions()
        
        # Reserve resources
        self.reserve_resources()
        
        # Create accounting entries
        self.create_accounting_entries()
    
    def on_submit(self):
        """Called after document is submitted"""
        # Update inventory
        self.update_inventory()
        
        # Create follow-up tasks
        self.create_follow_up_tasks()
        
        # Send confirmation
        self.send_submission_confirmation()
        
        # Update status in related documents
        self.update_related_status()
    
    def after_submit(self):
        """Called after all submission operations"""
        # Trigger workflows
        self.trigger_workflows()
        
        # Update reporting data
        self.update_reporting_data()
        
        # Archive old data
        self.archive_transaction_data()
```

#### Cancellation Hooks

```python
class CustomDocument(Document):
    def before_cancel(self):
        """Called before document cancellation"""
        # Validate cancellation requirements
        self.validate_cancellation_requirements()
        
        # Check if cancellation is allowed
        self.check_cancellation_allowed()
        
        # Reverse accounting entries
        self.reverse_accounting_entries()
    
    def on_cancel(self):
        """Called after document is cancelled"""
        # Release reserved resources
        self.release_resources()
        
        # Update inventory
        self.reverse_inventory_updates()
        
        # Cancel related documents
        self.cancel_related_documents()
        
        # Send cancellation notification
        self.send_cancellation_notification()
    
    def after_cancel(self):
        """Called after all cancellation operations"""
        # Update statistics
        self.update_cancellation_statistics()
        
        # Clear cache
        self.clear_cancellation_cache()
```

### 5.3 Data Access Methods

#### Understanding the Differences

```python
class DataAccessExample(Document):
    def demonstrate_data_access(self):
        """Different ways to access document data"""
        
        # 1. Direct attribute access (fastest)
        customer_name = self.customer_name
        total_amount = self.total_amount
        
        # 2. Using get() method (safe, with default)
        customer_name = self.get('customer_name', 'Unknown Customer')
        total_amount = self.get('total_amount', 0)
        
        # 3. Using get_value() (with fallback to database)
        customer_name = self.get_value('customer_name')
        total_amount = self.get_value('total_amount')
        
        # 4. Accessing child table data
        for item in self.get('items', []):
            item_code = item.item_code
            quantity = item.get('qty', 0)
        
        # 5. Getting single value from database
        customer_email = frappe.db.get_value('Customer', self.customer, 'email')
        
        # 6. Getting multiple values from database
        customer_data = frappe.db.get_value('Customer', self.customer, 
                                          ['email', 'customer_group', 'territory'])
        if customer_data:
            email, group, territory = customer_data
```

#### Performance Considerations

```python
class PerformanceOptimizedController(Document):
    def efficient_data_access(self):
        """Efficient data access patterns"""
        
        # Good: Batch database queries
        customers = frappe.db.get_all('Customer', 
                                     fields=['name', 'customer_name', 'email'],
                                     filters={'status': 'Active'})
        
        # Bad: Multiple individual queries in loop
        # for item in self.items:
        #     item_name = frappe.db.get_value('Item', item.item_code, 'item_name')
        
        # Good: Single query with IN clause
        item_codes = [item.item_code for item in self.items]
        item_names = frappe.db.get_all('Item',
                                       fields=['name', 'item_name'],
                                       filters={'name': ['in', item_codes]})
        
        # Create lookup dictionary
        item_lookup = {item.name: item.item_name for item in item_names}
        
        # Use lookup in loop
        for item in self.items:
            item.item_name = item_lookup.get(item.item_code)
```

### 5.4 Preventing Infinite Loops

#### Common Loop Scenarios

```python
class LoopPreventionController(Document):
    def safe_update_related(self):
        """Safely update related documents without loops"""
        
        # Method 1: Check if already updating
        if hasattr(self, '_updating_related'):
            return
        
        self._updating_related = True
        try:
            # Update related documents
            for child in self.get('items', []):
                if child.item_code:
                    # Update item statistics
                    self.update_item_stats(child.item_code)
        finally:
            delattr(self, '_updating_related')
    
    def safe_cross_validation(self):
        """Safe cross-document validation"""
        
        # Method 2: Use flag to prevent recursion
        if frappe.flags.in_cross_validation:
            return
        
        frappe.flags.in_cross_validation = True
        try:
            # Cross-validation logic
            self.validate_with_related_docs()
        finally:
            frappe.flags.in_cross_validation = False
    
    def safe_recursive_operation(self):
        """Safe recursive operations"""
        
        # Method 3: Track call stack
        if not hasattr(frappe.local, 'call_stack'):
            frappe.local.call_stack = []
        
        method_name = 'safe_recursive_operation'
        if method_name in frappe.local.call_stack:
            return
        
        frappe.local.call_stack.append(method_name)
        try:
            # Recursive operation
            self.process_related_data()
        finally:
            frappe.local.call_stack.remove(method_name)
```

### 5.5 Managing Document State

#### Understanding docstatus

```python
class DocumentStateController(Document):
    def manage_document_state(self):
        """Manage document state transitions"""
        
        # Current state
        current_state = self.docstatus  # 0=Draft, 1=Submitted, 2=Cancelled
        
        # State-based validation
        if current_state == 0:  # Draft
            self.validate_draft_state()
        elif current_state == 1:  # Submitted
            self.validate_submitted_state()
        elif current_state == 2:  # Cancelled
            self.validate_cancelled_state()
    
    def validate_draft_state(self):
        """Validations for draft state"""
        # Can modify all fields
        # Can add/remove child items
        # Can change customer
        pass
    
    def validate_submitted_state(self):
        """Validations for submitted state"""
        # Limited field changes allowed
        # Cannot modify financial fields
        # Cannot add/remove items
        
        # Example: Only allow status updates
        if self.has_value_changed('status'):
            self.validate_status_change()
        
        # Prevent modification of critical fields
        critical_fields = ['customer', 'transaction_date', 'total_amount']
        for field in critical_fields:
            if self.has_value_changed(field):
                frappe.throw(f"Cannot modify {field} after submission")
    
    def validate_cancelled_state(self):
        """Validations for cancelled state"""
        # Very limited changes allowed
        # Only can add cancellation remarks
        
        if self.has_value_changed('cancellation_remarks'):
            self.validate_cancellation_remarks()
    
    def state_based_operations(self):
        """Perform operations based on document state"""
        
        if self.docstatus == 0:  # Draft
            # Calculate provisional values
            self.calculate_provisional_totals()
            
        elif self.docstatus == 1:  # Submitted
            # Create accounting entries
            self.create_accounting_entries()
            
            # Update inventory
            self.update_inventory()
            
        elif self.docstatus == 2:  # Cancelled
            # Reverse accounting entries
            self.reverse_accounting_entries()
            
            # Restore inventory
            self.restore_inventory()
```

## 🛠️ Practical Exercises

### Exercise 5.1: Complete Controller Implementation

Create a comprehensive controller with:
- All lifecycle hooks
- Proper validation logic
- State management
- Performance optimization

### Exercise 5.2: Loop Prevention

Implement safe cross-document updates:
- Multiple methods for loop prevention
- Proper error handling
- Performance considerations

### Exercise 5.3: State Management

Build a state-aware controller:
- State-based validation
- Conditional operations
- Proper state transitions

## 🚀 Best Practices

### Controller Design

- **Keep methods focused** on single responsibilities
- **Use descriptive method names** for clarity
- **Handle errors gracefully** with meaningful messages
- **Document complex logic** with comments

### Performance Optimization

- **Minimize database queries** in loops
- **Use caching** for frequently accessed data
- **Batch operations** when possible
- **Profile performance** of critical methods

### Error Handling

- **Validate early** to fail fast
- **Provide clear error messages** to users
- **Log errors** for debugging
- **Handle edge cases** gracefully

## 📖 Further Reading

- [Document API Reference](https://frappeframework.com/docs/user/en/api/document)
- [Controller Hooks Guide](https://frappeframework.com/docs/user/en/development/hooks)
- [Database Operations](https://frappeframework.com/docs/user/en/development/database)

## 🎯 Chapter Summary

Mastering controllers is essential for robust Frappe applications:

- **Lifecycle hooks** provide complete control over document behavior
- **Data access methods** offer flexibility with performance considerations
- **Loop prevention** ensures system stability
- **State management** controls document workflows
- **Performance optimization** maintains application responsiveness

---

**Next Chapter**: Mastering the Frappe ORM for efficient database operations.


---

## 📌 Addendum: Document Lifecycle Flowchart & production_plan_controller.py

### Document Lifecycle — ASCII Flowchart

```
  frappe.get_doc({...})
         │
         ▼
    ┌─────────┐
    │ __init__ │  (autoname if new)
    └────┬────┘
         │ insert() / save()
         ▼
    ┌──────────┐
    │before_insert│ (new docs only)
    └─────┬────┘
          │
          ▼
    ┌──────────┐
    │ validate  │  ← main validation hook
    └─────┬────┘
          │
          ▼
    ┌─────────────┐
    │ before_save  │
    └──────┬──────┘
           │
           ▼
    ┌──────────────┐
    │  db_insert /  │  ← actual SQL write
    │  db_update    │
    └──────┬───────┘
           │
           ▼
    ┌──────────┐
    │ after_insert│ (new docs only)
    └─────┬────┘
          │
          ▼
    ┌──────────┐
    │ on_update │  ← runs after every save
    └─────┬────┘
          │
    ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─
    On submit():
          │
          ▼
    ┌───────────────┐
    │ before_submit  │
    └──────┬────────┘
           │
           ▼
    ┌──────────────┐
    │  db_update    │  (docstatus = 1)
    └──────┬───────┘
           │
           ▼
    ┌───────────┐
    │ on_submit  │
    └─────┬─────┘
          │
          ▼
    ┌────────────┐
    │after_submit │
    └────────────┘

    On cancel():
    ┌───────────────┐
    │ before_cancel  │
    └──────┬────────┘
           │
           ▼
    ┌──────────────┐
    │  db_update    │  (docstatus = 2)
    └──────┬───────┘
           │
           ▼
    ┌───────────┐
    │ on_cancel  │
    └─────┬─────┘
          │
          ▼
    ┌────────────┐
    │after_cancel │
    └────────────┘

    On delete():
    ┌───────────┐
    │ on_trash   │  ← before DB deletion
    └─────┬─────┘
          │
          ▼
    ┌──────────────┐
    │ after_delete  │  ← after DB deletion
    └──────────────┘
```

### Cross-Reference: production_plan_controller.py

The `production_plan_controller.py` in `chapter-05-controller-deep-dive/controller_examples/` demonstrates several advanced patterns covered in this chapter:

- **`validate()`** — date range validation and total calculation
- **`on_submit()`** — triggering downstream work order creation
- **`set_status()`** — deriving document status from business state rather than storing it manually
- **BOM explosion** — a real-world example of N+1 avoidance using batch SQL queries

See also `projects/production_planning/` for the full working implementation including `get_permission_query_conditions()` — a practical example of row-level permission filtering.


---

## Addendum: Source Article Insights

### `frappe.call()` and `run_doc_method` Internals

`frappe.call()` is the bridge between JavaScript and Python DocType methods. When you call `frm.call('method_name')`, Frappe automatically:
1. Takes your current document data
2. Creates a Document object on the server via `frappe.get_doc()`
3. Executes your whitelisted method on that object
4. Returns the result

**The full flow:**
```
frm.call('calculate_total')
    ↓
HTTP POST to /api/method/run_doc_method
    ↓
run_doc_method() creates doc = frappe.get_doc(docs)
    ↓
doc.run_method('calculate_total')
    ↓
Your @frappe.whitelist() method executes
    ↓
Response returned to client
```

**Why Postman gives "Method not found":** Postman needs to use the `run_doc_method` endpoint with the complete document data structure, not just the method name.

**Server-side method:**
```python
class MyDocType(Document):
    @frappe.whitelist()
    def calculate_total(self, multiplier=1.0):
        """Called from client via frm.call()"""
        self.total = sum(item.amount for item in self.items) * multiplier
        return self.total
    
    @frappe.whitelist()
    def get_related_data(self, param=None):
        # self is the document — already loaded, no need to fetch
        result = frappe.get_all("Related DocType",
            filters={"parent_ref": self.name},
            fields=["name", "value"]
        )
        return result
```

**Client-side call patterns:**
```javascript
// Pattern 1: frm.call (simplest — sends frm.doc automatically)
frm.call('calculate_total', { multiplier: 1.5 })
    .then(r => {
        frm.set_value('total', r.message);
    });

// Pattern 2: frappe.call with doc
frappe.call({
    doc: frm.doc,
    method: 'calculate_total',
    args: { multiplier: 1.5 },
    callback: r => {
        frm.set_value('total', r.message);
        frm.refresh_field('total');
    }
});

// Pattern 3: frappe.call with dt/dn (fetch from DB)
frappe.call({
    method: 'run_doc_method',
    args: {
        method: 'calculate_total',
        dt: 'My DocType',
        dn: frm.doc.name,
        args: { multiplier: 1.5 }
    }
});

// Pattern 4: module-level function (not a DocType method)
frappe.call({
    method: 'myapp.utils.currency.get_exchange_rate',
    args: { from_currency: 'USD', to_currency: 'EUR' },
    callback: r => console.log(r.message)
});
```

**Postman / REST API:**
```http
# Call a DocType instance method
POST /api/method/run_doc_method
{
    "method": "calculate_total",
    "dt": "Sales Invoice",
    "dn": "SINV-00001",
    "args": {"multiplier": 1.1}
}

# Call a module-level function
POST /api/method/myapp.utils.currency.get_exchange_rate
{
    "from_currency": "USD",
    "to_currency": "EUR"
}
```

---

### Creating Related Documents

A common controller pattern: creating a new related document from an existing one (e.g., creating Asset Maintenance from Asset, creating User from Employee).

**The pattern:**
```
User clicks button → JS collects data → frappe.call() → Python creates doc → JS navigates to new doc
```

**Server-side (Python):**
```python
@frappe.whitelist()
def create_asset_maintenance(asset, item_code, item_name, asset_category, company):
    """Create Asset Maintenance from Asset"""
    doc = frappe.new_doc("Asset Maintenance")
    doc.update({
        "asset_name": asset,
        "company": company,
        "item_code": item_code,
        "item_name": item_name,
        "asset_category": asset_category,
    })
    return doc  # Return unsaved draft for user to review
```

**Client-side (JavaScript):**
```javascript
create_asset_maintenance: function(frm) {
    frappe.call({
        method: "erpnext.assets.doctype.asset.asset.create_asset_maintenance",
        args: {
            asset: frm.doc.name,
            item_code: frm.doc.item_code,
            item_name: frm.doc.item_name,
            asset_category: frm.doc.asset_category,
            company: frm.doc.company,
        },
        callback: function(r) {
            // Sync document to local model, then navigate
            var doc = frappe.model.sync(r.message)[0];
            frappe.set_route("Form", doc.doctype, doc.name);
        }
    });
}
```

**`frappe.model.sync()` explained:** Takes the server response dictionary and stores it in Frappe's client-side `locals` object, making it available for navigation and form loading without another server round-trip.

**More complex example — create and save immediately:**
```python
@frappe.whitelist()
def create_user_from_employee(employee, email=None):
    emp = frappe.get_doc("Employee", employee)
    
    # Parse name
    parts = emp.employee_name.split(" ")
    first_name = parts[0]
    last_name = " ".join(parts[1:]) if len(parts) > 1 else ""
    
    user = frappe.new_doc("User")
    user.update({
        "email": email or emp.prefered_email,
        "first_name": first_name,
        "last_name": last_name,
        "enabled": 1,
        "gender": emp.gender,
    })
    user.insert()
    
    # Update employee with user link
    emp.user_id = user.name
    emp.save()
    
    return user.name  # Return name, not doc (caller reloads current form)
```

```javascript
// Client: reload current form instead of navigating
create_user: function(frm) {
    if (!frm.doc.prefered_email) {
        frappe.throw(__("Please enter Preferred Contact Email"));
    }
    frappe.call({
        method: "myapp.employee.create_user_from_employee",
        args: { employee: frm.doc.name },
        freeze: true,
        freeze_message: __("Creating User..."),
        callback: r => frm.reload_doc()
    });
}
```

**With child tables:**
```python
@frappe.whitelist()
def create_purchase_from_sales(sales_order):
    so = frappe.get_doc("Sales Order", sales_order)
    po = frappe.new_doc("Purchase Order")
    po.supplier = "DEFAULT-SUPPLIER"
    po.transaction_date = frappe.utils.today()
    
    for item in so.items:
        po.append("items", {
            "item_code": item.item_code,
            "qty": item.qty,
            "rate": item.rate * 0.7,  # 30% margin
        })
    
    return po  # Return draft for review
```

**Best practices:**
- Always use `@frappe.whitelist()` — without it, the method is inaccessible from JS
- Return the document (not just the name) when you want to navigate to it
- Return just the name when you want to reload the current form
- Use `freeze: true` for operations that take time
- Validate on the client side before calling the server
- Use `doc.update({...})` instead of setting fields one by one


---

## 📌 Addendum: Decorators in Frappe Controllers

### What Are Decorators?

A decorator modifies or enhances a function/method without changing its source code.

```python
@decorator
def func():
    pass
# Equivalent to: func = decorator(func)
```

### `@property` — Computed Attributes

Converts a method into a read-only attribute. Accessed like a field, computed dynamically.

```python
class AccountsController(Document):
    @property
    def company_currency(self):
        if not hasattr(self, "__company_currency"):
            self.__company_currency = get_company_currency(self.company)
        return self.__company_currency

# Usage (no parentheses!)
print(doc.company_currency)  # Not doc.company_currency()
```

**When to use `@property`:**
- Computed values based on other fields
- Lazy loading of related data
- Semantic aliases for existing fields
- Boolean checks (`is_overdue`, `is_remote_file`)

**Real examples from Frappe/ERPNext:**

```python
# frappe/core/doctype/file/file.py
@property
def is_remote_file(self):
    if self.file_url:
        return self.file_url.startswith(URL_PREFIXES)
    return not self.content

# frappe/core/doctype/communication/communication.py
@property
def sender_mailid(self):
    return parse_addr(self.sender)[1] if self.sender else ""
```

### `@cached_property` — Cached Computed Attributes

Like `@property` but caches the result after the first access. From `functools`.

```python
from functools import cached_property

class BaseDocument:
    @cached_property
    def meta(self):
        return frappe.get_meta(self.doctype)

    @cached_property
    def permitted_fieldnames(self) -> set[str]:
        return set(get_permitted_fields(doctype=self.doctype))
```

**`@property` vs `@cached_property`:**

| | `@property` | `@cached_property` |
|---|---|---|
| Computed | Every access | Only first access |
| Use for | Dynamic values | Expensive, stable values |
| Memory | No extra | Stores result |

### `@frappe.whitelist()` — API Exposure

Makes a method callable from JavaScript or external APIs.

```python
class SalesOrder(Document):
    @frappe.whitelist()
    def approve_order(self):
        self.status = "Approved"
        self.save()
        return {"status": "success"}

# Module-level function
@frappe.whitelist()
def get_pending_orders(customer=None):
    return frappe.get_all("Sales Order", filters={"status": "Pending"})

# Allow guest access
@frappe.whitelist(allow_guest=True)
def public_catalog():
    return frappe.get_all("Item", filters={"show_in_website": 1})

# Restrict HTTP method
@frappe.whitelist(methods=["POST"])
def create_order(data):
    pass
```

**Calling from JavaScript:**

```javascript
// Call doc method
frm.call({
    method: "approve_order",
    doc: frm.doc,
    callback: (r) => console.log(r.message)
});

// Call module function
frappe.call({
    method: "myapp.api.get_pending_orders",
    args: { customer: "CUST-001" },
    callback: (r) => console.log(r.message)
});
```

**Calling via Postman:**

```http
POST /api/method/run_doc_method
{ "method": "approve_order", "dt": "Sales Order", "dn": "SO-0001" }

POST /api/method/myapp.api.get_pending_orders
{ "customer": "CUST-001" }
```

### `@staticmethod` — Class-Scoped Utilities

No `self` or `cls`. Required for Virtual DocType methods.

```python
class APILog(Document):
    # Virtual DocType — these are required
    @staticmethod
    def get_list(args):
        return fetch_logs_from_api()

    @staticmethod
    def get_count(args):
        return len(fetch_logs_from_api())

    @staticmethod
    def get_stats(args):
        return {}
```

### `@classmethod` — Factory Methods

Receives the class (`cls`) instead of the instance. Useful for alternative constructors.

```python
class SalesOrder(Document):
    @classmethod
    def create_from_quotation(cls, quotation_name):
        quotation = frappe.get_doc("Quotation", quotation_name)
        order = cls({
            "doctype": "Sales Order",
            "customer": quotation.customer,
        })
        for item in quotation.items:
            order.append("items", {"item_code": item.item_code, "qty": item.qty})
        return order
```

### `@Document.hook` — Extensible Methods

Makes a method hookable — other apps can extend it via `doc_events` in `hooks.py`.

```python
# In frappe/model/document.py
class Document:
    @Document.hook
    def validate(self):
        pass  # Other apps can extend this
```

```python
# In another app's hooks.py
doc_events = {
    "Sales Order": {
        "validate": "custom_app.validations.validate_sales_order"
    }
}
```

### Custom Decorators

```python
# Permission check decorator
from functools import wraps

def require_permission(doctype, ptype="read"):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not frappe.has_permission(doctype, ptype):
                frappe.throw(f"No {ptype} permission for {doctype}")
            return func(*args, **kwargs)
        return wrapper
    return decorator

@frappe.whitelist()
@require_permission("Sales Order", "write")
def update_order(order_name, status):
    doc = frappe.get_doc("Sales Order", order_name)
    doc.status = status
    doc.save()
```

### Quick Reference

| Decorator | Purpose | Access |
|---|---|---|
| `@property` | Computed attribute, recalculated every time | `obj.attr` |
| `@cached_property` | Computed attribute, cached after first call | `obj.attr` |
| `@frappe.whitelist()` | Expose to HTTP API | `/api/method/...` |
| `@staticmethod` | Utility, no instance/class needed | `Class.method()` |
| `@classmethod` | Factory/class-level operations | `Class.method()` |
| `@Document.hook` | Extensible by other apps | Via `doc_events` |
