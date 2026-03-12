# -*- coding: utf-8 -*-
"""Webhook handlers for Purchase Order events"""

import frappe
import requests
from frappe.utils import get_url

def notify_vendor(doc, method):
	"""Send webhook notification to vendor when PO is submitted"""
	vendor = frappe.get_doc('Vendor', doc.supplier)
	
	if vendor.webhook_url:
		payload = {
			'event': 'purchase_order.submitted',
			'purchase_order': doc.name,
			'transaction_date': str(doc.transaction_date),
			'schedule_date': str(doc.schedule_date),
			'grand_total': doc.grand_total,
			'items': [{
				'item_code': item.item_code,
				'qty': item.qty,
				'rate': item.rate
			} for item in doc.items]
		}
		
		try:
			response = requests.post(
				vendor.webhook_url,
				json=payload,
				headers={'Content-Type': 'application/json'},
				timeout=10
			)
			
			if response.status_code == 200:
				frappe.logger().info(f"Webhook sent successfully to {vendor.name}")
			else:
				frappe.logger().error(f"Webhook failed: {response.status_code}")
		
		except Exception as e:
			frappe.logger().error(f"Webhook error: {str(e)}")
