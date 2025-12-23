# Thailand e-Tax Invoice Export Module for Odoo 19

## 🇹🇭 Overview

This Odoo 19 module provides a simple interface to export customer invoices and credit notes to Excel format for Thailand e-Tax processing.

The exported Excel file can be loaded into your separate e-Tax system to validate, convert to XML, and sign with digital certificates.

## ✨ Features

- ✅ **e-Tax Invoice List:** View all posted customer invoices and credit notes
- ✅ **Excel Export:** Export selected invoices to Excel format
- ✅ **Line Items:** Includes detailed line item information
- ✅ **Export Tracking:** Track which invoices have been exported
- ✅ **Batch Processing:** Export multiple invoices at once
- ✅ **Date Filters:** Filter by date range, month, quarter, year
- ✅ **Export Status:** Filter by exported/not exported status

## 📋 Requirements

### Odoo
- **Version:** Odoo 19.0 or later
- **Dependencies:** 
  - `base`
  - `account`

### Python Libraries
- `xlsxwriter` - For Excel file generation

```bash
pip install xlsxwriter
```

## 🚀 Installation

### Step 1: Install xlsxwriter

```bash
pip install xlsxwriter
```

### Step 2: Install Module

```bash
# Copy to Odoo addons directory
cp -r nexus_odoo_thailand_etax /path/to/odoo/addons/

# Update Odoo apps list
# Odoo → Apps → Update Apps List

# Install the module
# Search for "Thailand e-Tax" → Install
```

## 📖 Usage

### Accessing e-Tax Invoices

Navigate to: **Accounting → Reports → e-Tax Invoices**

This view shows all posted customer invoices and credit notes that can be exported.

### Export to Excel

1. **Select invoices** you want to export (use checkboxes)
2. Click the **"Export to Excel"** button
3. In the wizard:
   - Review selected invoices
   - Or set a date range to export all invoices in that period
   - Choose whether to include previously exported invoices
   - Choose whether to mark as exported after download
4. Click **"Export"**
5. Click **"Download Excel File"** to download

### Excel File Contents

The exported Excel file contains two sheets:

#### Sheet 1: e-Tax Invoices (Header Information)
| Column | Description |
|--------|-------------|
| Document Type | Tax Invoice or Credit Note |
| Invoice Number | Odoo invoice number |
| Invoice Date | Invoice date |
| Due Date | Payment due date |
| Customer Name | Customer/partner name |
| Customer Tax ID | VAT/Tax ID of customer |
| Customer Branch | Branch ID (default: 00000) |
| Customer Address | Full address |
| Seller Name | Your company name |
| Seller Tax ID | Your company VAT/Tax ID |
| Seller Branch | Your branch ID |
| Subtotal | Amount before tax |
| Tax Amount | VAT amount |
| Total Amount | Total including tax |
| Currency | Invoice currency |
| Reference | Invoice reference |
| Payment Terms | Payment terms |
| Salesperson | Sales person name |

#### Sheet 2: Line Items (Detail Information)
| Column | Description |
|--------|-------------|
| Invoice Number | Parent invoice number |
| Line # | Line sequence |
| Product Code | Internal reference/SKU |
| Product Name | Product name |
| Description | Line description |
| Quantity | Quantity |
| UoM | Unit of measure |
| Unit Price | Price per unit |
| Discount % | Discount percentage |
| Subtotal | Line subtotal |
| Tax | Tax names applied |
| Tax Amount | Tax amount for line |

### Filters Available

- **Invoices / Credit Notes** - Filter by document type
- **Not Exported / Exported** - Filter by export status  
- **This Month / Last Month** - Quick date filters
- **This Quarter / This Year** - Period filters
- **Group By** - Customer, Date, Type, Export Status

## 📁 Module Structure

```
nexus_odoo_thailand_etax/
├── __init__.py
├── __manifest__.py
├── README.md
├── models/
│   ├── __init__.py
│   └── account_move.py          # Invoice export tracking fields
├── wizards/
│   ├── __init__.py
│   └── etax_excel_export_wizard.py  # Excel export wizard
├── views/
│   ├── etax_invoice_report_views.xml    # Invoice list view
│   ├── etax_excel_export_wizard_views.xml  # Export wizard view
│   └── menu_views.xml           # Menu configuration
└── security/
    └── ir.model.access.csv      # Access rights
```

## 🔧 Technical Notes

### Fields Added to account.move

| Field | Type | Description |
|-------|------|-------------|
| `etax_exported` | Boolean | Whether exported for e-Tax |
| `etax_export_date` | Datetime | When exported |
| `etax_export_batch` | Char | Export batch identifier |

### Reset Export Status

To re-export an invoice, you can reset its export status:
1. Open the invoice
2. Use developer mode to access the e-Tax fields
3. Set `etax_exported` to False

Or use the wizard with "Include Previously Exported" option checked.

## 📝 License

LGPL-3

## 👥 Authors

- Nexus (https://nexus.co.th)

