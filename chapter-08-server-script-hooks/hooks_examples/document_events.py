# -*- coding: utf-8 -*-
"""
Document Event Hooks Examples
Chapter 8: Server Script Hooks & Schedulers
"""

import frappe
from frappe import _

def validate_sales_order(doc, method):
	"""Validate sales order before saving"""
	# Check credit limit
	if doc.customer and doc.grand_total:
		check_customer_credit_limit(doc)
	
	# Validate delivery date
	if doc.delivery_date and doc.transaction_date:
		from frappe.utils import getdate
		if getdate(doc.delivery_date) < getdate(doc.transaction_date):
			frappe.throw(_("Delivery date cannot be before transaction date"))

def check_customer_credit_limit(doc):
	"""Check if customer has exceeded credit limit"""
	customer = frappe.get_doc('Customer', doc.customer)
	
	if customer.credit_limit and customer.credit_limit > 0:
		outstanding = get_customer_outstanding(doc.customer)
		
		if outstanding + doc.grand_total > customer.credit_limit:
			frappe.msgprint(
				_("Warning: This order will exceed customer's credit limit"),
				indicator='orange',
				alert=True
			)

def get_customer_outstanding(customer):
	"""Get customer outstanding amount"""
	outstanding = frappe.db.sql("""
		SELECT SUM(outstanding_amount)
		FROM `tabSales Invoice`
		WHERE customer = %s AND docstatus = 1
	""", customer)
	
	return outstanding[0][0] if outstanding and outstanding[0][0] else 0

def on_sales_order_submit(doc, method):
	"""Actions after sales order is submitted"""
	# Send notification to warehouse
	send_warehouse_notification(doc)
	
	# Update customer statistics
	update_customer_statistics(doc.customer)
	
	# Create activity log
	create_activity_log(doc)

def send_warehouse_notification(doc):
	"""Send notification to warehouse team"""
	warehouse_users = get_warehouse_users(doc.set_warehouse)
	
	if warehouse_users:
		frappe.sendmail(
			recipients=warehouse_users,
			subject=_('New Sales Order: {0}').format(doc.name),
			message=_('A new sales order has been created. Please prepare items for delivery.'),
			reference_doctype=doc.doctype,
			reference_name=doc.name
		)

def get_warehouse_users(warehouse):
	"""Get users assigned to warehouse"""
	if not warehouse:
		return []
	
	return frappe.get_all('Warehouse User',
		filters={'parent': warehouse},
		pluck='user'
	)

def update_customer_statistics(customer):
	"""Update customer order statistics"""
	stats = frappe.db.sql("""
		SELECT 
			COUNT(*) as order_count,
			SUM(grand_total) as total_value
		FROM `tabSales Order`
		WHERE customer = %s AND docstatus = 1
	""", customer, as_dict=True)
	
	if stats:
		frappe.db.set_value('Customer', customer, {
			'total_orders': stats[0].order_count,
			'total_order_value': stats[0].total_value
		}, update_modified=False)

def create_activity_log(doc):
	"""Create activity log entry"""
	activity = frappe.get_doc({
		'doctype': 'Activity Log',
		'subject': _('Sales Order {0} submitted').format(doc.name),
		'content': _('Sales Order for customer {0} with value {1}').format(
			doc.customer_name, doc.grand_total
		),
		'reference_doctype': doc.doctype,
		'reference_name': doc.name,
		'user': frappe.session.user
	})
	activity.insert(ignore_permissions=True)

def on_payment_entry_submit(doc, method):
	"""Actions after payment entry is submitted"""
	# Send payment confirmation
	if doc.party_type == 'Customer' and doc.party:
		send_payment_confirmation(doc)
	
	# Update payment statistics
	update_payment_statistics(doc)

def send_payment_confirmation(doc):
	"""Send payment confirmation email"""
	customer_email = frappe.db.get_value('Customer', doc.party, 'email_id')
	
	if customer_email:
		frappe.sendmail(
			recipients=[customer_email],
			subject=_('Payment Received - {0}').format(doc.name),
			message=_('We have received your payment of {0}. Thank you!').format(
				frappe.format_value(doc.paid_amount, {'fieldtype': 'Currency'})
			),
			reference_doctype=doc.doctype,
			reference_name=doc.name
		)

def update_payment_statistics(doc):
	"""Update payment statistics"""
	if doc.party_type == 'Customer':
		stats = frappe.db.sql("""
			SELECT 
				COUNT(*) as payment_count,
				SUM(paid_amount) as total_paid
			FROM `tabPayment Entry`
			WHERE party_type = 'Customer' 
			AND party = %s 
			AND docstatus = 1
		""", doc.party, as_dict=True)
		
		if stats:
			frappe.db.set_value('Customer', doc.party, {
				'total_payments': stats[0].payment_count,
				'total_paid_amount': stats[0].total_paid
			}, update_modified=False)
