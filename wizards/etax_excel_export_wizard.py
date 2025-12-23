# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import base64
import logging
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
        default=False,
        help='Include invoices that have already been exported',
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
        
        # Define columns matching the e-Tax template exactly
        columns = [
            ('document_type', 15),
            ('document_number', 20),
            ('issue_date', 12),
            ('purpose', 10),
            ('seller_name', 30),
            ('seller_tax_id', 15),
            ('seller_branch', 12),
            ('seller_address', 30),
            ('seller_address2', 25),
            ('seller_subdistrict', 18),
            ('seller_district', 18),
            ('seller_province', 15),
            ('seller_postcode', 12),
            ('seller_phone', 15),
            ('seller_email', 25),
            ('buyer_name', 30),
            ('buyer_tax_id', 15),
            ('buyer_branch', 12),
            ('buyer_address', 30),
            ('buyer_address2', 25),
            ('buyer_subdistrict', 18),
            ('buyer_district', 18),
            ('buyer_province', 15),
            ('buyer_postcode', 12),
            ('buyer_phone', 15),
            ('buyer_email', 25),
            ('line_id', 8),
            ('item_name', 30),
            ('description', 40),
            ('quantity', 10),
            ('unit', 8),
            ('unit_name', 12),
            ('unit_price', 12),
            ('discount', 10),
            ('amount', 12),
            ('subtotal', 12),
            ('total_discount', 12),
            ('vat_rate', 10),
            ('vat_amount', 12),
            ('grand_total', 12),
        ]
        
        # Write header row
        for col_idx, (col_name, col_width) in enumerate(columns):
            worksheet.write(0, col_idx, col_name, header_format)
            worksheet.set_column(col_idx, col_idx, col_width)
        
        # Freeze header row
        worksheet.freeze_panes(1, 0)
        
        # Write data rows - one row per line item
        row = 1
        for invoice in invoices:
            # Determine document type
            if invoice.move_type == 'out_invoice':
                doc_type = 'TaxInvoice'
            else:
                doc_type = 'CreditNote'
            
            # Get seller (company) info
            company = invoice.company_id
            seller_tax_id = company.etax_tax_id or company.vat or ''
            seller_branch = company.etax_branch_id or '00000'
            
            # Build seller address parts
            seller_address = company.street or ''
            seller_address2 = ''
            if company.etax_building_name:
                seller_address2 = company.etax_building_name
                if company.etax_floor_number:
                    seller_address2 += f", Floor {company.etax_floor_number}"
            if company.street2 and not seller_address2:
                seller_address2 = company.street2
            
            seller_subdistrict = company.etax_sub_district or ''
            seller_district = company.etax_district or company.city or ''
            seller_province = company.etax_province or (company.state_id.name if company.state_id else '')
            seller_postcode = company.zip or ''
            seller_phone = company.phone or ''
            seller_email = company.email or ''
            
            # Get buyer (partner) info
            partner = invoice.partner_id
            buyer_tax_id = partner.etax_effective_tax_id or partner.vat or ''
            buyer_branch = partner.etax_branch_id or '00000'
            
            # Build buyer address parts
            buyer_address = partner.street or ''
            buyer_address2 = ''
            if partner.etax_building_name:
                buyer_address2 = partner.etax_building_name
                if partner.etax_floor_number:
                    buyer_address2 += f", Floor {partner.etax_floor_number}"
            if partner.street2 and not buyer_address2:
                buyer_address2 = partner.street2
            
            buyer_subdistrict = partner.etax_sub_district or ''
            buyer_district = partner.etax_district or partner.city or ''
            buyer_province = partner.etax_province or (partner.state_id.name if partner.state_id else '')
            buyer_postcode = partner.zip or ''
            buyer_phone = partner.phone or ''
            buyer_email = partner.email or ''
            
            # Get invoice totals
            subtotal = invoice.amount_untaxed
            total_discount = sum(line.discount * line.quantity * line.price_unit / 100 
                                 for line in invoice.invoice_line_ids.filtered(lambda l: l.display_type == 'product'))
            vat_amount = invoice.amount_tax
            grand_total = invoice.amount_total
            
            # Determine VAT rate (assume first tax line, typically 7% in Thailand)
            vat_rate = 7  # Default Thai VAT
            for line in invoice.invoice_line_ids.filtered(lambda l: l.display_type == 'product'):
                if line.tax_ids:
                    for tax in line.tax_ids:
                        if tax.amount > 0:
                            vat_rate = tax.amount
                            break
                    break
            
            # Write one row per line item
            line_num = 1
            product_lines = invoice.invoice_line_ids.filtered(lambda l: l.display_type == 'product')
            
            for line in product_lines:
                # Line-specific values
                item_name = line.product_id.name or line.name or ''
                description = line.name or ''
                quantity = line.quantity
                unit = line.product_uom_id.name[:2].upper() if line.product_uom_id else 'EA'
                unit_name = line.product_uom_id.name if line.product_uom_id else 'Each'
                unit_price = line.price_unit
                line_discount = line.discount * line.quantity * line.price_unit / 100 if line.discount else 0
                line_amount = line.price_subtotal
                
                # Write all columns
                col = 0
                worksheet.write(row, col, doc_type, text_format); col += 1
                worksheet.write(row, col, invoice.name or '', text_format); col += 1
                worksheet.write(row, col, invoice.invoice_date, date_format); col += 1
                worksheet.write(row, col, 'Sale', text_format); col += 1
                worksheet.write(row, col, company.name or '', text_format); col += 1
                worksheet.write(row, col, seller_tax_id, text_format); col += 1
                worksheet.write(row, col, seller_branch, text_format); col += 1
                worksheet.write(row, col, seller_address, text_format); col += 1
                worksheet.write(row, col, seller_address2, text_format); col += 1
                worksheet.write(row, col, seller_subdistrict, text_format); col += 1
                worksheet.write(row, col, seller_district, text_format); col += 1
                worksheet.write(row, col, seller_province, text_format); col += 1
                worksheet.write(row, col, seller_postcode, text_format); col += 1
                worksheet.write(row, col, seller_phone, text_format); col += 1
                worksheet.write(row, col, seller_email, text_format); col += 1
                worksheet.write(row, col, partner.name or '', text_format); col += 1
                worksheet.write(row, col, buyer_tax_id, text_format); col += 1
                worksheet.write(row, col, buyer_branch, text_format); col += 1
                worksheet.write(row, col, buyer_address, text_format); col += 1
                worksheet.write(row, col, buyer_address2, text_format); col += 1
                worksheet.write(row, col, buyer_subdistrict, text_format); col += 1
                worksheet.write(row, col, buyer_district, text_format); col += 1
                worksheet.write(row, col, buyer_province, text_format); col += 1
                worksheet.write(row, col, buyer_postcode, text_format); col += 1
                worksheet.write(row, col, buyer_phone, text_format); col += 1
                worksheet.write(row, col, buyer_email, text_format); col += 1
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
                worksheet.write(row, col, grand_total, money_format)
                
                row += 1
                line_num += 1
        
        workbook.close()
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'etax_invoices_{timestamp}.xlsx'
        
        return output.getvalue(), filename
    
    def _format_address(self, partner):
        """Format partner address as a single string, including Thai address fields"""
        parts = []
        
        # Thai-specific address fields first
        if partner.etax_building_name:
            parts.append(partner.etax_building_name)
        if partner.etax_floor_number:
            parts.append(f"Floor {partner.etax_floor_number}")
        if partner.etax_room_number:
            parts.append(f"Room {partner.etax_room_number}")
        
        # Standard address fields
        if partner.street:
            parts.append(partner.street)
        if partner.street2:
            parts.append(partner.street2)
        
        # Thai-specific location fields
        if partner.etax_moo:
            parts.append(f"Moo {partner.etax_moo}")
        if partner.etax_soi:
            parts.append(f"Soi {partner.etax_soi}")
        if partner.etax_sub_district:
            parts.append(partner.etax_sub_district)
        if partner.etax_district:
            parts.append(partner.etax_district)
        if partner.etax_province:
            parts.append(partner.etax_province)
        
        # Fallback to standard city/state if Thai fields not set
        if not partner.etax_sub_district and not partner.etax_district:
            if partner.city:
                parts.append(partner.city)
            if partner.state_id:
                parts.append(partner.state_id.name)
        
        if partner.zip:
            parts.append(partner.zip)
        if partner.country_id:
            parts.append(partner.country_id.name)
        
        return ', '.join(parts)
