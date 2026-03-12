# -*- coding: utf-8 -*-
"""Daily tasks for vendor portal"""

import frappe

def sync_vendor_data():
	"""Sync vendor data with external systems"""
	vendors = frappe.get_all('Vendor',
		filters={'sync_enabled': 1},
		fields=['name', 'api_endpoint']
	)
	
	for vendor in vendors:
		try:
			# Sync logic here
			frappe.logger().info(f"Syncing data for vendor {vendor.name}")
		except Exception as e:
			frappe.logger().error(f"Sync failed for {vendor.name}: {str(e)}")
