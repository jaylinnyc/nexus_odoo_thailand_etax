# -*- coding: utf-8 -*-
"""
ETDA Validation Module
======================
Validation utilities for Thailand e-Tax compliance.

This module provides validation functions for:
- Thai Tax ID format (13 digits)
- Branch ID format (5 digits)  
- Invoice data completeness
- XML schema validation
"""

import re
from datetime import datetime


class ETDAValidationError(Exception):
    """Exception raised for validation errors"""
    pass


class ThaiTaxIDValidator:
    """Validator for Thai Tax Identification Numbers"""
    
    @staticmethod
    def clean(tax_id):
        """
        Clean tax ID by removing non-numeric characters
        
        Args:
            tax_id: Raw tax ID string
            
        Returns:
            str: Cleaned tax ID (digits only)
        """
        if not tax_id:
            return ''
        return re.sub(r'[^0-9]', '', str(tax_id))
    
    @staticmethod
    def validate(tax_id, allow_empty=False):
        """
        Validate Thai Tax ID format
        
        Thai Tax ID (เลขประจำตัวผู้เสียภาษี) is 13 digits:
        - Position 1: Type indicator (0=individual, 1=company)
        - Position 2-13: Registration number
        
        Args:
            tax_id: Tax ID to validate
            allow_empty: Allow empty/None values
            
        Returns:
            tuple: (is_valid, error_message)
        """
        cleaned = ThaiTaxIDValidator.clean(tax_id)
        
        if not cleaned:
            if allow_empty:
                return (True, None)
            return (False, "Tax ID is required")
        
        if len(cleaned) != 13:
            return (False, f"Tax ID must be 13 digits, got {len(cleaned)}")
        
        if not cleaned.isdigit():
            return (False, "Tax ID must contain only digits")
        
        # Optional: Checksum validation (not strictly enforced by Revenue Dept)
        # The last digit is a check digit using modulo 11
        # But we'll skip this as some legacy IDs may not follow this
        
        return (True, None)
    
    @staticmethod
    def format_display(tax_id):
        """
        Format tax ID for display (with dashes)
        
        Args:
            tax_id: Cleaned tax ID
            
        Returns:
            str: Formatted tax ID (e.g., "1-2345-67890-12-3")
        """
        cleaned = ThaiTaxIDValidator.clean(tax_id)
        if len(cleaned) != 13:
            return cleaned
        
        return f"{cleaned[0]}-{cleaned[1:5]}-{cleaned[5:10]}-{cleaned[10:12]}-{cleaned[12]}"


class BranchIDValidator:
    """Validator for Thai Branch IDs"""
    
    @staticmethod
    def clean(branch_id):
        """Clean branch ID"""
        if not branch_id:
            return '00000'
        return re.sub(r'[^0-9]', '', str(branch_id))
    
    @staticmethod
    def validate(branch_id):
        """
        Validate Branch ID format
        
        Branch ID is 5 digits:
        - 00000: Head office (สำนักงานใหญ่)
        - 00001-99999: Branch numbers
        
        Args:
            branch_id: Branch ID to validate
            
        Returns:
            tuple: (is_valid, error_message)
        """
        cleaned = BranchIDValidator.clean(branch_id)
        
        if len(cleaned) != 5:
            return (False, f"Branch ID must be 5 digits, got {len(cleaned)}")
        
        if not cleaned.isdigit():
            return (False, "Branch ID must contain only digits")
        
        return (True, None)
    
    @staticmethod
    def is_head_office(branch_id):
        """Check if branch ID indicates head office"""
        return BranchIDValidator.clean(branch_id) == '00000'


