# -*- coding: utf-8 -*-
"""
Background Job Examples
Chapter 8: Server Script Hooks & Schedulers
"""

import frappe
from frappe.utils import today, cint
from frappe import _

def bulk_update_item_prices(price_list, percentage_change):
	"""Update all item prices in a price list by percentage"""
	frappe.enqueue(
		'chapter_08.background_jobs.bulk_operations._bulk_update_prices',
		price_list=price_list,
		percentage_change=percentage_change,
		queue='long',
		timeout=3600
	)
	
	frappe.msgprint(_('Price update has been queued. You will be notified when complete.'))

def _bulk_update_prices(price_list, percentage_change):
	"""Background worker for bulk price update"""
	try:
		items = frappe.get_all('Item Price',
			filters={'price_list': price_list},
			fields=['name', 'item_code', 'price_list_rate']
		)
		
		updated_count = 0
		
		for item in items:
			new_rate = item.price_list_rate * (1 + percentage_change / 100)
			
			frappe.db.set_value('Item Price', item.name, 'price_list_rate', new_rate)
			updated_count += 1
			
			# Commit every 100 records
			if updated_count % 100 == 0:
				frappe.db.commit()
		
		frappe.db.commit()
		
		# Send completion notification
		frappe.publish_realtime(
			'bulk_update_complete',
			{'message': _('Updated {0} item prices').format(updated_count)},
			user=frappe.session.user
		)
		
	except Exception as e:
		frappe.log_error(f"Bulk price update failed: {str(e)}")
		
		frappe.publish_realtime(
			'bulk_update_failed',
			{'message': _('Price update failed. Check error log.')},
			user=frappe.session.user
		)

def generate_monthly_reports(month, year):
	"""Generate monthly reports in background"""
	frappe.enqueue(
		'chapter_08.background_jobs.bulk_operations._generate_reports',
		month=month,
		year=year,
		queue='long',
		timeout=7200
	)

def _generate_reports(month, year):
	"""Background worker for report generation"""
	try:
		reports = [
			'Sales Report',
			'Purchase Report',
			'Inventory Report',
			'Financial Report'
		]
		
		generated_files = []
		
		for report_name in reports:
			file_path = generate_report(report_name, month, year)
			generated_files.append(file_path)
		
		# Send email with reports
		send_reports_email(generated_files, month, year)
		
	except Exception as e:
		frappe.log_error(f"Report generation failed: {str(e)}")

def generate_report(report_name, month, year):
	"""Generate individual report"""
	# Implementation would call report generation logic
	return f"/files/{report_name}_{month}_{year}.pdf"

def send_reports_email(files, month, year):
	"""Send generated reports via email"""
	recipients = frappe.get_all('User',
		filters={'role': 'Accounts Manager', 'enabled': 1},
		pluck='email'
	)
	
	if recipients:
		frappe.sendmail(
			recipients=recipients,
			subject=_('Monthly Reports - {0}/{1}').format(month, year),
			message=_('Please find attached monthly reports'),
			attachments=[{'file_url': f} for f in files]
		)

@frappe.whitelist()
def enqueue_bulk_operation(operation, **kwargs):
	"""Generic function to enqueue bulk operations"""
	frappe.enqueue(
		operation,
		queue='long',
		timeout=3600,
		**kwargs
	)
	
	return {'status': 'queued', 'message': _('Operation has been queued')}
