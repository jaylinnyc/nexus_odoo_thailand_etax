# Post-Update Checklist for nexus_odoo_thailand_etax Module

## Pre-Deployment Checks ✅

### 1. File Integrity
- [x] All new files created
- [x] All existing files updated
- [x] No syntax errors (Odoo imports are expected warnings)
- [x] Version bumped to 19.0.2.0.0
- [x] Manifest updated with new dependencies

### 2. Module Structure
```
✅ models/account_move.py - Updated with new fields
✅ models/res_company.py - Existing (no changes needed)
✅ models/res_partner.py - Existing (no changes needed)
✅ models/uom_uom.py - NEW FILE
✅ models/__init__.py - Updated to import uom_uom

✅ wizards/etax_excel_export_wizard.py - Major update to _generate_excel()

✅ views/account_move_views.xml - NEW FILE
✅ views/uom_uom_views.xml - NEW FILE
✅ views/res_company_views.xml - Existing
✅ views/res_partner_views.xml - Existing
✅ views/etax_excel_export_wizard_views.xml - Existing

✅ data/etax_data.xml - Existing
✅ data/etax_uom_mapping.xml - NEW FILE

✅ __manifest__.py - Updated
✅ README.md - Completely rewritten
✅ UPGRADE_SUMMARY.md - NEW FILE (this document)
```

---

## Deployment Steps

### Step 1: Backup Current System
```bash
# Backup database
pg_dump your_database > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup module (if overwriting)
cp -r jaylinnyc/nexus_odoo_thailand_etax jaylinnyc/nexus_odoo_thailand_etax.backup_$(date +%Y%m%d)
```

### Step 2: Update Module in Odoo
```bash
# Option A: Via command line (recommended)
./odoo-bin -u nexus_odoo_thailand_etax -d your_database --stop-after-init

# Option B: Via web interface
# 1. Apps → Update Apps List
# 2. Search "Thailand e-Tax"
# 3. Click "Upgrade"
```

### Step 3: Verify Installation
After upgrade, check:
- [ ] No errors in Odoo log
- [ ] Module shows version 19.0.2.0.0
- [ ] e-Tax tab appears on invoices
- [ ] e-Tax tab appears on Company settings
- [ ] e-Tax tab appears on Customer/Partner forms
- [ ] e-Tax fields appear on UoM forms

### Step 4: Configure Data

#### Company Configuration
1. Settings → Companies → Your Company
2. Click "e-Tax" tab
3. Fill in:
   - [ ] Tax ID (13 digits)
   - [ ] Branch ID (5 digits, e.g., 00000)
   - [ ] Sub-district (ตำบล/แขวง)
   - [ ] District (อำเภอ/เขต)
   - [ ] Province (จังหวัด)

#### Customer Configuration (Sample)
1. Contacts → Customers
2. Open a customer record
3. Click "e-Tax" tab
4. Fill in Thai address fields (same as above)

#### UoM Verification
1. Inventory → Configuration → Units of Measure
2. Open "Unit"
   - [ ] Check etax_code = "C62"
   - [ ] Check etax_name_th = "หน่วย"
3. Open "Kilogram"
   - [ ] Check etax_code = "KGM"
   - [ ] Check etax_name_th = "กิโลกรัม"

---

## Testing Procedures

### Test 1: Basic Export
1. Accounting → Customers → Invoices
2. Create a test invoice with 1 product line
3. Post the invoice
4. Select it and choose Actions → Export to e-Tax (Excel)
5. Verify:
   - [ ] Export succeeds
   - [ ] Excel file downloads
   - [ ] Filename format: `etax_export_YYYYMMDD_HHMMSS.xlsx`
   - [ ] File opens in Excel without errors
   - [ ] Header row has 50 columns
   - [ ] Data row present with invoice data

### Test 2: Multi-Line Invoice
1. Create invoice with 3+ product lines
2. Post and export
3. Verify:
   - [ ] 3 rows in Excel (one per line)
   - [ ] Same document_number on all rows
   - [ ] Line_id: 1, 2, 3
   - [ ] Different item_name on each row
   - [ ] Same totals on all rows

### Test 3: Document Type Codes
1. Export a Tax Invoice
   - [ ] document_type = "388"
2. Create and export a Credit Note
   - [ ] document_type = "81"

### Test 4: Unit Codes
1. Create invoice with products using different UoM:
   - Product A: Unit → Check unit="C62", unit_name="หน่วย"
   - Product B: Kg → Check unit="KGM", unit_name="กิโลกรัม"
   - Product C: Piece → Check unit="EA", unit_name="ชิ้น"

### Test 5: Tax ID Formatting
1. Set company VAT to "TH-1-2345-67890-12-3"
2. Export invoice
3. Verify seller_tax_id in Excel = "1234567890123" (cleaned)

### Test 6: Thai Characters
1. Set Thai text in:
   - Company sub-district = "บางรัก"
   - Customer sub-district = "สาทร"
2. Export invoice
3. Open in Excel
4. Verify Thai text displays correctly

### Test 7: Reference Documents (Credit Note)
1. Create a Credit Note
2. Open the credit note
3. Go to e-Tax tab
4. Set:
   - Reference Invoice Number = "INV-2024-001"
   - Reference Invoice Date = "2024-01-15"
5. Export
6. Verify Excel has these values in reference_number and reference_date columns

