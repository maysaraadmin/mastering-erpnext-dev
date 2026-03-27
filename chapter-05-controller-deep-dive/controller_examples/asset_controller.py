# -*- coding: utf-8 -*-
"""
Asset Controller Example
Chapter 5: The Controller – Document Class Deep Dive

This example demonstrates a complete asset management controller
with all lifecycle hooks, validation, and business logic for ERPNext v16/Frappe v16.

Updated with comprehensive type hints and modern Frappe framework practices.
"""

from typing import List, Dict, Any, Optional, Union
import frappe
from frappe.model.document import Document
from frappe.utils import flt, cint, getdate, add_days, today
from frappe import _

class Asset(Document):
    """
    Asset Management Controller
    Demonstrates complete document lifecycle management for ERPNext v16.
    
    Version Compatibility Notes:
    - Document hooks: validate(), before_save(), on_submit(), after_submit(), etc.
    - frappe.throw(): Standard error handling in v16
    - frappe.db.exists(): Optimized for existence checks
    - frappe.cache(): Standard caching mechanisms
    - Type hints: Supported for better IDE integration
    
    Security Notes:
    - Always validate user permissions before operations
    - Use parameterized queries for database operations
    - Implement proper audit logging
    """
    
    def __init__(self, *args, **kwargs) -> None:
        """Initialize asset with custom properties"""
        super().__init__(*args, **kwargs)
        
        # Custom properties
        self._maintenance_history: List[Dict[str, Any]] = []
        self._deprecation_warnings: List[str] = []
        
        # Capture original status BEFORE any changes so validate() can use it.
        # Must be done in __init__ (not before_save) since validate() runs first
        # in the Frappe lifecycle: validate → before_save → save → on_update.
        if not self.is_new():
            self._original_status: Optional[str] = frappe.db.get_value(
                self.doctype, self.name, 'status'
            )
        else:
            self._original_status = None
        
        # Load additional data if not new
        if not self.is_new():
            self.load_asset_history()
    
    def load_asset_history(self) -> None:
        """Load asset maintenance and depreciation history"""
        if self.name:
            self._maintenance_history = frappe.get_all('Asset Maintenance History',
                filters={'asset': self.name},
                fields=['date', 'type', 'description', 'cost'],
                order_by='date desc'
            )
    
    def autoname(self) -> None:
        """Generate asset name automatically"""
        if not self.name:
            # Format: ASSET-<CATEGORY_CODE>-<SEQUENCE>
            category_code = frappe.db.get_value('Asset Category', self.asset_category, 'code') or 'GEN'
            sequence = frappe.db.get_value('Series', f'ASSET-{category_code}-', 'current') or 0
            
            sequence += 1
            self.name = f"ASSET-{category_code}-{sequence:06d}"
            
            # Update series
            frappe.db.set_value('Series', f'ASSET-{category_code}-', 'current', sequence)
    
    def validate(self) -> None:
        """Main validation hook"""
        self.validate_required_fields()
        self.validate_asset_category()
        self.validate_purchase_details()
        self.validate_deprecation_settings()
        self.validate_location_and_status()
        self.validate_financial_data()
    
    def validate_required_fields(self) -> None:
        """Validate required fields"""
        required_fields: List[str] = ['asset_category', 'item_code', 'asset_name']
        
        for field in required_fields:
            if not self.get(field):
                frappe.throw(_(f"{field.replace('_', ' ').title()} is required"))
    
    def validate_asset_category(self) -> None:
        """Validate asset category and set defaults"""
        if self.asset_category:
            category = frappe.get_doc('Asset Category', self.asset_category)
            
            # Set default depreciation method if not set
            if not self.depreciation_method:
                self.depreciation_method = category.depreciation_method
            
            # Set default useful life if not set
            if not self.useful_life:
                self.useful_life = category.useful_life
            
            # Validate category is active
            if category.status != 'Active':
                frappe.throw(_("Asset Category must be active"))
    
    def validate_purchase_details(self) -> None:
        """Validate purchase information"""
        if self.purchase_date:
            if getdate(self.purchase_date) > getdate(today()):
                frappe.throw(_("Purchase date cannot be in the future"))
        
        if self.purchase_amount and self.purchase_amount <= 0:
            frappe.throw(_("Purchase amount must be greater than zero"))
        
        # Validate purchase date vs commissioning date
        if self.commissioning_date and self.purchase_date:
            if getdate(self.commissioning_date) < getdate(self.purchase_date):
                frappe.throw(_("Commissioning date cannot be before purchase date"))
    
    def validate_deprecation_settings(self) -> None:
        """Validate depreciation settings"""
        if self.depreciation_method == 'Straight Line':
            if not self.useful_life or self.useful_life <= 0:
                frappe.throw(_("Useful life is required for Straight Line depreciation"))
        
        elif self.depreciation_method == 'Written Down Value':
            if not self.depreciation_rate or self.depreciation_rate <= 0:
                frappe.throw(_("Depreciation rate is required for Written Down Value depreciation"))
        
        # Validate salvage value
        if self.salvage_value and self.purchase_amount:
            if self.salvage_value >= self.purchase_amount:
                frappe.throw(_("Salvage value cannot be greater than or equal to purchase amount"))
    
    def validate_location_and_status(self) -> None:
        """Validate asset location and status"""
        if self.location:
            # Validate location exists
            if not frappe.db.exists('Location', self.location):
                frappe.throw(_("Location {0} does not exist").format(self.location))
        
        # Status transition validation
        if self._original_status and self._original_status != self.status:
            self.validate_status_transition()
    
    def validate_status_transition(self) -> None:
        """Validate asset status transitions"""
        valid_transitions: Dict[str, List[str]] = {
            'In Stock': ['In Use', 'Under Maintenance', 'Scrapped'],
            'In Use': ['Under Maintenance', 'In Stock', 'Scrapped'],
            'Under Maintenance': ['In Use', 'In Stock', 'Scrapped'],
            'Scrapped': []  # Terminal state
        }
        
        if self.status not in valid_transitions.get(self._original_status, []):
            frappe.throw(_("Cannot transition from {0} to {1}").format(
                self._original_status, self.status
            ))
    
    def validate_financial_data(self) -> None:
        """Validate financial calculations"""
        if self.purchase_amount:
            # Calculate current value
            self.calculate_current_value()
            
            # Validate current value is not negative
            if self.current_value < 0:
                frappe.throw(_("Current value cannot be negative"))
    
    def before_save(self) -> None:
        """Called before saving the document"""
        # Note: _original_status is captured in __init__ so validate() can use it.
        # Do NOT re-assign it here — before_save runs after validate().
        
        # Calculate derived fields
        self.calculate_depreciation()
        self.calculate_current_value()
        
        # Set defaults
        self.set_default_values()
        
        # Format data
        self.format_data()
    
    def before_insert(self) -> None:
        """Called before inserting new document"""
        # Set initial values
        if not self.purchase_date:
            self.purchase_date = today()
        
        if not self.status:
            self.status = 'In Stock'
        
        # Initialize depreciation
        self.accumulated_depreciation = 0
        self.current_value = self.purchase_amount or 0
        
        # Generate asset ID
        self.asset_id = self.generate_asset_id()
    
    def calculate_depreciation(self) -> None:
        """Calculate depreciation based on method"""
        if not self.purchase_amount or not self.purchase_date:
            return
        
        if self.depreciation_method == 'Straight Line':
            self.calculate_straight_line_depreciation()
        elif self.depreciation_method == 'Written Down Value':
            self.calculate_wdv_depreciation()
    
    def calculate_straight_line_depreciation(self) -> None:
        """Calculate straight line depreciation"""
        if not self.useful_life:
            return
        
        # Annual depreciation
        annual_depreciation = (self.purchase_amount - (self.salvage_value or 0)) / self.useful_life
        
        # Calculate days since purchase
        days_since_purchase = (getdate(today()) - getdate(self.purchase_date)).days
        
        # Calculate accumulated depreciation
        self.accumulated_depreciation = min(
            (annual_depreciation * days_since_purchase) / 365,
            self.purchase_amount - (self.salvage_value or 0)
        )
    
    def calculate_wdv_depreciation(self) -> None:
        """Calculate written down value depreciation"""
        if not self.depreciation_rate:
            return
        
        # Calculate years since purchase
        years_since_purchase = (getdate(today()) - getdate(self.purchase_date)).days / 365.25
        
        # WDV formula: Value = Purchase Amount * (1 - Rate/100)^Years
        current_value = self.purchase_amount * ((1 - self.depreciation_rate/100) ** years_since_purchase)
        
        self.accumulated_depreciation = self.purchase_amount - current_value
        
        # Ensure depreciation doesn't exceed purchase amount minus salvage value
        max_depreciation = self.purchase_amount - (self.salvage_value or 0)
        self.accumulated_depreciation = min(self.accumulated_depreciation, max_depreciation)
    
    def calculate_current_value(self) -> None:
        """Calculate current asset value"""
        if self.purchase_amount:
            self.current_value = self.purchase_amount - (self.accumulated_depreciation or 0)
            
            # Ensure current value doesn't go below salvage value
            if self.salvage_value and self.current_value < self.salvage_value:
                self.current_value = self.salvage_value
    
    def set_default_values(self) -> None:
        """Set default values"""
        if not self.asset_name and self.item_code:
            self.asset_name = frappe.db.get_value('Item', self.item_code, 'item_name')
    
    def format_data(self) -> None:
        """Format data for consistency"""
        if self.asset_name:
            self.asset_name = self.asset_name.strip().title()
    
    def on_update(self) -> None:
        """Called after document is saved"""
        # Update asset statistics
        self.update_asset_statistics()
        
        # Send notifications for status changes
        if self._original_status and self._original_status != self.status:
            self.send_status_change_notification()
        
        # Log asset activity
        self.log_asset_activity()
    
    def on_submit(self) -> None:
        """Called after document is submitted"""
        # Create asset register entry
        self.create_asset_register_entry()
        
        # Update inventory if applicable
        self.update_inventory()
        
        # Schedule maintenance if required
        self.schedule_maintenance()
        
        # Send confirmation
        self.send_submission_confirmation()
    
    def on_cancel(self) -> None:
        """Called after document is cancelled"""
        # Reverse asset register entry
        self.reverse_asset_register_entry()
        
        # Cancel scheduled maintenance
        self.cancel_scheduled_maintenance()
        
        # Send cancellation notification
        self.send_cancellation_notification()
    
    def before_trash(self) -> None:
        """Called before deleting the document"""
        # Check if asset can be deleted
        if self.status == 'In Use':
            frappe.throw(_("Cannot delete asset that is currently in use"))
        
        # Check for related documents
        if self.has_related_transactions():
            frappe.throw(_("Cannot delete asset with related transactions"))
    
    def on_trash(self) -> None:
        """Called after deleting the document"""
        # Clean up related data
        self.cleanup_related_data()
    
    def generate_asset_id(self) -> str:
        """Generate unique asset ID"""
        import uuid
        return str(uuid.uuid4())[:8].upper()
    
    def update_asset_statistics(self) -> None:
        """Update asset statistics"""
        # Update category statistics
        frappe.db.sql("""
            UPDATE `tabAsset Category`
            SET total_assets = (
                SELECT COUNT(*) FROM `tabAsset` 
                WHERE asset_category = %(category)s AND docstatus != 2
            ),
            total_value = (
                SELECT COALESCE(SUM(current_value), 0) FROM `tabAsset` 
                WHERE asset_category = %(category)s AND docstatus != 2
            )
            WHERE name = %(category)s
        """, {
            'category': self.asset_category
        })
    
    def send_status_change_notification(self) -> None:
        """Send notification for status change"""
        recipients = self.get_notification_recipients()
        
        if recipients:
            frappe.sendmail(
                recipients=recipients,
                subject=_('Asset Status Changed'),
                template='asset_status_change',
                args={
                    'asset': self.name,
                    'asset_name': self.asset_name,
                    'old_status': self._original_status,
                    'new_status': self.status,
                    'changed_by': frappe.session.user
                }
            )
    
    def get_notification_recipients(self) -> List[str]:
        """Get list of notification recipients"""
        recipients: List[str] = []
        
        # Add asset manager
        if self.asset_manager:
            recipients.append(self.asset_manager)
        
        # Add location manager
        if self.location:
            location_manager = frappe.db.get_value('Location', self.location, 'manager')
            if location_manager:
                recipients.append(location_manager)
        
        # Remove duplicates
        return list(set(recipients))
    
    def log_asset_activity(self) -> None:
        """Log asset activity using Frappe's built-in logger.
        
        NOTE: 'Asset Activity Log' is not a standard Frappe DocType.
        If you need a persistent audit trail, define this DocType in your app
        or use frappe.log_error() / a custom DocType. For now we use the logger.
        """
        activity_type = 'Status Change' if self._original_status != self.status else 'Update'
        description = (
            f"Asset {self.name} status changed from "
            f"{self._original_status or 'New'} to {self.status}"
        )
        frappe.logger("asset").info(f"[{activity_type}] {description} by {frappe.session.user}")
    
    def create_asset_register_entry(self) -> None:
        """Create entry in asset register"""
        register = frappe.get_doc({
            'doctype': 'Asset Register',
            'asset': self.name,
            'transaction_date': self.commissioning_date or self.purchase_date,
            'transaction_type': 'Commissioning',
            'value': self.current_value,
            'status': self.status
        })
        register.insert()
    
    def reverse_asset_register_entry(self) -> None:
        """Reverse asset register entry"""
        frappe.db.sql("""
            UPDATE `tabAsset Register`
            SET status = 'Cancelled'
            WHERE asset = %(asset)s AND status != 'Cancelled'
        """, {'asset': self.name})
    
    def update_inventory(self) -> None:
        """Update inventory if asset is linked to item"""
        if self.item_code:
            # Update item status
            frappe.db.set_value('Item', self.item_code, 'asset_status', self.status)
    
    def schedule_maintenance(self) -> None:
        """Schedule maintenance if required"""
        if self.maintenance_frequency and self.commissioning_date:
            next_maintenance_date = add_days(self.commissioning_date, self.maintenance_frequency)
            
            if next_maintenance_date <= today():
                # Create maintenance schedule
                maintenance = frappe.get_doc({
                    'doctype': 'Asset Maintenance Schedule',
                    'asset': self.name,
                    'scheduled_date': next_maintenance_date,
                    'maintenance_type': 'Regular Maintenance'
                })
                maintenance.insert()
    
    def cancel_scheduled_maintenance(self) -> None:
        """Cancel scheduled maintenance"""
        frappe.db.sql("""
            UPDATE `tabAsset Maintenance Schedule`
            SET status = 'Cancelled'
            WHERE asset = %(asset)s AND status = 'Scheduled'
        """, {'asset': self.name})
    
    def send_submission_confirmation(self) -> None:
        """Send submission confirmation"""
        recipients = self.get_notification_recipients()
        
        if recipients:
            frappe.sendmail(
                recipients=recipients,
                subject=_('Asset Submitted Successfully'),
                template='asset_submission',
                args={
                    'asset': self.name,
                    'asset_name': self.asset_name,
                    'status': self.status,
                    'current_value': self.current_value
                }
            )
    
    def send_cancellation_notification(self) -> None:
        """Send cancellation notification"""
        recipients = self.get_notification_recipients()
        
        if recipients:
            frappe.sendmail(
                recipients=recipients,
                subject=_('Asset Cancelled'),
                template='asset_cancellation',
                args={
                    'asset': self.name,
                    'asset_name': self.asset_name,
                    'cancelled_by': frappe.session.user
                }
            )
    
    def has_related_transactions(self) -> bool:
        """Check if asset has related transactions"""
        related_doctypes: List[str] = ['Asset Maintenance', 'Asset Transfer', 'Asset Valuation']
        
        for doctype in related_doctypes:
            if frappe.db.exists(doctype, {'asset': self.name, 'docstatus': ['!=', 2]}):
                return True
        
        return False
    
    def cleanup_related_data(self) -> None:
        """Clean up related data when asset is deleted"""
        # NOTE: 'Asset Activity Log' is not a standard DocType — activity is
        # logged via frappe.logger() in log_asset_activity(). If your app
        # defines a custom 'Asset Activity Log' DocType, uncomment the line below.
        # frappe.db.delete('Asset Activity Log', {'asset': self.name})
        
        # Delete maintenance schedules
        frappe.db.delete('Asset Maintenance Schedule', {'asset': self.name})
        
        # Delete register entries
        frappe.db.delete('Asset Register', {'asset': self.name})
