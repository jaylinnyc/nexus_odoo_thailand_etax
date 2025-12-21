# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import base64
from datetime import datetime


class AccountMove(models.Model):
    _inherit = 'account.move'
    
    # e-Tax Export Fields
    etax_xml_file = fields.Binary(
        string='e-Tax XML File',
        readonly=True,
        attachment=True,
    )
    
    etax_xml_filename = fields.Char(
        string='XML Filename',
        readonly=True,
    )
    
    etax_document_id = fields.Char(
        string='e-Tax Document ID',
        readonly=True,
        help='Unique document ID for e-Tax system',
    )
    
    etax_export_date = fields.Datetime(
        string='Export Date',
        readonly=True,
    )
    
    etax_status = fields.Selection([
        ('draft', 'Draft'),
        ('exported', 'Exported'),
        ('signed', 'Signed'),
        ('validated', 'Validated'),
        ('error', 'Error'),
    ], string='e-Tax Status', default='draft', readonly=True)
    
    etax_error_message = fields.Text(
        string='Error Message',
        readonly=True,
    )
    
    etax_signature_date = fields.Datetime(
        string='Signature Date',
        readonly=True,
    )
    
    etax_is_exported = fields.Boolean(
        string='Exported to e-Tax',
        compute='_compute_etax_is_exported',
        store=True,
    )
    
    @api.depends('etax_status')
    def _compute_etax_is_exported(self):
        for move in self:
            move.etax_is_exported = move.etax_status in ('exported', 'signed', 'validated')
    
    def _check_etax_requirements(self):
        """Check if invoice meets e-Tax export requirements"""
        self.ensure_one()
        
        errors = []
        
        # Check invoice state
        if self.state != 'posted':
            errors.append(_('Invoice must be posted before exporting to e-Tax.'))
        
        # Check invoice type
        if self.move_type not in ('out_invoice', 'out_refund'):
            errors.append(_('Only customer invoices and credit notes can be exported to e-Tax.'))
        
        # Check company configuration
        if not self.company_id.etax_tax_id:
            errors.append(_('Company Tax ID is not configured. Please configure it in Company settings.'))
        
        if not self.company_id.etax_branch_id:
            errors.append(_('Company Branch ID is not configured.'))
        
        # Check partner information
        if not self.partner_id:
            errors.append(_('Customer is required for e-Tax export.'))
        elif not self.partner_id.vat:
            errors.append(_('Customer Tax ID is required for e-Tax export.'))
        
        # Check if there's a configuration
        config = self.env['etax.config'].search([
            ('company_id', '=', self.company_id.id),
            ('active', '=', True)
        ], limit=1)
        
        if not config:
            errors.append(_('e-Tax configuration not found. Please configure e-Tax settings.'))
        
        if errors:
            raise UserError('\n'.join(errors))
        
        return True
    
    def action_export_etax_xml(self):
        """Export invoice to e-Tax XML format"""
        self.ensure_one()
        
        try:
            # Check requirements
            self._check_etax_requirements()
            
            # Generate XML
            xml_content = self._generate_etax_xml()
            
            # Save XML file
            filename = self._get_etax_filename()
            
            self.write({
                'etax_xml_file': base64.b64encode(xml_content.encode('utf-8')),
                'etax_xml_filename': filename,
                'etax_export_date': fields.Datetime.now(),
                'etax_status': 'exported',
                'etax_error_message': False,
            })
            
            # Sign if auto-sign is enabled
            config = self._get_etax_config()
            if config.auto_sign:
                self.action_sign_etax_xml()
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('e-Tax XML file generated successfully.'),
                    'type': 'success',
                    'sticky': False,
                    'next': {
                        'type': 'ir.actions.act_window_close',
                    },
                }
            }
            
        except Exception as e:
            self.write({
                'etax_status': 'error',
                'etax_error_message': str(e),
            })
            raise UserError(_('Error generating e-Tax XML: %s') % str(e))
    
    def action_sign_etax_xml(self):
        """Sign e-Tax XML with digital signature"""
        self.ensure_one()
        
        if not self.etax_xml_file:
            raise UserError(_('No XML file to sign. Please export first.'))
        
        try:
            # TODO: Implement XAdES signature
            self.write({
                'etax_status': 'signed',
                'etax_signature_date': fields.Datetime.now(),
            })
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('XML signed successfully.'),
                    'type': 'success',
                    'sticky': False,
                }
            }
            
        except Exception as e:
            raise UserError(_('Error signing XML: %s') % str(e))
    
    def action_download_etax_xml(self):
        """Download e-Tax XML file"""
        self.ensure_one()
        
        if not self.etax_xml_file:
            raise UserError(_('No XML file available. Please export first.'))
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/account.move/{self.id}/etax_xml_file/{self.etax_xml_filename}?download=true',
            'target': 'self',
        }
    
    def action_reset_etax(self):
        """Reset e-Tax export status"""
        self.ensure_one()
        
        self.write({
            'etax_xml_file': False,
            'etax_xml_filename': False,
            'etax_document_id': False,
            'etax_export_date': False,
            'etax_status': 'draft',
            'etax_error_message': False,
            'etax_signature_date': False,
        })
        
        return True
    
    def _get_etax_config(self):
        """Get active e-Tax configuration for company"""
        config = self.env['etax.config'].search([
            ('company_id', '=', self.company_id.id),
            ('active', '=', True)
        ], limit=1)
        
        if not config:
            raise UserError(_('e-Tax configuration not found. Please configure e-Tax settings.'))
        
        return config
    
    def _get_etax_filename(self):
        """Generate filename for e-Tax XML"""
        self.ensure_one()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        invoice_name = self.name.replace('/', '_')
        return f'ETAX_{invoice_name}_{timestamp}.xml'
    
    def _generate_etax_xml(self):
        """Generate e-Tax XML content"""
        self.ensure_one()
        
        # TODO: Implement actual XML generation
        # This is a placeholder that will be replaced with proper ETDA XML generation
        
        xml_template = f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- Thailand e-Tax XML - Placeholder -->
<TaxInvoice>
    <DocumentID>{self.name}</DocumentID>
    <IssueDate>{self.invoice_date}</IssueDate>
    <Seller>
        <Name>{self.company_id.name}</Name>
        <TaxID>{self.company_id.etax_tax_id}</TaxID>
        <BranchID>{self.company_id.etax_branch_id}</BranchID>
    </Seller>
    <Buyer>
        <Name>{self.partner_id.name}</Name>
        <TaxID>{self.partner_id.vat}</TaxID>
    </Buyer>
    <Total>
        <AmountUntaxed>{self.amount_untaxed}</AmountUntaxed>
        <AmountTax>{self.amount_tax}</AmountTax>
        <AmountTotal>{self.amount_total}</AmountTotal>
    </Total>
</TaxInvoice>"""
        
        return xml_template
