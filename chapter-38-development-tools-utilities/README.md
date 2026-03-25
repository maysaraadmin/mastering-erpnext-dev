# Chapter 38: Development Tools and Utilities

## 🎯 Learning Objectives

By the end of this chapter, you will master:
- **Essential development tools** for Frappe development workflow
- **Permission debugging** and troubleshooting utilities
- **Role management** and access control tools
- **Performance monitoring** and optimization utilities
- **Database analysis** and query optimization tools
- **Code generation** and automation utilities
- **Testing frameworks** and debugging aids
- **Productivity enhancement** tools and shortcuts

## 📚 Chapter Topics

### 38.1 Permission Inspector Tool

**Overview**

The Permission Inspector is a powerful debugging tool that helps you understand why a user has or doesn't have specific permissions. It provides detailed logs explaining permission decisions, shows all roles the user has, and identifies which rules are matching or not matching.

**Location:** `/app/permission-inspector`

**What it does:**
- Tests permission for specific combinations of DocType, Document, User, and Permission Type
- Provides detailed logs explaining why permissions are granted or denied
- Shows all roles the user has
- Shows all permission rules that apply
- Identifies which rules are matching and which are not

**When to use:**
- Debugging permission issues
- Understanding complex permission scenarios
- Verifying permission configurations
- Troubleshooting access problems

**Permission Inspector Implementation:**
```python
# your_app/utils/permission_inspector.py
import frappe
from frappe.permissions import get_user_permissions, get_permission_query_conditions

class PermissionInspector:
    def __init__(self):
        self.permission_logs = []
    
    def inspect_permission(self, doctype, docname, user, permission_type):
        """Inspect permission for specific combination"""
        result = {
            'doctype': doctype,
            'docname': docname,
            'user': user,
            'permission_type': permission_type,
            'has_permission': False,
            'explanation': [],
            'user_roles': [],
            'permission_rules': [],
            'matching_rules': [],
            'non_matching_rules': []
        }
        
        # Get user roles
        user_roles = frappe.get_roles(user)
        result['user_roles'] = user_roles
        
        # Check if user has permission
        has_permission = frappe.has_permission(doctype, permission_type, docname, user)
        result['has_permission'] = has_permission
        
        # Get permission rules for this doctype
        permission_rules = self.get_permission_rules(doctype)
        result['permission_rules'] = permission_rules
        
        # Analyze each rule
        for rule in permission_rules:
            rule_result = self.analyze_permission_rule(rule, user_roles, docname, permission_type)
            if rule_result['matches']:
                result['matching_rules'].append(rule_result)
            else:
                result['non_matching_rules'].append(rule_result)
        
        # Generate explanation
        result['explanation'] = self.generate_explanation(result)
        
        return result
    
    def get_permission_rules(self, doctype):
        """Get all permission rules for a doctype"""
        rules = []
        
        # Get custom permissions
        custom_perms = frappe.get_all('Custom Permission',
            filters={'document_type': doctype},
            fields=['name', 'role', 'allow', 'read', 'write', 'create', 'delete', 'submit', 'cancel', 'amend']
        )
        
        for perm in custom_perms:
            rules.append({
                'type': 'Custom Permission',
                'name': perm.name,
                'role': perm.role,
                'permissions': {
                    'allow': perm.allow,
                    'read': perm.read,
                    'write': perm.write,
                    'create': perm.create,
                    'delete': perm.delete,
                    'submit': perm.submit,
                    'cancel': perm.cancel,
                    'amend': perm.amend
                }
            })
        
        # Get standard permissions
        standard_perms = frappe.get_all('DocPerm',
            filters={'parent': doctype},
            fields=['role', 'read', 'write', 'create', 'delete', 'submit', 'cancel', 'amend']
        )
        
        for perm in standard_perms:
            rules.append({
                'type': 'Standard Permission',
                'name': f"Standard {perm.role}",
                'role': perm.role,
                'permissions': {
                    'read': perm.read,
                    'write': perm.write,
                    'create': perm.create,
                    'delete': perm.delete,
                    'submit': perm.submit,
                    'cancel': perm.cancel,
                    'amend': perm.amend
                }
            })
        
        return rules
    
    def analyze_permission_rule(self, rule, user_roles, docname, permission_type):
        """Analyze if a permission rule matches"""
        result = {
            'rule': rule,
            'matches': False,
            'reason': '',
            'permission_value': None
        }
        
        # Check if user has the required role
        if rule['role'] not in user_roles:
            result['reason'] = f"User does not have role '{rule['role']}'"
            return result
        
        # Check if permission type is allowed
        permissions = rule['permissions']
        if permission_type in permissions:
            permission_value = permissions[permission_type]
            result['permission_value'] = permission_value
            result['matches'] = permission_value == 1
            result['reason'] = f"Permission '{permission_type}' is {'allowed' if permission_value else 'not allowed'} for role '{rule['role']}'"
        else:
            result['reason'] = f"Permission type '{permission_type}' not defined in rule"
        
        return result
    
    def generate_explanation(self, result):
        """Generate human-readable explanation"""
        explanation = []
        
        if result['has_permission']:
            explanation.append(f"User '{result['user']}' has {result['permission_type']} permission on {result['doctype']} '{result['docname']}'")
            
            if result['matching_rules']:
                explanation.append("Matching permission rules:")
                for rule in result['matching_rules']:
                    explanation.append(f"  - {rule['rule']['type']} '{rule['rule']['name']}': {rule['reason']}")
        else:
            explanation.append(f"User '{result['user']}' does NOT have {result['permission_type']} permission on {result['doctype']} '{result['docname']}'")
            
            if result['non_matching_rules']:
                explanation.append("Non-matching permission rules:")
                for rule in result['non_matching_rules']:
                    explanation.append(f"  - {rule['rule']['type']} '{rule['rule']['name']}': {rule['reason']}")
        
        return explanation

# Permission Inspector API endpoint
@frappe.whitelist()
def inspect_permission(doctype, docname, user, permission_type):
    """API endpoint for permission inspection"""
    inspector = PermissionInspector()
    result = inspector.inspect_permission(doctype, docname, user, permission_type)
    return result
```

