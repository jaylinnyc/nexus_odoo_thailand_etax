# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import base64
import logging
import requests
import uuid
from datetime import datetime

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'
    
    # e-Tax Export Fields
    etax_xml_file = fields.Binary(
        string='e-Tax XML File (Unsigned)',
        readonly=True,
        attachment=True,
    )
    
    etax_signed_xml_file = fields.Binary(
        string='e-Tax XML File (Signed)',
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
        ('exported', 'XML Generated'),
        ('pending_signature', 'Pending Signature'),
        ('signed', 'Signed'),
        ('submitted', 'Submitted to RD'),
        ('confirmed', 'Confirmed by RD'),
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
    
    # Signing Service Integration Fields
    etax_signing_batch_id = fields.Char(
        string='Signing Batch ID',
        readonly=True,
        help='Batch ID from signing service',
    )
    
    etax_rd_confirmation = fields.Char(
        string='RD Confirmation Number',
        readonly=True,
        help='Confirmation number from Thai Revenue Department',
    )
    
    etax_submitted_date = fields.Datetime(
        string='Submitted to RD Date',
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
            move.etax_is_exported = move.etax_status in (
                'exported', 'pending_signature', 'signed', 'submitted', 'confirmed'
            )
    
    def _check_etax_requirements(self):
        """Check if invoice meets e-Tax export requirements"""
        self.ensure_one()
        
        try:
            from ..lib.etax_validator import InvoiceValidator
            
            validator = InvoiceValidator(self)
            validator.validate_all()
            
            if validator.errors:
                raise UserError('\n'.join(validator.errors))
            
            if validator.warnings:
                _logger.warning(
                    f"e-Tax validation warnings for {self.name}: {validator.warnings}"
                )
            
            return True
            
        except ImportError:
            return self._check_etax_requirements_basic()
    
    def _check_etax_requirements_basic(self):
        """Basic requirement check (fallback)"""
        self.ensure_one()
        
        errors = []
        
        if self.state != 'posted':
            errors.append(_('Invoice must be posted before exporting to e-Tax.'))
        
        if self.move_type not in ('out_invoice', 'out_refund'):
            errors.append(_('Only customer invoices and credit notes can be exported.'))
        
        if not self.company_id.etax_tax_id:
            errors.append(_('Company Tax ID is not configured.'))
        
        if not self.company_id.etax_branch_id:
            errors.append(_('Company Branch ID is not configured.'))
        
        if not self.partner_id:
            errors.append(_('Customer is required for e-Tax export.'))
        else:
            tax_id = getattr(self.partner_id, 'etax_effective_tax_id', None) or self.partner_id.vat
            if not tax_id:
                errors.append(_('Customer Tax ID is required.'))
        
        config = self.env['etax.config'].search([
            ('company_id', '=', self.company_id.id),
            ('active', '=', True)
        ], limit=1)
        
        if not config:
            errors.append(_('e-Tax configuration not found.'))
        
        if errors:
            raise UserError('\n'.join(errors))
        
        return True
    
    def action_export_etax_xml(self):
        """Generate e-Tax XML (unsigned)"""
        self.ensure_one()
        
        try:
            self._check_etax_requirements()
            
            # Generate XML
            xml_content = self._generate_etax_xml()
            
            # Generate document ID
            doc_id = str(uuid.uuid4())
            filename = self._get_etax_filename()
            
            self.write({
                'etax_xml_file': base64.b64encode(xml_content.encode('utf-8')),
                'etax_xml_filename': filename,
                'etax_document_id': doc_id,
                'etax_export_date': fields.Datetime.now(),
                'etax_status': 'exported',
                'etax_error_message': False,
            })
            
            # Auto-send to signing service if enabled
            config = self._get_etax_config()
            if config.auto_sign:
                return self.action_send_to_signing_service()
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('e-Tax XML generated. Click "Send to Signing Service" to sign.'),
                    'type': 'success',
                    'sticky': False,
                }
            }
            
        except Exception as e:
            self.write({
                'etax_status': 'error',
                'etax_error_message': str(e),
            })
            raise UserError(_('Error generating XML: %s') % str(e))
    
    def action_send_to_signing_service(self):
        """Send unsigned XML to signing service for digital signature"""
        self.ensure_one()
        
        if not self.etax_xml_file:
            raise UserError(_('No XML file to sign. Please generate XML first.'))
        
        try:
            config = self._get_etax_config()
            
            # Decode XML content
            xml_content = base64.b64decode(self.etax_xml_file).decode('utf-8')
            
            # Prepare request
            headers = {'Content-Type': 'application/json'}
            if config.signing_api_key:
                headers['Authorization'] = f'Bearer {config.signing_api_key}'
            
            payload = {
                'callback_url': config.callback_url,
                'auto_submit_to_rd': config.auto_submit_to_rd,
                'documents': [{
                    'invoice_id': self.name,
                    'document_id': self.etax_document_id,
                    'xml_content': xml_content,
                    'document_type': 'tax_invoice' if self.move_type == 'out_invoice' else 'credit_note',
                    'seller_tax_id': self.company_id.etax_tax_id,
                    'buyer_tax_id': getattr(self.partner_id, 'etax_effective_tax_id', None) or self.partner_id.vat,
                    'total_amount': float(self.amount_total),
                    'currency': self.currency_id.name,
                }]
            }
            
            # Send to signing service
            response = requests.post(
                f'{config.signing_service_url}/api/v1/sign/batch',
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code in (200, 201, 202):
                result = response.json()
                self.write({
                    'etax_signing_batch_id': result.get('batch_id'),
                    'etax_status': 'pending_signature',
                    'etax_error_message': False,
                })
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Sent to Signing Service'),
                        'message': _('Document sent for digital signature. Batch ID: %s') % result.get('batch_id'),
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                error_msg = response.json().get('error', response.text)
                raise UserError(_('Signing service error: %s') % error_msg)
                
        except requests.exceptions.ConnectionError:
            self.write({
                'etax_status': 'error',
                'etax_error_message': _('Could not connect to signing service'),
            })
            raise UserError(_('Could not connect to signing service. '
                             'Please verify the service is running at %s') % config.signing_service_url)
        except Exception as e:
            self.write({
                'etax_status': 'error',
                'etax_error_message': str(e),
            })
            raise UserError(_('Error sending to signing service: %s') % str(e))
    
    def action_check_signing_status(self):
        """Check status of signing request"""
        self.ensure_one()
        
        if not self.etax_signing_batch_id:
            raise UserError(_('No pending signing request.'))
        
        try:
            config = self._get_etax_config()
            
            headers = {}
            if config.signing_api_key:
                headers['Authorization'] = f'Bearer {config.signing_api_key}'
            
            response = requests.get(
                f'{config.signing_service_url}/api/v1/sign/batch/{self.etax_signing_batch_id}',
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Find our document in the results
                for doc in result.get('documents', []):
                    if doc.get('invoice_id') == self.name:
                        doc_status = doc.get('status')
                        
                        if doc_status == 'signed':
                            signed_xml = doc.get('signed_xml')
                            if signed_xml:
                                self.write({
                                    'etax_signed_xml_file': base64.b64encode(signed_xml.encode('utf-8')),
                                    'etax_status': 'signed',
                                    'etax_signature_date': fields.Datetime.now(),
                                    'etax_rd_confirmation': doc.get('rd_confirmation'),
                                    'etax_error_message': False,
                                })
                        elif doc_status == 'submitted':
                            self.write({
                                'etax_status': 'submitted',
                                'etax_submitted_date': fields.Datetime.now(),
                            })
                        elif doc_status == 'confirmed':
                            self.write({
                                'etax_status': 'confirmed',
                                'etax_rd_confirmation': doc.get('rd_confirmation'),
                            })
                        elif doc_status == 'failed':
                            self.write({
                                'etax_status': 'error',
                                'etax_error_message': doc.get('error_message'),
                            })
                        break
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Status Updated'),
                        'message': _('Current status: %s') % self.etax_status,
                        'type': 'info',
                        'sticky': False,
                    }
                }
            else:
                raise UserError(_('Could not check status'))
                
        except requests.exceptions.ConnectionError:
            raise UserError(_('Could not connect to signing service'))
        except Exception as e:
            raise UserError(_('Error checking status: %s') % str(e))
    
    def action_download_etax_xml(self):
        """Download e-Tax XML file (signed if available, otherwise unsigned)"""
        self.ensure_one()
        
        # Prefer signed XML
        if self.etax_signed_xml_file:
            return {
                'type': 'ir.actions.act_url',
                'url': f'/web/content/account.move/{self.id}/etax_signed_xml_file/{self.etax_xml_filename}?download=true',
                'target': 'self',
            }
        elif self.etax_xml_file:
            return {
                'type': 'ir.actions.act_url',
                'url': f'/web/content/account.move/{self.id}/etax_xml_file/{self.etax_xml_filename}?download=true',
                'target': 'self',
            }
        else:
            raise UserError(_('No XML file available.'))
    
    def action_reset_etax(self):
        """Reset e-Tax export status"""
        self.ensure_one()
        
        self.write({
            'etax_xml_file': False,
            'etax_signed_xml_file': False,
            'etax_xml_filename': False,
            'etax_document_id': False,
            'etax_export_date': False,
            'etax_status': 'draft',
            'etax_error_message': False,
            'etax_signature_date': False,
            'etax_signing_batch_id': False,
            'etax_rd_confirmation': False,
            'etax_submitted_date': False,
        })
        
        return True
    
    def _get_etax_config(self):
        """Get active e-Tax configuration for company"""
        config = self.env['etax.config'].search([
            ('company_id', '=', self.company_id.id),
            ('active', '=', True)
        ], limit=1)
        
        if not config:
            raise UserError(_('e-Tax configuration not found.'))
        
        return config
    
    def _get_etax_filename(self):
        """Generate filename for e-Tax XML"""
        self.ensure_one()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        invoice_name = self.name.replace('/', '_')
        return f'ETAX_{invoice_name}_{timestamp}.xml'
    
    def _generate_etax_xml(self):
        """Generate e-Tax XML content using ETDA-compliant builder"""
        self.ensure_one()
        
        try:
            from ..lib.etax_tax_invoice import ETDATaxInvoiceGenerator
            
            generator = ETDATaxInvoiceGenerator(self)
            
            if not generator.validate():
                errors = generator.errors
                raise UserError(_('Validation failed:\n') + '\n'.join(errors))
            
            xml_content = generator.generate()
            
            _logger.info(f'Generated e-Tax XML for invoice {self.name}')
            return xml_content
            
        except ImportError as e:
            _logger.warning(f'lxml not available, using placeholder XML: {e}')
            return self._generate_placeholder_xml()
        except Exception as e:
            _logger.error(f'Error generating e-Tax XML: {e}')
            raise
    
    def _generate_placeholder_xml(self):
        """Generate placeholder XML (fallback when lxml not available)"""
        self.ensure_one()
        
        xml_template = f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- Thailand e-Tax XML - Placeholder (lxml required for ETDA compliance) -->
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
