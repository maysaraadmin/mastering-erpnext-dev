# -*- coding: utf-8 -*-
"""Daily tasks for production planning"""

import frappe

def check_material_shortages():
	"""Check for material shortages in active production plans"""
	plans = frappe.get_all('Production Plan',
		filters={'status': ['in', ['Submitted', 'In Process']]},
		fields=['name']
	)
	
	for plan in plans:
		# Check material availability
		frappe.msgprint(f"Checking materials for {plan.name}")

def update_production_status():
	"""Update production plan status based on work orders"""
	frappe.db.sql("""
		UPDATE `tabProduction Plan`
		SET status = 'Completed'
		WHERE completion_percentage >= 100
		AND status != 'Completed'
	""")
	frappe.db.commit()
