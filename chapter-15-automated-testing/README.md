# Chapter 15: Automated Testing in Frappe - Quality Assurance

## 🎯 Learning Objectives

By the end of this chapter, you will master:
- **Understanding Frappe's** v16 testing framework and architecture
- **Writing effective** unit tests for DocType controllers with type hints
- **Testing server-side** methods and whitelisted APIs with v16 security
- **Managing fixtures** and test data effectively for v16
- **Building integration** tests for complex workflows
- **Setting up CI/CD** pipelines for automated testing with v16 compatibility
- **Performance testing** with v16 bulk operations and optimization
- **E2E testing** with modern browser automation tools
- **Advanced testing patterns** and best practices
- **Test coverage analysis** and quality metrics

## 📚 Chapter Topics

### 15.1 Testing Fundamentals and Architecture

## Introduction to Frappe Testing

Frappe uses Python's built-in `unittest` framework for unit testing, enhanced with Frappe-specific utilities and infrastructure. The framework provides a robust testing environment that integrates seamlessly with Frappe's database, caching, and permission systems.

### Key Features of Frappe Testing

- **Automatic Database Rollback**: All database changes are automatically rolled back after each test
- **Test Record Management**: Automatic creation and management of test data
- **Permission Testing**: Built-in utilities for testing user permissions
- **Transaction Management**: Proper handling of database transactions
- **Cache Management**: Automatic cache clearing between tests
- **Parallel Execution**: Support for running tests in parallel
- **Version Compatibility**: Works across v14, v15, and v16 with appropriate adaptations

### Prerequisites

Before writing tests, ensure:

1. **Tests are enabled** for your site:
   ```bash
   bench --site [site-name] set-config allow_tests true
   ```

2. **Development dependencies** are installed:
   ```bash
   bench setup requirements --dev
   ```

3. **Test site** is properly configured (usually `test_site` or your development site)

### Test Structure and Organization

**Standard Test Directory Structure:**
```
my_app/
├── my_app/
│   ├── doctype/
│   │   └── my_doctype/
│   │       ├── __init__.py
│   │       ├── my_doctype.py
│   │       └── test_my_doctype.py  # Test file for this DocType
│   ├── api/
│   │   ├── __init__.py
│   │   ├── my_api.py
│   │   └── test_my_api.py  # Test file for API methods
│   └── utils/
│       ├── __init__.py
│       ├── my_utils.py
│       └── test_my_utils.py  # Test file for utilities
└── tests/
    ├── __init__.py
    ├── test_integration.py  # Integration tests
    ├── test_performance.py  # Performance tests
    └── fixtures/  # Test data fixtures
        ├── users.json
        ├── customers.json
        └── items.json
```

### Base Test Classes

Frappe provides several base test classes to inherit from:

```python
# Basic test class with database support
from frappe.tests.utils import FrappeTestCase

class MyTestCase(FrappeTestCase):
    def setUp(self):
        """Set up test data before each test"""
        super().setUp()
        # Create test data here
        
    def tearDown(self):
        """Clean up after each test"""
        super().tearDown()
        # Additional cleanup if needed

# Integration test class with multiple apps
from frappe.tests.utils import IntegrationTestCase

class MyIntegrationTest(IntegrationTestCase):
    apps = ['my_app', 'erpnext']  # Apps to install for tests

# Performance test class
from frappe.tests.utils import PerformanceTestCase

class MyPerformanceTest(PerformanceTestCase):
    def test_bulk_operations(self):
        """Test performance of bulk operations"""
        self.assertQueryPerformance(
            lambda: self.bulk_create_records(1000),
            max_time=2.0  # Max 2 seconds
        )
```

### Writing Your First Test

**Basic Unit Test Example:**
```python
# test_my_doctype.py
import frappe
from frappe.tests.utils import FrappeTestCase

class TestMyDocType(FrappeTestCase):
    def setUp(self):
        """Set up test data"""
        # Create test customer
        self.customer = frappe.get_doc({
            "doctype": "Customer",
            "customer_name": "Test Customer",
            "customer_group": "Individual",
            "territory": "All Territories"
        })
        self.customer.insert()
        
    def tearDown(self):
        """Clean up test data"""
        frappe.db.rollback()
        
    def test_customer_creation(self):
        """Test customer creation"""
        # Verify customer was created
        self.assertTrue(frappe.db.exists("Customer", self.customer.name))
        
        # Test customer fields
        customer = frappe.get_doc("Customer", self.customer.name)
        self.assertEqual(customer.customer_name, "Test Customer")
        self.assertEqual(customer.customer_group, "Individual")
        
    def test_customer_validation(self):
        """Test customer validation rules"""
        # Test required field validation
        customer = frappe.new_doc("Customer")
        # Don't set required fields
        self.assertRaises(frappe.ValidationError, customer.insert)
        
    def test_customer_permissions(self):
        """Test customer permissions"""
        # Test with different user roles
        with self.set_user("System Manager"):
            # Should have access
            customer = frappe.get_doc("Customer", self.customer.name)
            self.assertIsNotNone(customer)
            
        with self.set_user("Guest"):
            # Should not have access
            self.assertRaises(frappe.PermissionError, 
                            frappe.get_doc, "Customer", self.customer.name)
```

### Test Discovery and Execution

**Running Tests:**
```bash
# Run all tests for an app
bench --site test_site run-tests --app my_app

# Run specific test file
bench --site test_site run-tests --app my_app --module test_my_doctype

# Run specific test class
bench --site test_site run-tests --app my_app --class TestMyDocType

# Run specific test method
bench --site test_site run-tests --app my_app --test test_customer_creation

# Run tests with verbose output
bench --site test_site run-tests --app my_app --verbose

# Run tests with coverage
bench --site test_site run-tests --app my_app --coverage

# Run tests in parallel
bench --site test_site run-tests --app my_app --parallel
```

### 15.2 Advanced Testing Patterns

## Mocking and Patching

**Using Python's unittest.mock:**
```python
from unittest.mock import patch, MagicMock
import frappe
from frappe.tests.utils import FrappeTestCase

class TestMyAPI(FrappeTestCase):
    @patch('my_app.api.external_service_call')
    def test_external_api_integration(self, mock_external):
        """Test integration with external API"""
        # Mock external service
        mock_external.return_value = {"status": "success", "data": {"id": 123}}
        
        # Call your API method
        result = frappe.call({
            'method': 'my_app.api.process_external_data',
            'args': {'input': 'test'}
        })
        
        # Verify result
        self.assertEqual(result.status, "success")
        self.assertEqual(result.data.id, 123)
        
        # Verify external service was called
        mock_external.assert_called_once_with('test')
    
    @patch('frappe.db.sql')
    def test_database_query_optimization(self, mock_sql):
        """Test database query with mock"""
        # Mock database response
        mock_sql.return_value = [("Customer1", 1000), ("Customer2", 2000)]
        
        # Test your method
        customers = frappe.get_all("Customer", 
            fields=["customer_name", "credit_limit"])
        
        # Verify query was called
        mock_sql.assert_called_once()
        self.assertEqual(len(customers), 2)
```

## Fixtures and Test Data Management

**Creating Test Fixtures:**
```python
# tests/fixtures/customers.json
[
    {
        "doctype": "Customer",
        "customer_name": "Test Customer 1",
        "customer_group": "Individual",
        "territory": "All Territories",
        "credit_limit": 10000
    },
    {
        "doctype": "Customer", 
        "customer_name": "Test Customer 2",
        "customer_group": "Company",
        "territory": "All Territories",
        "credit_limit": 50000
    }
]
```

**Using Fixtures in Tests:**
```python
from frappe.tests.utils import FrappeTestCase
from frappe.tests.utils import make_test_records

class TestCustomerReports(FrappeTestCase):
    def setUp(self):
        """Set up test data using fixtures"""
        super().setUp()
        
        # Load test fixtures
        self.customers = make_test_records("Customer", "tests/fixtures/customers.json")
        
    def test_customer_credit_report(self):
        """Test customer credit report"""
        # Test report with fixture data
        report_data = frappe.call({
            'method': 'my_app.api.get_customer_credit_report'
        })
        
        # Verify report includes fixture data
        customer_names = [row.customer_name for row in report_data]
        self.assertIn("Test Customer 1", customer_names)
        self.assertIn("Test Customer 2", customer_names)
```

**Dynamic Fixture Creation:**
```python
def create_test_customer(name, credit_limit=10000):
    """Create a test customer with given parameters"""
    return frappe.get_doc({
        "doctype": "Customer",
        "customer_name": name,
        "customer_group": "Individual",
        "territory": "All Territories",
        "credit_limit": credit_limit
    }).insert()

class TestBulkOperations(FrappeTestCase):
    def test_bulk_customer_creation(self):
        """Test bulk customer creation"""
        customers = []
        
        # Create multiple test customers
        for i in range(100):
            customer = create_test_customer(f"Test Customer {i}", i * 100)
            customers.append(customer)
        
        # Verify all customers were created
        self.assertEqual(len(customers), 100)
        
        # Test bulk query performance
        import time
        start_time = time.time()
        
        customer_names = frappe.db.sql("""
            SELECT customer_name FROM `tabCustomer` 
            WHERE customer_name LIKE 'Test Customer %'
        """)
        
        elapsed_time = time.time() - start_time
        self.assertLess(elapsed_time, 1.0)  # Should complete in < 1 second
        self.assertEqual(len(customer_names), 100)
```

## Integration Testing

**Multi-Document Workflow Testing:**
```python
class TestSalesWorkflow(FrappeTestCase):
    def setUp(self):
        """Set up complete workflow test data"""
        super().setUp()
        
        # Create customer
        self.customer = frappe.get_doc({
            "doctype": "Customer",
            "customer_name": "Test Customer",
            "customer_group": "Individual"
        }).insert()
        
        # Create item
        self.item = frappe.get_doc({
            "doctype": "Item",
            "item_code": "TEST-ITEM",
            "item_name": "Test Item",
            "item_group": "Products",
            "stock_uom": "Nos"
        }).insert()
        
    def test_complete_sales_workflow(self):
        """Test complete sales order to delivery workflow"""
        # Create Sales Order
        so = frappe.get_doc({
            "doctype": "Sales Order",
            "customer": self.customer.name,
            "order_type": "Sales",
            "company": "_Test Company",
            "items": [
                {
                    "item_code": self.item.item_code,
                    "qty": 10,
                    "rate": 100
                }
            ]
        })
        so.insert()
        so.submit()
        
        # Verify Sales Order status
        self.assertEqual(so.status, "To Deliver")
        self.assertEqual(so.docstatus, 1)
        
        # Create Delivery Note from Sales Order
        dn = frappe.new_doc("Delivery Note")
        dn.customer = self.customer.name
        dn.company = "_Test Company"
        
        # Add items from Sales Order
        for so_item in so.items:
            dn.append("items", {
                "item_code": so_item.item_code,
                "qty": so_item.qty,
                "against_sales_order": so.name,
                "so_detail": so_item.name
            })
        
        dn.insert()
        dn.submit()
        
        # Verify Delivery Note
        self.assertEqual(dn.status, "Completed")
        self.assertEqual(dn.docstatus, 1)
        
        # Verify Sales Order updated
        so.reload()
        self.assertEqual(so.status, "Completed")
        self.assertEqual(so.per_delivered, 100)
```

## API Testing

