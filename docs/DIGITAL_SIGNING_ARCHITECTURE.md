# Digital Signing Architecture for Thailand e-Tax

## Table of Contents
1. [Overview](#overview)
2. [Understanding USB Certificate Tokens](#understanding-usb-certificate-tokens)
3. [Architecture Options](#architecture-options)
4. [Recommended Architecture: Local Signing Service](#recommended-architecture-local-signing-service)
5. [Implementation Guide](#implementation-guide)
6. [Security Considerations](#security-considerations)
7. [Workflow Diagrams](#workflow-diagrams)

---

## Overview

Thailand's e-Tax system requires XML documents to be digitally signed using XAdES-BES (XML Advanced Electronic Signatures - Basic Electronic Signature) format. Businesses typically receive their signing certificates from authorized Certificate Authorities (CAs) in Thailand, delivered on **USB hardware tokens**.

### Common Thai e-Tax Certificate Providers
| Provider | Token Type | PKCS#11 Library |
|----------|-----------|-----------------|
| TOT (CAT Telecom) | SafeNet eToken | `libeTPkcs11.so` |
| INET | Gemalto/Thales | `libCryptoki2_64.so` |
| Thai Digital ID | Smart Card | `opensc-pkcs11.so` |

---

## Understanding USB Certificate Tokens

### What is a Hardware Token?

A USB certificate token (also called HSM - Hardware Security Module) is a physical device that:

1. **Stores the private key securely** - The key is generated ON the device and NEVER leaves it
2. **Performs cryptographic operations internally** - Signing happens inside the device
3. **Requires PIN authentication** - Protects against unauthorized use
4. **Is tamper-resistant** - Physical security prevents key extraction

### PKCS#11 Standard

PKCS#11 (Cryptoki) is the standard API for communicating with hardware tokens:

```
┌─────────────────────────────────────────────────────────────────┐
│                    PKCS#11 Architecture                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ Application  │    │  PKCS#11     │    │  USB Token   │      │
│  │ (Python)     │───▶│  Library     │───▶│  (HSM)       │      │
│  │              │    │  (.so/.dll)  │    │              │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│        │                    │                    │              │
│        │                    │                    │              │
│  1. Call sign()       2. Send hash         3. Sign hash        │
│     with PIN             to token          with private key    │
│                                                  │              │
│                          4. Return signature ◀───┘              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Key Security Principle

**The private key NEVER leaves the hardware token.**

When signing:
1. Application sends the DATA HASH to the token
2. Token signs the hash with its internal private key
3. Token returns only the SIGNATURE
4. Private key remains secure inside the device

---

## Architecture Options

### Option 1: Direct Integration (NOT Recommended)

```
┌─────────────────────────────────────────────────────────────────┐
│                    Direct Integration                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐                          │
│  │   Odoo       │───▶│  USB Token   │                          │
│  │   Server     │    │  (attached)  │                          │
│  │   (Cloud)    │    │              │                          │
│  └──────────────┘    └──────────────┘                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

❌ Problems:
- USB token must be attached to cloud server (impractical)
- PIN must be stored/entered on cloud server (security risk)
- Single point of failure
- No audit trail
- Difficult to manage multiple certificates
```

### Option 2: Browser Extension Signing (Complex)

```
┌─────────────────────────────────────────────────────────────────┐
│                 Browser Extension Signing                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  User's Workstation              │        Cloud                 │
│  ─────────────────               │        ─────                 │
│  ┌──────────────┐                │    ┌──────────────┐         │
│  │   Browser    │◀───────────────┼───▶│   Odoo       │         │
│  │ + Extension  │                │    │   Server     │         │
│  └──────┬───────┘                │    └──────────────┘         │
│         │                        │                              │
│         ▼                        │                              │
│  ┌──────────────┐                │                              │
│  │  USB Token   │                │                              │
│  │  (local)     │                │                              │
│  └──────────────┘                │                              │
│                                  │                              │
└─────────────────────────────────────────────────────────────────┘

⚠️ Challenges:
- Requires custom browser extension development
- Users must install drivers on each workstation
- Browser security policies may block extension
- PIN entry on each signing operation
```

### Option 3: Local Signing Service (✅ RECOMMENDED)

```
┌─────────────────────────────────────────────────────────────────┐
│              Local Signing Service Architecture                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Business Premises (On-Premise)         │     Cloud/Hosted    │
│   ──────────────────────────────         │     ────────────    │
│                                          │                      │
│   ┌──────────────┐                       │   ┌──────────────┐  │
│   │   Signing    │◀──── REST API ────────┼──▶│    Odoo      │  │
│   │   Service    │      (HTTPS)          │   │    Server    │  │
│   │   (Docker)   │                       │   │              │  │
│   └──────┬───────┘                       │   └──────────────┘  │
│          │                               │                      │
│          ▼                               │                      │
│   ┌──────────────┐                       │                      │
│   │  USB Token   │ (physically attached) │                      │
│   │              │                       │                      │
│   └──────────────┘                       │                      │
│          │                               │                      │
│          ▼                               │                      │
│   ┌──────────────┐                       │                      │
│   │  Local DB    │ (PostgreSQL)          │                      │
│   │  (Audit Log) │                       │                      │
│   └──────────────┘                       │                      │
│          │                               │                      │
│          ▼                               │                      │
│   ┌──────────────┐                       │                      │
│   │  Revenue     │ (Thai RD Gateway)     │                      │
│   │  Department  │                       │                      │
│   └──────────────┘                       │                      │
│                                          │                      │
└─────────────────────────────────────────────────────────────────┘

✅ Benefits:
- USB token stays on-premise (secure)
- Clear separation of concerns
- Full audit trail in local database
- Batch processing capability
- Can handle multiple certificates
- Docker provides consistent environment
- Compliant with security best practices
```

---

## Recommended Architecture: Local Signing Service

### System Components

```
thailand-etax-signing-service/
├── docker-compose.yml          # Container orchestration
├── Dockerfile                  # Signing service image
├── app/
│   ├── main.py                # FastAPI application
│   ├── signer.py              # PKCS#11 signing logic
│   ├── validator.py           # XML validation
│   ├── submitter.py           # Revenue Dept API client
│   ├── models.py              # Database models
│   └── config.py              # Configuration
├── db/
│   └── init.sql               # PostgreSQL schema
├── certs/                     # Certificate storage (public only)
└── logs/                      # Audit logs
```

### Complete Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                    Complete e-Tax Workflow                      │
├─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  STEP 1: Invoice Creation (Odoo)                               │
│  ════════════════════════════════                              │
│  ┌──────────────┐                                              │
│  │ Accountant   │                                              │
│  │ creates and  │──▶ Invoice posted in Odoo                    │
│  │ posts invoice│                                              │
│  └──────────────┘                                              │
│         │                                                       │
│         ▼                                                       │
│  STEP 2: XML Generation (Odoo)                                 │
│  ════════════════════════════════                              │
│  ┌──────────────┐                                              │
│  │ Odoo e-Tax   │                                              │
│  │ Module       │──▶ Generates ETDA-compliant unsigned XML     │
│  │              │                                              │
│  └──────────────┘                                              │
│         │                                                       │
│         ▼                                                       │
│  STEP 3: Batch Export (Odoo)                                   │
│  ════════════════════════════════                              │
│  ┌──────────────┐                                              │
│  │ Export       │                                              │
│  │ Wizard       │──▶ Collects unsigned XMLs for batch          │
│  │              │    Sends to Signing Service via API          │
│  └──────────────┘                                              │
│         │                                                       │
│         │  HTTPS POST /api/sign/batch                          │
│         │  { "documents": [...unsigned XMLs...] }              │
│         ▼                                                       │
│  ═══════════════════════════════════════════════════════════   │
│  │           ON-PREMISE SIGNING SERVICE                    │   │
│  ═══════════════════════════════════════════════════════════   │
│         │                                                       │
│         ▼                                                       │
│  STEP 4: Validation (Signing Service)                          │
│  ════════════════════════════════════                          │
│  ┌──────────────┐                                              │
│  │ Validator    │                                              │
│  │              │──▶ Validates XML against ETDA schema         │
│  │              │    Checks required fields                    │
│  └──────────────┘                                              │
│         │                                                       │
│         ▼                                                       │
│  STEP 5: Digital Signing (Signing Service)                     │
│  ════════════════════════════════════════                      │
│  ┌──────────────┐    ┌──────────────┐                         │
│  │ PKCS#11      │───▶│ USB Token    │                         │
│  │ Signer       │◀───│ (Hardware)   │                         │
│  └──────────────┘    └──────────────┘                         │
│         │                 │                                     │
│         │                 │ PIN authentication                  │
│         │                 │ Sign with private key               │
│         │                 │ Return XAdES-BES signature          │
│         ▼                                                       │
│  STEP 6: Record Keeping (Signing Service)                      │
│  ════════════════════════════════════════                      │
│  ┌──────────────┐                                              │
│  │ PostgreSQL   │                                              │
│  │ Database     │──▶ Store signed XML                          │
│  │              │    Store signature details                   │
│  │              │    Store audit log entry                     │
│  └──────────────┘                                              │
│         │                                                       │
│         ▼                                                       │
│  STEP 7: Submit to Revenue Dept (Signing Service)              │
│  ════════════════════════════════════════════════              │
│  ┌──────────────┐    ┌──────────────┐                         │
│  │ Submitter    │───▶│ Thai Revenue │                         │
│  │              │◀───│ Dept Gateway │                         │
│  └──────────────┘    └──────────────┘                         │
│         │                 │                                     │
│         │                 │ Submission receipt                  │
│         │                 │ Confirmation number                 │
│         ▼                                                       │
│  STEP 8: Update Status (Signing Service → Odoo)                │
│  ═══════════════════════════════════════════════               │
│  ┌──────────────┐                                              │
│  │ Callback to  │                                              │
│  │ Odoo API     │──▶ Update invoice status                     │
│  │              │    Store confirmation number                 │
│  └──────────────┘                                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow Summary

| Step | Source | Destination | Data |
|------|--------|-------------|------|
| 1 | Odoo | Signing Service | Unsigned XML batch |
| 2 | Signing Service | USB Token | Hash to sign |
| 3 | USB Token | Signing Service | Digital signature |
| 4 | Signing Service | Local DB | Signed XML + audit log |
| 5 | Signing Service | Revenue Dept | Signed XML |
| 6 | Revenue Dept | Signing Service | Confirmation |
| 7 | Signing Service | Odoo | Status update |

---

## Implementation Guide

### Prerequisites

1. **Hardware**
   - Server/PC at business premises
   - USB certificate token from authorized Thai CA
   - Network connectivity to Odoo and Revenue Department

2. **Software**
   - Docker & Docker Compose
   - PKCS#11 driver for your token type
   - PostgreSQL (containerized)

### Step 1: Identify Your Token

```bash
# List USB devices
lsusb

# Example output:
# Bus 001 Device 003: ID 0529:0620 Aladdin Knowledge Systems Token

# Check if recognized as smart card
pcsc_scan
```

### Step 2: Install PKCS#11 Driver

```bash
# For SafeNet eToken (TOT)
# Download from SafeNet website and install

# For generic smart cards
sudo apt install opensc opensc-pkcs11

# Verify library location
ls -la /usr/lib/x86_64-linux-gnu/opensc-pkcs11.so
# or
ls -la /usr/lib/libeTPkcs11.so
```

### Step 3: Test Token Access

```bash
# List available tokens
pkcs11-tool --module /usr/lib/opensc-pkcs11.so --list-tokens

# List objects (requires PIN)
pkcs11-tool --module /usr/lib/opensc-pkcs11.so --list-objects --login

# Test signing
echo "test" | pkcs11-tool --module /usr/lib/opensc-pkcs11.so --sign --login
```

### Step 4: Deploy Signing Service

See [SIGNING_SERVICE_SETUP.md](./SIGNING_SERVICE_SETUP.md) for detailed Docker setup instructions.

---

## Security Considerations

### Physical Security
- [ ] Signing server in secure location
- [ ] USB token secured when not in use
- [ ] Access restricted to authorized personnel

### Network Security
- [ ] HTTPS/TLS for all API communications
- [ ] API authentication (API keys or OAuth)
- [ ] Firewall rules limiting access
- [ ] VPN for Odoo ↔ Signing Service communication

### Credential Security
- [ ] PIN never stored in plain text
- [ ] PIN entered at signing time only
- [ ] Consider HSM PIN pad for PIN entry
- [ ] Session timeout for PIN cache

### Audit & Compliance
- [ ] All signing operations logged
- [ ] Signed documents archived
- [ ] Regular backup of audit database
- [ ] Compliance with Thai RD requirements

### Certificate Management
- [ ] Monitor certificate expiration
- [ ] Secure renewal process documented
- [ ] Backup certificate (if extractable)

---

## Database Schema (Audit Log)

```sql
-- Signing requests table
CREATE TABLE signing_requests (
    id SERIAL PRIMARY KEY,
    request_id UUID UNIQUE NOT NULL,
    odoo_invoice_id VARCHAR(64),
    odoo_invoice_name VARCHAR(128),
    
    -- Document info
    document_type VARCHAR(32),  -- 'tax_invoice', 'credit_note', etc.
    seller_tax_id VARCHAR(13),
    buyer_tax_id VARCHAR(13),
    total_amount DECIMAL(15,2),
    
    -- Timestamps
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    validated_at TIMESTAMP,
    signed_at TIMESTAMP,
    submitted_at TIMESTAMP,
    
    -- Status
    status VARCHAR(32) DEFAULT 'pending',
    -- pending, validated, signed, submitted, confirmed, failed
    
    -- Results
    rd_confirmation_number VARCHAR(64),
    error_message TEXT,
    
    -- Documents
    unsigned_xml TEXT,
    signed_xml TEXT,
    
    -- Audit
    client_ip VARCHAR(45),
    user_agent VARCHAR(256)
);

-- Audit log table
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    request_id UUID REFERENCES signing_requests(request_id),
    action VARCHAR(64),
    details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45)
);

-- Certificate info (public data only)
CREATE TABLE certificates (
    id SERIAL PRIMARY KEY,
    serial_number VARCHAR(64) UNIQUE,
    subject_cn VARCHAR(256),
    issuer_cn VARCHAR(256),
    valid_from TIMESTAMP,
    valid_until TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## API Specification

### Sign Batch Endpoint

```
POST /api/v1/sign/batch
Authorization: Bearer <api_key>
Content-Type: application/json

Request:
{
    "callback_url": "https://odoo.example.com/api/etax/callback",
    "documents": [
        {
            "invoice_id": "INV/2025/00001",
            "xml_content": "<rsm:TaxInvoice_CrossIndustryInvoice>...</rsm:TaxInvoice_CrossIndustryInvoice>"
        },
        {
            "invoice_id": "INV/2025/00002", 
            "xml_content": "<rsm:TaxInvoice_CrossIndustryInvoice>...</rsm:TaxInvoice_CrossIndustryInvoice>"
        }
    ]
}

Response:
{
    "batch_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "processing",
    "document_count": 2,
    "message": "Batch queued for signing"
}
```

### Check Status Endpoint

```
GET /api/v1/sign/batch/{batch_id}
Authorization: Bearer <api_key>

Response:
{
    "batch_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "completed",
    "documents": [
        {
            "invoice_id": "INV/2025/00001",
            "status": "signed",
            "signed_xml": "<rsm:TaxInvoice_CrossIndustryInvoice>...<ds:Signature>...</ds:Signature></rsm:TaxInvoice_CrossIndustryInvoice>",
            "rd_confirmation": "RD20251222001234"
        },
        {
            "invoice_id": "INV/2025/00002",
            "status": "signed",
            "signed_xml": "...",
            "rd_confirmation": "RD20251222001235"
        }
    ]
}
```

### Callback to Odoo

```
POST {callback_url}
Content-Type: application/json

{
    "batch_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "completed",
    "results": [
        {
            "invoice_id": "INV/2025/00001",
            "status": "success",
            "rd_confirmation": "RD20251222001234",
            "signed_at": "2025-12-22T10:30:00Z"
        }
    ]
}
```

---

## Appendix: Thai Revenue Department Integration

### RD Gateway Endpoints (Example)

> **Note:** Actual endpoints may vary. Consult official RD documentation.

| Environment | Base URL |
|-------------|----------|
| Sandbox | `https://etax-sandbox.rd.go.th/api/` |
| Production | `https://etax.rd.go.th/api/` |

### Typical Submission Flow

1. **Authenticate** with RD credentials
2. **Submit** signed XML
3. **Receive** confirmation number
4. **Query** status (if async)

---

## Next Steps

1. **Review this architecture** with your IT team
2. **Identify your specific token type** and obtain PKCS#11 driver
3. **Set up test environment** with sandbox credentials
4. **Implement signing service** (separate project)
5. **Integrate Odoo module** with signing service API

---

## Related Documentation

- [IMPLEMENTATION_STATUS.md](../IMPLEMENTATION_STATUS.md) - Module implementation status
- [SIGNING_SERVICE_SETUP.md](./SIGNING_SERVICE_SETUP.md) - Docker setup guide (TODO)
- [API_INTEGRATION.md](./API_INTEGRATION.md) - API integration guide (TODO)
