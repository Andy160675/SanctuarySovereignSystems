# Pentad Connection Layer: Sovereign Network Architecture

## Protocol Stack

1. **Physical Layer**: Dedicated hardware nodes (Node-0, Node-1).
2. **Data Link Layer**: Physical segmentation via Ubiquiti switch.
3. **Network Layer**: Isolated Pentad VLAN (ID 100, 10.0.100.0/24).
4. **Transport Layer**: Constitutional Messaging with priority queuing.
5. **Session Layer**: Sovereign TLS (sTLS) - Mutual TLS 1.3 with evidence logging.
6. **Governance Layer**: RBAC enforced via certificate roles and constitutional rules.
7. **Application Layer**: Sovereign agentic services.

## Cryptographic Foundation (PKI)

The system uses a private Root CA and per-head Intermediate CAs to issue role-constrained certificates.

- **Root CA**: 20-year validity, stored in `evidence_store/pki/root-ca.key`.
- **Intermediate CAs**: One per head (PC-A to PC-E), used to sign leaf certificates.
- **Leaf Certificates**: 1-year validity, include role-based Distinguished Names and Subject Alternative Names (SANs).

### Roles and Mapping
- **PC-A**: Constitutional (Sovereign Legislature)
- **PC-B**: Orchestration (Sovereign Executive)
- **PC-C**: Verification (Sovereign Judiciary)
- **PC-D**: Analytics (Sovereign Intelligence)
- **PC-E**: Safety (Sovereign Security)

## Sovereign TLS (sTLS)

sTLS extends standard TLS 1.3 by:
- Requiring Mutual TLS (mTLS) for all connections.
- Generating cryptographic evidence of every handshake (CN, fingerprint, cipher).
- Restricting ciphers to `ECDHE-ECDSA-AES256-GCM-SHA384` and `ECDHE-RSA-AES256-GCM-SHA384`.

Handshake evidence is archived in `evidence_store/connection/handshake_<head>.jsonl`.

## Constitutional Messaging

Messages are encapsulated in `ConstitutionalMessage` dataclasses:
- **Priority**: Critical, High, Normal, Low.
- **Evidence Chain**: Each message contains hashes of previous messages in the flow.
- **Signing**: Messages are cryptographically signed by the sender.

Delivery evidence is archived in `evidence_store/connection/delivery_<head>.jsonl`.

## Operational Commands (Windows/Node-0)

### 1. Initialize Connection Layer
Bootstrap PKI and generate all head certificates:
```powershell
powershell -ExecutionPolicy Bypass -File scripts/ops/Deploy-ConnectionLayer.ps1
```

### 2. Verify Connectivity
Run integrity checks and loopback verification:
```powershell
powershell -ExecutionPolicy Bypass -File scripts/ops/Verify-ConnectionLayer.ps1
```

### 3. Manual Certificate Generation
Generate a specific head certificate:
```powershell
python -c "from core.transport.certificate_generator import HeadCertificateGenerator; HeadCertificateGenerator('pc-a', 'constitutional', '10.0.100.11').generate_certificate()"
```

## Security Boundaries
- **Intra-Pentad**: Unrestricted communication between heads over VLAN 100.
- **External**: All external traffic blocked by default, except through **PC-E** (Safety Head) for monitoring and essential updates.
- **NAS**: All connection and delivery evidence is synchronized to `nas-01` for immutable archiving.
