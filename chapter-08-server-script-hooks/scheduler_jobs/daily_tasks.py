# -*- coding: utf-8 -*-
"""
Daily Scheduled Tasks
Chapter 8: Server Script Hooks & Schedulers
"""

import frappe
from frappe.utils import today, add_days, getdate
from frappe import _

def send_payment_reminders():
	"""Send payment reminders for overdue invoices"""
	overdue_invoices = frappe.get_all('Sales Invoice',
		filters={
			'docstatus': 1,
			'status': 'Overdue',
			'outstanding_amount': ['>', 0]
		},
		fields=['name', 'customer', 'customer_name', 'due_date', 'outstanding_amount']
	)
	
	for invoice in overdue_invoices:
		days_overdue = (getdate(today()) - getdate(invoice.due_date)).days
		
		# Send reminder based on overdue days
		if days_overdue in [1, 7, 14, 30]:
			send_payment_reminder_email(invoice, days_overdue)

def send_payment_reminder_email(invoice, days_overdue):
	"""Send payment reminder email"""
	customer_email = frappe.db.get_value('Customer', invoice.customer, 'email_id')
	
	if customer_email:
		frappe.sendmail(
			recipients=[customer_email],
			subject=_('Payment Reminder: Invoice {0}').format(invoice.name),
			template='payment_reminder',
			args={
				'invoice': invoice.name,
				'customer_name': invoice.customer_name,
				'due_date': invoice.due_date,
				'outstanding_amount': invoice.outstanding_amount,
				'days_overdue': days_overdue
			},
			reference_doctype='Sales Invoice',
			reference_name=invoice.name
		)

def check_low_stock_items():
	"""Check for low stock items and send alerts"""
	low_stock_items = frappe.db.sql("""
		SELECT 
			item.name,
			item.item_name,
			bin.actual_qty,
			item.reorder_level,
			bin.warehouse
		FROM `tabItem` item
		JOIN `tabBin` bin ON item.name = bin.item_code
		WHERE bin.actual_qty <= item.reorder_level
		AND item.is_stock_item = 1
		AND item.disabled = 0
	""", as_dict=True)
	
	if low_stock_items:
		send_low_stock_alert(low_stock_items)

def send_low_stock_alert(items):
	"""Send low stock alert to inventory managers"""
	inventory_managers = frappe.get_all('User',
		filters={'role': 'Stock Manager', 'enabled': 1},
		pluck='email'
	)
	
	if inventory_managers:
		frappe.sendmail(
			recipients=inventory_managers,
			subject=_('Low Stock Alert: {0} items').format(len(items)),
			template='low_stock_alert',
			args={'items': items}
		)

def update_asset_depreciation():
	"""Update depreciation for all assets"""
	assets = frappe.get_all('Asset',
		filters={
			'docstatus': 1,
			'status': ['!=', 'Scrapped'],
			'depreciation_method': ['!=', '']
		},
		fields=['name']
	)
	
	for asset in assets:
		try:
			asset_doc = frappe.get_doc('Asset', asset.name)
			asset_doc.calculate_depreciation()
			asset_doc.save()
		except Exception as e:
			frappe.log_error(f"Failed to update depreciation for {asset.name}: {str(e)}")

def cleanup_old_logs():
	"""Clean up old log entries"""
	# Delete error logs older than 90 days
	old_date = add_days(today(), -90)
	
	frappe.db.delete('Error Log', {
		'creation': ['<', old_date]
	})
	
	# Delete activity logs older than 180 days
	old_date = add_days(today(), -180)
	
	frappe.db.delete('Activity Log', {
		'creation': ['<', old_date]
	})
	
	frappe.db.commit()
