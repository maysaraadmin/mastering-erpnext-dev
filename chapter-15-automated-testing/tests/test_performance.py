# -*- coding: utf-8 -*-
"""
Performance Tests
Chapter 15: Automated Testing - Performance Tests

Comprehensive performance benchmarks for ERPNext operations
including database queries, API responses, and batch operations.
"""

import frappe
import unittest
import time
import statistics
from frappe.utils import today, add_days, getdate, nowdate
from contextlib import contextmanager
import psutil
import os
import threading
import queue

class TestPerformance(unittest.TestCase):
	"""Performance tests for critical operations"""
	
	def setUp(self):
		"""Set up test data"""
		self.company = frappe.defaults.get_defaults().get("company")
		self.create_test_data()
	
	def tearDown(self):
		"""Clean up"""
		frappe.db.rollback()
		
	@contextmanager
	def measure_time(self, operation_name):
		"""Context manager to measure execution time"""
		start_time = time.time()
		yield
		end_time = time.time()
		self.last_execution_time = end_time - start_time
		
	def create_test_data(self):
		"""Create test data for performance testing"""
		# Create test category
		if not frappe.db.exists('Asset Category', 'Perf Test Category'):
			category = frappe.get_doc({
				'doctype': 'Asset Category',
				'asset_category_name': 'Perf Test Category',
				'depreciation_method': 'Straight Line',
				'useful_life': 5
			})
			category.insert()
			
		# Create test item
		if not frappe.db.exists('Item', 'PERF-TEST-ITEM'):
			item = frappe.get_doc({
				'doctype': 'Item',
				'item_code': 'PERF-TEST-ITEM',
				'item_name': 'Performance Test Item',
				'item_group': 'Products',
				'stock_uom': 'Nos'
			})
			item.insert()
	
	def test_asset_list_query_performance(self):
		"""Test asset list query performance"""
		# Create test assets for realistic testing
		self.create_test_assets(20)
		
		with self.measure_time("Asset List Query"):
			assets = frappe.get_all('Asset',
				filters={'docstatus': ['<', 2]},
				fields=['name', 'asset_name', 'status', 'current_value'],
				limit=100
			)
		
		# Should complete in under 0.5 seconds
		self.assertLess(self.last_execution_time, 0.5, 
			f"Asset list query took {self.last_execution_time:.3f}s, expected < 0.5s")
		
		# Verify results
		self.assertGreater(len(assets), 0)
		
	def test_asset_list_query_performance_with_multiple_runs(self):
		"""Test asset list query performance with multiple runs"""
		self.create_test_assets(50)
		
		execution_times = []
		
		# Run query 10 times to get average
		for _ in range(10):
			with self.measure_time("Asset List Query"):
				assets = frappe.get_all('Asset',
					filters={'docstatus': ['<', 2]},
					fields=['name', 'asset_name', 'status', 'current_value'],
					limit=100
				)
			execution_times.append(self.last_execution_time)
		
		avg_time = statistics.mean(execution_times)
		max_time = max(execution_times)
		
		# Average should be under 0.3 seconds
		self.assertLess(avg_time, 0.3,
			f"Average query time: {avg_time:.3f}s, expected < 0.3s")
		# Max should be under 0.5 seconds
		self.assertLess(max_time, 0.5,
			f"Max query time: {max_time:.3f}s, expected < 0.5s")
	
	def test_dashboard_data_performance(self):
		"""Test dashboard data retrieval performance"""
		from asset_management_app.asset_management.dashboard.asset_dashboard import get_dashboard_data
		
		start_time = time.time()
		
		# Get dashboard data
		data = get_dashboard_data()
		
		end_time = time.time()
		execution_time = end_time - start_time
		
		# Should complete in under 2 seconds
		self.assertLess(execution_time, 2.0,
			f"Dashboard query took {execution_time:.2f}s, expected < 2.0s")
		
		# Verify data structure
		self.assertIn('summary', data)
		self.assertIn('by_category', data)
		self.assertIn('utilization', data)
	
	def test_bom_explosion_performance(self):
		"""Test BOM explosion performance"""
		# Create test production plan
		plan = frappe.get_doc({
			"doctype": "Production Plan",
			"company": self.company,
			"posting_date": today()
		})
		
		# Add multiple items
		for i in range(10):
			plan.append("po_items", {
				"item_code": f"TEST-ITEM-{i:03d}",
				"planned_qty": 100,
				"uom": "Nos"
			})
		
		plan.insert()
		
		start_time = time.time()
		
		# Explode BOM
		from production_planning_app.production_planning.doctype.production_plan.production_plan import explode_bom
		raw_materials = explode_bom(plan.name)
		
		end_time = time.time()
		execution_time = end_time - start_time
		
		# Should complete in under 3 seconds for 10 items
		self.assertLess(execution_time, 3.0,
			f"BOM explosion took {execution_time:.2f}s, expected < 3.0s")
	
	def test_bulk_asset_creation_performance(self):
		"""Test bulk asset creation performance"""
		batch_sizes = [10, 25, 50]
		
		for batch_size in batch_sizes:
			with self.measure_time(f"Bulk Creation - {batch_size} assets"):
				assets_created = []
				for i in range(batch_size):
					asset = frappe.get_doc({
						"doctype": "Asset",
						"asset_name": f"Perf Test Asset {i}",
						"item_code": "PERF-TEST-ITEM",
						"asset_category": "Perf Test Category",
						"purchase_date": today(),
						"purchase_amount": 10000,
						"company": self.company
					})
					asset.insert()
					assets_created.append(asset.name)
			
			# Calculate average time per asset
			avg_time = self.last_execution_time / batch_size
			
			# Performance should scale reasonably
			if batch_size == 10:
				self.assertLess(avg_time, 0.1,
					f"Avg time per asset ({batch_size}): {avg_time:.3f}s, expected < 0.1s")
			elif batch_size == 25:
				self.assertLess(avg_time, 0.08,
					f"Avg time per asset ({batch_size}): {avg_time:.3f}s, expected < 0.08s")
			elif batch_size == 50:
				self.assertLess(avg_time, 0.06,
					f"Avg time per asset ({batch_size}): {avg_time:.3f}s, expected < 0.06s")
	
	def test_report_generation_performance(self):
		"""Test report generation performance"""
		from asset_management_app.asset_management.report.asset_utilization_report.asset_utilization_report import execute
		
		filters = {
			'from_date': add_days(today(), -30),
			'to_date': today()
		}
		
		start_time = time.time()
		
		# Generate report
		columns, data = execute(filters)
		
		end_time = time.time()
		execution_time = end_time - start_time
		
		# Should complete in under 2 seconds
		self.assertLess(execution_time, 2.0,
			f"Report generation took {execution_time:.2f}s, expected < 2.0s")
	
	def test_api_authentication_performance(self):
		"""Test API authentication performance"""
		# Create test vendor if not exists
		if not frappe.db.exists("Vendor", "PERF-TEST-VENDOR"):
			vendor = frappe.get_doc({
				"doctype": "Vendor",
				"vendor_name": "Performance Test Vendor",
				"api_key": "perf_test_key",
				"api_secret": "perf_test_secret",
				"status": "Active"
			})
			vendor.insert(ignore_permissions=True)
		
		# Test multiple authentications
		auth_counts = [1, 10, 50]
		
		for auth_count in auth_counts:
			with self.measure_time(f"Authentication - {auth_count} requests"):
				for i in range(auth_count):
					try:
						# Simulate API authentication
						vendor = frappe.db.get_value('Vendor',
							{'api_key': 'perf_test_key', 'api_secret': 'perf_test_secret'},
							['name', 'vendor_name']
						)
					except:
						pass  # Handle authentication errors gracefully
			
			# Calculate average time per authentication
			avg_time = self.last_execution_time / auth_count
			
			# Single auth should be very fast
			if auth_count == 1:
				self.assertLess(avg_time, 0.05,
					f"Single auth time: {avg_time:.3f}s, expected < 0.05s")
			# Batch auths should be efficient
			else:
				self.assertLess(avg_time, 0.02,
					f"Avg auth time ({auth_count}): {avg_time:.3f}s, expected < 0.02s")
	
	def test_database_query_optimization(self):
		"""Test that queries use proper indexes"""
		self.create_test_assets(100)
		
		# Test indexed query
		with self.measure_time("Indexed Query"):
			result = frappe.db.sql("""
				SELECT name, asset_name, status
				FROM `tabAsset`
				WHERE status = 'In Stock'
				AND asset_category = 'Perf Test Category'
				LIMIT 100
		""")
		
		# Should be very fast with proper indexing
		self.assertLess(self.last_execution_time, 0.1,
			f"Indexed query took {self.last_execution_time:.3f}s, expected < 0.1s")
		
		# Test non-indexed query (should be slower)
		with self.measure_time("Non-Indexed Query"):
			result = frappe.db.sql("""
				SELECT name, asset_name, status
				FROM `tabAsset`
				WHERE asset_name LIKE '%Test%'
				LIMIT 100
		""")
		
		# Non-indexed query will be slower but should still be reasonable
		self.assertLess(self.last_execution_time, 0.5,
			f"Non-indexed query took {self.last_execution_time:.3f}s, expected < 0.5s")
			
	def create_test_assets(self, count):
		"""Helper method to create test assets"""
		for i in range(count):
			try:
				asset = frappe.get_doc({
					"doctype": "Asset",
					"asset_name": f"Perf Test Asset {i}",
					"item_code": "PERF-TEST-ITEM",
					"asset_category": "Perf Test Category",
					"purchase_date": today(),
					"purchase_amount": 1000 + i,
					"status": "In Stock"
				})
				asset.insert()
			except:
				pass  # Ignore duplicates
				
	def test_memory_usage_performance(self):
		"""Test memory usage during operations"""
		process = psutil.Process(os.getpid())
		initial_memory = process.memory_info().rss / 1024 / 1024  # MB
		
		# Create many assets
		self.create_test_assets(100)
		
		final_memory = process.memory_info().rss / 1024 / 1024  # MB
		memory_increase = final_memory - initial_memory
		
		# Memory increase should be reasonable (< 50MB for 100 assets)
		self.assertLess(memory_increase, 50,
			f"Memory increased by {memory_increase:.1f}MB, expected < 50MB")
			
	def test_concurrent_operations_performance(self):
		"""Test performance under concurrent load"""
		results = queue.Queue()
		
		def worker():
			try:
				with self.measure_time("Concurrent Query"):
					assets = frappe.get_all('Asset',
						filters={'status': 'In Stock'},
						fields=['name', 'asset_name'],
						limit=10
					)
					results.put(('success', self.last_execution_time))
			except Exception as e:
				results.put(('error', str(e)))
		
		# Start 5 concurrent threads
		threads = []
		for _ in range(5):
			thread = threading.Thread(target=worker)
			threads.append(thread)
			thread.start()
		
		# Wait for all threads to complete
		for thread in threads:
			thread.join()
		
		# Collect results
		execution_times = []
		while not results.empty():
			status, time_taken = results.get()
			if status == 'success':
				execution_times.append(time_taken)
		
		# All operations should complete successfully
		self.assertEqual(len(execution_times), 5)
		
		# Average time should be reasonable
		avg_time = statistics.mean(execution_times)
		self.assertLess(avg_time, 0.5,
			f"Concurrent avg time: {avg_time:.3f}s, expected < 0.5s")

def run_tests():
	"""Run all performance tests"""
	suite = unittest.TestLoader().loadTestsFromTestCase(TestPerformance)
	unittest.TextTestRunner(verbosity=2).run(suite)

if __name__ == '__main__':
	run_tests()
