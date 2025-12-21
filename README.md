# Thailand e-Tax Export Module for Odoo 19

## 🇹🇭 Overview

This Odoo 19 module enables automatic generation of e-Tax XML files compliant with Thailand's Electronic Tax Invoice and Receipt System (ETDA Standard) as required by the Thai Revenue Department.

**Architecture:** This module generates unsigned XML documents and integrates with an external [on-premise signing service](https://github.com/jaylinnyc/thailand-etax-signing-service) that handles PKCS#11 hardware token digital signing.

## ✨ Features

- ✅ **ETDA XML Generation:** Full compliance with ETDA XML standards
- ✅ **Company Configuration:** Thai tax registration and address management
- ✅ **Invoice Export:** Single invoice export with status tracking
- ✅ **Batch Export:** Export multiple invoices to XML or ZIP archive
- ✅ **Signing Service Integration:** Connect to on-premise signing service
- ✅ **Callback Support:** Receive signed documents automatically
- ✅ **Status Tracking:** Track export, signing, and submission status
- ✅ **Export Wizard:** User-friendly batch export interface
- ✅ **Security:** Role-based access control

## 📋 Requirements

### Odoo
- **Version:** Odoo 19.0 or later
- **Dependencies:** 
  - `base`
  - `account`
  - `l10n_th` (Thai localization - optional but recommended)

### Signing Service
For digital signatures, you need to deploy the [Thailand e-Tax Signing Service](https://github.com/jaylinnyc/thailand-etax-signing-service) on-premise.

## 🚀 Installation

### Step 1: Install Module

```bash
# Copy to Odoo addons directory
cp -r nexus_odoo_thailand_etax /path/to/odoo/addons/thailand_etax

# Update Odoo apps list
# Odoo → Apps → Update Apps List

# Install the module
# Search for "Thailand e-Tax Export" → Install
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
2. Create/edit configuration:
   - **Signing Service URL:** URL of your on-premise signing service (e.g., `http://localhost:8443`)
   - **API Key:** Authentication key for signing service
   - **Auto Sign:** Enable automatic sending to signing service
   - **Auto Submit to RD:** Automatically submit to Revenue Department after signing

## 📖 Usage

### Export Single Invoice

1. Open a **posted** customer invoice
2. Click **"Generate e-Tax XML"** button
3. The unsigned XML file is generated
4. Click **"Send to Signing Service"** to sign
5. Signed document will be returned via callback

### Batch Export

1. Go to: **Accounting → Configuration → e-Tax → Export Wizard**
2. Choose export type:
   - **Selected Invoices:** Pick specific invoices
   - **Date Range:** Export all invoices in a period
3. Configure options and click **"Export"**

### Status Tracking

| Status | Description |
|--------|-------------|
| Draft | Not yet exported |
| Exported | XML generated (unsigned) |
| Pending Signature | Sent to signing service |
| Signed | Digital signature applied |
| Submitted | Sent to Revenue Department |
| Confirmed | Confirmed by Revenue Department |
| Error | Error occurred |

## 📁 Module Structure

```
nexus_odoo_thailand_etax/
├── __init__.py
├── __manifest__.py
├── README.md
├── models/
│   ├── account_move.py         # Invoice e-Tax functionality
│   ├── etax_config.py          # Signing service configuration
│   ├── res_company.py          # Company Thai tax fields
│   └── res_partner.py          # Partner tax ID fields
├── controllers/
│   └── etax_callback.py        # Callback endpoint for signing service
├── wizards/
│   └── etax_export_wizard.py   # Batch export wizard
├── views/
│   ├── account_move_views.xml
│   ├── etax_config_views.xml
│   ├── etax_export_wizard_views.xml
│   ├── res_company_views.xml
│   └── res_partner_views.xml
├── lib/
│   ├── etax_tax_invoice.py     # XML generation for tax invoices
│   ├── etax_validator.py       # Invoice validation
│   └── etax_xml_builder.py     # XML builder utilities
├── security/
│   └── ir.model.access.csv
└── docs/                       # Additional documentation
```

## 🔗 Integration Architecture

```
┌─────────────────┐        ┌───────────────────────────┐        ┌──────────────┐
│    Odoo 19      │   →    │  Signing Service (Java)   │   →    │  Thai RD     │
│  (this module)  │   ←    │  (PKCS#11 USB Token)      │   ←    │  e-Tax API   │
└─────────────────┘        └───────────────────────────┘        └──────────────┘
     │                              │
     │ 1. Generate XML              │ 2. Sign with XAdES-BES
     │ 3. Send unsigned XML ────────▶
     │ ◀──────── 4. Callback with signed XML
     │                              │ 5. Submit to RD (optional)
     │ ◀──────── 6. Callback with RD confirmation
```

## 🔒 Security

### User Roles
- **Accountant User:** Export and download XML files
- **Accountant Manager:** Full access including configuration

### API Security
- Signing service requires API key authentication
- Callback endpoint validates requests
- Sensitive data (certificates) stored on signing service only

## 📄 License

LGPL-3

## 🤝 Support

For issues or questions:
- Signing Service: [thailand-etax-signing-service](https://github.com/jaylinnyc/thailand-etax-signing-service)
- Odoo Module: [nexus_odoo_thailand_etax](https://github.com/jaylinnyc/nexus_odoo_thailand_etax)
