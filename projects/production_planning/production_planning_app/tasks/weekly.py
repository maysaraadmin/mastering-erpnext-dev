# -*- coding: utf-8 -*-
"""Weekly tasks for production planning"""

import frappe

def generate_capacity_report():
	"""Generate weekly capacity utilization report"""
	# Get production data
	data = frappe.db.sql("""
		SELECT 
			company,
			COUNT(*) as total_plans,
			SUM(total_planned_qty) as planned_qty,
			SUM(total_produced_qty) as produced_qty
		FROM `tabProduction Plan`
		WHERE docstatus = 1
		GROUP BY company
	""", as_dict=1)
	
	# Send to manufacturing managers
	users = frappe.get_all('Has Role',
		filters={'role': 'Manufacturing Manager'},
		fields=['parent']
	)
	
	for user in users:
		frappe.sendmail(
			recipients=[user.parent],
			subject='Weekly Production Capacity Report',
			message=f"<pre>{data}</pre>"
		)
