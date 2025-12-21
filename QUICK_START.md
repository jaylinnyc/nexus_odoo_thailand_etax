# Quick Start Guide - Thailand e-Tax Module

## Step 1: Clone Official ETDA Repositories

Run these commands from your project root:

```bash
cd /Users/Jay/development/git/nexus/panya19prod/jaylinnyc/thailand_etax

# Create schemas directory
mkdir -p schemas

# Clone ETDA repositories
cd schemas
git clone https://github.com/ETDA/soda-etax.git
git clone https://github.com/ETDA/etax-xades.git

cd ..
```

## Step 2: Download Official XML Schemas

1. Download the official schema package:
   - URL: https://etax.rd.go.th/etax_staticpage/app/download/XMLSchemaV2.zip
   
2. Extract to: `schemas/XMLSchemaV2/`

## Step 3: Review Reference Implementations

### soda-etax Repository Structure
```
soda-etax/
├── src/
│   ├── etda/uncefact/data/standard/
│   │   ├── taxinvoice_crossindustryinvoice/
│   │   ├── receipt_crossindustryinvoice/
│   │   ├── debitcreditnote_crossindustryinvoice/
│   │   └── [other document types]/
│   └── service/test/Run.java  # Example usage
└── changelog.md
```

Key files to study:
- `TaxInvoiceCrossIndustryInvoiceType.java` - Main invoice structure
- `ExchangedDocumentType.java` - Document metadata
- `SupplyChainTradeTransactionType.java` - Transaction details
- `Run.java` - Example of how to use the classes

### etax-xades Repository Structure
```
etax-xades/
├── src/main/java/
│   ├── XadesBesSigner.java       # Signature generation
│   ├── XadesBesVerifier.java     # Signature verification
│   └── xades4j/providers/impl/   # Supporting classes
└── src/main/resources/conf/
    └── etax-xades.properties     # Configuration example
```

## Step 4: Install Python Dependencies

Create/update `requirements.txt` in the module:

```bash
# Create requirements file
cat > requirements.txt << EOF
lxml>=4.9.0
xmlsec>=1.3.13
cryptography>=40.0.0
pyOpenSSL>=23.0.0
EOF

# Install dependencies
pip install -r requirements.txt
```

## Step 5: Understand Document Types

| Document Type | Code | Use Case |
|--------------|------|----------|
| Tax Invoice | 380 | Standard sales invoice with VAT |
| Receipt | - | Payment receipt |
| Debit Note | 383 | Additional charges after invoice |
| Credit Note | 381 | Returns, discounts, corrections |
| Cancellation Note | - | Cancel previous documents |

## Step 6: Key XML Structure to Implement

### Tax Invoice XML Template
```xml
<?xml version="1.0" encoding="UTF-8"?>
<TaxInvoice_CrossIndustryInvoice 
    xmlns:rsm="urn:etda:uncefact:data:standard:TaxInvoice_CrossIndustryInvoice:2"
    xmlns:ram="urn:etda:uncefact:data:standard:TaxInvoice_ReusableAggregateBusinessInformationEntity:2"
    xmlns:qdt="urn:etda:uncefact:data:standard:QualifiedDataType:1"
    xmlns:udt="urn:un:unece:uncefact:data:standard:UnqualifiedDataType:16">
    
    <!-- 1. Document Context -->
    <ExchangedDocumentContext>
        <GuidelineSpecifiedDocumentContextParameter>
            <ID>TaxInvoice</ID>
        </GuidelineSpecifiedDocumentContextParameter>
    </ExchangedDocumentContext>
    
    <!-- 2. Document Header -->
    <ExchangedDocument>
        <ID>IV2023-001</ID>
        <Name>ใบกำกับภาษี</Name>
        <TypeCode>380</TypeCode>
        <IssueDateTime>2023-12-21T10:00:00</IssueDateTime>
        <PurposeCode>9</PurposeCode>
    </ExchangedDocument>
    
    <!-- 3. Transaction Details -->
    <SupplyChainTradeTransaction>
        <!-- Seller Party -->
        <ApplicableHeaderTradeAgreement>
            <SellerTradeParty>
                <Name>Your Company Ltd.</Name>
                <PostalTradeAddress>...</PostalTradeAddress>
                <SpecifiedTaxRegistration>
                    <ID>1234567890123</ID>
                </SpecifiedTaxRegistration>
            </SellerTradeParty>
            
            <!-- Buyer Party -->
            <BuyerTradeParty>...</BuyerTradeParty>
        </ApplicableHeaderTradeAgreement>
        
        <!-- Delivery Details -->
        <ApplicableHeaderTradeDelivery>
            <ActualDeliverySupplyChainEvent>...</ActualDeliverySupplyChainEvent>
        </ApplicableHeaderTradeDelivery>
        
        <!-- Settlement (Payment & Totals) -->
        <ApplicableHeaderTradeSettlement>
            <TaxCurrencyCode>THB</TaxCurrencyCode>
            
            <!-- Tax Breakdown -->
            <ApplicableTradeTax>
                <TypeCode>VAT</TypeCode>
                <BasisAmount>1000.00</BasisAmount>
                <RateApplicablePercent>7</RateApplicablePercent>
                <CalculatedAmount>70.00</CalculatedAmount>
            </ApplicableTradeTax>
            
            <!-- Monetary Summary -->
            <SpecifiedTradeSettlementMonetarySummation>
                <LineTotalAmount>1000.00</LineTotalAmount>
                <TaxBasisTotalAmount>1000.00</TaxBasisTotalAmount>
                <TaxTotalAmount>70.00</TaxTotalAmount>
                <GrandTotalAmount>1070.00</GrandTotalAmount>
            </SpecifiedTradeSettlementMonetarySummation>
        </ApplicableHeaderTradeSettlement>
        
        <!-- Line Items -->
        <IncludedSupplyChainTradeLineItem>
            <AssociatedDocumentLineDocument>
                <LineID>1</LineID>
            </AssociatedDocumentLineDocument>
            
            <SpecifiedTradeProduct>
                <Name>Product Name</Name>
                <Description>Product Description</Description>
            </SpecifiedTradeProduct>
            
            <SpecifiedLineTradeAgreement>
                <NetPriceProductTradePrice>
                    <ChargeAmount>100.00</ChargeAmount>
                </NetPriceProductTradePrice>
            </SpecifiedLineTradeAgreement>
            
            <SpecifiedLineTradeDelivery>
                <BilledQuantity unitCode="EA">10</BilledQuantity>
            </SpecifiedLineTradeDelivery>
            
            <SpecifiedLineTradeSettlement>
                <ApplicableTradeTax>
                    <TypeCode>VAT</TypeCode>
                    <RateApplicablePercent>7</RateApplicablePercent>
                </ApplicableTradeTax>
                
                <SpecifiedTradeSettlementLineMonetarySummation>
                    <LineTotalAmount>1000.00</LineTotalAmount>
                </SpecifiedTradeSettlementLineMonetarySummation>
            </SpecifiedLineTradeSettlement>
        </IncludedSupplyChainTradeLineItem>
    </SupplyChainTradeTransaction>
    
    <!-- 4. Digital Signature (XAdES-BES) -->
    <Signature xmlns="http://www.w3.org/2000/09/xmldsig#">
        <!-- Will be added by signature process -->
    </Signature>
</TaxInvoice_CrossIndustryInvoice>
```