**Testing Whitelisted APIs:**
```python
class TestMyAPI(FrappeTestCase):
    def setUp(self):
        """Set up API test user"""
        super().setUp()
        
        # Create test user with appropriate roles
        self.test_user = frappe.get_doc({
            "doctype": "User",
            "email": "test@example.com",
            "first_name": "Test",
            "roles": [{"role": "System Manager"}]
        })
        self.test_user.insert()
        
    def test_api_authentication(self):
        """Test API authentication"""
        # Test without authentication
        with self.set_user("Guest"):
            result = frappe.call({
                'method': 'my_app.api.get_customer_data',
                'args': {'customer': 'TEST-CUST'}
            })
            self.assertEqual(result.status, "error")
            self.assertIn("permission", result.message.lower())
        
        # Test with authentication
        with self.set_user("test@example.com"):
            result = frappe.call({
                'method': 'my_app.api.get_customer_data',
                'args': {'customer': 'TEST-CUST'}
            })
            self.assertEqual(result.status, "success")
    
    def test_api_validation(self):
        """Test API input validation"""
        with self.set_user("test@example.com"):
            # Test missing required parameter
            result = frappe.call({
                'method': 'my_app.api.get_customer_data'
                # Missing customer parameter
            })
            self.assertEqual(result.status, "error")
            self.assertIn("required", result.message.lower())
            
            # Test invalid customer
            result = frappe.call({
                'method': 'my_app.api.get_customer_data',
                'args': {'customer': 'INVALID-CUST'}
            })
            self.assertEqual(result.status, "error")
            self.assertIn("not found", result.message.lower())
    
    def test_api_rate_limiting(self):
        """Test API rate limiting"""
        with self.set_user("test@example.com"):
            # Make multiple rapid calls
            for i in range(10):
                result = frappe.call({
                    'method': 'my_app.api.get_customer_data',
                    'args': {'customer': 'TEST-CUST'}
                })
                
                # Should succeed for first few calls
                if i < 5:
                    self.assertEqual(result.status, "success")
                # After rate limit, should fail
                else:
                    self.assertEqual(result.status, "error")
                    self.assertIn("rate limit", result.message.lower())
                    break
```

## Performance Testing

**Database Performance Testing:**
```python
import time
from frappe.tests.utils import PerformanceTestCase

class TestDatabasePerformance(PerformanceTestCase):
    def test_query_performance(self):
        """Test database query performance"""
        # Create test data
        customers = []
        for i in range(1000):
            customer = frappe.get_doc({
                "doctype": "Customer",
                "customer_name": f"Customer {i}",
                "customer_group": "Individual"
            })
            customers.append(customer)
        
        # Bulk insert
        start_time = time.time()
        for customer in customers:
            customer.insert()
        bulk_insert_time = time.time() - start_time
        
        # Test bulk insert performance
        self.assertLess(bulk_insert_time, 5.0)  # Should complete in < 5 seconds
        
        # Test query performance
        start_time = time.time()
        results = frappe.db.sql("""
            SELECT name, customer_name FROM `tabCustomer` 
            WHERE customer_group = 'Individual'
            ORDER BY creation DESC
            LIMIT 100
        """)
        query_time = time.time() - start_time
        
        # Test query performance
        self.assertLess(query_time, 0.5)  # Should complete in < 0.5 seconds
        self.assertEqual(len(results), 100)
    
    def test_cache_performance(self):
        """Test cache performance"""
        # Test without cache
        start_time = time.time()
        for i in range(100):
            frappe.get_doc("Customer", f"Customer {i}")
        no_cache_time = time.time() - start_time
        
        # Test with cache
        start_time = time.time()
        for i in range(100):
            frappe.get_cached_doc("Customer", f"Customer {i}")
        cache_time = time.time() - start_time
        
        # Cache should be significantly faster
        self.assertLess(cache_time, no_cache_time / 2)
```

## UI Testing with Selenium

**Browser Automation Testing:**
```python
from frappe.tests.utils import FrappeTestCase
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class TestUserInterface(FrappeTestCase):
    @classmethod
    def setUpClass(cls):
        """Set up Selenium driver"""
        super().setUpClass()
        cls.driver = webdriver.Chrome()
        cls.driver.implicitly_wait(10)
        
    @classmethod
    def tearDownClass(cls):
        """Clean up Selenium driver"""
        cls.driver.quit()
        super().tearDownClass()
    
    def test_customer_form_ui(self):
        """Test customer form UI"""
        # Login
        self.driver.get(f"{frappe.utils.get_url()}/login")
        
        # Enter credentials
        self.driver.find_element(By.ID, "login_email").send_keys("Administrator")
        self.driver.find_element(By.ID, "login_password").send_keys("admin")
        self.driver.find_element(By.CSS_SELECTOR, ".btn-login").click()
        
        # Navigate to Customer form
        self.driver.get(f"{frappe.utils.get_url()}/app/customer/new-customer-1")
        
        # Wait for form to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".form-layout"))
        )
        
        # Test form fields
        customer_name_field = self.driver.find_element(By.CSS_SELECTOR, "[data-fieldname='customer_name']")
        self.assertIsNotNone(customer_name_field)
        
        # Fill form
        customer_name_field.send_keys("UI Test Customer")
        
        # Save form
        save_button = self.driver.find_element(By.CSS_SELECTOR, ".btn-primary[data-label='Save']")
        save_button.click()
        
        # Verify success
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".indicator-green"))
        )
        
        # Verify customer was created
        self.driver.get(f"{frappe.utils.get_url()}/app/customer")
        search_box = self.driver.find_element(By.CSS_SELECTOR, ".search-box")
        search_box.send_keys("UI Test Customer")
        
        # Wait for search results
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".list-row"))
        )
        
        # Verify customer in list
        customer_row = self.driver.find_element(By.CSS_SELECTOR, ".list-row")
        self.assertIn("UI Test Customer", customer_row.text)
```

## Test Coverage Analysis

**Generating Coverage Reports:**
```bash
# Run tests with coverage
bench --site test_site run-tests --app my_app --coverage --coverage-module my_app

# Generate HTML coverage report
coverage html -d coverage_html

# View coverage in terminal
coverage report -m
```

**Coverage Configuration:**
```ini
# .coveragerc
[run]
source = my_app
omit = 
    */migrations/*
    */tests/*
    */__pycache__/*
    
[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    
[html]
directory = coverage_html
```

**Target Coverage Goals:**
```python
# tests/test_coverage.py
import unittest
import coverage

class TestCoverageGoals(unittest.TestCase):
    def test_minimum_coverage(self):
        """Ensure minimum test coverage"""
        cov = coverage.Coverage()
        cov.start()
        
        # Import and run your app code
        import my_app
        
        cov.stop()
        
        # Get coverage report
        report = cov.get_report()
        total_coverage = report.coverage
        
        # Assert minimum coverage (e.g., 80%)
        self.assertGreaterEqual(total_coverage, 80.0, 
                              f"Coverage {total_coverage}% is below required 80%")
```

### 15.3 The Frappe v16 Testing Framework

**Understanding Testing Architecture for v16**

```python
# Frappe v16 testing framework components
testing_components = {
    "Test Runner": "frappe.tests.utils.FrappeTestCase with enhanced type hints",
    "Test Database": "Separate test database with prefix 'test_' and v16 optimizations",
    "Fixtures": "JSON-based test data management with v16 bulk operations",
    "Integration Tests": "Multi-document workflow testing with v16 mock services",
    "UI Tests": "Selenium-based interface testing with v16 browser automation",
    "API Tests": "REST endpoint testing with v16 security validation",
    "Performance Tests": "v16 bulk operations and performance benchmarking"
}
}

# v16 Test execution flow
# 1. Setup test environment with v16 optimizations
# 2. Load fixtures using v16 bulk operations
# 3. Run tests with proper type checking
# 4. Clean up test data with v16 transaction management
# 5. Generate reports with v16 performance metrics
# 4. Clean up test data
# 5. Generate reports
```

**Setting Up Test Environment**

```python
# your_app/tests/__init__.py - Test configuration

import frappe
import unittest
from frappe.tests.utils import FrappeTestCase

class BaseTest(FrappeTestCase):
    """Base test class with common setup and teardown"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment for all tests in class"""
        super().setUpClass()
        
        # Enable test mode
        frappe.flags.test_events = 1
        
        # Create test data
        cls.setup_test_data()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests"""
        super().tearDownClass()
        
        # Clean up test data
        cls.cleanup_test_data()
    
    def setUp(self):
        """Set up before each test"""
        super().setUp()
        
        # Reset flags
        frappe.flags.test_events = 1
        frappe.flags.ignore_permissions = 0
        
        # Clear cache
        frappe.clear_cache()
    
    def tearDown(self):
        """Clean up after each test"""
        super().tearDown()
        
        # Rollback any database changes
        frappe.db.rollback()
        
        # Clear cache
        frappe.clear_cache()
    
    @classmethod
    def setup_test_data(cls):
        """Create common test data"""
        pass
    
    @classmethod
    def cleanup_test_data(cls):
        """Clean up common test data"""
        pass

# Test configuration in hooks.py
test_dependencies = ['Frappe']
test_data_fixtures = [
    {"doctype": "User", "name": "test@example.com"},
    {"doctype": "Role", "name": "Test Role"}
]
```

**Test Database Management**

```python
# your_app/tests/test_setup.py - Test environment setup

import frappe
from frappe.tests.utils import FrappeTestCase

class TestEnvironmentSetup(FrappeTestCase):
    """Test environment configuration and validation"""
    
    def test_database_is_test_database(self):
        """Verify we're running in test database"""
        self.assertTrue(frappe.conf.get('db_name', '').startswith('test_'))
    
    def test_test_mode_enabled(self):
        """Verify test mode is properly enabled"""
        self.assertTrue(frappe.flags.test_events)
    
    def test_user_permissions_disabled(self):
        """Verify user permissions are handled correctly in tests"""
        # In tests, we should be able to ignore permissions when needed
        frappe.flags.ignore_permissions = 1
        self.assertTrue(frappe.flags.ignore_permissions)
    
    def test_fixtures_loaded(self):
        """Verify test fixtures are properly loaded"""
        # Check if standard fixtures exist
        self.assertTrue(frappe.db.exists('User', 'Administrator'))
        self.assertTrue(frappe.db.exists('Role', 'System Manager'))
```

### 15.2 Unit Testing DocType Controllers

**Testing Document Lifecycle**

