# Thailand e-Tax Invoice Export Module for Odoo 19

## 🇹🇭 Overview

This Odoo 19 module provides a comprehensive interface to export customer invoices and credit notes to Excel format for Thailand e-Tax processing, fully compliant with Thai Revenue Department requirements.

The exported Excel file can be loaded into your separate e-Tax signing system to validate, convert to XML, and sign with digital certificates.

## ✨ Features

- ✅ **Comprehensive e-Tax Export:** Export invoices with all required Thai RD fields
- ✅ **Line-Item Detail:** One row per line item with complete product information
- ✅ **UN/CEFACT Unit Codes:** Proper unit mapping for Thai tax compliance
- ✅ **Thai Address Support:** Sub-district, district, province breakdown
- ✅ **Reference Documents:** Support for credit/debit note references
- ✅ **Withholding Tax:** Track and export WHT information
- ✅ **Payment Terms:** Include payment terms and due dates
- ✅ **Tax ID Validation:** Automatic 13-digit tax ID formatting
- ✅ **Export Tracking:** Track which invoices have been exported
- ✅ **Batch Processing:** Export multiple invoices at once
- ✅ **Validation:** Skip invoices with missing required fields

## 📋 Requirements

### Odoo
- **Version:** Odoo 19.0 or later
- **Dependencies:** 
  - `base`
  - `account`
  - `uom`

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

### Step 3: Configure Thai Address Fields

After installation:
1. Go to **Settings → Companies → Your Company**
2. Fill in the **e-Tax** tab with Thai address details:
   - Tax ID (13 digits)
   - Branch ID (5 digits, 00000 for head office)
   - Sub-district (ตำบล/แขวง)
   - District (อำเภอ/เขต)
   - Province (จังหวัด)

3. Update **Partner** records with Thai address details:
   - Contacts → Customers
   - Fill in e-Tax fields in each customer record

## 📖 Usage

### Accessing e-Tax Export

Navigate to: **Accounting → Customers → Invoices**

Select the invoices you want to export and use the **Actions → Export to e-Tax (Excel)** menu.

### Export to Excel

1. **Select invoices** you want to export (use checkboxes)
2. Click **Actions → Export to e-Tax (Excel)**
3. In the wizard:
   - Review selected invoices
   - Choose whether to include previously exported invoices
   - Choose whether to include finalized invoices
   - Choose whether to mark as exported after download
4. Click **"Export"**
5. Click **"Download Excel File"** to download

### Excel File Format

The exported Excel file follows the Thailand e-Tax specification with one row per line item.

#### Export Columns (50 fields)

**Document Header:**
- `document_type` - Thai RD code (388=Tax Invoice, 81=Credit Note, 80=Debit Note)
- `document_number` - Invoice number
- `issue_date` - Invoice date (YYYY-MM-DD)
- `purpose` - Document purpose

**Seller Information (15 fields):**
- Company name, 13-digit tax ID, branch code
- Full Thai address breakdown (address, subdistrict, district, province, postcode)
- Contact information (phone, email)

**Buyer Information (15 fields):**
- Customer name, 13-digit tax ID, branch code
- Full Thai address breakdown
- Contact information

**Line Item Details:**
- `line_id` - Line sequence number
- `item_name` - Product name
- `description` - Product description
- `quantity` - Quantity
- `unit` - UN/CEFACT unit code (e.g., C62, EA, KGM, MTR)
- `unit_name` - Thai unit name (e.g., หน่วย, ชิ้น, กิโลกรัม)
- `unit_price` - Price per unit
- `discount` - Line discount amount
- `amount` - Line total

**Totals:**
- `subtotal` - Amount before tax
- `total_discount` - Total discount
- `vat_rate` - VAT percentage (typically 7%)
- `vat_amount` - VAT amount
- `grand_total` - Total including VAT

**Reference Documents (Credit/Debit Notes):**
- `reference_number` - Original invoice number
- `reference_date` - Original invoice date

**Withholding Tax:**
- `withholding_tax_rate` - WHT rate %
- `withholding_tax_amount` - WHT amount

**Payment Terms:**
- `payment_terms` - Payment terms description
- `due_date` - Payment due date

### Unit of Measure Mapping

The module automatically maps Odoo UoM to UN/CEFACT codes required by Thai e-Tax:

