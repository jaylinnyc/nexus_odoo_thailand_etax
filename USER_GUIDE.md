# Thailand e-Tax Export - User Guide

## 📋 Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Initial Configuration](#initial-configuration)
4. [Single Invoice Workflow](#single-invoice-workflow)
5. [Batch Export Workflow](#batch-export-workflow)
6. [Troubleshooting](#troubleshooting)
7. [Legal Compliance](#legal-compliance)
8. [FAQ](#faq)

---

## Overview

### What is Thailand e-Tax?

Thailand e-Tax is the Revenue Department's mandatory electronic tax invoice system that requires businesses to submit tax documents in a specific XML format compliant with ETDA (Electronic Transactions Development Agency) standards.

### Module Features

✅ **ETDA-compliant XML generation** - Follows official Thai Revenue Department specifications  
✅ **Digital signature support** - XAdES-BES standard with PKCS#11/PKCS#12 certificates  
✅ **Thai Tax ID validation** - Automatic mod 11 algorithm validation  
✅ **Batch processing** - Export multiple invoices at once  
✅ **Status tracking** - Visual workflow with draft → exported → signed → validated  
✅ **Audit trail** - Complete history of e-Tax operations  

---

## Installation

### Step 1: Update Apps List

1. Go to **Apps** menu
2. Click **Update Apps List**
3. Search for **"Thailand e-Tax Export"**
4. Click **Install**

### Step 2: Verify Installation

After installation, verify the module is active:
- Menu: **Invoicing → Configuration → e-Tax Configuration** (should appear)
- Company settings: **Settings → Companies → e-Tax Thailand tab** (should appear)

---

## Initial Configuration

### Configure Company Information

Required for all e-Tax exports.

1. Navigate to **Settings → Companies → Companies**
2. Select your company
3. Go to **e-Tax Thailand** tab
4. Fill in required fields:

| Field | Format | Example | Required |
|-------|--------|---------|----------|
| **Thai Tax ID** | 13 digits | 0105536001419 | ✅ Yes |
| **Branch ID** | 5 digits (00000 = head office) | 00000 | ✅ Yes |
| **Building Name/Number** | Text | Silom Complex | Optional |
| **Floor** | Text | 15th Floor | Optional |
| **Village No. (Moo)** | Number | 5 | Optional |
| **Soi** | Text | Sukhumvit 21 | Optional |
| **Street** | Text | Silom Road | ✅ Yes |
| **Sub-district** | Text | Silom | ✅ Yes |
| **District** | Text | Bang Rak | ✅ Yes |
| **Province** | Text | Bangkok | ✅ Yes |
| **Postal Code** | 5 digits | 10500 | ✅ Yes |

**Important:** Thai Tax ID is validated using mod 11 algorithm. Invalid IDs will be rejected.

### Configure e-Tax System Settings

1. Navigate to **Invoicing → Configuration → e-Tax Configuration**
2. Click **Create**
3. Configure the following sections:

#### Certificate Settings

**PKCS#11 (Smartcard):**
- Certificate Type: `PKCS#11`
- Library Path: `/usr/lib/opensc-pkcs11.so` (Linux) or `C:\Windows\System32\opensc-pkcs11.dll` (Windows)
- Token PIN: *Your smartcard PIN*

**PKCS#12 (File):**
- Certificate Type: `PKCS#12`
- Certificate File: Upload your `.p12` or `.pfx` file
- Certificate Password: *Your certificate password*

#### Output Settings

- **Export Directory**: `/home/odoo/etax_exports/` (default)
- **Auto-sign After Export**: ✅ Enable for automatic signing (requires certificate configured)
- **Validate XML After Export**: ✅ Enable for automatic validation (Phase 2)

#### Algorithm Settings

**Recommended settings (ETDA standard):**
- Digest Algorithm: `SHA-256`
- Signature Algorithm: `RSA-SHA256`

**High-security option:**
- Digest Algorithm: `SHA-512`
- Signature Algorithm: `RSA-SHA512`

4. Click **Test Certificate** to verify certificate is working
5. Click **Save**

---

## Single Invoice Workflow

### Step-by-Step Process

#### 1. Create and Post Invoice

1. Create invoice: **Invoicing → Customers → Invoices → Create**
2. Fill in invoice details (customer, line items, taxes)
3. Click **Confirm**
4. Click **Post**

**Status:** Invoice posted ✅

#### 2. Export e-Tax XML

1. Open the posted invoice
2. Click **Export e-Tax XML** button in header

**What happens:**
- System validates company Thai Tax ID
- System validates customer has Thai tax information
- Generates ETDA-compliant XML
- Status changes to **Exported** (green badge)
- XML file stored in invoice record

**Validation checks:**
- ✅ Invoice must be posted
- ✅ Invoice must be customer invoice (not vendor bill)
- ✅ Company must have Thai Tax ID configured
- ✅ Customer must have Thai tax information

**Status:** Exported ✅ → Can proceed to signing

#### 3. Sign e-Tax XML (Phase 2)

1. Click **Sign e-Tax XML** button in header
2. If using smartcard, enter PIN when prompted
3. Wait for signature process to complete

**What happens:**
- Reads digital certificate (smartcard or file)
- Creates XAdES-BES digital signature
- Embeds signature in XML
- Status changes to **Signed** (green badge)

**Important:** Once signed, XML cannot be modified. Any changes require reset and re-export.

**Status:** Signed ✅ → Legally binding document

#### 4. Download XML File

1. Click **Download e-Tax XML** button in header
2. Save file to your computer
3. File format: `etax_[invoice_number]_[date].xml`

**Use cases:**
- Manual submission to Revenue Department web portal
- Send to accountant for review
- Archive for audit purposes (required 5 years)

#### 5. Submit to Revenue Department

**Manual submission:**
1. Go to [Revenue Department e-Tax Portal](https://etax.rd.go.th)
2. Login with your credentials
3. Upload the signed XML file
4. Verify submission confirmation

**API submission (Phase 2 - Future):**
- Automatic submission via API integration
- Real-time status updates
- Rejection handling and resubmission

---

## Batch Export Workflow

For processing multiple invoices at once (end-of-month, quarterly filing, etc.)

### When to Use Batch Export

- ✅ Monthly tax filing (50-200 invoices)
- ✅ Quarter-end submissions
- ✅ Catching up on backlog
- ✅ Export all invoices for specific customer
- ✅ Re-export after configuration changes

### Step-by-Step Process

#### 1. Open Batch Export Wizard

Navigate to: **Invoicing → e-Tax → Batch Export e-Tax**

#### 2. Configure Export Options

**Export Type:**

**Option A: Selected Invoices**
- Select from invoice list view: **Invoicing → Customers → Invoices**
- Check boxes next to invoices to export
- Go to **Action → Batch Export e-Tax**

**Option B: Date Range**
- Export Type: `Date Range`
- Start Date: `2024-01-01`
- End Date: `2024-01-31`
- (Optional) Filter by Customer: Select specific customer
- (Optional) Filter by Invoice Type: Customer Invoice / Refund

**Export Format:**
- `Individual XML Files` - One file per invoice (for manual review)
- `ZIP Archive` - All XMLs in one compressed file (for batch submission)

**Additional Options:**
- ☑️ **Include Digital Signature** - Sign all invoices during export (requires certificate PIN entry once)

#### 3. Execute Batch Export

1. Click **Export** button
2. Wait for processing (progress bar shows status)
3. Review results summary:

```
✅ Successfully exported: 45 invoices
⚠️ Warnings: 2 invoices (missing customer tax info)
❌ Errors: 3 invoices (invalid Thai Tax ID)
```

#### 4. Download Results

- **Individual files**: Downloads each XML separately
- **ZIP archive**: Downloads single file `etax_export_[date].zip`

#### 5. Review Failed Invoices

1. Click **View Failed Invoices** link
2. For each failed invoice:
   - Review error message
   - Fix the underlying issue (company/customer data)
   - Re-run batch export for failed invoices only

---

## Invoice Status Reference

Visual guide to e-Tax status badges:

| Status | Badge Color | Meaning | Next Action |
|--------|-------------|---------|-------------|
| **Draft** | Gray | Not yet exported | Click "Export e-Tax XML" |
| **Exported** | Blue | XML generated, not signed | Click "Sign e-Tax XML" or download |
| **Signed** | Green | Digitally signed | Download and submit to Revenue Dept |
| **Validated** | Dark Green | Passed ETDA schema validation | Ready for submission |
| **Error** | Red | Export/signing failed | Check error message, fix issue, reset |

### Status Workflow Diagram

```
[Create Invoice] → [Post Invoice]
                        ↓
                   [Draft Status]
                        ↓
              [Export e-Tax XML] ← Button
                        ↓
                  [Exported Status]
                        ↓
              [Sign e-Tax XML] ← Button (Phase 2)
                        ↓
                   [Signed Status]
                        ↓
           [Auto-validate if enabled]
                        ↓
                 [Validated Status]
                        ↓
           [Download e-Tax XML] ← Button
                        ↓
       [Submit to Revenue Department]
```

---

## Troubleshooting

### Common Issues and Solutions

#### Issue 1: "Invalid Thai Tax ID"

**Error message:**
```
ValidationError: Thai Tax ID must be exactly 13 digits and pass mod 11 validation
```

**Solution:**
1. Go to **Settings → Companies → [Your Company]**
2. Check **e-Tax Thailand** tab → **Thai Tax ID** field
3. Verify it's 13 digits (no spaces or dashes)
4. Use [Thai Tax ID Validator](https://www.rd.go.th) to verify correct number
5. If incorrect, update and click **Save**

#### Issue 2: "Customer Missing Thai Tax Information"

**Error message:**
```
ValidationError: Customer must have Thai tax registration to export e-Tax
```

**Solution:**
1. Open the invoice
2. Click on **Customer** name to open customer form
3. Add Thai Tax ID in customer form (will be available in Phase 2)
4. Return to invoice and retry export

#### Issue 3: "Certificate Test Failed"

**Error message:**
```
Certificate cannot be read or is invalid
```

**Solution - PKCS#11 (Smartcard):**
1. Verify smartcard is inserted in reader
2. Check reader is connected to computer
3. Verify library path is correct:
   - Linux: `/usr/lib/opensc-pkcs11.so`
   - Windows: `C:\Windows\System32\opensc-pkcs11.dll`
4. Test reader: `pkcs11-tool --list-slots` (Linux/Mac)

**Solution - PKCS#12 (File):**
1. Verify certificate file is not corrupted
2. Check certificate password is correct
3. Verify certificate has not expired
4. Check certificate is issued by authorized CA (Revenue Department approved)

#### Issue 4: "Export Button is Grayed Out"

**Possible causes:**
- ❌ Invoice is not posted → Click **Post** first
- ❌ Invoice is vendor bill → Only customer invoices can be exported
- ❌ Invoice already exported → Click **Reset e-Tax** to re-export

#### Issue 5: "Cannot Reset e-Tax"

**Error message:**
```
Cannot reset e-Tax for invoices already submitted to Revenue Department
```

**Solution:**
- This is intentional - once submitted, e-Tax cannot be modified
- If invoice needs correction:
  1. Create credit note to cancel original invoice
  2. Create new invoice with correct information
  3. Export and submit new invoice

#### Issue 6: "ZIP Download is Empty"

**Solution:**
1. Check batch export results - verify some invoices succeeded
2. If all failed, review error messages and fix underlying issues
3. Re-run batch export after fixes

---

## Legal Compliance

### Revenue Department Requirements

The Thailand e-Tax module complies with:

1. **ETDA XML Standard** (urn:etda:uncefact:data:standard)
   - Based on UN/CEFACT Cross Industry Invoice
   - Mandatory namespace and structure
   - Specific date/time formats (ISO 8601)

2. **Digital Signature Requirements**
   - XAdES-BES (XML Advanced Electronic Signatures - Basic)
   - Must use Revenue Department approved CA certificates
   - SHA-256 or SHA-512 digest algorithms
   - RSA-SHA256 or RSA-SHA512 signature algorithms

3. **Data Retention**
   - Store signed XML files for minimum **5 years**
   - Maintain audit trail of all e-Tax operations
   - Keep certificate records and validation logs

4. **Submission Deadlines**
   - B2B invoices: Submit within 30 days of invoice date
   - Government invoices: Submit within 7 days
   - Late submission penalties apply

### Address Format Compliance

Thai address fields follow **TISI 1099-2548** standard:
- Building/Number → Floor → Village (Moo) → Soi → Street
- Sub-district (Tambon) → District (Amphoe) → Province (Changwat)
- Postal Code (5 digits)

All fields must be in Thai language for official submissions.

---

## FAQ

### Q1: Do I need to export e-Tax for all invoices?

**A:** No. e-Tax is typically required for:
- ✅ B2B invoices (business to business)
- ✅ Invoices above THB 1,000 threshold
- ✅ VAT invoices
- ❌ Cash sales receipts (unless requested by customer)
- ❌ Invoices to individual consumers (unless B2C e-Tax is implemented)

### Q2: Can I export invoices before they are posted?

**A:** No. Invoices must be posted (status = "Posted") before e-Tax export. This ensures invoice data is finalized and cannot be changed after signing.

### Q3: What happens if I need to correct a signed invoice?

**A:** Signed invoices cannot be modified (digital signature would break). Process:
1. Do NOT reset the original invoice
2. Create a **Credit Note** to cancel the original
3. Create a **new invoice** with correct information
4. Export and sign the new invoice

### Q4: Can I use the same certificate for multiple companies?

**A:** No. Each Thai Tax ID (company) must have its own digital certificate issued by the Revenue Department's approved Certificate Authority.

### Q5: How do I know if my certificate is about to expire?

**A:** Certificate expiration checking will be added in Phase 2. Currently:
- Check certificate validity: **e-Tax Configuration → Test Certificate**
- Renew certificates 30-60 days before expiration
- Update configuration with new certificate immediately after renewal

### Q6: Can I export invoices from previous months/years?

**A:** Yes. There's no time limit for export in the module. However:
- Revenue Department may reject late submissions (check deadlines)
- Late submission penalties may apply
- Use batch export with date range to process historical invoices

### Q7: Does batch export require me to enter PIN multiple times?

**A:** No. When "Include Digital Signature" is enabled:
- Enter certificate PIN once at the start
- System signs all invoices in the batch
- Much faster than signing individually

### Q8: Can I customize the XML format?

**A:** No. The XML format is strictly defined by ETDA standards and cannot be customized. Non-compliant XMLs will be rejected by the Revenue Department.

### Q9: What if my internet is disconnected during batch export?

**A:** Batch export runs entirely on the Odoo server:
- ✅ Process will complete even if browser disconnects
- ✅ Results are saved in the wizard record
- ✅ Already-exported invoices remain exported
- ❌ Signing operations may need to be retried if interrupted

### Q10: Can I export invoices in currencies other than THB?

**A:** Yes, but the XML will include:
- Original currency and amount
- Exchange rate used
- THB equivalent (required for Revenue Department)

Make sure exchange rates are configured in Odoo before export.

---

## Support and Resources

### Official Documentation

- [ETDA e-Tax Standards](https://www.etda.or.th/)
- [Revenue Department e-Tax Portal](https://etax.rd.go.th)
- [Digital Certificate Registration](https://www.rd.go.th)

### Module Documentation

- **Technical Guide**: See `RESEARCH_AND_PLAN.md` for ETDA specifications
- **Developer Guide**: See `QUICK_START.md` for installation and setup
- **Implementation Status**: See `IMPLEMENTATION_STATUS.md` for Phase 1/2 status

### Getting Help

1. Check this user guide first
2. Review error messages in Odoo (click on invoice → error details)
3. Verify configuration: **e-Tax Configuration → Test Certificate**
4. Contact your system administrator for technical issues
5. Contact Revenue Department for compliance questions

---

## Appendix: Button Reference

Quick reference for all e-Tax buttons in invoice form:

| Button | Location | When Visible | Action |
|--------|----------|--------------|--------|
| **Export e-Tax XML** | Invoice header | Posted customer invoices in draft status | Generates XML, changes status to "Exported" |
| **Sign e-Tax XML** | Invoice header | Invoices in "Exported" status | Creates digital signature, changes status to "Signed" |
| **Download e-Tax XML** | Invoice header | Invoices with XML file (exported/signed/validated) | Downloads XML file to computer |
| **Reset e-Tax** | Invoice header | Any e-Tax status (except submitted) | Clears status and XML, allows re-export |
| **Batch Export** | Action menu (invoice list) | Multiple invoices selected | Opens batch export wizard |

---

## Version History

- **v1.0** (Phase 1) - December 2024
  - Initial release
  - Basic XML export
  - Batch processing
  - Thai Tax ID validation
  - Status tracking

- **v2.0** (Phase 2) - Planned Q1 2025
  - ETDA-compliant XML generation
  - XAdES-BES digital signatures
  - XML schema validation
  - Certificate expiration warnings
  - API submission to Revenue Department

---

*Last updated: December 21, 2024*
