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
    
    date_from = fields.Date(
        string='From Date',
        help='Export invoices from this date',
    )
    
    date_to = fields.Date(
        string='To Date',
        help='Export invoices up to this date',
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
        domain = [
            ('move_type', 'in', ('out_invoice', 'out_refund')),
            ('state', '=', 'posted'),
            ('company_id', '=', self.company_id.id),
        ]
        
        if self.invoice_ids:
            # Export selected invoices
            invoices = self.invoice_ids
            if not self.include_exported:
                invoices = invoices.filtered(lambda m: not m.etax_exported)
            if not self.include_finalized:
                invoices = invoices.filtered(lambda m: not m.etax_finalized)
            return invoices
        
        # Export by date range
        if self.date_from:
            domain.append(('invoice_date', '>=', self.date_from))
        if self.date_to:
            domain.append(('invoice_date', '<=', self.date_to))
        
        if not self.include_exported:
            domain.append(('etax_exported', '=', False))
        
        if not self.include_finalized:
            domain.append(('etax_finalized', '=', False))
        
        return self.env['account.move'].search(domain, order='invoice_date, name')
    
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
        """Generate Excel file from invoices"""
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
        
        # Create worksheet
        worksheet = workbook.add_worksheet('e-Tax Invoices')
        
        # Define columns
        columns = [
            ('A', 'Document Type', 15),
            ('B', 'Invoice Number', 20),
            ('C', 'Invoice Date', 15),
            ('D', 'Due Date', 15),
            ('E', 'Customer Name', 35),
            ('F', 'Customer Tax ID', 18),
            ('G', 'Customer Branch', 15),
            ('H', 'Customer Address', 50),
            ('I', 'Seller Name', 35),
            ('J', 'Seller Tax ID', 18),
            ('K', 'Seller Branch', 15),
            ('L', 'Subtotal (Untaxed)', 18),
            ('M', 'Tax Amount', 15),
            ('N', 'Total Amount', 18),
            ('O', 'Currency', 10),
            ('P', 'Reference', 25),
            ('Q', 'Payment Terms', 25),
            ('R', 'Salesperson', 20),
        ]
        
        # Write header row
        for col_idx, (col_letter, col_name, col_width) in enumerate(columns):
            worksheet.write(0, col_idx, col_name, header_format)
            worksheet.set_column(col_idx, col_idx, col_width)
        
        # Freeze header row
        worksheet.freeze_panes(1, 0)
        
        # Write data rows
        row = 1
        for invoice in invoices:
            # Determine document type
            if invoice.move_type == 'out_invoice':
                doc_type = 'Tax Invoice'
            else:
                doc_type = 'Credit Note'
            
            # Get customer info - prefer etax fields, fallback to standard VAT
            partner = invoice.partner_id
            customer_tax_id = partner.etax_effective_tax_id or partner.vat or ''
            customer_branch = partner.etax_branch_id or '00000'
            customer_address = self._format_address(partner)
            
            # Get seller info - prefer etax fields, fallback to standard VAT
            company = invoice.company_id
            seller_tax_id = company.etax_tax_id or company.vat or ''
            seller_branch = company.etax_branch_id or '00000'
            
            # Write row data
            worksheet.write(row, 0, doc_type, text_format)
            worksheet.write(row, 1, invoice.name or '', text_format)
            worksheet.write(row, 2, invoice.invoice_date, date_format)
            worksheet.write(row, 3, invoice.invoice_date_due, date_format)
            worksheet.write(row, 4, partner.name or '', text_format)
            worksheet.write(row, 5, customer_tax_id, text_format)
            worksheet.write(row, 6, customer_branch, text_format)
            worksheet.write(row, 7, customer_address, text_format)
            worksheet.write(row, 8, company.name or '', text_format)
            worksheet.write(row, 9, seller_tax_id, text_format)
            worksheet.write(row, 10, seller_branch, text_format)
            worksheet.write(row, 11, invoice.amount_untaxed, money_format)
            worksheet.write(row, 12, invoice.amount_tax, money_format)
            worksheet.write(row, 13, invoice.amount_total, money_format)
            worksheet.write(row, 14, invoice.currency_id.name or 'THB', text_format)
            worksheet.write(row, 15, invoice.ref or '', text_format)
            worksheet.write(row, 16, invoice.invoice_payment_term_id.name if invoice.invoice_payment_term_id else '', text_format)
            worksheet.write(row, 17, invoice.invoice_user_id.name if invoice.invoice_user_id else '', text_format)
            
            row += 1
        
        # Add line items sheet
        self._add_line_items_sheet(workbook, invoices)
        
        workbook.close()
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'etax_invoices_{timestamp}.xlsx'
        
        return output.getvalue(), filename
    
    def _add_line_items_sheet(self, workbook, invoices):
        """Add a sheet with invoice line items"""
        worksheet = workbook.add_worksheet('Line Items')
        
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
        
        money_format = workbook.add_format({
            'num_format': '#,##0.00',
            'border': 1,
        })
        
        text_format = workbook.add_format({
            'border': 1,
        })
        
        qty_format = workbook.add_format({
            'num_format': '#,##0.00',
            'border': 1,
        })
        
        # Define columns
        columns = [
            ('Invoice Number', 20),
            ('Line #', 8),
            ('Product Code', 20),
            ('Product Name', 40),
            ('Description', 50),
            ('Quantity', 12),
            ('UoM', 10),
            ('Unit Price', 15),
            ('Discount %', 12),
            ('Subtotal', 15),
            ('Tax', 20),
            ('Tax Amount', 12),
        ]
        
        # Write header
        for col_idx, (col_name, col_width) in enumerate(columns):
            worksheet.write(0, col_idx, col_name, header_format)
            worksheet.set_column(col_idx, col_idx, col_width)
        
        worksheet.freeze_panes(1, 0)
        
        # Write line items
        row = 1
        for invoice in invoices:
            line_num = 1
            for line in invoice.invoice_line_ids.filtered(lambda l: l.display_type == 'product'):
                worksheet.write(row, 0, invoice.name or '', text_format)
                worksheet.write(row, 1, line_num, text_format)
                worksheet.write(row, 2, line.product_id.default_code or '', text_format)
                worksheet.write(row, 3, line.product_id.name or '', text_format)
                worksheet.write(row, 4, line.name or '', text_format)
                worksheet.write(row, 5, line.quantity, qty_format)
                worksheet.write(row, 6, line.product_uom_id.name if line.product_uom_id else '', text_format)
                worksheet.write(row, 7, line.price_unit, money_format)
                worksheet.write(row, 8, line.discount, qty_format)
                worksheet.write(row, 9, line.price_subtotal, money_format)
                worksheet.write(row, 10, ', '.join(line.tax_ids.mapped('name')), text_format)
                worksheet.write(row, 11, line.price_total - line.price_subtotal, money_format)
                
                row += 1
                line_num += 1
    
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
