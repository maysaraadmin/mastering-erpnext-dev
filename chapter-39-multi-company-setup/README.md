# Chapter 39: Multi-Company Setup - Enterprise Multi-Entity Management

## 🎯 Learning Objectives

By the end of this chapter, you will master:
- **Setting up** multi-company environments in ERPNext
- **Managing** shared resources across companies
- **Implementing** company-specific workflows and permissions
- **Handling** inter-company transactions and reporting
- **Optimizing** performance for multi-company deployments
- **Security** considerations for multi-company setups
- **Data isolation** and sharing strategies
- **Consolidated reporting** across multiple entities

## 📚 Chapter Topics

### 39.1 Understanding Multi-Company Architecture

**Multi-Company System Overview**

ERPNext's multi-company feature allows managing multiple legal entities within a single instance while maintaining proper data isolation and security boundaries.

> **📊 Visual Reference**: See the complete ERPNext architecture diagram in `resources/diagrams/erpnext_architecture.md` for understanding how multi-company fits into the overall system architecture.

#### Multi-Company Data Model

```python
# Multi-company data structure
class MultiCompanyDataModel:
    """Multi-company data model and relationships"""
    
    def __init__(self):
        self.companies = self._get_companies()
        self.shared_resources = self._get_shared_resources()
        self.company_specific_data = self._get_company_data()
    
    def _get_companies(self):
        """Get all companies in the system"""
        return frappe.db.get_all('Company', 
            fields=['name', 'company_name', 'abbr', 'country', 'currency'],
            order_by='name'
        )
    
    def _get_shared_resources(self):
        """Get resources shared across companies"""
        return {
            'users': self._get_shared_users(),
            'item_groups': self._get_shared_item_groups(),
            'chart_of_accounts': self._get_shared_accounts(),
            'custom_fields': self._get_shared_custom_fields()
        }
    
    def _get_company_data(self):
        """Get company-specific data structure"""
        company_data = {}
        for company in self.companies:
            company_data[company.name] = {
                'customers': f"tabCustomer for {company.name}",
                'suppliers': f"tabSupplier for {company.name}",
                'sales_orders': f"tabSales Order for {company.name}",
                'purchase_orders': f"tabPurchase Order for {company.name}",
                'gl_entries': f"tabGL Entry for {company.name}",
                'stock_ledger': f"tabStock Ledger Entry for {company.name}"
            }
        return company_data
```

#### Company Isolation Levels

```python
# Company isolation configuration
class CompanyIsolationLevels:
    """Different levels of company data isolation"""
    
    ISOLATION_LEVELS = {
        'complete': {
            'description': 'Complete data isolation',
            'shared_resources': ['Users', 'Roles', 'Permissions'],
            'isolated_resources': [
                'Customers', 'Suppliers', 'Sales Orders', 
                'Purchase Orders', 'GL Entries', 'Inventory'
            ],
            'use_case': 'Separate legal entities with no data sharing'
        },
        'partial': {
            'description': 'Partial data sharing',
            'shared_resources': [
                'Users', 'Roles', 'Permissions', 'Items', 
                'Item Groups', 'Chart of Accounts'
            ],
            'isolated_resources': [
                'Customers', 'Suppliers', 'Transactions', 
                'GL Entries', 'Inventory'
            ],
            'use_case': 'Related entities with shared master data'
        },
        'consolidated': {
            'description': 'Consolidated operations with reporting',
            'shared_resources': [
                'Users', 'Roles', 'Permissions', 'Items', 
                'Customers', 'Suppliers'
            ],
            'isolated_resources': [
                'GL Entries', 'Inventory', 'Bank Accounts'
            ],
            'use_case': 'Holding company with subsidiaries'
        }
    }
    
    def configure_isolation(self, level, companies):
        """Configure company isolation level"""
        
        config = self.ISOLATION_LEVELS[level]
        
        for company in companies:
            self._setup_company_isolation(company, config)
    
    def _setup_company_isolation(self, company, config):
        """Setup isolation for specific company"""
        
        # Set up shared resources
        for resource in config['shared_resources']:
            self._configure_shared_resource(resource, company)
        
        # Set up isolated resources
        for resource in config['isolated_resources']:
            self._configure_isolated_resource(resource, company)
```

### 39.2 Setting Up Multi-Company Environment

**Initial Configuration**

