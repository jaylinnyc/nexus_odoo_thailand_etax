"""
Check UoM (Unit of Measure) configuration
"""
from odoo_client import OdooClient
import json


def main():
    client = OdooClient()
    
    print("\n" + "="*80)
    print("ANALYZING UOM (UNIT OF MEASURE) CONFIGURATION")
    print("="*80)
    
    # Check uom.uom fields
    print("\n📋 Checking uom.uom fields...")
    uom_fields = client.get_fields('uom.uom')
    uom_field_names = [f['name'] for f in uom_fields]
    
    etax_uom_fields = [
        'etax_code',
        'etax_name_th',
    ]
    
    print("\n📏 e-Tax UoM Fields:")
    for field in etax_uom_fields:
        exists = field in uom_field_names
        status = "✅ EXISTS" if exists else "❌ MISSING"
        print(f"  {status}: {field}")
    
    # Get all UoM units
    print("\n📊 Current UoM Units:")
    uoms = client.search_read(
        'uom.uom',
        [('active', '=', True)],
        ['name'],
        limit=50
    )
    
    print(f"\nFound {len(uoms)} active units:")
    for uom in uoms:
        print(f"  - {uom['name']}")
    
    # Save to file
    with open('uom_config.json', 'w') as f:
        json.dump({
            'uom_fields': uom_fields,
            'uom_units': uoms
        }, f, indent=2)
    print("\n💾 Results saved to: uom_config.json")


if __name__ == '__main__':
    main()
