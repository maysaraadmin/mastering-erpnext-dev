# Chapter 4: Advanced DocType Design

## 🎯 Learning Objectives

By the end of this chapter, you will master:

- **How** DocType metadata drives database schema and UI generation
- **Why** different DocType types have specific performance characteristics
- **When** to use advanced field types for optimal data modeling
- **How** the Meta system manages metadata caching and validation
- **Advanced property setter patterns** for runtime customization
- **Performance optimization** of complex DocType structures

## 📚 Chapter Topics

### 4.1 Understanding DocType Architecture and Performance

**The DocType Metadata Engine**

DocTypes are not just data structures—they're **metadata-driven code generators** that create database tables, REST APIs, and user interfaces. Understanding this architecture is crucial for performance optimization.

#### How DocType Metadata Generates Code

```python
# Simplified version of Frappe's DocType metadata processor
class DocTypeMetadataProcessor:
    def __init__(self, doctype_name):
        self.doctype_name = doctype_name
        self.metadata = self.load_metadata()
        self.field_metadata = self.process_fields()
    
    def load_metadata(self):
        """Load DocType metadata from database"""
        meta = frappe.get_doc('DocType', self.doctype_name)
        return {
            'name': meta.name,
            'module': meta.module,
            'is_submittable': meta.is_submittable,
            'istable': meta.istable,
            'is_single': meta.is_single,
            'autoname': meta.autoname,
            'naming_rule': meta.naming_rule,
            'fields': self.extract_field_metadata(meta)
        }
    
    def generate_database_schema(self):
        """Generate SQL table creation script"""
        columns = []
        constraints = []
        indexes = []
        
        # Standard Frappe fields
        standard_fields = [
            "`name` varchar(255) NOT NULL",
            "`creation` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP",
            "`modified` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP",
            "`modified_by` varchar(255) NOT NULL",
            "`owner` varchar(255) NOT NULL",
            "`docstatus` int(11) NOT NULL DEFAULT '0'",
            "`idx` int(11) NOT NULL DEFAULT '0'"
        ]
        columns.extend(standard_fields)
        
        # Custom fields
        for field in self.field_metadata:
            column_def = self.field_to_sql_column(field)
            columns.append(column_def['sql'])
            
            # Add constraints
            if column_def.get('unique'):
                constraints.append(f"UNIQUE KEY `{field['fieldname']}` (`{field['fieldname']}`)")
            
            # Add indexes for performance
            if column_def.get('indexed'):
                indexes.append(f"INDEX `idx_{field['fieldname']}` (`{field['fieldname']}`)")
        
        # Build final SQL
        sql = f"""
            CREATE TABLE `tab{self.doctype_name}` (
                {', '.join(columns)},
                PRIMARY KEY (`name`)
                {', '.join(constraints) if constraints else ''}
                {', '.join(indexes) if indexes else ''}
            )
            ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        
        return sql
    
    def field_to_sql_column(self, field):
        """Convert field metadata to SQL column definition"""
        fieldtype_map = {
            'Data': 'varchar(255)',
            'Text': 'text',
            'Small Text': 'varchar(140)',
            'Long Text': 'longtext',
            'Int': 'int',
            'Float': 'decimal(18,6)',
            'Currency': 'decimal(18,6)',
            'Percent': 'decimal(5,2)',
            'Date': 'date',
            'Datetime': 'datetime',
            'Time': 'time',
            'Check': 'int',
            'Link': 'varchar(255)',
            'Select': 'varchar(255)',
            'Read Only': 'varchar(255)',
            'Password': 'varchar(255)',
            'Email': 'varchar(255)',
            'URL': 'varchar(255)',
            'Phone': 'varchar(255)',
            'HTML': 'longtext',
            'Code': 'longtext',
            'Markdown Editor': 'longtext',
            'Text Editor': 'longtext',
            'Signature': 'longtext',
            'Color': 'varchar(7)',
            'Icon': 'varchar(255)',
            'Rating': 'int',
            'Geolocation': 'varchar(255)',
            'JSON': 'longtext',
            'Autocomplete': 'varchar(255)',
            'Barcode': 'varchar(255)'
        }
        
        sql_type = fieldtype_map.get(field['fieldtype'], 'varchar(255)')
        
        # Add length specification
        if field.get('length') and field['fieldtype'] in ['Data', 'Small Text']:
            sql_type = f"varchar({field['length']})"
        
        # Add NOT NULL for required fields
        null_spec = "NOT NULL" if field.get('reqd') else ""
        
        # Add default value
        default_spec = ""
        if field.get('default'):
            if field['fieldtype'] in ['Check']:
                default_spec = f"DEFAULT {field['default']}"
            else:
                default_spec = f"DEFAULT '{field['default']}'"
        
        return {
            'sql': f"`{field['fieldname']}` {sql_type} {null_spec} {default_spec}",
            'unique': field.get('unique', False),
            'indexed': field.get('indexed', False)
        }
```