| Odoo UoM | UN/CEFACT Code | Thai Name |
|----------|----------------|-----------|
| Unit | C62 | หน่วย |
| Piece | EA | ชิ้น |
| Box | BX | กล่อง |
| Set | SET | ชุด |
| Kilogram | KGM | กิโลกรัม |
| Gram | GRM | กรัม |
| Meter | MTR | เมตร |
| Liter | LTR | ลิตร |
| Hour | HUR | ชั่วโมง |
| Day | DAY | วัน |

You can customize these mappings in **Inventory → Configuration → Units of Measure** by setting the **e-Tax Code** and **Thai Unit Name** fields.

### Managing e-Tax Fields on Invoices

Each invoice has an **e-Tax** tab where you can:

1. **View Export Status:**
   - Whether exported
   - Export date and batch ID
   - Finalization status

2. **Set Reference Documents** (for Credit/Debit Notes):
   - Reference Invoice Number
   - Reference Invoice Date

3. **Set Withholding Tax:**
   - WHT Rate (%)
   - WHT Amount

### Validation and Warnings

The export process validates:
- ✅ Seller tax ID is exactly 13 digits
- ✅ Buyer tax ID is exactly 13 digits
- ✅ Invoice has at least one product line
- ✅ Credit/Debit notes have reference documents (warning only)
- ✅ Unit codes are properly mapped

Invoices with missing required fields will be skipped, and a warning will be logged.

## 🔧 Configuration

### Company Setup

**Settings → Companies → Your Company → e-Tax tab:**

| Field | Required | Format | Example |
|-------|----------|--------|---------|
| Tax ID | Yes | 13 digits | 1234567890123 |
| Branch ID | Yes | 5 digits | 00000 |
| Sub-district | Recommended | Text | บางรัก |
| District | Recommended | Text | บางรัก |
| Province | Recommended | Text | กรุงเทพมหานคร |

### Customer/Partner Setup

**Contacts → Customers → e-Tax tab:**

Same fields as company setup. Ensure all customers have:
- Valid 13-digit Thai tax ID
- Branch ID (00000 for head office)
- Complete Thai address

### Unit of Measure Setup

**Inventory → Configuration → Units of Measure:**

For each UoM, you can set:
- **e-Tax UN/CEFACT Code** - Standard code (e.g., EA, C62, KGM)
- **Thai Unit Name** - Thai translation (e.g., ชิ้น, หน่วย)

The system will auto-map common units, but you can override for custom UoMs.

## 📁 Module Structure

```
nexus_odoo_thailand_etax/
├── __init__.py
├── __manifest__.py
├── README.md
├── models/
│   ├── __init__.py
│   ├── account_move.py          # Invoice e-Tax fields & tracking
│   ├── res_company.py           # Company Thai address fields
│   ├── res_partner.py           # Partner Thai address fields
│   └── uom_uom.py              # UoM e-Tax code mapping
├── wizards/
│   ├── __init__.py
│   └── etax_excel_export_wizard.py  # Excel export wizard
├── views/
│   ├── account_move_views.xml      # Invoice e-Tax tab
│   ├── res_company_views.xml       # Company e-Tax fields
│   ├── res_partner_views.xml       # Partner e-Tax fields
│   ├── uom_uom_views.xml          # UoM e-Tax fields
│   ├── etax_excel_export_wizard_views.xml
│   ├── etax_invoice_report_views.xml
│   └── menu_views.xml
├── data/
│   ├── etax_data.xml              # Base configuration
│   └── etax_uom_mapping.xml       # UoM UN/CEFACT mappings
└── security/
    └── ir.model.access.csv
```

## 🔧 Technical Details

### Fields Added to Models

#### account.move (Invoices)

| Field | Type | Description |
|-------|------|-------------|
| `etax_exported` | Boolean | Whether exported for e-Tax |
| `etax_export_date` | Datetime | When exported |
| `etax_export_batch` | Char | Export batch identifier |
| `etax_finalized` | Boolean | Whether finalized (locked) |
| `etax_finalized_date` | Datetime | When finalized |
| `etax_finalized_by` | Many2one(res.users) | Who finalized |
| `etax_reference_number` | Char | Reference invoice number |
| `etax_reference_date` | Date | Reference invoice date |
| `etax_withholding_tax_rate` | Float | WHT rate % |
| `etax_withholding_tax_amount` | Monetary | WHT amount |

#### res.company & res.partner

