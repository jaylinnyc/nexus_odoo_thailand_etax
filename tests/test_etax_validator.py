# -*- coding: utf-8 -*-
"""
Unit Tests for ETDA Validator Module
====================================
Tests for Thai Tax ID, Branch ID, and Invoice validation.
"""

import pytest
import sys
import os

# Add lib to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from lib.etax_validator import (
    ThaiTaxIDValidator,
    BranchIDValidator,
    InvoiceValidator,
    validate_invoice_for_etax,
)


class TestThaiTaxIDValidator:
    """Tests for ThaiTaxIDValidator class"""
    
    def test_clean_removes_dashes(self):
        """Test that clean removes dashes from Tax ID"""
        assert ThaiTaxIDValidator.clean('0-1055-61234-56-7') == '0105561234567'
    
    def test_clean_removes_spaces(self):
        """Test that clean removes spaces from Tax ID"""
        assert ThaiTaxIDValidator.clean('0105561234567 ') == '0105561234567'
    
    def test_clean_removes_th_prefix(self):
        """Test that clean handles TH prefix"""
        # Note: clean only removes non-numeric chars, so TH gets removed
        assert ThaiTaxIDValidator.clean('TH0105561234567') == '0105561234567'
    
    def test_clean_empty_string(self):
        """Test that clean handles empty string"""
        assert ThaiTaxIDValidator.clean('') == ''
    
    def test_clean_none(self):
        """Test that clean handles None"""
        assert ThaiTaxIDValidator.clean(None) == ''
    
    def test_validate_valid_13_digits(self):
        """Test validation of valid 13-digit Tax ID"""
        is_valid, error = ThaiTaxIDValidator.validate('0105561234567')
        assert is_valid is True
        assert error is None
    
    def test_validate_12_digits_fails(self):
        """Test validation fails for 12 digits"""
        is_valid, error = ThaiTaxIDValidator.validate('012345678901')
        assert is_valid is False
        assert '13 digits' in error
    
    def test_validate_14_digits_fails(self):
        """Test validation fails for 14 digits"""
        is_valid, error = ThaiTaxIDValidator.validate('01234567890123')
        assert is_valid is False
        assert '13 digits' in error
    
    def test_validate_empty_fails(self):
        """Test validation fails for empty Tax ID"""
        is_valid, error = ThaiTaxIDValidator.validate('')
        assert is_valid is False
        assert 'required' in error.lower()
    
    def test_validate_empty_allowed(self):
        """Test validation passes for empty when allow_empty=True"""
        is_valid, error = ThaiTaxIDValidator.validate('', allow_empty=True)
        assert is_valid is True
        assert error is None
    
    def test_format_display(self):
        """Test display format with dashes"""
        formatted = ThaiTaxIDValidator.format_display('0105561234567')
        assert formatted == '0-1055-61234-56-7'
    
    def test_format_display_invalid_length(self):
        """Test display format returns original if not 13 digits"""
        formatted = ThaiTaxIDValidator.format_display('123')
        assert formatted == '123'


class TestBranchIDValidator:
    """Tests for BranchIDValidator class"""
    
    def test_clean_returns_default_for_none(self):
        """Test that clean returns 00000 for None"""
        assert BranchIDValidator.clean(None) == '00000'
    
    def test_clean_returns_default_for_empty(self):
        """Test that clean returns 00000 for empty string"""
        assert BranchIDValidator.clean('') == '00000'
    
    def test_clean_removes_non_numeric(self):
        """Test that clean removes non-numeric characters"""
        assert BranchIDValidator.clean('00-001') == '00001'
    
    def test_validate_valid_5_digits(self):
        """Test validation of valid 5-digit Branch ID"""
        is_valid, error = BranchIDValidator.validate('00000')
        assert is_valid is True
        assert error is None
    
    def test_validate_4_digits_fails(self):
        """Test validation fails for 4 digits"""
        is_valid, error = BranchIDValidator.validate('0000')
        assert is_valid is False
        assert '5 digits' in error
    
    def test_validate_6_digits_fails(self):
        """Test validation fails for 6 digits"""
        is_valid, error = BranchIDValidator.validate('000001')
        assert is_valid is False
        assert '5 digits' in error
    
    def test_is_head_office_00000(self):
        """Test head office detection for 00000"""
        assert BranchIDValidator.is_head_office('00000') is True
    
    def test_is_head_office_00001(self):
        """Test head office detection for 00001"""
        assert BranchIDValidator.is_head_office('00001') is False
    
    def test_is_head_office_cleaned(self):
        """Test head office detection with cleaning"""
        assert BranchIDValidator.is_head_office('00-000') is True


