# Thailand e-Tax Export Module

## 🇹🇭 Overview
This Odoo 19 module enables automatic generation of e-Tax XML files compliant with Thailand's Electronic Tax Invoice and Receipt System (ETDA Standard) as required by the Thai Revenue Department.

## ✨ Features

### Current Implementation (Phase 1 - Foundation)
- ✅ **Company Configuration:** Complete Thai tax registration and address management
- ✅ **Certificate Management:** Support for PKCS#11 and PKCS#12 digital certificates
- ✅ **Invoice Export:** Single invoice export with status tracking
- ✅ **Batch Export:** Export multiple invoices to XML or ZIP archive
- ✅ **Export Tracking:** Track export status, dates, and errors
- ✅ **User Interface:** Intuitive configuration and export wizards
- ✅ **Security:** Role-based access control for users and managers

### Planned Features (Phase 2 & 3)
- ⏳ **ETDA XML Generation:** Full compliance with ETDA XML standards
- ⏳ **XAdES-BES Signature:** Digital signature with Thai certificates
- ⏳ **Schema Validation:** Automatic validation against official ETDA schemas
- ⏳ **Multiple Document Types:** Tax invoices, receipts, debit/credit notes

## 📋 Requirements

### Odoo
- **Version:** Odoo 19.0 or later
- **Dependencies:** 
  - `base`
  - `account`
  - `l10n_th` (Thai localization - optional but recommended)

### Python Libraries (for Phase 2)
```bash
pip install lxml>=4.9.0
pip install xmlsec>=1.3.13
pip install cryptography>=40.0.0
pip install pyOpenSSL>=23.0.0
```

### System Requirements
- Python 3.8 or later
- Linux/macOS/Windows with Odoo 19

## 🚀 Installation

### Step 1: Install Module
1. Copy the `thailand_etax` folder to your Odoo addons directory:
   ```bash
   cp -r jaylinnyc/thailand_etax /path/to/odoo/addons/
   ```

2. Update Odoo apps list:
   ```
   Odoo → Apps → Update Apps List
   ```

3. Install the module:
   ```
   Search for "Thailand e-Tax Export" → Install
   ```

### Step 2: Configure Company Information
1. Navigate to: **Settings → Companies → [Your Company]**
2. Go to the **"e-Tax Thailand"** tab
3. Fill in required information:
   - **Tax ID:** 13-digit Thai Tax Identification Number
   - **Branch ID:** 5-digit branch code (00000 for head office)
   - **Address Details:** Complete Thai address following TISI1099-2548
   - **Contact Info:** Telephone, email, website

### Step 3: Configure e-Tax Settings
1. Navigate to: **Accounting → Configuration → e-Tax → e-Tax Settings**
2. Create a new configuration:
   - **Certificate Type:** Choose PKCS#12 (file) or PKCS#11 (smart card)
   - **Certificate Path:** Path to your .p12/.pfx file
   - **Certificate Password:** Password to unlock certificate
   - **Output Directory:** Where to save XML files
   - **Auto Sign:** Enable automatic digital signature
   - **Validate XML:** Enable XML schema validation

## 📖 Usage

### Export Single Invoice
1. Open a **posted** customer invoice
2. Click the **"Export e-Tax XML"** button in the header
3. The XML file is generated automatically
4. Click **"Download XML"** to save the file
5. Invoice status changes to "Exported"

### Batch Export
1. Go to: **Accounting → Configuration → e-Tax → Export Wizard**
2. Choose export type:
   - **Selected Invoices:** Pick specific invoices
   - **Date Range:** Export all invoices in a period
3. Configure options:
   - Include digital signature
   - Export format (individual XML or ZIP)
4. Click **"Export"**
5. Download the generated file(s)

### Check Export Status
- View invoice list with e-Tax status column
- Green badge = Successfully exported
- Red badge = Error during export
- Gray badge = Not yet exported

### Reset Export
If you need to re-export:
1. Open the invoice
2. Click **"Reset e-Tax"** (requires Manager role)
3. Confirm the action
4. Export again

## 📁 Module Structure