```python
# Multi-company setup script
class MultiCompanySetup:
    """Setup multi-company environment"""
    
    def __init__(self):
        self.default_company = None
        self.additional_companies = []
        self.setup_complete = False
    
    def create_master_company(self):
        """Create master/parent company"""
        
        master_company = frappe.get_doc({
            'doctype': 'Company',
            'company_name': 'Holding Company Inc.',
            'abbr': 'HCI',
            'country': 'United States',
            'currency': 'USD',
            'domain': 'Holding',
            'default_currency': 'USD',
            'default_gst_account': 'Input Tax CGST - HCI',
            'default_cst_account': 'Input Tax CST - HCI',
            'default_vat_account': 'Input VAT - HCI',
            'default_service_tax_account': 'Service Tax - HCI',
            'default_expense_account': 'Office Expenses - HCI',
            'default_income_account': 'Sales - HCI',
            'default_payable_account': 'Creditors - HCI',
            'default_receivable_account': 'Debtors - HCI',
            'default_bank_account': 'Bank - HCI',
            'cash_account': 'Bank - HCI',
            'round_off_account': 'Exchange Gain/Loss - HCI',
            'write_off_account': 'Exchange Gain/Loss - HCI',
            'depreciation_expense_account': 'Depreciation - HCI',
            'accumulated_depreciation_account': 'Accumulated Depreciation - HCI',
            'disposal_account': 'Asset Disposal Account - HCI',
            'capital_work_in_progress_account': 'Capital Work in Progress - HCI',
            'stock_received_but_not_billed': 'Stock Received But Not Billed - HCI',
            'default_finance_book': 'HCI - Finance Book',
            'cost_center': 'Main - HCI',
            'warehouse': 'Stores - HCI',
            'email': 'info@holdingcompany.com',
            'phone': '+1-555-0100',
            'website': 'https://holdingcompany.com',
            'favicon': '/assets/holding_favicon.ico',
            'brand_html': '<strong>Holding Company Inc.</strong>',
            'timezone': 'America/New_York',
            'date_format': 'dd-mm-yyyy',
            'time_format': 'HH:mm',
            'number_format': '#,###.##',
            'default_price_list': 'Standard Selling',
            'default_buying_price_list': 'Standard Buying',
            'enable_perpetual_inventory': 1,
            'stock_uom': 'Units',
            'dimension_uom': 'Inches',
            'weight_uom': 'Pound',
            'last_naming_series': 'HCI-.YYYY.-',
            'series_start_value': '1000'
        })
        
        master_company.insert(ignore_permissions=True)
        self.default_company = master_company.name
        
        # Set as default company
        frappe.db.set_single_value('Global Defaults', 'default_company', master_company.name)
        
        return master_company
    
    def create_subsidiary_companies(self):
        """Create subsidiary companies"""
        
        subsidiaries_data = [
            {
                'company_name': 'North America Operations LLC',
                'abbr': 'NAO',
                'country': 'United States',
                'currency': 'USD',
                'domain': 'North America',
                'parent_company': self.default_company,
                'email': 'na@holdingcompany.com'
            },
            {
                'company_name': 'European Operations GmbH',
                'abbr': 'EOG',
                'country': 'Germany',
                'currency': 'EUR',
                'domain': 'Europe',
                'parent_company': self.default_company,
                'email': 'eu@holdingcompany.com'
            },
            {
                'company_name': 'Asia Pacific Pte Ltd',
                'abbr': 'APL',
                'country': 'Singapore',
                'currency': 'SGD',
                'domain': 'Asia Pacific',
                'parent_company': self.default_company,
                'email': 'ap@holdingcompany.com'
            }
        ]
        
        for sub_data in subsidiaries_data:
            subsidiary = frappe.get_doc({
                'doctype': 'Company',
                **sub_data,
                'default_currency': sub_data['currency'],
                'default_gst_account': f'Input Tax CGST - {sub_data["abbr"]}',
                'default_cst_account': f'Input Tax CST - {sub_data["abbr"]}',
                'default_vat_account': f'Input VAT - {sub_data["abbr"]}',
                'default_service_tax_account': f'Service Tax - {sub_data["abbr"]}',
                'default_expense_account': f'Office Expenses - {sub_data["abbr"]}',
                'default_income_account': f'Sales - {sub_data["abbr"]}',
                'default_payable_account': f'Creditors - {sub_data["abbr"]}',
                'default_receivable_account': f'Debtors - {sub_data["abbr"]}',
                'default_bank_account': f'Bank - {sub_data["abbr"]}',
                'cash_account': f'Bank - {sub_data["abbr"]}',
                'round_off_account': f'Exchange Gain/Loss - {sub_data["abbr"]}',
                'write_off_account': f'Exchange Gain/Loss - {sub_data["abbr"]}',
                'depreciation_expense_account': f'Depreciation - {sub_data["abbr"]}',
                'accumulated_depreciation_account': f'Accumulated Depreciation - {sub_data["abbr"]}',
                'disposal_account': f'Asset Disposal Account - {sub_data["abbr"]}',
                'capital_work_in_progress_account': f'Capital Work in Progress - {sub_data["abbr"]}',
                'stock_received_but_not_billed': f'Stock Received But Not Billed - {sub_data["abbr"]}',
                'default_finance_book': f'{sub_data["abbr"]} - Finance Book',
                'cost_center': f'Main - {sub_data["abbr"]}',
                'warehouse': f'Stores - {sub_data["abbr"]}',
                'last_naming_series': f'{sub_data["abbr"]}-.YYYY.-',
                'series_start_value': '1000'
            })
            
            subsidiary.insert(ignore_permissions=True)
            self.additional_companies.append(subsidiary.name)
        
        return self.additional_companies
```

**User and Role Configuration**

