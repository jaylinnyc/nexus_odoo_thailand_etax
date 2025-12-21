# -*- coding: utf-8 -*-
"""
Unit Tests for ETDA XML Builder Module
======================================
Tests for ETDANamespace and ETDAXMLBuilder classes.
"""

import pytest
import sys
import os

# Add lib to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from lxml import etree
    LXML_AVAILABLE = True
except ImportError:
    LXML_AVAILABLE = False

from lib.etax_xml_builder import ETDANamespace, ETDAXMLBuilder


class TestETDANamespace:
    """Tests for ETDANamespace class"""
    
    def test_rsm_namespace(self):
        """Test RSM namespace is correct"""
        assert ETDANamespace.RSM == "urn:etda:uncefact:data:standard:TaxInvoice_CrossIndustryInvoice:2"
    
    def test_ram_namespace(self):
        """Test RAM namespace is correct"""
        assert ETDANamespace.RAM == "urn:etda:uncefact:data:standard:TaxInvoice_ReusableAggregateBusinessInformationEntity:2"
    
    def test_ds_namespace(self):
        """Test DS namespace is correct"""
        assert ETDANamespace.DS == "http://www.w3.org/2000/09/xmldsig#"
    
    def test_xades_namespace(self):
        """Test XADES namespace is correct"""
        assert ETDANamespace.XADES == "http://uri.etsi.org/01903/v1.3.2#"
    
    def test_get_nsmap(self):
        """Test get_nsmap returns correct mapping"""
        nsmap = ETDANamespace.get_nsmap()
        
        assert 'rsm' in nsmap
        assert 'ram' in nsmap
        assert 'ns3' in nsmap
        assert nsmap['rsm'] == ETDANamespace.RSM
        assert nsmap['ram'] == ETDANamespace.RAM
    
    def test_get_nsmap_with_xades(self):
        """Test get_nsmap_with_xades includes xades"""
        nsmap = ETDANamespace.get_nsmap_with_xades()
        
        assert 'xades' in nsmap
        assert nsmap['xades'] == ETDANamespace.XADES


