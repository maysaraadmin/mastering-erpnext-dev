# Production Planning System

Advanced production planning and scheduling application for manufacturing operations.

## Features

- Sales Order to Production Plan conversion
- Multi-level BOM explosion
- Material requirement planning (MRP)
- Capacity planning and analysis
- Material shortage detection
- Work order generation
- Production tracking and reporting

## Installation

```bash
cd ~/frappe-bench
bench get-app production_planning_app /path/to/projects/production_planning/production_planning_app
bench --site your-site.local install-app production_planning_app
bench --site your-site.local migrate
```

## DocTypes

### Production Plan
Main DocType for planning production activities.

**Key Features:**
- Pull items from Sales Orders or Material Requests
- BOM explosion for raw material requirements
- Automatic work order creation
- Production tracking and completion percentage

**API Methods:**
- `get_sales_orders(from_date, to_date, company)`: Get pending sales orders
- `get_items_for_production_plan(sales_orders)`: Extract items from sales orders
- `explode_bom(production_plan)`: Calculate raw material requirements

## Usage

1. Create Production Plan from Sales Orders
2. Get raw materials using BOM explosion
3. Submit to create work orders
4. Track production progress

## License

MIT License