class TestInvoiceValidator:
    """Tests for InvoiceValidator class"""
    
    class MockCompany:
        def __init__(self, name='Test Co', tax_id='0105561234567', branch_id='00000'):
            self.name = name
            self.etax_tax_id = tax_id
            self.etax_branch_id = branch_id
    
    class MockPartner:
        def __init__(self, name='Customer', tax_id='1234567890123'):
            self.name = name
            self.vat = tax_id
            self.etax_effective_tax_id = tax_id
    
    class MockLine:
        def __init__(self, name='Product', qty=1, price=100):
            self.name = name
            self.quantity = qty
            self.price_unit = price
            self.display_type = False
            self.product_id = type('obj', (object,), {'name': name})()
    
    class MockInvoice:
        def __init__(self):
            self.move_type = 'out_invoice'
            self.state = 'posted'
            self.name = 'INV/001'
            self.invoice_date = '2025-12-22'
            self.company_id = TestInvoiceValidator.MockCompany()
            self.partner_id = TestInvoiceValidator.MockPartner()
            self._lines = [TestInvoiceValidator.MockLine()]
            self.amount_total = 107.0
            self.amount_untaxed = 100.0
        
        @property
        def invoice_line_ids(self):
            class MockCollection:
                def __init__(self, lines):
                    self._lines = lines
                def filtered(self, func):
                    return [l for l in self._lines if func(l)]
            return MockCollection(self._lines)
    
    def test_validate_all_valid_invoice(self):
        """Test validation passes for valid invoice"""
        invoice = self.MockInvoice()
        validator = InvoiceValidator(invoice)
        
        result = validator.validate_all()
        
        assert result is True
        assert len(validator.errors) == 0
    
    def test_validate_draft_invoice_fails(self):
        """Test validation fails for draft invoice"""
        invoice = self.MockInvoice()
        invoice.state = 'draft'
        validator = InvoiceValidator(invoice)
        
        result = validator.validate_all()
        
        assert result is False
        assert any('posted' in e.lower() for e in validator.errors)
    
    def test_validate_wrong_type_fails(self):
        """Test validation fails for wrong invoice type"""
        invoice = self.MockInvoice()
        invoice.move_type = 'in_invoice'  # Vendor bill
        validator = InvoiceValidator(invoice)
        
        result = validator.validate_all()
        
        assert result is False
        assert any('not supported' in e.lower() for e in validator.errors)
    
    def test_validate_missing_company_tax_id(self):
        """Test validation fails when company Tax ID missing"""
        invoice = self.MockInvoice()
        invoice.company_id.etax_tax_id = None
        validator = InvoiceValidator(invoice)
        
        result = validator.validate_all()
        
        assert result is False
        assert any('company tax id' in e.lower() for e in validator.errors)
    
    def test_validate_missing_partner(self):
        """Test validation fails when partner missing"""
        invoice = self.MockInvoice()
        invoice.partner_id = None
        validator = InvoiceValidator(invoice)
        
        result = validator.validate_all()
        
        assert result is False
        assert any('customer' in e.lower() for e in validator.errors)
    
    def test_validate_missing_lines(self):
        """Test validation fails when no invoice lines"""
        invoice = self.MockInvoice()
        invoice._lines = []
        validator = InvoiceValidator(invoice)
        
        result = validator.validate_all()
        
        assert result is False
        assert any('line item' in e.lower() for e in validator.errors)
    
    def test_validate_get_summary(self):
        """Test get_summary returns correct structure"""
        invoice = self.MockInvoice()
        validator = InvoiceValidator(invoice)
        validator.validate_all()
        
        summary = validator.get_summary()
        
        assert 'valid' in summary
        assert 'errors' in summary
        assert 'warnings' in summary
        assert 'error_count' in summary
        assert 'warning_count' in summary


class TestValidateInvoiceForEtax:
    """Tests for validate_invoice_for_etax convenience function"""
    
    def test_returns_dict(self):
        """Test function returns dictionary"""
        invoice = TestInvoiceValidator.MockInvoice()
        result = validate_invoice_for_etax(invoice)
        
        assert isinstance(result, dict)
        assert 'valid' in result


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