#### Performance Characteristics by DocType Type

```python
# Performance analysis of different DocType types
doctype_performance = {
    "Master DocType": {
        "characteristics": {
            "query_frequency": "High - frequently referenced",
            "update_frequency": "Low - relatively static",
            "relationship_count": "High - linked by many other DocTypes",
            "data_volume": "Medium to High - core business data"
        },
        "optimization_strategies": [
            "Index frequently queried fields",
            "Cache reference data",
            "Use efficient naming patterns",
            "Minimize custom fields"
        ],
        "performance_impact": {
            "read_performance": "Critical",
            "write_performance": "Medium",
            "memory_usage": "Medium"
        }
    },
    "Transaction DocType": {
        "characteristics": {
            "query_frequency": "Medium - transaction-specific queries",
            "update_frequency": "High - frequent updates",
            "relationship_count": "Medium - linked to masters and children",
            "data_volume": "High - continuous growth"
        },
        "optimization_strategies": [
            "Optimize child table queries",
            "Use efficient naming series",
            "Implement proper indexing",
            "Cache calculated fields"
        ],
        "performance_impact": {
            "read_performance": "Medium",
            "write_performance": "Critical",
            "memory_usage": "High"
        }
    },
    "Child Table DocType": {
        "characteristics": {
            "query_frequency": "High - always queried with parent",
            "update_frequency": "High - bulk operations",
            "relationship_count": "Low - belongs to one parent",
            "data_volume": "Very High - line item data"
        },
        "optimization_strategies": [
            "Composite indexes on parent fields",
            "Batch operations for bulk updates",
            "Optimize list view queries",
            "Use efficient field types"
        ],
        "performance_impact": {
            "read_performance": "Critical",
            "write_performance": "Critical",
            "memory_usage": "Very High"
        }
    },
    "Single DocType": {
        "characteristics": {
            "query_frequency": "Low - configuration data",
            "update_frequency": "Low - occasional updates",
            "relationship_count": "None - standalone",
            "data_volume": "Very Low - single record"
        },
        "optimization_strategies": [
            "Cache entire record",
            "Minimal field optimization needed",
            "Focus on validation logic"
        ],
        "performance_impact": {
            "read_performance": "Low",
            "write_performance": "Low",
            "memory_usage": "Very Low"
        }
    }
}
```

#### Advanced DocType Design Patterns

**1. Optimized Master DocType Design**

```python
# High-performance Customer Master DocType
customer_master = {
    "doctype": "DocType",
    "name": "Customer",
    "module": "Selling",
    "is_submittable": 0,
    "istable": 0,
    "naming_rule": "By fieldname",
    "autoname": "field:customer_name",
    "fields": [
        # Primary identification fields (indexed)
        {
            "fieldname": "customer_name",
            "fieldtype": "Data",
            "label": "Customer Name",
            "reqd": 1,
            "unique": 1,
            "length": 140,
            "search_index": 1
        },
        {
            "fieldname": "email",
            "fieldtype": "Data",
            "label": "Email",
            "options": "Email",
            "unique": 1,
            "search_index": 1
        },
        {
            "fieldname": "customer_group",
            "fieldtype": "Link",
            "options": "Customer Group",
            "reqd": 1,
            "search_index": 1,
            "depends_on": "eval:doc.docstatus == 0"
        },
        # Contact information (non-indexed)
        {
            "fieldname": "phone",
            "fieldtype": "Data",
            "label": "Phone",
            "options": "Phone"
        },
        {
            "fieldname": "mobile_no",
            "fieldtype": "Data",
            "label": "Mobile",
            "options": "Phone"
        },
        # Address information (child table for performance)
        {
            "fieldname": "address",
            "fieldtype": "Table",
            "options": "Address",
            "label": "Address"
        },
        # Financial information (sensitive, limited access)
        {
            "fieldname": "credit_limit",
            "fieldtype": "Currency",
            "label": "Credit Limit",
            "depends_on": "eval:doc.customer_group == 'Premium'",
            "permlevel": 1  # Requires higher permissions
        },
        # Status fields (indexed)
        {
            "fieldname": "status",
            "fieldtype": "Select",
            "options": "Active\nInactive\nBlocked",
            "default": "Active",
            "search_index": 1
        }
    ],
    "permissions": [
        {
            "role": "Sales Manager",
            "read": 1,
            "write": 1,
            "create": 1,
            "delete": 1
        },
        {
            "role": "Sales User",
            "read": 1,
            "write": 1,
            "create": 1,
            "delete": 0,
            "if_owner": 1
        }
    ]
}
```

