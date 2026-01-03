"""
Analyze account.move (Invoice) fields to see what already exists
"""
from odoo_client import OdooClient
import json


def main():
    client = OdooClient()
    
    print("\n" + "="*80)
    print("ANALYZING ACCOUNT.MOVE (INVOICE) FIELDS")
    print("="*80)
    
    # Get all fields for account.move
    fields = client.get_fields('account.move')
    
    # Key fields we're interested in
    key_fields = {
        'Credit/Debit Note Reference': [
            'reversed_entry_id',
            'reversal_move_id', 
            'ref',
            'invoice_origin',
        ],
        'Payment Terms': [
            'invoice_payment_term_id',
            'invoice_date_due',
        ],
        'Tax Information': [
            'amount_tax',
            'amount_untaxed', 
            'amount_total',
            'tax_totals',
        ],
        'Existing e-Tax Fields': [
            'etax_exported',
            'etax_export_date',
            'etax_export_batch',
            'etax_finalized',
            'etax_reference_number',
            'etax_reference_date',
            'etax_withholding_tax_rate',
            'etax_withholding_tax_amount',
        ],
    }
    
    # Check which fields exist
    field_names = [f['name'] for f in fields]
    
    for category, field_list in key_fields.items():
        print(f"\n📋 {category}:")
        for field in field_list:
            exists = field in field_names
            status = "✅ EXISTS" if exists else "❌ MISSING"
            print(f"  {status}: {field}")
            
            if exists:
                field_info = next(f for f in fields if f['name'] == field)
                print(f"     Type: {field_info['ttype']}, Label: {field_info['field_description']}")
    
    # Find all custom etax fields
    etax_fields = [f for f in fields if 'etax' in f['name'].lower()]
    
    if etax_fields:
        print(f"\n🔍 Found {len(etax_fields)} custom e-Tax fields:")
        for f in etax_fields:
            print(f"  - {f['name']} ({f['ttype']}): {f['field_description']}")
    else:
        print("\n⚠️  No custom e-Tax fields found in database")
    
    # Save full field list to file
    with open('invoice_fields.json', 'w') as f:
        json.dump(fields, f, indent=2)
    print("\n💾 Full field list saved to: invoice_fields.json")


if __name__ == '__main__':
    main()