**Permission Inspector Frontend:**
```javascript
// your_app/public/js/permission_inspector.js
frappe.pages['permission-inspector'].on_page_load = function(wrapper) {
    new PermissionInspector(wrapper);
}

class PermissionInspector {
    constructor(wrapper) {
        this.wrapper = $(wrapper);
        this.page = frappe.ui.make_app_page({
            parent: wrapper,
            title: 'Permission Inspector',
            single_column: true
        });
        
        this.make_form();
        this.bind_events();
    }
    
    make_form() {
        let fields = [
            {
                fieldname: 'doctype',
                fieldtype: 'Link',
                options: 'DocType',
                label: 'DocType',
                reqd: 1
            },
            {
                fieldname: 'docname',
                fieldtype: 'Data',
                label: 'Document Name',
                reqd: 1
            },
            {
                fieldname: 'user',
                fieldtype: 'Link',
                options: 'User',
                label: 'User',
                reqd: 1,
                default: frappe.session.user
            },
            {
                fieldname: 'permission_type',
                fieldtype: 'Select',
                label: 'Permission Type',
                options: 'read\nwrite\ncreate\ndelete\nsubmit\ncancel\namend',
                reqd: 1
            },
            {
                fieldname: 'inspect_button',
                fieldtype: 'Button',
                label: 'Inspect Permission',
                click: () => this.inspect_permission()
            }
        ];
        
        this.form = new frappe.ui.Dialog({
            title: 'Inspect Permission',
            fields: fields,
            primary_action_label: 'Inspect',
            primary_action: () => this.inspect_permission()
        });
        
        this.form.show();
    }
    
    inspect_permission() {
        let values = this.form.get_values();
        
        if (!values) return;
        
        frappe.call({
            method: 'your_app.utils.permission_inspector.inspect_permission',
            args: {
                doctype: values.doctype,
                docname: values.docname,
                user: values.user,
                permission_type: values.permission_type
            },
            callback: (response) => {
                this.show_results(response.message);
            }
        });
    }
    
    show_results(result) {
        this.form.hide();
        
        let html = `
            <div class="permission-inspection-results">
                <div class="result-header">
                    <h3>Permission Inspection Results</h3>
                    <div class="result-badge ${result.has_permission ? 'success' : 'danger'}">
                        ${result.has_permission ? 'PERMISSION GRANTED' : 'PERMISSION DENIED'}
                    </div>
                </div>
                
                <div class="result-details">
                    <div class="section">
                        <h4>User Information</h4>
                        <p><strong>User:</strong> ${result.user}</p>
                        <p><strong>Roles:</strong> ${result.user_roles.join(', ')}</p>
                    </div>
                    
                    <div class="section">
                        <h4>Permission Details</h4>
                        <p><strong>DocType:</strong> ${result.doctype}</p>
                        <p><strong>Document:</strong> ${result.docname}</p>
                        <p><strong>Permission Type:</strong> ${result.permission_type}</p>
                    </div>
                    
                    <div class="section">
                        <h4>Explanation</h4>
                        <ul>
                            ${result.explanation.map(explanation => `<li>${explanation}</li>`).join('')}
                        </ul>
                    </div>
                    
                    <div class="section">
                        <h4>Matching Rules</h4>
                        ${this.render_rules(result.matching_rules)}
                    </div>
                    
                    <div class="section">
                        <h4>Non-Matching Rules</h4>
                        ${this.render_rules(result.non_matching_rules)}
                    </div>
                </div>
            </div>
        `;
        
        this.page.main.html(html);
    }
    
    render_rules(rules) {
        if (!rules || rules.length === 0) {
            return '<p>No rules found</p>';
        }
        
        return rules.map(rule => `
            <div class="rule-item ${rule.matches ? 'match' : 'no-match'}">
                <div class="rule-header">
                    <strong>${rule.rule.type}</strong>: ${rule.rule.name}
                </div>
                <div class="rule-details">
                    <p><strong>Role:</strong> ${rule.rule.role}</p>
                    <p><strong>Reason:</strong> ${rule.reason}</p>
                    ${rule.permission_value !== null ? `<p><strong>Permission Value:</strong> ${rule.permission_value}</p>` : ''}
                </div>
            </div>
        `).join('');
    }
    
    bind_events() {
        // Auto-fetch document name when doctype changes
        this.form.get_field('doctype').$input.on('change', () => {
            let doctype = this.form.get_value('doctype');
            if (doctype) {
                this.fetch_document_names(doctype);
            }
        });
    }
    
    fetch_document_names(doctype) {
        frappe.call({
            method: 'frappe.db.get_all',
            args: {
                doctype: doctype,
                fields: ['name'],
                limit: 100
            },
            callback: (response) => {
                let options = response.message.map(doc => doc.name).join('\n');
                this.form.get_field('docname').df.options = options;
                this.form.get_field('docname').refresh();
            }
        });
    }
}
```

