# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'
    
    # e-Tax Export Tracking Fields
    etax_export_date = fields.Datetime(
        string='Last Export Date',
        readonly=True,
        help='Date when this invoice was last exported to Excel for e-Tax processing',
    )
    
    etax_exported = fields.Boolean(
        string='Exported',
        default=False,
        readonly=True,
        help='Whether this invoice has been exported for e-Tax processing',
    )
    
    etax_export_batch = fields.Char(
        string='Export Batch',
        readonly=True,
        help='Batch identifier for the e-Tax export',
    )
    
    # e-Tax Finalization Fields
    etax_finalized = fields.Boolean(
        string='e-Tax Finalized',
        default=False,
        readonly=True,
        tracking=True,
        help='When finalized, this invoice has been submitted for e-Tax processing and cannot be modified',
    )
    
    etax_finalized_date = fields.Datetime(
        string='Finalized Date',
        readonly=True,
        help='Date when this invoice was finalized for e-Tax',
    )
    
    etax_finalized_by = fields.Many2one(
        'res.users',
        string='Finalized By',
        readonly=True,
        help='User who finalized this invoice for e-Tax',
    )
    
    def action_mark_etax_exported(self, batch_id=None):
        """Mark invoices as exported for e-Tax (does not lock)"""
        self.write({
            'etax_exported': True,
            'etax_export_date': fields.Datetime.now(),
            'etax_export_batch': batch_id,
        })
    
    def action_mark_etax_finalized(self):
        """Mark invoices as finalized - locks them from further editing"""
        for move in self:
            if move.etax_finalized:
                continue
            if move.state != 'posted':
                raise UserError(_('Only posted invoices can be finalized for e-Tax.'))
        
        self.write({
            'etax_finalized': True,
            'etax_finalized_date': fields.Datetime.now(),
            'etax_finalized_by': self.env.uid,
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('e-Tax Finalized'),
                'message': _('%d invoice(s) have been finalized for e-Tax and can no longer be modified.') % len(self),
                'type': 'success',
                'sticky': False,
            }
        }
    
    def action_reset_etax_export(self):
        """Reset e-Tax export status (only if not finalized)"""
        for move in self:
            if move.etax_finalized:
                raise UserError(_('Cannot reset export status for finalized invoice %s.') % move.name)
        
        self.write({
            'etax_exported': False,
            'etax_export_date': False,
            'etax_export_batch': False,
        })
    
    def action_unfinalize_etax(self):
        """Unfinalize e-Tax invoices (manager only)"""
        self.write({
            'etax_finalized': False,
            'etax_finalized_date': False,
            'etax_finalized_by': False,
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('e-Tax Unfinalized'),
                'message': _('%d invoice(s) have been unfinalized and can now be modified.') % len(self),
                'type': 'warning',
                'sticky': False,
            }
        }
    
    def write(self, vals):
        """Prevent modifications to finalized e-Tax invoices"""
        # Fields that are allowed to be updated even on finalized invoices
        allowed_fields = {
            'etax_finalized', 'etax_finalized_date', 'etax_finalized_by',
            'etax_exported', 'etax_export_date', 'etax_export_batch',
            'message_follower_ids', 'message_ids', 'activity_ids',
        }
        
        # Check if trying to modify restricted fields on finalized invoices
        modifying_restricted = bool(set(vals.keys()) - allowed_fields)
        
        if modifying_restricted:
            for move in self:
                if move.etax_finalized:
                    raise UserError(_(
                        'Cannot modify invoice %s because it has been finalized for e-Tax. '
                        'Contact your administrator to unfinalize it first.'
                    ) % move.name)
        
        return super().write(vals)