**2. Optimized Transaction DocType Design**

```python
# High-performance Sales Order Transaction DocType
sales_order = {
    "doctype": "DocType",
    "name": "Sales Order",
    "module": "Selling",
    "is_submittable": 1,
    "istable": 0,
    "naming_rule": "By fieldname",
    "autoname": "SO-.YYYY.-.#####",
    "fields": [
        # Core transaction fields (indexed)
        {
            "fieldname": "customer",
            "fieldtype": "Link",
            "options": "Customer",
            "reqd": 1,
            "search_index": 1,
            "change_on_update": 1
        },
        {
            "fieldname": "transaction_date",
            "fieldtype": "Date",
            "default": "Today",
            "reqd": 1,
            "search_index": 1
        },
        {
            "fieldname": "delivery_date",
            "fieldtype": "Date",
            "reqd": 1,
            "search_index": 1
        },
        {
            "fieldname": "status",
            "fieldtype": "Select",
            "options": "Draft\nSubmitted\nCancelled",
            "default": "Draft",
            "search_index": 1
        },
        # Financial fields (calculated, not stored)
        {
            "fieldname": "total",
            "fieldtype": "Currency",
            "label": "Total",
            "depends_on": "eval:doc.docstatus == 1",
            "read_only": 1
        },
        {
            "fieldname": "grand_total",
            "fieldtype": "Currency",
            "label": "Grand Total",
            "depends_on": "eval:doc.docstatus == 1",
            "read_only": 1
        },
        # Child table (optimized for bulk operations)
        {
            "fieldname": "items",
            "fieldtype": "Table",
            "options": "Sales Order Item",
            "label": "Items",
            "reqd": 1
        }
    ],
    "index_web_pages_for_search": 1,
    "search_index_weight": "High"
}
```

**3. Optimized Child Table Design**

```python
# High-performance Sales Order Item Child Table
sales_order_item = {
    "doctype": "DocType",
    "name": "Sales Order Item",
    "module": "Selling",
    "is_submittable": 0,
    "istable": 1,
    "fields": [
        # Parent reference (indexed)
        {
            "fieldname": "parent",
            "fieldtype": "Link",
            "options": "Sales Order",
            "reqd": 1,
            "hidden": 1,
            "search_index": 1
        },
        {
            "fieldname": "parenttype",
            "fieldtype": "Data",
            "default": "Sales Order",
            "hidden": 1
        },
        # Item information (indexed)
        {
            "fieldname": "item_code",
            "fieldtype": "Link",
            "options": "Item",
            "reqd": 1,
            "in_list_view": 1,
            "search_index": 1
        },
        {
            "fieldname": "item_name",
            "fieldtype": "Data",
            "label": "Item Name",
            "read_only": 1,
            "in_list_view": 1
        },
        # Quantity and pricing (optimized)
        {
            "fieldname": "qty",
            "fieldtype": "Float",
            "label": "Quantity",
            "reqd": 1,
            "in_list_view": 1,
            "precision": "2"
        },
        {
            "fieldname": "rate",
            "fieldtype": "Currency",
            "label": "Rate",
            "reqd": 1,
            "in_list_view": 1,
            "precision": "2"
        },
        {
            "fieldname": "amount",
            "fieldtype": "Currency",
            "label": "Amount",
            "reqd": 1,
            "in_list_view": 1,
            "read_only": 1,
            "depends_on": "eval:doc.qty && doc.rate"
        },
        # Status fields (indexed)
        {
            "fieldname": "delivered_qty",
            "fieldtype": "Float",
            "label": "Delivered Quantity",
            "precision": "2",
            "search_index": 1
        },
        {
            "fieldname": "status",
            "fieldtype": "Select",
            "options": "Pending\nPartially Delivered\nDelivered",
            "default": "Pending",
            "search_index": 1
        }
    ],
    "permissions": [
        {
            "role": "Sales Manager",
            "read": 1,
            "write": 1,
            "create": 1,
            "delete": 1,
            "if_owner": 0
        },
        {
            "role": "Sales User",
            "read": 1,
            "write": 1,
            "create": 1,
            "delete": 0,
            "if_owner": 1
        }
    ]
}
```

