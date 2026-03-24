# -*- coding: utf-8 -*-
"""
ORM Examples - Chapter 6: Mastering the Frappe ORM
Comprehensive examples of ORM operations and best practices for ERPNext v16/Frappe v16
Updated with modern security practices and v16 compatibility notes.
"""

import frappe
from frappe.model.document import Document
from frappe.utils import flt, cint, getdate, today, nowdate
from frappe import _
from typing import Dict, List, Any, Optional, Union

class ORMExamples:
    """
    Comprehensive ORM examples demonstrating various database operations
    and best practices in Frappe framework v16.
    
    Version Compatibility Notes:
    - frappe.db.sql(): Uses parameterized queries (recommended)
    - frappe.db.bulk_insert(): Available in v16 for bulk operations
    - frappe.new_doc(): Standard document creation
    - frappe.get_doc(): Standard document loading
    - frappe.db.get_value(): Optimized for single field retrieval
    - frappe.db.get_all(): Optimized for multiple document retrieval
    
    Security Notes:
    - Always use parameterized queries to prevent SQL injection
    - Validate inputs before database operations
    - Use frappe.throw() for proper error handling
    """
    
    def __init__(self):
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging for debugging ORM operations"""
        self.logger = frappe.logger("orm_examples")
    
    # =============================================================================
    # DOCUMENT OPERATIONS
    # =============================================================================
    
    def demonstrate_document_operations(self):
        """Demonstrate various document operations"""
        self.logger.info("=== Document Operations Demo ===")
        
        # 1. Create new document
        customer = self.create_customer_document()
        
        # 2. Load existing document
        loaded_customer = self.load_customer_document(customer.name)
        
        # 3. Update document
        updated_customer = self.update_customer_document(customer.name)
        
        # 4. Submit document (if applicable)
        # self.submit_document(customer.name)
        
        # 5. Delete document
        # self.delete_document(customer.name)
        
        return {
            "created": customer,
            "loaded": loaded_customer,
            "updated": updated_customer
        }
    
    def create_customer_document(self):
        """Create a new customer document"""
        self.logger.info("Creating new customer document")
        
        # Method 1: Using frappe.new_doc()
        customer = frappe.new_doc('Customer')
        customer.customer_name = 'John Doe'
        customer.email = 'john.doe@example.com'
        customer.customer_group = 'Individual'
        customer.territory = 'United States'
        customer.insert()
        
        self.logger.info(f"Created customer: {customer.name}")
        return customer
    
    def load_customer_document(self, customer_name):
        """Load existing customer document"""
        self.logger.info(f"Loading customer: {customer_name}")
        
        # Method 1: Using frappe.get_doc()
        customer = frappe.get_doc('Customer', customer_name)
        
        # Method 2: Using frappe.db.get_value() for specific fields
        customer_data = frappe.db.get_value('Customer', customer_name, 
                                          ['customer_name', 'email', 'customer_group'])
        
        self.logger.info(f"Loaded customer data: {customer_data}")
        return customer
    
    def update_customer_document(self, customer_name):
        """Update existing customer document"""
        self.logger.info(f"Updating customer: {customer_name}")
        
        # Method 1: Load, modify, save
        customer = frappe.get_doc('Customer', customer_name)
        customer.phone = '+1234567890'
        customer.save()
        
        # Method 2: Direct database update
        frappe.db.set_value('Customer', customer_name, {
            'mobile_no': '+0987654321',
            'website': 'https://johndoe.example.com'
        })
        
        return customer
    
    # =============================================================================
    # QUERY METHODS COMPARISON
    # =============================================================================
    
    def demonstrate_query_methods(self):
        """Compare different query methods"""
        self.logger.info("=== Query Methods Comparison ===")
        
        # Method 1: frappe.get_all()
        customers_get_all = self.get_customers_with_get_all()
        
        # Method 2: frappe.get_list()
        customers_get_list = self.get_customers_with_get_list()
        
        # Method 3: frappe.db.get_all()
        customers_db_get_all = self.get_customers_with_db_get_all()
        
        # Method 4: Raw SQL
        customers_sql = self.get_customers_with_sql()
        
        return {
            "get_all": customers_get_all,
            "get_list": customers_get_list,
            "db_get_all": customers_db_get_all,
            "sql": customers_sql
        }
    
    def get_customers_with_get_all(self):
        """Get customers using frappe.get_all()"""
        self.logger.info("Using frappe.get_all()")
        
        customers = frappe.get_all('Customer', 
            fields=['name', 'customer_name', 'email', 'customer_group'],
            filters={'customer_group': 'Individual'},
            order_by='customer_name asc',
            limit=10
        )
        
        self.logger.info(f"Found {len(customers)} customers with get_all()")
        return customers
    
    def get_customers_with_get_list(self):
        """Get customers using frappe.get_list()"""
        self.logger.info("Using frappe.get_list()")
        
        customers = frappe.get_list('Customer',
            fields=['name', 'customer_name', 'email', 'customer_group'],
            filters={'customer_group': 'Individual'},
            order_by='customer_name asc',
            limit_page_length=10
        )
        
        self.logger.info(f"Found {len(customers)} customers with get_list()")
        return customers
    
    def get_customers_with_db_get_all(self):
        """Get customers using frappe.db.get_all()"""
        self.logger.info("Using frappe.db.get_all()")
        
        customers = frappe.db.get_all('Customer',
            fields=['name', 'customer_name', 'email', 'customer_group'],
            filters={'customer_group': 'Individual'},
            order_by='customer_name asc',
            limit=10
        )
        
        self.logger.info(f"Found {len(customers)} customers with db_get_all()")
        return customers
    
    def get_customers_with_sql(self):
        """Get customers using raw SQL"""
        self.logger.info("Using raw SQL")
        
        customers = frappe.db.sql("""
            SELECT name, customer_name, email, customer_group
            FROM `tabCustomer`
            WHERE customer_group = %s
            ORDER BY customer_name ASC
            LIMIT 10
        """, ('Individual',), as_dict=True)
        
        self.logger.info(f"Found {len(customers)} customers with SQL")
        return customers
    
    # =============================================================================
    # ADVANCED QUERY WRITING
    # =============================================================================
    
    def demonstrate_advanced_queries(self):
        """Demonstrate advanced query techniques"""
        self.logger.info("=== Advanced Queries Demo ===")
        
        # Complex filters
        complex_filters = self.complex_filter_example()
        
        # Joins and relationships
        join_queries = self.join_query_example()
        
        # Aggregations
        aggregation_queries = self.aggregation_example()
        
        # Subqueries
        subquery_examples = self.subquery_example()
        
        return {
            "complex_filters": complex_filters,
            "joins": join_queries,
            "aggregations": aggregation_queries,
            "subqueries": subquery_examples
        }
    
    def complex_filter_example(self):
        """Example of complex filters"""
        self.logger.info("Complex filters example")
        
        # Multiple conditions
        orders = frappe.get_all('Sales Order',
            filters={
                'customer': 'CUST-00001',
                'status': ['!=', 'Closed'],
                'transaction_date': ['>=', '2023-01-01'],
                'grand_total': ['>', 1000]
            },
            fields=['name', 'grand_total', 'status', 'transaction_date']
        )
        
        # OR conditions
        orders_or = frappe.get_all('Sales Order',
            filters=[
                ['status', '=', 'Open'],
                ['or', ['grand_total', '>', 5000], ['transaction_date', '>=', '2023-06-01']]
            ],
            fields=['name', 'grand_total', 'status']
        )
        
        return {"and_conditions": orders, "or_conditions": orders_or}
    
    def join_query_example(self):
        """Example of join queries"""
        self.logger.info("Join queries example")
        
        # Using Link fields (automatic joins)
        orders_with_customers = frappe.get_all('Sales Order',
            fields=[
                'name', 
                'customer', 
                'customer_name',
                'grand_total'
            ],
            filters={'status': 'Submitted'},
            order_by='grand_total desc',
            limit=5
        )
        
        # Manual joins with SQL
        orders_with_details = frappe.db.sql("""
            SELECT 
                so.name as order_name,
                so.customer,
                c.customer_name,
                c.email,
                so.grand_total,
                so.transaction_date
            FROM `tabSales Order` so
            JOIN `tabCustomer` c ON so.customer = c.name
            WHERE so.status = 'Submitted'
            AND so.transaction_date >= %s
            ORDER BY so.grand_total DESC
            LIMIT 10
        """, ('2023-01-01',), as_dict=True)
        
        return {
            "auto_join": orders_with_customers,
            "manual_join": orders_with_details
        }
    
    def aggregation_example(self):
        """Example of aggregation queries"""
        self.logger.info("Aggregation queries example")
        
        # Simple aggregations
        total_sales = frappe.db.get_value('Sales Order', 
            filters={'status': 'Submitted'},
            fieldname='SUM(grand_total)'
        ) or 0
        
        # Group by operations
        sales_by_customer = frappe.db.sql("""
            SELECT 
                customer,
                customer_name,
                COUNT(*) as order_count,
                SUM(grand_total) as total_sales,
                AVG(grand_total) as avg_order_value
            FROM `tabSales Order`
            WHERE status = 'Submitted'
            AND transaction_date >= %s
            GROUP BY customer, customer_name
            HAVING COUNT(*) > 1
            ORDER BY total_sales DESC
            LIMIT 10
        """, ('2023-01-01',), as_dict=True)
        
        # Monthly sales trend
        monthly_sales = frappe.db.sql("""
            SELECT 
                DATE_FORMAT(transaction_date, '%%Y-%%m') as month,
                COUNT(*) as order_count,
                SUM(grand_total) as total_sales
            FROM `tabSales Order`
            WHERE status = 'Submitted'
            AND transaction_date >= DATE_SUB(NOW(), INTERVAL 12 MONTH)
            GROUP BY DATE_FORMAT(transaction_date, '%%Y-%%m')
            ORDER BY month ASC
        """, as_dict=True)
        
        return {
            "total_sales": total_sales,
            "by_customer": sales_by_customer,
            "monthly_trend": monthly_sales
        }
    
    def subquery_example(self):
        """Example of subqueries"""
        self.logger.info("Subquery example")
        
        # Customers with orders
        customers_with_orders = frappe.db.sql("""
            SELECT DISTINCT c.name, c.customer_name
            FROM `tabCustomer` c
            WHERE EXISTS (
                SELECT 1 FROM `tabSales Order` so 
                WHERE so.customer = c.name 
                AND so.docstatus = 1
            )
            ORDER BY c.customer_name
        """, as_dict=True)
        
        # High-value customers
        high_value_customers = frappe.db.sql("""
            SELECT c.name, c.customer_name
            FROM `tabCustomer` c
            WHERE c.name IN (
                SELECT customer 
                FROM `tabSales Order` so
                WHERE docstatus = 1
                GROUP BY customer
                HAVING SUM(so.grand_total) > 100000
            )
        """)
            
        high_value_results = high_value_customers if high_value_customers else {}
        self.logger.info(f"High-value customers query completed: {len(high_value_customers)}")
        
        return {
            "high_value_results": high_value_results,
            "execution_time": self.last_execution_time
        }
    
    # =============================================================================
    # BULK OPERATIONS
    # =============================================================================
    
    def demonstrate_bulk_operations(self):
        """Demonstrate bulk operations"""
        self.logger.info("=== Bulk Operations Demo ===")
        
        # Bulk insert
        bulk_insert_result = self.bulk_insert_example()
        
        # Bulk update
        bulk_update_result = self.bulk_update_example()
        
        # Performance comparison
        performance_comparison = self.performance_comparison()
        
        return {
            "bulk_insert": bulk_insert_result,
            "bulk_update": bulk_update_result,
            "performance": performance_comparison
        }
    
    def bulk_insert_example(self):
        """Example of bulk insert operations using frappe.db.sql for performance"""
        self.logger.info("Bulk insert example")
        
        # Prepare data for bulk insert
        customers_data = []
        for i in range(100):
            customers_data.append({
                'doctype': 'Customer',
                'customer_name': f'Bulk Customer {i}',
                'email': f'bulk{i}@example.com',
                'customer_group': 'Individual',
                'territory': 'United States'
            })
        
        import time
        start_time = time.time()
        
        # frappe.db.bulk_insert() does not exist in Frappe v14/v15.
        # Use a single SQL INSERT with multiple value rows for true bulk performance.
        import uuid
        from frappe.utils import now_datetime
        
        now = now_datetime()
        values = []
        for d in customers_data:
            name = frappe.generate_hash(length=10)
            values.append(f"('{name}', '{d['customer_name']}', '{d['customer_group']}', "
                          f"'{d['territory']}', '{frappe.session.user}', '{now}', "
                          f"'{frappe.session.user}', '{now}')")
        
        if values:
            frappe.db.sql("""
                INSERT INTO `tabCustomer`
                    (name, customer_name, customer_group, territory,
                     owner, creation, modified_by, modified)
                VALUES {}
            """.format(", ".join(values)))
            frappe.db.commit()
        
        end_time = time.time()
        duration = end_time - start_time
        
        self.logger.info(f"Bulk inserted {len(customers_data)} customers in {duration:.2f} seconds")
        
        return {
            "count": len(customers_data),
            "duration": duration,
            "records_per_second": len(customers_data) / duration
        }
    
    def bulk_update_example(self):
        """Example of bulk update operations"""
        self.logger.info("Bulk update example")
        
        # Update multiple customers
        updates = [
            {'name': 'CUST-00001', 'customer_group': 'Premium'},
            {'name': 'CUST-00002', 'customer_group': 'Premium'},
            {'name': 'CUST-00003', 'customer_group': 'Premium'}
        ]
        
        import time
        start_time = time.time()
        
        for update in updates:
            frappe.db.set_value('Customer', update['name'], 'customer_group', update['customer_group'])
        
        end_time = time.time()
        duration = end_time - start_time
        
        self.logger.info(f"Bulk updated {len(updates)} customers in {duration:.2f} seconds")
        
        return {
            "count": len(updates),
            "duration": duration
        }
    
    def performance_comparison(self):
        """Compare performance of different methods"""
        self.logger.info("Performance comparison")
        
        # Method 1: Individual inserts
        import time
        start_time = time.time()
        
        for i in range(50):
            customer = frappe.new_doc('Customer')
            customer.customer_name = f'Individual {i}'
            customer.email = f'individual{i}@example.com'
            customer.customer_group = 'Individual'
            customer.insert()
        
        individual_time = time.time() - start_time
        
        # Method 2: Bulk SQL insert (frappe.db.bulk_insert does not exist in v14/v15)
        customers_data = []
        for i in range(50):
            customers_data.append({
                'doctype': 'Customer',
                'customer_name': f'Bulk {i}',
                'email': f'bulk{i}@example.com',
                'customer_group': 'Individual'
            })
        
        from frappe.utils import now_datetime
        now = now_datetime()
        values = []
        for d in customers_data:
            name = frappe.generate_hash(length=10)
            values.append((name, d['customer_name'], 'Individual', 
                        frappe.session.user, frappe.session.user, now, now))
        
        start_time = time.time()
        if values:
            # SECURE: Use parameterized query to prevent SQL injection
            placeholders = ', '.join(['%s'] * len(values[0]))
            frappe.db.sql("""
                INSERT INTO `tabCustomer`
                    (name, customer_name, customer_group, owner, creation, modified_by, modified)
                VALUES ({})
            """.format(placeholders), tuple(values))
            """.format(placeholders), tuple(values)))
            frappe.db.commit()
        bulk_time = time.time() - start_time
        
        return {
            "individual_inserts": individual_time,
            "bulk_insert": bulk_time,
            "improvement_factor": individual_time / bulk_time
        }
    
    def demonstrate_v16_bulk_operations(self):
        """Demonstrate v16 bulk operations for better performance"""
        self.logger.info("=== v16 Bulk Operations Demo ===")
        
        # v16: Bulk insert with frappe.db.bulk_insert()
        start_time = time.time()
        
        customers_to_insert = []
        for i in range(100):
            customers_to_insert.append({
                'doctype': 'Customer',
                'customer_name': f'Bulk Customer {i}',
                'email': f'bulk{i}@example.com',
                'customer_group': 'Individual'
            })
        
        # v16: Use official bulk_insert method
        try:
            frappe.db.bulk_insert(customers_to_insert)
            bulk_insert_time = time.time() - start_time
            self.logger.info(f"v16 bulk_insert completed in {bulk_insert_time:.3f}s")
        except Exception as e:
            self.logger.error(f"v16 bulk_insert failed: {str(e)}")
        
        # v16: Bulk update with frappe.db.bulk_update()
        start_time = time.time()
        
        customers_to_update = []
        for i in range(50):
            customers_to_update.append({
                'doctype': 'Customer',
                'name': f'BULK-CUST-{i:03d}',
                'mobile_no': f'+12345678{i:03d}'
            })
        
        # v16: Use official bulk_update method
        try:
            frappe.db.bulk_update(customers_to_update)
            bulk_update_time = time.time() - start_time
            self.logger.info(f"v16 bulk_update completed in {bulk_update_time:.3f}s")
        except Exception as e:
            self.logger.error(f"v16 bulk_update failed: {str(e)}")
        
        return {
            "bulk_insert_time": bulk_insert_time,
            "bulk_update_time": bulk_update_time,
            "total_records": len(customers_to_insert) + len(customers_to_update)
        }
    
    # =============================================================================
    # TRANSACTION MANAGEMENT
    # =============================================================================
    
    def demonstrate_transactions(self):
        """Demonstrate transaction management"""
        self.logger.info("=== Transaction Management Demo ===")
        
        # Basic transaction
        basic_transaction = self.basic_transaction_example()
        
        # Savepoints
        savepoint_example = self.savepoint_example()
        
        # Error handling
        error_handling = self.error_handling_example()
        
        return {
            "basic_transaction": basic_transaction,
            "savepoints": savepoint_example,
            "error_handling": error_handling
        }
    
    def basic_transaction_example(self):
        """Example of basic transaction"""
        self.logger.info("Basic transaction example")
        
        try:
            # Start transaction
            frappe.db.begin()
            
            # Create customer
            customer = frappe.new_doc('Customer')
            customer.customer_name = 'Transaction Customer'
            customer.email = 'transaction@example.com'
            customer.customer_group = 'Individual'
            customer.insert()
            
            # Create sales order for customer
            sales_order = frappe.new_doc('Sales Order')
            sales_order.customer = customer.name
            sales_order.transaction_date = today()
            sales_order.append('items', {
                'item_code': 'ITEM-001',
                'qty': 10,
                'rate': 100
            })
            sales_order.insert()
            
            # Commit transaction
            frappe.db.commit()
            
            self.logger.info(f"Transaction completed: Customer {customer.name}, Order {sales_order.name}")
            
            return {
                "customer": customer.name,
                "sales_order": sales_order.name,
                "status": "success"
            }
            
        except Exception as e:
            # Rollback on error
            frappe.db.rollback()
            self.logger.error(f"Transaction failed: {str(e)}")
            
            return {
                "status": "failed",
                "error": str(e)
            }
    
    def savepoint_example(self):
        """Example of savepoints using the official Frappe v14/v15 savepoint API.

        frappe.db.savepoint(name) and frappe.db.rollback(save_point=name) are
        public APIs documented in the Frappe DB reference — no raw SQL needed.
        """
        self.logger.info("Savepoint example")
        
        try:
            frappe.db.begin()
            
            # First savepoint via official API
            frappe.db.savepoint("customer_created")
            
            customer = frappe.new_doc('Customer')
            customer.customer_name = 'Savepoint Customer'
            customer.email = 'savepoint@example.com'
            customer.customer_group = 'Individual'
            customer.insert()
            
            try:
                # Second savepoint via official API
                frappe.db.savepoint("order_created")
                
                sales_order = frappe.new_doc('Sales Order')
                sales_order.customer = customer.name
                sales_order.transaction_date = today()
                # Simulate error - missing required fields
                sales_order.insert()
                
            except Exception as e:
                # Rollback to named savepoint via official API
                frappe.db.rollback(save_point="order_created")
                self.logger.warning(f"Order creation failed, rolled back: {str(e)}")
            
            # Continue with customer creation
            frappe.db.commit()
            
            return {
                "customer": customer.name,
                "status": "partial_success"
            }
            
        except Exception as e:
            frappe.db.rollback()
            self.logger.error(f"Savepoint transaction failed: {str(e)}")
            return {"status": "failed", "error": str(e)}
    
    def error_handling_example(self):
        """Example of transaction error handling"""
        self.logger.info("Error handling example")
        
        def create_customer_with_validation(customer_data):
            """Create customer with validation"""
            try:
                frappe.db.begin()
                
                # Validate email
                if not customer_data.get('email') or '@' not in customer_data['email']:
                    raise ValueError("Invalid email address")
                
                # Check for duplicate
                if frappe.db.exists('Customer', {'email': customer_data['email']}):
                    raise ValueError("Customer with this email already exists")
                
                customer = frappe.new_doc('Customer')
                customer.update(customer_data)
                customer.insert()
                
                frappe.db.commit()
                return {"status": "success", "customer": customer.name}
                
            except ValueError as e:
                frappe.db.rollback()
                return {"status": "validation_error", "error": str(e)}
            except Exception as e:
                frappe.db.rollback()
                frappe.log_error(f"Customer creation failed: {str(e)}")
                return {"status": "error", "error": str(e)}
        
        # Test with valid data
        valid_result = create_customer_with_validation({
            'customer_name': 'Valid Customer',
            'email': 'valid@example.com',
            'customer_group': 'Individual'
        })
        
        # Test with invalid data
        invalid_result = create_customer_with_validation({
            'customer_name': 'Invalid Customer',
            'email': 'invalid-email',
            'customer_group': 'Individual'
        })
        
        return {
            "valid_data": valid_result,
            "invalid_data": invalid_result
        }
    
    # =============================================================================
    # QUERY OPTIMIZATION
    # =============================================================================
    
    def demonstrate_query_optimization(self):
        """Demonstrate query optimization techniques"""
        self.logger.info("=== Query Optimization Demo ===")
        
        # Query analysis
        query_analysis = self.analyze_queries()
        
        # Optimization strategies
        optimization_strategies = self.optimization_examples()
        
        # Caching strategies
        caching_examples = self.caching_examples()
        
        return {
            "analysis": query_analysis,
            "optimization": optimization_strategies,
            "caching": caching_examples
        }
    
    def analyze_queries(self):
        """Analyze query performance"""
        self.logger.info("Query analysis")
        
        # Analyze simple query
        explain_simple = frappe.db.sql("""
            EXPLAIN SELECT name, customer_name 
            FROM `tabCustomer` 
            WHERE customer_group = 'Individual'
        """)
        
        # Analyze complex query
        explain_complex = frappe.db.sql("""
            EXPLAIN SELECT so.name, so.grand_total, c.customer_name
            FROM `tabSales Order` so
            JOIN `tabCustomer` c ON so.customer = c.name
            WHERE so.status = 'Submitted'
            ORDER BY so.transaction_date DESC
            LIMIT 100
        """)
        
        return {
            "simple_query": explain_simple,
            "complex_query": explain_complex
        }
    
    def optimization_examples(self):
        """Examples of query optimization"""
        self.logger.info("Optimization examples")
        
        # Strategy 1: Specific fields vs *
        specific_fields = frappe.db.sql("""
            SELECT name, customer_name, email 
            FROM `tabCustomer` 
            WHERE customer_group = %s
            LIMIT 100
        """, ('Individual',), as_dict=True)
        
        # Strategy 2: Use LIMIT
        limited_results = frappe.get_all('Customer', 
                                       filters={'customer_group': 'Individual'},
                                       limit_page_length=100)
        
        # Strategy 3: Use EXISTS instead of IN
        exists_query = frappe.db.sql("""
            SELECT DISTINCT name FROM `tabCustomer` c
            WHERE EXISTS (
                SELECT 1 FROM `tabSales Order` so 
                WHERE so.customer = c.name
            )
            LIMIT 50
        """, as_dict=True)
        
        return {
            "specific_fields": len(specific_fields),
            "limited_results": len(limited_results),
            "exists_query": len(exists_query)
        }
    
    def caching_examples(self):
        """Examples of caching strategies"""
        self.logger.info("Caching examples")
        
        def get_customer_with_cache(customer_id):
            """Get customer with caching"""
            cache_key = f"customer_data_{customer_id}"
            
            # Try to get from cache
            # NOTE: In Frappe v15+, frappe.cache is a property (no parentheses).
            # frappe.cache().get() is the v14 pattern; use frappe.cache.get_value() in v15.
            cached_data = frappe.cache.get_value(cache_key)
            if cached_data:
                self.logger.info(f"Customer {customer_id} found in cache")
                return cached_data
            
            # Get from database
            # TIP: For read-heavy paths, prefer frappe.get_cached_doc() which uses
            # Frappe's built-in document cache and is ~10,000x faster on repeated reads.
            customer = frappe.get_doc('Customer', customer_id)
            customer_data = customer.as_dict()
            
            # Cache for 1 hour (v15 API: frappe.cache.set_value)
            frappe.cache.set_value(cache_key, customer_data, expires_in_sec=3600)
            
            self.logger.info(f"Customer {customer_id} loaded from database and cached")
            return customer_data
        
        # Test caching
        customer_data = get_customer_with_cache('CUST-00001')
        cached_data = get_customer_with_cache('CUST-00001')
        
        return {
            "first_load": "from_database",
            "second_load": "from_cache",
            "data_consistency": customer_data == cached_data
        }
    
    # =============================================================================
    # UTILITY METHODS
    # =============================================================================
    
    def cleanup_test_data(self):
        """Clean up test data created during examples"""
        self.logger.info("Cleaning up test data")
        
        # Remove test customers
        test_customers = frappe.get_all('Customer', 
                                       filters={'customer_name': ['like', '%Test%']})
        
        for customer in test_customers:
            try:
                frappe.delete_doc('Customer', customer.name)
                self.logger.info(f"Deleted test customer: {customer.name}")
            except Exception as e:
                self.logger.error(f"Failed to delete customer {customer.name}: {str(e)}")
        
        # Clear cache (v15 API: frappe.cache.clear())
        frappe.cache.clear()
        
        self.logger.info("Cleanup completed")
    
    def get_performance_metrics(self):
        """Get performance metrics for ORM operations"""
        self.logger.info("Collecting performance metrics")
        
        metrics = {
            "customer_count": frappe.db.count('Customer'),
            "sales_order_count": frappe.db.count('Sales Order'),
            "item_count": frappe.db.count('Item'),
            "database_size": self.get_database_size(),
            "cache_stats": self.get_cache_stats()
        }
        
        return metrics
    
    def get_database_size(self):
        """Get database size information"""
        try:
            size_info = frappe.db.sql("""
                SELECT 
                    table_schema as 'Database',
                    ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS 'Size (MB)'
                FROM information_schema.tables 
                WHERE table_schema = DATABASE()
                GROUP BY table_schema
            """, as_dict=True)
            
            return size_info[0] if size_info else {"Size (MB)": 0}
        except Exception as e:
            self.logger.error(f"Failed to get database size: {str(e)}")
            return {"Size (MB)": 0}
    
    def get_cache_stats(self):
        """Get cache statistics"""
        try:
            # This is a simplified example
            return {
                "cache_enabled": True,
                "cache_type": "Redis" if frappe.cache.redis else "File"
            }
        except Exception as e:
            self.logger.error(f"Failed to get cache stats: {str(e)}")
            return {"cache_enabled": False}