```python
# your_app/tests/test_asset_controller.py - Asset DocType tests

import frappe
from frappe.tests.utils import FrappeTestCase
from your_app.assets.controller import Asset

class TestAssetController(FrappeTestCase):
    """Comprehensive tests for Asset DocType controller"""
    
    def setUp(self):
        """Set up test data for each test"""
        super().setUp()
        
        # Create test asset category
        self.asset_category = frappe.get_doc({
            "doctype": "Asset Category",
            "category_name": "Test Category",
            "accounting_required": 0
        })
        self.asset_category.insert()
        
        # Create test company
        self.company = frappe.get_doc({
            "doctype": "Company",
            "company_name": "Test Company",
            "default_currency": "USD"
        })
        self.company.insert()
        
        # Create test asset
        self.asset = frappe.get_doc({
            "doctype": "Asset",
            "asset_name": "Test Asset",
            "asset_category": self.asset_category.name,
            "company": self.company.name,
            "purchase_date": "2024-01-01",
            "purchase_cost": 1000.00,
            "current_status": "Available"
        })
    
    def test_asset_creation(self):
        """Test basic asset creation"""
        asset = self.asset
        asset.insert()
        
        # Verify asset was created
        self.assertTrue(frappe.db.exists('Asset', asset.name))
        
        # Verify field values
        saved_asset = frappe.get_doc('Asset', asset.name)
        self.assertEqual(saved_asset.asset_name, 'Test Asset')
        self.assertEqual(saved_asset.purchase_cost, 1000.00)
        self.assertEqual(saved_asset.current_status, 'Available')
    
    def test_asset_validation(self):
        """Test asset validation rules"""
        asset = self.asset
        
        # Test required fields
        asset.asset_name = ""
        self.assertRaises(frappe.MandatoryError, asset.insert)
        
        asset.asset_name = "Test Asset"
        asset.asset_category = ""
        self.assertRaises(frappe.MandatoryError, asset.insert)
        
        # Test purchase cost validation
        asset.asset_category = self.asset_category.name
        asset.purchase_cost = -100
        self.assertRaises(frappe.ValidationError, asset.insert)
    
    def test_asset_naming_series(self):
        """Test automatic asset code generation"""
        asset = self.asset
        asset.insert()
        
        # Verify asset code was generated
        self.assertTrue(asset.asset_code)
        self.assertTrue(asset.asset_code.startswith('AST-'))
        
        # Verify uniqueness
        asset2 = frappe.get_doc({
            "doctype": "Asset",
            "asset_name": "Test Asset 2",
            "asset_category": self.asset_category.name,
            "company": self.company.name,
            "purchase_date": "2024-01-01",
            "purchase_cost": 1500.00
        })
        asset2.insert()
        
        self.assertNotEqual(asset.asset_code, asset2.asset_code)
    
    def test_asset_status_change(self):
        """Test asset status workflow"""
        asset = self.asset
        asset.insert()
        
        # Test status change to "In Use"
        asset.current_status = "In Use"
        asset.save()
        
        saved_asset = frappe.get_doc('Asset', asset.name)
        self.assertEqual(saved_asset.current_status, 'In Use')
        
        # Test status change validation
        asset.current_status = "Invalid Status"
        self.assertRaises(frappe.ValidationError, asset.save)
    
    def test_asset_deletion(self):
        """Test asset deletion rules"""
        asset = self.asset
        asset.insert()
        
        # Test deletion of unused asset
        asset.delete()
        self.assertFalse(frappe.db.exists('Asset', asset.name))
        
        # Test deletion prevention when asset is assigned
        asset.insert()
        
        # Create asset assignment
        assignment = frappe.get_doc({
            "doctype": "Asset Assignment",
            "asset": asset.name,
            "assigned_to": "test@example.com",
            "assignment_date": "2024-01-01"
        })
        assignment.insert()
        assignment.submit()
        
        # Should not be able to delete assigned asset
        self.assertRaises(frappe.CannotDeleteError, asset.delete)
    
    def test_asset_calculations(self):
        """Test asset calculation methods"""
        asset = self.asset
        asset.insert()
        
        # Test depreciation calculation
        if hasattr(asset, 'calculate_depreciation'):
            asset.purchase_date = "2023-01-01"
            asset.current_date = "2024-01-01"
            depreciation = asset.calculate_depreciation()
            self.assertIsInstance(depreciation, (int, float))
            self.assertGreaterEqual(depreciation, 0)
        
        # Test asset age calculation
        if hasattr(asset, 'get_asset_age'):
            age = asset.get_asset_age()
            self.assertIsInstance(age, (int, float))
            self.assertGreaterEqual(age, 0)
    
    def test_asset_permissions(self):
        """Test asset permission checks"""
        asset = self.asset
        asset.insert()
        
        # Test with different user roles
        test_user = frappe.get_doc({
            "doctype": "User",
            "email": "test_asset_user@example.com",
            "first_name": "Test",
            "enabled": 1
        })
        test_user.insert()
        
        # Add test role
        test_role = frappe.get_doc({
            "doctype": "Role",
            "role_name": "Asset User"
        })
        test_role.insert()
        
        frappe.add_roles(test_user.name, test_role.name)
        
        # Test permission with test user
        frappe.set_user(test_user.name)
        
        has_read_perm = frappe.has_permission('Asset', 'read', asset.name)
        has_write_perm = frappe.has_permission('Asset', 'write', asset.name)
        
        # Reset to admin
        frappe.set_user('Administrator')
```

**Testing Custom Methods**

```python
# your_app/tests/test_asset_methods.py - Asset method tests

import frappe
from frappe.tests.utils import FrappeTestCase
from your_app.assets.controller import Asset

class TestAssetMethods(FrappeTestCase):
    """Tests for custom Asset methods"""
    
    def setUp(self):
        """Set up test assets"""
        super().setUp()
        
        self.asset = self.create_test_asset()
        self.asset2 = self.create_test_asset("Test Asset 2")
    
    def create_test_asset(self, name="Test Asset"):
        """Helper method to create test asset"""
        return frappe.get_doc({
            "doctype": "Asset",
            "asset_name": name,
            "asset_category": "Test Category",
            "company": "Test Company",
            "purchase_date": "2024-01-01",
            "purchase_cost": 1000.00,
            "current_status": "Available"
        }).insert()
    
    def test_get_available_assets(self):
        """Test get_available_assets method"""
        # Set one asset as available, one as in use
        self.asset.current_status = "Available"
        self.asset.save()
        
        self.asset2.current_status = "In Use"
        self.asset2.save()
        
        # Test the method
        available_assets = Asset.get_available_assets()
        
        self.assertIsInstance(available_assets, list)
        self.assertEqual(len(available_assets), 1)
        self.assertEqual(available_assets[0].name, self.asset.name)
    
    def test_assign_asset(self):
        """Test asset assignment method"""
        employee = self.create_test_employee()
        
        # Test successful assignment
        assignment = Asset.assign_asset(
            asset_name=self.asset.name,
            employee=employee.name,
            assignment_date="2024-01-01"
        )
        
        self.assertIsInstance(assignment, dict)
        self.assertIn('assignment_id', assignment)
        
        # Verify assignment was created
        self.assertTrue(frappe.db.exists('Asset Assignment', assignment['assignment_id']))
        
        # Verify asset status changed
        updated_asset = frappe.get_doc('Asset', self.asset.name)
        self.assertEqual(updated_asset.current_status, 'In Use')
    
    def test_assign_already_assigned_asset(self):
        """Test assignment of already assigned asset"""
        employee = self.create_test_employee()
        
        # First assignment
        Asset.assign_asset(
            asset_name=self.asset.name,
            employee=employee.name,
            assignment_date="2024-01-01"
        )
        
        # Try second assignment - should fail
        with self.assertRaises(frappe.ValidationError) as context:
            Asset.assign_asset(
                asset_name=self.asset.name,
                employee="another@example.com",
                assignment_date="2024-01-02"
            )
        
        self.assertIn('already assigned', str(context.exception))
    
    def test_release_asset(self):
        """Test asset release method"""
        employee = self.create_test_employee()
        
        # Assign asset first
        assignment = Asset.assign_asset(
            asset_name=self.asset.name,
            employee=employee.name,
            assignment_date="2024-01-01"
        )
        
        # Release asset
        result = Asset.release_asset(
            asset_name=self.asset.name,
            release_date="2024-01-15"
        )
        
        self.assertTrue(result['success'])
        
        # Verify asset status changed
        updated_asset = frappe.get_doc('Asset', self.asset.name)
        self.assertEqual(updated_asset.current_status, 'Available')
        
        # Verify assignment was closed
        assignment_doc = frappe.get_doc('Asset Assignment', assignment['assignment_id'])
        self.assertEqual(assignment_doc.status, 'Closed')
    
    def test_get_asset_history(self):
        """Test asset history method"""
        employee = self.create_test_employee()
        
        # Create some history
        self.asset.current_status = "In Use"
        self.asset.save()
        
        Asset.assign_asset(
            asset_name=self.asset.name,
            employee=employee.name,
            assignment_date="2024-01-01"
        )
        
        Asset.release_asset(
            asset_name=self.asset.name,
            release_date="2024-01-15"
        )
        
        # Get history
        history = Asset.get_asset_history(self.asset.name)
        
        self.assertIsInstance(history, list)
        self.assertGreater(len(history), 0)
        
        # Verify history structure
        for entry in history:
            self.assertIn('date', entry)
            self.assertIn('action', entry)
            self.assertIn('status', entry)
    
    def test_calculate_utilization(self):
        """Test asset utilization calculation"""
        employee = self.create_test_employee()
        
        # Assign asset for specific period
        Asset.assign_asset(
            asset_name=self.asset.name,
            employee=employee.name,
            assignment_date="2024-01-01"
        )
        
        Asset.release_asset(
            asset_name=self.asset.name,
            release_date="2024-01-15"
        )
        
        # Calculate utilization for January 2024
        utilization = Asset.calculate_utilization(
            asset_name=self.asset.name,
            start_date="2024-01-01",
            end_date="2024-01-31"
        )
        
        self.assertIsInstance(utilization, dict)
        self.assertIn('percentage', utilization)
        self.assertIn('days_used', utilization)
        self.assertIn('total_days', utilization)
        
        # Should be 15 days out of 31
        self.assertEqual(utilization['days_used'], 15)
        self.assertEqual(utilization['total_days'], 31)
        self.assertAlmostEqual(utilization['percentage'], 48.39, places=1)
    
    def create_test_employee(self):
        """Helper method to create test employee"""
        # Create user first
        user = frappe.get_doc({
            "doctype": "User",
            "email": "test_employee@example.com",
            "first_name": "Test",
            "last_name": "Employee",
            "enabled": 1
        })
        user.insert()
        
        # Create employee
        employee = frappe.get_doc({
            "doctype": "Employee",
            "employee_name": "Test Employee",
            "company": "Test Company",
            "user_id": user.email,
            "status": "Active"
        })
        employee.insert()
        
        return employee
```

### 15.3 Testing Server-Side Methods and APIs

**Testing Whitelisted Methods**

