"""
Check res.company and res.partner fields for Thai address support
"""
from odoo_client import OdooClient
import json


def main():
    client = OdooClient()
    
    print("\n" + "="*80)
    print("ANALYZING COMPANY & PARTNER FIELDS")
    print("="*80)
    
    # Check res.company fields
    print("\n📋 Checking res.company fields...")
    company_fields = client.get_fields('res.company')
    
    thai_address_fields = [
        'etax_tax_id',
        'etax_branch_id',
        'etax_sub_district',
        'etax_district',
        'etax_province',
        'etax_building_name',
        'etax_moo',
        'etax_soi',
    ]
    
    company_field_names = [f['name'] for f in company_fields]
    
    print("\n🏢 Company Thai Address Fields:")
    for field in thai_address_fields:
        exists = field in company_field_names
        status = "✅ EXISTS" if exists else "❌ MISSING"
        print(f"  {status}: {field}")
    
    # Check res.partner fields
    print("\n📋 Checking res.partner fields...")
    partner_fields = client.get_fields('res.partner')
    partner_field_names = [f['name'] for f in partner_fields]
    
    print("\n👤 Partner Thai Address Fields:")
    for field in thai_address_fields:
        exists = field in partner_field_names
        status = "✅ EXISTS" if exists else "❌ MISSING"
        print(f"  {status}: {field}")
    
    # Get sample company data
    print("\n📊 Sample Company Data:")
    companies = client.search_read(
        'res.company',
        [],
        ['name', 'vat', 'street', 'street2', 'city', 'state_id', 'zip', 'country_id'],
        limit=1
    )
    if companies:
        comp = companies[0]
        print(f"  Company: {comp['name']}")
        print(f"  VAT: {comp.get('vat', 'Not set')}")
        print(f"  Address: {comp.get('street', 'Not set')}")
        print(f"  City: {comp.get('city', 'Not set')}")
        print(f"  State: {comp.get('state_id', ['Not set'])[1] if comp.get('state_id') else 'Not set'}")
        print(f"  Zip: {comp.get('zip', 'Not set')}")
    
    # Save to file
    with open('company_partner_fields.json', 'w') as f:
        json.dump({
            'company_fields': company_fields,
            'partner_fields': partner_fields,
            'sample_company': companies[0] if companies else None
        }, f, indent=2)
    print("\n💾 Results saved to: analysis/company_partner_fields.json")


if __name__ == '__main__':
    main()
