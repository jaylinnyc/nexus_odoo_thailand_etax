# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import re


class ResCompany(models.Model):
    _inherit = 'res.company'
    
    # Thai Tax Registration
    # Note: Use standard 'vat' field for Tax ID
    
    etax_branch_id = fields.Char(
        string='Branch ID',
        size=5,
        default='00000',
        help='Branch identification code (5 digits, 00000 for head office)',
    )
    
    # Thai Address Details
    etax_building_number = fields.Char(
        string='Building Number (เลขที่)',
        size=16,
        help='Building/house number (max 16 characters)',
    )
    
    etax_building_name = fields.Char(
        string='Building Name (ชื่ออาคาร)',
        size=70,
        help='Building name (max 70 characters)',
    )
    
    etax_floor_number = fields.Char(
        string='Floor Number (ชั้น)',
        help='Floor number',
    )
    
    etax_room_number = fields.Char(
        string='Room Number (ห้องเลขที่)',
        help='Room number',
    )
    
    etax_village_name = fields.Char(
        string='Village Name (หมู่บ้าน)',
        size=70,
        help='Village name (max 70 characters)',
    )
    
    etax_moo = fields.Char(
        string='Moo (หมู่ที่)',
        help='Village group number',
    )
    
    etax_soi = fields.Char(
        string='Soi (ซอย)',
        size=70,
        help='Soi/lane/alley (max 70 characters)',
    )
    
    etax_street_name = fields.Char(
        string='Street Name (ถนน)',
        size=70,
        help='Street/road name (max 70 characters)',
    )
    
    etax_sub_district = fields.Char(
        string='Sub-district (ตำบล/แขวง)',
        help='Sub-district (Tambon/Khwaeng)',
    )
    
    etax_sub_district_code = fields.Char(
        string='Sub-district Code',
        size=6,
        help='TISI 1099 standard code for sub-district',
    )
    
    etax_district = fields.Char(
        string='District (อำเภอ/เขต)',
        help='District (Amphoe/Khet)',
    )
    
    etax_district_code = fields.Char(
        string='District Code',
        size=4,
        help='TISI 1099 standard code for district',
    )
    
    etax_province = fields.Char(
        string='Province (จังหวัด)',
        help='Province name',
    )
    
    etax_province_code = fields.Char(
        string='Province Code',
        size=2,
        help='Thai province code',
    )
    
    etax_postal_code = fields.Char(
        string='Postal Code (รหัสไปรษณีย์)',
        size=5,
        required=False,
        help='5-digit postal code (required for e-Tax)',
    )
    
    etax_country_code = fields.Char(
        string='Country Code',
        size=2,
        default='TH',
        help='ISO 3166-1 alpha-2 country code',
    )
    
    etax_address_line_one = fields.Char(
        string='Address Line 1',
        size=256,
        compute='_compute_etax_address_lines',
        store=True,
        help='Composite address line (auto-generated)',
    )
    
    etax_address_line_two = fields.Char(
        string='Address Line 2',
        size=256,
        help='Additional address details',
    )
    
    @api.depends('etax_building_number', 'etax_village_name', 'etax_moo', 
                 'etax_soi', 'etax_street_name')
    def _compute_etax_address_lines(self):
        """Compute composite address line from Thai address components"""
        for company in self:
            parts = []
            
            # Building number (เลขที่)
            if company.etax_building_number:
                parts.append(company.etax_building_number)
            
            # Village name (หมู่บ้าน)
            if company.etax_village_name:
                parts.append(company.etax_village_name)
            
            # Moo (หมู่ที่)
            if company.etax_moo:
                parts.append(f"หมู่ {company.etax_moo}")
            
            # Soi (ซอย)
            if company.etax_soi:
                parts.append(f"ซอย{company.etax_soi}")
            
            # Street (ถนน)
            if company.etax_street_name:
                parts.append(f"ถนน{company.etax_street_name}")
            
            company.etax_address_line_one = ' '.join(parts) if parts else ''
    
    @api.constrains('vat')
    def _check_vat_thai_format(self):
        """Validate Thai Tax ID format (13 digits)"""
        for company in self:
            if company.vat and company.country_id.code == 'TH':
                # Remove any non-digit characters for validation
                tax_id_digits = re.sub(r'[^0-9]', '', company.vat)
                # Remove country prefix if present
                if tax_id_digits.startswith('66'):
                    tax_id_digits = tax_id_digits[2:]
                if len(tax_id_digits) != 13:
                    raise ValidationError(_('Thai Tax ID must be exactly 13 digits.'))
    
    @api.constrains('etax_postal_code')
    def _check_etax_postal_code(self):
        """Validate Thai postal code format (5 digits)"""
        for company in self:
            if company.etax_postal_code:
                if not re.match(r'^\d{5}$', company.etax_postal_code):
                    raise ValidationError(_('Postal code must be exactly 5 digits.'))
    
    @api.constrains('etax_country_code')
    def _check_etax_country_code(self):
        """Validate ISO 3166-1 alpha-2 country code"""
        for company in self:
            if company.etax_country_code:
                if not re.match(r'^[A-Z]{2}$', company.etax_country_code.upper()):
                    raise ValidationError(_('Country code must be 2 uppercase letters (ISO 3166-1 alpha-2).'))
    
    @api.constrains('etax_building_number')
    def _check_etax_building_number(self):
        """Validate building number max length"""
        for company in self:
            if company.etax_building_number and len(company.etax_building_number) > 16:
                raise ValidationError(_('Building number cannot exceed 16 characters.'))
    
    @api.constrains('etax_branch_id')
    def _check_etax_branch_id(self):
        for company in self:
            if company.etax_branch_id:
                branch_digits = re.sub(r'[^0-9]', '', company.etax_branch_id)
                if len(branch_digits) != 5:
                    raise ValidationError(_('Branch ID must be exactly 5 digits.'))
