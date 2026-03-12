# -*- coding: utf-8 -*-
"""Purchase Order API endpoints"""

import frappe
from frappe import _

@frappe.whitelist()
def get_purchase_order_details(purchase_order):
	"""Get detailed purchase order information"""
	doc = frappe.get_doc('Purchase Order', purchase_order)
	
	# Check vendor access
	vendor = get_current_vendor()
	if doc.supplier != vendor:
		frappe.throw(_("Access denied"), frappe.PermissionError)
	
	return {
		'success': True,
		'data': {
			'name': doc.name,
			'transaction_date': doc.transaction_date,
			'schedule_date': doc.schedule_date,
			'supplier': doc.supplier,
			'grand_total': doc.grand_total,
			'status': doc.status,
			'items': [{
				'item_code': item.item_code,
				'item_name': item.item_name,
				'qty': item.qty,
				'rate': item.rate,
				'amount': item.amount,
				'received_qty': item.received_qty
			} for item in doc.items]
		}
	}

@frappe.whitelist()
def acknowledge_purchase_order(purchase_order, acknowledgement_date, notes=None):
	"""Vendor acknowledges receipt of purchase order"""
	doc = frappe.get_doc('Purchase Order', purchase_order)
	
	# Check vendor access
	vendor = get_current_vendor()
	if doc.supplier != vendor:
		frappe.throw(_("Access denied"), frappe.PermissionError)
	
	# Add acknowledgement
	doc.add_comment('Comment', f"Acknowledged on {acknowledgement_date}. Notes: {notes or 'None'}")
	
	return {
		'success': True,
		'message': 'Purchase order acknowledged successfully'
	}

def get_current_vendor():
	"""Get current vendor from session token"""
	token = frappe.get_request_header('Authorization', '').replace('Bearer ', '')
	vendor = frappe.cache().get(f"vendor_token:{token}")
	
	if not vendor:
		frappe.throw(_("Invalid or expired token"), frappe.AuthenticationError)
	
	return vendor