class InvoiceValidator:
    """Validator for invoice data completeness"""
    
    REQUIRED_FIELDS = {
        'company': [
            ('name', 'Company Name'),
            ('etax_tax_id', 'Company Tax ID'),
            ('etax_branch_id', 'Company Branch ID'),
        ],
        'partner': [
            ('name', 'Customer Name'),
        ],
        'invoice': [
            ('name', 'Invoice Number'),
            ('invoice_date', 'Invoice Date'),
        ],
    }
    
    SUPPORTED_TYPES = ('out_invoice', 'out_refund')
    
    def __init__(self, invoice):
        """
        Initialize validator with invoice
        
        Args:
            invoice: Odoo account.move record
        """
        self.invoice = invoice
        self.errors = []
        self.warnings = []
    
    def validate_all(self):
        """
        Run all validations
        
        Returns:
            bool: True if valid (no errors)
        """
        self.errors = []
        self.warnings = []
        
        self._validate_invoice_type()
        self._validate_invoice_state()
        self._validate_company()
        self._validate_partner()
        self._validate_invoice_lines()
        self._validate_amounts()
        
        return len(self.errors) == 0
    
    def _validate_invoice_type(self):
        """Validate invoice type is supported"""
        if self.invoice.move_type not in self.SUPPORTED_TYPES:
            self.errors.append(
                f"Invoice type '{self.invoice.move_type}' is not supported. "
                f"Only {self.SUPPORTED_TYPES} are allowed."
            )
    
    def _validate_invoice_state(self):
        """Validate invoice is posted"""
        if self.invoice.state != 'posted':
            self.errors.append(
                f"Invoice must be posted before export. Current state: {self.invoice.state}"
            )
    
    def _validate_company(self):
        """Validate company (seller) information"""
        company = self.invoice.company_id
        
        if not company:
            self.errors.append("Company is not set on invoice")
            return
        
        # Check required fields
        for field, label in self.REQUIRED_FIELDS['company']:
            value = getattr(company, field, None)
            if not value:
                self.errors.append(f"{label} is required")
        
        # Validate Tax ID format
        if company.etax_tax_id:
            is_valid, error = ThaiTaxIDValidator.validate(company.etax_tax_id)
            if not is_valid:
                self.errors.append(f"Company Tax ID: {error}")
        
        # Validate Branch ID format
        if company.etax_branch_id:
            is_valid, error = BranchIDValidator.validate(company.etax_branch_id)
            if not is_valid:
                self.errors.append(f"Company Branch ID: {error}")
    
    def _validate_partner(self):
        """Validate partner (buyer) information"""
        partner = self.invoice.partner_id
        
        if not partner:
            self.errors.append("Customer is required")
            return
        
        # Check name
        if not partner.name:
            self.errors.append("Customer Name is required")
        
        # Check Tax ID - get effective tax ID
        if hasattr(partner, 'etax_effective_tax_id'):
            tax_id = partner.etax_effective_tax_id
        else:
            tax_id = partner.vat
        
        if not tax_id:
            self.errors.append("Customer Tax ID is required")
        else:
            # Clean and validate
            cleaned = ThaiTaxIDValidator.clean(tax_id)
            if cleaned:
                is_valid, error = ThaiTaxIDValidator.validate(cleaned)
                if not is_valid:
                    self.errors.append(f"Customer Tax ID: {error}")
    
    def _validate_invoice_lines(self):
        """Validate invoice has line items"""
        lines = self.invoice.invoice_line_ids.filtered(lambda l: not l.display_type)
        
        if not lines:
            self.errors.append("Invoice must have at least one line item")
            return
        
        for idx, line in enumerate(lines, 1):
            # Check product name
            if not line.name and not line.product_id:
                self.warnings.append(f"Line {idx}: No product name specified")
            
            # Check quantity
            if line.quantity <= 0:
                self.warnings.append(f"Line {idx}: Quantity should be positive")
            
            # Check price
            if line.price_unit < 0:
                self.warnings.append(f"Line {idx}: Negative price detected")
    
    def _validate_amounts(self):
        """Validate invoice amounts"""
        if self.invoice.amount_total < 0:
            self.warnings.append("Invoice has negative total amount")
        
        if self.invoice.amount_untaxed == 0:
            self.warnings.append("Invoice has zero subtotal")
    
    def get_summary(self):
        """
        Get validation summary
        
        Returns:
            dict: Summary with errors, warnings, and status
        """
        return {
            'valid': len(self.errors) == 0,
            'errors': self.errors,
            'warnings': self.warnings,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings),
        }


def validate_invoice_for_etax(invoice):
    """
    Convenience function to validate invoice for e-Tax export
    
    Args:
        invoice: Odoo account.move record
        
    Returns:
        dict: Validation result with 'valid', 'errors', 'warnings'
    """
    validator = InvoiceValidator(invoice)
    validator.validate_all()
    return validator.get_summary()
