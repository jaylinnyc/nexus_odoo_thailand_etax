# -*- coding: utf-8 -*-
"""
Unit Tests for ETDA Tax Invoice Generator Module
================================================
Tests for ETDATaxInvoiceGenerator class.
"""

import pytest
import sys
import os
from datetime import date, datetime

# Add lib to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from lxml import etree
    LXML_AVAILABLE = True
except ImportError:
    LXML_AVAILABLE = False

from lib.etax_tax_invoice import ETDATaxInvoiceGenerator, generate_etax_xml
from lib.etax_xml_builder import ETDANamespace


# Mock classes for testing without Odoo
class MockUOM:
    def __init__(self, name='EA'):
        self.name = name


class MockProduct:
    def __init__(self, name='Test Product'):
        self.name = name


class MockTax:
    def __init__(self, amount=7.0, amount_type='percent'):
        self.amount = amount
        self.amount_type = amount_type


class MockCurrency:
    def __init__(self, name='THB'):
        self.name = name


class MockState:
    def __init__(self, name='กรุงเทพมหานคร', code='10'):
        self.name = name
        self.code = code


class MockInvoiceLine:
    def __init__(self, name='Test Product', quantity=1, price_unit=100.0, discount=0):
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
        self.price_total = subtotal * 1.07


class MockLineCollection:
    def __init__(self, lines):
        self._lines = lines
    
    def filtered(self, func):
        return [l for l in self._lines if func(l)]
    
    def __iter__(self):
        return iter(self._lines)


