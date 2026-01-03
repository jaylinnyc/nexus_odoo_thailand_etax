"""
Run all analysis scripts in sequence
"""
import subprocess
import sys


def run_script(script_name):
    """Run a Python script and print output"""
    print(f"\n{'='*80}")
    print(f"RUNNING: {script_name}")
    print(f"{'='*80}")
    
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running {script_name}:")
        print(e.stdout)
        print(e.stderr)
        return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False


def main():
    print("\n" + "="*80)
    print("ODOO ANALYSIS SUITE")
    print("="*80)
    print("\nThis will analyze your Odoo instance to determine what's needed for e-Tax export")
    
    scripts = [
        '01_check_invoice_fields.py',
        '02_check_tax_config.py',
        '03_check_company_partner_fields.py',
        '04_check_uom.py',
        '05_check_sample_invoice.py',
    ]
    
    results = {}
    for script in scripts:
        success = run_script(script)
        results[script] = success
    
    # Summary
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE - SUMMARY")
    print("="*80)
    
    for script, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{status}: {script}")
    
    print("\n📁 Results saved to analysis/ folder")
    print("\nNext steps:")
    print("1. Review the JSON files in analysis/ folder")
    print("2. Check what fields already exist vs what needs to be added")
    print("3. Update the e-Tax module accordingly")


if __name__ == '__main__':
    main()
