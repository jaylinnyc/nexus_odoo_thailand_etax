# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class UomUom(models.Model):
    _inherit = 'uom.uom'
    
    etax_code = fields.Char(
        string='e-Tax UN/CEFACT Code',
        size=10,
        help='UN/CEFACT unit code for Thailand e-Tax (e.g., EA, C62, KGM, MTR)',
    )
    
    etax_name_th = fields.Char(
        string='Thai Unit Name',
        help='Thai language unit name (e.g., ชิ้น, หน่วย, กิโลกรัม)',
    )
    
    @api.model
    def _get_default_etax_mapping(self):
        """Get default e-Tax code mapping based on UoM name"""
        mappings = {
            'unit': ('C62', 'หน่วย'),
            'units': ('C62', 'หน่วย'),
            'piece': ('EA', 'ชิ้น'),
            'pieces': ('EA', 'ชิ้น'),
            'each': ('EA', 'ชิ้น'),
            'box': ('BX', 'กล่อง'),
            'boxes': ('BX', 'กล่อง'),
            'kg': ('KGM', 'กิโลกรัม'),
            'kilogram': ('KGM', 'กิโลกรัม'),
            'kilograms': ('KGM', 'กิโลกรัม'),
            'g': ('GRM', 'กรัม'),
            'gram': ('GRM', 'กรัม'),
            'grams': ('GRM', 'กรัม'),
            'meter': ('MTR', 'เมตร'),
            'meters': ('MTR', 'เมตร'),
            'metre': ('MTR', 'เมตร'),
            'metres': ('MTR', 'เมตร'),
            'm': ('MTR', 'เมตร'),
            'cm': ('CMT', 'เซนติเมตร'),
            'centimeter': ('CMT', 'เซนติเมตร'),
            'centimeters': ('CMT', 'เซนติเมตร'),
            'hour': ('HUR', 'ชั่วโมง'),
            'hours': ('HUR', 'ชั่วโมง'),
            'day': ('DAY', 'วัน'),
            'days': ('DAY', 'วัน'),
            'set': ('SET', 'ชุด'),
            'sets': ('SET', 'ชุด'),
            'liter': ('LTR', 'ลิตร'),
            'liters': ('LTR', 'ลิตร'),
            'litre': ('LTR', 'ลิตร'),
            'litres': ('LTR', 'ลิตร'),
            'l': ('LTR', 'ลิตร'),
            'dozen': ('DZN', 'โหล'),
            'ton': ('TNE', 'ตัน'),
            'tons': ('TNE', 'ตัน'),
            'tonne': ('TNE', 'ตัน'),
            'tonnes': ('TNE', 'ตัน'),
            'pair': ('PR', 'คู่'),
            'pairs': ('PR', 'คู่'),
            'pack': ('PK', 'แพ็ค'),
            'packs': ('PK', 'แพ็ค'),
            'package': ('PK', 'แพ็ค'),
            'packages': ('PK', 'แพ็ค'),
            'bottle': ('BT', 'ขวด'),
            'bottles': ('BT', 'ขวด'),
            'can': ('CA', 'กระป๋อง'),
            'cans': ('CA', 'กระป๋อง'),
            'bag': ('BG', 'ถุง'),
            'bags': ('BG', 'ถุง'),
            'roll': ('RO', 'ม้วน'),
            'rolls': ('RO', 'ม้วน'),
            'sheet': ('ST', 'แผ่น'),
            'sheets': ('ST', 'แผ่น'),
            'carton': ('CT', 'กล่องใหญ่'),
            'cartons': ('CT', 'กล่องใหญ่'),
        }
        return mappings
    
    def get_etax_code(self):
        """Get e-Tax UN/CEFACT code for this UoM"""
        self.ensure_one()
        
        # Use explicitly set code if available
        if self.etax_code:
            return self.etax_code
        
        # Try to map from name
        name_lower = (self.name or '').lower().strip()
        mappings = self._get_default_etax_mapping()
        
        if name_lower in mappings:
            return mappings[name_lower][0]
        
        # Default fallback
        return 'C62'  # Default to "unit"
    
    def get_etax_name_th(self):
        """Get Thai name for this UoM"""
        self.ensure_one()
        
        # Use explicitly set Thai name if available
        if self.etax_name_th:
            return self.etax_name_th
        
        # Try to map from name
        name_lower = (self.name or '').lower().strip()
        mappings = self._get_default_etax_mapping()
        
        if name_lower in mappings:
            return mappings[name_lower][1]
        
        # Default fallback - return English name
        return self.name or 'หน่วย'
