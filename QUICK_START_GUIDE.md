# Quick Start Guide

## Mastering ERPNext Development - Get Started in 5 Minutes

This guide helps you quickly set up and explore the three complete applications included in this book.

---

## Prerequisites

- Frappe Bench installed and configured
- Python 3.10+
- MariaDB 10.3+
- Node.js 16+

If you don't have Frappe Bench, follow Chapter 2 for setup instructions.

---

## Quick Installation

### 1. Clone the Repository

```bash
git clone https://github.com/maysaraadmin/mastering-erpnext-dev.git
cd mastering-erpnext-dev
```

### 2. Install the Three Apps

```bash
cd ~/frappe-bench

# Install Asset Management App
bench get-app asset_management_app /path/to/mastering-erpnext-dev/projects/asset_management/asset_management_app
bench --site your-site.local install-app asset_management_app

# Install Production Planning App
bench get-app production_planning_app /path/to/mastering-erpnext-dev/projects/production_planning/production_planning_app
bench --site your-site.local install-app production_planning_app

# Install Vendor Portal App
bench get-app vendor_portal_app /path/to/mastering-erpnext-dev/projects/vendor_portal/vendor_portal_app
bench --site your-site.local install-app vendor_portal_app

# Run migrations
bench --site your-site.local migrate
```

### 3. Start the Server

```bash
bench start
```

Visit: http://localhost:8000

---

## Explore the Apps

### Asset Management System

**Access:** Desk > Asset Management

**Try This:**
1. Create an Asset Category (e.g., "Laptops")
2. Create an Asset with purchase details
3. Assign the asset to an employee
4. Schedule maintenance
5. View the dashboard: `/app/asset-dashboard`
6. Run the Utilization Report

**API Test:**
```python
# In Frappe console (bench console)
import frappe

# Get available assets
assets = frappe.call(
    'asset_management_app.asset_management.doctype.asset.asset.get_available_assets',
    asset_category='Laptops'
)
print(assets)
```

### Production Planning Tool

**Access:** Desk > Production Planning

**Try This:**
1. Create a Sales Order (if not exists)
2. Create a Production Plan
3. Select "Get Items From" > "Sales Order"
4. Click "Get Sales Orders"
5. Click "Get Raw Materials" for BOM explosion
6. Submit to create work orders

**API Test:**
```python
# Get pending sales orders
orders = frappe.call(
    'production_planning_app.production_planning.doctype.production_plan.production_plan.get_sales_orders',
    from_date='2026-01-01',
    to_date='2026-12-31',
    company='Your Company'
)
print(orders)
```

### Vendor Portal

**Access:** REST API endpoints

**Try This:**

1. **Authenticate:**
```bash
curl -X POST http://localhost:8000/api/method/vendor_portal_app.vendor_portal.api.vendor.authenticate \
  -H "Content-Type: application/json" \
  -d '{"api_key":"your-key","api_secret":"your-secret"}'
```

2. **Get Purchase Orders:**
```bash
curl -X GET "http://localhost:8000/api/method/vendor_portal_app.vendor_portal.api.vendor.get_purchase_orders?vendor=VENDOR-001" \
  -H "Authorization: Bearer YOUR-TOKEN"
```

3. **Get PO Details:**
```bash
curl -X GET "http://localhost:8000/api/method/vendor_portal_app.vendor_portal.api.purchase_order.get_purchase_order_details?purchase_order=PO-0001" \
  -H "Authorization: Bearer YOUR-TOKEN"
```

---

## Code Examples

### Explore JavaScript Examples (Chapter 7)

```bash
cd chapter-07-client-side-mastery/client_scripts/
ls -la
# form_events.js - Form lifecycle events
# custom_dialogs.js - Dialog patterns
# dynamic_ui.js - Dynamic UI manipulation
# api_calls.js - API call patterns
# field_validation.js - Validation logic
```

### Explore Python Examples (Chapter 8)

```bash
cd chapter-08-server-script-hooks/
ls -la hooks_examples/
ls -la scheduler_jobs/
ls -la background_jobs/
```

### Run Tests (Chapter 15)

```bash
# Run all tests
bench --site your-site.local run-tests --app asset_management_app

# Run specific test
bench --site your-site.local run-tests --doctype "Asset"
```

---

## Common Tasks

### Enable Scheduler (for automated tasks)

```bash
bench --site your-site.local enable-scheduler
```

### View Logs

```bash
# Application logs
tail -f ~/frappe-bench/sites/your-site.local/logs/web.log

# Error logs
tail -f ~/frappe-bench/sites/your-site.local/logs/error.log
```

### Clear Cache

```bash
bench --site your-site.local clear-cache
```

### Rebuild Assets

```bash
bench build
```

---

## Learning Path

### Beginner (Weeks 1-2)
1. Read Chapters 1-3 (Foundation)
2. Set up development environment
3. Explore the Asset Management app
4. Modify JavaScript examples in Chapter 7

### Intermediate (Weeks 3-4)
1. Read Chapters 4-7 (Core Development)
2. Study Asset Management app code
3. Create custom fields and modifications
4. Write your own client scripts

### Advanced (Weeks 5-6)
1. Read Chapters 8-10 (Business Logic)
2. Study Production Planning app
3. Implement custom hooks and schedulers
4. Create custom reports

### Expert (Weeks 7-8)
1. Read Chapters 11-17 (Projects & Production)
2. Study Vendor Portal app
3. Build your own custom app
4. Deploy to production

---

## Troubleshooting

### App not showing in desk
```bash
bench --site your-site.local clear-cache
bench build
```

### Migration errors
```bash
bench --site your-site.local migrate --skip-failing
```

### Permission errors
```bash
# Add yourself to required roles
bench --site your-site.local add-to-role your@email.com "Asset Manager"
bench --site your-site.local add-to-role your@email.com "Manufacturing Manager"
```

### API authentication issues
- Check API key/secret in Vendor master
- Verify token hasn't expired (24-hour limit)
- Check Authorization header format

---

## Next Steps

1. **Read the Book:** Start with Chapter 1 and work through sequentially
2. **Explore Code:** Study the three apps in the `projects/` directory
3. **Experiment:** Modify examples and see what happens
4. **Build:** Create your own custom app using the patterns learned
5. **Deploy:** Use Chapter 17 guides to deploy to production

---

## Resources

- **Official Docs:** https://frappeframework.com/docs
- **Community Forum:** https://discuss.frappe.io
- **GitHub:** https://github.com/frappe
- **Book Repository:** https://github.com/maysaraadmin/mastering-erpnext-dev

---

## Support

- **Issues:** Open a GitHub issue
- **Questions:** Ask on Frappe Forum
- **Contributions:** See CONTRIBUTING.md

---

**Happy Coding!** 🚀

Start with the Asset Management app - it's the most complete and easiest to understand!