```python
# Multi-company user and role setup
class MultiCompanyUserSetup:
    """Setup users and roles for multi-company environment"""
    
    def __init__(self):
        self.companies = frappe.db.get_all('Company', pluck='name')
        self.user_roles = {}
    
    def create_multi_company_roles(self):
        """Create roles for multi-company access"""
        
        # Global roles (access to all companies)
        global_roles = [
            {
                'role_name': 'System Manager',
                'desk_access': 1,
                'restrict_to_domain': 0,
                'is_standard': 1,
                'permissions': [
                    {'doctype': 'Company', 'permlevel': 1, 'read': 1, 'write': 1, 'create': 1, 'delete': 1},
                    {'doctype': 'User', 'permlevel': 1, 'read': 1, 'write': 1, 'create': 1, 'delete': 1},
                    {'doctype': 'Role', 'permlevel': 1, 'read': 1, 'write': 1, 'create': 1, 'delete': 1}
                ]
            },
            {
                'role_name': 'Global Finance Manager',
                'desk_access': 1,
                'restrict_to_domain': 0,
                'is_standard': 1,
                'permissions': [
                    {'doctype': 'GL Entry', 'permlevel': 0, 'read': 1, 'write': 1, 'create': 1, 'submit': 1},
                    {'doctype': 'Sales Invoice', 'permlevel': 0, 'read': 1, 'write': 1, 'create': 1, 'submit': 1},
                    {'doctype': 'Purchase Invoice', 'permlevel': 0, 'read': 1, 'write': 1, 'create': 1, 'submit': 1}
                ]
            }
        ]
        
        # Company-specific roles
        for company in self.companies:
            company_roles = [
                {
                    'role_name': f'{company} Finance Manager',
                    'desk_access': 1,
                    'restrict_to_domain': company,
                    'is_standard': 1,
                    'permissions': [
                        {'doctype': 'GL Entry', 'permlevel': 0, 'read': 1, 'write': 1, 'create': 1, 'submit': 1},
                        {'doctype': 'Sales Invoice', 'permlevel': 0, 'read': 1, 'write': 1, 'create': 1, 'submit': 1},
                        {'doctype': 'Purchase Invoice', 'permlevel': 0, 'read': 1, 'write': 1, 'create': 1, 'submit': 1}
                    ]
                },
                {
                    'role_name': f'{company} Sales Manager',
                    'desk_access': 1,
                    'restrict_to_domain': company,
                    'is_standard': 1,
                    'permissions': [
                        {'doctype': 'Customer', 'permlevel': 0, 'read': 1, 'write': 1, 'create': 1, 'delete': 1},
                        {'doctype': 'Sales Order', 'permlevel': 0, 'read': 1, 'write': 1, 'create': 1, 'submit': 1},
                        {'doctype': 'Sales Invoice', 'permlevel': 0, 'read': 1, 'write': 1, 'create': 1, 'submit': 1}
                    ]
                }
            ]
            global_roles.extend(company_roles)
        
        # Create roles
        for role_data in global_roles:
            if not frappe.db.exists('Role', role_data['role_name']):
                role = frappe.get_doc(role_data)
                role.insert(ignore_permissions=True)
                
                # Add permissions
                for perm in role_data['permissions']:
                    role.append('permissions', perm)
                
                role.save(ignore_permissions=True)
    
    def setup_user_permissions(self, user_email, companies, roles):
        """Setup user permissions for specific companies"""
        
        user = frappe.get_doc('User', user_email)
        
        # Add user to companies
        for company in companies:
            user_permission = frappe.get_doc({
                'doctype': 'User Permission',
                'user': user_email,
                'allow': 'Company',
                'for_value': company,
                'is_default': 1 if company == companies[0] else 0
            })
            user_permission.insert(ignore_permissions=True)
        
        # Assign roles
        for role_name in roles:
            user.append('roles', {'role': role_name})
        
        user.save(ignore_permissions=True)
```

### 39.3 Managing Shared Resources

**Shared Items and Master Data**

```python
# Shared resources management
class SharedResourceManager:
    """Manage resources shared across companies"""
    
    def __init__(self):
        self.shared_doctypes = ['Item', 'Item Group', 'Customer Group', 'Supplier Group', 'Chart of Accounts']
        self.isolated_doctypes = ['Customer', 'Supplier', 'Sales Order', 'Purchase Order', 'GL Entry']
    
    def configure_shared_doctypes(self):
        """Configure doctypes to be shared across companies"""
        
        for doctype in self.shared_doctypes:
            # Update doctype to be shared
            frappe.db.set_value('DocType', doctype, 'allow_multiple_companies', 1)
            
            # Remove company field from shared doctypes
            if frappe.db.exists('Custom Field', {'dt': doctype, 'fieldname': 'company'}):
                frappe.delete_doc('Custom Field', {
                    'dt': doctype,
                    'fieldname': 'company'
                })
    
    def configure_isolated_doctypes(self):
        """Configure doctypes to be company-specific"""
        
        for doctype in self.isolated_doctypes:
            # Ensure company field exists
            if not frappe.db.exists('Custom Field', {'dt': doctype, 'fieldname': 'company'}):
                company_field = frappe.get_doc({
                    'doctype': 'Custom Field',
                    'dt': doctype,
                    'fieldname': 'company',
                    'fieldtype': 'Link',
                    'options': 'Company',
                    'label': 'Company',
                    'reqd': 1,
                    'insert_after': 'naming_series'
                })
                company_field.insert(ignore_permissions=True)
            
            # Update doctype to require company
            frappe.db.set_value('DocType', doctype, 'allow_multiple_companies', 0)
    
    def setup_shared_item_management(self):
        """Setup shared item management across companies"""
        
        # Create shared item groups
        shared_groups = [
            {'item_group_name': 'Raw Materials', 'parent_item_group': 'All Item Groups'},
            {'item_group_name': 'Finished Goods', 'parent_item_group': 'All Item Groups'},
            {'item_group_name': 'Services', 'parent_item_group': 'All Item Groups'},
            {'item_group_name': 'Consumables', 'parent_item_group': 'All Item Groups'}
        ]
        
        for group_data in shared_groups:
            if not frappe.db.exists('Item Group', group_data['item_group_name']):
                group = frappe.get_doc(group_data)
                group.insert(ignore_permissions=True)
    
    def setup_company_specific_pricing(self):
        """Setup company-specific pricing for shared items"""
        
        companies = frappe.db.get_all('Company', pluck='name')
        
        for company in companies:
            # Create price list for each company
            price_list = frappe.get_doc({
                'doctype': 'Price List',
                'price_list_name': f'Standard Selling - {company}',
                'currency': frappe.db.get_value('Company', company, 'default_currency'),
                'enabled': 1,
                'selling': 1
            })
            price_list.insert(ignore_permissions=True)
            
            # Create item price records for shared items
            items = frappe.db.get_all('Item', 
                fields=['item_code', 'item_name'],
                limit=100  # Process in batches
            )
            
            for item in items:
                item_price = frappe.get_doc({
                    'doctype': 'Item Price',
                    'price_list': price_list.name,
                    'item_code': item['item_code'],
                    'price_list_rate': self._calculate_company_price(item, company)
                })
                item_price.insert(ignore_permissions=True)
    
    def _calculate_company_price(self, item, company):
        """Calculate company-specific price based on business rules"""
        
        base_price = frappe.db.get_value('Item', item['item_code'], 'valuation_rate') or 100
        
        # Apply company-specific multipliers
        company_multipliers = {
            'North America Operations LLC': 1.1,  # 10% markup
            'European Operations GmbH': 0.95,  # 5% discount
            'Asia Pacific Pte Ltd': 1.05   # 5% markup
        }
        
        multiplier = company_multipliers.get(company, 1.0)
        return base_price * multiplier
```

