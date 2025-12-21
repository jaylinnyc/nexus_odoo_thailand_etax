# Thailand e-Tax Export Module - Research & Implementation Plan

## Research Summary

### Official Thai Government GitHub Resources

I've identified **three official ETDA (Electronic Transactions Development Agency) repositories** that are essential for this project:

#### 1. **ETDA/soda-etax**
- **Repository:** https://github.com/ETDA/soda-etax
- **Purpose:** XML Schema implementation for Thailand e-Tax system
- **Language:** Java (JAXB-based)
- **Key Features:**
  - Complete JAXB-generated classes for e-Tax XML schemas
  - Support for multiple document types:
    - Tax Invoices (`TaxInvoice_CrossIndustryInvoice`)
    - Receipts (`Receipt_CrossIndustryInvoice`)
    - Debit/Credit Notes (`DebitCreditNote_CrossIndustryInvoice`)
    - Cancellation Notes
    - Standard Invoices
  - Based on UN/CEFACT standards
  - ETDA namespace implementations

#### 2. **ETDA/etax-xades**
- **Repository:** https://github.com/ETDA/etax-xades
- **Purpose:** XAdES digital signature implementation for Thailand e-Tax
- **Language:** Java
- **Key Features:**
  - XAdES-BES signature generation
  - Signature verification
  - Support for PKCS#11 and PKCS#12 certificates
  - Certificate chain validation
  - SHA-512 digest algorithm
  - RSA-SHA512 signature algorithm

#### 3. **ETDA/ETDA-Mobile-Sign-XmlsignApi**
- **Repository:** https://github.com/ETDA/ETDA-Mobile-Sign-XmlsignApi
- **Purpose:** XML signing API
- **Language:** Java

### XML Schema Information

**Official Schema Source:** https://etax.rd.go.th/etax_staticpage/app/download/XMLSchemaV2.zip

**Root Elements:**
- `TaxInvoice_CrossIndustryInvoice` - for tax invoices
- `Receipt_CrossIndustryInvoice` - for receipts
- `DebitCreditNote_CrossIndustryInvoice` - for debit/credit notes

**Root Schema Path:** `XMLSchemaV2\ETDA\data\standard\TaxInvoice_CrossIndustryInvoice_2p0.xsd`

### Document Structure

Based on the ETDA repositories, the XML documents follow this structure:

```xml
<TaxInvoice_CrossIndustryInvoice>
    <ExchangedDocumentContext>
        <!-- Document context and parameters -->
    </ExchangedDocumentContext>
    
    <ExchangedDocument>
        <!-- Document metadata: ID, Name, TypeCode, IssueDateTime, etc. -->
    </ExchangedDocument>
    
    <SupplyChainTradeTransaction>
        <!-- Trade transaction details, parties, line items, totals -->
    </SupplyChainTradeTransaction>
    
    <Signature xmlns="http://www.w3.org/2000/09/xmldsig#">
        <!-- XAdES-BES digital signature -->
    </Signature>
</TaxInvoice_CrossIndustryInvoice>
```

### Key Standards & Requirements

1. **XML Format:** ETDA Standard (based on UN/CEFACT Cross Industry Invoice)
2. **Namespaces:**
   - `urn:etda:uncefact:data:standard:TaxInvoice_CrossIndustryInvoice:2`
   - `urn:etda:uncefact:data:standard:TaxInvoice_ReusableAggregateBusinessInformationEntity:2`
   - `urn:etda:uncefact:data:standard:QualifiedDataType:1`
   - `urn:un:unece:uncefact:data:standard:UnqualifiedDataType:16`

3. **Digital Signature:** XAdES-BES (XML Advanced Electronic Signatures - Basic Electronic Signature)
   - Algorithm: RSA-SHA512
   - Digest: SHA-512
   - Support for certificate chain validation

4. **Document Types:**
   - Tax Invoices (380)
   - Receipts
   - Debit Notes
   - Credit Notes
   - Cancellation Notes

---

## Implementation Plan for Odoo 19

### Phase 1: Foundation Setup ✓ (COMPLETED)

- [x] Create module structure under `jaylinnyc/thailand_etax/`
- [x] Set up `__manifest__.py` with proper dependencies
- [x] Create basic directory structure (models, wizards, views, security)

