#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Script for ETDA Tax Invoice Generator
==========================================
This script tests the XML generation without Odoo context.

Usage:
    python test_xml_generation.py
"""

import sys
import os

# Add lib to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, date


class MockUOM:
    """Mock UOM for testing"""
    def __init__(self, name='EA'):
        self.name = name


class MockProduct:
    """Mock product for testing"""
    def __init__(self, name='Test Product'):
        self.name = name


class MockTax:
    """Mock tax for testing"""
    def __init__(self, amount=7.0, amount_type='percent'):
        self.amount = amount
        self.amount_type = amount_type


class MockCurrency:
    """Mock currency for testing"""
    def __init__(self, name='THB'):
        self.name = name


class MockState:
    """Mock state/province for testing"""
    def __init__(self, name='กรุงเทพมหานคร', code='10'):
        self.name = name
        self.code = code


class MockCountry:
    """Mock country for testing"""
    def __init__(self, code='TH'):
        self.code = code


class MockInvoiceLine:
    """Mock invoice line for testing"""
    def __init__(self, line_num, name, quantity, price_unit, discount=0, tax_amount=0):
        self.name = name
        self.quantity = quantity
        self.price_unit = price_unit
        self.discount = discount
        self.display_type = False
        self.product_id = MockProduct(name)
        self.product_uom_id = MockUOM('EA')
        self.tax_ids = [MockTax(7.0)]
        
        # Calculate totals
        subtotal = quantity * price_unit * (1 - discount/100)
        self.price_subtotal = subtotal
        self.price_total = subtotal * 1.07  # Add 7% VAT


class MockPartner:
    """Mock partner for testing"""
    def __init__(self):
        self.name = 'บริษัท ลูกค้าทดสอบ จำกัด'
        self.vat = 'TH0123456789012'
        self.etax_tax_id = '0123456789012'
        self.etax_branch_id = '00000'
        self.etax_use_vat = False
        self.etax_effective_tax_id = '0123456789012'
        self.email = 'customer@example.com'
        self.phone = '02-123-4567'
        self.mobile = '081-234-5678'
        self.street = 'ถนนสุขุมวิท'
        self.zip = '10110'
        self.state_id = MockState()
        self.country_id = MockCountry()
        
        # e-Tax address fields
        self.etax_building_number = '123'
        self.etax_soi = 'สุขุมวิท 21'
        self.etax_moo = None
        self.etax_floor_number = '5'
        self.etax_sub_district = 'คลองเตยเหนือ'
        self.etax_district = 'วัฒนา'
        self.etax_province = 'กรุงเทพมหานคร'
        self.etax_province_code = '10'
    
    def get_etax_address_dict(self):
        return {
            'postal_code': self.zip,
            'building_number': self.etax_building_number,
            'soi': self.etax_soi,
            'floor': self.etax_floor_number,
            'sub_district': self.etax_sub_district,
            'district': self.etax_district,
            'province': self.etax_province,
            'province_code': self.etax_province_code,
        }
    
    def get_etax_contact_dict(self):
        return {
            'person_name': self.name,
            'email': self.email,
            'telephone': self.phone,
        }


class MockCompany:
    """Mock company for testing"""
    def __init__(self):
        self.name = 'บริษัท ทดสอบ จำกัด'
        self.etax_tax_id = '0105561234567'
        self.etax_branch_id = '00000'
        self.email = 'company@example.com'
        self.phone = '02-987-6543'
        self.etax_telephone = '02-987-6543'
        self.street = 'ถนนพระราม 9'
        self.zip = '10310'
        self.state_id = MockState()
        self.country_id = MockCountry()
        
        # e-Tax address fields
        self.etax_house_number = '999'
        self.etax_building_number = '999'
        self.etax_building_name = 'อาคารทดสอบ'
        self.etax_floor_number = '10'
        self.etax_room_number = '1001'
        self.etax_village_name = None
        self.etax_moo = None
        self.etax_soi = 'พระราม 9 ซอย 5'
        self.etax_street = 'พระราม 9'
        self.etax_sub_district = 'ห้วยขวาง'
        self.etax_district = 'ห้วยขวาง'
        self.etax_province = 'กรุงเทพมหานคร'
        self.etax_province_code = '10'
        self.etax_postal_code = '10310'


class MockInvoice:
    """Mock invoice for testing"""
    def __init__(self):
        self.name = 'INV/2025/00001'
        self.move_type = 'out_invoice'
        self.state = 'posted'
        self.invoice_date = date(2025, 12, 22)
        self.narration = 'ทดสอบการส่งออก e-Tax'
        self.ref = None
        
        self.company_id = MockCompany()
        self.partner_id = MockPartner()
        self.currency_id = MockCurrency()
        
        # Invoice lines
        self._lines = [
            MockInvoiceLine(1, 'สินค้าทดสอบ A', 10, 100.00),
            MockInvoiceLine(2, 'สินค้าทดสอบ B', 5, 200.00),
            MockInvoiceLine(3, 'บริการทดสอบ', 1, 500.00),
        ]
        
        # Calculate totals
        self.amount_untaxed = sum(l.price_subtotal for l in self._lines)
        self.amount_tax = self.amount_untaxed * 0.07
        self.amount_total = self.amount_untaxed + self.amount_tax
    
    @property
    def invoice_line_ids(self):
        return MockLineCollection(self._lines)


class MockLineCollection:
    """Mock for invoice_line_ids with filtered method"""
    def __init__(self, lines):
        self._lines = lines
    
    def filtered(self, func):
        return [l for l in self._lines if func(l)]
    
    def __iter__(self):
        return iter(self._lines)


def test_xml_generation():
    """Test XML generation with mock invoice"""
    print("=" * 60)
    print("Thailand e-Tax XML Generation Test")
    print("=" * 60)
    
    try:
        from lib.etax_tax_invoice import ETDATaxInvoiceGenerator
        
        # Create mock invoice
        invoice = MockInvoice()
        print(f"\n✓ Created mock invoice: {invoice.name}")
        print(f"  Company: {invoice.company_id.name}")
        print(f"  Customer: {invoice.partner_id.name}")
        print(f"  Amount: {invoice.amount_total:,.2f} THB")
        
        # Create generator
        generator = ETDATaxInvoiceGenerator(invoice)
        print("\n✓ Created ETDATaxInvoiceGenerator")
        
        # Validate
        is_valid = generator.validate()
        if is_valid:
            print("✓ Validation passed")
        else:
            print("✗ Validation failed:")
            for error in generator.errors:
                print(f"  - {error}")
            return False
        
        # Generate XML
        xml_content = generator.generate()
        print("✓ Generated XML content")
        
        # Save to file
        output_file = 'test_output.xml'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        print(f"✓ Saved to {output_file}")
        
        # Print preview
        print("\n" + "-" * 60)
        print("XML Preview (first 2000 chars):")
        print("-" * 60)
        print(xml_content[:2000])
        if len(xml_content) > 2000:
            print(f"\n... (truncated, total {len(xml_content)} chars)")
        
        print("\n" + "=" * 60)
        print("TEST PASSED")
        print("=" * 60)
        return True
        
    except ImportError as e:
        print(f"\n✗ Import error: {e}")
        print("  Make sure lxml is installed: pip install lxml>=4.9.0")
        return False
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_validator():
    """Test validation module"""
    print("\n" + "=" * 60)
    print("Validation Module Test")
    print("=" * 60)
    
    try:
        from lib.etax_validator import ThaiTaxIDValidator, BranchIDValidator
        
        # Test Tax ID validation
        print("\nThai Tax ID Validation:")
        test_ids = [
            ('0105561234567', True),
            ('1234567890123', True),
            ('123456789012', False),  # 12 digits
            ('12345678901234', False),  # 14 digits
            ('TH0105561234567', True),  # With TH prefix (cleaned)
            ('', False),
        ]
        
        for tax_id, expected in test_ids:
            cleaned = ThaiTaxIDValidator.clean(tax_id)
            is_valid, error = ThaiTaxIDValidator.validate(cleaned)
            status = "✓" if is_valid == expected else "✗"
            print(f"  {status} '{tax_id}' -> valid={is_valid} (expected={expected})")
        
        # Test Branch ID validation
        print("\nBranch ID Validation:")
        test_branches = [
            ('00000', True),
            ('00001', True),
            ('12345', True),
            ('1234', False),  # 4 digits
            ('123456', False),  # 6 digits
        ]
        
        for branch_id, expected in test_branches:
            is_valid, error = BranchIDValidator.validate(branch_id)
            status = "✓" if is_valid == expected else "✗"
            print(f"  {status} '{branch_id}' -> valid={is_valid} (expected={expected})")
        
        print("\n✓ Validation tests completed")
        return True
        
    except ImportError as e:
        print(f"\n✗ Import error: {e}")
        return False


if __name__ == '__main__':
    # Run tests
    success = True
    
    success = test_validator() and success
    success = test_xml_generation() and success
    
    sys.exit(0 if success else 1)
