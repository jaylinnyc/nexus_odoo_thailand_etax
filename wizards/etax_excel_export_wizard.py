# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import base64
import logging
import re
from io import BytesIO
from datetime import datetime

_logger = logging.getLogger(__name__)

try:
    import xlsxwriter
    XLSXWRITER_AVAILABLE = True
except ImportError:
    XLSXWRITER_AVAILABLE = False
    _logger.warning('xlsxwriter library not installed. Excel export will not be available.')


class EtaxExcelExportWizard(models.TransientModel):
    _name = 'etax.excel.export.wizard'
    _description = 'e-Tax Excel Export Wizard'
    
    invoice_ids = fields.Many2many(
        'account.move',
        'etax_export_wizard_invoice_rel',
        'wizard_id',
        'invoice_id',
        string='Invoices to Export',
        domain=[
            ('move_type', 'in', ('out_invoice', 'out_refund')),
            ('state', '=', 'posted'),
        ],
    )
    
    # Store the actually exported invoices for finalization
    exported_invoice_ids = fields.Many2many(
        'account.move',
        'etax_export_wizard_exported_rel',
        'wizard_id',
        'invoice_id',
        string='Exported Invoices',
        readonly=True,
    )
    
    include_exported = fields.Boolean(
        string='Include Previously Exported',
        default=True,
        help='Include invoices that have already been exported. Uncheck to only export new invoices.',
    )
    
    include_finalized = fields.Boolean(
        string='Include Finalized',
        default=False,
        help='Include invoices that have already been finalized',
    )
    
    mark_as_exported = fields.Boolean(
        string='Mark as Exported',
        default=True,
        help='Mark the exported invoices as exported after download',
    )
    
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
    )
    
    # Result fields
    result_file = fields.Binary(
        string='Excel File',
        readonly=True,
        attachment=False,
    )
    
    result_filename = fields.Char(
        string='Filename',
        readonly=True,
    )
    
    export_count = fields.Integer(
        string='Exported Count',
        readonly=True,
    )
    
    export_batch_id = fields.Char(
        string='Batch ID',
        readonly=True,
    )
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Exported'),
        ('finalized', 'Finalized'),
    ], default='draft')
    
    @api.model
    def default_get(self, fields_list):
        """Get default values from context"""
        res = super().default_get(fields_list)
        
        # Get selected invoices from context
        active_ids = self.env.context.get('active_ids', [])
        active_model = self.env.context.get('active_model')
        
        if active_model == 'account.move' and active_ids:
            # Filter to only valid invoice types
            invoices = self.env['account.move'].browse(active_ids).filtered(
                lambda m: m.move_type in ('out_invoice', 'out_refund') and m.state == 'posted'
            )
            res['invoice_ids'] = [(6, 0, invoices.ids)]
        
        return res
    
    def _get_invoices_to_export(self):
        """Get invoices based on wizard selection"""
        if not self.invoice_ids:
            raise UserError(_('Please select invoices to export.'))
        
        # Export selected invoices
        invoices = self.invoice_ids
        if not self.include_exported:
            invoices = invoices.filtered(lambda m: not m.etax_exported)
        if not self.include_finalized:
            invoices = invoices.filtered(lambda m: not m.etax_finalized)
        return invoices
    
    def action_export(self):
        """Export invoices to Excel"""
        self.ensure_one()
        
        if not XLSXWRITER_AVAILABLE:
            raise UserError(_('xlsxwriter library is not installed. Please install it using: pip install xlsxwriter'))
        
        invoices = self._get_invoices_to_export()
        
        if not invoices:
            raise UserError(_('No invoices found to export. Check your selection criteria.'))
        
        # Generate Excel file
        excel_file, filename = self._generate_excel(invoices)
        
        # Generate batch ID
        batch_id = f"ETAX-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        # Mark invoices as exported if requested
        if self.mark_as_exported:
            invoices.action_mark_etax_exported(batch_id=batch_id)
        
        # Update wizard with results
        self.write({
            'result_file': base64.b64encode(excel_file),
            'result_filename': filename,
            'export_count': len(invoices),
            'export_batch_id': batch_id,
            'exported_invoice_ids': [(6, 0, invoices.ids)],
            'state': 'done',
        })
        
        # Return the wizard view to show download button
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'etax.excel.export.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
    
    def action_download(self):
        """Download the generated Excel file"""
        self.ensure_one()
        
        if not self.result_file:
            raise UserError(_('No file to download. Please export first.'))
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/etax.excel.export.wizard/{self.id}/result_file/{self.result_filename}?download=true',
            'target': 'self',
        }
    
    def action_finalize(self):
        """Finalize the exported invoices - locks them from further modification"""
        self.ensure_one()
        
        if not self.exported_invoice_ids:
            raise UserError(_('No invoices to finalize. Please export first.'))
        
        # Filter out already finalized invoices
        to_finalize = self.exported_invoice_ids.filtered(lambda m: not m.etax_finalized)
        
        if not to_finalize:
            raise UserError(_('All exported invoices are already finalized.'))
        
        to_finalize.action_mark_etax_finalized()
        
        self.write({'state': 'finalized'})
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'etax.excel.export.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
    
    def action_close(self):
        """Close the wizard"""
        return {'type': 'ir.actions.act_window_close'}
    
    def _generate_excel(self, invoices):
        """Generate Excel file from invoices in e-Tax format (one row per line item)"""
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        
        # Add formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4472C4',
            'font_color': 'white',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'text_wrap': True,
        })
        
        date_format = workbook.add_format({
            'num_format': 'yyyy-mm-dd',
            'border': 1,
        })
        
        money_format = workbook.add_format({
            'num_format': '#,##0.00',
            'border': 1,
        })
        
        text_format = workbook.add_format({
            'border': 1,
        })
        
        int_format = workbook.add_format({
            'num_format': '0',
            'border': 1,
        })
        
        # Create worksheet
        worksheet = workbook.add_worksheet('e-Tax Invoices')
        
        # Define columns matching the updated e-Tax requirements
        columns = [
            # Document Header
            ('document_type', 15),
            ('document_number', 20),
            ('issue_date', 12),
            ('purpose', 15),
            # Seller Information
            ('seller_name', 30),
            ('seller_tax_id', 15),
            ('seller_branch', 12),
            # Seller Thai Address Components
            ('seller_building_number', 16),
            ('seller_building_name', 20),
            ('seller_floor', 10),
            ('seller_room', 10),
            ('seller_village_name', 20),
            ('seller_moo', 8),
            ('seller_soi', 18),
            ('seller_street', 20),
            # Seller Composite Address
            ('seller_address', 30),
            ('seller_address2', 25),
            # Seller Administrative Divisions
            ('seller_subdistrict', 18),
            ('seller_subdistrict_code', 12),
            ('seller_district', 18),
            ('seller_district_code', 10),
            ('seller_province', 15),
            ('seller_province_code', 10),
            ('seller_postcode', 12),
            ('seller_country_code', 10),
            ('seller_phone', 15),
            ('seller_email', 25),
            # Buyer Information
            ('buyer_name', 30),
            ('buyer_tax_id', 15),
            ('buyer_branch', 12),
            # Buyer Thai Address Components
            ('buyer_building_number', 16),
            ('buyer_building_name', 20),
            ('buyer_floor', 10),
            ('buyer_room', 10),
            ('buyer_village_name', 20),
            ('buyer_moo', 8),
            ('buyer_soi', 18),
            ('buyer_street', 20),
            # Buyer Composite Address
            ('buyer_address', 30),
            ('buyer_address2', 25),
            # Buyer Administrative Divisions
            ('buyer_subdistrict', 18),
            ('buyer_subdistrict_code', 12),
            ('buyer_district', 18),
            ('buyer_district_code', 10),
            ('buyer_province', 15),
            ('buyer_province_code', 10),
            ('buyer_postcode', 12),
            ('buyer_country_code', 10),
            ('buyer_phone', 15),
            ('buyer_email', 25),
            # Line Items
            ('line_id', 8),
            ('item_name', 30),
            ('description', 40),
            ('quantity', 10),
            ('unit', 10),
            ('unit_name', 15),
            ('unit_price', 12),
            ('discount', 10),
            ('amount', 12),
            # Totals
            ('subtotal', 12),
            ('total_discount', 12),
            ('vat_rate', 10),
            ('vat_amount', 12),
            ('grand_total', 12),
            # Reference Documents (for Credit/Debit Notes)
            ('reference_number', 20),
            ('reference_date', 12),
            # Withholding Tax
            ('withholding_tax_rate', 12),
            ('withholding_tax_amount', 15),
            # Payment Terms
            ('payment_terms', 20),
            ('due_date', 12),
        ]
        
        # Write header row
        for col_idx, (col_name, col_width) in enumerate(columns):
            worksheet.write(0, col_idx, col_name, header_format)
            worksheet.set_column(col_idx, col_idx, col_width)
        
        # Freeze header row
        worksheet.freeze_panes(1, 0)
        
        # Track skipped invoices for warning message
        skipped_invoices = []
        
        # Write data rows - one row per line item
        row = 1
        for invoice in invoices:
            # Validate required fields
            if not self._validate_invoice_for_export(invoice):
                skipped_invoices.append((invoice.name, invoice.partner_id.name, 'Missing required fields'))
                continue
            
            # Map document type to Thai RD codes
            doc_type_map = {
                'out_invoice': '388',      # Tax Invoice
                'out_refund': '81',        # Credit Note
                # Note: Debit notes would be '80' if supported
            }
            doc_type = doc_type_map.get(invoice.move_type, '388')
            
            # Determine purpose
            if invoice.move_type == 'out_refund':
                purpose = 'Credit Note'
            elif invoice.move_type == 'out_invoice':
                purpose = 'Sale'
            else:
                purpose = ''
            
            # Get seller (company) info
            company = invoice.company_id
            seller_tax_id = self._clean_tax_id(company.vat or '')
            seller_branch = self._clean_branch_id(company.etax_branch_id or '00000')
            
            # Seller Thai Address Component Fields
            seller_building_number = company.etax_building_number or ''
            seller_building_name = company.etax_building_name or ''
            seller_floor = company.etax_floor_number or ''
            seller_room = company.etax_room_number or ''
            seller_village_name = company.etax_village_name or ''
            seller_moo = company.etax_moo or ''
            seller_soi = company.etax_soi or ''
            seller_street = company.etax_street_name or ''
            
            # Build seller address - use composite line or build from components
            seller_address = company.etax_address_line_one or company.street or ''
            seller_address2 = company.etax_address_line_two or ''
            
            # If no composite address, build from components for backward compatibility
            if not seller_address and company.etax_building_number:
                parts = [company.etax_building_number]
                if company.etax_village_name:
                    parts.append(company.etax_village_name)
                if company.etax_moo:
                    parts.append(f"Moo {company.etax_moo}")
                if company.etax_soi:
                    parts.append(f"Soi {company.etax_soi}")
                if company.etax_street_name:
                    parts.append(company.etax_street_name)
                seller_address = ' '.join(parts)
            
            # Build address line 2 from building details if not set
            if not seller_address2:
                if company.etax_building_name:
                    seller_address2 = company.etax_building_name
                    if company.etax_floor_number:
                        seller_address2 += f", Floor {company.etax_floor_number}"
                    if company.etax_room_number:
                        seller_address2 += f", Room {company.etax_room_number}"
                elif company.street2:
                    seller_address2 = company.street2
            
            # Seller Administrative Division Fields
            seller_subdistrict = company.etax_sub_district or ''
            seller_subdistrict_code = company.etax_sub_district_code or ''
            seller_district = company.etax_district or company.city or ''
            seller_district_code = company.etax_district_code or ''
            seller_province = company.etax_province or (company.state_id.name if company.state_id else '')
            seller_province_code = company.etax_province_code or ''
            seller_postcode = company.etax_postal_code or company.zip or ''
            seller_country_code = company.etax_country_code or 'TH'
            seller_phone = company.phone or ''
            seller_email = company.email or ''
            
            # Get buyer (partner) info
            partner = invoice.partner_id
            buyer_tax_id = self._clean_tax_id(partner.etax_effective_tax_id or partner.vat or '')
            buyer_branch = self._clean_branch_id(partner.etax_branch_id or '00000')
            
            # Buyer Thai Address Component Fields
            buyer_building_number = partner.etax_building_number or ''
            buyer_building_name = partner.etax_building_name or ''
            buyer_floor = partner.etax_floor_number or ''
            buyer_room = partner.etax_room_number or ''
            buyer_village_name = partner.etax_village_name or ''
            buyer_moo = partner.etax_moo or ''
            buyer_soi = partner.etax_soi or ''
            buyer_street = partner.etax_street_name or ''
            
            # Build buyer address - use composite line or build from components
            buyer_address = partner.etax_address_line_one or partner.street or ''
            buyer_address2 = partner.etax_address_line_two or ''
            
            # If no composite address, build from components for backward compatibility
            if not buyer_address and partner.etax_building_number:
                parts = [partner.etax_building_number]
                if partner.etax_village_name:
                    parts.append(partner.etax_village_name)
                if partner.etax_moo:
                    parts.append(f"Moo {partner.etax_moo}")
                if partner.etax_soi:
                    parts.append(f"Soi {partner.etax_soi}")
                if partner.etax_street_name:
                    parts.append(partner.etax_street_name)
                buyer_address = ' '.join(parts)
            
            # Build address line 2 from building details if not set
            if not buyer_address2:
                if partner.etax_building_name:
                    buyer_address2 = partner.etax_building_name
                    if partner.etax_floor_number:
                        buyer_address2 += f", Floor {partner.etax_floor_number}"
                    if partner.etax_room_number:
                        buyer_address2 += f", Room {partner.etax_room_number}"
                elif partner.street2:
                    buyer_address2 = partner.street2
            
            # Buyer Administrative Division Fields
            buyer_subdistrict = partner.etax_sub_district or ''
            buyer_subdistrict_code = partner.etax_sub_district_code or ''
            buyer_district = partner.etax_district or partner.city or ''
            buyer_district_code = partner.etax_district_code or ''
            buyer_province = partner.etax_province or (partner.state_id.name if partner.state_id else '')
            buyer_province_code = partner.etax_province_code or ''
            buyer_postcode = partner.etax_postal_code or partner.zip or ''
            buyer_country_code = partner.etax_country_code or 'TH'
            buyer_phone = partner.phone or ''
            buyer_email = partner.email or ''
            
            # Get invoice totals
            subtotal = invoice.amount_untaxed
            
            # Calculate total discount
            total_discount = 0
            for line in invoice.invoice_line_ids.filtered(lambda l: l.display_type == 'product'):
                if line.discount:
                    total_discount += (line.discount / 100) * line.quantity * line.price_unit
            
            vat_amount = invoice.amount_tax
            grand_total = invoice.amount_total
            
            # Determine VAT rate (typically 7% in Thailand)
            vat_rate = 7  # Default Thai VAT
            for line in invoice.invoice_line_ids.filtered(lambda l: l.display_type == 'product'):
                if line.tax_ids:
                    for tax in line.tax_ids:
                        if tax.amount > 0:
                            vat_rate = tax.amount
                            break
                    break
            
            # Reference document fields (for Credit/Debit Notes)
            reference_number = ''
            reference_date = ''
            if invoice.move_type == 'out_refund' and invoice.reversed_entry_id:
                reference_number = invoice.reversed_entry_id.name or ''
                reference_date = invoice.reversed_entry_id.invoice_date or ''
            
            # Withholding tax - calculate from tax lines
            wht_rate = 0
            wht_amount = 0
            for line in invoice.invoice_line_ids.filtered(lambda l: l.display_type == 'product'):
                for tax in line.tax_ids:
                    # Withholding taxes typically have negative amounts
                    if tax.amount < 0:
                        wht_rate = abs(tax.amount)
                        # Calculate WHT amount for this line
                        line_subtotal = line.quantity * line.price_unit * (1 - (line.discount or 0) / 100)
                        wht_amount += abs(line_subtotal * tax.amount / 100)
            
            # Payment terms
            payment_terms = invoice.invoice_payment_term_id.name if invoice.invoice_payment_term_id else ''
            due_date = invoice.invoice_date_due or ''
            
            # Write one row per line item
            line_num = 1
            product_lines = invoice.invoice_line_ids.filtered(lambda l: l.display_type == 'product')
            
            if not product_lines:
                skipped_invoices.append((invoice.name, invoice.partner_id.name, 'No product lines'))
                continue
            
            for line in product_lines:
                # Line-specific values
                item_name = line.product_id.name if line.product_id else (line.name or '')
                description = line.name or item_name
                quantity = line.quantity
                
                # Get UoM name - e-Tax service will handle code mapping
                if line.product_uom_id:
                    unit = line.product_uom_id.name
                    unit_name = line.product_uom_id.name
                else:
                    unit = 'Unit'
                    unit_name = 'Unit'
                
                unit_price = line.price_unit
                
                # Calculate line discount
                line_discount = 0
                if line.discount:
                    line_discount = (line.discount / 100) * line.quantity * line.price_unit
                
                line_amount = line.price_subtotal
                
                # Write all columns
                col = 0
                # Document header
                worksheet.write(row, col, doc_type, text_format); col += 1
                worksheet.write(row, col, invoice.name or '', text_format); col += 1
                worksheet.write(row, col, invoice.invoice_date, date_format); col += 1
                worksheet.write(row, col, purpose, text_format); col += 1
                # Seller info
                worksheet.write(row, col, company.name or '', text_format); col += 1
                worksheet.write(row, col, seller_tax_id, text_format); col += 1
                worksheet.write(row, col, seller_branch, text_format); col += 1
                # Seller Thai address components
                worksheet.write(row, col, seller_building_number, text_format); col += 1
                worksheet.write(row, col, seller_building_name, text_format); col += 1
                worksheet.write(row, col, seller_floor, text_format); col += 1
                worksheet.write(row, col, seller_room, text_format); col += 1
                worksheet.write(row, col, seller_village_name, text_format); col += 1
                worksheet.write(row, col, seller_moo, text_format); col += 1
                worksheet.write(row, col, seller_soi, text_format); col += 1
                worksheet.write(row, col, seller_street, text_format); col += 1
                # Seller composite address
                worksheet.write(row, col, seller_address, text_format); col += 1
                worksheet.write(row, col, seller_address2, text_format); col += 1
                # Seller administrative divisions
                worksheet.write(row, col, seller_subdistrict, text_format); col += 1
                worksheet.write(row, col, seller_subdistrict_code, text_format); col += 1
                worksheet.write(row, col, seller_district, text_format); col += 1
                worksheet.write(row, col, seller_district_code, text_format); col += 1
                worksheet.write(row, col, seller_province, text_format); col += 1
                worksheet.write(row, col, seller_province_code, text_format); col += 1
                worksheet.write(row, col, seller_postcode, text_format); col += 1
                worksheet.write(row, col, seller_country_code, text_format); col += 1
                worksheet.write(row, col, seller_phone, text_format); col += 1
                worksheet.write(row, col, seller_email, text_format); col += 1
                # Buyer info
                worksheet.write(row, col, partner.name or '', text_format); col += 1
                worksheet.write(row, col, buyer_tax_id, text_format); col += 1
                worksheet.write(row, col, buyer_branch, text_format); col += 1
                # Buyer Thai address components
                worksheet.write(row, col, buyer_building_number, text_format); col += 1
                worksheet.write(row, col, buyer_building_name, text_format); col += 1
                worksheet.write(row, col, buyer_floor, text_format); col += 1
                worksheet.write(row, col, buyer_room, text_format); col += 1
                worksheet.write(row, col, buyer_village_name, text_format); col += 1
                worksheet.write(row, col, buyer_moo, text_format); col += 1
                worksheet.write(row, col, buyer_soi, text_format); col += 1
                worksheet.write(row, col, buyer_street, text_format); col += 1
                # Buyer composite address
                worksheet.write(row, col, buyer_address, text_format); col += 1
                worksheet.write(row, col, buyer_address2, text_format); col += 1
                # Buyer administrative divisions
                worksheet.write(row, col, buyer_subdistrict, text_format); col += 1
                worksheet.write(row, col, buyer_subdistrict_code, text_format); col += 1
                worksheet.write(row, col, buyer_district, text_format); col += 1
                worksheet.write(row, col, buyer_district_code, text_format); col += 1
                worksheet.write(row, col, buyer_province, text_format); col += 1
                worksheet.write(row, col, buyer_province_code, text_format); col += 1
                worksheet.write(row, col, buyer_postcode, text_format); col += 1
                worksheet.write(row, col, buyer_country_code, text_format); col += 1
                worksheet.write(row, col, buyer_phone, text_format); col += 1
                worksheet.write(row, col, buyer_email, text_format); col += 1
                # Line item details
                worksheet.write(row, col, line_num, int_format); col += 1
                worksheet.write(row, col, item_name, text_format); col += 1
                worksheet.write(row, col, description, text_format); col += 1
                worksheet.write(row, col, quantity, money_format); col += 1
                worksheet.write(row, col, unit, text_format); col += 1
                worksheet.write(row, col, unit_name, text_format); col += 1
                worksheet.write(row, col, unit_price, money_format); col += 1
                worksheet.write(row, col, line_discount, money_format); col += 1
                worksheet.write(row, col, line_amount, money_format); col += 1
                worksheet.write(row, col, subtotal, money_format); col += 1
                worksheet.write(row, col, total_discount, money_format); col += 1
                worksheet.write(row, col, vat_rate, int_format); col += 1
                worksheet.write(row, col, vat_amount, money_format); col += 1
                worksheet.write(row, col, grand_total, money_format); col += 1
                worksheet.write(row, col, reference_number, text_format); col += 1
                if reference_date:
                    worksheet.write(row, col, reference_date, date_format)
                else:
                    worksheet.write(row, col, '', text_format)
                col += 1
                worksheet.write(row, col, wht_rate, money_format); col += 1
                worksheet.write(row, col, wht_amount, money_format); col += 1
                worksheet.write(row, col, payment_terms, text_format); col += 1
                if due_date:
                    worksheet.write(row, col, due_date, date_format)
                else:
                    worksheet.write(row, col, '', text_format)
                
                row += 1
                line_num += 1
        
        workbook.close()
        
        # Log skipped invoices
        if skipped_invoices:
            warning_msg = _('Warning: Skipped %d invoice(s):\n') % len(skipped_invoices)
            for inv_name, partner_name, reason in skipped_invoices[:10]:
                warning_msg += f'  - {inv_name} ({partner_name}): {reason}\n'
            if len(skipped_invoices) > 10:
                warning_msg += f'  ... and {len(skipped_invoices) - 10} more'
            _logger.warning(warning_msg)
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'etax_export_{timestamp}.xlsx'
        
        return output.getvalue(), filename
    
    def _clean_tax_id(self, tax_id):
        """Clean tax ID to 13 digits without hyphens"""
        if not tax_id:
            return ''
        # Remove TH prefix if present
        if tax_id.upper().startswith('TH'):
            tax_id = tax_id[2:]
        # Remove all non-digit characters
        cleaned = re.sub(r'[^0-9]', '', tax_id)
        return cleaned
    
    def _clean_branch_id(self, branch_id):
        """Clean branch ID to 5 digits"""
        if not branch_id:
            return '00000'
        # Remove all non-digit characters
        cleaned = re.sub(r'[^0-9]', '', branch_id)
        # Pad with zeros if needed
        return cleaned.zfill(5)[:5]
    
    def _validate_invoice_for_export(self, invoice):
        """Validate invoice has required fields for e-Tax export"""
        # Basic validation
        if not invoice.name:
            return False
        if not invoice.invoice_date:
            return False
        
        # Seller validation
        company = invoice.company_id
        seller_tax_id = self._clean_tax_id(company.vat or '')
        if not seller_tax_id or len(seller_tax_id) != 13:
            _logger.warning(f'Invoice {invoice.name}: Invalid seller tax ID')
            return False
        
        # Seller postal code validation (critical for e-Tax)
        if not company.etax_postal_code and not company.zip:
            _logger.warning(f'Invoice {invoice.name}: Missing seller postal code (required for e-Tax)')
            # Don't fail validation, but log warning
        
        # Buyer validation
        partner = invoice.partner_id
        buyer_tax_id = self._clean_tax_id(partner.etax_effective_tax_id or partner.vat or '')
        if not buyer_tax_id or len(buyer_tax_id) != 13:
            _logger.warning(f'Invoice {invoice.name}: Invalid buyer tax ID for {partner.name}')
            return False
        
        # Buyer postal code validation (critical for e-Tax)
        if not partner.etax_postal_code and not partner.zip:
            _logger.warning(f'Invoice {invoice.name}: Missing buyer postal code for {partner.name} (required for e-Tax)')
            # Don't fail validation, but log warning
        
        # Line items validation
        product_lines = invoice.invoice_line_ids.filtered(lambda l: l.display_type == 'product')
        if not product_lines:
            return False
        
        # Reference document validation for Credit/Debit Notes
        if invoice.move_type in ('out_refund',):
            if not invoice.reversed_entry_id:
                _logger.warning(
                    f'Invoice {invoice.name}: Credit note missing reference to original invoice'
                )
                # Still export but log warning
        
        return True

    
    def _format_address(self, partner):
        """Format partner address as a single string, including Thai address fields"""
        parts = []
        
        # Use composite address line if available (preferred)
        if partner.etax_address_line_one:
            parts.append(partner.etax_address_line_one)
        else:
            # Build from individual components
            if partner.etax_building_number:
                parts.append(partner.etax_building_number)
            if partner.etax_village_name:
                parts.append(partner.etax_village_name)
            if partner.etax_moo:
                parts.append(f"Moo {partner.etax_moo}")
            if partner.etax_soi:
                parts.append(f"Soi {partner.etax_soi}")
            if partner.etax_street_name:
                parts.append(partner.etax_street_name)
            # Fallback to standard street if no Thai fields
            elif partner.street:
                parts.append(partner.street)
        
        # Building details
        if partner.etax_building_name:
            parts.append(partner.etax_building_name)
        if partner.etax_floor_number:
            parts.append(f"Floor {partner.etax_floor_number}")
        if partner.etax_room_number:
            parts.append(f"Room {partner.etax_room_number}")
        
        # Additional address line
        if partner.etax_address_line_two:
            parts.append(partner.etax_address_line_two)
        elif partner.street2:
            parts.append(partner.street2)
        
        # Administrative divisions
        if partner.etax_sub_district:
            parts.append(partner.etax_sub_district)
        if partner.etax_district:
            parts.append(partner.etax_district)
        elif partner.city:
            parts.append(partner.city)
            
        if partner.etax_province:
            parts.append(partner.etax_province)
        elif partner.state_id:
            parts.append(partner.state_id.name)
        
        # Postal code (prefer etax field)
        postal = partner.etax_postal_code or partner.zip
        if postal:
            parts.append(postal)
            
        # Country
        country_code = partner.etax_country_code or (partner.country_id.code if partner.country_id else None)
        if country_code:
            parts.append(country_code)
        elif partner.country_id:
            parts.append(partner.country_id.name)
        
        return ', '.join(parts)
