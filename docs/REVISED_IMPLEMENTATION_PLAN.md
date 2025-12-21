# Thailand e-Tax - Revised Implementation Plan

## Executive Summary

Based on the real-world requirement of using **USB hardware tokens** for digital signing, the implementation is split into two components:

1. **Odoo Module** (`nexus_odoo_thailand_etax`) - XML generation & workflow management
2. **Signing Service** (`thailand-etax-signing-service`) - Separate on-premise service for digital signing

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Production Architecture                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Cloud/Hosted                     │    Business Premises       │
│   ────────────                     │    ─────────────────       │
│                                    │                            │
│   ┌──────────────┐                 │    ┌──────────────┐       │
│   │    Odoo      │                 │    │   Signing    │       │
│   │    Server    │◀── REST API ───┼───▶│   Service    │       │
│   │              │    (HTTPS)      │    │   (Docker)   │       │
│   └──────────────┘                 │    └──────┬───────┘       │
│         │                          │           │                │
│   ┌─────▼──────┐                   │    ┌──────▼───────┐       │
│   │  Unsigned  │                   │    │  USB Token   │       │
│   │  XML Files │                   │    │  (Hardware)  │       │
│   └────────────┘                   │    └──────────────┘       │
│                                    │           │                │
│                                    │    ┌──────▼───────┐       │
│                                    │    │  Local DB    │       │
│                                    │    │  (Audit)     │       │
│                                    │    └──────────────┘       │
│                                    │           │                │
│                                    │    ┌──────▼───────┐       │
│                                    │    │  Thai RD     │       │
│                                    │    │  Gateway     │       │
│                                    │    └──────────────┘       │
│                                    │                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Revised Phase Plan

### Component 1: Odoo Module (`nexus_odoo_thailand_etax`)

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Foundation Setup | ✅ Complete |
| 2 | XML Schema Integration | ✅ Complete |
| 3 | Core Models | ✅ Complete |
| 4 | ETDA XML Generation | ✅ Complete |
| 5 | Validation Module | ✅ Complete |
| 6 | Signing Service Integration | 🔄 In Progress |
| 7 | User Interface & Workflow | ✅ Complete |
| 8 | Testing & Documentation | 🔄 In Progress |

### Component 2: Signing Service (`thailand-etax-signing-service`)

| Phase | Description | Status |
|-------|-------------|--------|
| A | Project Setup (Docker/FastAPI) | 📋 Planned |
| B | PKCS#11 Integration | 📋 Planned |
| C | XAdES-BES Signing | 📋 Planned |
| D | Database & Audit Log | 📋 Planned |
| E | Revenue Dept Integration | 📋 Planned |
| F | API Security | 📋 Planned |
| G | Testing & Deployment | 📋 Planned |

---

## Component 1: Odoo Module

### What's Implemented

#### ✅ Phase 1-5: Core Functionality
- Company/Partner Thai tax fields
- ETDA-compliant XML generation
- Tax Invoice (388) and Credit Note (381) support
- Thai Tax ID validation (mod-11 algorithm)
- Branch ID validation

#### ✅ Phase 7: User Interface
- Export buttons on invoice form
- Batch export wizard
- Status tracking badges
- Configuration screens

#### 🔄 Phase 6: Signing Service Integration (UPDATED)

**Original Plan:** Direct XAdES-BES signing in Odoo
**Revised Plan:** REST API integration with external signing service

```python
# models/account_move.py - Updated approach

class AccountMove(models.Model):
    _inherit = 'account.move'
    
    # New fields for signing service integration
    etax_signing_batch_id = fields.Char('Signing Batch ID')
    etax_rd_confirmation = fields.Char('RD Confirmation Number')
    etax_signed_at = fields.Datetime('Signed At')
    
    def action_send_to_signing_service(self):
        """Send unsigned XML to signing service"""
        config = self.env['etax.config'].get_active_config()
        
        # Generate unsigned XML
        xml_content = self._generate_etax_xml()
        
        # Send to signing service
        response = requests.post(
            f"{config.signing_service_url}/api/v1/sign/batch",
            headers={'Authorization': f'Bearer {config.signing_api_key}'},
            json={
                'callback_url': config.callback_url,
                'documents': [{
                    'invoice_id': self.name,
                    'xml_content': xml_content
                }]
            }
        )
        
        if response.ok:
            self.etax_signing_batch_id = response.json()['batch_id']
            self.etax_status = 'pending_signature'
```

