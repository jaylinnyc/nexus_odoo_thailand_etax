# -*- coding: utf-8 -*-
"""
ETDA XML Builder
================
Core XML generation engine for Thailand e-Tax compliance.

This module provides the foundation for creating ETDA-compliant XML documents
according to the UN/CEFACT Cross Industry Invoice standard with Thai extensions.

Reference: soda-etax repository (https://github.com/ETDA/soda-etax)
"""

try:
    from lxml import etree
except ImportError:
    # Fallback for Phase 1 - will be required in Phase 2
    etree = None

from datetime import datetime


class ETDANamespace:
    """ETDA XML Namespaces according to Thai Revenue Department standards"""
    
    # Root namespace for Tax Invoice
    RSM = "urn:etda:uncefact:data:standard:TaxInvoice_CrossIndustryInvoice:2"
    
    # Reusable Aggregate Business Information Entity
    RAM = "urn:etda:uncefact:data:standard:TaxInvoice_ReusableAggregateBusinessInformationEntity:2"
    
    # XML Digital Signature
    DS = "http://www.w3.org/2000/09/xmldsig#"
    
    # XAdES (for digital signatures - Phase 2)
    XADES = "http://uri.etsi.org/01903/v1.3.2#"
    
    @classmethod
    def get_nsmap(cls):
        """Returns namespace map for lxml"""
        return {
            'rsm': cls.RSM,
            'ram': cls.RAM,
            'ns3': cls.DS,
        }
    
    @classmethod
    def get_nsmap_with_xades(cls):
        """Returns namespace map including XAdES for signed documents"""
        nsmap = cls.get_nsmap()
        nsmap['xades'] = cls.XADES
        return nsmap