### 38.2 Role Permission Manager

**Overview**

The Role Permission Manager is a tool for reviewing and managing permissions for a specific role on a specific DocType. It provides a comprehensive view of all permissions and allows for easy modification.

**Location:** `/app/permission-manager`

**What it does:**
- Reviews and manages permissions for a specific role on a specific DocType
- Shows all available permission types
- Allows bulk permission updates
- Provides permission conflict detection
- Shows permission dependencies

**Role Permission Manager Implementation:**
```python
# your_app/utils/role_permission_manager.py
import frappe

class RolePermissionManager:
    def __init__(self):
        self.permission_types = ['read', 'write', 'create', 'delete', 'submit', 'cancel', 'amend']
    
    def get_role_permissions(self, role, doctype):
        """Get all permissions for a role on a doctype"""
        permissions = {
            'role': role,
            'doctype': doctype,
            'standard_permissions': {},
            'custom_permissions': {},
            'conflicts': [],
            'dependencies': []
        }
        
        # Get standard permissions
        standard_perms = frappe.get_all('DocPerm',
            filters={'parent': doctype, 'role': role},
            fields=['read', 'write', 'create', 'delete', 'submit', 'cancel', 'amend']
        )
        
        if standard_perms:
            permissions['standard_permissions'] = standard_perms[0]
        
        # Get custom permissions
        custom_perms = frappe.get_all('Custom Permission',
            filters={'document_type': doctype, 'role': role},
            fields=['name', 'read', 'write', 'create', 'delete', 'submit', 'cancel', 'amend']
        )
        
        for perm in custom_perms:
            permissions['custom_permissions'][perm.name] = perm
        
        # Check for conflicts
        permissions['conflicts'] = self.detect_permission_conflicts(permissions)
        
        # Get dependencies
        permissions['dependencies'] = self.get_permission_dependencies(role, doctype)
        
        return permissions
    
    def detect_permission_conflicts(self, permissions):
        """Detect permission conflicts between standard and custom permissions"""
        conflicts = []
        
        standard_perms = permissions['standard_permissions']
        custom_perms = permissions['custom_permissions']
        
        for perm_type in self.permission_types:
            standard_value = standard_perms.get(perm_type, 0)
            
            for custom_name, custom_perm in custom_perms.items():
                custom_value = getattr(custom_perm, perm_type, 0)
                
                if standard_value != custom_value:
                    conflicts.append({
                        'permission_type': perm_type,
                        'standard_value': standard_value,
                        'custom_value': custom_value,
                        'custom_permission': custom_name,
                        'conflict_type': 'value_mismatch'
                    })
        
        return conflicts
    
    def get_permission_dependencies(self, role, doctype):
        """Get permission dependencies for a role on a doctype"""
        dependencies = []
        
        # Check if role has dependencies on other roles
        role_doc = frappe.get_doc('Role', role)
        if hasattr(role_doc, 'role_privileges') and role_doc.role_privileges:
            for privilege in role_doc.role_privileges:
                if privilege.role:
                    dependencies.append({
                        'type': 'role_dependency',
                        'depends_on': privilege.role,
                        'description': f"Depends on role '{privilege.role}'"
                    })
        
        # Check if doctype has dependencies on other doctypes
        if hasattr(frappe.get_doc(doctype), 'permissions'):
            doctype_doc = frappe.get_doc(doctype)
            for perm in doctype_doc.permissions:
                if perm.role == role and perm.permlevel > 0:
                    dependencies.append({
                        'type': 'permission_level_dependency',
                        'permlevel': perm.permlevel,
                        'description': f"Requires permission level {perm.permlevel}"
                    })
        
        return dependencies
    
    def update_role_permissions(self, role, doctype, permissions):
        """Update permissions for a role on a doctype"""
        try:
            # Update or create standard permissions
            standard_perm = frappe.db.exists('DocPerm', {'parent': doctype, 'role': role})
            
            if standard_perm:
                doc = frappe.get_doc('DocPerm', standard_perm)
            else:
                doc = frappe.new_doc('DocPerm')
                doc.parent = doctype
                doc.parenttype = 'DocType'
                doc.parentfield = 'permissions'
                doc.role = role
            
            # Update permission values
            for perm_type, value in permissions.items():
                if perm_type in self.permission_types:
                    setattr(doc, perm_type, value)
            
            doc.save()
            
            return {'success': True, 'message': 'Permissions updated successfully'}
            
        except Exception as e:
            return {'success': False, 'message': str(e)}

# Role Permission Manager API endpoints
@frappe.whitelist()
def get_role_permissions(role, doctype):
    """Get role permissions"""
    manager = RolePermissionManager()
    return manager.get_role_permissions(role, doctype)

@frappe.whitelist()
def update_role_permissions(role, doctype, permissions):
    """Update role permissions"""
    manager = RolePermissionManager()
    return manager.update_role_permissions(role, doctype, permissions)
```