### 4.2 Advanced Naming Series

#### Autoname Patterns

```python
# Different naming patterns
patterns = {
    "Sequential": "#####",                    # 1, 2, 3...
    "Year-based": "INV-.YYYY.-.#####",       # INV-2023-00001
    "Month-based": "EXP-.YYYY.MM.-.####",    # EXP-2023.01-0001
    "Field-based": "field:customer_name",    # Uses field value
    "Mixed": "PO-.####.-.field:supplier",    # PO-0001-SupplierName
    "Date-based": "DOC-.DD.MM.YYYY.-.####",   # DOC-10.03.2026-0001
    "Random": "######",                      # Random 6-digit number
}
```

#### Custom Naming Logic

```python
# Custom naming function in controller
def autoname(self):
    if self.customer_type == "Government":
        self.name = f"GOV-{self.customer_name[:3].upper()}-{frappe.utils.random_string(4)}"
    else:
        self.name = f"COM-{self.customer_name[:3].upper()}-{frappe.utils.random_string(4)}"
```

#### Naming Series Management

```python
# Create naming series
def create_naming_series():
    series = [
        "INV-.YYYY.-.#####",
        "PO-.YYYY.MM.-.####",
        "EXP-.YYYY.-.#####"
    ]
    
    for s in series:
        if not frappe.db.exists("Series", s):
            frappe.get_doc({
                "doctype": "Series",
                "name": s,
                "current": 0
            }).insert()
```

### 4.3 Field Types In Depth

#### Basic Field Types

```python
basic_fields = {
    "Data": {
        "description": "Text input field",
        "example": {"fieldtype": "Data", "label": "Name"},
        "validation": "max_length=140"
    },
    "Link": {
        "description": "Reference to another DocType",
        "example": {"fieldtype": "Link", "options": "Customer"},
        "features": ["search", "filters", "depends_on"]
    },
    "Select": {
        "description": "Dropdown selection",
        "example": {"fieldtype": "Select", "options": "Low\nMedium\nHigh"},
        "validation": "options must be newline-separated"
    },
    "Check": {
        "description": "Boolean checkbox",
        "example": {"fieldtype": "Check", "label": "Active"},
        "default": 0
    }
}
```

#### Advanced Field Types

```python
advanced_fields = {
    "Table": {
        "description": "Child table link",
        "example": {"fieldtype": "Table", "options": "Sales Order Item"},
        "features": ["add_multiple", "bulk_edit"]
    },
    "Table MultiSelect": {
        "description": "Multi-select from child table",
        "example": {"fieldtype": "Table MultiSelect", "options": "Item"},
        "use_case": "Product selection with variants"
    },
    "Dynamic Link": {
        "description": "Link to multiple DocTypes",
        "example": {
            "fieldtype": "Dynamic Link",
            "options": "reference_doctype",
            "fieldname": "reference_name"
        }
    },
    "HTML": {
        "description": "Rich text content",
        "example": {"fieldtype": "HTML", "options": "<h1>Static Content</h1>"},
        "use_case": "Instructions, help text"
    }
}
```

#### Specialized Field Types

```python
specialized_fields = {
    "Currency": {
        "description": "Monetary values",
        "example": {"fieldtype": "Currency", "options": "currency"},
        "features": ["formatting", "conversion", "precision"]
    },
    "Percent": {
        "description": "Percentage values",
        "example": {"fieldtype": "Percent", "precision": "2"},
        "validation": "0-100 range"
    },
    "Date": {
        "description": "Date picker",
        "example": {"fieldtype": "Date", "default": "Today"},
        "features": ["calendar", "range", "validation"]
    },
    "Datetime": {
        "description": "Date and time",
        "example": {"fieldtype": "Datetime", "default": "Now"},
        "features": ["timezone", "formatting"]
    },
    "Time": {
        "description": "Time picker",
        "example": {"fieldtype": "Time"},
        "format": "24-hour"
    }
}
```