### Phase 2: XML Schema Integration

**Approach:** Python-based XML generation (instead of Java translation)

#### 2.1 Install Python Libraries
```python
# Required libraries
- lxml (for XML generation and validation)
- xmlsec (for XAdES signature)
- cryptography (for certificate handling)
```

#### 2.2 Download Official Schemas
- Clone or download schemas from ETDA GitHub
- Store in module directory: `thailand_etax/schemas/`
- Use for validation during development

#### 2.3 Create XML Builder Classes
```
models/
├── etax_xml_builder.py         # Base XML builder
├── etax_tax_invoice.py         # Tax invoice XML generator
├── etax_receipt.py             # Receipt XML generator
├── etax_debit_credit_note.py  # Debit/Credit note generator
└── etax_signature.py           # XAdES signature handler
```

### Phase 3: Core Models

#### 3.1 Configuration Model (`etax_config.py`)
```python
class EtaxConfig(models.Model):
    _name = 'etax.config'
    
    # Certificate settings
    certificate_type = Selection([('pkcs11', 'PKCS#11'), ('pkcs12', 'PKCS#12')])
    certificate_path = Char()
    certificate_password = Char()
    
    # Tax settings
    tax_id = Char()
    branch_number = Char()
    
    # Output settings
    output_directory = Char()
    auto_sign = Boolean()
```

#### 3.2 Extended Account Move (`account_move.py`)
```python
class AccountMove(models.Model):
    _inherit = 'account.move'
    
    etax_xml_file = Binary('e-Tax XML File')
    etax_xml_filename = Char()
    etax_document_id = Char()
    etax_export_date = Datetime()
    etax_status = Selection([
        ('draft', 'Draft'),
        ('exported', 'Exported'),
        ('signed', 'Signed'),
        ('validated', 'Validated')
    ])
    
    def action_export_etax_xml(self):
        # Export to XML
        pass
```

#### 3.3 Company Extension (`res_company.py`)
```python
class ResCompany(models.Model):
    _inherit = 'res.company'
    
    etax_tax_id = Char('Tax ID (13 digits)')
    etax_branch_id = Char('Branch ID (5 digits)')
    etax_postal_code = Char()
    etax_city_code = Char()  # TISI1099-2548 code
    etax_province_code = Char()
```

### Phase 4: XML Generation Logic

#### 4.1 Tax Invoice XML Generator
Key components to map from Odoo to ETDA format:
- Document context (GuidelineSpecifiedDocumentContextParameter)
- Document header (ID, TypeCode, IssueDateTime)
- Seller/Buyer party information
- Line items with tax details
- Payment terms
- Monetary summaries
- Tax breakdown

#### 4.2 Data Mapping
```
Odoo → ETDA Mapping:
- invoice.name → ExchangedDocument.ID
- invoice.invoice_date → ExchangedDocument.IssueDateTime
- invoice.company_id.vat → SellerTradeParty.TaxRegistration.ID
- invoice.partner_id.vat → BuyerTradeParty.TaxRegistration.ID
- invoice.invoice_line_ids → SupplyChainTradeLineItem
- invoice.amount_tax → ApplicableTradeTax.CalculatedAmount
- invoice.amount_total → GrandTotalAmount
```

### Phase 5: Digital Signature Implementation

#### 5.1 XAdES-BES Signature
- Implement using `xmlsec` library
- Support for Thai digital certificates
- Certificate validation
- Timestamp support

#### 5.2 Certificate Management
- Store certificate configuration securely
- Support both PKCS#11 (smart card) and PKCS#12 (file)
- Certificate chain validation

### Phase 6: Validation & Testing

#### 6.1 XML Schema Validation
- Validate against official ETDA XSD schemas
- Error reporting and correction

#### 6.2 Test Data
- Create sample invoices
- Export and validate XML
- Test signature generation

#### 6.3 Integration with ETDA Tools
- Use ETDA's verification tools if available
- Validate XML structure
- Verify digital signatures

### Phase 7: User Interface

#### 7.1 Configuration Views
- Certificate setup wizard
- Company e-Tax information
- Export settings

#### 7.2 Invoice Views
- "Export e-Tax XML" button on invoices
- Download generated XML
- View export status
- Re-export capability