### 38.3 Performance Analysis Tools

**Database Performance Monitor**

```python
# your_app/utils/performance_monitor.py
import frappe
import time
import psutil
from collections import defaultdict

class PerformanceMonitor:
    def __init__(self):
        self.query_times = []
        self.memory_usage = []
        self.cpu_usage = []
        self.request_times = []
    
    def start_monitoring(self):
        """Start performance monitoring"""
        self.start_time = time.time()
        self.initial_memory = psutil.Process().memory_info().rss
    
    def stop_monitoring(self):
        """Stop performance monitoring and collect metrics"""
        self.end_time = time.time()
        self.final_memory = psutil.Process().memory_info().rss
        
        return {
            'total_time': self.end_time - self.start_time,
            'memory_used': self.final_memory - self.initial_memory,
            'query_times': self.query_times,
            'request_times': self.request_times
        }
    
    def log_query_time(self, query, execution_time):
        """Log query execution time"""
        self.query_times.append({
            'query': query,
            'time': execution_time,
            'timestamp': time.time()
        })
    
    def log_request_time(self, endpoint, execution_time):
        """Log request execution time"""
        self.request_times.append({
            'endpoint': endpoint,
            'time': execution_time,
            'timestamp': time.time()
        })
    
    def get_performance_summary(self):
        """Get performance summary"""
        if not self.query_times:
            return {}
        
        query_times = [q['time'] for q in self.query_times]
        request_times = [r['time'] for r in self.request_times]
        
        return {
            'queries': {
                'count': len(query_times),
                'total_time': sum(query_times),
                'avg_time': sum(query_times) / len(query_times),
                'max_time': max(query_times),
                'min_time': min(query_times)
            },
            'requests': {
                'count': len(request_times),
                'total_time': sum(request_times),
                'avg_time': sum(request_times) / len(request_times) if request_times else 0,
                'max_time': max(request_times) if request_times else 0,
                'min_time': min(request_times) if request_times else 0
            },
            'slow_queries': [q for q in self.query_times if q['time'] > 1.0],
            'memory_usage': self.memory_usage,
            'cpu_usage': self.cpu_usage
        }

# Performance monitoring middleware
def monitor_request_performance():
    """Monitor request performance"""
    if frappe.conf.developer_mode:
        monitor = PerformanceMonitor()
        monitor.start_monitoring()
        
        # Store monitor in frappe.local for access during request
        frappe.local.performance_monitor = monitor

def log_request_performance():
    """Log request performance at the end of request"""
    if hasattr(frappe.local, 'performance_monitor'):
        monitor = frappe.local.performance_monitor
        results = monitor.stop_monitoring()
        
        # Log to console in development mode
        if frappe.conf.developer_mode:
            print(f"Request completed in {results['total_time']:.3f}s")
            print(f"Memory used: {results['memory_used'] / 1024 / 1024:.2f} MB")
            print(f"Queries executed: {len(results['query_times'])}")
```

**Query Optimizer**