@pytest.mark.skipif(not LXML_AVAILABLE, reason="lxml not installed")
class TestETDAXMLBuilder:
    """Tests for ETDAXMLBuilder class"""
    
    def test_init(self):
        """Test builder initialization"""
        builder = ETDAXMLBuilder()
        assert builder.root is None
        assert builder.nsmap is not None
    
    def test_create_root_tax_invoice(self):
        """Test creating TaxInvoice root element"""
        builder = ETDAXMLBuilder()
        root = builder.create_root('TaxInvoice')
        
        assert root is not None
        assert 'TaxInvoice_CrossIndustryInvoice' in root.tag
        assert ETDANamespace.RSM in root.tag
    
    def test_create_root_credit_note(self):
        """Test creating CreditNote root element"""
        builder = ETDAXMLBuilder()
        root = builder.create_root('CreditNote')
        
        assert 'CreditNote_CrossIndustryInvoice' in root.tag
    
    def test_create_element_with_text(self):
        """Test creating element with text content"""
        builder = ETDAXMLBuilder()
        elem = builder.create_element('TestElement', text='Hello')
        
        assert elem.text == 'Hello'
    
    def test_create_element_with_attributes(self):
        """Test creating element with attributes"""
        builder = ETDAXMLBuilder()
        elem = builder.create_element('TestElement', attrib={'id': '123'})
        
        assert elem.get('id') == '123'
    
    def test_create_element_with_namespace(self):
        """Test creating element with namespace"""
        builder = ETDAXMLBuilder()
        elem = builder.create_element('Name', namespace='ram')
        
        assert ETDANamespace.RAM in elem.tag
    
    def test_append_element(self):
        """Test appending element to parent"""
        builder = ETDAXMLBuilder()
        builder.create_root()
        
        child = builder.append_element(builder.root, 'Child', text='test')
        
        assert child.getparent() == builder.root
        assert child.text == 'test'
    
    def test_create_document_context(self):
        """Test creating ExchangedDocumentContext"""
        builder = ETDAXMLBuilder()
        context = builder.create_document_context()
        
        assert context is not None
        # Check for GuidelineSpecifiedDocumentContextParameter
        param = context.find('.//{%s}GuidelineSpecifiedDocumentContextParameter' % ETDANamespace.RAM)
        assert param is not None
    
    def test_create_document_context_with_guideline(self):
        """Test creating context with specific guideline"""
        builder = ETDAXMLBuilder()
        context = builder.create_document_context(guideline_id='ER3-2560', scheme_version='v2.0')
        
        id_elem = context.find('.//{%s}ID' % ETDANamespace.RAM)
        assert id_elem is not None
        assert id_elem.text == 'ER3-2560'
        assert id_elem.get('schemeAgencyID') == 'ETDA'
        assert id_elem.get('schemeVersionID') == 'v2.0'
    
    def test_create_exchanged_document(self):
        """Test creating ExchangedDocument"""
        builder = ETDAXMLBuilder()
        from datetime import datetime
        
        doc = builder.create_exchanged_document(
            invoice_id='INV/001',
            invoice_name='ใบกำกับภาษี',
            type_code='388',
            issue_datetime=datetime(2025, 12, 22, 10, 30, 0)
        )
        
        assert doc is not None
        
        # Check ID
        id_elem = doc.find('.//{%s}ID' % ETDANamespace.RAM)
        assert id_elem is not None
        assert id_elem.text == 'INV/001'
        
        # Check Name
        name_elem = doc.find('.//{%s}Name' % ETDANamespace.RAM)
        assert name_elem is not None
        assert name_elem.text == 'ใบกำกับภาษี'
        
        # Check TypeCode
        type_elem = doc.find('.//{%s}TypeCode' % ETDANamespace.RAM)
        assert type_elem is not None
        assert type_elem.text == '388'
    
    def test_create_trade_party(self):
        """Test creating TradeParty element"""
        builder = ETDAXMLBuilder()
        
        party = builder.create_trade_party(
            name='บริษัท ทดสอบ จำกัด',
            tax_id='0105561234567',
            branch_id='00000'
        )
        
        assert party is not None
        
        # Check name
        name_elem = party.find('.//{%s}Name' % ETDANamespace.RAM)
        assert name_elem is not None
        
        # Check tax registration
        tax_reg = party.find('.//{%s}SpecifiedTaxRegistration' % ETDANamespace.RAM)
        assert tax_reg is not None
    
    def test_create_trade_party_with_address(self):
        """Test creating TradeParty with address"""
        builder = ETDAXMLBuilder()
        
        address = {
            'postal_code': '10310',
            'building_number': '999',
            'street': 'พระราม 9',
            'district': 'ห้วยขวาง',
            'province': 'กรุงเทพมหานคร',
        }
        
        party = builder.create_trade_party(
            name='Test Company',
            tax_id='0105561234567',
            branch_id='00000',
            address=address
        )
        
        # Check postal address exists
        addr_elem = party.find('.//{%s}PostalTradeAddress' % ETDANamespace.RAM)
        assert addr_elem is not None
        
        # Check postal code
        postcode = addr_elem.find('.//{%s}PostcodeCode' % ETDANamespace.RAM)
        assert postcode is not None
        assert postcode.text == '10310'
    
    def test_create_trade_tax(self):
        """Test creating ApplicableTradeTax element"""
        builder = ETDAXMLBuilder()
        
        tax = builder.create_trade_tax(
            type_code='VAT',
            rate=7.0,
            basis_amount=1000.0,
            calculated_amount=70.0
        )
        
        assert tax is not None
        
        # Check type code
        type_elem = tax.find('.//{%s}TypeCode' % ETDANamespace.RAM)
        assert type_elem is not None
        assert type_elem.text == 'VAT'
        
        # Check calculated amount
        calc_elem = tax.find('.//{%s}CalculatedAmount' % ETDANamespace.RAM)
        assert calc_elem is not None
        assert calc_elem.text == '70.00'
    
    def test_create_monetary_summation(self):
        """Test creating MonetarySummation element"""
        builder = ETDAXMLBuilder()
        
        summation = builder.create_monetary_summation(
            line_total=1000.0,
            tax_basis=1000.0,
            tax_total=70.0,
            grand_total=1070.0
        )
        
        assert summation is not None
        
        # Check grand total
        grand = summation.find('.//{%s}GrandTotalAmount' % ETDANamespace.RAM)
        assert grand is not None
        assert grand.text == '1070.00'
    
    def test_create_line_item(self):
        """Test creating IncludedSupplyChainTradeLineItem"""
        builder = ETDAXMLBuilder()
        
        tax_info = {
            'type_code': 'VAT',
            'rate': 7.0,
            'basis_amount': 100.0,
            'calculated_amount': 7.0,
        }
        
        line_totals = {
            'net_total': 100.0,
            'tax_amount': 7.0,
            'net_with_tax': 107.0,
            'currency': 'THB',
        }
        
        line = builder.create_line_item(
            line_id=1,
            product_name='Test Product',
            quantity=10,
            unit_code='EA',
            price_per_unit=10.0,
            tax_info=tax_info,
            line_totals=line_totals
        )
        
        assert line is not None
        
        # Check line ID
        line_doc = line.find('.//{%s}AssociatedDocumentLineDocument' % ETDANamespace.RAM)
        assert line_doc is not None
        line_id_elem = line_doc.find('.//{%s}LineID' % ETDANamespace.RAM)
        assert line_id_elem.text == '1'
        
        # Check product name
        product = line.find('.//{%s}SpecifiedTradeProduct' % ETDANamespace.RAM)
        name_elem = product.find('.//{%s}Name' % ETDANamespace.RAM)
        assert name_elem.text == 'Test Product'
    
    def test_to_string(self):
        """Test converting XML to string"""
        builder = ETDAXMLBuilder()
        builder.create_root()
        
        xml_bytes = builder.to_string(pretty_print=True, xml_declaration=True)
        
        assert isinstance(xml_bytes, bytes)
        assert b'<?xml version' in xml_bytes
        assert b'TaxInvoice_CrossIndustryInvoice' in xml_bytes
    
    def test_to_string_without_root_raises(self):
        """Test to_string raises when no root"""
        builder = ETDAXMLBuilder()
        
        with pytest.raises(ValueError):
            builder.to_string()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