## Step 7: Odoo Data Mapping

### Critical Mappings

| Odoo Field | ETDA XML Path | Notes |
|------------|---------------|-------|
| `invoice.name` | `ExchangedDocument/ID` | Invoice number |
| `invoice.invoice_date` | `ExchangedDocument/IssueDateTime` | ISO datetime |
| `invoice.company_id.name` | `SellerTradeParty/Name` | Company name |
| `invoice.company_id.vat` | `SellerTradeParty/SpecifiedTaxRegistration/ID` | 13 digits |
| `invoice.partner_id.name` | `BuyerTradeParty/Name` | Customer name |
| `invoice.partner_id.vat` | `BuyerTradeParty/SpecifiedTaxRegistration/ID` | 13 digits |
| `invoice.amount_untaxed` | `LineTotalAmount` | Subtotal |
| `invoice.amount_tax` | `TaxTotalAmount` | Total tax |
| `invoice.amount_total` | `GrandTotalAmount` | Total amount |
| `line.product_id.name` | `SpecifiedTradeProduct/Name` | Product name |
| `line.quantity` | `BilledQuantity` | Quantity |
| `line.price_unit` | `ChargeAmount` | Unit price |
| `line.price_subtotal` | `LineTotalAmount` | Line total |

## Step 8: Certificate Configuration

You'll need to obtain:
1. **Digital Certificate** from authorized Thai CA:
   - ETDA
   - Thawte Thailand
   - DigiCert Thailand
   
2. **Certificate Format:**
   - PKCS#12 (.p12, .pfx) - Most common
   - PKCS#11 - For smart card/token

3. **Store Securely:**
   - Encrypt certificate password
   - Store path in Odoo configuration
   - Never commit certificates to git

## Next Development Tasks

1. ✅ Module scaffolded
2. ✅ Research completed
3. ⬜ Clone ETDA repositories
4. ⬜ Download official schemas
5. ⬜ Install Python dependencies
6. ⬜ Implement XML builder base class
7. ⬜ Implement tax invoice generator
8. ⬜ Implement digital signature
9. ⬜ Create configuration UI
10. ⬜ Test with sample data

## Useful Commands

```bash
# Validate XML against schema
xmllint --noout --schema schemas/XMLSchemaV2/ETDA/data/standard/TaxInvoice_CrossIndustryInvoice_2p0.xsd output.xml

# View XML structure
xmllint --format output.xml

# Check Python libraries
python -c "import lxml, xmlsec, cryptography; print('All libraries installed')"
```

## Resources

- Thai Revenue Dept: https://etax.rd.go.th
- ETDA Portal: https://www.etda.or.th
- ETDA GitHub: https://github.com/ETDA
- UN/CEFACT: https://unece.org/trade/uncefact

## Support

For technical questions about ETDA standards:
- ETDA Support: Contact through etda.or.th
- Thai Revenue Dept: etax.rd.go.th support section

For Odoo implementation questions:
- Internal team discussion
- Odoo Thailand community