```python
# your_app/utils/query_optimizer.py
import frappe
import re
from collections import defaultdict

class QueryOptimizer:
    def __init__(self):
        self.query_patterns = {
            'slow_select': re.compile(r'SELECT.*FROM.*WHERE.*', re.IGNORECASE),
            'missing_index': re.compile(r'.*WHERE.*\w+\s*=.*', re.IGNORECASE),
            'n_plus_one': re.compile(r'.*SELECT.*FROM.*WHERE.*IN.*', re.IGNORECASE)
        }
    
    def analyze_query(self, query):
        """Analyze a SQL query for optimization opportunities"""
        analysis = {
            'query': query,
            'issues': [],
            'suggestions': [],
            'estimated_cost': self.estimate_query_cost(query)
        }
        
        # Check for common performance issues
        self.check_missing_indexes(query, analysis)
        self.check_n_plus_one(query, analysis)
        self.check_select_star(query, analysis)
        self.check_missing_where(query, analysis)
        
        return analysis
    
    def check_missing_indexes(self, query, analysis):
        """Check for queries that could benefit from indexes"""
        if 'WHERE' in query.upper():
            # Extract WHERE clause
            where_match = re.search(r'WHERE\s+(.+?)(?:\s+(?:ORDER|GROUP|LIMIT)|$)', query, re.IGNORECASE)
            if where_match:
                where_clause = where_match.group(1)
                
                # Look for equality conditions that should be indexed
                equality_matches = re.findall(r'(\w+)\s*=\s*', where_clause)
                for column in equality_matches:
                    analysis['issues'].append({
                        'type': 'missing_index',
                        'column': column,
                        'description': f"Column '{column}' in WHERE clause may benefit from an index",
                        'suggestion': f"CREATE INDEX idx_{column} ON table ({column})"
                    })
    
    def check_n_plus_one(self, query, analysis):
        """Check for N+1 query patterns"""
        if 'IN' in query.upper() and 'SELECT' in query.upper():
            analysis['issues'].append({
                'type': 'n_plus_one',
                'description': 'Query may be part of N+1 pattern',
                'suggestion': 'Consider using JOIN or bulk operations'
            })
    
    def check_select_star(self, query, analysis):
        """Check for SELECT * queries"""
        if re.search(r'SELECT\s+\*\s+FROM', query, re.IGNORECASE):
            analysis['issues'].append({
                'type': 'select_star',
                'description': 'SELECT * can be inefficient',
                'suggestion': 'Specify only required columns'
            })
    
    def check_missing_where(self, query, analysis):
        """Check for queries without WHERE clauses on large tables"""
        if 'WHERE' not in query.upper():
            analysis['issues'].append({
                'type': 'missing_where',
                'description': 'Query without WHERE clause may scan entire table',
                'suggestion': 'Add WHERE clause to limit results'
            })
    
    def estimate_query_cost(self, query):
        """Estimate query execution cost (simplified)"""
        cost = 1.0
        
        # Add cost for SELECT *
        if re.search(r'SELECT\s+\*\s+FROM', query, re.IGNORECASE):
            cost += 0.5
        
        # Add cost for missing WHERE
        if 'WHERE' not in query.upper():
            cost += 1.0
        
        # Add cost for JOIN operations
        join_count = len(re.findall(r'\bJOIN\b', query, re.IGNORECASE))
        cost += join_count * 0.3
        
        # Add cost for subqueries
        subquery_count = len(re.findall(r'\(SELECT.*?\)', query, re.IGNORECASE))
        cost += subquery_count * 0.4
        
        return cost

# Query optimizer API
@frappe.whitelist()
def optimize_query(query):
    """Optimize a SQL query"""
    optimizer = QueryOptimizer()
    return optimizer.analyze_query(query)

@frappe.whitelist()
def get_slow_queries(limit=50):
    """Get slow queries from the database"""
    if frappe.conf.developer_mode:
        # In development, get from frappe.local
        if hasattr(frappe.local, 'performance_monitor'):
            monitor = frappe.local.performance_monitor
            slow_queries = [q for q in monitor.query_times if q['time'] > 1.0]
            return slow_queries[:limit]
    
    # In production, check database logs
    return frappe.db.sql("""
        SELECT query_time, sql_text, start_time
        FROM mysql.slow_log
        WHERE start_time > DATE_SUB(NOW(), INTERVAL 1 HOUR)
        ORDER BY query_time DESC
        LIMIT %s
    """, (limit,), as_dict=True)
```

### 38.4 Code Generation Tools

**DocType Generator**

