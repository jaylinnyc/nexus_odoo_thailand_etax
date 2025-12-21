#!/bin/bash
# Thailand e-Tax Module - Installation Verification Script

echo "================================================"
echo "Thailand e-Tax Module - Installation Check"
echo "================================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track results
ERRORS=0
WARNINGS=0

# Check module structure
echo "1. Checking module structure..."
REQUIRED_FILES=(
    "__init__.py"
    "__manifest__.py"
    "README.md"
    "models/__init__.py"
    "models/account_move.py"
    "models/etax_config.py"
    "models/res_company.py"
    "wizards/__init__.py"
    "wizards/etax_export_wizard.py"
    "views/account_move_views.xml"
    "views/etax_config_views.xml"
    "views/etax_export_wizard_views.xml"
    "views/res_company_views.xml"
    "security/ir.model.access.csv"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "  ${GREEN}✓${NC} $file"
    else
        echo -e "  ${RED}✗${NC} $file (MISSING)"
        ERRORS=$((ERRORS + 1))
    fi
done

# Check Python syntax
echo ""
echo "2. Checking Python syntax..."
for pyfile in __init__.py models/*.py wizards/*.py; do
    if python3 -m py_compile "$pyfile" 2>/dev/null; then
        echo -e "  ${GREEN}✓${NC} $pyfile"
    else
        echo -e "  ${RED}✗${NC} $pyfile (SYNTAX ERROR)"
        ERRORS=$((ERRORS + 1))
    fi
done

# Check XML syntax
echo ""
echo "3. Checking XML syntax..."
for xmlfile in views/*.xml; do
    if xmllint --noout "$xmlfile" 2>/dev/null; then
        echo -e "  ${GREEN}✓${NC} $xmlfile"
    else
        echo -e "  ${RED}✗${NC} $xmlfile (XML ERROR)"
        ERRORS=$((ERRORS + 1))
    fi
done

# Check ETDA repositories
echo ""
echo "4. Checking ETDA reference repositories..."
if [ -d "schemas/soda-etax" ]; then
    echo -e "  ${GREEN}✓${NC} soda-etax repository cloned"
else
    echo -e "  ${YELLOW}⚠${NC} soda-etax repository not found"
    WARNINGS=$((WARNINGS + 1))
fi

if [ -d "schemas/etax-xades" ]; then
    echo -e "  ${GREEN}✓${NC} etax-xades repository cloned"
else
    echo -e "  ${YELLOW}⚠${NC} etax-xades repository not found"
    WARNINGS=$((WARNINGS + 1))
fi

# Check documentation
echo ""
echo "5. Checking documentation..."
DOCS=("README.md" "RESEARCH_AND_PLAN.md" "QUICK_START.md" "IMPLEMENTATION_STATUS.md")
for doc in "${DOCS[@]}"; do
    if [ -f "$doc" ]; then
        echo -e "  ${GREEN}✓${NC} $doc"
    else
        echo -e "  ${YELLOW}⚠${NC} $doc (not found)"
        WARNINGS=$((WARNINGS + 1))
    fi
done

# Check Python dependencies (optional)
echo ""
echo "6. Checking Python dependencies (optional for Phase 2)..."
DEPENDENCIES=("lxml" "xmlsec" "cryptography" "OpenSSL")
for dep in "${DEPENDENCIES[@]}"; do
    if python3 -c "import $dep" 2>/dev/null; then
        echo -e "  ${GREEN}✓${NC} $dep installed"
    else
        echo -e "  ${YELLOW}⚠${NC} $dep not installed (needed for Phase 2)"
        WARNINGS=$((WARNINGS + 1))
    fi
done

# Summary
echo ""
echo "================================================"
echo "Summary"
echo "================================================"
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ All critical checks passed!${NC}"
    echo ""
    echo "Module is ready for installation in Odoo 19."
    echo ""
    echo "Next steps:"
    echo "1. Install module in Odoo: Apps → Update Apps List → Install"
    echo "2. Configure company: Settings → Companies → e-Tax Thailand tab"
    echo "3. Configure e-Tax: Accounting → Configuration → e-Tax Settings"
    echo "4. Test export on a posted invoice"
else
    echo -e "${RED}✗ $ERRORS error(s) found!${NC}"
    echo "Please fix errors before installing."
fi

if [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}⚠ $WARNINGS warning(s)${NC}"
    echo "Warnings don't prevent installation but may affect functionality."
fi

echo ""
echo "For detailed information, see:"
echo "  - README.md - Installation and usage guide"
echo "  - IMPLEMENTATION_STATUS.md - Current status and roadmap"
echo "  - QUICK_START.md - Developer quick start"
echo "================================================"

exit $ERRORS
