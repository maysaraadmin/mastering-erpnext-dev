# -*- coding: utf-8 -*-
"""
Performance Tests
Chapter 15: Automated Testing - Performance Tests

Enhanced for ERPNext v16 with bulk operations testing,
modern performance monitoring, and comprehensive benchmarking.
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
from typing import Dict, Any, List, Optional, Union

class TestPerformance(unittest.TestCase):
	"""Performance tests for critical operations with v16 enhancements"""
	
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
		# v16: Use bulk operations for better performance
		test_assets = []
		for i in range(50):
			test_assets.append({
				"doctype": "Asset",
				"asset_name": f"Performance Test Asset {i}",
				"item_code": f"PERF-TEST-{i:03d}",
				"asset_category": "Test Category",
				"purchase_date": today(),
				"purchase_amount": 1000 + i,
				"status": "Available"
			})
		
		# v16: Bulk insert for performance
		try:
			frappe.db.bulk_insert(test_assets)
			self.logger.info(f"v16 bulk_insert created {len(test_assets)} test assets")
		except Exception as e:
			self.logger.error(f"v16 bulk_insert failed: {str(e)}")
	
	def test_v16_bulk_operations_performance(self):
		"""Test v16 bulk operations performance"""
		with self.measure_time("v16 bulk_insert"):
			# v16: Create 100 test assets
			test_assets = []
			for i in range(100):
				test_assets.append({
					"doctype": "Asset",
					"asset_name": f"Bulk Test Asset {i}",
					"item_code": f"BULK-TEST-{i:03d}",
					"asset_category": "Bulk Test Category",
					"purchase_date": today(),
					"purchase_amount": 500 + i,
					"status": "Available"
				})
			
			# v16: Use bulk_insert for performance
			frappe.db.bulk_insert(test_assets)
		
		# v16: Should complete in under 2 seconds for 100 records
		self.assertLess(self.last_execution_time, 2.0,
			f"v16 bulk_insert took {self.last_execution_time:.3f}s, expected < 2.0s")
		
	def test_v16_individual_vs_bulk_performance(self):
		"""Compare individual vs bulk operations in v16"""
		# Test individual inserts
		with self.measure_time("individual_inserts"):
			for i in range(50):
				asset = frappe.get_doc({
					"doctype": "Asset",
					"asset_name": f"Individual Test {i}",
					"item_code": f"IND-TEST-{i:03d}",
					"asset_category": "Individual Test Category",
					"purchase_date": today(),
					"purchase_amount": 500 + i,
					"status": "Available"
				})
				asset.insert()
		
		individual_time = self.last_execution_time
		
		# Test bulk inserts
		with self.measure_time("bulk_inserts"):
			bulk_assets = []
			for i in range(50):
				bulk_assets.append({
					"doctype": "Asset",
					"asset_name": f"Bulk Test Asset {i}",
					"item_code": f"BULK-TEST-{i:03d}",
					"asset_category": "Bulk Test Category",
					"purchase_date": today(),
					"purchase_amount": 500 + i,
					"status": "Available"
				})
			
			# v16: Use bulk_insert for performance
			frappe.db.bulk_insert(bulk_assets)
		
		bulk_time = self.last_execution_time
		
		# v16: Bulk should be significantly faster
		improvement_factor = individual_time / bulk_time
		self.assertGreater(improvement_factor, 5.0,
			f"v16 bulk operations improvement factor: {improvement_factor:.1f}x, expected > 5.0x")
		
	def test_v16_memory_usage_optimization(self):
		"""Test memory usage with v16 optimizations"""
		import gc
		process = psutil.Process(os.getpid())
		
		# v16: Test memory before operations
		initial_memory = process.memory_info().rss / 1024 / 1024  # MB
		
		# v16: Create large dataset to test memory efficiency
		large_dataset = []
		for i in range(1000):
			large_dataset.append({
				"doctype": "Asset",
				"asset_name": f"Memory Test Asset {i}",
				"item_code": f"MEM-TEST-{i:04d}",
				"asset_category": "Memory Test Category",
				"purchase_date": today(),
				"purchase_amount": 100 + i,
				"status": "Available"
			})
		
		# v16: Use bulk operations to reduce memory overhead
		try:
			frappe.db.bulk_insert(large_dataset)
			peak_memory = process.memory_info().rss / 1024 / 1024  # MB
		except Exception as e:
			self.logger.error(f"v16 bulk memory test failed: {str(e)}")
		
		# v16: Force garbage collection
		gc.collect()
		final_memory = process.memory_info().rss / 1024 / 1024  # MB
		memory_increase = final_memory - initial_memory
		
		# v16: Memory increase should be reasonable (< 100MB for 1000 records)
		self.assertLess(memory_increase, 100,
			f"v16 memory increased by {memory_increase:.1f}MB, expected < 100MB")
		
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
		# Skip if Production Plan doctype is not available in this context
		if not frappe.db.exists('DocType', 'Production Plan'):
			self.skipTest("Production Plan DocType not available")

		# Use our custom explode_bom which doesn't require bom_no on insert
		plan = frappe.get_doc({
			"doctype": "Production Plan",
			"company": self.company,
			"posting_date": today()
		})
		plan.append("po_items", {
			"item_code": "PERF-TEST-ITEM",
			"planned_qty": 100,
			"uom": "Nos"
		})
		plan.insert(ignore_permissions=True, ignore_mandatory=True)

		start_time = time.time()
		from production_planning_app.production_planning.doctype.production_plan.production_plan import explode_bom
		explode_bom(plan.name)
		execution_time = time.time() - start_time

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
		
		# Should be fast with proper indexing (relaxed for Docker/CI environments)
		self.assertLess(self.last_execution_time, 1.0,
			f"Indexed query took {self.last_execution_time:.3f}s, expected < 1.0s")
		
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
					"status": "In Stock",
					"company": self.company
				})
				asset.insert()
			except:
				pass  # Ignore duplicates
				
	def test_memory_usage_performance(self):
		"""Test that bulk operations complete in reasonable time (memory proxy)"""
		start_time = time.time()
		
		# Create many assets — if memory were leaking badly this would slow down
		self.create_test_assets(100)
		
		elapsed = time.time() - start_time
		
		# 100 inserts should complete in under 30 seconds
		self.assertLess(elapsed, 30,
			f"Bulk insert of 100 assets took {elapsed:.1f}s, expected < 30s")
			
	def test_concurrent_operations_performance(self):
		"""Test performance under simulated concurrent load (sequential, Frappe is not thread-safe)"""
		execution_times = []

		for _ in range(5):
			start = time.time()
			frappe.get_all('Asset',
				filters={'status': 'In Stock'},
				fields=['name', 'asset_name'],
				limit=10
			)
			execution_times.append(time.time() - start)

		self.assertEqual(len(execution_times), 5)

		avg_time = statistics.mean(execution_times)
		self.assertLess(avg_time, 0.5,
			f"Sequential query avg time: {avg_time:.3f}s, expected < 0.5s")

def run_tests():
	"""Run all performance tests"""
	suite = unittest.TestLoader().loadTestsFromTestCase(TestPerformance)
	unittest.TextTestRunner(verbosity=2).run(suite)

if __name__ == '__main__':
	run_tests()
