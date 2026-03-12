# -*- coding: utf-8 -*-
"""
Vendor Portal REST API
Chapter 13: Vendor Portal - REST API Development
"""

import frappe
from frappe import _
from frappe.utils import today, getdate

@frappe.whitelist(allow_guest=True)
def authenticate(api_key, api_secret):
	"""Authenticate vendor using API credentials"""
	vendor = frappe.db.get_value('Vendor',
		{'api_key': api_key, 'api_secret': api_secret},
		['name', 'vendor_name', 'email'],
		as_dict=1
	)
	
	if not vendor:
		frappe.throw(_("Invalid API credentials"), frappe.AuthenticationError)
	
	# Generate session token
	token = frappe.generate_hash(length=32)
	
	# Store token in cache (expires in 24 hours)
	frappe.cache().setex(f"vendor_token:{token}", vendor.name, 86400)
	
	return {
		'success': True,
		'token': token,
		'vendor': vendor
	}

@frappe.whitelist()
def get_purchase_orders(vendor, status=None):
	"""Get purchase orders for vendor"""
	filters = {'supplier': vendor, 'docstatus': 1}
	
	if status:
		filters['status'] = status
	
	orders = frappe.get_all('Purchase Order',
		filters=filters,
		fields=['name', 'transaction_date', 'schedule_date', 'grand_total', 'status'],
		order_by='transaction_date desc'
	)
	
	return {
		'success': True,
		'data': orders
	}
