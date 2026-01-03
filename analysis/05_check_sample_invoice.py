"""
Get sample invoice data to understand the actual data structure
"""
from odoo_client import OdooClient
import json


def main():
    client = OdooClient()
    
    print("\n" + "="*80)
    print("ANALYZING SAMPLE INVOICE DATA")
    print("="*80)
    
    # Get a sample posted invoice
    print("\n🔍 Searching for posted invoices...")
    invoices = client.search_read(
        'account.move',
        [
            ('move_type', 'in', ['out_invoice', 'out_refund']),
            ('state', '=', 'posted')
        ],
        [
            'name', 'move_type', 'invoice_date', 'partner_id',
            'amount_untaxed', 'amount_tax', 'amount_total',
            'ref', 'invoice_origin', 'reversed_entry_id',
            'invoice_payment_term_id', 'invoice_date_due',
        ],
        limit=5
    )
    
    if not invoices:
        print("⚠️  No posted invoices found")
        return
    
    print(f"\n✅ Found {len(invoices)} sample invoices\n")
    
    for idx, inv in enumerate(invoices, 1):
        print(f"\n{'='*60}")
        print(f"Invoice #{idx}: {inv['name']}")
        print(f"{'='*60}")
        print(f"Type: {inv['move_type']}")
        print(f"Date: {inv['invoice_date']}")
        print(f"Customer: {inv['partner_id'][1] if inv.get('partner_id') else 'N/A'}")
        print(f"Subtotal: {inv['amount_untaxed']}")
        print(f"Tax: {inv['amount_tax']}")
        print(f"Total: {inv['amount_total']}")
        print(f"Reference: {inv.get('ref', 'N/A')}")
        print(f"Origin: {inv.get('invoice_origin', 'N/A')}")
        print(f"Reversed Entry: {inv.get('reversed_entry_id', 'N/A')}")
        print(f"Payment Terms: {inv.get('invoice_payment_term_id', ['N/A'])[1] if inv.get('invoice_payment_term_id') else 'N/A'}")
        print(f"Due Date: {inv.get('invoice_date_due', 'N/A')}")
        
        # Get invoice lines
        print(f"\n📋 Invoice Lines:")
        lines = client.search_read(
            'account.move.line',
            [
                ('move_id', '=', inv['id']),
                ('display_type', '=', 'product')
            ],
            [
                'name', 'product_id', 'quantity', 'product_uom_id',
                'price_unit', 'discount', 'price_subtotal',
                'tax_ids'
            ]
        )
        
        for line_idx, line in enumerate(lines, 1):
            print(f"\n  Line {line_idx}:")
            print(f"    Product: {line.get('product_id', ['N/A'])[1] if line.get('product_id') else 'N/A'}")
            print(f"    Description: {line.get('name', 'N/A')}")
            print(f"    Quantity: {line.get('quantity', 0)}")
            print(f"    UoM: {line.get('product_uom_id', ['N/A'])[1] if line.get('product_uom_id') else 'N/A'}")
            print(f"    Unit Price: {line.get('price_unit', 0)}")
            print(f"    Discount: {line.get('discount', 0)}%")
            print(f"    Subtotal: {line.get('price_subtotal', 0)}")
            
            if line.get('tax_ids'):
                tax_names = []
                for tax_id in line['tax_ids']:
                    tax = client.search_read('account.tax', [('id', '=', tax_id)], ['name'], limit=1)
                    if tax:
                        tax_names.append(tax[0]['name'])
                print(f"    Taxes: {', '.join(tax_names)}")
    
    # Save to file
    with open('sample_invoices.json', 'w') as f:
        json.dump(invoices, f, indent=2, default=str)
    print("\n\n💾 Sample invoices saved to: analysis/sample_invoices.json")


if __name__ == '__main__':
    main()