```python
# your_app/tests/test_api_methods.py - API method tests

import frappe
from frappe.tests.utils import FrappeTestCase
from your_app.api import get_asset_details, assign_asset_via_api

class TestAPIMethods(FrappeTestCase):
    """Tests for whitelisted API methods"""
    
    def setUp(self):
        """Set up test data"""
        super().setUp()
        
        self.asset = self.create_test_asset()
        self.employee = self.create_test_employee()
        
        # Create API user
        self.api_user = frappe.get_doc({
            "doctype": "User",
            "email": "api_user@example.com",
            "first_name": "API",
            "last_name": "User",
            "enabled": 1
        })
        self.api_user.insert()
        
        # Add API role
        frappe.add_roles(self.api_user.name, "System Manager")
    
    def create_test_asset(self):
        """Create test asset"""
        return frappe.get_doc({
            "doctype": "Asset",
            "asset_name": "API Test Asset",
            "asset_category": "Test Category",
            "company": "Test Company",
            "purchase_date": "2024-01-01",
            "purchase_cost": 1000.00,
            "current_status": "Available"
        }).insert()
    
    def create_test_employee(self):
        """Create test employee"""
        user = frappe.get_doc({
            "doctype": "User",
            "email": "api_employee@example.com",
            "first_name": "API",
            "last_name": "Employee",
            "enabled": 1
        })
        user.insert()
        
        employee = frappe.get_doc({
            "doctype": "Employee",
            "employee_name": "API Employee",
            "company": "Test Company",
            "user_id": user.email,
            "status": "Active"
        })
        employee.insert()
        
        return employee
    
    def test_get_asset_details_success(self):
        """Test successful asset details retrieval"""
        # Switch to API user
        frappe.set_user(self.api_user.name)
        
        try:
            result = get_asset_details(asset_name=self.asset.name)
            
            # Verify response structure
            self.assertIsInstance(result, dict)
            self.assertIn('asset', result)
            self.assertIn('success', result)
            self.assertTrue(result['success'])
            
            # Verify asset details
            asset_data = result['asset']
            self.assertEqual(asset_data['name'], self.asset.name)
            self.assertEqual(asset_data['asset_name'], 'API Test Asset')
            self.assertEqual(asset_data['current_status'], 'Available')
            
        finally:
            frappe.set_user('Administrator')
    
    def test_get_asset_details_not_found(self):
        """Test asset details retrieval for non-existent asset"""
        frappe.set_user(self.api_user.name)
        
        try:
            with self.assertRaises(frappe.DoesNotExistError) as context:
                get_asset_details(asset_name="NON-EXISTENT-ASSET")
            
            self.assertIn('Asset', str(context.exception))
            
        finally:
            frappe.set_user('Administrator')
    
    def test_get_asset_details_permission_denied(self):
        """Test asset details retrieval without permission"""
        # Create user without permissions
        limited_user = frappe.get_doc({
            "doctype": "User",
            "email": "limited_user@example.com",
            "first_name": "Limited",
            "last_name": "User",
            "enabled": 1
        })
        limited_user.insert()
        
        frappe.set_user(limited_user.name)
        
        try:
            with self.assertRaises(frappe.PermissionError) as context:
                get_asset_details(asset_name=self.asset.name)
            
            self.assertIn('permission', str(context.exception).lower())
            
        finally:
            frappe.set_user('Administrator')
    
    def test_assign_asset_via_api_success(self):
        """Test successful asset assignment via API"""
        frappe.set_user(self.api_user.name)
        
        try:
            result = assign_asset_via_api(
                asset_name=self.asset.name,
                employee_email=self.employee.user_id,
                assignment_date="2024-01-01",
                notes="API Assignment Test"
            )
            
            # Verify response
            self.assertIsInstance(result, dict)
            self.assertIn('success', result)
            self.assertIn('assignment_id', result)
            self.assertTrue(result['success'])
            
            # Verify assignment was created
            assignment = frappe.get_doc('Asset Assignment', result['assignment_id'])
            self.assertEqual(assignment.asset, self.asset.name)
            self.assertEqual(assignment.assigned_to, self.employee.user_id)
            
            # Verify asset status changed
            updated_asset = frappe.get_doc('Asset', self.asset.name)
            self.assertEqual(updated_asset.current_status, 'In Use')
            
        finally:
            frappe.set_user('Administrator')
    
    def test_assign_asset_via_api_validation(self):
        """Test asset assignment validation via API"""
        frappe.set_user(self.api_user.name)
        
        try:
            # Test missing required fields
            with self.assertRaises(frappe.MandatoryError):
                assign_asset_via_api(asset_name=self.asset.name)
            
            # Test invalid date
            with self.assertRaises(frappe.ValidationError):
                assign_asset_via_api(
                    asset_name=self.asset.name,
                    employee_email=self.employee.user_id,
                    assignment_date="invalid-date"
                )
            
            # Test already assigned asset
            # First assignment
            assign_asset_via_api(
                asset_name=self.asset.name,
                employee_email=self.employee.user_id,
                assignment_date="2024-01-01"
            )
            
            # Second assignment - should fail
            with self.assertRaises(frappe.ValidationError) as context:
                assign_asset_via_api(
                    asset_name=self.asset.name,
                    employee_email="another@example.com",
                    assignment_date="2024-01-02"
                )
            
            self.assertIn('already assigned', str(context.exception))
            
        finally:
            frappe.set_user('Administrator')
    
    def test_api_error_handling(self):
        """Test API error handling"""
        frappe.set_user(self.api_user.name)
        
        try:
            # Test with invalid asset name format
            with self.assertRaises(frappe.ValidationError):
                get_asset_details(asset_name="")
            
            # Test with special characters
            with self.assertRaises(frappe.ValidationError):
                get_asset_details(asset_name="Asset@#$")
            
        finally:
            frappe.set_user('Administrator')
    
    def test_api_response_format(self):
        """Test API response format consistency"""
        frappe.set_user(self.api_user.name)
        
        try:
            # Test successful response format
            result = get_asset_details(asset_name=self.asset.name)
            
            required_fields = ['success', 'asset', 'timestamp']
            for field in required_fields:
                self.assertIn(field, result)
            
            # Test asset data structure
            asset_fields = ['name', 'asset_name', 'current_status', 'purchase_cost']
            for field in asset_fields:
                self.assertIn(field, result['asset'])
            
        finally:
            frappe.set_user('Administrator')
```

**Testing REST API Endpoints**

```python
# your_app/tests/test_rest_api.py - REST API tests

import frappe
import json
from frappe.tests.utils import FrappeTestCase
from frappe.auth import AuthenticationManager

class TestRestAPI(FrappeTestCase):
    """Tests for REST API endpoints"""
    
    def setUp(self):
        """Set up API test environment"""
        super().setUp()
        
        # Create API user with appropriate roles
        self.api_user = self.create_api_user()
        
        # Get API key and secret
        self.api_key, self.api_secret = self.generate_api_keys(self.api_user.name)
        
        # Create test asset
        self.asset = self.create_test_asset()
    
    def create_api_user(self):
        """Create API user with necessary permissions"""
        user = frappe.get_doc({
            "doctype": "User",
            "email": "api_rest_user@example.com",
            "first_name": "API REST",
            "last_name": "User",
            "enabled": 1
        })
        user.insert()
        
        # Add API role
        frappe.add_roles(user.name, "System Manager")
        
        return user
    
    def generate_api_keys(self, user):
        """Generate API keys for user"""
        api_key = frappe.generate_hash(length=15)
        api_secret = frappe.generate_hash(length=15)
        
        # Store API keys (simplified - in real app, use proper API Key doctype)
        frappe.db.set_value('User', user, 'api_key', api_key)
        frappe.db.set_value('User', user, 'api_secret', api_secret)
        
        return api_key, api_secret
    
    def create_test_asset(self):
        """Create test asset for API testing"""
        return frappe.get_doc({
            "doctype": "Asset",
            "asset_name": "REST API Test Asset",
            "asset_category": "Test Category",
            "company": "Test Company",
            "purchase_date": "2024-01-01",
            "purchase_cost": 1000.00,
            "current_status": "Available"
        }).insert()
    
    def get_api_headers(self):
        """Get API authentication headers"""
        import base64
        import hashlib
        import hmac
        
        # Create signature
        timestamp = str(int(frappe.utils.time.time_in_seconds()))
        message = f"{timestamp}\nGET\n/api/v1/asset/{self.asset.name}"
        
        signature = hmac.new(
            self.api_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).digest()
        
        encoded_signature = base64.b64encode(signature).decode()
        
        return {
            'X-API-Key': self.api_key,
            'X-API-Timestamp': timestamp,
            'X-API-Signature': encoded_signature,
            'Content-Type': 'application/json'
        }
    
    def test_get_asset_endpoint_success(self):
        """Test GET /api/v1/asset/{name} endpoint"""
        headers = self.get_api_headers()
        
        # Simulate API request (simplified)
        try:
            # In real test, you'd use requests or test client
            # For this example, we'll call the method directly
            
            from your_app.rest_api import get_asset_endpoint
            
            # Simulate request context
            frappe.local.request = type('Request', (), {
                'headers': headers,
                'method': 'GET'
            })()
            
            result = get_asset_endpoint(asset_name=self.asset.name)
            
            # Verify response
            self.assertIsInstance(result, dict)
            self.assertIn('data', result)
            self.assertIn('status', result)
            self.assertEqual(result['status'], 'success')
            
            asset_data = result['data']
            self.assertEqual(asset_data['name'], self.asset.name)
            self.assertEqual(asset_data['asset_name'], 'REST API Test Asset')
            
        except Exception as e:
            self.fail(f"API endpoint test failed: {str(e)}")
    
    def test_get_asset_endpoint_not_found(self):
        """Test GET endpoint with non-existent asset"""
        headers = self.get_api_headers()
        
        try:
            from your_app.rest_api import get_asset_endpoint
            
            frappe.local.request = type('Request', (), {
                'headers': headers,
                'method': 'GET'
            })()
            
            with self.assertRaises(frappe.DoesNotExistError):
                get_asset_endpoint(asset_name="NON-EXISTENT")
                
        except Exception as e:
            self.fail(f"API endpoint test failed: {str(e)}")
    
    def test_post_asset_assignment_endpoint(self):
        """Test POST /api/v1/asset/assign endpoint"""
        headers = self.get_api_headers()
        
        assignment_data = {
            "asset_name": self.asset.name,
            "employee_email": "test_employee@example.com",
            "assignment_date": "2024-01-01",
            "notes": "API Test Assignment"
        }
        
        try:
            from your_app.rest_api import assign_asset_endpoint
            
            frappe.local.request = type('Request', (), {
                'headers': headers,
                'method': 'POST',
                'get_json': lambda: assignment_data
            })()
            
            result = assign_asset_endpoint()
            
            # Verify response
            self.assertIsInstance(result, dict)
            self.assertIn('data', result)
            self.assertIn('status', result)
            self.assertEqual(result['status'], 'success')
            
            assignment_data = result['data']
            self.assertIn('assignment_id', assignment_data)
            
            # Verify assignment was created
            self.assertTrue(frappe.db.exists('Asset Assignment', assignment_data['assignment_id']))
            
        except Exception as e:
            self.fail(f"API endpoint test failed: {str(e)}")
    
    def test_api_authentication_invalid_key(self):
        """Test API authentication with invalid key"""
        invalid_headers = self.get_api_headers()
        invalid_headers['X-API-Key'] = 'invalid-key'
        
        try:
            from your_app.rest_api import get_asset_endpoint
            
            frappe.local.request = type('Request', (), {
                'headers': invalid_headers,
                'method': 'GET'
            })()
            
            with self.assertRaises(frappe.AuthenticationError):
                get_asset_endpoint(asset_name=self.asset.name)
                
        except Exception as e:
            self.fail(f"API authentication test failed: {str(e)}")
    
    def test_api_rate_limiting(self):
        """Test API rate limiting"""
        headers = self.get_api_headers()
        
        try:
            from your_app.rest_api import get_asset_endpoint
            
            frappe.local.request = type('Request', (), {
                'headers': headers,
                'method': 'GET'
            })()
            
            # Make multiple rapid requests
            for i in range(100):  # Assuming rate limit is less than 100
                try:
                    get_asset_endpoint(asset_name=self.asset.name)
                except frappe.TooManyRequestsError:
                    # Rate limit triggered - test passes
                    return
            
            # If we get here, rate limiting might not be working
            self.fail("Rate limiting not triggered")
            
        except Exception as e:
            self.fail(f"Rate limiting test failed: {str(e)}")
```

### 15.4 Fixture Management

**Creating and Managing Test Fixtures**

```json
// your_app/tests/fixtures/users.json
{
    "User": [
        {
            "doctype": "User",
            "name": "test_asset_manager@example.com",
            "first_name": "Test",
            "last_name": "Asset Manager",
            "email": "test_asset_manager@example.com",
            "enabled": 1,
            "user_type": "System User"
        },
        {
            "doctype": "User",
            "name": "test_employee@example.com",
            "first_name": "Test",
            "last_name": "Employee",
            "email": "test_employee@example.com",
            "enabled": 1,
            "user_type": "System User"
        }
    ],
    "Role": [
        {
            "doctype": "Role",
            "name": "Asset Manager",
            "role_name": "Asset Manager",
            "desk_access": 1,
            "is_standard": 1
        },
        {
            "doctype": "Role",
            "name": "Asset User",
            "role_name": "Asset User",
            "desk_access": 1,
            "is_standard": 1
        }
    ],
    "Has Role": [
        {
            "doctype": "Has Role",
            "parent": "test_asset_manager@example.com",
            "parenttype": "User",
            "parentfield": "roles",
            "role": "Asset Manager"
        },
        {
            "doctype": "Has Role",
            "parent": "test_employee@example.com",
            "parenttype": "User",
            "parentfield": "roles",
            "role": "Asset User"
        }
    ]
}
```

