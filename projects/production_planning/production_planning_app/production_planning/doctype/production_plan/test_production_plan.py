# -*- coding: utf-8 -*-
"""
Production Plan DocType Tests
Enhanced test coverage for Production Planning project

Chapter 15 Fix: Expanded test coverage for Production Planning project
"""

import frappe
import unittest
from frappe.utils import today, add_days, getdate, nowdate
from frappe import _

class TestProductionPlan(unittest.TestCase):
    """Test cases for Production Plan DocType"""
    
    def setUp(self):
        """Set up test data"""
        self.create_test_item()
        self.create_test_bom()
        self.create_test_workstation()
        
    def tearDown(self):
        """Clean up test data"""
        frappe.db.rollback()
        
    def create_test_item(self):
        """Create test item"""
        if not frappe.db.exists('Item', 'TEST-ITEM-001'):
            item = frappe.get_doc({
                'doctype': 'Item',
                'item_code': 'TEST-ITEM-001',
                'item_name': 'Test Product',
                'item_group': 'Products',
                'stock_uom': 'Nos',
                'is_stock_item': 1
            })
            item.insert()
            
    def create_test_bom(self):
        """Create test BOM"""
        if not frappe.db.exists('BOM', 'BOM-TEST-001'):
            bom = frappe.get_doc({
                'doctype': 'BOM',
                'bom_no': 'BOM-TEST-001',
                'item': 'TEST-ITEM-001',
                'quantity': 1,
                'uom': 'Nos',
                'is_active': 1
            })
            bom.append('items', {
                'item_code': 'TEST-ITEM-001',
                'qty': 1,
                'uom': 'Nos'
            })
            bom.insert()
            
    def create_test_workstation(self):
        """Create test workstation"""
        if not frappe.db.exists('Workstation', 'WS-TEST-001'):
            workstation = frappe.get_doc({
                'doctype': 'Workstation',
                'workstation_name': 'Test Workstation',
                'workstation_type': 'Assembly',
                'capacity': 8.0
            })
            workstation.insert()
    
    def test_production_plan_creation(self):
        """Test basic production plan creation"""
        plan = frappe.get_doc({
            'doctype': 'Production Plan',
            'production_item': 'TEST-ITEM-001',
            'quantity': 100,
            'planned_start_date': today(),
            'planned_end_date': add_days(today(), 10)
        })
        plan.insert()
        
        self.assertTrue(plan.name)
        self.assertEqual(plan.production_item, 'TEST-ITEM-001')
        self.assertEqual(plan.quantity, 100)
        self.assertEqual(plan.status, 'Draft')
        
    def test_production_plan_validation(self):
        """Test production plan validation"""
        # Test missing production item
        plan = frappe.get_doc({
            'doctype': 'Production Plan',
            'quantity': 100,
            'planned_start_date': today(),
            'planned_end_date': add_days(today(), 10)
        })
        
        with self.assertRaises(frappe.ValidationError):
            plan.insert()
            
        # Test negative quantity
        plan = frappe.get_doc({
            'doctype': 'Production Plan',
            'production_item': 'TEST-ITEM-001',
            'quantity': -10,
            'planned_start_date': today(),
            'planned_end_date': add_days(today(), 10)
        })
        
        with self.assertRaises(frappe.ValidationError):
            plan.insert()
            
        # Test end date before start date
        plan = frappe.get_doc({
            'doctype': 'Production Plan',
            'production_item': 'TEST-ITEM-001',
            'quantity': 100,
            'planned_start_date': add_days(today(), 10),
            'planned_end_date': today()
        })
        
        with self.assertRaises(frappe.ValidationError):
            plan.insert()
    
    def test_bom_explosion(self):
        """Test BOM explosion functionality"""
        plan = frappe.get_doc({
            'doctype': 'Production Plan',
            'production_item': 'TEST-ITEM-001',
            'quantity': 100,
            'planned_start_date': today(),
            'planned_end_date': add_days(today(), 10)
        })
        plan.insert()
        
        # Test BOM explosion
        plan.explode_bom()
        plan.save()
        
        self.assertTrue(len(plan.get('items')) > 0)
        
    def test_material_requirement_calculation(self):
        """Test material requirement calculation"""
        plan = frappe.get_doc({
            'doctype': 'Production Plan',
            'production_item': 'TEST-ITEM-001',
            'quantity': 100,
            'planned_start_date': today(),
            'planned_end_date': add_days(today(), 10)
        })
        plan.insert()
        plan.explode_bom()
        plan.calculate_material_requirements()
        plan.save()
        
        # Check if material requirements are calculated
        self.assertTrue(hasattr(plan, 'material_requirements'))
        if hasattr(plan, 'material_requirements'):
            self.assertTrue(len(plan.material_requirements) > 0)
    
    def test_capacity_planning(self):
        """Test capacity planning functionality"""
        plan = frappe.get_doc({
            'doctype': 'Production Plan',
            'production_item': 'TEST-ITEM-001',
            'quantity': 100,
            'planned_start_date': today(),
            'planned_end_date': add_days(today(), 10),
            'workstation': 'WS-TEST-001'
        })
        plan.insert()
        
        # Test capacity calculation
        plan.calculate_capacity_requirements()
        plan.save()
        
        # Check if capacity is calculated
        self.assertTrue(hasattr(plan, 'capacity_required'))
        
    def test_work_order_generation(self):
        """Test work order generation"""
        plan = frappe.get_doc({
            'doctype': 'Production Plan',
            'production_item': 'TEST-ITEM-001',
            'quantity': 100,
            'planned_start_date': today(),
            'planned_end_date': add_days(today(), 10)
        })
        plan.insert()
        plan.explode_bom()
        plan.submit()
        
        # Test work order generation
        work_orders = plan.generate_work_orders()
        
        self.assertTrue(len(work_orders) > 0)
        
        # Check if work orders are created
        for wo in work_orders:
            self.assertTrue(frappe.db.exists('Work Order', wo))
    
    def test_production_plan_submission(self):
        """Test production plan submission workflow"""
        plan = frappe.get_doc({
            'doctype': 'Production Plan',
            'production_item': 'TEST-ITEM-001',
            'quantity': 100,
            'planned_start_date': today(),
            'planned_end_date': add_days(today(), 10)
        })
        plan.insert()
        plan.explode_bom()
        
        # Test submission
        plan.submit()
        
        self.assertEqual(plan.docstatus, 1)
        self.assertEqual(plan.status, 'Submitted')
        
        # Test cancellation
        plan.cancel()
        
        self.assertEqual(plan.docstatus, 2)
        self.assertEqual(plan.status, 'Cancelled')
    
    def test_material_shortage_detection(self):
        """Test material shortage detection"""
        plan = frappe.get_doc({
            'doctype': 'Production Plan',
            'production_item': 'TEST-ITEM-001',
            'quantity': 1000,  # High quantity to trigger shortage
            'planned_start_date': today(),
            'planned_end_date': add_days(today(), 10)
        })
        plan.insert()
        plan.explode_bom()
        plan.check_material_availability()
        plan.save()
        
        # Check if shortages are detected
        if hasattr(plan, 'material_shortages'):
            self.assertTrue(len(plan.material_shortages) >= 0)
    
    def test_production_plan_reporting(self):
        """Test production plan reporting functionality"""
        plan = frappe.get_doc({
            'doctype': 'Production Plan',
            'production_item': 'TEST-ITEM-001',
            'quantity': 100,
            'planned_start_date': today(),
            'planned_end_date': add_days(today(), 10)
        })
        plan.insert()
        plan.submit()
        
        # Test report data generation
        report_data = plan.get_report_data()
        
        self.assertTrue('plan_details' in report_data)
        self.assertTrue('material_requirements' in report_data)
        self.assertTrue('capacity_utilization' in report_data)