### 39.4 Inter-Company Transactions

**Inter-Company Workflows**

```python
# Inter-company transaction management
class InterCompanyTransactions:
    """Manage transactions between companies"""
    
    def __init__(self):
        self.inter_company_doctypes = ['Inter Company Journal Entry', 'Inter Company Stock Transfer']
        self.setup_inter_company_features()
    
    def setup_inter_company_features(self):
        """Setup inter-company transaction features"""
        
        # Enable inter-company features
        frappe.db.set_single_value('Accounts Settings', 'allow_inter_company_journal_entry', 1)
        frappe.db.set_single_value('Stock Settings', 'allow_inter_company_stock_transfer', 1)
    
    def create_inter_company_journal_entry(self, from_company, to_company, accounts, amounts):
        """Create inter-company journal entry"""
        
        je = frappe.get_doc({
            'doctype': 'Journal Entry',
            'voucher_type': 'Inter Company Journal Entry',
            'posting_date': frappe.utils.nowdate(),
            'company': from_company,
            'inter_company_journal_entry_reference': self._generate_reference(),
            'multi_currency': 1,
            'accounts': []
        })
        
        # Add debit and credit entries
        for account_data in accounts:
            account_entry = {
                'account': account_data['account'],
                'debit_in_account_currency': account_data.get('debit', 0),
                'credit_in_account_currency': account_data.get('credit', 0),
                'cost_center': account_data.get('cost_center'),
                'project': account_data.get('project'),
                'reference_type': account_data.get('reference_type'),
                'reference_name': account_data.get('reference_name'),
                'user_remark': f"Inter-company transaction with {to_company}"
            }
            je.append('accounts', account_entry)
        
        # Create corresponding entry in target company
        self._create_corresponding_entry(je, to_company)
        
        je.insert(ignore_permissions=True)
        je.submit()
        
        return je
    
    def create_inter_company_stock_transfer(self, from_company, to_company, items, warehouses):
        """Create inter-company stock transfer"""
        
        transfer = frappe.get_doc({
            'doctype': 'Stock Entry',
            'purpose': 'Material Transfer',
            'company': from_company,
            'inter_company_stock_transfer': 1,
            'target_company': to_company,
            'posting_date': frappe.utils.nowdate(),
            'posting_time': frappe.utils.nowtime(),
            'remarks': f"Inter-company transfer to {to_company}",
            'items': []
        })
        
        # Add items to transfer
        for item_data in items:
            item_entry = {
                'item_code': item_data['item_code'],
                'qty': item_data['quantity'],
                's_warehouse': item_data['from_warehouse'],
                't_warehouse': item_data['to_warehouse'],
                'batch_no': item_data.get('batch_no'),
                'serial_no': item_data.get('serial_no'),
                'basic_rate': item_data.get('rate'),
                'basic_amount': item_data['quantity'] * item_data.get('rate', 0)
            }
            transfer.append('items', item_entry)
        
        transfer.insert(ignore_permissions=True)
        transfer.submit()
        
        # Create corresponding receipt in target company
        self._create_stock_receipt(transfer, to_company)
        
        return transfer
    
    def _create_corresponding_entry(self, original_entry, target_company):
        """Create corresponding entry in target company"""
        
        # Switch to target company context
        frappe.set_user(target_company)
        
        try:
            corresponding_entry = frappe.get_doc({
                'doctype': original_entry.doctype,
                'posting_date': original_entry.posting_date,
                'company': target_company,
                'inter_company_journal_entry_reference': original_entry.inter_company_journal_entry_reference,
                'accounts': []
            })
            
            # Reverse the accounts for corresponding entry
            for account in original_entry.accounts:
                reversed_account = {
                    'account': account.account,
                    'debit_in_account_currency': account.credit_in_account_currency,
                    'credit_in_account_currency': account.debit_in_account_currency,
                    'cost_center': account.cost_center,
                    'project': account.project,
                    'reference_type': 'Journal Entry',
                    'reference_name': original_entry.name,
                    'user_remark': f"Corresponding entry from {original_entry.company}"
                }
                corresponding_entry.append('accounts', reversed_account)
            
            corresponding_entry.insert(ignore_permissions=True)
            corresponding_entry.submit()
            
        finally:
            # Restore original company context
            frappe.set_user(original_entry.company)
    
    def _generate_reference(self):
        """Generate unique reference for inter-company transactions"""
        import uuid
        return f"IC-{frappe.utils.nowdate().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
```