```json
// your_app/tests/fixtures/assets.json
{
    "Company": [
        {
            "doctype": "Company",
            "name": "Test Company",
            "company_name": "Test Company",
            "default_currency": "USD",
            "country": "United States"
        }
    ],
    "Asset Category": [
        {
            "doctype": "Asset Category",
            "name": "Test Category",
            "category_name": "Test Category",
            "accounting_required": 0
        },
        {
            "doctype": "Asset Category",
            "name": "IT Equipment",
            "category_name": "IT Equipment",
            "accounting_required": 1
        }
    ],
    "Asset": [
        {
            "doctype": "Asset",
            "name": "TEST-LAPTOP-001",
            "asset_name": "Test Laptop",
            "asset_category": "IT Equipment",
            "company": "Test Company",
            "purchase_date": "2024-01-01",
            "purchase_cost": 1200.00,
            "current_status": "Available",
            "specifications": "Dell XPS 15, 16GB RAM, 512GB SSD"
        },
        {
            "doctype": "Asset",
            "name": "TEST-MONITOR-001",
            "asset_name": "Test Monitor",
            "asset_category": "Test Category",
            "company": "Test Company",
            "purchase_date": "2024-01-15",
            "purchase_cost": 300.00,
            "current_status": "Available",
            "specifications": "Dell 24\" UltraSharp"
        }
    ]
}
```

**Fixture Management Utilities**

```python
# your_app/tests/fixtures.py - Fixture management utilities

import frappe
import json
import os
from frappe.tests.utils import FrappeTestCase

class FixtureManager:
    """Utility class for managing test fixtures"""
    
    FIXTURE_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')
    
    @classmethod
    def load_fixture(cls, fixture_name):
        """Load a specific fixture file"""
        fixture_path = os.path.join(cls.FIXTURE_DIR, f"{fixture_name}.json")
        
        if not os.path.exists(fixture_path):
            raise FileNotFoundError(f"Fixture file not found: {fixture_path}")
        
        with open(fixture_path, 'r') as f:
            fixture_data = json.load(f)
        
        # Insert fixture data
        for doctype, documents in fixture_data.items():
            for doc_data in documents:
                try:
                    # Check if document already exists
                    if frappe.db.exists(doctype, doc_data.get('name')):
                        continue
                    
                    # Create document
                    doc = frappe.get_doc(doc_data)
                    doc.insert(ignore_permissions=True)
                    frappe.db.commit()
                    
                except Exception as e:
                    frappe.logger().error(f"Failed to load fixture {doctype} {doc_data.get('name')}: {str(e)}")
    
    @classmethod
    def load_all_fixtures(cls):
        """Load all fixture files"""
        fixture_files = [f for f in os.listdir(cls.FIXTURE_DIR) if f.endswith('.json')]
        
        for fixture_file in fixture_files:
            fixture_name = fixture_file.replace('.json', '')
            cls.load_fixture(fixture_name)
    
    @classmethod
    def cleanup_fixture(cls, fixture_name):
        """Clean up a specific fixture"""
        fixture_path = os.path.join(cls.FIXTURE_DIR, f"{fixture_name}.json")
        
        if not os.path.exists(fixture_path):
            return
        
        with open(fixture_path, 'r') as f:
            fixture_data = json.load(f)
        
        # Delete fixture data in reverse order (to handle dependencies)
        for doctype in reversed(list(fixture_data.keys())):
            documents = fixture_data[doctype]
            for doc_data in documents:
                try:
                    if frappe.db.exists(doctype, doc_data.get('name')):
                        frappe.delete_doc(doctype, doc_data.get('name'), ignore_permissions=True)
                        frappe.db.commit()
                except Exception as e:
                    frappe.logger().error(f"Failed to cleanup fixture {doctype} {doc_data.get('name')}: {str(e)}")
    
    @classmethod
    def cleanup_all_fixtures(cls):
        """Clean up all fixture data"""
        fixture_files = [f for f in os.listdir(cls.FIXTURE_DIR) if f.endswith('.json')]
        
        for fixture_file in fixture_files:
            fixture_name = fixture_file.replace('.json', '')
            cls.cleanup_fixture(fixture_name)

class FixtureTestCase(FrappeTestCase):
    """Base test case with fixture management"""
    
    fixtures = ['users', 'assets']
    
    @classmethod
    def setUpClass(cls):
        """Set up test class with fixtures"""
        super().setUpClass()
        
        # Load fixtures
        for fixture_name in cls.fixtures:
            FixtureManager.load_fixture(fixture_name)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up fixtures"""
        super().tearDownClass()
        
        # Clean up fixtures in reverse order
        for fixture_name in reversed(cls.fixtures):
            FixtureManager.cleanup_fixture(fixture_name)
    
    def get_fixture_user(self, email):
        """Get user from fixtures"""
        return frappe.get_doc('User', email)
    
    def get_fixture_asset(self, asset_name):
        """Get asset from fixtures"""
        return frappe.get_doc('Asset', asset_name)
```

### 15.5 Integration Testing

**Testing Complex Workflows**

```python
# your_app/tests/test_integration.py - Integration tests

import frappe
from frappe.tests.utils import FrappeTestCase
from your_app.tests.fixtures import FixtureTestCase

class TestAssetWorkflowIntegration(FixtureTestCase):
    """Integration tests for complete asset workflows"""
    
    fixtures = ['users', 'assets']
    
    def setUp(self):
        """Set up integration test environment"""
        super().setUp()
        
        # Get fixture data
        self.asset_manager = self.get_fixture_user('test_asset_manager@example.com')
        self.employee = self.get_fixture_user('test_employee@example.com')
        self.laptop = self.get_fixture_asset('TEST-LAPTOP-001')
        self.monitor = self.get_fixture_asset('TEST-MONITOR-001')
    
    def test_complete_asset_lifecycle(self):
        """Test complete asset lifecycle from creation to disposal"""
        
        # Step 1: Asset creation (already done in fixtures)
        self.assertEqual(self.laptop.current_status, 'Available')
        
        # Step 2: Asset assignment
        assignment = self.assign_asset_to_employee(self.laptop, self.employee)
        self.assertEqual(assignment.docstatus, 1)  # Submitted
        self.assertEqual(assignment.assigned_to, self.employee.name)
        
        # Step 3: Verify asset status changed
        updated_laptop = frappe.get_doc('Asset', self.laptop.name)
        self.assertEqual(updated_laptop.current_status, 'In Use')
        
        # Step 4: Asset maintenance
        maintenance = self.create_maintenance_record(self.laptop)
        self.assertEqual(maintenance.status, 'Open')
        
        # Step 5: Complete maintenance
        maintenance.status = 'Completed'
        maintenance.completion_date = frappe.utils.today()
        maintenance.save()
        maintenance.submit()
        
        # Step 6: Asset return
        return_record = self.return_asset_from_employee(self.laptop, self.employee)
        self.assertEqual(return_record.docstatus, 1)
        
        # Step 7: Verify asset status
        final_laptop = frappe.get_doc('Asset', self.laptop.name)
        self.assertEqual(final_laptop.current_status, 'Available')
        
        # Step 8: Asset disposal
        disposal = self.dispose_asset(self.laptop)
        self.assertEqual(disposal.docstatus, 1)
        
        # Step 9: Verify final status
        disposed_laptop = frappe.get_doc('Asset', self.laptop.name)
        self.assertEqual(disposed_laptop.current_status, 'Disposed')
    
    def test_asset_transfer_workflow(self):
        """Test asset transfer between employees"""
        
        # Assign to first employee
        assignment1 = self.assign_asset_to_employee(self.monitor, self.employee)
        self.assertEqual(assignment1.assigned_to, self.employee.name)
        
        # Create second employee
        employee2 = self.create_test_employee('employee2@example.com')
        
        # Transfer asset
        transfer = self.transfer_asset(self.monitor, self.employee, employee2)
        self.assertEqual(transfer.docstatus, 1)
        self.assertEqual(transfer.transfer_to, employee2.name)
        
        # Verify first assignment is closed
        closed_assignment = frappe.get_doc('Asset Assignment', assignment1.name)
        self.assertEqual(closed_assignment.status, 'Closed')
        
        # Verify new assignment exists
        new_assignment = frappe.get_doc('Asset Assignment', transfer.new_assignment)
        self.assertEqual(new_assignment.assigned_to, employee2.name)
    
    def test_asset_audit_workflow(self):
        """Test asset audit and reconciliation"""
        
        # Create audit schedule
        audit = self.create_asset_audit([self.laptop.name, self.monitor.name])
        self.assertEqual(audit.status, 'Scheduled')
        
        # Start audit
        audit.status = 'In Progress'
        audit.save()
        
        # Perform audit for laptop (found)
        audit_entry = self.create_audit_entry(audit.name, self.laptop.name, 'Found', 'In Good Condition')
        self.assertEqual(audit_entry.status, 'Found')
        
        # Perform audit for monitor (missing)
        missing_entry = self.create_audit_entry(audit.name, self.monitor.name, 'Missing', 'Not Found')
        self.assertEqual(missing_entry.status, 'Missing')
        
        # Complete audit
        audit.status = 'Completed'
        audit.completion_date = frappe.utils.today()
        audit.save()
        audit.submit()
        
        # Verify audit results
        audit_report = self.generate_audit_report(audit.name)
        self.assertEqual(audit_report['total_assets'], 2)
        self.assertEqual(audit_report['found_assets'], 1)
        self.assertEqual(audit_report['missing_assets'], 1)
    
    def test_multi_asset_assignment(self):
        """Test assigning multiple assets to employee"""
        
        # Assign laptop and monitor to employee
        assignment1 = self.assign_asset_to_employee(self.laptop, self.employee)
        assignment2 = self.assign_asset_to_employee(self.monitor, self.employee)
        
        # Get employee's current assignments
        employee_assignments = frappe.get_all('Asset Assignment',
            filters={
                'assigned_to': self.employee.name,
                'status': 'Active'
            },
            fields=['asset', 'asset_name']
        )
        
        self.assertEqual(len(employee_assignments), 2)
        
        asset_names = [a.asset for a in employee_assignments]
        self.assertIn(self.laptop.name, asset_names)
        self.assertIn(self.monitor.name, asset_names)
        
        # Return all assets
        for assignment in [assignment1, assignment2]:
            self.return_asset_from_employee(
                frappe.get_doc('Asset', assignment.asset),
                self.employee
            )
        
        # Verify all assets returned
        final_assignments = frappe.get_all('Asset Assignment',
            filters={
                'assigned_to': self.employee.name,
                'status': 'Active'
            }
        )
        
        self.assertEqual(len(final_assignments), 0)
    
    def test_asset_bulk_operations(self):
        """Test bulk operations on multiple assets"""
        
        # Create additional assets
        assets = [self.laptop, self.monitor]
        
        for i in range(3):
            asset = self.create_test_asset(f'Bulk Test Asset {i+1}')
            assets.append(asset)
        
        # Bulk assign to department
        bulk_assignment = self.bulk_assign_to_department(
            assets, 
            'IT Department'
        )
        self.assertEqual(bulk_assignment.docstatus, 1)
        
        # Verify all assets assigned to department
        for asset in assets:
            updated_asset = frappe.get_doc('Asset', asset.name)
            self.assertEqual(updated_asset.current_department, 'IT Department')
        
        # Bulk maintenance
        bulk_maintenance = self.bulk_schedule_maintenance(assets)
        self.assertEqual(bulk_maintenance.docstatus, 1)
        
        # Verify maintenance records created
        maintenance_count = frappe.db.count('Asset Maintenance', {
            'parent': bulk_maintenance.name
        })
        self.assertEqual(maintenance_count, len(assets))
    
    # Helper methods for integration tests
    def assign_asset_to_employee(self, asset, employee):
        """Helper method to assign asset to employee"""
        assignment = frappe.get_doc({
            "doctype": "Asset Assignment",
            "asset": asset.name,
            "assigned_to": employee.name,
            "assignment_date": frappe.utils.today(),
            "status": "Active"
        })
        assignment.insert()
        assignment.submit()
        return assignment
    
    def return_asset_from_employee(self, asset, employee):
        """Helper method to return asset from employee"""
        # Find active assignment
        assignment = frappe.get_doc('Asset Assignment', {
            'asset': asset.name,
            'assigned_to': employee.name,
            'status': 'Active'
        })
        
        assignment.status = 'Closed'
        assignment.return_date = frappe.utils.today()
        assignment.save()
        assignment.submit()
        
        # Update asset status
        asset.current_status = 'Available'
        asset.save()
        
        return assignment
    
    def create_maintenance_record(self, asset):
        """Helper method to create maintenance record"""
        maintenance = frappe.get_doc({
            "doctype": "Asset Maintenance",
            "asset": asset.name,
            "maintenance_date": frappe.utils.today(),
            "maintenance_type": "Preventive",
            "status": "Open",
            "description": "Routine maintenance"
        })
        maintenance.insert()
        return maintenance
    
    def dispose_asset(self, asset):
        """Helper method to dispose asset"""
        disposal = frappe.get_doc({
            "doctype": "Asset Disposal",
            "asset": asset.name,
            "disposal_date": frappe.utils.today(),
            "disposal_method": "Scrap",
            "disposal_reason": "End of Life"
        })
        disposal.insert()
        disposal.submit()
        
        # Update asset status
        asset.current_status = 'Disposed'
        asset.save()
        
        return disposal
    
    def create_test_employee(self, email):
        """Helper method to create test employee"""
        user = frappe.get_doc({
            "doctype": "User",
            "email": email,
            "first_name": "Test",
            "last_name": f"Employee {email.split('@')[0]}",
            "enabled": 1
        })
        user.insert()
        
        employee = frappe.get_doc({
            "doctype": "Employee",
            "employee_name": user.full_name,
            "company": "Test Company",
            "user_id": user.email,
            "status": "Active"
        })
        employee.insert()
        
        return employee
    
    def transfer_asset(self, asset, from_employee, to_employee):
        """Helper method to transfer asset between employees"""
        transfer = frappe.get_doc({
            "doctype": "Asset Transfer",
            "asset": asset.name,
            "transfer_from": from_employee.name,
            "transfer_to": to_employee.name,
            "transfer_date": frappe.utils.today()
        })
        transfer.insert()
        transfer.submit()
        return transfer
    
    def create_asset_audit(self, asset_names):
        """Helper method to create asset audit"""
        audit = frappe.get_doc({
            "doctype": "Asset Audit",
            "audit_date": frappe.utils.today(),
            "status": "Scheduled"
        })
        audit.insert()
        
        # Add assets to audit
        for asset_name in asset_names:
            audit.append('assets', {
                'asset': asset_name
            })
        
        audit.save()
        return audit
    
    def create_audit_entry(self, audit_name, asset_name, status, condition):
        """Helper method to create audit entry"""
        entry = frappe.get_doc({
            "doctype": "Asset Audit Entry",
            "audit": audit_name,
            "asset": asset_name,
            "status": status,
            "condition": condition,
            "audit_date": frappe.utils.today()
        })
        entry.insert()
        return entry
    
    def generate_audit_report(self, audit_name):
        """Helper method to generate audit report"""
        audit = frappe.get_doc('Asset Audit', audit_name)
        
        total_assets = len(audit.assets)
        found_assets = len([a for a in audit.assets if a.status == 'Found'])
        missing_assets = len([a for a in audit.assets if a.status == 'Missing'])
        
        return {
            'total_assets': total_assets,
            'found_assets': found_assets,
            'missing_assets': missing_assets
        }
    
    def bulk_assign_to_department(self, assets, department):
        """Helper method for bulk department assignment"""
        bulk_assignment = frappe.get_doc({
            "doctype": "Bulk Asset Assignment",
            "department": department,
            "assignment_date": frappe.utils.today()
        })
        bulk_assignment.insert()
        
        for asset in assets:
            bulk_assignment.append('assets', {'asset': asset.name})
        
        bulk_assignment.submit()
        return bulk_assignment
    
    def bulk_schedule_maintenance(self, assets):
        """Helper method for bulk maintenance scheduling"""
        bulk_maintenance = frappe.get_doc({
            "doctype": "Bulk Asset Maintenance",
            "maintenance_date": frappe.utils.today(),
            "maintenance_type": "Preventive"
        })
        bulk_maintenance.insert()
        
        for asset in assets:
            bulk_maintenance.append('assets', {'asset': asset.name})
        
        bulk_maintenance.submit()
        return bulk_maintenance
    
    def create_test_asset(self, name):
        """Helper method to create test asset"""
        return frappe.get_doc({
            "doctype": "Asset",
            "asset_name": name,
            "asset_category": "Test Category",
            "company": "Test Company",
            "purchase_date": "2024-01-01",
            "purchase_cost": 500.00,
            "current_status": "Available"
        }).insert()
```