| Field | Type | Description |
|-------|------|-------------|
| `etax_tax_id` | Char(13) | Thai tax ID (company only) |
| `etax_branch_id` | Char(5) | Branch ID (00000=head office) |
| `etax_building_name` | Char | Building name |
| `etax_floor_number` | Char | Floor number |
| `etax_room_number` | Char | Room number |
| `etax_moo` | Char | Moo (village group) |
| `etax_soi` | Char | Soi (lane/alley) |
| `etax_sub_district` | Char | Sub-district (ตำบล/แขวง) |
| `etax_district` | Char | District (อำเภอ/เขต) |
| `etax_province` | Char | Province (จังหวัด) |

#### uom.uom

| Field | Type | Description |
|-------|------|-------------|
| `etax_code` | Char(10) | UN/CEFACT unit code |
| `etax_name_th` | Char | Thai unit name |

### Document Type Mapping

| Odoo Type | Thai RD Code | Description |
|-----------|--------------|-------------|
| `out_invoice` | 388 | Tax Invoice |
| `out_refund` | 81 | Credit Note |
| Debit Note | 80 | Debit Note (if supported) |

### Tax ID Formatting

The export automatically:
- Removes "TH" prefix from VAT field
- Removes all hyphens and spaces
- Validates exactly 13 digits
- Rejects invoices with invalid tax IDs

### Branch Code Formatting

The export automatically:
- Removes non-digit characters
- Pads with leading zeros to 5 digits
- Defaults to "00000" if not set

## 🐛 Troubleshooting

### Invoice Not Appearing in Export

**Check:**
1. Invoice is **Posted** (not draft)
2. Invoice type is **Customer Invoice** or **Customer Credit Note**
3. Invoice has not been **Finalized** (if "Include Finalized" is unchecked)

### Tax ID Validation Errors

**Problem:** Invoice skipped with "Invalid tax ID" warning

**Solution:**
1. Check company tax ID: Settings → Companies → Your Company → e-Tax tab
2. Check customer tax ID: Contacts → Customer → e-Tax tab
3. Ensure tax ID is exactly 13 digits
4. Remove any hyphens or spaces (system will auto-clean)

### Missing Unit Codes

**Problem:** Unit shows as "C62" instead of proper code

**Solution:**
1. Go to Inventory → Configuration → Units of Measure
2. Find your UoM
3. Set **e-Tax Code** and **Thai Unit Name**
4. Re-export the invoice

### Missing Thai Address Fields

**Problem:** Address columns are empty in export

**Solution:**
1. Fill in e-Tax address fields for company and customers
2. Fields are in the **e-Tax** tab of company/partner form

## 📄 Export File Specification

### Filename Format
```
etax_export_YYYYMMDD_HHMMSS.xlsx
```

### File Format
- **Type:** Excel 2007+ (.xlsx)
- **Encoding:** UTF-8 (supports Thai characters)
- **Header Row:** First row with column names
- **Data Rows:** One row per invoice line item
- **Multi-Line Invoices:** Same document_number repeated across rows

### Example Export

```
document_type | document_number | issue_date | ... | line_id | item_name | quantity | unit | unit_name
388          | INV-2024-001    | 2024-01-15 | ... | 1       | Product A | 10       | EA   | ชิ้น
388          | INV-2024-001    | 2024-01-15 | ... | 2       | Product B | 5        | KGM  | กิโลกรัม
388          | INV-2024-002    | 2024-01-16 | ... | 1       | Product C | 2        | C62  | หน่วย
```

## 📝 Version History

### Version 19.0.2.0.0 (Current)
- ✅ Added UN/CEFACT unit code mapping
- ✅ Added reference document fields for credit/debit notes
- ✅ Added withholding tax tracking
- ✅ Added payment terms and due date
- ✅ Updated document type codes (388, 81, 80)
- ✅ Improved tax ID validation and formatting
- ✅ Added comprehensive validation logic
- ✅ Enhanced export with all Thai RD required fields

### Version 19.0.1.0.0
- Initial release
- Basic invoice export functionality

## 🔒 Security

- Export requires **Billing** or **Accounting** access rights
- Finalization requires **Billing Manager** rights
- Un-finalization requires **Accounting Manager** rights

## 📝 License

LGPL-3

## 👥 Authors

- Nexus (https://nexus.co.th)

## 🙏 Support

For issues, questions, or feature requests:
- Contact: Nexus Support
- Website: https://nexus.co.th

## 🌟 Credits

Developed for compliance with Thailand Revenue Department e-Tax requirements.


