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
    
    # Thai Address Details (TISI1099-2548)
    etax_building_number = fields.Char(
        string='Building Number',
    )
    
    etax_building_name = fields.Char(
        string='Building Name',
    )
    
    etax_floor_number = fields.Char(
        string='Floor Number',
    )
    
    etax_room_number = fields.Char(
        string='Room Number',
    )
    
    etax_village_name = fields.Char(
        string='Village Name',
    )
    
    etax_house_number = fields.Char(
        string='House Number',
    )
    
    etax_moo = fields.Char(
        string='Moo (หมู่)',
        help='Moo number (village group)',
    )
    
    etax_soi = fields.Char(
        string='Soi (ซอย)',
        help='Soi (lane/alley)',
    )
    
    etax_street = fields.Char(
        string='Street (ถนน)',
        help='Street name',
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
    
    etax_province_code = fields.Char(
        string='Province Code',
        help='Province code according to TISI1099-2548',
    )
    
    etax_postal_code = fields.Char(
        string='Postal Code',
        size=5,
    )
    
    etax_country_code = fields.Char(
        string='Country Code',
        default='TH',
        help='ISO 3166-1 alpha-2 country code',
    )
    
    # Contact Information
    etax_telephone = fields.Char(
        string='Telephone',
    )
    
    etax_email = fields.Char(
        string='Email',
    )
    
    etax_website = fields.Char(
        string='Website',
    )
    
    @api.constrains('etax_tax_id')
    def _check_etax_tax_id(self):
        """Validate Thai Tax ID (13 digits)"""
        for company in self:
            if company.etax_tax_id:
                # Remove any non-digit characters
                tax_id = re.sub(r'\D', '', company.etax_tax_id)
                
                if len(tax_id) != 13:
                    raise ValidationError(_('Thai Tax ID must be exactly 13 digits.'))
                
                # Validate using Thai Tax ID algorithm (mod 11)
                if not self._validate_thai_tax_id(tax_id):
                    raise ValidationError(_('Invalid Thai Tax ID. Please check the number.'))
    
    @api.constrains('etax_branch_id')
    def _check_etax_branch_id(self):
        """Validate Branch ID (5 digits)"""
        for company in self:
            if company.etax_branch_id:
                branch_id = re.sub(r'\D', '', company.etax_branch_id)
                if len(branch_id) != 5:
                    raise ValidationError(_('Branch ID must be exactly 5 digits. Use 00000 for head office.'))
    
    @api.constrains('etax_postal_code')
    def _check_etax_postal_code(self):
        """Validate Thai postal code (5 digits)"""
        for company in self:
            if company.etax_postal_code:
                postal_code = re.sub(r'\D', '', company.etax_postal_code)
                if len(postal_code) != 5:
                    raise ValidationError(_('Postal code must be exactly 5 digits.'))
    
    def _validate_thai_tax_id(self, tax_id):
        """
        Validate Thai Tax ID using mod 11 algorithm
        Formula: 13 - ((sum of (digit * weight)) % 11)
        Weights: 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2
        """
        if len(tax_id) != 13:
            return False
        
        try:
            # Calculate weighted sum for first 12 digits
            weights = [13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2]
            total = sum(int(tax_id[i]) * weights[i] for i in range(12))
            
            # Calculate check digit
            check_digit = (11 - (total % 11)) % 10
            
            # Compare with the 13th digit
            return int(tax_id[12]) == check_digit
        except (ValueError, IndexError):
            return False
    
    def get_etax_full_address(self):
        """Get formatted Thai address for e-Tax"""
        self.ensure_one()
        address_parts = []
        
        # Building information
        if self.etax_building_name:
            address_parts.append(self.etax_building_name)
        if self.etax_building_number:
            address_parts.append(f"เลขที่อาคาร {self.etax_building_number}")
        if self.etax_floor_number:
            address_parts.append(f"ชั้น {self.etax_floor_number}")
        if self.etax_room_number:
            address_parts.append(f"ห้อง {self.etax_room_number}")
        
        # House and village information
        if self.etax_house_number:
            address_parts.append(f"เลขที่ {self.etax_house_number}")
        if self.etax_village_name:
            address_parts.append(self.etax_village_name)
        if self.etax_moo:
            address_parts.append(f"หมู่ {self.etax_moo}")
        if self.etax_soi:
            address_parts.append(f"ซอย {self.etax_soi}")
        if self.etax_street:
            address_parts.append(f"ถนน {self.etax_street}")
        
        # Administrative divisions
        if self.etax_sub_district:
            address_parts.append(f"ตำบล/แขวง {self.etax_sub_district}")
        if self.etax_district:
            address_parts.append(f"อำเภอ/เขต {self.etax_district}")
        if self.etax_province:
            address_parts.append(f"จังหวัด {self.etax_province}")
        if self.etax_postal_code:
            address_parts.append(self.etax_postal_code)
        
        return ' '.join(address_parts)