#### File and Media Fields

```python
media_fields = {
    "Attach": {
        "description": "File attachment",
        "example": {"fieldtype": "Attach", "label": "Document"},
        "features": ["upload", "preview", "validation"]
    },
    "Attach Image": {
        "description": "Image attachment",
        "example": {"fieldtype": "Attach Image", "label": "Photo"},
        "features": ["thumbnail", "resize", "validation"]
    },
    "Image": {
        "description": "Image display",
        "example": {"fieldtype": "Image", "options": "photo"},
        "features": ["display", "sizing", "responsive"]
    }
}
```

### 4.4 The Meta System

#### How Metadata is Stored

```python
# DocType metadata structure
metadata_structure = {
    "DocType": {
        "table": "tabDocType",
        "key_fields": ["name", "module", "custom", "istable"],
        "relationships": {
            "fields": "DocField",
            "permissions": "DocPerm",
            "actions": "DocAction"
        }
    },
    "DocField": {
        "table": "tabDocField",
        "key_fields": ["parent", "fieldtype", "fieldname", "label"],
        "relationships": {
            "options": "various DocTypes",
            "depends_on": "conditional logic"
        }
    }
}
```

#### Loading Metadata

```python
# How Frappe loads DocType metadata
def load_doctype_meta(doctype):
    # Load from database
    meta = frappe.get_doc('DocType', doctype)
    
    # Cache for performance
    frappe.cache().hset('doctype_meta', doctype, meta.as_dict())
    
    # Process field relationships
    for field in meta.get('fields', []):
        if field.fieldtype == 'Link':
            field._options = field.options
    
    return meta
```

#### Custom Metadata

```python
# Adding custom metadata
def add_custom_metadata():
    # Custom field properties
    custom_properties = {
        "validation": {
            "min_length": 5,
            "max_length": 100,
            "pattern": r"^[A-Za-z0-9\s]+$"
        },
        "ui": {
            "width": "full",
            "css_class": "custom-field",
            "help_text": "Enter alphanumeric characters only"
        }
    }
    
    return custom_properties
```

### 4.5 Property Setters

#### Overriding Field Properties

```python
# Using Property Setters to customize fields
def create_property_setters():
    property_setters = [
        {
            "doctype": "Property Setter",
            "doc_type": "Sales Order",
            "property": "label",
            "property_type": "Data",
            "field_name": "customer",
            "value": "Client Name",
            "__newname": "Sales Order-label-customer-Client Name"
        },
        {
            "doctype": "Property Setter",
            "doc_type": "Sales Order",
            "property": "reqd",
            "property_type": "Check",
            "field_name": "delivery_date",
            "value": "1",
            "__newname": "Sales Order-reqd-delivery_date-1"
        }
    ]
    
    for ps in property_setters:
        if not frappe.db.exists("Property Setter", ps["__newname"]):
            frappe.get_doc(ps).insert()
```

#### Dynamic Property Setters

```python
# Create property setters programmatically
def set_field_properties(doctype, fieldname, properties):
    for prop, value in properties.items():
        ps_name = f"{doctype}-{prop}-{fieldname}-{value}"
        
        if not frappe.db.exists("Property Setter", ps_name):
            frappe.get_doc({
                "doctype": "Property Setter",
                "doc_type": doctype,
                "field_name": fieldname,
                "property": prop,
                "property_type": get_property_type(prop),
                "value": str(value)
            }).insert()
```

### 4.6 Matrix Child Tables

#### Creating Matrix Fields

```python
# Matrix child table configuration
matrix_config = {
    "doctype": "DocType",
    "name": "Price Matrix",
    "istable": 1,
    "fields": [
        {
            "fieldname": "item_group",
            "fieldtype": "Link",
            "options": "Item Group",
            "in_list_view": 1,
            "reqd": 1
        },
        {
            "fieldname": "price_list",
            "fieldtype": "Link",
            "options": "Price List",
            "in_list_view": 1,
            "reqd": 1
        },
        {
            "fieldname": "price",
            "fieldtype": "Currency",
            "in_list_view": 1,
            "reqd": 1
        }
    ]
}
```