class MockPartner:
    def __init__(self, name='บริษัท ลูกค้า จำกัด', tax_id='0123456789012'):
        self.name = name
        self.vat = 'TH' + tax_id
        self.etax_tax_id = tax_id
        self.etax_branch_id = '00000'
        self.etax_use_vat = False
        self.etax_effective_tax_id = tax_id
        self.email = 'customer@example.com'
        self.phone = '02-123-4567'
        self.mobile = None
        self.street = 'ถนนสุขุมวิท'
        self.zip = '10110'
        self.state_id = MockState()
        
        self.etax_building_number = '123'
        self.etax_soi = 'สุขุมวิท 21'
        self.etax_moo = None
        self.etax_floor_number = None
        self.etax_sub_district = 'คลองเตย'
        self.etax_district = 'คลองเตย'
        self.etax_province = 'กรุงเทพมหานคร'
        self.etax_province_code = '10'
    
    def get_etax_address_dict(self):
        return {
            'postal_code': self.zip,
            'building_number': self.etax_building_number,
            'soi': self.etax_soi,
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
    def __init__(self, name='บริษัท ทดสอบ จำกัด', tax_id='0105561234567'):
        self.name = name
        self.etax_tax_id = tax_id
        self.etax_branch_id = '00000'
        self.email = 'company@example.com'
        self.phone = '02-987-6543'
        self.etax_telephone = '02-987-6543'
        self.street = 'ถนนพระราม 9'
        self.zip = '10310'
        self.state_id = MockState()
        
        self.etax_house_number = '999'
        self.etax_building_number = '999'
        self.etax_building_name = None
        self.etax_floor_number = '10'
        self.etax_room_number = None
        self.etax_village_name = None
        self.etax_moo = None
        self.etax_soi = None
        self.etax_street = 'พระราม 9'
        self.etax_sub_district = 'ห้วยขวาง'
        self.etax_district = 'ห้วยขวาง'
        self.etax_province = 'กรุงเทพมหานคร'
        self.etax_province_code = '10'
        self.etax_postal_code = '10310'


class MockInvoice:
    def __init__(self):
        self.name = 'INV/2025/00001'
        self.move_type = 'out_invoice'
        self.state = 'posted'
        self.invoice_date = date(2025, 12, 22)
        self.narration = None
        self.ref = None
        
        self.company_id = MockCompany()
        self.partner_id = MockPartner()
        self.currency_id = MockCurrency()
        
        self._lines = [
            MockInvoiceLine('สินค้าทดสอบ A', 10, 100.00),
            MockInvoiceLine('สินค้าทดสอบ B', 5, 200.00),
        ]
        
        self.amount_untaxed = sum(l.price_subtotal for l in self._lines)
        self.amount_tax = self.amount_untaxed * 0.07
        self.amount_total = self.amount_untaxed + self.amount_tax
    
    @property
    def invoice_line_ids(self):
        return MockLineCollection(self._lines)


class TestETDATaxInvoiceGenerator:
    """Tests for ETDATaxInvoiceGenerator class"""
    
    def test_document_type_codes(self):
        """Test document type code constants"""
        assert ETDATaxInvoiceGenerator.DOCUMENT_TYPE_CODES['out_invoice'] == '388'
        assert ETDATaxInvoiceGenerator.DOCUMENT_TYPE_CODES['out_refund'] == '381'
    
    def test_document_names(self):
        """Test document name constants"""
        assert ETDATaxInvoiceGenerator.DOCUMENT_NAMES['out_invoice'] == 'ใบกำกับภาษี'
        assert ETDATaxInvoiceGenerator.DOCUMENT_NAMES['out_refund'] == 'ใบลดหนี้'
    
    def test_unit_codes_mapping(self):
        """Test unit code mapping"""
        assert ETDATaxInvoiceGenerator.UNIT_CODES['Units'] == 'EA'
        assert ETDATaxInvoiceGenerator.UNIT_CODES['ชิ้น'] == 'EA'
        assert ETDATaxInvoiceGenerator.UNIT_CODES['kg'] == 'KGM'
    
    def test_init(self):
        """Test generator initialization"""
        invoice = MockInvoice()
        generator = ETDATaxInvoiceGenerator(invoice)
        
        assert generator.invoice == invoice
        assert generator.builder is not None
        assert len(generator._errors) == 0
    
    def test_validate_valid_invoice(self):
        """Test validation passes for valid invoice"""
        invoice = MockInvoice()
        generator = ETDATaxInvoiceGenerator(invoice)
        
        result = generator.validate()
        
        assert result is True
        assert len(generator.errors) == 0
    
    def test_validate_draft_invoice_fails(self):
        """Test validation fails for draft invoice"""
        invoice = MockInvoice()
        invoice.state = 'draft'
        generator = ETDATaxInvoiceGenerator(invoice)
        
        result = generator.validate()
        
        assert result is False
        assert any('posted' in e.lower() for e in generator.errors)
    
    def test_validate_vendor_bill_fails(self):
        """Test validation fails for vendor bill"""
        invoice = MockInvoice()
        invoice.move_type = 'in_invoice'
        generator = ETDATaxInvoiceGenerator(invoice)
        
        result = generator.validate()
        
        assert result is False
    
    def test_validate_missing_company_tax_id(self):
        """Test validation fails when company Tax ID missing"""
        invoice = MockInvoice()
        invoice.company_id.etax_tax_id = None
        generator = ETDATaxInvoiceGenerator(invoice)
        
        result = generator.validate()
        
        assert result is False
        assert any('tax id' in e.lower() for e in generator.errors)
    
    def test_validate_invalid_company_tax_id_length(self):
        """Test validation fails for invalid Tax ID length"""
        invoice = MockInvoice()
        invoice.company_id.etax_tax_id = '12345'  # Too short
        generator = ETDATaxInvoiceGenerator(invoice)
        
        result = generator.validate()
        
        assert result is False
        assert any('13 digits' in e.lower() for e in generator.errors)
    
    def test_validate_missing_partner(self):
        """Test validation fails when partner missing"""
        invoice = MockInvoice()
        invoice.partner_id = None
        generator = ETDATaxInvoiceGenerator(invoice)
        
        result = generator.validate()
        
        assert result is False
        assert any('customer' in e.lower() for e in generator.errors)
    
    def test_validate_no_lines(self):
        """Test validation fails when no invoice lines"""
        invoice = MockInvoice()
        invoice._lines = []
        generator = ETDATaxInvoiceGenerator(invoice)
        
        result = generator.validate()
        
        assert result is False
        assert any('line item' in e.lower() for e in generator.errors)
    
    def test_errors_property(self):
        """Test errors property returns list"""
        invoice = MockInvoice()
        generator = ETDATaxInvoiceGenerator(invoice)
        
        assert isinstance(generator.errors, list)
    
    @pytest.mark.skipif(not LXML_AVAILABLE, reason="lxml not installed")
    def test_generate_returns_string(self):
        """Test generate returns XML string"""
        invoice = MockInvoice()
        generator = ETDATaxInvoiceGenerator(invoice)
        
        xml = generator.generate()
        
        assert isinstance(xml, str)
        assert '<?xml version' in xml
    
    @pytest.mark.skipif(not LXML_AVAILABLE, reason="lxml not installed")
    def test_generate_contains_root_element(self):
        """Test generated XML contains root element"""
        invoice = MockInvoice()
        generator = ETDATaxInvoiceGenerator(invoice)
        
        xml = generator.generate()
        
        assert 'TaxInvoice_CrossIndustryInvoice' in xml
    
    @pytest.mark.skipif(not LXML_AVAILABLE, reason="lxml not installed")
    def test_generate_contains_namespaces(self):
        """Test generated XML contains correct namespaces"""
        invoice = MockInvoice()
        generator = ETDATaxInvoiceGenerator(invoice)
        
        xml = generator.generate()
        
        assert 'xmlns:rsm=' in xml
        assert 'xmlns:ram=' in xml
        assert ETDANamespace.RSM in xml
    
    @pytest.mark.skipif(not LXML_AVAILABLE, reason="lxml not installed")
    def test_generate_contains_document_context(self):
        """Test generated XML contains ExchangedDocumentContext"""
        invoice = MockInvoice()
        generator = ETDATaxInvoiceGenerator(invoice)
        
        xml = generator.generate()
        
        assert 'ExchangedDocumentContext' in xml
        assert 'ER3-2560' in xml
    
    @pytest.mark.skipif(not LXML_AVAILABLE, reason="lxml not installed")
    def test_generate_contains_invoice_id(self):
        """Test generated XML contains invoice ID"""
        invoice = MockInvoice()
        generator = ETDATaxInvoiceGenerator(invoice)
        
        xml = generator.generate()
        
        assert 'INV/2025/00001' in xml
    
    @pytest.mark.skipif(not LXML_AVAILABLE, reason="lxml not installed")
    def test_generate_contains_type_code(self):
        """Test generated XML contains type code 388"""
        invoice = MockInvoice()
        generator = ETDATaxInvoiceGenerator(invoice)
        
        xml = generator.generate()
        
        assert '>388<' in xml or '>388</ram:TypeCode>' in xml
    
    @pytest.mark.skipif(not LXML_AVAILABLE, reason="lxml not installed")
    def test_generate_contains_seller_party(self):
        """Test generated XML contains seller party"""
        invoice = MockInvoice()
        generator = ETDATaxInvoiceGenerator(invoice)
        
        xml = generator.generate()
        
        assert 'SellerTradeParty' in xml
        assert 'บริษัท ทดสอบ จำกัด' in xml
    
    @pytest.mark.skipif(not LXML_AVAILABLE, reason="lxml not installed")
    def test_generate_contains_buyer_party(self):
        """Test generated XML contains buyer party"""
        invoice = MockInvoice()
        generator = ETDATaxInvoiceGenerator(invoice)
        
        xml = generator.generate()
        
        assert 'BuyerTradeParty' in xml
        assert 'บริษัท ลูกค้า จำกัด' in xml
    
    @pytest.mark.skipif(not LXML_AVAILABLE, reason="lxml not installed")
    def test_generate_contains_line_items(self):
        """Test generated XML contains line items"""
        invoice = MockInvoice()
        generator = ETDATaxInvoiceGenerator(invoice)
        
        xml = generator.generate()
        
        assert 'IncludedSupplyChainTradeLineItem' in xml
        assert 'สินค้าทดสอบ A' in xml
        assert 'สินค้าทดสอบ B' in xml
    
    @pytest.mark.skipif(not LXML_AVAILABLE, reason="lxml not installed")
    def test_generate_contains_totals(self):
        """Test generated XML contains monetary totals"""
        invoice = MockInvoice()
        generator = ETDATaxInvoiceGenerator(invoice)
        
        xml = generator.generate()
        
        assert 'SpecifiedTradeSettlementHeaderMonetarySummation' in xml
        assert 'GrandTotalAmount' in xml
    
    @pytest.mark.skipif(not LXML_AVAILABLE, reason="lxml not installed")
    def test_generate_credit_note(self):
        """Test generating credit note XML"""
        invoice = MockInvoice()
        invoice.move_type = 'out_refund'
        invoice.ref = 'Return of goods'
        generator = ETDATaxInvoiceGenerator(invoice)
        
        xml = generator.generate()
        
        assert 'CreditNote_CrossIndustryInvoice' in xml
        assert '>381<' in xml or '>381</ram:TypeCode>' in xml
    
    @pytest.mark.skipif(not LXML_AVAILABLE, reason="lxml not installed")
    def test_generate_with_notes(self):
        """Test generating XML with notes"""
        invoice = MockInvoice()
        invoice.narration = 'Test note content'
        generator = ETDATaxInvoiceGenerator(invoice)
        
        xml = generator.generate()
        
        assert 'IncludedNote' in xml
        assert 'Test note content' in xml
    
    def test_generate_invalid_invoice_raises(self):
        """Test generate raises for invalid invoice"""
        invoice = MockInvoice()
        invoice.state = 'draft'
        generator = ETDATaxInvoiceGenerator(invoice)
        
        with pytest.raises(ValueError) as exc_info:
            generator.generate()
        
        assert 'Validation failed' in str(exc_info.value)


@pytest.mark.skipif(not LXML_AVAILABLE, reason="lxml not installed")
class TestGenerateEtaxXml:
    """Tests for generate_etax_xml convenience function"""
    
    def test_returns_string(self):
        """Test function returns XML string"""
        invoice = MockInvoice()
        xml = generate_etax_xml(invoice)
        
        assert isinstance(xml, str)
        assert '<?xml version' in xml
    
    def test_generates_valid_xml(self):
        """Test function generates parseable XML"""
        invoice = MockInvoice()
        xml = generate_etax_xml(invoice)
        
        # Try to parse the generated XML
        root = etree.fromstring(xml.encode('utf-8'))
        assert root is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
