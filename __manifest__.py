# -*- coding: utf-8 -*-
{
    'name': "Thailand e-Tax Invoice Export",
    'summary': """
        Export customer invoices and credit notes for Thailand e-Tax processing
    """,
    'description': """
        Thailand e-Tax Invoice Export Module
        =====================================
        
        This module provides a simple interface to export customer invoices 
        and credit notes to Excel format for Thailand e-Tax processing.
        
        Features:
        ---------
        * View all customer invoices and credit notes
        * Filter by date, status, and customer
        * Export selected invoices to Excel format
        * Track e-Tax export status
        
        The exported Excel file can be loaded into your separate system 
        to validate, convert to XML, and sign with digital certificates.
        
        Menu Location:
        --------------
        Accounting > Reports > Tax Reports > e-Tax Invoices
    """,
    'author': "Nexus",
    'website': "https://nexus.co.th",
    'category': 'Accounting/Localizations',
    'version': '19.0.2.0.0',
    'depends': [
        'base',
        'account',
        'uom',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/etax_data.xml',
        'data/etax_uom_mapping.xml',
        'views/res_company_views.xml',
        'views/res_partner_views.xml',
        'views/account_move_views.xml',
        'views/uom_uom_views.xml',
        'views/etax_excel_export_wizard_views.xml',
        'views/etax_invoice_report_views.xml',
        'views/menu_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
    'external_dependencies': {
        'python': ['xlsxwriter'],
    },
}
