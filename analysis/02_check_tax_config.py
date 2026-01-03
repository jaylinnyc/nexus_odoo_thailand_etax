"""
Analyze tax configuration to see if withholding tax is already set up
"""
from odoo_client import OdooClient
import json


def main():
    client = OdooClient()
    
    print("\n" + "="*80)
    print("ANALYZING TAX CONFIGURATION")
    print("="*80)
    
    # Get all taxes
    taxes = client.search_read(
        'account.tax',
        [('active', '=', True)],
        ['name', 'amount', 'type_tax_use', 'tax_group_id', 'description']
    )
    
    print(f"\n📊 Found {len(taxes)} active taxes")
    
    # Categorize taxes
    vat_taxes = []
    wht_taxes = []
    other_taxes = []
    
    for tax in taxes:
        name_lower = tax['name'].lower()
        desc_lower = (tax.get('description') or '').lower()
        
        if 'vat' in name_lower or 'ภาษี' in tax['name']:
            vat_taxes.append(tax)
        elif 'withhold' in name_lower or 'wht' in name_lower or 'หัก ณ ที่จ่าย' in tax['name']:
            wht_taxes.append(tax)
        else:
            other_taxes.append(tax)
    
    # Display results
    print(f"\n✅ VAT Taxes ({len(vat_taxes)}):")
    for tax in vat_taxes[:10]:
        print(f"  - {tax['name']}: {tax['amount']}% ({tax['type_tax_use']})")
    
    print(f"\n💰 Withholding Tax ({len(wht_taxes)}):")
    if wht_taxes:
        for tax in wht_taxes:
            print(f"  - {tax['name']}: {tax['amount']}% ({tax['type_tax_use']})")
    else:
        print("  ⚠️  No withholding taxes found")
    
    print(f"\n📌 Other Taxes ({len(other_taxes)}):")
    for tax in other_taxes[:5]:
        print(f"  - {tax['name']}: {tax['amount']}% ({tax['type_tax_use']})")
    
    # Save to file
    with open('tax_config.json', 'w') as f:
        json.dump({
            'vat_taxes': vat_taxes,
            'wht_taxes': wht_taxes,
            'other_taxes': other_taxes
        }, f, indent=2)
    print("\n💾 Tax configuration saved to: tax_config.json")


if __name__ == '__main__':
    main()