class ETDAXMLBuilder:
    """
    Builder class for creating ETDA-compliant XML structures.
    
    This class handles the low-level XML construction using lxml,
    ensuring proper namespace management and element ordering.
    """
    
    def __init__(self):
        """Initialize XML builder with ETDA namespaces"""
        if etree is None:
            raise ImportError("lxml is required for Phase 2. Install with: pip install lxml>=4.9.0")
        
        self.nsmap = ETDANamespace.get_nsmap()
        self.root = None
    
    def create_root(self, document_type='TaxInvoice'):
        """
        Create root element for ETDA document
        
        Args:
            document_type: Type of document (TaxInvoice, DebitNote, CreditNote)
        
        Returns:
            lxml Element: Root element with proper namespace
        """
        root_tag = f'{{{ETDANamespace.RSM}}}{document_type}_CrossIndustryInvoice'
        self.root = etree.Element(root_tag, nsmap=self.nsmap)
        return self.root
    
    def create_element(self, tag_name, text=None, attrib=None, namespace='ram'):
        """
        Create an XML element with proper namespace
        
        Args:
            tag_name: Element name without namespace prefix
            text: Text content of the element
            attrib: Dictionary of attributes
            namespace: Namespace prefix ('ram', 'rsm', 'ds')
        
        Returns:
            lxml Element: Created element
        """
        ns_uri = getattr(ETDANamespace, namespace.upper())
        full_tag = f'{{{ns_uri}}}{tag_name}'
        
        element = etree.Element(full_tag, attrib=attrib or {})
        if text is not None:
            element.text = str(text)
        
        return element
    
    def append_element(self, parent, tag_name, text=None, attrib=None, namespace='ram'):
        """
        Create and append element to parent in one step
        
        Args:
            parent: Parent element
            tag_name: Element name
            text: Text content
            attrib: Element attributes
            namespace: Namespace prefix
        
        Returns:
            lxml Element: Created and appended element
        """
        element = self.create_element(tag_name, text, attrib, namespace)
        parent.append(element)
        return element
    
    def create_document_context(self, guideline_id='ER3-2560', scheme_version='v2.0'):
        """
        Create ExchangedDocumentContext section
        
        Args:
            guideline_id: ETDA guideline ID (ER3-2560 for current standard)
            scheme_version: Version of the standard
        
        Returns:
            lxml Element: DocumentContext element
        """
        context = self.create_element('ExchangedDocumentContext')
        
        param = self.append_element(context, 'GuidelineSpecifiedDocumentContextParameter')
        self.append_element(
            param, 'ID', guideline_id,
            attrib={'schemeAgencyID': 'ETDA', 'schemeVersionID': scheme_version}
        )
        
        return context
    
    def create_exchanged_document(self, invoice_id, invoice_name, type_code='388',
                                  issue_datetime=None, purpose=None, notes=None):
        """
        Create ExchangedDocument section (invoice header information)
        
        Args:
            invoice_id: Invoice number/ID
            invoice_name: Document name (e.g., "ใบกำกับภาษี" = Tax Invoice)
            type_code: Document type code (388 = Tax Invoice, 380 = Commercial Invoice)
            issue_datetime: Issue date/time (datetime object)
            purpose: Purpose or reason for document
            notes: List of dictionaries with 'subject' and 'content' keys
        
        Returns:
            lxml Element: ExchangedDocument element
        """
        doc = self.create_element('ExchangedDocument')
        
        self.append_element(doc, 'ID', invoice_id)
        self.append_element(doc, 'Name', invoice_name)
        self.append_element(doc, 'TypeCode', type_code)
        
        # Format datetime as ISO 8601 with timezone
        if issue_datetime:
            iso_datetime = issue_datetime.strftime('%Y-%m-%dT%H:%M:%S.000Z')
            self.append_element(doc, 'IssueDateTime', iso_datetime)
        
        if purpose:
            self.append_element(doc, 'Purpose', purpose)
        
        # Creation datetime (usually same as issue datetime)
        creation_datetime = issue_datetime or datetime.now()
        iso_creation = creation_datetime.strftime('%Y-%m-%dT%H:%M:%S.000Z')
        self.append_element(doc, 'CreationDateTime', iso_creation)
        
        # Add notes if provided
        if notes:
            for note in notes:
                note_elem = self.append_element(doc, 'IncludedNote')
                self.append_element(note_elem, 'Subject', note.get('subject', ''))
                self.append_element(note_elem, 'Content', note.get('content', ''))
        
        return doc
    
    def create_trade_party(self, name, tax_id, branch_id='00000', contact=None, address=None):
        """
        Create TradeParty element (Seller or Buyer)
        
        Args:
            name: Party name
            tax_id: Thai Tax Registration ID (13 digits)
            branch_id: Branch ID (00000 for head office)
            contact: Dictionary with 'person_name', 'email', 'telephone'
            address: Dictionary with Thai address fields
        
        Returns:
            lxml Element: TradeParty element
        """
        if not name.endswith('TradeParty'):
            # This is the party data, create the element
            party = self.create_element('TradeParty')
        else:
            # This is being called from a wrapper, create with specific name
            party = self.create_element(name)
        
        self.append_element(party, 'Name', name if not name.endswith('TradeParty') else tax_id)
        
        # Tax Registration (13 digits + 5 digits branch)
        tax_reg = self.append_element(party, 'SpecifiedTaxRegistration')
        full_tax_id = f"{tax_id}{branch_id}" if len(str(tax_id)) == 13 else tax_id
        self.append_element(tax_reg, 'ID', full_tax_id)
        
        # Contact information
        if contact:
            contact_elem = self.append_element(party, 'DefinedTradeContact')
            
            if contact.get('person_name'):
                self.append_element(contact_elem, 'PersonName', contact['person_name'])
            
            if contact.get('email'):
                email_comm = self.append_element(contact_elem, 'EmailURIUniversalCommunication')
                self.append_element(email_comm, 'URIID', contact['email'])
            
            if contact.get('telephone'):
                tel_comm = self.append_element(contact_elem, 'TelephoneUniversalCommunication')
                self.append_element(tel_comm, 'CompleteNumber', contact['telephone'])
        
        # Postal address (Thai format according to TISI 1099-2548)
        if address:
            addr_elem = self.append_element(party, 'PostalTradeAddress')
            
            # Postal code
            if address.get('postal_code'):
                self.append_element(addr_elem, 'PostcodeCode', address['postal_code'])
            
            # Address lines
            # LineOne: Building Number + Street + Soi
            line_one_parts = []
            if address.get('building_number'):
                line_one_parts.append(address['building_number'])
            if address.get('street'):
                line_one_parts.append(f"ถนน{address['street']}" if 'ถนน' not in address['street'] else address['street'])
            if address.get('soi'):
                line_one_parts.append(f"ซอย{address['soi']}" if 'ซอย' not in address['soi'] else address['soi'])
            
            if line_one_parts:
                self.append_element(addr_elem, 'LineOne', ' '.join(line_one_parts))
            
            # LineTwo: Additional address info (floor, moo, etc.)
            line_two_parts = []
            if address.get('floor'):
                line_two_parts.append(f"ชั้น {address['floor']}")
            if address.get('moo'):
                line_two_parts.append(f"หมู่ {address['moo']}")
            
            if line_two_parts:
                self.append_element(addr_elem, 'LineTwo', ' '.join(line_two_parts))
            
            # Administrative divisions (using codes)
            if address.get('district_code'):
                self.append_element(addr_elem, 'CityName', address['district_code'])
            elif address.get('district'):
                self.append_element(addr_elem, 'CityName', address['district'])
            
            if address.get('sub_district_code'):
                self.append_element(addr_elem, 'CitySubDivisionName', address['sub_district_code'])
            elif address.get('sub_district'):
                self.append_element(addr_elem, 'CitySubDivisionName', address['sub_district'])
            
            # Country (always TH for Thailand)
            self.append_element(addr_elem, 'CountryID', 'TH')
            
            # Province code
            if address.get('province_code'):
                self.append_element(addr_elem, 'CountrySubDivisionID', address['province_code'])
            elif address.get('province'):
                self.append_element(addr_elem, 'CountrySubDivisionID', address['province'])
            
            # Building number (repeated for compatibility)
            if address.get('building_number'):
                self.append_element(addr_elem, 'BuildingNumber', address['building_number'])
        
        return party
    
    def create_trade_tax(self, type_code='VAT', rate=7.00, basis_amount=0.0, calculated_amount=0.0):
        """
        Create TradeTax element for tax calculation
        
        Args:
            type_code: Tax type (VAT, ST, etc.)
            rate: Tax rate percentage
            basis_amount: Amount before tax
            calculated_amount: Tax amount
        
        Returns:
            lxml Element: ApplicableTradeTax element
        """
        tax = self.create_element('ApplicableTradeTax')
        
        self.append_element(tax, 'TypeCode', type_code)
        self.append_element(tax, 'CalculatedRate', f"{rate:.2f}")
        self.append_element(tax, 'BasisAmount', f"{basis_amount:.2f}")
        self.append_element(tax, 'CalculatedAmount', f"{calculated_amount:.2f}")
        
        return tax
    
    def create_monetary_summation(self, line_total, tax_basis, tax_total, grand_total):
        """
        Create MonetarySummation element (totals)
        
        Args:
            line_total: Sum of all line items before tax
            tax_basis: Taxable amount
            tax_total: Total tax amount
            grand_total: Final total including tax
        
        Returns:
            lxml Element: MonetarySummation element
        """
        summation = self.create_element('SpecifiedTradeSettlementHeaderMonetarySummation')
        
        self.append_element(summation, 'LineTotalAmount', f"{line_total:.2f}")
        self.append_element(summation, 'TaxBasisTotalAmount', f"{tax_basis:.2f}")
        self.append_element(summation, 'TaxTotalAmount', f"{tax_total:.2f}")
        self.append_element(summation, 'GrandTotalAmount', f"{grand_total:.2f}")
        
        return summation
    
    def create_line_item(self, line_id, product_name, quantity, unit_code,
                        price_per_unit, tax_info, line_totals):
        """
        Create SupplyChainTradeLineItem element (invoice line)
        
        Args:
            line_id: Line number
            product_name: Product/service name
            quantity: Quantity sold
            unit_code: Unit of measure (e.g., "กล่อง", "ชิ้น", "EA")
            price_per_unit: Unit price
            tax_info: Dictionary with tax details
            line_totals: Dictionary with line totals
        
        Returns:
            lxml Element: IncludedSupplyChainTradeLineItem element
        """
        line_item = self.create_element('IncludedSupplyChainTradeLineItem')
        
        # Line document
        line_doc = self.append_element(line_item, 'AssociatedDocumentLineDocument')
        self.append_element(line_doc, 'LineID', str(line_id))
        
        # Product
        product = self.append_element(line_item, 'SpecifiedTradeProduct')
        self.append_element(product, 'Name', product_name)
        
        # Agreement (pricing)
        agreement = self.append_element(line_item, 'SpecifiedLineTradeAgreement')
        price = self.append_element(agreement, 'GrossPriceProductTradePrice')
        self.append_element(price, 'ChargeAmount', f"{price_per_unit:.2f}")
        
        # Delivery (quantity)
        delivery = self.append_element(line_item, 'SpecifiedLineTradeDelivery')
        self.append_element(delivery, 'BilledQuantity', str(quantity),
                          attrib={'unitCode': unit_code})
        
        # Settlement (tax and totals)
        settlement = self.append_element(line_item, 'SpecifiedLineTradeSettlement')
        
        # Tax for this line
        if tax_info:
            line_tax = self.create_trade_tax(
                type_code=tax_info.get('type_code', 'VAT'),
                rate=tax_info.get('rate', 7.0),
                basis_amount=tax_info.get('basis_amount', 0.0),
                calculated_amount=tax_info.get('calculated_amount', 0.0)
            )
            settlement.append(line_tax)
        
        # Allowances/charges if any
        if line_totals.get('discount_amount'):
            allowance = self.append_element(settlement, 'SpecifiedTradeAllowanceCharge')
            self.append_element(allowance, 'ChargeIndicator', 'false')  # false = discount
            self.append_element(allowance, 'ActualAmount',
                              f"{line_totals['discount_amount']:.2f}")
        
        # Line monetary summation
        line_sum = self.append_element(settlement, 'SpecifiedTradeSettlementLineMonetarySummation')
        
        if line_totals.get('tax_amount'):
            self.append_element(line_sum, 'TaxTotalAmount',
                              f"{line_totals['tax_amount']:.2f}")
        
        self.append_element(line_sum, 'NetLineTotalAmount',
                          f"{line_totals.get('net_total', 0.0):.2f}",
                          attrib={'currencyID': line_totals.get('currency', 'THB')})
        
        if line_totals.get('net_with_tax'):
            self.append_element(line_sum, 'NetIncludingTaxesLineTotalAmount',
                              f"{line_totals['net_with_tax']:.2f}",
                              attrib={'currencyID': line_totals.get('currency', 'THB')})
        
        return line_item
    
    def to_string(self, pretty_print=True, xml_declaration=True, encoding='UTF-8'):
        """
        Convert XML tree to string
        
        Args:
            pretty_print: Add indentation and newlines
            xml_declaration: Include XML declaration
            encoding: Character encoding
        
        Returns:
            bytes: XML as bytes string
        """
        if self.root is None:
            raise ValueError("No XML root element created")
        
        return etree.tostring(
            self.root,
            pretty_print=pretty_print,
            xml_declaration=xml_declaration,
            encoding=encoding
        )
    
    def to_file(self, filepath, pretty_print=True):
        """
        Write XML to file
        
        Args:
            filepath: Output file path
            pretty_print: Format with indentation
        """
        if self.root is None:
            raise ValueError("No XML root element created")
        
        tree = etree.ElementTree(self.root)
        tree.write(
            filepath,
            pretty_print=pretty_print,
            xml_declaration=True,
            encoding='UTF-8'
        )
