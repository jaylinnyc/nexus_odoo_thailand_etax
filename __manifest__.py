# -*- coding: utf-8 -*-
{
    'name': "Nexus Odoo Thailand e-Tax Export",
    'summary': """
        Export invoices and receipts in ETDA XML format for Thailand Revenue Department
    """,
    'description': """
        Nexus Odoo Thailand e-Tax Export Module
        ========================================
        
        This module enables electronic tax invoice and receipt generation compliant with:
        - Thai Revenue Department requirements
        - ETDA (Electronic Transactions Development Agency) XML standards
        
        Features:
        ---------
        * Export tax invoices in ETDA XML format
        * Export receipts in ETDA XML format
        * Validate XML files against ETDA schema
        * Support for Thai tax requirements and formats
        * Integration with Odoo's accounting module
    """,
    'author': "Nexus",
    'website': "https://www.yourcompany.com",
    'category': 'Accounting/Localizations',
    'version': '19.0.1.0.0',
    'depends': [
        'base',
        'account',
        'l10n_th',  # Thai localization
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/etax_config_views.xml',
        'views/res_company_views.xml',
        'views/account_move_views.xml',
        'views/etax_export_wizard_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