#### Dynamic Matrix Generation

```python
# Generate matrix based on data
def generate_price_matrix():
    item_groups = frappe.get_all("Item Group", pluck="name")
    price_lists = frappe.get_all("Price List", pluck="name")
    
    matrix = []
    for group in item_groups:
        for price_list in price_lists:
            matrix.append({
                "item_group": group,
                "price_list": price_list,
                "price": 0
            })
    
    return matrix
```

#### Matrix Validation

```python
# Validate matrix data
def validate_matrix(doc):
    matrix_data = doc.get("price_matrix", [])
    
    # Check for duplicates
    seen = set()
    for row in matrix_data:
        key = (row.item_group, row.price_list)
        if key in seen:
            frappe.throw(f"Duplicate entry for {row.item_group} in {row.price_list}")
        seen.add(key)
    
    # Validate prices
    for row in matrix_data:
        if row.price < 0:
            frappe.throw(f"Price cannot be negative for {row.item_group}")
```

## 🛠️ Practical Exercises

### Exercise 4.1: Create Advanced DocType

Create a comprehensive DocType with:
- Multiple field types
- Custom naming series
- Property setters
- Validation logic

### Exercise 4.2: Implement Matrix Child Table

Build a matrix system for:
- Multi-dimensional data
- Dynamic generation
- Validation rules

### Exercise 4.3: Customize Existing DocType

Use property setters to:
- Modify field properties
- Add custom validation
- Enhance user experience

## 🚀 Best Practices

### DocType Design

- **Choose the right DocType type** based on use case
- **Use consistent naming conventions** across your app
- **Implement proper validation** at the field level
- **Design for scalability** with future requirements in mind

### Field Management

- **Use appropriate field types** for data validation
- **Implement field dependencies** for dynamic forms
- **Add helpful descriptions** and placeholders
- **Consider mobile responsiveness** in field layout

### Performance Optimization

- **Minimize custom fields** in high-traffic DocTypes
- **Use efficient indexing** for frequently queried fields
- **Cache metadata** for faster loading
- **Optimize child table queries** with proper filters

## 📖 Further Reading

