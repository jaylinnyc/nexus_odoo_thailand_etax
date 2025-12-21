# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
import requests

_logger = logging.getLogger(__name__)


class EtaxConfig(models.Model):
    _name = 'etax.config'
    _description = 'e-Tax Configuration'
    _rec_name = 'company_id'

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
    )
    
    # ========================================
    # Signing Service Settings (NEW)
    # ========================================
    signing_service_url = fields.Char(
        string='Signing Service URL',
        default='http://localhost:8443',
        help='URL of the on-premise signing service (e.g., http://localhost:8443)',
        required=True,
    )
    
    signing_api_key = fields.Char(
        string='API Key',
        help='API key for authenticating with the signing service',
    )
    
    auto_submit_to_rd = fields.Boolean(
        string='Auto Submit to Revenue Dept',
        default=False,
        help='Automatically submit signed documents to Thai Revenue Department',
    )
    
    callback_url = fields.Char(
        string='Callback URL',
        help='URL for signing service to send status updates (auto-generated)',
        compute='_compute_callback_url',
    )
    
    # Output Settings
    output_directory = fields.Char(
        string='Output Directory',
        default='/tmp/etax_exports',
        help='Directory to save exported XML files locally',
    )
    
    auto_sign = fields.Boolean(
        string='Auto Send to Signing Service',
        default=True,
        help='Automatically send XML to signing service after generation',
    )
    
    validate_xml = fields.Boolean(
        string='Validate XML',
        default=True,
        help='Validate XML locally before sending to signing service',
    )
    
    # Active flag
    active = fields.Boolean(default=True)
    
    @api.depends('company_id')
    def _compute_callback_url(self):
        """Compute callback URL based on Odoo's base URL"""
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for config in self:
            config.callback_url = f'{base_url}/etax/callback'
    
    @api.constrains('signing_service_url')
    def _check_signing_service_url(self):
        for config in self:
            if config.signing_service_url:
                if not config.signing_service_url.startswith(('http://', 'https://')):
                    raise UserError(_('Signing service URL must start with http:// or https://'))
    
    def action_test_connection(self):
        """Test connection to signing service"""
        self.ensure_one()
        
        try:
            headers = {}
            if self.signing_api_key:
                headers['Authorization'] = f'Bearer {self.signing_api_key}'
            
            response = requests.get(
                f'{self.signing_service_url}/api/v1/health',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Connection Successful'),
                        'message': _('Signing service is online. Status: %s') % data.get('status', 'OK'),
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Connection Failed'),
                        'message': _('Signing service returned status %s') % response.status_code,
                        'type': 'warning',
                        'sticky': True,
                    }
                }
                
        except requests.exceptions.ConnectionError:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Connection Error'),
                    'message': _('Could not connect to signing service at %s. '
                                 'Please verify the service is running.') % self.signing_service_url,
                    'type': 'danger',
                    'sticky': True,
                }
            }
        except Exception as e:
            _logger.error(f'Error testing signing service connection: {e}')
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': str(e),
                    'type': 'danger',
                    'sticky': True,
                }
            }
    
    def action_test_certificate(self):
        """Test certificate on signing service"""
        self.ensure_one()
        
        try:
            headers = {}
            if self.signing_api_key:
                headers['Authorization'] = f'Bearer {self.signing_api_key}'
            
            response = requests.get(
                f'{self.signing_service_url}/api/v1/certificates',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                certs = response.json()
                if certs:
                    cert = certs[0]  # Get first certificate
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': _('Certificate Found'),
                            'message': _('Subject: %s\nValid Until: %s') % (
                                cert.get('subject_cn', 'Unknown'),
                                cert.get('valid_until', 'Unknown')
                            ),
                            'type': 'success',
                            'sticky': True,
                        }
                    }
                else:
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': _('No Certificate'),
                            'message': _('No certificate found on signing service. '
                                        'Please insert USB token and configure the service.'),
                            'type': 'warning',
                            'sticky': True,
                        }
                    }
            else:
                raise UserError(_('Could not retrieve certificate information'))
                
        except requests.exceptions.ConnectionError:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Connection Error'),
                    'message': _('Could not connect to signing service'),
                    'type': 'danger',
                    'sticky': True,
                }
            }
        except Exception as e:
            _logger.error(f'Error testing certificate: {e}')
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': str(e),
                    'type': 'danger',
                    'sticky': True,
                }
            }