### 39.5 Consolidated Reporting

**Multi-Company Reporting**

```python
# Consolidated reporting across companies
class ConsolidatedReporting:
    """Generate consolidated reports across multiple companies"""
    
    def __init__(self):
        self.companies = frappe.db.get_all('Company', pluck='name')
        self.reporting_currency = 'USD'  # Base currency for consolidation
    
    def generate_consolidated_balance_sheet(self, date):
        """Generate consolidated balance sheet across all companies"""
        
        consolidated_data = {
            'date': date,
            'companies': {},
            'totals': {
                'total_assets': 0,
                'total_liabilities': 0,
                'total_equity': 0,
                'total_revenue': 0,
                'total_expenses': 0
            }
        }
        
        for company in self.companies:
            company_data = self._get_company_balance_sheet(company, date)
            consolidated_data['companies'][company] = company_data
            
            # Convert to reporting currency and add to totals
            converted_data = self._convert_to_reporting_currency(company_data, company)
            for key in consolidated_data['totals']:
                consolidated_data['totals'][key] += converted_data.get(key, 0)
        
        return consolidated_data
    
    def generate_consolidated_profit_loss(self, from_date, to_date):
        """Generate consolidated profit and loss statement"""
        
        consolidated_pl = {
            'from_date': from_date,
            'to_date': to_date,
            'companies': {},
            'consolidated': {
                'total_income': 0,
                'total_expenses': 0,
                'net_profit': 0,
                'gross_profit': 0,
                'operating_profit': 0
            }
        }
        
        for company in self.companies:
            company_pl = self._get_company_profit_loss(company, from_date, to_date)
            consolidated_pl['companies'][company] = company_pl
            
            # Convert and consolidate
            converted_pl = self._convert_to_reporting_currency(company_pl, company)
            for key in consolidated_pl['consolidated']:
                consolidated_pl['consolidated'][key] += converted_pl.get(key, 0)
        
        # Calculate consolidated metrics
        consolidated_pl['consolidated']['gross_profit'] = (
            consolidated_pl['consolidated']['total_income'] - 
            consolidated_pl['consolidated']['total_expenses'] * 0.7  # Assume 70% are direct costs
        )
        consolidated_pl['consolidated']['operating_profit'] = (
            consolidated_pl['consolidated']['gross_profit'] - 
            consolidated_pl['consolidated']['total_expenses'] * 0.2  # Assume 20% are operating expenses
        )
        consolidated_pl['consolidated']['net_profit'] = (
            consolidated_pl['consolidated']['total_income'] - 
            consolidated_pl['consolidated']['total_expenses']
        )
        
        return consolidated_pl
    
    def generate_inter_company_reconciliation(self, from_date, to_date):
        """Generate inter-company transaction reconciliation"""
        
        reconciliation = {
            'from_date': from_date,
            'to_date': to_date,
            'transactions': [],
            'balances': {}
        }
        
        # Get all inter-company transactions
        transactions = frappe.db.sql("""
            SELECT 
                name, company, posting_date, total_debit, total_credit,
                inter_company_journal_entry_reference
            FROM `tabJournal Entry`
            WHERE voucher_type = 'Inter Company Journal Entry'
            AND posting_date BETWEEN %s AND %s
            ORDER BY posting_date, name
        """, (from_date, to_date), as_dict=True)
        
        # Process transactions and calculate balances
        company_balances = {company: 0 for company in self.companies}
        
        for transaction in transactions:
            transaction_data = {
                'name': transaction.name,
                'company': transaction.company,
                'date': transaction.posting_date,
                'debit': transaction.total_debit,
                'credit': transaction.total_credit,
                'net': transaction.total_debit - transaction.total_credit,
                'reference': transaction.inter_company_journal_entry_reference
            }
            reconciliation['transactions'].append(transaction_data)
            
            # Update company balance
            company_balances[transaction.company] += transaction_data['net']
        
        reconciliation['balances'] = company_balances
        
        # Verify balances sum to zero (all inter-company transactions should net out)
        total_balance = sum(company_balances.values())
        reconciliation['is_balanced'] = abs(total_balance) < 0.01  # Allow for rounding
        
        return reconciliation
    
    def _get_company_balance_sheet(self, company, date):
        """Get balance sheet for specific company"""
        
        # Get company's default currency
        company_currency = frappe.db.get_value('Company', company, 'default_currency')
        
        # Get balance sheet data
        balance_sheet = frappe.db.sql("""
            SELECT 
                account,
                SUM(debit) - SUM(credit) as balance,
                account_type,
                parent_account
            FROM `tabGL Entry`
            WHERE company = %s
            AND posting_date <= %s
            AND docstatus = 1
            GROUP BY account, account_type, parent_account
        """, (company, date), as_dict=True)
        
        # Organize by account type
        assets = [a for a in balance_sheet if a.account_type == 'Asset']
        liabilities = [a for a in balance_sheet if a.account_type == 'Liability']
        equity = [a for a in balance_sheet if a.account_type == 'Equity']
        
        return {
            'company': company,
            'currency': company_currency,
            'date': date,
            'assets': {
                'total': sum(a.balance for a in assets),
                'details': assets
            },
            'liabilities': {
                'total': sum(a.balance for a in liabilities),
                'details': liabilities
            },
            'equity': {
                'total': sum(a.balance for a in equities),
                'details': equity
            }
        }
    
    def _convert_to_reporting_currency(self, data, company):
        """Convert company data to reporting currency"""
        
        company_currency = frappe.db.get_value('Company', company, 'default_currency')
        
        if company_currency == self.reporting_currency:
            return data
        
        # Get exchange rate
        exchange_rate = self._get_exchange_rate(company_currency, self.reporting_currency)
        
        # Convert monetary values
        converted_data = {}
        for key, value in data.items():
            if isinstance(value, (int, float)):
                converted_data[key] = value * exchange_rate
            elif isinstance(value, dict):
                converted_data[key] = {}
                for sub_key, sub_value in value.items():
                    if isinstance(sub_value, (int, float)):
                        converted_data[key][sub_key] = sub_value * exchange_rate
                    else:
                        converted_data[key][sub_key] = sub_value
            else:
                converted_data[key] = value
        
        return converted_data
    
    def _get_exchange_rate(self, from_currency, to_currency):
        """Get exchange rate between currencies"""
        
        if from_currency == to_currency:
            return 1.0
        
        # Try to get from system
        exchange_rate = frappe.db.get_value('Currency Exchange', 
            {
                'from_currency': from_currency,
                'to_currency': to_currency
            }, 
            'exchange_rate'
        )
        
        if exchange_rate:
            return float(exchange_rate)
        
        # Default to 1 if not found
        return 1.0
```