- [DocType API Reference](https://frappeframework.com/docs/user/en/api/doc)
- [Field Types Documentation](https://frappeframework.com/docs/user/en/doctype/field-types)
- [Property Setter Guide](https://frappeframework.com/docs/user/en/doctype/property-setter)

## 🎯 Chapter Summary

Advanced DocType design is fundamental to building robust ERPNext applications:

- **DocType types** define behavior and lifecycle
- **Naming series** provide flexible document identification
- **Field types** ensure data integrity and user experience
- **Meta system** manages all DocType metadata efficiently
- **Property setters** enable customization without core modifications
- **Matrix tables** handle complex multi-dimensional data

---

**Next Chapter**: Deep dive into controller methods and document lifecycle.


---

## 📌 Addendum: fetch_from, Child DocTypes, and set_fetch_from_value

### fetch_from — Auto-populate Fields from Linked Documents

`fetch_from` lets a field automatically copy a value from a linked (Link) field's target document.  This avoids a round-trip `frappe.call` in client scripts for simple lookups.

```json
{
  "fieldname": "customer_group",
  "fieldtype": "Data",
  "label": "Customer Group",
  "fetch_from": "customer.customer_group",
  "read_only": 1,
  "in_list_view": 0
}
```

- `fetch_from` format: `<link_fieldname>.<target_fieldname>`
- The field is populated automatically when the Link field changes (client-side) and on `validate` (server-side).
- Mark the field `read_only: 1` so users cannot override the fetched value.

**Server-side equivalent — `set_fetch_from_value`:**

```python
# In your controller's validate() or before_save():
def validate(self):
    # Manually trigger fetch_from logic for all fields
    self.set_fetch_from_value()

    # Or fetch a specific value explicitly:
    if self.customer:
        self.customer_group = frappe.db.get_value('Customer', self.customer, 'customer_group')
```

`set_fetch_from_value()` is called automatically by Frappe during `validate`, but calling it explicitly is useful when you need the fetched value available earlier in the lifecycle.

### Child DocTypes (Table Fields)

A **Child DocType** (`istable: 1`) represents a one-to-many relationship — the rows of a child table belong to a single parent document.

**Key design rules:**
- Set `istable: 1` in the DocType definition.
- The child table must have `parent`, `parenttype`, and `parentfield` system fields (added automatically by Frappe).
- Reference the child DocType from the parent using a `Table` field: `"fieldtype": "Table", "options": "My Child DocType"`.
- Child DocType permissions are inherited from the parent — you do not set separate permissions on child tables.
- Use `permlevel` on child fields to restrict access to sensitive columns (e.g. cost fields visible only to managers).

```python
# Accessing child table rows in a controller
class SalesOrder(Document):
    def validate(self):
        for item in self.get('items', []):
            if item.qty <= 0:
                frappe.throw(f"Quantity must be > 0 for item {item.item_code}")
            item.amount = item.qty * item.rate

    def calculate_total(self):
        self.total = sum(item.amount for item in self.get('items', []))
```

**Bulk-inserting child rows efficiently:**

```python
# Avoid calling doc.save() in a loop — set all rows then save once
doc = frappe.get_doc('Sales Order', 'SO-0001')
for row_data in new_rows:
    doc.append('items', row_data)
doc.save()
```


---

## Addendum: Source Article Insights

### DocType: The Complete Story

A DocType is more than a database table — it's a metadata-driven definition that tells Frappe how to handle a specific type of document. The name comes from "Document Type": just as you have different types of documents in real life (invoices, contracts, reports), Frappe has different types of documents (Sales Orders, Customers, Users).

**The meta-system:** DocType definitions are themselves stored as DocType records. When you add a field to Customer via the UI, Frappe inserts a row into `tabDocField`. When you create a new DocType, Frappe creates a record in `tabDocType`. The system manages its own schema as data.

```sql
-- DocType definition stored as data
INSERT INTO tabDocType (name, module, custom, ...) VALUES ('Customer', 'Selling', 0, ...);

-- Field definitions stored as data
INSERT INTO tabDocField (parent, fieldname, fieldtype, label, ...)
VALUES ('Customer', 'customer_name', 'Data', 'Customer Name', ...);
```

**Schema sync:** When you save a DocType, Frappe automatically creates or alters the backing SQL table:
```sql
-- Frappe auto-generates this from DocType metadata
CREATE TABLE `tabCustomer` (
    `name` varchar(255) NOT NULL,
    `creation` datetime(6) DEFAULT NULL,
    `modified` datetime(6) DEFAULT NULL,
    `modified_by` varchar(255) DEFAULT NULL,
    `owner` varchar(255) DEFAULT NULL,
    `docstatus` int(1) NOT NULL DEFAULT '0',
    `customer_name` varchar(255) DEFAULT NULL,
    PRIMARY KEY (`name`)
);
```

Schema sync happens automatically when you save a DocType in the UI, or via `bench migrate` when pulling code changes.

---

### DocType Types

| Type | Storage | Use Case |
|------|---------|----------|
| Document | `tab{DocType}` | Business records (Customer, Sales Order) |
| Child Table | `tab{DocType}` with parent/parenttype/parentfield | Line items (Sales Order Item) |
| Single | `tabSingles` key-value store | Global settings (System Settings) |
| Setup | `tab{DocType}` | System definitions (Role, Module Def) |

```python
# Single DocType access
date_format = frappe.db.get_single_value("System Settings", "date_format")
settings = frappe.get_single("System Settings")

# Standard DocType access
customer = frappe.get_doc("Customer", "CUST-001")

# Child table access (always through parent)
order = frappe.get_doc("Sales Order", "SAL-001")
for item in order.items:
    print(item.item_code, item.qty)
```

---

### Child DocType Philosophy

Child DocTypes implement the **Aggregate Pattern** from Domain-Driven Design. They represent **part-of** relationships (not has-a), maintain lifecycle dependency on their parent, and operate as atomic units within the parent's transaction boundary.

**The three mandatory fields in every child record:**
```python
parent      = "SAL-001"        # Parent document name
parenttype  = "Sales Order"    # Parent DocType name
parentfield = "items"          # Field name in parent
```

**Database schema:**
```sql
CREATE TABLE `tabSales Order Item` (
    `name` VARCHAR(255) NOT NULL,
    `parent` VARCHAR(255) DEFAULT NULL,
    `parenttype` VARCHAR(255) DEFAULT NULL,
    `parentfield` VARCHAR(255) DEFAULT NULL,
    `idx` BIGINT NOT NULL DEFAULT 0,
    `item_code` VARCHAR(255) DEFAULT NULL,
    `quantity` DECIMAL(21,9) DEFAULT 0,
    `rate` DECIMAL(21,9) DEFAULT 0,
    PRIMARY KEY (`name`),
    INDEX `parent` (`parent`, `parenttype`, `parentfield`),
    INDEX `idx` (`parent`, `parentfield`, `idx`)
);
```

**Working with child tables:**
```python
# Add child row
doc = frappe.get_doc("Sales Order", "SAL-001")
doc.append("items", {
    "item_code": "ITEM-001",
    "quantity": 10,
    "rate": 100
})
doc.save()

# Iterate children
for item in doc.items:
    item.amount = item.quantity * item.rate
doc.save()

# Remove child
doc.remove(doc.items[0])
doc.save()

# Query children directly
items = frappe.get_all("Sales Order Item",
    filters={"parent": "SAL-001", "parenttype": "Sales Order"},
    fields=["item_code", "quantity", "rate"]
)
```

**Avoid the N+1 problem:**
```python
# Bad: N+1 queries
for item in parent.items:
    item_details = frappe.get_doc("Item", item.item_code)  # N queries!

# Good: batch query
item_codes = [item.item_code for item in parent.items]
items_data = {i.name: i for i in frappe.get_all("Item",
    filters={"name": ["in", item_codes]},
    fields=["name", "item_name", "standard_rate"]
)}
for item in parent.items:
    details = items_data.get(item.item_code)
```

**CDT (Child DocType) vs CDN (Child DocName):**
- CDT = the DocType name of the child table (e.g., `"Sales Order Item"`)
- CDN = the unique name of a specific child record (e.g., `"SAL-001-Sales Order Item-1"`)

In client scripts, `cdt` and `cdn` are passed to child table event handlers:
```javascript
frappe.ui.form.on('Sales Order Item', {
    quantity: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];  // Access the specific row
        row.amount = row.quantity * row.rate;
        frm.refresh_field('items');
    }
});
```

---

### Frappe Field Types Reference

Frappe supports 47 field types. The most important distinction for performance is **in-row storage**:

| Field Type | MySQL Type | In-Row Storage | Notes |
|------------|-----------|----------------|-------|
| Data | VARCHAR(140) | 140-142 bytes | Short text, indexed |
| Link | VARCHAR(140) | 140-142 bytes | Reference to another DocType |
| Select | VARCHAR(140) | 140-142 bytes | Dropdown options |
| Text | TEXT | 10 bytes | Medium content, not indexed |
| Small Text | TEXT | 10 bytes | Short content, not indexed |
| Long Text | LONGTEXT | 12 bytes | Long content |
| Int | INT | 4 bytes | Integer |
| Float | DECIMAL | varies | Decimal number |
| Currency | DECIMAL | varies | Money values |
| Date | DATE | 3 bytes | Date only |
| Datetime | DATETIME | 5+ bytes | Date + time |
| Check | INT(1) | 1 byte | Boolean 0/1 |
| Table | — | 0 bytes | Child table reference |
| Section Break | — | 0 bytes | Layout only |
| Column Break | — | 0 bytes | Layout only |

**The 65KB row size limit:** MySQL/MariaDB limits each row to 65,535 bytes. TEXT/BLOB fields store data separately and only use a 10-byte pointer in the row. VARCHAR fields store data inline.

```python
# Check row size utilization
row_size = frappe.db.get_row_size("Customer")
print(f"Row size: {row_size} bytes / 65535 bytes")

# Fix: change Data fields to Text where indexing isn't needed
# Before: description = Data (140 bytes in row)
# After:  description = Text (10 bytes in row) — saves 130 bytes
```

**Table trimming** — remove orphan database columns left behind when fields are deleted:
```bash
# Preview what will be removed
bench --site mysite.local trim-tables --dry-run

# Execute (creates backup first)
bench --site mysite.local trim-tables
```

```python
# Python API
from frappe.model.meta import trim_table, trim_tables

orphans = trim_table("Customer", dry_run=True)   # Preview
trim_table("Customer", dry_run=False)             # Execute
trim_tables(dry_run=False)                        # All tables
```