### 15.6 CI/CD Pipeline Integration

**GitHub Actions Configuration**

```yaml
# .github/workflows/test.yml - GitHub Actions for Frappe testing

name: Frappe Test Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      mariadb:
        image: mariadb:10.6
        env:
          MYSQL_ROOT_PASSWORD: root
          MYSQL_DATABASE: test_frappe
        options: >-
          --health-cmd="mysqladmin ping"
          --health-interval=10s
          --health-timeout=5s
          --health-retries=3
        ports:
          - 3306:3306
      
      redis:
        image: redis:6.2
        options: >-
          --health-cmd="redis-cli ping"
          --health-interval=10s
          --health-timeout=5s
          --health-retries=3
        ports:
          - 6379:6379
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Cache pip dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
        restore-keys: |
          ${{ runner.os }}-pip-
    
    - name: Install system dependencies
      run: |
        sudo apt-get update
        sudo apt-get install -y \
          python3-dev \
          python3-setuptools \
          python3-pip \
          build-essential \
          libffi-dev \
          libssl-dev \
          libmysqlclient-dev \
          redis-tools \
          mariadb-client
    
    - name: Install Frappe bench
      run: |
        pip install frappe-bench
    
    - name: Setup bench
      run: |
        bench init --frappe-branch version-14 frappe-bench
        cd frappe-bench
        
        # Get apps
        bench get-app erpnext --branch version-14
        bench get-app your_app ${{ github.workspace }}
        
        # Create test site
        bench new-site test.frappe --admin-password admin --mariadb-root-password root
        
        # Install apps
        bench install-app your_app
        
        # Configure for testing
        bench --site test.frappe set-config developer_mode 1
        bench --site test.frappe set-config enable_telemetry 0
    
    - name: Run tests
      run: |
        cd frappe-bench
        
        # Run all tests
        bench --site test.frappe test your_app
        
        # Generate coverage report
        bench --site test.frappe test --coverage your_app
    
    - name: Upload coverage reports
      uses: codecov/codecov-action@v3
      with:
        file: frappe-bench/sites/test.frappe/coverage.xml
        flags: unittests
        name: codecov-umbrella
    
    - name: Run linting
      run: |
        cd frappe-bench/apps/your_app
        flake8 --max-line-length=120 --ignore=E501,W503 .
        black --check .
    
    - name: Security scan
      run: |
        cd frappe-bench
        bench --site test.frappe execute your_app.tests.security_tests.run_security_scan
    
    - name: Performance tests
      run: |
        cd frappe-bench
        bench --site test.frappe execute your_app.tests.performance_tests.run_performance_tests
    
    - name: Archive test results
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: test-results
        path: |
          frappe-bench/sites/test.frappe/test-results/
          frappe-bench/sites/test.frappe/coverage.xml
```

**Jenkins Pipeline Configuration**

```groovy
// Jenkinsfile - Jenkins pipeline for Frappe testing

pipeline {
    agent any
    
    environment {
        FRAPPE_BRANCH = 'version-14'
        TEST_SITE = 'test.frappe'
        DB_ROOT_PASSWORD = credentials('db-root-password')
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Setup Environment') {
            steps {
                sh '''
                    # Install dependencies
                    sudo apt-get update
                    sudo apt-get install -y python3-dev python3-pip build-essential libffi-dev libssl-dev libmysqlclient-dev
                    
                    # Install bench
                    pip install frappe-bench
                    
                    # Initialize bench
                    bench init --frappe-branch ${FRAPPE_BRANCH} frappe-bench
                    cd frappe-bench
                    
                    # Get apps
                    bench get-app erpnext --branch ${FRAPPE_BRANCH}
                    bench get-app your_app ${WORKSPACE}
                    
                    # Create test site
                    bench new-site ${TEST_SITE} --admin-password admin --mariadb-root-password ${DB_ROOT_PASSWORD}
                    
                    # Install apps
                    bench install-app your_app
                    
                    # Configure for testing
                    bench --site ${TEST_SITE} set-config developer_mode 1
                '''
            }
        }
        
        stage('Unit Tests') {
            steps {
                sh '''
                    cd frappe-bench
                    bench --site ${TEST_SITE} test your_app --module your_app.tests.test_asset_controller
                    bench --site ${TEST_SITE} test your_app --module your_app.tests.test_api_methods
                '''
            }
            post {
                always {
                    publishTestResults testResultsPattern: 'frappe-bench/sites/test.frappe/test-results/**/*.xml'
                }
            }
        }
        
        stage('Integration Tests') {
            steps {
                sh '''
                    cd frappe-bench
                    bench --site ${TEST_SITE} test your_app --module your_app.tests.test_integration
                '''
            }
        }
        
        stage('Coverage') {
            steps {
                sh '''
                    cd frappe-bench
                    bench --site ${TEST_SITE} test --coverage your_app
                '''
            }
            post {
                success {
                    publishCoverage adapters: [coberturaAdapter('frappe-bench/sites/test.frappe/coverage.xml')], sourceFileResolver: sourceFiles('STORE_LAST_BUILD')
                }
            }
        }
        
        stage('Quality Checks') {
            parallel {
                stage('Linting') {
                    steps {
                        sh '''
                            cd frappe-bench/apps/your_app
                            flake8 --max-line-length=120 --ignore=E501,W503 .
                            black --check .
                        '''
                    }
                }
                
                stage('Security Scan') {
                    steps {
                        sh '''
                            cd frappe-bench
                            bench --site ${TEST_SITE} execute your_app.tests.security_tests.run_security_scan
                        '''
                    }
                }
            }
        }
        
        stage('Performance Tests') {
            steps {
                sh '''
                    cd frappe-bench
                    bench --site ${TEST_SITE} execute your_app.tests.performance_tests.run_performance_tests
                '''
            }
        }
    }
    
    post {
        always {
            archiveArtifacts artifacts: 'frappe-bench/sites/test.frappe/test-results/**/*,frappe-bench/sites/test.frappe/coverage.xml', fingerprint: true
        }
        
        success {
            echo 'All tests passed!'
        }
        
        failure {
            echo 'Tests failed. Check logs for details.'
        }
    }
}
```

**Test Configuration and Scripts**