### 39.6 Performance Optimization for Multi-Company

**Multi-Company Performance Considerations**

```python
# Performance optimization for multi-company setups
class MultiCompanyPerformance:
    """Performance optimization for multi-company environments"""
    
    def __init__(self):
        self.companies = frappe.db.get_all('Company', pluck='name')
        self.performance_metrics = {}
    
    def optimize_database_queries(self):
        """Optimize database queries for multi-company access"""
        
        # Add company indexes for frequently accessed tables
        company_indexes = [
            {
                'table': 'tabCustomer',
                'index': 'idx_customer_company',
                'columns': ['company', 'customer_name']
            },
            {
                'table': 'tabSales Order',
                'index': 'idx_so_company_date',
                'columns': ['company', 'transaction_date', 'status']
            },
            {
                'table': 'tabGL Entry',
                'index': 'idx_gl_company_date',
                'columns': ['company', 'posting_date', 'account']
            }
        ]
        
        for index_config in company_indexes:
            self._create_composite_index(index_config)
    
    def _create_composite_index(self, index_config):
        """Create composite database index"""
        
        table = index_config['table']
        index_name = index_config['index']
        columns = index_config['columns']
        
        # Check if index exists
        index_exists = frappe.db.sql("""
            SELECT COUNT(*) as count
            FROM information_schema.statistics
            WHERE table_schema = DATABASE()
            AND table_name = %s
            AND index_name = %s
        """, (table.replace('tab', ''), index_name), as_dict=True)[0]['count'] > 0
        
        if not index_exists:
            # Create index
            columns_str = ', '.join(columns)
            frappe.db.sql(f"""
                CREATE INDEX {index_name}
                ON {table} ({columns_str})
            """)
            
            frappe.logger().info(f"Created index {index_name} on {table}")
    
    def optimize_caching_strategy(self):
        """Optimize caching for multi-company access"""
        
        # Company-specific cache keys
        for company in self.companies:
            # Warm up cache for frequently accessed data
            self._warm_company_cache(company)
        
        # Implement cache invalidation strategies
        self._setup_cache_invalidation()
    
    def _warm_company_cache(self, company):
        """Warm up cache for specific company"""
        
        cache_prefix = f"company:{company}:"
        
        # Cache company settings
        company_data = frappe.db.get_value('Company', company, '*', as_dict=True)
        frappe.cache().set_value(f"{cache_prefix}settings", company_data, expires_in_sec=3600)
        
        # Cache frequently accessed master data
        customers = frappe.db.get_all('Customer', 
            filters={'company': company}, 
            fields=['name', 'customer_name', 'email_id'],
            limit=100
        )
        frappe.cache().set_value(f"{cache_prefix}customers", customers, expires_in_sec=1800)
        
        # Cache chart of accounts
        accounts = frappe.db.get_all('Account', 
            fields=['name', 'account_name', 'account_type'],
            limit=200
        )
        frappe.cache().set_value(f"{cache_prefix}accounts", accounts, expires_in_sec=3600)
    
    def _setup_cache_invalidation(self):
        """Setup intelligent cache invalidation"""
        
        # Hook into document save events to invalidate relevant cache
        def invalidate_company_cache(doc, method):
            if doc.doctype in ['Customer', 'Supplier', 'Sales Order', 'Purchase Order']:
                company = doc.get('company')
                if company:
                    cache_prefix = f"company:{company}:"
                    
                    # Invalidate relevant cache entries
                    if doc.doctype == 'Customer':
                        frappe.cache().delete_key(f"{cache_prefix}customers")
                    elif doc.doctype in ['Sales Order', 'Purchase Order']:
                        frappe.cache().delete_key(f"{cache_prefix}transactions")
                    
                    # Invalidate company settings if company is updated
                    if doc.doctype == 'Company':
                        frappe.cache().delete_key(f"{cache_prefix}settings")
                        frappe.cache().delete_key(f"{cache_prefix}accounts")
        
        # Register cache invalidation hooks
        frappe.get_doc('Custom DocType', 'Customer').on('update', invalidate_company_cache)
        frappe.get_doc('Custom DocType', 'Supplier').on('update', invalidate_company_cache)
        frappe.get_doc('Custom DocType', 'Sales Order').on('update', invalidate_company_cache)
        frappe.get_doc('Custom DocType', 'Purchase Order').on('update', invalidate_company_cache)
        frappe.get_doc('Custom DocType', 'Company').on('update', invalidate_company_cache)
    
    def monitor_multi_company_performance(self):
        """Monitor performance across all companies"""
        
        metrics = {}
        
        for company in self.companies:
            company_metrics = {
                'query_performance': self._measure_query_performance(company),
                'cache_hit_ratio': self._measure_cache_performance(company),
                'user_activity': self._measure_user_activity(company),
                'resource_usage': self._measure_resource_usage(company)
            }
            metrics[company] = company_metrics
        
        self.performance_metrics = metrics
        return metrics
    
    def _measure_query_performance(self, company):
        """Measure database query performance for company"""
        
        # Get slow queries for this company
        slow_queries = frappe.db.sql("""
            SELECT 
                query_time,
                rows_sent,
                rows_examined,
                sql_text
            FROM performance_schema.events_statements_summary
            WHERE digest_text LIKE CONCAT('%', %s, '%')
            ORDER BY query_time DESC
            LIMIT 10
        """, f'`tab{company}`', as_dict=True)
        
        return {
            'slow_queries_count': len(slow_queries),
            'avg_query_time': sum(q['query_time'] for q in slow_queries) / len(slow_queries) if slow_queries else 0,
            'slow_queries': slow_queries
        }
    
    def _measure_cache_performance(self, company):
        """Measure cache performance for company"""
        
        cache_stats = frappe.cache().get_stats()
        
        return {
            'hit_ratio': cache_stats.get('hit_ratio', 0),
            'miss_ratio': cache_stats.get('miss_ratio', 0),
            'evictions': cache_stats.get('evictions', 0),
            'memory_usage': cache_stats.get('memory_usage', 0)
        }
```

