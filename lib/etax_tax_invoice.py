# -*- coding: utf-8 -*-
"""
ETDA Tax Invoice Generator
==========================
High-level interface for generating ETDA-compliant Tax Invoice XML documents
from Odoo invoice records.

This module bridges Odoo's account.move model with the low-level ETDAXMLBuilder,
translating Odoo data structures into the ETDA XML format.
"""

from datetime import datetime
from .etax_xml_builder import ETDAXMLBuilder, ETDANamespace


class ETDATaxInvoiceGenerator:
    """
    Generator class for creating ETDA-compliant Tax Invoice XML from Odoo invoices.
    
    Usage:
        generator = ETDATaxInvoiceGenerator(invoice)
        xml_content = generator.generate()
    """
    
    # Document type codes according to ETDA
    DOCUMENT_TYPE_CODES = {
        'out_invoice': '388',      # Tax Invoice
        'out_refund': '381',       # Credit Note
        'in_invoice': '380',       # Commercial Invoice (for reference)
        'debit_note': '383',       # Debit Note
    }
    
    # Thai document names
    DOCUMENT_NAMES = {
        'out_invoice': 'ใบกำกับภาษี',           # Tax Invoice
        'out_refund': 'ใบลดหนี้',               # Credit Note  
        'debit_note': 'ใบเพิ่มหนี้',            # Debit Note
    }
    
    # Unit code mapping (common Thai units)
    UNIT_CODES = {
        'Units': 'EA',
        'pieces': 'EA',
        'units': 'EA',
        'ชิ้น': 'EA',
        'hours': 'HUR',
        'ชั่วโมง': 'HUR',
        'days': 'DAY',
        'วัน': 'DAY',
        'liters': 'LTR',
        'ลิตร': 'LTR',
        'kg': 'KGM',
        'กิโลกรัม': 'KGM',
        'meters': 'MTR',
        'เมตร': 'MTR',
        'boxes': 'BX',
        'กล่อง': 'BX',
        'packs': 'PK',
        'แพ็ค': 'PK',
        'sets': 'SET',
        'ชุด': 'SET',
    }
    
    def __init__(self, invoice):
        """
        Initialize generator with Odoo invoice record
        
        Args:
            invoice: account.move record (Odoo model)
        """
        self.invoice = invoice
        self.builder = ETDAXMLBuilder()
        self._errors = []
        
    def validate(self):
        """
        Validate invoice data for ETDA compliance
        
        Returns:
            bool: True if valid, False otherwise
        """
        self._errors = []
        
        # Check invoice type
        if self.invoice.move_type not in ('out_invoice', 'out_refund'):
            self._errors.append("Only customer invoices and credit notes are supported")
        
        # Check invoice state
        if self.invoice.state != 'posted':
            self._errors.append("Invoice must be posted")
        
        # Check seller (company) info
        company = self.invoice.company_id
        if not company.etax_tax_id:
            self._errors.append("Company Tax ID is required")
        elif len(company.etax_tax_id.replace('-', '').replace(' ', '')) != 13:
            self._errors.append("Company Tax ID must be 13 digits")
        
        if not company.etax_branch_id:
            self._errors.append("Company Branch ID is required")
        
        # Check buyer (partner) info
        partner = self.invoice.partner_id
        if not partner:
            self._errors.append("Customer is required")
        else:
            tax_id = partner.etax_effective_tax_id if hasattr(partner, 'etax_effective_tax_id') else partner.vat
            if not tax_id:
                self._errors.append("Customer Tax ID is required")
        
        # Check invoice lines
        if not self.invoice.invoice_line_ids:
            self._errors.append("Invoice must have at least one line item")
        
        return len(self._errors) == 0
    
    @property
    def errors(self):
        """Get validation errors"""
        return self._errors
    
    def generate(self):
        """
        Generate ETDA-compliant XML document
        
        Returns:
            str: XML document as UTF-8 string
            
        Raises:
            ValueError: If validation fails
        """
        if not self.validate():
            raise ValueError("Validation failed: " + "; ".join(self._errors))
        
        # Create root element
        doc_type = 'TaxInvoice' if self.invoice.move_type == 'out_invoice' else 'CreditNote'
        self.builder.create_root(document_type=doc_type)
        
        # Add ExchangedDocumentContext
        context = self._create_document_context()
        self.builder.root.append(context)
        
        # Add ExchangedDocument
        doc = self._create_exchanged_document()
        self.builder.root.append(doc)
        
        # Add SupplyChainTradeTransaction
        transaction = self._create_trade_transaction()
        self.builder.root.append(transaction)
        
        # Return as string (decoded from bytes)
        xml_bytes = self.builder.to_string(pretty_print=True, xml_declaration=True)
        return xml_bytes.decode('utf-8')
    
    def _create_document_context(self):
        """Create ExchangedDocumentContext section"""
        # Use ER3-2560 guideline (current ETDA standard)
        return self.builder.create_document_context(
            guideline_id='ER3-2560',
            scheme_version='v2.0'
        )
    
    def _create_exchanged_document(self):
        """Create ExchangedDocument section (invoice header)"""
        invoice = self.invoice
        
        # Determine document type code
        type_code = self.DOCUMENT_TYPE_CODES.get(invoice.move_type, '388')
        
        # Determine document name
        doc_name = self.DOCUMENT_NAMES.get(invoice.move_type, 'ใบกำกับภาษี')
        
        # Use invoice date/time or current datetime
        issue_datetime = datetime.combine(
            invoice.invoice_date,
            datetime.min.time()
        ) if invoice.invoice_date else datetime.now()
        
        # Build notes list
        notes = []
        if invoice.narration:
            notes.append({
                'subject': 'หมายเหตุ',
                'content': invoice.narration
            })
        
        # Purpose for credit notes
        purpose = None
        if invoice.move_type == 'out_refund':
            purpose = invoice.ref or 'ปรับปรุงราคา'
        
        return self.builder.create_exchanged_document(
            invoice_id=invoice.name,
            invoice_name=doc_name,
            type_code=type_code,
            issue_datetime=issue_datetime,
            purpose=purpose,
            notes=notes if notes else None
        )
    
    def _create_trade_transaction(self):
        """Create SupplyChainTradeTransaction section"""
        transaction = self.builder.create_element('SupplyChainTradeTransaction')
        
        # Header Trade Agreement (parties)
        agreement = self._create_header_trade_agreement()
        transaction.append(agreement)
        
        # Header Trade Delivery
        delivery = self._create_header_trade_delivery()
        transaction.append(delivery)
        
        # Header Trade Settlement (totals and taxes)
        settlement = self._create_header_trade_settlement()
        transaction.append(settlement)
        
        # Line Items
        for line_number, line in enumerate(self.invoice.invoice_line_ids.filtered(lambda l: not l.display_type), 1):
            line_item = self._create_line_item(line, line_number)
            transaction.append(line_item)
        
        return transaction
    
    def _create_header_trade_agreement(self):
        """Create ApplicableHeaderTradeAgreement with seller and buyer"""
        agreement = self.builder.create_element('ApplicableHeaderTradeAgreement')
        
        # Seller (Company)
        seller = self._create_seller_party()
        seller_wrapper = self.builder.create_element('SellerTradeParty')
        for child in seller:
            seller_wrapper.append(child)
        agreement.append(seller_wrapper)
        
        # Buyer (Customer)  
        buyer = self._create_buyer_party()
        buyer_wrapper = self.builder.create_element('BuyerTradeParty')
        for child in buyer:
            buyer_wrapper.append(child)
        agreement.append(buyer_wrapper)
        
        return agreement
    
    def _create_seller_party(self):
        """Create seller TradeParty from company"""
        company = self.invoice.company_id
        
        # Clean tax ID (remove dashes and spaces)
        tax_id = company.etax_tax_id.replace('-', '').replace(' ', '')
        branch_id = company.etax_branch_id or '00000'
        
        # Build address dictionary
        address = {
            'postal_code': company.etax_postal_code or company.zip or '',
            'building_number': company.etax_building_number or company.etax_house_number or '',
            'street': company.etax_street or company.street or '',
            'soi': company.etax_soi or '',
            'moo': company.etax_moo or '',
            'floor': company.etax_floor_number or '',
            'sub_district': company.etax_sub_district or '',
            'district': company.etax_district or '',
            'province': company.etax_province or (company.state_id.name if company.state_id else ''),
            'province_code': company.etax_province_code or (company.state_id.code if company.state_id else ''),
        }
        
        # Build contact dictionary
        contact = {
            'person_name': company.name,
            'email': company.email or '',
            'telephone': company.etax_telephone or company.phone or '',
        }
        
        return self.builder.create_trade_party(
            name=company.name,
            tax_id=tax_id,
            branch_id=branch_id,
            contact=contact if any(contact.values()) else None,
            address=address if any(address.values()) else None
        )
    
    def _create_buyer_party(self):
        """Create buyer TradeParty from partner"""
        partner = self.invoice.partner_id
        
        # Get tax ID
        if hasattr(partner, 'etax_effective_tax_id') and partner.etax_effective_tax_id:
            tax_id = partner.etax_effective_tax_id.replace('-', '').replace(' ', '')
        else:
            tax_id = (partner.vat or '').replace('-', '').replace(' ', '')
            # Remove TH prefix if present
            if tax_id.upper().startswith('TH'):
                tax_id = tax_id[2:]
        
        # Get branch ID
        branch_id = getattr(partner, 'etax_branch_id', None) or '00000'
        
        # Build address - use e-Tax helper method if available
        if hasattr(partner, 'get_etax_address_dict'):
            address = partner.get_etax_address_dict()
        else:
            address = {
                'postal_code': partner.zip or '',
                'street': partner.street or '',
                'province': partner.state_id.name if partner.state_id else '',
            }
        
        # Build contact - use e-Tax helper method if available
        if hasattr(partner, 'get_etax_contact_dict'):
            contact = partner.get_etax_contact_dict()
        else:
            contact = {
                'person_name': partner.name,
                'email': partner.email or '',
                'telephone': partner.phone or partner.mobile or '',
            }
        
        return self.builder.create_trade_party(
            name=partner.name,
            tax_id=tax_id,
            branch_id=branch_id,
            contact=contact if contact and any(contact.values()) else None,
            address=address if address and any(address.values()) else None
        )
    
    def _create_header_trade_delivery(self):
        """Create ApplicableHeaderTradeDelivery"""
        delivery = self.builder.create_element('ApplicableHeaderTradeDelivery')
        
        # Ship-to party (same as buyer for now)
        ship_to = self.builder.create_element('ShipToTradeParty')
        self.builder.append_element(ship_to, 'Name', self.invoice.partner_id.name)
        delivery.append(ship_to)
        
        return delivery
    
    def _create_header_trade_settlement(self):
        """Create ApplicableHeaderTradeSettlement with taxes and totals"""
        settlement = self.builder.create_element('ApplicableHeaderTradeSettlement')
        
        # Currency
        currency_code = self.invoice.currency_id.name or 'THB'
        self.builder.append_element(settlement, 'InvoiceCurrencyCode', currency_code)
        
        # Tax summary
        tax_summary = self._create_tax_summary()
        settlement.append(tax_summary)
        
        # Monetary summation
        summation = self.builder.create_monetary_summation(
            line_total=float(self.invoice.amount_untaxed),
            tax_basis=float(self.invoice.amount_untaxed),
            tax_total=float(self.invoice.amount_tax),
            grand_total=float(self.invoice.amount_total)
        )
        settlement.append(summation)
        
        return settlement
    
    def _create_tax_summary(self):
        """Create ApplicableTradeTax summary"""
        # For Thai VAT, standard rate is 7%
        # Get actual tax from invoice lines
        
        tax_amount = float(self.invoice.amount_tax)
        tax_basis = float(self.invoice.amount_untaxed)
        
        # Calculate effective rate
        if tax_basis > 0:
            effective_rate = (tax_amount / tax_basis) * 100
        else:
            effective_rate = 7.0  # Default VAT rate
        
        return self.builder.create_trade_tax(
            type_code='VAT',
            rate=effective_rate,
            basis_amount=tax_basis,
            calculated_amount=tax_amount
        )
    
    def _create_line_item(self, line, line_number):
        """Create IncludedSupplyChainTradeLineItem from invoice line"""
        # Get product name
        product_name = line.name or (line.product_id.name if line.product_id else f'Line {line_number}')
        
        # Get unit code
        unit_name = line.product_uom_id.name if line.product_uom_id else 'EA'
        unit_code = self.UNIT_CODES.get(unit_name, 'EA')
        
        # Calculate line amounts
        quantity = float(line.quantity)
        price_unit = float(line.price_unit)
        
        # Calculate tax for this line
        line_subtotal = float(line.price_subtotal)  # Without tax
        line_total = float(line.price_total)  # With tax
        line_tax = line_total - line_subtotal
        
        # Tax rate from line taxes
        tax_rate = 7.0  # Default VAT
        if line.tax_ids:
            # Get first tax rate
            tax = line.tax_ids[0]
            if tax.amount_type == 'percent':
                tax_rate = float(tax.amount)
        
        # Tax info
        tax_info = {
            'type_code': 'VAT',
            'rate': tax_rate,
            'basis_amount': line_subtotal,
            'calculated_amount': line_tax,
        }
        
        # Line totals
        line_totals = {
            'net_total': line_subtotal,
            'tax_amount': line_tax,
            'net_with_tax': line_total,
            'currency': self.invoice.currency_id.name or 'THB',
            'discount_amount': float(line.discount * line.price_unit * quantity / 100) if line.discount else 0,
        }
        
        return self.builder.create_line_item(
            line_id=line_number,
            product_name=product_name,
            quantity=quantity,
            unit_code=unit_code,
            price_per_unit=price_unit,
            tax_info=tax_info,
            line_totals=line_totals
        )


def generate_etax_xml(invoice):
    """
    Convenience function to generate e-Tax XML from an Odoo invoice
    
    Args:
        invoice: account.move record
        
    Returns:
        str: XML content as UTF-8 string
    """
    generator = ETDATaxInvoiceGenerator(invoice)
    return generator.generate()