```python
# your_app/tests/security_tests.py - Security tests

import frappe
from frappe.tests.utils import FrappeTestCase

def run_security_scan():
    """Run comprehensive security scan"""
    
    print("Running security scan...")
    
    # Test 1: SQL injection vulnerabilities
    test_sql_injection_protection()
    
    # Test 2: XSS vulnerabilities
    test_xss_protection()
    
    # Test 3: Permission bypass
    test_permission_bypass()
    
    # Test 4: Authentication security
    test_authentication_security()
    
    print("Security scan completed.")

def test_sql_injection_protection():
    """Test SQL injection protection"""
    
    # Test malicious input in API calls
    malicious_inputs = [
        "'; DROP TABLE tabUser; --",
        "' OR '1'='1",
        "admin'--",
        "admin' /*"
    ]
    
    for malicious_input in malicious_inputs:
        try:
            # Test in get_doc
            result = frappe.get_doc('User', malicious_input)
            assert not result, f"SQL injection vulnerability detected with input: {malicious_input}"
        except Exception:
            pass  # Expected to fail
    
    print("✓ SQL injection protection tests passed")

def test_xss_protection():
    """Test XSS protection"""
    
    xss_payloads = [
        "<script>alert('xss')</script>",
        "javascript:alert('xss')",
        "<img src=x onerror=alert('xss')>",
        "';alert('xss');//"
    ]
    
    for payload in xss_payloads:
        # Test in data fields
        doc = frappe.get_doc({
            'doctype': 'User',
            'email': f'test{len(payload)}@example.com',
            'first_name': payload
        })
        
        # Sanitization should occur
        sanitized_name = doc.first_name
        assert '<script>' not in sanitized_name, f"XSS vulnerability detected with payload: {payload}"
    
    print("✓ XSS protection tests passed")

def test_permission_bypass():
    """Test permission bypass attempts"""
    
    # Create test user with minimal permissions
    test_user = frappe.get_doc({
        'doctype': 'User',
        'email': 'minimal_user@example.com',
        'first_name': 'Minimal',
        'enabled': 1
    })
    test_user.insert()
    
    # Test permission bypass
    frappe.set_user(test_user.name)
    
    try:
        # Should not be able to access restricted data
        result = frappe.get_all('User', fields=['name', 'email'])
        # Should only return own record
        assert len(result) <= 1, "Permission bypass detected"
    finally:
        frappe.set_user('Administrator')
    
    print("✓ Permission bypass tests passed")

def test_authentication_security():
    """Test authentication security"""
    
    # Test weak password detection
    weak_passwords = ['password', '123456', 'admin', 'password123']
    
    for weak_password in weak_passwords:
        try:
            user = frappe.get_doc({
                'doctype': 'User',
                'email': f'test{weak_password}@example.com',
                'first_name': 'Test',
                'enabled': 1,
                'new_password': weak_password
            })
            user.insert()
            
            # Should enforce password policy
            assert user.password_policy_failed, f"Weak password accepted: {weak_password}"
        except frappe.ValidationError:
            pass  # Expected to fail
    
    print("✓ Authentication security tests passed")

# your_app/tests/performance_tests.py - Performance tests

import frappe
import time
from frappe.tests.utils import FrappeTestCase

def run_performance_tests():
    """Run performance tests"""
    
    print("Running performance tests...")
    
    # Test 1: Query performance
    test_query_performance()
    
    # Test 2: Document load performance
    test_document_load_performance()
    
    # Test 3: API response performance
    test_api_performance()
    
    print("Performance tests completed.")

def test_query_performance():
    """Test database query performance"""
    
    queries = [
        "SELECT name FROM `tabUser` WHERE enabled = 1",
        "SELECT name, customer_name FROM `tabCustomer` ORDER BY creation DESC LIMIT 50",
        "SELECT COUNT(*) as count FROM `tabAsset` WHERE current_status = 'Available'"
    ]
    
    for query in queries:
        start_time = time.time()
        result = frappe.db.sql(query, as_dict=True)
        end_time = time.time()
        
        duration = (end_time - start_time) * 1000  # Convert to milliseconds
        
        # Assert reasonable performance (should be under 100ms for simple queries)
        assert duration < 100, f"Slow query detected: {query} took {duration:.2f}ms"
    
    print("✓ Query performance tests passed")

def test_document_load_performance():
    """Test document loading performance"""
    
    # Test loading different document types
    doctypes = ['User', 'Role', 'Asset', 'Company']
    
    for doctype in doctypes:
        # Get a document name
        doc_name = frappe.db.get_value(doctype, {'docstatus': ['<', 2]}, 'name')
        
        if doc_name:
            start_time = time.time()
            doc = frappe.get_doc(doctype, doc_name)
            end_time = time.time()
            
            duration = (end_time - start_time) * 1000
            
            # Document loading should be under 50ms
            assert duration < 50, f"Slow document load: {doctype} took {duration:.2f}ms"
    
    print("✓ Document load performance tests passed")

def test_api_performance():
    """Test API response performance"""
    
    # Test common API endpoints
    api_tests = [
        ('frappe.client.get', {'doctype': 'User', 'name': 'Administrator'}),
        ('frappe.client.get_list', {'doctype': 'Role', 'limit': 20}),
        ('frappe.client.count', {'doctype': 'User'})
    ]
    
    for method, args in api_tests:
        start_time = time.time()
        result = frappe.call(method, **args)
        end_time = time.time()
        
        duration = (end_time - start_time) * 1000
        
        # API calls should be under 200ms
        assert duration < 200, f"Slow API response: {method} took {duration:.2f}ms"
    
    print("✓ API performance tests passed")
```

## 🛠️ Practical Exercises

### Exercise 15.1: Create Comprehensive Unit Tests

1. Write unit tests for your custom DocType controllers
2. Test all validation rules and business logic
3. Test custom methods with various inputs
4. Achieve at least 80% code coverage

### Exercise 15.2: Build Integration Tests

1. Create end-to-end workflow tests
2. Test multi-document transactions
3. Test error scenarios and recovery
4. Verify data consistency

### Exercise 15.3: Set Up CI/CD Pipeline

1. Configure GitHub Actions or Jenkins
2. Set up automated testing on pull requests
3. Configure coverage reporting
4. Add quality gates and security scans

## 🤔 Thought Questions

1. How do you balance test coverage with development velocity?
2. What's the right level of testing for different types of applications?
3. How do you handle testing of external integrations?
4. What strategies do you use for maintaining test data?

## 📖 Further Reading

