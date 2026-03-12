# -*- coding: utf-8 -*-
"""
Production Plan DocType Controller
Chapter 12: Production Planning Tool
"""

import frappe
from frappe.model.document import Document
from frappe.utils import flt, getdate, today
from frappe import _

class ProductionPlan(Document):
	"""Production planning controller with BOM explosion"""
	
	def validate(self):
		"""Validate production plan"""
		self.validate_dates()
		self.calculate_totals()
		self.set_status()
	
	def validate_dates(self):
		"""Validate date fields"""
		if self.from_date and self.to_date:
			if getdate(self.to_date) < getdate(self.from_date):
				frappe.throw(_("To Date cannot be before From Date"))
	
	def calculate_totals(self):
		"""Calculate total quantities"""
		self.total_planned_qty = sum([flt(d.planned_qty) for d in self.po_items])
		self.total_produced_qty = sum([flt(d.produced_qty) for d in self.po_items])
		
		if self.total_planned_qty > 0:
			self.completion_percentage = (self.total_produced_qty / self.total_planned_qty) * 100
	
	def set_status(self):
		"""Set document status"""
		if self.docstatus == 0:
			self.status = "Draft"
		elif self.docstatus == 1:
			if self.completion_percentage >= 100:
				self.status = "Completed"
			elif self.completion_percentage > 0:
				self.status = "In Process"
			else:
				self.status = "Submitted"
		elif self.docstatus == 2:
			self.status = "Cancelled"

	def on_submit(self):
		"""Create work orders on submit"""
		self.create_work_orders()
	
	def create_work_orders(self):
		"""Create work orders for planned items"""
		for item in self.po_items:
			if item.planned_qty > 0:
				# In real implementation, create Work Order DocType
				frappe.msgprint(f"Work Order would be created for {item.item_code}: {item.planned_qty} units")

@frappe.whitelist()
def get_sales_orders(from_date, to_date, company):
	"""Get pending sales orders for production planning"""
	return frappe.db.sql("""
		SELECT 
			so.name,
			so.customer,
			so.transaction_date,
			so.delivery_date,
			SUM(soi.qty - soi.delivered_qty) as pending_qty
		FROM `tabSales Order` so
		INNER JOIN `tabSales Order Item` soi ON soi.parent = so.name
		WHERE so.docstatus = 1
		AND so.status != 'Closed'
		AND so.company = %(company)s
		AND so.transaction_date BETWEEN %(from_date)s AND %(to_date)s
		AND soi.delivered_qty < soi.qty
		GROUP BY so.name
		ORDER BY so.delivery_date
	""", {
		'from_date': from_date,
		'to_date': to_date,
		'company': company
	}, as_dict=1)

@frappe.whitelist()
def get_items_for_production_plan(sales_orders):
	"""Get items from selected sales orders"""
	import json
	if isinstance(sales_orders, str):
		sales_orders = json.loads(sales_orders)
	
	items = []
	for so in sales_orders:
		so_items = frappe.db.sql("""
			SELECT 
				item_code,
				item_name,
				SUM(qty - delivered_qty) as qty,
				uom,
				warehouse
			FROM `tabSales Order Item`
			WHERE parent = %(sales_order)s
			AND docstatus = 1
			AND qty > delivered_qty
			GROUP BY item_code
		""", {'sales_order': so}, as_dict=1)
		
		items.extend(so_items)
	
	return items


@frappe.whitelist()
def explode_bom(production_plan):
	"""Explode BOM to get raw material requirements"""
	doc = frappe.get_doc('Production Plan', production_plan)
	raw_materials = {}
	
	for item in doc.po_items:
		# Get BOM for item
		bom = frappe.db.get_value('BOM', {
			'item': item.item_code,
			'is_active': 1,
			'is_default': 1
		}, 'name')
		
		if bom:
			# Get BOM items
			bom_items = frappe.db.sql("""
				SELECT 
					item_code,
					item_name,
					qty,
					uom,
					stock_uom
				FROM `tabBOM Item`
				WHERE parent = %(bom)s
			""", {'bom': bom}, as_dict=1)
			
			for bom_item in bom_items:
				required_qty = flt(bom_item.qty) * flt(item.planned_qty)
				
				if bom_item.item_code in raw_materials:
					raw_materials[bom_item.item_code]['required_qty'] += required_qty
				else:
					raw_materials[bom_item.item_code] = {
						'item_code': bom_item.item_code,
						'item_name': bom_item.item_name,
						'required_qty': required_qty,
						'uom': bom_item.uom
					}
	
	return list(raw_materials.values())

def get_permission_query_conditions(user):
	"""Permission query conditions"""
	if not user:
		user = frappe.session.user
	
	if "Manufacturing Manager" in frappe.get_roles(user):
		return None
	
	return f"`tabProduction Plan`.company in ({', '.join(frappe.get_user_companies(user))})"
