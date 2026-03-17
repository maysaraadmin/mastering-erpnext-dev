# -*- coding: utf-8 -*-
"""
Asset DocType Tests
Chapter 15: Automated Testing

Enhanced unit tests for Asset Management with comprehensive coverage
including edge cases, error handling, and business logic validation.
"""

import frappe
import unittest
from frappe.utils import today, add_days, getdate, nowdate
from frappe import _

class TestAsset(unittest.TestCase):
	"""Test cases for Asset DocType"""
	
	def setUp(self):
		"""Set up test data"""
		self.create_test_category()
		self.create_test_item()
		self.create_test_location()
		self.create_test_user()
		
	def tearDown(self):
		"""Clean up test data"""
		frappe.db.rollback()
		
	def create_test_category(self):
		"""Create test asset category"""
		if not frappe.db.exists('Asset Category', 'Test Category'):
			category = frappe.get_doc({
				'doctype': 'Asset Category',
				'category_name': 'Test Category',  # correct field name
				'depreciation_method': 'Straight Line',
				'useful_life': 5,
				'status': 'Active'
			})
			category.insert()
			
	def create_test_wdv_category(self):
		"""Create test WDV asset category"""
		if not frappe.db.exists('Asset Category', 'Test WDV Category'):
			category = frappe.get_doc({
				'doctype': 'Asset Category',
				'category_name': 'Test WDV Category',  # correct field name
				'depreciation_method': 'Written Down Value',
				'depreciation_rate': 20.0,
				'status': 'Active'
			})
			category.insert()
		
	def create_test_item(self):
		"""Create test item"""
		if not frappe.db.exists('Item', 'TEST-ASSET-001'):
			item = frappe.get_doc({
				'doctype': 'Item',
				'item_code': 'TEST-ASSET-001',
				'item_name': 'Test Asset Item',
				'item_group': 'Products',
				'stock_uom': 'Nos',
				'is_stock_item': 1
			})
			item.insert()
			
	def create_test_location(self):
		"""Create test location"""
		if not frappe.db.exists('Location', 'Test Location'):
			location = frappe.get_doc({
				'doctype': 'Location',
				'location_name': 'Test Location',
				'status': 'Active'
			})
			location.insert()
			
	def create_test_user(self):
		"""Create test user"""
		if not frappe.db.exists('User', 'test@example.com'):
			user = frappe.get_doc({
				'doctype': 'User',
				'email': 'test@example.com',
				'first_name': 'Test',
				'last_name': 'User'
			})
			user.insert()
	
	def test_asset_creation(self):
		"""Test basic asset creation"""
		asset = frappe.get_doc({
			'doctype': 'Asset',
			'asset_name': 'Test Laptop',
			'asset_category': 'Test Category',
			'item_code': 'TEST-ASSET-001',
			'purchase_date': today(),
			'purchase_amount': 1000.00,
			'status': 'In Stock'
		})
		asset.insert()
		
		self.assertTrue(frappe.db.exists('Asset', asset.name))
		self.assertEqual(asset.asset_name, 'Test Laptop')
		self.assertEqual(asset.purchase_amount, 1000.00)
		self.assertEqual(asset.status, 'In Stock')
		self.assertIsNotNone(asset.asset_id)
		self.assertEqual(asset.current_value, 1000.00)
		
	def test_asset_autoname(self):
		"""Test automatic asset naming"""
		asset = frappe.get_doc({
			'doctype': 'Asset',
			'asset_name': 'Test Asset 2',
			'asset_category': 'Test Category',
			'item_code': 'TEST-ASSET-001',
			'purchase_date': today(),
			'purchase_amount': 500.00
		})
		asset.insert()
		
		# Check if name follows pattern ASSET-GEN-XXXXXX
		self.assertTrue(asset.name.startswith('ASSET-GEN-'))
		self.assertEqual(len(asset.name), 16)
		
	def test_asset_validation_required_fields(self):
		"""Test required field validation"""
		# Test missing asset_category
		asset = frappe.get_doc({
			'doctype': 'Asset',
			'asset_name': 'Test Asset'
		})
		
		with self.assertRaises(frappe.ValidationError):
			asset.insert()
			
		# Test missing item_code
		asset = frappe.get_doc({
			'doctype': 'Asset',
			'asset_name': 'Test Asset',
			'asset_category': 'Test Category'
		})
		
		with self.assertRaises(frappe.ValidationError):
			asset.insert()
			
		# Test missing asset_name
		asset = frappe.get_doc({
			'doctype': 'Asset',
			'asset_category': 'Test Category',
			'item_code': 'TEST-ASSET-001'
		})
		
		with self.assertRaises(frappe.ValidationError):
			asset.insert()
	
	def test_asset_validation_dates(self):
		"""Test date validation"""
		future_date = add_days(today(), 30)
		
		# Test future purchase date
		asset = frappe.get_doc({
			'doctype': 'Asset',
			'asset_name': 'Test Asset',
			'asset_category': 'Test Category',
			'item_code': 'TEST-ASSET-001',
			'purchase_date': future_date,
			'purchase_amount': 1000.00
		})
		
		with self.assertRaises(frappe.ValidationError):
			asset.insert()
			
		# Test commissioning date before purchase date
		past_date = add_days(today(), -30)
		asset = frappe.get_doc({
			'doctype': 'Asset',
			'asset_name': 'Test Asset',
			'asset_category': 'Test Category',
			'item_code': 'TEST-ASSET-001',
			'purchase_date': today(),
			'commissioning_date': past_date,
			'purchase_amount': 1000.00
		})
		
		with self.assertRaises(frappe.ValidationError):
			asset.insert()
	
	def test_asset_validation_amounts(self):
		"""Test amount validation"""
		# Test negative purchase amount
		asset = frappe.get_doc({
			'doctype': 'Asset',
			'asset_name': 'Test Asset',
			'asset_category': 'Test Category',
			'item_code': 'TEST-ASSET-001',
			'purchase_date': today(),
			'purchase_amount': -100.00
		})
		
		with self.assertRaises(frappe.ValidationError):
			asset.insert()
			
		# Test zero purchase amount
		asset = frappe.get_doc({
			'doctype': 'Asset',
			'asset_name': 'Test Asset',
			'asset_category': 'Test Category',
			'item_code': 'TEST-ASSET-001',
			'purchase_date': today(),
			'purchase_amount': 0
		})
		
		with self.assertRaises(frappe.ValidationError):
			asset.insert()
			
		# Test salvage value greater than purchase amount
		asset = frappe.get_doc({
			'doctype': 'Asset',
			'asset_name': 'Test Asset',
			'asset_category': 'Test Category',
			'item_code': 'TEST-ASSET-001',
			'purchase_date': today(),
			'purchase_amount': 1000.00,
			'salvage_value': 1500.00
		})
		
		with self.assertRaises(frappe.ValidationError):
			asset.insert()
	
	def test_asset_depreciation_straight_line(self):
		"""Test straight line depreciation calculation"""
		past_date = add_days(today(), -365)  # 1 year ago
		
		asset = frappe.get_doc({
			'doctype': 'Asset',
			'asset_name': 'Test Asset',
			'asset_category': 'Test Category',
			'item_code': 'TEST-ASSET-001',
			'purchase_date': past_date,
			'purchase_amount': 1000.00,
			'depreciation_method': 'Straight Line',
			'useful_life': 5,
			'salvage_value': 100.00
		})
		asset.insert()
		
		# After 1 year, depreciation should be (1000-100)/5 = 180
		expected_depreciation = 180.0
		self.assertAlmostEqual(asset.accumulated_depreciation, expected_depreciation, places=2)
		self.assertLess(asset.accumulated_depreciation, asset.purchase_amount)
		
		# Current value should be purchase - depreciation
		expected_current_value = 1000.00 - expected_depreciation
		self.assertAlmostEqual(asset.current_value, expected_current_value, places=2)
		
	def test_asset_depreciation_wdv(self):
		"""Test written down value depreciation calculation"""
		self.create_test_wdv_category()
		past_date = add_days(today(), -365)  # 1 year ago
		
		asset = frappe.get_doc({
			'doctype': 'Asset',
			'asset_name': 'Test WDV Asset',
			'asset_category': 'Test WDV Category',
			'item_code': 'TEST-ASSET-001',
			'purchase_date': past_date,
			'purchase_amount': 1000.00,
			'depreciation_method': 'Written Down Value',
			'depreciation_rate': 20.0
		})
		asset.insert()
		
		# WDV: Value = 1000 * (1 - 0.2)^1 = 800, Depreciation = 200
		expected_depreciation = 200.0
		self.assertAlmostEqual(asset.accumulated_depreciation, expected_depreciation, places=2)
		expected_current_value = 800.0
		self.assertAlmostEqual(asset.current_value, expected_current_value, places=2)
	
	def test_asset_current_value(self):
		"""Test current value calculation"""
		asset = frappe.get_doc({
			'doctype': 'Asset',
			'asset_name': 'Test Asset',
			'asset_category': 'Test Category',
			'item_code': 'TEST-ASSET-001',
			'purchase_date': today(),
			'purchase_amount': 1000.00
		})
		asset.insert()
		
		expected_value = asset.purchase_amount - (asset.accumulated_depreciation or 0)
		self.assertEqual(asset.current_value, expected_value)
		
		# Test with salvage value floor
		asset.salvage_value = 900.00
		asset.calculate_current_value()
		self.assertGreaterEqual(asset.current_value, asset.salvage_value)
	
	def test_asset_status_transition(self):
		"""Test asset status workflow"""
		asset = frappe.get_doc({
			'doctype': 'Asset',
			'asset_name': 'Test Asset',
			'asset_category': 'Test Category',
			'item_code': 'TEST-ASSET-001',
			'purchase_date': today(),
			'purchase_amount': 1000.00,
			'status': 'In Stock'
		})
		asset.insert()
		
		# Valid transitions
		valid_transitions = [
			('In Stock', 'In Use'),
			('In Stock', 'Under Maintenance'),
			('In Stock', 'Scrapped'),
			('In Use', 'Under Maintenance'),
			('In Use', 'In Stock'),
			('Under Maintenance', 'In Use')
		]
		
		for from_status, to_status in valid_transitions:
			asset.status = from_status
			asset.save()
			asset.status = to_status
			asset.save()
			saved_asset = frappe.get_doc('Asset', asset.name)
			self.assertEqual(saved_asset.status, to_status)
			
		# Test invalid transition
		asset.status = 'Scrapped'
		asset.save()
		
		# Scrapped should not transition to In Use
		asset.status = 'In Use'
		with self.assertRaises(frappe.ValidationError):
			asset.save()
			
	def test_asset_location_validation(self):
		"""Test asset location validation"""
		# Test with valid location
		asset = frappe.get_doc({
			'doctype': 'Asset',
			'asset_name': 'Test Asset',
			'asset_category': 'Test Category',
			'item_code': 'TEST-ASSET-001',
			'purchase_date': today(),
			'purchase_amount': 1000.00,
			'location': 'Test Location'
		})
		asset.insert()
		self.assertEqual(asset.location, 'Test Location')
		
		# Test with invalid location
		asset = frappe.get_doc({
			'doctype': 'Asset',
			'asset_name': 'Test Asset 2',
			'asset_category': 'Test Category',
			'item_code': 'TEST-ASSET-001',
			'purchase_date': today(),
			'purchase_amount': 1000.00,
			'location': 'Invalid Location'
		})
		
		with self.assertRaises(frappe.ValidationError):
			asset.insert()

	def test_asset_duplicate_validation(self):
		"""Test duplicate asset validation"""
		# Create first asset
		asset1 = frappe.get_doc({
			'doctype': 'Asset',
			'asset_name': 'Test Laptop',
			'asset_category': 'Test Category',
			'item_code': 'TEST-ASSET-001',
			'purchase_date': today(),
			'purchase_amount': 1000.00,
			'serial_number': 'SN123456',
			'status': 'In Stock'
		})
		asset1.insert()
		
		# Try to create duplicate asset with same serial number
		asset2 = frappe.get_doc({
			'doctype': 'Asset',
			'asset_name': 'Test Laptop 2',
			'asset_category': 'Test Category',
			'item_code': 'TEST-ASSET-001',
			'purchase_date': today(),
			'purchase_amount': 1200.00,
			'serial_number': 'SN123456',
			'status': 'In Stock'
		})
		
		# Should raise validation error for duplicate serial number
		with self.assertRaises(frappe.ValidationError):
			asset2.insert()
			
	def test_asset_submission_workflow(self):
		"""Test asset submission and cancellation"""
		asset = frappe.get_doc({
			'doctype': 'Asset',
			'asset_name': 'Test Asset',
			'asset_category': 'Test Category',
			'item_code': 'TEST-ASSET-001',
			'purchase_date': today(),
			'purchase_amount': 1000.00,
			'status': 'In Stock'
		})
		asset.insert()
		
		# Test submission
		asset.submit()
		self.assertEqual(asset.docstatus, 1)
		
		# Test cancellation
		asset.cancel()
		self.assertEqual(asset.docstatus, 2)
		
	def test_asset_deletion_constraints(self):
		"""Test asset deletion constraints"""
		asset = frappe.get_doc({
			'doctype': 'Asset',
			'asset_name': 'Test Asset',
			'asset_category': 'Test Category',
			'item_code': 'TEST-ASSET-001',
			'purchase_date': today(),
			'purchase_amount': 1000.00,
			'status': 'In Use'  # In Use assets cannot be deleted
		})
		asset.insert()
		
		# Should not be able to delete asset in use
		with self.assertRaises(frappe.ValidationError):
			asset.delete()
			
		# Change to available status
		asset.status = 'In Stock'
		asset.save()
		
		# Should be able to delete available asset
		asset.delete()
		self.assertFalse(frappe.db.exists('Asset', asset.name))
		
	def test_asset_category_defaults(self):
		"""Test asset category defaults are applied"""
		asset = frappe.get_doc({
			'doctype': 'Asset',
			'asset_name': 'Test Asset',
			'asset_category': 'Test Category',
			'item_code': 'TEST-ASSET-001',
			'purchase_date': today(),
			'purchase_amount': 1000.00
			# Note: depreciation_method and useful_life not set
		})
		asset.insert()
		
		# Should inherit from category
		self.assertEqual(asset.depreciation_method, 'Straight Line')
		self.assertEqual(asset.useful_life, 5)

def run_tests():
	"""Run all asset tests"""
	suite = unittest.TestLoader().loadTestsFromTestCase(TestAsset)
	unittest.TextTestRunner(verbosity=2).run(suite)

if __name__ == '__main__':
	run_tests()
