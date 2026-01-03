# Odoo Analysis Scripts

This folder contains Python scripts to analyze your Odoo 19 instance and determine what's needed for the e-Tax export feature.

## Scripts

### Configuration
- `config.py` - Odoo connection configuration
- `odoo_client.py` - Reusable Odoo API client

### Analysis Scripts
1. `01_check_invoice_fields.py` - Check what fields exist on invoices
2. `02_check_tax_config.py` - Check tax configuration (VAT, WHT)
3. `03_check_company_partner_fields.py` - Check Thai address fields
4. `04_check_uom.py` - Check Unit of Measure configuration
5. `05_check_sample_invoice.py` - Get sample invoice data

### Run All
- `run_all_checks.py` - Run all scripts in sequence

## Usage

### Run Individual Script
```bash
cd analysis
python3 01_check_invoice_fields.py
```

### Run All Scripts
```bash
cd analysis
python3 run_all_checks.py
```

## Output

Each script will:
1. Print results to console
2. Save detailed JSON output to analysis/ folder

### Output Files
- `invoice_fields.json` - All invoice fields
- `tax_config.json` - Tax configuration
- `company_partner_fields.json` - Company/partner fields
- `uom_config.json` - UoM configuration
- `sample_invoices.json` - Sample invoice data

## What We're Looking For

### Already in Odoo (No need to add)
- ✅ Credit note reference: `reversed_entry_id`
- ✅ Payment terms: `invoice_payment_term_id`, `invoice_date_due`
- ✅ Tax amounts: `amount_tax`, `amount_untaxed`, `amount_total`

### Need to Check
- ❓ Thai address fields: `etax_sub_district`, `etax_district`, etc.
- ❓ Withholding tax configuration
- ❓ UoM UN/CEFACT codes: `etax_code`, `etax_name_th`
- ❓ Export tracking fields: `etax_exported`, `etax_export_date`

## Next Steps

After running the analysis:
1. Review JSON output files
2. Determine what fields truly need to be added
3. Update e-Tax module to use existing fields where possible
4. Only create new fields for what's missing
