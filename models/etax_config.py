# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


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
    
    # Certificate Settings
    certificate_type = fields.Selection([
        ('pkcs12', 'PKCS#12 (File)'),
        ('pkcs11', 'PKCS#11 (Smart Card/Token)'),
    ], string='Certificate Type', default='pkcs12', required=True)
    
    certificate_path = fields.Char(
        string='Certificate Path',
        help='Full path to PKCS#12 certificate file (.p12 or .pfx)',
    )
    
    certificate_password = fields.Char(
        string='Certificate Password',
        help='Password to unlock the certificate',
    )
    
    pkcs11_library_path = fields.Char(
        string='PKCS#11 Library Path',
        help='Path to PKCS#11 library (for smart card/token)',
    )
    
    pkcs11_slot_id = fields.Integer(
        string='PKCS#11 Slot ID',
        default=0,
        help='Slot ID for PKCS#11 device',
    )
    
    # Output Settings
    output_directory = fields.Char(
        string='Output Directory',
        default='/tmp/etax_exports',
        help='Directory to save exported XML files',
    )
    
    auto_sign = fields.Boolean(
        string='Auto Sign Documents',
        default=True,
        help='Automatically sign XML documents with digital signature',
    )
    
    validate_xml = fields.Boolean(
        string='Validate XML',
        default=True,
        help='Validate XML against ETDA schemas before export',
    )
    
    # Algorithm Settings
    digest_algorithm = fields.Selection([
        ('sha256', 'SHA-256'),
        ('sha512', 'SHA-512'),
    ], string='Digest Algorithm', default='sha512', required=True)
    
    signature_algorithm = fields.Selection([
        ('rsa_sha256', 'RSA-SHA256'),
        ('rsa_sha512', 'RSA-SHA512'),
    ], string='Signature Algorithm', default='rsa_sha512', required=True)
    
    # Active flag
    active = fields.Boolean(default=True)
    
    @api.constrains('certificate_type', 'certificate_path', 'pkcs11_library_path')
    def _check_certificate_configuration(self):
        for config in self:
            if config.certificate_type == 'pkcs12' and not config.certificate_path:
                raise UserError(_('Certificate path is required for PKCS#12 type.'))
            if config.certificate_type == 'pkcs11' and not config.pkcs11_library_path:
                raise UserError(_('PKCS#11 library path is required for PKCS#11 type.'))
    
    def action_test_certificate(self):
        """Test certificate configuration"""
        self.ensure_one()
        # TODO: Implement certificate testing
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Certificate Test'),
                'message': _('Certificate configuration test - to be implemented'),
                'type': 'info',
                'sticky': False,
            }
        }