### 39.7 Security and Compliance

**Multi-Company Security Considerations**

```python
# Security for multi-company environments
class MultiCompanySecurity:
    """Security management for multi-company setups"""
    
    def __init__(self):
        self.companies = frappe.db.get_all('Company', pluck='name')
        self.security_policies = self._load_security_policies()
    
    def implement_company_data_isolation(self):
        """Implement strict data isolation between companies"""
        
        # Row-level security policies
        isolation_policies = [
            {
                'doctype': 'Customer',
                'policy': 'strict_isolation',
                'description': 'Users can only access customers from their assigned companies'
            },
            {
                'doctype': 'Supplier',
                'policy': 'strict_isolation',
                'description': 'Users can only access suppliers from their assigned companies'
            },
            {
                'doctype': 'Sales Order',
                'policy': 'strict_isolation',
                'description': 'Sales orders are strictly company-specific'
            },
            {
                'doctype': 'GL Entry',
                'policy': 'strict_isolation',
                'description': 'Financial entries are isolated by company'
            }
        ]
        
        for policy in isolation_policies:
            self._implement_isolation_policy(policy)
    
    def _implement_isolation_policy(self, policy):
        """Implement specific isolation policy"""
        
        doctype = policy['doctype']
        
        # Add custom permission check
        permission_check_code = f"""
def check_company_permission(doc, user):
    \"\"\"Check if user has permission for this company\"\"\"
    user_companies = frappe.db.get_all('User Permission', 
        filters={{'user': user, 'allow': 'Company'}}, 
        pluck='for_value'
    )
    
    if doc.get('company') not in user_companies:
        frappe.throw('You do not have permission to access {0} data from company {{1}}'.format(
            doc.doctype, doc.get('company')
        ))
    
    return True
        """
        
        # Add to custom script
        custom_script = frappe.get_doc({
            'doctype': 'Custom Script',
            'name': f'check_{doctype.lower()}_company_permission',
            'script': permission_check_code,
            'script_type': 'Server Script'
        })
        custom_script.insert(ignore_permissions=True)
        
        # Add permission check to doctype
        frappe.db.set_value('DocType', doctype, 'permissions_check', 
            f'check_{doctype.lower()}_company_permission')
    
    def setup_audit_trail(self):
        """Setup comprehensive audit trail for multi-company access"""
        
        # Enable audit trail for sensitive operations
        audit_settings = {
            'enable_audit_trail': 1,
            'track_login_attempts': 1,
            'track_data_access': 1,
            'track_permission_changes': 1,
            'track_inter_company_transactions': 1,
            'retention_days': 2555  # 7 years
        }
        
        for key, value in audit_settings.items():
            frappe.db.set_single_value('System Settings', key, value)
    
    def implement_cross_company_access_control(self):
        """Control cross-company data access"""
        
        # Define cross-company access rules
        cross_company_rules = {
            'consolidated_reporting': {
                'allowed_roles': ['System Manager', 'Global Finance Manager'],
                'required_approval': True,
                'approval_workflow': 'Multi-Company Access Approval'
            },
            'inter_company_transactions': {
                'allowed_roles': ['System Manager', 'Regional Finance Manager'],
                'required_approval': False,  # Built into workflow
                'transaction_limits': {
                    'daily_limit': 100000,  # $100K daily
                    'monthly_limit': 1000000,  # $1M monthly
                    'requires_approval_above': 50000  # $50K requires approval
                }
            },
            'data_sharing': {
                'allowed_roles': ['System Manager'],
                'required_approval': True,
                'approval_workflow': 'Data Sharing Approval',
                'shareable_data_types': ['Customer', 'Supplier', 'Item']
            }
        }
        
        for rule_type, rule_config in cross_company_rules.items():
            self._implement_cross_company_rule(rule_type, rule_config)
    
    def _implement_cross_company_rule(self, rule_type, rule_config):
        """Implement specific cross-company access rule"""
        
        # Create custom workflow for approval
        if rule_config.get('required_approval'):
            workflow = frappe.get_doc({
                'doctype': 'Workflow',
                'workflow_name': rule_config['approval_workflow'],
                'document_type': 'Custom DocType',
                'workflow_state': [
                    {
                        'state': 'Pending Approval',
                        'action': 'Update',
                        'allowed_roles': rule_config['allowed_roles']
                    },
                    {
                        'state': 'Approved',
                        'action': 'Update',
                        'allowed_roles': ['System Manager']
                    }
                ]
            })
            workflow.insert(ignore_permissions=True)
        
        # Implement transaction limits
        if rule_type == 'inter_company_transactions':
            self._implement_transaction_limits(rule_config['transaction_limits'])
    
    def _implement_transaction_limits(self, limits):
        """Implement transaction limits for inter-company transactions"""
        
        limit_code = f"""
def check_inter_company_transaction_limits(doc):
    \"\"\"Check inter-company transaction limits\"\"\"
    if doc.doctype != 'Journal Entry' or doc.voucher_type != 'Inter Company Journal Entry':
        return True
    
    total_amount = abs(sum(d.debit_in_account_currency - d.credit_in_account_currency for d in doc.accounts))
    
    # Check daily limit
    from datetime import datetime, timedelta
    today = datetime.now().date()
    daily_total = frappe.db.sql(\"\"\"
        SELECT SUM(ABS(total_debit - total_credit)) as total
        FROM `tabJournal Entry`
        WHERE voucher_type = 'Inter Company Journal Entry'
        AND DATE(posting_date) = %s
        AND docstatus = 1
    \"\"\", today, as_dict=True)[0]['total'] or 0
    
    if daily_total + total_amount > {limits['daily_limit']}:
        frappe.throw('Daily inter-company transaction limit exceeded. Limit: ${{}}, Current: ${{}}, Attempted: ${{}}'.format(
            {limits['daily_limit']}, daily_total, daily_total + total_amount
        ))
    
    # Check approval requirement
    if total_amount > {limits['requires_approval_above']}:
        # Check if approved
        if not doc.get('inter_company_approved'):
            frappe.throw('Inter-company transactions above ${{}} require approval'.format(
                {limits['requires_approval_above']}
            ))
    
    return True
        """
        
        # Add as custom script
        custom_script = frappe.get_doc({
            'doctype': 'Custom Script',
            'name': 'check_inter_company_transaction_limits',
            'script': limit_code,
            'script_type': 'Server Script'
        })
        custom_script.insert(ignore_permissions=True)
        
        # Add to journal entry doctype
        frappe.db.set_value('DocType', 'Journal Entry', 'permissions_check', 
            'check_inter_company_transaction_limits')
```