- [Frappe Testing Documentation](https://frappeframework.com/docs/user/en/testing)
- [Python unittest Framework](https://docs.python.org/3/library/unittest.html)
- [CI/CD Best Practices](https://docs.github.com/en/actions/guides)

## 🎯 Chapter Summary

Automated testing ensures code quality and reliability:

- **Unit Tests** validate individual components and methods
- **Integration Tests** verify complex workflows and interactions
- **API Tests** ensure REST endpoints work correctly
- **Fixtures** provide consistent test data management
- **CI/CD** automates testing in development workflow
- **Performance Tests** maintain application responsiveness

---

**Next Chapter**: Performance tuning and optimization strategies.


---

## Addendum: FrappeTestCase vs unittest.TestCase

### A.1 Why `FrappeTestCase` Instead of Plain `unittest.TestCase`

`frappe.tests.utils.FrappeTestCase` (v14+) wraps `unittest.TestCase` with Frappe-specific setup that plain `unittest.TestCase` does not provide:

| Feature | `unittest.TestCase` | `FrappeTestCase` |
|---------|--------------------|--------------------|
| Database transaction rollback after each test | ✗ manual | ✓ automatic |
| `frappe.init()` / site context | ✗ must call manually | ✓ handled in `setUpClass` |
| `frappe.flags.test_events = 1` | ✗ | ✓ set automatically |
| `frappe.db.rollback()` in `tearDown` | ✗ | ✓ |
| Access to `self.assertDocumentEqual()` helper | ✗ | ✓ |
| Works with `bench run-tests` | ✓ (if site is initialised) | ✓ |

Always inherit from `FrappeTestCase` for DocType and API tests:

```python
# tests/test_asset.py
from frappe.tests.utils import FrappeTestCase

class TestAsset(FrappeTestCase):
    def test_naming_series(self):
        doc = frappe.get_doc({
            "doctype": "Asset",
            "asset_name": "Laptop 001",
            "asset_category": "Electronics",
            "purchase_date": "2025-01-01",
            "purchase_cost": 1500,
        })
        doc.insert()
        self.assertTrue(doc.name.startswith("AST-"))
```

Use plain `unittest.TestCase` only for pure-Python utility functions that have zero Frappe dependencies.

### A.2 Running Tests

```bash
# Run all tests for an app
bench --site dev.local run-tests --app asset_management

# Run a specific test module
bench --site dev.local run-tests --module asset_management.tests.test_asset

# Run a specific test class
bench --site dev.local run-tests --module asset_management.tests.test_asset \
    --test TestAssetDepreciationEdgeCases
```

### A.3 `TestAssetDepreciationEdgeCases` (added in this session)

The file `chapter-15-automated-testing/tests/test_asset.py` now includes a `TestAssetDepreciationEdgeCases` class that covers:

- Zero purchase cost
- Depreciation on the purchase date itself
- Fully depreciated asset (book value = 0)
- Depreciation with a mid-year purchase
- Negative depreciation guard
- Leap-year date boundary
- Asset with no depreciation schedule

These edge cases complement the existing `TestAssetController` and `TestAssetMethods` classes and are designed to run with `FrappeTestCase` so each test is automatically rolled back.


---

## 📌 Addendum: Frappe Unit Testing — Fundamentals and Patterns

### Testing Framework Overview

Frappe uses Python's built-in `unittest` framework. Key features:
- **Automatic database rollback** after each test
- **Test record management** — automatic creation and cleanup of test data
- **Permission testing** — built-in utilities for testing user permissions
- **Cache management** — automatic cache clearing between tests
- **Parallel execution** support

### Prerequisites

```bash
# Enable tests for your site
bench --site [site-name] set-config allow_tests true

# Install dev dependencies
bench setup requirements --dev
```

### Directory Structure

```
your_app/
├── your_app/
│   ├── module/
│   │   ├── doctype/
│   │   │   └── doctype_name/
│   │   │       ├── doctype_name.py
│   │   │       ├── test_doctype_name.py   # DocType tests
│   │   │       └── test_records.json      # Test data (optional)
│   │   └── tests/
│   │       └── test_module.py             # Module-level tests
│   └── tests/
│       └── test_app.py                    # App-level tests
```

### Base Test Classes

#### FrappeTestCase (primary)

```python
import frappe
from frappe.tests.utils import FrappeTestCase

class TestMyDocType(FrappeTestCase):
    def test_something(self):
        pass
```

Key: always call `super().setUpClass()` if you override `setUpClass`. Database changes are automatically rolled back after each test.

#### FrappeAPITestCase (for API endpoints)

```python
from frappe.tests.test_api import FrappeAPITestCase

class TestMyAPI(FrappeAPITestCase):
    version = "v1"  # or "v2"
    
    def test_get_resource(self):
        response = self.get(self.resource("ToDo", "test-todo"))
        self.assertEqual(response.status_code, 200)
    
    def test_create_resource(self):
        data = {"doctype": "ToDo", "description": "Test"}
        response = self.post(self.resource("ToDo"), data)
        self.assertEqual(response.status_code, 200)
```

#### MockedRequestTestCase (for external HTTP calls)

```python
from frappe.tests.utils import MockedRequestTestCase
import responses

class TestExternalAPI(MockedRequestTestCase):
    def test_external_call(self):
        self.responses.add(
            responses.GET,
            "https://api.example.com/data",
            json={"status": "ok"},
            status=200
        )
        result = call_external_api()
        self.assertEqual(result["status"], "ok")
```

### Common Test Patterns

#### Document creation

```python
def test_create_document(self):
    doc = frappe.get_doc({
        "doctype": "MyDocType",
        "field1": "value1"
    })
    doc.insert()
    
    self.assertIsNotNone(doc.name)
    self.assertTrue(frappe.db.exists("MyDocType", doc.name))
```

#### Validation errors

```python
def test_required_field_validation(self):
    doc = frappe.get_doc({"doctype": "MyDocType"})  # Missing required field
    
    with self.assertRaises(frappe.ValidationError):
        doc.insert()
```

#### Permission testing

```python
def test_permissions(self):
    doc = frappe.get_doc({"doctype": "MyDocType", "field1": "value1"})
    doc.insert()
    
    with self.set_user("test@example.com"):
        doc = frappe.get_doc("MyDocType", doc.name)
        self.assertTrue(doc.has_permission("read"))
        self.assertFalse(doc.has_permission("write"))
```

#### Document updates

```python
def test_update_document(self):
    doc = frappe.get_doc({"doctype": "MyDocType", "field1": "old_value"})
    doc.insert()
    
    doc.field1 = "new_value"
    doc.save()
    
    doc.reload()
    self.assertEqual(doc.field1, "new_value")
```

### Test File Naming Rules

1. Test files **must** start with `test_`
2. For DocType tests: match the DocType name (`test_item.py` for `Item`)
3. Test methods **must** start with `test_`
4. Use descriptive names: `test_create_document`, `test_validate_required_fields`

### Test Discovery

Frappe automatically discovers:
- Files starting with `test_`
- Classes inheriting from `unittest.TestCase` or `FrappeTestCase`
- Methods starting with `test_`

Excluded directories: `locals/`, `.git/`, `public/`, `__pycache__/`, `doctype/doctype/boilerplate/`

### Running Tests

```bash
# Run all tests for an app
bench run-tests --app your_app

# Run tests for a specific DocType
bench run-tests --doctype "My DocType"

# Run a specific test
bench run-tests --test "test_create_document"

# Run with coverage
bench run-tests --app your_app --coverage

# Run and stop on first failure
bench run-tests --app your_app --failfast
```

### Testing Whitelisted API Methods

```python
class TestAPIMethods(FrappeTestCase):
    def setUp(self):
        super().setUp()
        self.api_user = frappe.get_doc({
            "doctype": "User",
            "email": "api_user@example.com",
            "first_name": "API",
            "enabled": 1
        })
        self.api_user.insert()
        frappe.add_roles(self.api_user.name, "System Manager")
    
    def test_api_success(self):
        frappe.set_user(self.api_user.name)
        try:
            result = my_whitelisted_function(param="value")
            self.assertIsInstance(result, dict)
            self.assertTrue(result.get("success"))
        finally:
            frappe.set_user("Administrator")
    
    def test_api_permission_denied(self):
        limited_user = frappe.get_doc({
            "doctype": "User",
            "email": "limited@example.com",
            "first_name": "Limited",
            "enabled": 1
        })
        limited_user.insert()
        
        frappe.set_user(limited_user.name)
        try:
            with self.assertRaises(frappe.PermissionError):
                my_whitelisted_function(param="value")
        finally:
            frappe.set_user("Administrator")
```

### Test Series Reference

The full unit testing guide spans 10 parts:
- Part 1: Fundamentals (test structure, base classes, discovery)
- Part 2: Test Commands and Execution
- Part 3: Test Patterns and Best Practices
- Part 4: Advanced Testing Techniques
- Part 5: Test Data Management
- Part 6: Test Utilities and Techniques
- Part 7: Assertions
- Part 8: Reports
- Part 9: Test Records
- Part 10: Improving Test Coverage


---

## 📌 Addendum: Frappe Unit Testing — The Complete Reference

### Testing Architecture Overview

Frappe uses Python's `unittest` framework with a custom `FrappeTestCase` base class that provides:
- Automatic database rollback after each test
- Thread-local variable cleanup
- Cache clearing between tests
- Custom assertion methods
- User context management (`set_user`, `freeze_time`)

### Enabling Tests

```bash
# Enable tests for a site (required before running any tests)
bench --site [site-name] set-config allow_tests true
```

### Test Commands Reference

```bash
# Run all tests
bench --site [site] run-tests

# Run tests for a specific app
bench --site [site] run-tests --app my_app

# Run tests for a specific DocType
bench --site [site] run-tests --doctype "Sales Order"

# Run a specific test method
bench --site [site] run-tests --doctype "Sales Order" --test test_create_order

# Run with verbose output
bench --site [site] run-tests --app my_app --verbose

# Stop on first failure
bench --site [site] run-tests --app my_app --failfast

# Skip test record creation (when records already exist)
bench --site [site] run-tests --doctype "Sales Order" --skip-test-records

# Generate coverage report
bench --site [site] run-tests --app my_app --coverage

# Run parallel tests (for CI/CD)
bench --site [site] run-parallel-tests --app my_app --build-number 1 --total-builds 4
```

### Quick Testing (Without Full Test Suite)

```bash
# Test a specific patch
bench execute my_app.patches.v1_0.my_patch.execute

# Trigger a scheduler event manually
bench trigger-scheduler-event my_app.tasks.daily_task

# Test translations
bench --site [site] console
# Then: frappe.lang = "ar"; frappe._("hello")

# Test notifications
bench console
# Then: from frappe.email.doctype.notification.notification import trigger_daily_alerts; trigger_daily_alerts()
```

### Test File Structure

```
your_app/
└── your_app/
    └── module/
        └── doctype/
            └── my_doctype/
                ├── my_doctype.py
                ├── test_my_doctype.py    # Test file
                └── test_records.json     # Test data
```

### Base Test Class

```python
import frappe
from frappe.tests.utils import FrappeTestCase

class TestMyDocType(FrappeTestCase):
    """All tests inherit from FrappeTestCase"""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()  # ALWAYS call super()
        # Expensive setup done once for all tests
        cls.shared_data = frappe.get_doc("Company", "_Test Company")
    
    def setUp(self):
        super().setUp()
        # Fresh setup before each test
        self.test_doc = frappe.get_doc({
            "doctype": "MyDocType",
            "field1": "value1"
        }).insert()
    
    def test_something(self):
        self.assertEqual(self.test_doc.field1, "value1")
```

### Test Data: test_records.json

```json
[
  {
    "doctype": "MyDocType",
    "field1": "_Test Value 1",
    "field2": "value2"
  },
  {
    "doctype": "MyDocType",
    "field1": "_Test Value 2",
    "docstatus": 1
  }
]
```

Frappe automatically:
1. Detects all Link fields (dependencies)
2. Creates dependencies first (recursively)
3. Creates your records last
4. Caches in `.test_log` to avoid recreation

### Declaring Dependencies

```python
# test_my_doctype.py
test_dependencies = ["Company", "Customer", "Item"]
test_ignore = ["Account"]  # Break circular dependencies

class TestMyDocType(FrappeTestCase):
    pass  # Dependencies created automatically
```

### Context Managers

```python
class TestMyDocType(FrappeTestCase):
    def test_user_context(self):
        with self.set_user("test@example.com"):
            # All operations run as this user
            doc = frappe.get_doc("MyDocType", "test-doc")
    
    def test_frozen_time(self):
        with self.freeze_time("2024-01-15 10:00:00"):
            # All datetime operations use frozen time
            doc = frappe.get_doc({"doctype": "MyDocType"}).insert()
            self.assertEqual(str(doc.creation.date()), "2024-01-15")
    
    def test_query_performance(self):
        with self.assertQueryCount(5):
            # Fails if more than 5 SQL queries are executed
            frappe.get_all("MyDocType", limit=10)
    
    def test_rows_read(self):
        with self.assertRowsRead(100):
            frappe.get_all("MyDocType", limit=100)
```

### Frappe-Specific Assertions

```python
def test_document_equal(self):
    expected = {
        "field1": "value1",
        "field2": 100,
        "items": [
            {"item_code": "ITEM-001", "qty": 10}
        ]
    }
    actual = frappe.get_doc("MyDocType", "test-doc")
    self.assertDocumentEqual(expected, actual)  # Handles floats, child tables, datetimes

def test_subset(self):
    all_roles = ["Employee", "Manager", "Admin"]
    user_roles = ["Employee", "Manager"]
    self.assertSequenceSubset(all_roles, user_roles)
```

### Mocking

```python
from unittest.mock import patch, Mock

class TestWithMocks(FrappeTestCase):
    @patch('frappe.sendmail')
    def test_email_not_sent(self, mock_sendmail):
        # Code that calls frappe.sendmail
        trigger_notification()
        mock_sendmail.assert_called_once()
    
    @patch.dict(frappe.conf, {"developer_mode": 0})
    def test_production_mode(self):
        self.assertEqual(frappe.conf.developer_mode, 0)
    
    def test_with_context_patch(self):
        with patch('frappe.get_doc') as mock_get_doc:
            mock_doc = Mock()
            mock_doc.name = "test-doc"
            mock_get_doc.return_value = mock_doc
            
            result = frappe.get_doc("MyDocType", "test-doc")
            self.assertEqual(result.name, "test-doc")
```

### Testing API Methods

```python
from frappe.tests.test_api import FrappeAPITestCase

class TestMyAPI(FrappeAPITestCase):
    version = "v1"
    
    def test_get_resource(self):
        response = self.get(self.resource("MyDocType", "test-doc"))
        self.assertEqual(response.status_code, 200)
    
    def test_create_resource(self):
        data = {"doctype": "MyDocType", "field1": "value1"}
        response = self.post(self.resource("MyDocType"), data)
        self.assertEqual(response.status_code, 200)
    
    def test_api_method(self):
        response = self.get(self.method("my_app.api.my_function"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["message"], "expected_value")
```

### Testing Reports

```python
from frappe.tests.utils import FrappeTestCase
from my_app.module.report.my_report.my_report import execute

class TestMyReport(FrappeTestCase):
    def setUp(self):
        self.filters = frappe._dict(
            company="_Test Company",
            from_date="2021-01-01",
            to_date="2021-12-31",
        )
    
    def test_report_execution(self):
        columns, data = execute(self.filters)
        self.assertIsInstance(columns, list)
        self.assertGreater(len(columns), 0)
        self.assertIsInstance(data, list)
    
    def test_report_data_structure(self):
        columns, data = execute(self.filters)
        if data:
            for col in columns:
                self.assertIn("fieldname", col)
                self.assertIn("label", col)
```

### Coverage Configuration

Create `.coveragerc` in your app root to get accurate coverage:

```ini
[run]
omit =
    tests/*
    **/test_*.py
    **/__init__.py
    **/doctype/*/*.py          # Auto-generated DocType files
    **/doctype/*/*_dashboard.py
    **/patches/*
    **/commands/*

[report]
exclude_lines =
    pragma: no cover
    if TYPE_CHECKING:
    def __repr__
    raise NotImplementedError
    if __name__ == .__main__.:
    @(abc\.)?abstractmethod
```

Use `# pragma: no cover` for code that genuinely shouldn't be unit tested:

```python
if TYPE_CHECKING:  # pragma: no cover
    from frappe.types import DF

if __name__ == "__main__":  # pragma: no cover
    main()
```

### Factory Functions Pattern

For complex test data, use factory functions:

```python
def make_test_asset(asset_name="Test Asset", **kwargs):
    """Factory function for creating test assets"""
    defaults = {
        "doctype": "Asset",
        "asset_name": asset_name,
        "asset_category": "_Test Asset Category",
        "company": "_Test Company",
        "purchase_date": "2024-01-01",
        "purchase_cost": 1000.00,
    }
    defaults.update(kwargs)
    
    doc = frappe.get_doc(defaults)
    if not kwargs.get("do_not_save"):
        doc.insert()
        if not kwargs.get("do_not_submit"):
            doc.submit()
    return doc

# Usage
asset = make_test_asset(purchase_cost=5000)
asset_draft = make_test_asset(do_not_submit=True)
```

### Common Exception Types

```python
frappe.ValidationError      # HTTP 417 — default for frappe.throw()
frappe.MandatoryError       # Missing required field
frappe.PermissionError      # HTTP 403
frappe.DoesNotExistError    # HTTP 404
frappe.DuplicateEntryError  # Duplicate record
frappe.LinkValidationError  # Invalid link reference

# Usage in tests
with self.assertRaises(frappe.ValidationError):
    doc.insert()

with self.assertRaises(frappe.PermissionError):
    frappe.get_doc("Restricted DocType", "name")
```