#### 7.3 Wizards
```python
class EtaxExportWizard(models.TransientModel):
    _name = 'etax.export.wizard'
    
    invoice_ids = Many2many('account.move')
    date_from = Date()
    date_to = Date()
    include_signature = Boolean(default=True)
    export_format = Selection([('xml', 'XML'), ('zip', 'ZIP Archive')])
```

### Phase 8: Reporting & Batch Export

- Batch export multiple invoices
- Export log/history
- Summary reports
- Error tracking

---

## Feasibility Assessment

### ✅ **HIGHLY FEASIBLE**

**Strengths:**
1. **Official Standards Available:** ETDA provides complete specifications and reference implementations
2. **Clear Documentation:** GitHub repositories have working Java code we can reference
3. **Mature Python Libraries:** `lxml` and `xmlsec` are battle-tested
4. **Odoo Integration:** Good fit with Odoo's architecture
5. **Thai Localization Exists:** `l10n_th` module already in Odoo

**Challenges & Solutions:**

| Challenge | Solution |
|-----------|----------|
| **Complex XML Schema** | Use official schemas for validation; implement builders incrementally |
| **Digital Signatures** | Use Python `xmlsec` library (equivalent to Java xades4j) |
| **Certificate Management** | Store encrypted, support standard formats (PKCS#11/12) |
| **Thai-specific Business Rules** | Reference Java code, consult with Thai accounting experts |
| **Testing & Validation** | Use ETDA's validation tools, create comprehensive test suite |

### Technical Stack Recommendation

```
Language: Python 3.8+
Libraries:
├── lxml (4.9+)           # XML generation & parsing
├── xmlsec (1.3+)         # Digital signatures
├── cryptography (40.0+)  # Certificate handling
├── pyOpenSSL (23.0+)     # SSL/TLS support
└── zeep (optional)       # If SOAP submission required
```

### Development Timeline Estimate

| Phase | Duration | Complexity |
|-------|----------|------------|
| XML Schema Integration | 1-2 weeks | Medium |
| Core Models | 1 week | Low |
| XML Generation Logic | 2-3 weeks | High |
| Digital Signature | 2 weeks | High |
| Validation & Testing | 2 weeks | Medium |
| User Interface | 1 week | Low |
| Documentation & Polish | 1 week | Low |
| **TOTAL** | **10-12 weeks** | - |

---

## Next Steps - Recommended Actions

### Immediate Actions (You):
1. **Clone ETDA Repositories:**
   ```bash
   cd /Users/Jay/development/git/nexus/panya19prod/jaylinnyc/thailand_etax
   git clone https://github.com/ETDA/soda-etax.git schemas/soda-etax
   git clone https://github.com/ETDA/etax-xades.git schemas/etax-xades
   ```

2. **Download Official Schemas:**
   - Download from: https://etax.rd.go.th/etax_staticpage/app/download/XMLSchemaV2.zip
   - Extract to: `jaylinnyc/thailand_etax/schemas/XMLSchemaV2/`

3. **Review Requirements:**
   - Study the Java code structure in `soda-etax`
   - Understand document types your business needs
   - Identify certificate provider (for digital signatures)

### Development Actions (Next Phase):
1. Install required Python libraries
2. Create XML builder base classes
3. Implement tax invoice generator
4. Test XML generation with sample data
5. Implement digital signature
6. Create user interfaces

---

## Conclusion

**This project is DEFINITELY FEASIBLE** and well-suited for implementation in Odoo 19.

**Key Success Factors:**
- ✅ Official Thai government repositories provide complete specifications
- ✅ Working reference implementations available (Java)
- ✅ Python has equivalent libraries for all required functionality
- ✅ Clear standards and documentation
- ✅ Odoo's architecture fits well with the requirements

**Recommendation:** Proceed with implementation. Start with basic XML generation, then add signature functionality, and finally polish the UI.

The module structure has been created and is ready for development. The main technical challenge will be correctly mapping Odoo's invoice data to the ETDA XML format, but the reference implementations provide clear guidance.

---

## References

- ETDA soda-etax: https://github.com/ETDA/soda-etax
- ETDA etax-xades: https://github.com/ETDA/etax-xades
- Official Schema: https://etax.rd.go.th/etax_staticpage/app/download/XMLSchemaV2.zip
- Thai Revenue Department: https://etax.rd.go.th