### Files to Update

| File | Changes Needed |
|------|----------------|
| `models/etax_config.py` | Add signing service URL, API key fields |
| `models/account_move.py` | Add signing service integration methods |
| `views/etax_config_views.xml` | Add signing service configuration tab |
| `controllers/callback.py` | NEW: Handle signing service callbacks |

---

## Component 2: Signing Service (New Repository)

### Recommended Tech Stack

```yaml
# docker-compose.yml structure
services:
  signing-service:
    build: .
    image: thailand-etax-signing:latest
    ports:
      - "8443:8443"
    volumes:
      - /dev/bus/usb:/dev/bus/usb  # USB passthrough
    devices:
      - /dev/usb/hiddev0  # Smart card reader
    environment:
      - PKCS11_MODULE=/usr/lib/opensc-pkcs11.so
      - DATABASE_URL=postgresql://...
    
  postgres:
    image: postgres:15
    volumes:
      - pgdata:/var/lib/postgresql/data
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/sign/batch` | Submit batch for signing |
| GET | `/api/v1/sign/batch/{id}` | Check batch status |
| GET | `/api/v1/sign/document/{id}` | Get signed document |
| POST | `/api/v1/config/test` | Test token connectivity |
| GET | `/api/v1/certificates` | List available certificates |
| GET | `/api/v1/health` | Health check |

### Key Features

1. **PKCS#11 Integration**
   - Support multiple token types
   - PIN caching with configurable timeout
   - Certificate chain handling

2. **Batch Processing**
   - Queue management
   - Parallel signing (if multiple tokens)
   - Retry logic for failures

3. **Audit & Compliance**
   - All operations logged
   - Document archival
   - Search and retrieval

4. **Revenue Department Integration**
   - Sandbox and production environments
   - Automatic submission
   - Status tracking

---

## Implementation Priority

### Immediate (This Sprint)

1. **Update Odoo module** for signing service integration:
   - Add configuration fields
   - Add API client methods
   - Add callback controller

2. **Create signing service skeleton**:
   - Docker setup
   - FastAPI application
   - Basic PKCS#11 test

### Short-term (Next Sprint)

3. **Complete signing service**:
   - Full PKCS#11 signing
   - Database setup
   - Batch processing

4. **Integration testing**:
   - End-to-end flow
   - Error handling
   - Recovery scenarios

### Medium-term

5. **Revenue Department integration**:
   - API research
   - Sandbox testing
   - Production certification

6. **Production deployment**:
   - Security hardening
   - Monitoring setup
   - Documentation

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Token compatibility | High | Test with actual token early |
| RD API changes | Medium | Monitor official announcements |
| Network reliability | Medium | Implement retry logic, offline queue |
| PIN management | Medium | Implement secure PIN caching |
| Certificate expiration | Low | Add monitoring and alerts |

---

## Questions to Resolve

1. **Token Details**
   - What brand/model is the USB token?
   - What PKCS#11 library does it use?
   - Is documentation available?

2. **Revenue Department**
   - Do you have sandbox credentials?
   - What is the submission API?
   - Are there rate limits?

3. **Infrastructure**
   - Where will signing service run?
   - Network connectivity to Odoo?
   - Backup/redundancy requirements?

---

## Next Steps

1. ☐ Confirm USB token type and obtain PKCS#11 driver
2. ☐ Create new repository for signing service
3. ☐ Set up Docker development environment
4. ☐ Test token access with `pkcs11-tool`
5. ☐ Update Odoo module with signing service integration
6. ☐ Implement signing service MVP
7. ☐ End-to-end testing