```python
# your_app/utils/code_generator.py
import frappe
import json
from jinja2 import Template

class CodeGenerator:
    def __init__(self):
        self.templates = self.load_templates()
    
    def load_templates(self):
        """Load code generation templates"""
        templates = {}
        
        # DocType template
        templates['doctype'] = Template("""
# {{ doc_type }}.py
import frappe
from frappe.model.document import Document

class {{ class_name }}(Document):
    {% for method in methods %}
    def {{ method.name }}(self):
        """{{ method.description }}"""
        {% if method.code %}
        {{ method.code | indent(8) }}
        {% endif %}
        pass
    
    {% endfor %}
    
    def validate(self):
        super().validate()
        # Custom validation logic here
    
    def on_update(self):
        super().on_update()
        # Custom update logic here
    
    def on_submit(self):
        super().on_submit()
        # Custom submit logic here
        """)
        
        # Controller template
        templates['controller'] = Template("""
# {{ doc_type }}_controller.py
import frappe
from frappe.model.controller import Controller

class {{ class_name }}Controller(Controller):
    {% for method in methods %}
    def {{ method.name }}(self):
        """{{ method.description }}"""
        {% if method.code %}
        {{ method.code | indent(8) }}
        {% endif %}
        pass
    
    {% endfor %}
    """)
        
        # API template
        templates['api'] = Template("""
# {{ doc_type }}_api.py
import frappe

@frappe.whitelist()
def get_{{ doc_type.lower().replace(' ', '_') }}(docname):
    """Get {{ doc_type }} details"""
    doc = frappe.get_doc('{{ doc_type }}', docname)
    return doc.as_dict()

@frappe.whitelist()
def create_{{ doc_type.lower().replace(' ', '_') }}(data):
    """Create new {{ doc_type }}"""
    doc = frappe.new_doc('{{ doc_type }}')
    doc.update(data)
    doc.insert()
    return doc.name

@frappe.whitelist()
def update_{{ doc_type.lower().replace(' ', '_') }}(docname, data):
    """Update {{ doc_type }}"""
    doc = frappe.get_doc('{{ doc_type }}', docname)
    doc.update(data)
    doc.save()
    return doc.name

@frappe.whitelist()
def delete_{{ doc_type.lower().replace(' ', '_') }}(docname):
    """Delete {{ doc_type }}"""
    frappe.delete_doc('{{ doc_type }}', docname)
    return True
    """)
        
        return templates
    
    def generate_doctype_code(self, doc_type, fields, methods=None):
        """Generate DocType code"""
        class_name = ''.join(word.capitalize() for word in doc_type.split())
        
        if methods is None:
            methods = [
                {'name': 'custom_method', 'description': 'Custom method', 'code': ''}
            ]
        
        template = self.templates['doctype']
        code = template.render(
            doc_type=doc_type,
            class_name=class_name,
            methods=methods
        )
        
        return code
    
    def generate_api_code(self, doc_type):
        """Generate API endpoints for DocType"""
        template = self.templates['api']
        code = template.render(doc_type=doc_type)
        
        return code
    
    def generate_test_code(self, doc_type, test_scenarios=None):
        """Generate test code for DocType"""
        if test_scenarios is None:
            test_scenarios = [
                {'name': 'test_create', 'description': 'Test creating document'},
                {'name': 'test_update', 'description': 'Test updating document'},
                {'name': 'test_delete', 'description': 'Test deleting document'}
            ]
        
        template = Template("""
# test_{{ doc_type.lower().replace(' ', '_') }}.py
import frappe
import unittest

class Test{{ class_name }}(unittest.TestCase):
    def setUp(self):
        """Setup test environment"""
        self.doc_data = {
            # Add test data here
        }
    
    {% for scenario in test_scenarios %}
    def {{ scenario.name }}(self):
        """{{ scenario.description }}"""
        # Add test implementation here
        pass
    
    {% endfor %}
    
    def tearDown(self):
        """Cleanup test environment"""
        pass
        """)
        
        class_name = ''.join(word.capitalize() for word in doc_type.split())
        code = template.render(
            doc_type=doc_type,
            class_name=class_name,
            test_scenarios=test_scenarios
        )
        
        return code

# Code generator API endpoints
@frappe.whitelist()
def generate_doctype_code(doc_type, fields, methods=None):
    """Generate DocType code"""
    generator = CodeGenerator()
    
    if isinstance(fields, str):
        fields = json.loads(fields)
    
    if isinstance(methods, str):
        methods = json.loads(methods)
    
    return {
        'doctype_code': generator.generate_doctype_code(doc_type, fields, methods),
        'api_code': generator.generate_api_code(doc_type),
        'test_code': generator.generate_test_code(doc_type)
    }

@frappe.whitelist()
def generate_custom_report(report_name, doctype, fields=None):
    """Generate custom report code"""
    template = Template("""
# {{ report_name }}.py
import frappe
from frappe import _

def execute(filters=None):
    """Execute custom report"""
    columns = get_columns()
    data = get_data(filters)
    
    return columns, data

def get_columns():
    """Get report columns"""
    return [
        {"label": _("Name"), "fieldname": "name", "fieldtype": "Data", "width": 150},
        {"label": _("Created"), "fieldname": "creation", "fieldtype": "Datetime", "width": 150},
        {"label": _("Modified"), "fieldname": "modified", "fieldtype": "Datetime", "width": 150}
    ]

def get_data(filters):
    """Get report data"""
    conditions = build_conditions(filters)
    
    data = frappe.db.sql(f"""
        SELECT name, creation, modified
        FROM `tab{{ doctype }}`
        {conditions}
        ORDER BY creation DESC
    """, filters, as_dict=True)
    
    return data

def build_conditions(filters):
    """Build SQL conditions from filters"""
    conditions = []
    
    if filters and filters.get('from_date'):
        conditions.append(f"creation >= '{filters['from_date']}'")
    
    if filters and filters.get('to_date'):
        conditions.append(f"creation <= '{filters['to_date']}'")
    
    if conditions:
        return "WHERE " + " AND ".join(conditions)
    
    return ""
    """)
    
    code = template.render(
        report_name=report_name,
        doctype=doctype
    )
    
    return code
```

