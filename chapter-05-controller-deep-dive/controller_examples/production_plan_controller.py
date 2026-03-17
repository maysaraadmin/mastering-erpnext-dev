# -*- coding: utf-8 -*-
"""
Production Plan Controller Example
Chapter 5: The Controller – Document Class Deep Dive

This example demonstrates a production planning controller
with complex business logic and cross-document operations.
"""

from typing import List, Dict, Any, Optional, Union
import frappe
from frappe.model.document import Document
from frappe.utils import flt, cint, getdate, add_days, today, nowdate
from frappe import _

class ProductionPlan(Document):
    """
    Production Plan Controller
    Demonstrates complex business logic and cross-document operations
    """
    
    def __init__(self, *args, **kwargs) -> None:
        """Initialize production plan with custom properties"""
        super().__init__(*args, **kwargs)
        
        # Custom properties
        self._original_status: Optional[str] = None
        self._material_requirements: List[Dict[str, Any]] = []
        self._capacity_conflicts: List[Dict[str, Any]] = []
        self._bom_explosion: Dict[str, Any] = {}
        self._workstation_load: List[Dict[str, Any]] = []
        
        # Load additional data if not new
        if not self.is_new():
            self.load_production_data()
    
    def load_production_data(self) -> None:
        """Load production-related data"""
        if self.name:
            # Load material requirements
            self._material_requirements = frappe.get_all('Production Plan Material',
                filters={'parent': self.name},
                fields=['item_code', 'required_qty', 'available_qty', 'shortage_qty'],
                order_by='item_code'
            )
            
            # Load workstation load
            self.load_workstation_load()
    
    def load_workstation_load(self) -> None:
        """Load current workstation load"""
        if self.planning_start_date and self.planning_end_date:
            self._workstation_load = frappe.db.sql("""
                SELECT 
                    w.workstation,
                    COALESCE(SUM(op.allocated_time), 0) as total_load
                FROM `tabWorkstation` w
                LEFT JOIN `tabProduction Plan Operation` op ON w.name = op.workstation
                LEFT JOIN `tabProduction Plan` pp ON op.parent = pp.name
                WHERE pp.planning_start_date <= %(end_date)s 
                AND pp.planning_end_date >= %(start_date)s
                AND pp.docstatus = 1
                AND pp.name != %(plan_name)s
                GROUP BY w.workstation
            """, {
                'start_date': self.planning_start_date,
                'end_date': self.planning_end_date,
                'plan_name': self.name
            }, as_dict=True)
    
    def validate(self) -> None:
        """Main validation hook"""
        self.validate_required_fields()
        self.validate_planning_dates()
        self.validate_sales_orders()
        self.validate_production_items()
        self.validate_capacity_constraints()
        self.validate_material_availability()
        self.validate_bom_availability()
    
    def validate_required_fields(self) -> None:
        """Validate required fields"""
        required_fields: List[str] = ['planning_start_date', 'planning_end_date']
        
        for field in required_fields:
            if not self.get(field):
                frappe.throw(_(f"{field.replace('_', ' ').title()} is required"))
    
    def validate_planning_dates(self) -> None:
        """Validate planning date range"""
        if self.planning_start_date and self.planning_end_date:
            if getdate(self.planning_start_date) >= getdate(self.planning_end_date):
                frappe.throw(_("Planning start date must be before end date"))
            
            if getdate(self.planning_start_date) < getdate(today()):
                frappe.throw(_("Planning start date cannot be in the past"))
            
            # Validate planning period (max 90 days)
            planning_days = (getdate(self.planning_end_date) - getdate(self.planning_start_date)).days
            if planning_days > 90:
                frappe.throw(_("Planning period cannot exceed 90 days"))
    
    def validate_sales_orders(self) -> None:
        """Validate linked sales orders"""
        if self.get('sales_orders'):
            for so in self.sales_orders:
                # Check if sales order exists and is submitted
                if not frappe.db.exists('Sales Order', so.sales_order):
                    frappe.throw(_("Sales Order {0} does not exist").format(so.sales_order))
                
                so_status = frappe.db.get_value('Sales Order', so.sales_order, 'docstatus')
                if so_status != 1:
                    frappe.throw(_("Sales Order {0} must be submitted").format(so.sales_order))
                
                # Check if sales order is already linked to another production plan
                existing_plan = frappe.db.exists('Production Plan Sales Order', {
                    'sales_order': so.sales_order,
                    'parent': ['!=', self.name],
                    'parenttype': 'Production Plan'
                })
                
                if existing_plan:
                    frappe.throw(_("Sales Order {0} is already linked to another production plan").format(so.sales_order))
    
    def validate_production_items(self) -> None:
        """Validate production items"""
        if not self.get('production_items'):
            frappe.throw(_("At least one production item is required"))
        
        for item in self.production_items:
            # Validate item exists and is manufactured
            if not frappe.db.exists('Item', item.item_code):
                frappe.throw(_("Item {0} does not exist").format(item.item_code))
            
            is_manufactured = frappe.db.get_value('Item', item.item_code, 'is_manufactured_item')
            if not is_manufactured:
                frappe.throw(_("Item {0} is not a manufactured item").format(item.item_code))
            
            # Validate quantity
            if item.qty <= 0:
                frappe.throw(_("Quantity must be greater than zero for item {0}").format(item.item_code))
            
            # Validate BOM exists
            bom_exists = frappe.db.exists('BOM', {
                'item': item.item_code,
                'is_active': 1,
                'is_default': 1
            })
            
            if not bom_exists:
                frappe.throw(_("No active default BOM found for item {0}").format(item.item_code))
    
    def validate_capacity_constraints(self) -> None:
        """Validate production capacity constraints"""
        if not self.get('production_operations'):
            return
        
        # Check workstation availability
        for operation in self.production_operations:
            if operation.workstation:
                # Get workstation capacity
                workstation_capacity = frappe.db.get_value('Workstation', operation.workstation, 'capacity')
                
                if workstation_capacity:
                    # Calculate current load
                    current_load = self.get_workstation_load(operation.workstation)
                    proposed_load = operation.estimated_time or 0
                    
                    if current_load + proposed_load > workstation_capacity:
                        self._capacity_conflicts.append({
                            'workstation': operation.workstation,
                            'current_load': current_load,
                            'proposed_load': proposed_load,
                            'capacity': workstation_capacity
                        })
        
        # Report capacity conflicts
        if self._capacity_conflicts:
            conflict_details = "\n".join([
                f"• {conflict['workstation']}: Current load {conflict['current_load']}h + Proposed {conflict['proposed_load']}h > Capacity {conflict['capacity']}h"
                for conflict in self._capacity_conflicts
            ])
            frappe.throw(_("Capacity constraints violated:\n{0}").format(conflict_details))
    
    def validate_material_availability(self) -> None:
        """Validate material availability"""
        self.calculate_material_requirements()
        
        for req in self._material_requirements:
            if req.shortage_qty > 0:
                frappe.msgprint(_("Warning: Material shortage for {0}: {1} units").format(
                    req.item_code, req.shortage_qty
                ))
    
    def validate_bom_availability(self) -> None:
        """Validate BOM availability for all items"""
        for item in self.production_items:
            bom = frappe.db.get_value('BOM', {
                'item': item.item_code,
                'is_active': 1,
                'is_default': 1
            })
            
            if bom:
                # Check BOM validity dates
                bom_doc = frappe.get_doc('BOM', bom)
                if bom_doc.from_date and getdate(self.planning_start_date) < getdate(bom_doc.from_date):
                    frappe.throw(_("BOM {0} is not valid from {1}").format(bom, bom_doc.from_date))
                
                if bom_doc.to_date and getdate(self.planning_end_date) > getdate(bom_doc.to_date):
                    frappe.throw(_("BOM {0} is not valid after {1}").format(bom, bom_doc.to_date))
    
    def get_workstation_load(self, workstation: str) -> float:
        """Get current workstation load"""
        for load in self._workstation_load:
            if load.workstation == workstation:
                return load.total_load
        return 0
    
    def before_save(self) -> None:
        """Called before saving the document"""
        self._original_status = self.get_db_value('status') if not self.is_new() else None
        
        # Calculate derived fields
        self.calculate_production_schedule()
        self.calculate_material_requirements()
        self.calculate_operation_times()
        
        # Set defaults
        self.set_default_values()
        
        # Clear conflicts and regenerate
        self._capacity_conflicts = []
    
    def before_insert(self) -> None:
        """Called before inserting new document"""
        # Set initial values
        if not self.status:
            self.status = 'Draft'
        
        if not self.planning_start_date:
            self.planning_start_date = today()
        
        # Generate plan number
        self.plan_number = self.generate_plan_number()
    
    def calculate_production_schedule(self) -> None:
        """Calculate production schedule"""
        if not self.production_items or not self.planning_start_date:
            return
        
        current_date = getdate(self.planning_start_date)
        
        for item in self.production_items:
            # Calculate production start date based on priority and lead time
            lead_time = frappe.db.get_value('BOM', {
                'item': item.item_code,
                'is_default': 1
            }, 'total_lead_time_days') or 7
            
            item.planned_start_date = current_date
            item.planned_end_date = add_days(current_date, lead_time)
            
            # Move to next item
            current_date = add_days(item.planned_end_date, 1)
    
    def calculate_material_requirements(self) -> None:
        """Calculate material requirements through BOM explosion"""
        self._material_requirements = []
        material_dict: Dict[str, float] = {}
        
        for item in self.production_items:
            # Get BOM
            bom = frappe.db.get_value('BOM', {
                'item': item.item_code,
                'is_default': 1
            })
            
            if bom:
                # Explode BOM
                bom_items = frappe.get_all('BOM Item',
                    filters={'parent': bom},
                    fields=['item_code', 'qty', 'stock_uom']
                )
                
                for bom_item in bom_items:
                    required_qty = bom_item.qty * item.qty
                    
                    if bom_item.item_code in material_dict:
                        material_dict[bom_item.item_code] += required_qty
                    else:
                        material_dict[bom_item.item_code] = required_qty
        
        # Calculate availability and shortage
        for item_code, required_qty in material_dict.items():
            # Get available qty (projected)
            available_qty = self.get_projected_availability(item_code)
            
            material_dict[item_code] = {
                'item_code': item_code,
                'required_qty': required_qty,
                'available_qty': available_qty,
                'shortage_qty': max(0, required_qty - available_qty)
            }
        
        self._material_requirements = list(material_dict.values())
    
    def get_projected_availability(self, item_code: str) -> float:
        """Get projected availability for an item"""
        # Current stock
        current_stock = frappe.db.get_value('Bin', {'item_code': item_code}, 'actual_qty') or 0
        
        # Planned receipts (purchase orders, production orders)
        planned_receipts = frappe.db.sql("""
            SELECT COALESCE(SUM(qty), 0)
            FROM `tabPurchase Order Item` poi
            JOIN `tabPurchase Order` po ON poi.parent = po.name
            WHERE poi.item_code = %(item_code)s
            AND po.status = 'Submitted'
            AND po.docstatus = 1
            AND po.expected_delivery_date <= %(end_date)s
        """, {
            'item_code': item_code,
            'end_date': self.planning_end_date
        })[0][0] or 0
        
        return current_stock + planned_receipts
    
    def calculate_operation_times(self) -> None:
        """Calculate operation times based on BOM operations"""
        if not self.production_operations:
            return
        
        for operation in self.production_operations:
            if operation.item_code and operation.operation:
                # Get operation time from BOM
                operation_time = frappe.db.get_value('BOM Operation', {
                    'parent': f"BOM-{operation.item_code}",
                    'operation': operation.operation
                }, 'time_in_mins')
                
                if operation_time:
                    operation.estimated_time = operation_time / 60  # Convert to hours
    
    def set_default_values(self) -> None:
        """Set default values"""
        if not self.fiscal_year:
            self.fiscal_year = frappe.db.get_default('fiscal_year')
    
    def on_update(self) -> None:
        """Called after document is saved"""
        # Update material requirements table
        self.update_material_requirements_table()
        
        # Send notifications for status changes
        if self._original_status and self._original_status != self.status:
            self.send_status_change_notification()
        
        # Log production plan activity
        self.log_production_activity()
    
    def on_submit(self) -> None:
        """Called after document is submitted"""
        # Create production orders
        self.create_production_orders()
        
        # Create material requests for shortages
        self.create_material_requests()
        
        # Update capacity planning
        self.update_capacity_planning()
        
        # Send submission confirmation
        self.send_submission_confirmation()
    
    def on_cancel(self) -> None:
        """Called after document is cancelled"""
        # Cancel production orders
        self.cancel_production_orders()
        
        # Cancel material requests
        self.cancel_material_requests()
        
        # Update capacity planning
        self.reverse_capacity_planning()
        
        # Send cancellation notification
        self.send_cancellation_notification()
    
    def generate_plan_number(self) -> str:
        """Generate unique production plan number"""
        # Format: PP-YYYYMMDD-SEQ
        date_str = nowdate().replace('-', '')
        sequence = frappe.db.get_value('Series', f'PP-{date_str}-', 'current') or 0
        sequence += 1
        
        frappe.db.set_value('Series', f'PP-{date_str}-', 'current', sequence)
        return f"PP-{date_str}-{sequence:04d}"
    
    def update_material_requirements_table(self) -> None:
        """Update material requirements child table"""
        # Clear existing requirements
        self.set('production_materials', [])
        
        # Add new requirements
        for req in self._material_requirements:
            self.append('production_materials', {
                'item_code': req['item_code'],
                'required_qty': req['required_qty'],
                'available_qty': req['available_qty'],
                'shortage_qty': req['shortage_qty']
            })
    
    def send_status_change_notification(self) -> None:
        """Send notification for status change"""
        recipients = self.get_notification_recipients()
        
        if recipients:
            frappe.sendmail(
                recipients=recipients,
                subject=_('Production Plan Status Changed'),
                template='production_plan_status_change',
                args={
                    'plan': self.name,
                    'plan_number': self.plan_number,
                    'old_status': self._original_status,
                    'new_status': self.status,
                    'changed_by': frappe.session.user
                }
            )
    
    def get_notification_recipients(self) -> List[str]:
        """Get list of notification recipients"""
        recipients: List[str] = []
        
        # Add production manager
        if self.production_manager:
            recipients.append(self.production_manager)
        
        # Add production supervisor
        if self.production_supervisor:
            recipients.append(self.production_supervisor)
        
        # Remove duplicates
        return list(set(recipients))
    
    def log_production_activity(self) -> None:
        """Log production plan activity"""
        activity_log = frappe.get_doc({
            'doctype': 'Production Plan Activity Log',
            'production_plan': self.name,
            'activity_type': 'Status Change' if self._original_status != self.status else 'Update',
            'description': f"Production plan status changed from {self._original_status or 'New'} to {self.status}",
            'user': frappe.session.user
        })
        activity_log.insert(ignore_permissions=True)
    
    def create_production_orders(self) -> None:
        """Create production orders based on plan"""
        for item in self.production_items:
            production_order = frappe.get_doc({
                'doctype': 'Production Order',
                'production_item': item.item_code,
                'qty': item.qty,
                'planned_start_date': item.planned_start_date,
                'planned_end_date': item.planned_end_date,
                'production_plan': self.name,
                'sales_order': self.get_linked_sales_order(item.item_code)
            })
            
            production_order.insert()
            production_order.submit()
            
            # Link back to production plan
            item.production_order = production_order.name
    
    def get_linked_sales_order(self, item_code: str) -> Optional[str]:
        """Get linked sales order for an item"""
        for so in self.get('sales_orders', []):
            # Check if item is in sales order
            so_item = frappe.db.exists('Sales Order Item', {
                'parent': so.sales_order,
                'item_code': item_code
            })
            
            if so_item:
                return so.sales_order
        
        return None
    
    def create_material_requests(self) -> None:
        """Create material requests for shortages"""
        for req in self._material_requirements:
            if req['shortage_qty'] > 0:
                material_request = frappe.get_doc({
                    'doctype': 'Material Request',
                    'material_request_type': 'Purchase',
                    'schedule_date': self.planning_start_date,
                    'production_plan': self.name
                })
                
                material_request.append('items', {
                    'item_code': req['item_code'],
                    'qty': req['shortage_qty'],
                    'schedule_date': self.planning_start_date
                })
                
                material_request.insert()
                material_request.submit()
    
    def update_capacity_planning(self) -> None:
        """Update capacity planning with this plan's operations"""
        for operation in self.production_operations:
            if operation.workstation and operation.estimated_time:
                # Update workstation load
                frappe.db.sql("""
                    INSERT INTO `tabWorkstation Load` 
                    (workstation, date, load_hours, production_plan, operation)
                    VALUES (%(workstation)s, %(date)s, %(load_hours)s, %(plan)s, %(operation)s)
                    ON DUPLICATE KEY UPDATE 
                    load_hours = load_hours + VALUES(load_hours)
                """, {
                    'workstation': operation.workstation,
                    'date': self.planning_start_date,
                    'load_hours': operation.estimated_time,
                    'plan': self.name,
                    'operation': operation.operation
                })
    
    def send_submission_confirmation(self) -> None:
        """Send submission confirmation"""
        recipients = self.get_notification_recipients()
        
        if recipients:
            frappe.sendmail(
                recipients=recipients,
                subject=_('Production Plan Submitted Successfully'),
                template='production_plan_submission',
                args={
                    'plan': self.name,
                    'plan_number': self.plan_number,
                    'start_date': self.planning_start_date,
                    'end_date': self.planning_end_date,
                    'total_items': len(self.production_items)
                }
            )
    
    def cancel_production_orders(self) -> None:
        """Cancel created production orders"""
        for item in self.production_items:
            if item.production_order:
                production_order = frappe.get_doc('Production Order', item.production_order)
                if production_order.docstatus == 1:
                    production_order.cancel()
    
    def cancel_material_requests(self) -> None:
        """Cancel created material requests"""
        material_requests = frappe.get_all('Material Request',
            filters={'production_plan': self.name, 'docstatus': 1},
            pluck='name'
        )
        
        for mr_name in material_requests:
            mr = frappe.get_doc('Material Request', mr_name)
            mr.cancel()
    
    def reverse_capacity_planning(self) -> None:
        """Reverse capacity planning updates"""
        frappe.db.sql("""
            DELETE FROM `tabWorkstation Load`
            WHERE production_plan = %(plan)s
        """, {'plan': self.name})
    
    def send_cancellation_notification(self) -> None:
        """Send cancellation notification"""
        recipients = self.get_notification_recipients()
        
        if recipients:
            frappe.sendmail(
                recipients=recipients,
                subject=_('Production Plan Cancelled'),
                template='production_plan_cancellation',
                args={
                    'plan': self.name,
                    'plan_number': self.plan_number,
                    'cancelled_by': frappe.session.user
                }
            )