### Test 8: Withholding Tax
1. Open an invoice
2. Go to e-Tax tab
3. Set:
   - WHT Rate = 3
   - WHT Amount = 150.00
4. Export
5. Verify Excel has 3 and 150.00 in WHT columns

### Test 9: Validation (Negative Tests)
1. Create invoice with customer having no tax ID
2. Try to export
3. Verify:
   - [ ] Invoice is skipped
   - [ ] Warning logged in Odoo
   - [ ] Other valid invoices still export

### Test 10: Payment Terms
1. Create invoice with Payment Terms = "Net 30"
2. Set invoice date = 2024-01-01
3. Set due date = 2024-01-31
4. Export
5. Verify:
   - [ ] payment_terms = "Net 30"
   - [ ] due_date = "2024-01-31"

---

## Troubleshooting

### Issue: Module upgrade fails

**Solution:**
```bash
# Check Odoo log
tail -f /var/log/odoo/odoo-server.log

# Common issues:
# - XML syntax error → Check views/*.xml files
# - Python syntax error → Check models/*.py files
# - Missing dependency → Check __manifest__.py
```

### Issue: Excel export shows old format (no new columns)

**Possible causes:**
- Module not upgraded (still version 19.0.1.0.0)
- Browser cache (reload wizard page)
- Old wizard instance (close and reopen)

**Solution:**
```bash
# Force upgrade
./odoo-bin -u nexus_odoo_thailand_etax -d your_database --stop-after-init

# Or restart Odoo service
sudo systemctl restart odoo
```

### Issue: Unit codes show as "C62" for all products

**Cause:** UoM mapping data not loaded

**Solution:**
```bash
# Reload data
./odoo-bin -d your_database -i nexus_odoo_thailand_etax --stop-after-init

# Or manually update UoM records:
# Inventory → Configuration → Units of Measure
# Edit each UoM and set e-Tax Code and Thai Unit Name
```

### Issue: Thai characters show as "???" in Excel

**Cause:** Excel not recognizing UTF-8

**Solution:**
1. Open Excel file
2. Data → Get Data → From File → From Text/CSV
3. Choose file, select encoding: UTF-8
4. Import

Or ensure Excel is set to UTF-8 by default.

### Issue: Invoice skipped during export (validation error)

**Check:**
1. Company tax ID is exactly 13 digits
2. Customer tax ID is exactly 13 digits
3. Invoice has at least one product line
4. Invoice is in "Posted" state

**Debug:**
```bash
# Check Odoo log for details
grep "Invalid" /var/log/odoo/odoo-server.log
```

---

## Rollback Plan (If Needed)

If issues arise, you can rollback:

### Option 1: Restore Backup
```bash
# Stop Odoo
sudo systemctl stop odoo

# Restore database backup
psql your_database < backup_YYYYMMDD_HHMMSS.sql

# Restore module files
rm -rf jaylinnyc/nexus_odoo_thailand_etax
cp -r jaylinnyc/nexus_odoo_thailand_etax.backup_YYYYMMDD jaylinnyc/nexus_odoo_thailand_etax

# Restart Odoo
sudo systemctl start odoo
```

### Option 2: Downgrade Module
```bash
# Checkout previous version from git
cd jaylinnyc/nexus_odoo_thailand_etax
git checkout <previous_commit_hash>

# Downgrade module
./odoo-bin -u nexus_odoo_thailand_etax -d your_database --stop-after-init
```

---

## Performance Notes

**Expected Performance:**
- Export 100 invoices with 5 lines each = ~500 rows
- Expected time: < 5 seconds
- File size: ~200 KB

**Large Dataset:**
- 1000+ invoices: Consider batching
- File size: May exceed 10 MB
- Consider splitting into multiple exports by date range

---

## User Communication

### Announcement Template

```
Subject: Updated Thailand e-Tax Export Module

Dear Team,

We have updated the Thailand e-Tax export module to comply with the latest 
Thai Revenue Department requirements.

New Features:
✅ UN/CEFACT unit codes for products
✅ Reference document tracking for credit notes
✅ Withholding tax information
✅ Payment terms and due dates
✅ Enhanced validation

What You Need to Do:
1. Update company Thai address fields (Settings → Companies)
2. Update customer Thai address fields (Contacts → Customers)
3. Review and test the new export format

Training Session:
Date: [TBD]
Time: [TBD]
Location: [TBD]

Questions? Contact IT Support.
```

---

## Sign-Off

### Pre-Deployment
- [ ] All files reviewed
- [ ] Backup completed
- [ ] Module upgraded successfully
- [ ] Basic configuration completed

### Testing
- [ ] All 10 test cases passed
- [ ] No errors in Odoo log
- [ ] Excel file opens correctly
- [ ] Thai characters render correctly

### Production Deployment
- [ ] Module deployed to production
- [ ] Users notified
- [ ] Training conducted (if needed)
- [ ] Documentation updated

### Post-Deployment
- [ ] Monitor for errors (first 24 hours)
- [ ] User feedback collected
- [ ] Issues documented and resolved

---

**Deployment Date:** _________________

**Deployed By:** _________________

**Tested By:** _________________

**Approved By:** _________________

---

*Checklist Version: 1.0*  
*Module Version: 19.0.2.0.0*  
*Date Created: January 3, 2026*
