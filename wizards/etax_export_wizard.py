# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import base64
import zipfile
from io import BytesIO


class EtaxExportWizard(models.TransientModel):
    _name = 'etax.export.wizard'
    _description = 'e-Tax Export Wizard'
    
    invoice_ids = fields.Many2many(
        'account.move',
        string='Invoices',
        domain=[('move_type', 'in', ('out_invoice', 'out_refund')), ('state', '=', 'posted')],
    )
    
    date_from = fields.Date(
        string='From Date',
        help='Export invoices from this date',
    )
    
    date_to = fields.Date(
        string='To Date',
        help='Export invoices up to this date',
    )
    
    partner_ids = fields.Many2many(
        'res.partner',
        string='Customers',
        help='Filter by specific customers',
    )
    
    include_signature = fields.Boolean(
        string='Include Digital Signature',
        default=True,
        help='Sign XML files with digital signature',
    )
    
    export_format = fields.Selection([
        ('xml', 'Individual XML Files'),
        ('zip', 'ZIP Archive'),
    ], string='Export Format', default='zip', required=True)
    
    export_type = fields.Selection([
        ('selected', 'Selected Invoices'),
        ('date_range', 'Date Range'),
    ], string='Export Type', default='selected', required=True)
    
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
    )
    
    # Results
    result_file = fields.Binary(
        string='Result File',
        readonly=True,
        attachment=False,
    )
    
    result_filename = fields.Char(
        string='Filename',
        readonly=True,
    )
    
    export_log = fields.Text(
        string='Export Log',
        readonly=True,
    )
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
    ], default='draft')
    
    @api.onchange('export_type')
    def _onchange_export_type(self):
        """Clear fields based on export type"""
        if self.export_type == 'selected':
            self.date_from = False
            self.date_to = False
        else:
            self.invoice_ids = [(5, 0, 0)]
    
    def action_export(self):
        """Execute the export"""
        self.ensure_one()
        
        # Get invoices to export
        invoices = self._get_invoices_to_export()
        
        if not invoices:
            raise UserError(_('No invoices found to export.'))
        
        # Export invoices
        export_log = []
        success_count = 0
        error_count = 0
        xml_files = {}
        
        for invoice in invoices:
            try:
                # Check if already exported
                if invoice.etax_status in ('exported', 'signed', 'validated'):
                    export_log.append(f"⚠️ {invoice.name}: Already exported (status: {invoice.etax_status})")
                    continue
                
                # Export invoice
                invoice.action_export_etax_xml()
                
                # Sign if requested
                if self.include_signature:
                    invoice.action_sign_etax_xml()
                
                # Get XML content
                xml_content = base64.b64decode(invoice.etax_xml_file)
                xml_files[invoice.etax_xml_filename] = xml_content
                
                export_log.append(f"✓ {invoice.name}: Exported successfully")
                success_count += 1
                
            except Exception as e:
                export_log.append(f"✗ {invoice.name}: Error - {str(e)}")
                error_count += 1
        
        # Generate result file
        if self.export_format == 'zip':
            result_file, filename = self._create_zip_archive(xml_files)
        else:
            # For single XML, just return the first file
            if xml_files:
                filename = list(xml_files.keys())[0]
                result_file = base64.b64encode(list(xml_files.values())[0])
            else:
                result_file = False
                filename = False
        
        # Update wizard with results
        log_text = '\n'.join(export_log)
        log_text += f"\n\n=== Summary ===\n"
        log_text += f"Total: {len(invoices)}\n"
        log_text += f"Success: {success_count}\n"
        log_text += f"Errors: {error_count}\n"
        
        self.write({
            'result_file': result_file,
            'result_filename': filename,
            'export_log': log_text,
            'state': 'done',
        })
        
        # Return wizard form view with results
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'etax.export.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': self.env.context,
        }
    
    def action_download_result(self):
        """Download the exported file"""
        self.ensure_one()
        
        if not self.result_file:
            raise UserError(_('No file to download.'))
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/etax.export.wizard/{self.id}/result_file/{self.result_filename}?download=true',
            'target': 'self',
        }
    
    def _get_invoices_to_export(self):
        """Get invoices based on wizard configuration"""
        self.ensure_one()
        
        if self.export_type == 'selected':
            return self.invoice_ids
        
        # Date range export
        domain = [
            ('move_type', 'in', ('out_invoice', 'out_refund')),
            ('state', '=', 'posted'),
            ('company_id', '=', self.company_id.id),
        ]
        
        if self.date_from:
            domain.append(('invoice_date', '>=', self.date_from))
        
        if self.date_to:
            domain.append(('invoice_date', '<=', self.date_to))
        
        if self.partner_ids:
            domain.append(('partner_id', 'in', self.partner_ids.ids))
        
        return self.env['account.move'].search(domain, order='invoice_date, name')
    
    def _create_zip_archive(self, xml_files):
        """Create a ZIP archive from XML files"""
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for filename, content in xml_files.items():
                zip_file.writestr(filename, content)
        
        zip_content = zip_buffer.getvalue()
        filename = f'etax_export_{fields.Date.today()}.zip'
        
        return base64.b64encode(zip_content), filename
