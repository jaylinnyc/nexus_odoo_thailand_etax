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
        string='Use VAT field',
        default=True,
        help='If checked, use the standard VAT field for e-Tax. Otherwise use Thai Tax ID field.',
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
    
    etax_province_code = fields.Char(
        string='Province Code',
        help='Province code according to TISI1099-2548',
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
                # Clean the tax ID
                tax_id = re.sub(r'[^0-9]', '', partner.etax_tax_id)
                if len(tax_id) != 13:
                    raise ValidationError(
                        _('Thai Tax ID must be exactly 13 digits. Got %d digits.') % len(tax_id)
                    )
    
    @api.constrains('etax_branch_id')
    def _check_etax_branch_id(self):
        for partner in self:
            if partner.etax_branch_id:
                # Clean the branch ID
                branch_id = re.sub(r'[^0-9]', '', partner.etax_branch_id)
                if len(branch_id) != 5:
                    raise ValidationError(
                        _('Branch ID must be exactly 5 digits. Got %d digits.') % len(branch_id)
                    )
    
    def get_etax_address_dict(self):
        """
        Get partner address formatted for e-Tax XML builder
        
        Returns:
            dict: Address fields for ETDAXMLBuilder.create_trade_party()
        """
        self.ensure_one()
        
        # Build address from either e-Tax specific fields or standard fields
        address = {
            'postal_code': self.zip or '',
            'country_code': self.country_id.code if self.country_id else 'TH',
        }
        
        # Use e-Tax specific fields if available
        if self.etax_building_number:
            address['building_number'] = self.etax_building_number
        
        if self.etax_soi:
            address['soi'] = self.etax_soi
        
        if self.etax_moo:
            address['moo'] = self.etax_moo
        
        if self.etax_floor_number:
            address['floor'] = self.etax_floor_number
        
        # Use street from standard field or e-Tax field
        if self.street:
            address['street'] = self.street
        
        # Administrative divisions - prefer e-Tax fields, fallback to parsing city
        if self.etax_sub_district:
            address['sub_district'] = self.etax_sub_district
        
        if self.etax_district:
            address['district'] = self.etax_district
        
        if self.etax_province:
            address['province'] = self.etax_province
        elif self.state_id:
            address['province'] = self.state_id.name
        
        if self.etax_province_code:
            address['province_code'] = self.etax_province_code
        elif self.state_id and self.state_id.code:
            address['province_code'] = self.state_id.code
        
        return address
    
    def get_etax_contact_dict(self):
        """
        Get partner contact info formatted for e-Tax XML builder
        
        Returns:
            dict: Contact fields for ETDAXMLBuilder.create_trade_party()
        """
        self.ensure_one()
        
        contact = {}
        
        if self.name:
            contact['person_name'] = self.name
        
        if self.email:
            contact['email'] = self.email
        
        if self.phone:
            contact['telephone'] = self.phone
        elif self.mobile:
            contact['telephone'] = self.mobile
        
        return contact if contact else None
