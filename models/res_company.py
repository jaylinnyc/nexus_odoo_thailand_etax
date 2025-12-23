# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import re


class ResCompany(models.Model):
    _inherit = 'res.company'
    
    # Thai Tax Registration
    etax_tax_id = fields.Char(
        string='Tax ID',
        size=13,
        help='Thai Tax Identification Number (13 digits)',
    )
    
    etax_branch_id = fields.Char(
        string='Branch ID',
        size=5,
        default='00000',
        help='Branch identification code (5 digits, 00000 for head office)',
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
    
    @api.constrains('etax_tax_id')
    def _check_etax_tax_id(self):
        for company in self:
            if company.etax_tax_id:
                # Remove any non-digit characters for validation
                tax_id_digits = re.sub(r'[^0-9]', '', company.etax_tax_id)
                if len(tax_id_digits) != 13:
                    raise ValidationError(_('Tax ID must be exactly 13 digits.'))
    
    @api.constrains('etax_branch_id')
    def _check_etax_branch_id(self):
        for company in self:
            if company.etax_branch_id:
                branch_digits = re.sub(r'[^0-9]', '', company.etax_branch_id)
                if len(branch_digits) != 5:
                    raise ValidationError(_('Branch ID must be exactly 5 digits.'))