### 38.5 Testing and Debugging Tools

**Enhanced Test Runner**

```python
# your_app/utils/test_runner.py
import frappe
import unittest
import time
from collections import defaultdict

class EnhancedTestRunner:
    def __init__(self):
        self.test_results = defaultdict(list)
        self.coverage_data = {}
        self.performance_data = {}
    
    def run_tests(self, test_modules=None, coverage=False, performance=False):
        """Run tests with enhanced features"""
        if test_modules is None:
            test_modules = self.discover_test_modules()
        
        results = {
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'errors': 0,
            'skipped': 0,
            'coverage': {},
            'performance': {},
            'test_results': []
        }
        
        for module in test_modules:
            module_results = self.run_module_tests(module, coverage, performance)
            
            # Aggregate results
            results['total_tests'] += module_results['total_tests']
            results['passed'] += module_results['passed']
            results['failed'] += module_results['failed']
            results['errors'] += module_results['errors']
            results['skipped'] += module_results['skipped']
            
            results['test_results'].extend(module_results['test_results'])
            
            if coverage:
                results['coverage'][module] = module_results['coverage']
            
            if performance:
                results['performance'][module] = module_results['performance']
        
        return results
    
    def discover_test_modules(self):
        """Discover all test modules"""
        test_modules = []
        
        # Get all test files in the app
        import os
        app_path = frappe.get_app_path('your_app')
        test_path = os.path.join(app_path, 'tests')
        
        if os.path.exists(test_path):
            for file in os.listdir(test_path):
                if file.startswith('test_') and file.endswith('.py'):
                    module_name = file[:-3]  # Remove .py extension
                    test_modules.append(f'your_app.tests.{module_name}')
        
        return test_modules
    
    def run_module_tests(self, module, coverage=False, performance=False):
        """Run tests for a specific module"""
        suite = unittest.TestLoader().loadTestsFromName(module)
        runner = unittest.TextTestRunner(verbosity=2, stream=frappe.local.stdout)
        
        start_time = time.time()
        result = runner.run(suite)
        end_time = time.time()
        
        module_results = {
            'module': module,
            'total_tests': result.testsRun,
            'passed': result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped),
            'failed': len(result.failures),
            'errors': len(result.errors),
            'skipped': len(result.skipped),
            'execution_time': end_time - start_time,
            'test_results': []
        }
        
        # Process individual test results
        for test, error in result.failures + result.errors:
            module_results['test_results'].append({
                'test': str(test),
                'status': 'failed' if test in [f[0] for f in result.failures] else 'error',
                'error': error,
                'execution_time': 0  # Could be enhanced with timing
            })
        
        for test, reason in result.skipped:
            module_results['test_results'].append({
                'test': str(test),
                'status': 'skipped',
                'reason': reason,
                'execution_time': 0
            })
        
        # Add coverage data if requested
        if coverage:
            module_results['coverage'] = self.calculate_coverage(module)
        
        # Add performance data if requested
        if performance:
            module_results['performance'] = self.get_performance_metrics(module)
        
        return module_results
    
    def calculate_coverage(self, module):
        """Calculate code coverage for a module"""
        # This is a simplified implementation
        # In practice, you'd use coverage.py or similar
        return {
            'lines_covered': 150,
            'total_lines': 200,
            'coverage_percentage': 75.0,
            'uncovered_lines': [45, 67, 89, 123]
        }
    
    def get_performance_metrics(self, module):
        """Get performance metrics for tests"""
        return {
            'avg_test_time': 0.5,
            'max_test_time': 2.1,
            'min_test_time': 0.1,
            'memory_usage': 50.5  # MB
        }

# Test runner API
@frappe.whitelist()
def run_tests(test_modules=None, coverage=False, performance=False):
    """Run tests with enhanced features"""
    runner = EnhancedTestRunner()
    return runner.run_tests(test_modules, coverage, performance)

@frappe.whitelist()
def get_test_coverage(module):
    """Get code coverage for a specific module"""
    runner = EnhancedTestRunner()
    return runner.calculate_coverage(module)
```

**Debug Helper**

