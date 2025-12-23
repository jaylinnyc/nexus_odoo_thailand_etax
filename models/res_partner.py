# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import re


class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    # Thai Tax Registration for e-Tax
    etax_tax_id = fields.Char(
        string='Thai Tax ID',
        size=13,
        help='Thai Tax Identification Number (13 digits)',
    )
    
    etax_branch_id = fields.Char(
        string='Branch ID',
        size=5,
        default='00000',
        help='Branch identification code (5 digits, 00000 for head office)',
    )
    
    etax_use_vat = fields.Boolean(
        string='Use VAT field for e-Tax',
        default=True,
        help='If checked, use the standard VAT field for e-Tax. Otherwise use Thai Tax ID field.',
    )
    
    # Thai Address Details
    etax_building_name = fields.Char(
        string='Building Name',
    )
    
    etax_floor_number = fields.Char(
        string='Floor Number',
    )
    
    etax_room_number = fields.Char(
        string='Room Number',
    )
    
    etax_moo = fields.Char(
        string='Moo (หมู่)',
        help='Moo number (village group)',
    )
    
    etax_soi = fields.Char(
        string='Soi (ซอย)',
        help='Soi (lane/alley)',
    )
    
    etax_sub_district = fields.Char(
        string='Sub-district (ตำบล/แขวง)',
        help='Sub-district (Tambon/Khwaeng)',
    )
    
    etax_district = fields.Char(
        string='District (อำเภอ/เขต)',
        help='District (Amphoe/Khet)',
    )
    
    etax_province = fields.Char(
        string='Province (จังหวัด)',
        help='Province name',
    )
    
    # Computed field for effective Tax ID
    etax_effective_tax_id = fields.Char(
        string='Effective Tax ID',
        compute='_compute_etax_effective_tax_id',
        help='Tax ID used for e-Tax (either VAT or Thai Tax ID field)',
    )
    
    @api.depends('vat', 'etax_tax_id', 'etax_use_vat')
    def _compute_etax_effective_tax_id(self):
        for partner in self:
            if partner.etax_use_vat:
                # Extract numeric part from VAT (remove country prefix if present)
                vat = partner.vat or ''
                # Remove TH prefix if present
                if vat.upper().startswith('TH'):
                    vat = vat[2:]
                partner.etax_effective_tax_id = re.sub(r'[^0-9]', '', vat)
            else:
                partner.etax_effective_tax_id = partner.etax_tax_id or ''
    
    @api.constrains('etax_tax_id')
    def _check_etax_tax_id(self):
        for partner in self:
            if partner.etax_tax_id:
                tax_id_digits = re.sub(r'[^0-9]', '', partner.etax_tax_id)
                if len(tax_id_digits) != 13:
                    raise ValidationError(_('Tax ID must be exactly 13 digits.'))
    
    @api.constrains('etax_branch_id')
    def _check_etax_branch_id(self):
        for partner in self:
            if partner.etax_branch_id:
                branch_digits = re.sub(r'[^0-9]', '', partner.etax_branch_id)
                if len(branch_digits) != 5:
                    raise ValidationError(_('Branch ID must be exactly 5 digits.'))