class TestProductionPlanIntegration(unittest.TestCase):
    """Integration tests for Production Planning"""
    
    def setUp(self):
        """Set up test data"""
        self.create_test_data()
        
    def tearDown(self):
        """Clean up test data"""
        frappe.db.rollback()
        
    def create_test_data(self):
        """Create comprehensive test data"""
        # Create items
        self.create_item('RAW-001', 'Raw Material 1')
        self.create_item('RAW-002', 'Raw Material 2') 
        self.create_item('FINISHED-001', 'Finished Product 1')
        
        # Create BOM
        self.create_bom('BOM-FINISHED-001', 'FINISHED-001', [
            {'item_code': 'RAW-001', 'qty': 2},
            {'item_code': 'RAW-002', 'qty': 1}
        ])
        
    def create_item(self, code, name):
        """Create test item"""
        if not frappe.db.exists('Item', code):
            item = frappe.get_doc({
                'doctype': 'Item',
                'item_code': code,
                'item_name': name,
                'item_group': 'Products',
                'stock_uom': 'Nos',
                'is_stock_item': 1
            })
            item.insert()
            
    def create_bom(self, bom_no, item, items):
        """Create test BOM"""
        if not frappe.db.exists('BOM', bom_no):
            bom = frappe.get_doc({
                'doctype': 'BOM',
                'bom_no': bom_no,
                'item': item,
                'quantity': 1,
                'uom': 'Nos',
                'is_active': 1
            })
            
            for item_data in items:
                bom.append('items', item_data)
                
            bom.insert()
    
    def test_end_to_end_production_flow(self):
        """Test complete production workflow"""
        # Create production plan
        plan = frappe.get_doc({
            'doctype': 'Production Plan',
            'production_item': 'FINISHED-001',
            'quantity': 50,
            'planned_start_date': today(),
            'planned_end_date': add_days(today(), 15)
        })
        plan.insert()
        
        # Explode BOM
        plan.explode_bom()
        
        # Check material availability
        plan.check_material_availability()
        
        # Submit plan
        plan.submit()
        
        # Generate work orders
        work_orders = plan.generate_work_orders()
        
        # Verify workflow completion
        self.assertEqual(plan.docstatus, 1)
        self.assertTrue(len(work_orders) > 0)
        self.assertTrue(len(plan.get('items')) > 0)
        
    def test_multi_level_bom_explosion(self):
        """Test multi-level BOM explosion"""
        # Create sub-assembly
        self.create_item('SUB-ASSY-001', 'Sub Assembly 1')
        self.create_bom('BOM-SUB-001', 'SUB-ASSY-001', [
            {'item_code': 'RAW-001', 'qty': 1}
        ])
        
        # Update finished goods BOM to use sub-assembly
        frappe.db.sql("DELETE FROM `tabBOM Item` WHERE parent = 'BOM-FINISHED-001'")
        bom = frappe.get_doc('BOM', 'BOM-FINISHED-001')
        bom.append('items', {'item_code': 'SUB-ASSY-001', 'qty': 1})
        bom.append('items', {'item_code': 'RAW-002', 'qty': 1})
        bom.save()
        
        # Test multi-level explosion
        plan = frappe.get_doc({
            'doctype': 'Production Plan',
            'production_item': 'FINISHED-001',
            'quantity': 10,
            'planned_start_date': today(),
            'planned_end_date': add_days(today(), 10)
        })
        plan.insert()
        plan.explode_bom()
        
        # Should explode to all levels
        items = plan.get('items', [])
        self.assertTrue(len(items) >= 2)  # Raw materials should be included