# =============================================================================
# MAIN DEMONSTRATION FUNCTION
# =============================================================================

def run_orm_examples():
    """Run all ORM examples"""
    examples = ORMExamples()
    
    print("=== Frappe ORM Examples ===")
    print("Running comprehensive ORM demonstrations...\n")
    
    try:
        # Document operations
        doc_ops = examples.demonstrate_document_operations()
        print(f"✓ Document Operations: {len(doc_ops)} examples completed")
        
        # Query methods
        query_methods = examples.demonstrate_query_methods()
        print(f"✓ Query Methods: {len(query_methods)} methods demonstrated")
        
        # Advanced queries
        advanced_queries = examples.demonstrate_advanced_queries()
        print(f"✓ Advanced Queries: {len(advanced_queries)} techniques shown")
        
        # Bulk operations
        bulk_ops = examples.demonstrate_bulk_operations()
        print(f"✓ Bulk Operations: {len(bulk_ops)} operations tested")
        
        # Transactions
        transactions = examples.demonstrate_transactions()
        print(f"✓ Transactions: {len(transactions)} scenarios handled")
        
        # Optimization
        optimization = examples.demonstrate_query_optimization()
        print(f"✓ Query Optimization: {len(optimization)} strategies applied")
        
        # Performance metrics
        metrics = examples.get_performance_metrics()
        print(f"✓ Performance Metrics: {len(metrics)} metrics collected")
        
        print("\n=== All ORM Examples Completed Successfully ===")
        
        return {
            "document_operations": doc_ops,
            "query_methods": query_methods,
            "advanced_queries": advanced_queries,
            "bulk_operations": bulk_ops,
            "transactions": transactions,
            "optimization": optimization,
            "metrics": metrics
        }
        
    except Exception as e:
        print(f"❌ Error running examples: {str(e)}")
        frappe.log_error(f"ORM Examples Error: {str(e)}")
        return None
    
    finally:
        # Cleanup
        examples.cleanup_test_data()


if __name__ == "__main__":
    # Run examples when script is executed directly
    results = run_orm_examples()
    if results:
        print("\nResults summary:")
        for key, value in results.items():
            print(f"  {key}: {type(value).__name__}")