```python
# your_app/utils/debug_helper.py
import frappe
import json
import traceback
from datetime import datetime

class DebugHelper:
    def __init__(self):
        self.debug_logs = []
        self.breakpoints = {}
        self.watch_variables = {}
    
    def log_debug_info(self, message, data=None, context=None):
        """Log debug information"""
        debug_entry = {
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'data': data,
            'context': context or self.get_current_context(),
            'user': frappe.session.user,
            'request_url': frappe.request.url if frappe.request else None
        }
        
        self.debug_logs.append(debug_entry)
        
        # Log to file if in development mode
        if frappe.conf.developer_mode:
            frappe.log_error(debug_entry, "Debug Log")
    
    def get_current_context(self):
        """Get current execution context"""
        context = {
            'doctype': getattr(frappe.local, 'doctype', None),
            'docname': getattr(frappe.local, 'docname', None),
            'form_dict': getattr(frappe.local, 'form_dict', {}),
            'request': {
                'method': getattr(frappe.request, 'method', None),
                'url': getattr(frappe.request, 'url', None)
            }
        }
        return context
    
    def set_breakpoint(self, name, condition=None):
        """Set a breakpoint"""
        self.breakpoints[name] = {
            'condition': condition,
            'hit_count': 0,
            'created_at': datetime.now().isoformat()
        }
    
    def check_breakpoint(self, name):
        """Check if breakpoint should trigger"""
        if name not in self.breakpoints:
            return False
        
        breakpoint = self.breakpoints[name]
        breakpoint['hit_count'] += 1
        
        if breakpoint['condition']:
            try:
                # Evaluate condition in current context
                return eval(breakpoint['condition'])
            except:
                return False
        
        return True
    
    def watch_variable(self, name, variable):
        """Watch a variable for changes"""
        current_value = self.get_variable_value(variable)
        self.watch_variables[name] = {
            'variable': variable,
            'initial_value': current_value,
            'current_value': current_value,
            'changes': []
        }
    
    def get_variable_value(self, variable):
        """Get current value of a variable"""
        try:
            # Try to get from global namespace
            if variable in globals():
                return globals()[variable]
            
            # Try to get from frappe.local
            if hasattr(frappe.local, variable):
                return getattr(frappe.local, variable)
            
            # Try to evaluate as expression
            return eval(variable)
        except:
            return None
    
    def check_variable_changes(self):
        """Check for variable changes"""
        for name, watch in self.watch_variables.items():
            current_value = self.get_variable_value(watch['variable'])
            
            if current_value != watch['current_value']:
                change = {
                    'timestamp': datetime.now().isoformat(),
                    'old_value': watch['current_value'],
                    'new_value': current_value
                }
                
                watch['changes'].append(change)
                watch['current_value'] = current_value
                
                self.log_debug_info(f"Variable '{watch['variable']}' changed", change)
    
    def get_debug_summary(self):
        """Get summary of debug information"""
        return {
            'total_logs': len(self.debug_logs),
            'breakpoints': self.breakpoints,
            'watch_variables': self.watch_variables,
            'recent_logs': self.debug_logs[-10:]  # Last 10 logs
        }

# Debug helper API endpoints
@frappe.whitelist()
def log_debug_message(message, data=None, context=None):
    """Log debug message"""
    helper = DebugHelper()
    helper.log_debug_info(message, data, context)
    return True

@frappe.whitelist()
def get_debug_summary():
    """Get debug summary"""
    helper = DebugHelper()
    return helper.get_debug_summary()

@frappe.whitelist()
def set_breakpoint(name, condition=None):
    """Set a breakpoint"""
    helper = DebugHelper()
    helper.set_breakpoint(name, condition)
    return True

@frappe.whitelist()
def watch_variable(name, variable):
    """Watch a variable"""
    helper = DebugHelper()
    helper.watch_variable(name, variable)
    return True
```

---

## 🎯 **Development Tools Best Practices Summary**

### **Tool Selection Guidelines**
- **Choose tools based on specific needs** - don't overcomplicate the workflow
- **Integrate tools into existing workflows** for better adoption
- **Automate repetitive tasks** to improve productivity
- **Monitor tool performance** to ensure they don't become bottlenecks

### **Permission Debugging**
- **Use Permission Inspector** for complex permission issues
- **Document permission rules** for future reference
- **Test permissions with different user roles** regularly
- **Maintain permission audit trails** for compliance

### **Performance Monitoring**
- **Monitor during development** to catch issues early
- **Set up production monitoring** before deployment
- **Establish performance baselines** for comparison
- **Monitor database queries** for optimization opportunities

### **Code Generation**
- **Use templates for consistency** across similar code
- **Customize generated code** to fit specific needs
- **Review generated code** before committing
- **Maintain template library** for common patterns

### **Testing and Debugging**
- **Write tests alongside code** development
- **Use debugging tools** to understand complex issues
- **Automate test execution** in CI/CD pipelines
- **Monitor test coverage** for quality assurance

---

**💡 Pro Tip**: Development tools should enhance productivity without adding complexity. Start with essential tools and gradually add more sophisticated ones as needed. Always measure the impact of tools on development velocity and code quality.