## 🎯 Chapter Summary

### Key Takeaways

1. **Multi-Company Architecture Requires Careful Planning**
   - Define data sharing requirements upfront
   - Choose appropriate isolation levels
   - Plan for scalability from the beginning
   - Consider regulatory and compliance requirements

2. **Performance Optimization is Critical**
   - Implement proper database indexing
   - Use intelligent caching strategies
   - Monitor performance across all companies
   - Optimize for cross-company operations

3. **Security and Compliance Are Paramount**
   - Implement strict data isolation
   - Set up comprehensive audit trails
   - Control cross-company access carefully
   - Regular security assessments

4. **User Experience Should Be Seamless**
   - Clear company switching interface
   - Consistent user experience across companies
   - Proper training and documentation
   - Responsive design for different devices

### Implementation Checklist

- [ ] **Company Setup**: All companies configured with proper settings
- [ ] **User Permissions**: Role-based access with company restrictions
- [ ] **Data Isolation**: Proper isolation levels configured
- [ ] **Shared Resources**: Master data properly shared
- [ ] **Inter-Company Workflows**: Approval processes implemented
- [ ] **Consolidated Reporting**: Cross-company reporting setup
- [ ] **Performance Optimization**: Indexes and caching configured
- [ ] **Security Controls**: Audit trails and access controls
- [ ] **Testing**: Comprehensive testing of all scenarios
- [ ] **Documentation**: Clear documentation for administrators

**Remember**: Multi-company setup complexity grows exponentially with the number of companies. Start with a simple setup and gradually add complexity as needed.

---

**Next Chapter**: Advanced Topics and Future Trends