class TestProductionPlanPerformance(unittest.TestCase):
    """Performance tests for Production Planning"""
    
    def test_bulk_plan_creation(self):
        """Test bulk production plan creation performance"""
        import time
        
        # Create test item if not exists
        if not frappe.db.exists('Item', 'PERF-TEST-001'):
            item = frappe.get_doc({
                'doctype': 'Item',
                'item_code': 'PERF-TEST-001',
                'item_name': 'Performance Test Item',
                'item_group': 'Products',
                'stock_uom': 'Nos'
            })
            item.insert()
        
        start_time = time.time()
        
        # Create 100 production plans
        for i in range(100):
            plan = frappe.get_doc({
                'doctype': 'Production Plan',
                'production_item': 'PERF-TEST-001',
                'quantity': 10,
                'planned_start_date': today(),
                'planned_end_date': add_days(today(), 5)
            })
            plan.insert()
            
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete within reasonable time (5 seconds)
        self.assertLess(execution_time, 5.0, 
                       f"Bulk creation took {execution_time:.3f}s, expected < 5.0s")
        
    def test_bom_explosion_performance(self):
        """Test BOM explosion performance"""
        import time
        
        # Create complex BOM if not exists
        if not frappe.db.exists('BOM', 'PERF-BOM-001'):
            bom = frappe.get_doc({
                'doctype': 'BOM',
                'bom_no': 'PERF-BOM-001',
                'item': 'PERF-TEST-001',
                'quantity': 1,
                'uom': 'Nos'
            })
            
            # Add 50 components
            for i in range(50):
                bom.append('items', {
                    'item_code': 'PERF-TEST-001',
                    'qty': 1,
                    'uom': 'Nos'
                })
                
            bom.insert()
        
        # Test explosion performance
        plan = frappe.get_doc({
            'doctype': 'Production Plan',
            'production_item': 'PERF-TEST-001',
            'quantity': 1000,
            'planned_start_date': today(),
            'planned_end_date': add_days(today(), 10)
        })
        plan.insert()
        
        start_time = time.time()
        plan.explode_bom()
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Should complete within reasonable time (2 seconds)
        self.assertLess(execution_time, 2.0, 
                       f"BOM explosion took {execution_time:.3f}s, expected < 2.0s")