```
thailand_etax/
├── __init__.py
├── __manifest__.py
├── README.md                    # This file
├── RESEARCH_AND_PLAN.md        # Detailed implementation plan
├── QUICK_START.md              # Developer quick start guide
├── IMPLEMENTATION_STATUS.md    # Current status and roadmap
├── models/
│   ├── __init__.py
│   ├── etax_config.py          # Certificate & export configuration
│   ├── res_company.py          # Company Thai tax fields
│   └── account_move.py         # Invoice e-Tax functionality
├── wizards/
│   ├── __init__.py
│   └── etax_export_wizard.py   # Batch export wizard
├── views/
│   ├── etax_config_views.xml
│   ├── res_company_views.xml
│   ├── account_move_views.xml
│   └── etax_export_wizard_views.xml
├── security/
│   └── ir.model.access.csv
└── schemas/                     # Reference implementations (git ignored)
    ├── soda-etax/              # ETDA XML schemas
    └── etax-xades/             # XAdES signature reference
```

## 🔒 Security & Permissions

### User Roles
- **Accountant User:** Can export and download XML files
- **Accountant Manager:** Full access including configuration and reset

### Certificate Security
- Passwords stored encrypted in Odoo database
- Certificate files not stored in database
- Supports hardware security modules (PKCS#11)

## ⚙️ Configuration Examples

### PKCS#12 Certificate (File-based)
```
Certificate Type: PKCS#12
Certificate Path: /path/to/certificate.p12
Certificate Password: ********
Auto Sign: Yes
```

### PKCS#11 Smart Card
```
Certificate Type: PKCS#11
PKCS#11 Library: /usr/lib/opensc-pkcs11.so
Slot ID: 0
Certificate Password: ********
Auto Sign: Yes
```

## 🐛 Troubleshooting

### "Company Tax ID is not configured"
- Go to Settings → Companies → e-Tax Thailand tab
- Enter your 13-digit Thai Tax ID
- Must pass validation (mod 11 checksum)

### "Customer Tax ID is required"
- Update customer record with Thai Tax ID
- Go to Contacts → [Customer] → Tax ID field

### "e-Tax configuration not found"
- Create configuration: Accounting → Configuration → e-Tax Settings
- Must be marked as Active

### "Invalid Thai Tax ID"
- Verify the 13-digit number is correct
- Check digit must match mod 11 algorithm
- Remove any spaces or special characters

## 📚 Standards Compliance

This module implements:
- **ETDA Standards:** Electronic Transactions Development Agency XML format
- **UN/CEFACT:** Cross Industry Invoice standards
- **XAdES-BES:** XML Advanced Electronic Signatures
- **TISI1099-2548:** Thai address standards

## 🔗 References

- **Thai Revenue Department:** https://etax.rd.go.th
- **ETDA Portal:** https://www.etda.or.th
- **Official Schemas:** https://etax.rd.go.th/etax_staticpage/app/download/XMLSchemaV2.zip
- **ETDA GitHub:** https://github.com/ETDA
  - soda-etax: https://github.com/ETDA/soda-etax
  - etax-xades: https://github.com/ETDA/etax-xades

## 🛠️ Development

### Current Status
**Phase 1 Complete:** Foundation, UI, and basic export functionality
**Phase 2 In Progress:** ETDA-compliant XML generation

See `IMPLEMENTATION_STATUS.md` for detailed progress.

### Contributing
This module is part of the Nexus Panya19 production system.
For development guidelines, see `RESEARCH_AND_PLAN.md`.

## 📄 License
LGPL-3

## 👥 Credits
- **Author:** Nexus
- **Based on:** ETDA official standards and reference implementations
- **Odoo Version:** 19.0

## 📞 Support

### Technical Issues
- Check `IMPLEMENTATION_STATUS.md` for known limitations
- Review `QUICK_START.md` for setup instructions

### ETDA Standards Questions
- Thai Revenue Department: https://etax.rd.go.th
- ETDA Support: https://www.etda.or.th/contact

---

**Version:** 19.0.1.0.0  
**Last Updated:** December 21, 2025  
**Status:** Phase 1 Complete - Foundation Ready for Testing
