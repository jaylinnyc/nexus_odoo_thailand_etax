# -*- coding: utf-8 -*-
"""
e-Tax Callback Controller
=========================
Handles callbacks from the signing service to update invoice status.
"""

from odoo import http
from odoo.http import request
import json
import logging
import base64

_logger = logging.getLogger(__name__)


class EtaxCallbackController(http.Controller):
    """Controller to handle callbacks from signing service"""
    
    @http.route('/etax/callback', type='json', auth='public', methods=['POST'], csrf=False)
    def etax_callback(self, **kwargs):
        """
        Callback endpoint for signing service to update invoice status.
        
        Expected payload:
        {
            "batch_id": "uuid",
            "status": "completed|failed",
            "results": [
                {
                    "invoice_id": "INV/2025/00001",
                    "document_id": "uuid",
                    "status": "signed|submitted|confirmed|failed",
                    "signed_xml": "...",
                    "rd_confirmation": "RD...",
                    "signed_at": "2025-01-01T12:00:00Z",
                    "submitted_at": "2025-01-01T12:05:00Z",
                    "error_message": null
                }
            ]
        }
        """
        try:
            # Get JSON data
            data = request.jsonrequest
            
            batch_id = data.get('batch_id')
            results = data.get('results', [])
            
            _logger.info(f'Received e-Tax callback for batch {batch_id} with {len(results)} documents')
            
            processed = 0
            errors = []
            
            for result in results:
                try:
                    self._process_callback_result(result)
                    processed += 1
                except Exception as e:
                    _logger.error(f'Error processing callback result: {e}')
                    errors.append({
                        'invoice_id': result.get('invoice_id'),
                        'error': str(e)
                    })
            
            return {
                'success': True,
                'processed': processed,
                'errors': errors
            }
            
        except Exception as e:
            _logger.error(f'Error in e-Tax callback: {e}')
            return {
                'success': False,
                'error': str(e)
            }
    
    def _process_callback_result(self, result):
        """Process a single callback result"""
        invoice_id = result.get('invoice_id')
        document_id = result.get('document_id')
        status = result.get('status')
        
        # Find the invoice
        invoice = request.env['account.move'].sudo().search([
            '|',
            ('name', '=', invoice_id),
            ('etax_document_id', '=', document_id)
        ], limit=1)
        
        if not invoice:
            raise ValueError(f'Invoice not found: {invoice_id}')
        
        # Update based on status
        vals = {}
        
        if status == 'signed':
            vals['etax_status'] = 'signed'
            vals['etax_signature_date'] = result.get('signed_at')
            
            # Store signed XML if provided
            signed_xml = result.get('signed_xml')
            if signed_xml:
                vals['etax_signed_xml_file'] = base64.b64encode(signed_xml.encode('utf-8'))
            
            # Store RD confirmation if available
            rd_confirmation = result.get('rd_confirmation')
            if rd_confirmation:
                vals['etax_rd_confirmation'] = rd_confirmation
                
        elif status == 'submitted':
            vals['etax_status'] = 'submitted'
            vals['etax_submitted_date'] = result.get('submitted_at')
            
        elif status == 'confirmed':
            vals['etax_status'] = 'confirmed'
            vals['etax_rd_confirmation'] = result.get('rd_confirmation')
            
        elif status == 'failed':
            vals['etax_status'] = 'error'
            vals['etax_error_message'] = result.get('error_message', 'Unknown error from signing service')
        
        if vals:
            invoice.write(vals)
            _logger.info(f'Updated invoice {invoice.name} with status {status}')
    
    @http.route('/etax/health', type='http', auth='public', methods=['GET'], csrf=False)
    def health_check(self):
        """Simple health check endpoint"""
        return request.make_json_response({
            'status': 'ok',
            'service': 'odoo-etax-module'
        })
