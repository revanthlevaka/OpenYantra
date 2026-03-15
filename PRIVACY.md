# OpenYantra Privacy & Regional Compliance

> Four official regional profiles: OpenYantra-IN · OpenYantra-EU · OpenYantra-US · OpenYantra-CN

---

## The Core Privacy Claim

In OpenYantra, **the user is the sole data controller**. The Chitrapat (memory file) lives in storage the user owns. No third party has access. No data processing agreements needed. No cloud jurisdiction risks.

Every write is signed with a Mudra (SHA-256) and recorded permanently in the Agrasandhanī (audit ledger). The user can open the Chitrapat in LibreOffice at any time, read everything Chitragupta has written, and issue a Dharma-Adesh (override) on any cell.

*The record exists to serve the remembered, not the recorder.*

---

## GDPR Alignment (Universal)

| GDPR Principle | OpenYantra implementation |
|---|---|
| **Data control** | User owns the `.ods` file — no third-party access |
| **Right of access** | Open in LibreOffice — everything visible |
| **Right to rectification** | Edit any cell — Dharma-Adesh respected next session |
| **Right to erasure** | Delete rows/file — Chitragupta records deletion in Agrasandhanī |
| **Data portability** | ISO/IEC 26300 `.ods` — export to CSV, JSON anytime |
| **Privacy by design** | Local by default, structured, minimal |
| **Transparency** | Agrasandhanī — every write signed and auditable |

---

## OpenYantra-IN 🇮🇳 — India (Home Profile)

*Applicable: DPDP Act 2023, IT Act 2000*

India is OpenYantra's home. The Chitragupta heritage is explicit in this profile. The memory file is the Chitrapat. The LedgerAgent is Chitragupta. The audit trail is the Agrasandhanī. Built in Hyderabad; inspired by 3,000 years of Indian record-keeping tradition.

### DPDP Act 2023 Alignment

| DPDP Principle | OpenYantra-IN |
|---|---|
| **Consent** | `Consent_Flag` column on Identity and Beliefs — explicit consent before sensitive data is written |
| **Purpose limitation** | Each sheet scoped to a named purpose — agents must not read sheets beyond the current task |
| **Data minimisation** | Agents write only what the user explicitly shares (`Source = "User-stated"` preferred) |
| **Data localisation** | File stored on Indian infrastructure by default (AWS Mumbai, Azure India, GCP Mumbai, or local device) |
| **Right to correction** | Dharma-Adesh — user edits any cell, respected above all agent writes |
| **Right to erasure** | Delete the `.ods` file or specific rows — Chitragupta records the erasure in Agrasandhanī |
| **Grievance redressal** | Vivada log in Agrasandhanī serves as the dispute record |

### Additional columns (OpenYantra-IN)

| Column | Sheet | Values |
|---|---|---|
| `Consent_Flag` | Identity, Beliefs | `Explicit` / `Implied` / `Pending` |
| `Data_Fiduciary` | Agent Config | Name of the data fiduciary |
| `Localisation_Tag` | All sheets | `India-only` / `Cross-border-permitted` |

### Recommended file location

```
~/openyantra-in/
├── chitrapat.ods          ← The Chitrapat
├── sanchitta.json         ← Sanchitta (WriteQueue)
└── archive/
```

---

## OpenYantra-EU 🇪🇺 — Europe

*Applicable: GDPR, EU AI Act, Data Act 2023*

### GDPR

The user is the sole data controller (GDPR Article 4). No data processing agreement required. No cross-border transfer unless the user explicitly moves the file. The Agrasandhanī serves as the GDPR Article 13 transparency record.

### EU AI Act

The Agrasandhanī provides a complete timestamped record of every AI write — satisfying Article 13 transparency requirements for general-purpose AI systems using OpenYantra as memory backend.

### Additional columns (OpenYantra-EU)

| Column | Sheet | Values |
|---|---|---|
| `Data_Classification` | All sheets | `Personal` / `Sensitive` / `Professional` |
| `Retention_Policy` | All sheets | Days until archival (integer) |
| `Legal_Basis` | Identity, Beliefs | `Consent` / `Legitimate Interest` / `Contract` |

### Data sovereignty

File stays in EU-jurisdiction storage by default. Compatible with Gaia-X, EUCS-certified providers, and on-premises deployment.

---

## OpenYantra-US 🇺🇸 — United States

*Applicable: CCPA/CPRA, HIPAA, COPPA, FTC Act, state privacy laws*

### CCPA / CPRA Alignment

| Right | OpenYantra-US |
|---|---|
| **Right to know** | Open the `.ods` file — everything the AI knows is visible |
| **Right to delete** | Delete rows or the file — fully user-controlled |
| **Right to correct** | Edit any cell — Dharma-Adesh respected |
| **Right to opt-out of sale** | OpenYantra does not sell data — file is local |
| **Right to limit sensitive data use** | `Sensitivity_Tag` controls agent access per sheet |

### Additional columns (OpenYantra-US)

| Column | Sheet | Values |
|---|---|---|
| `Sensitivity_Tag` | All sheets | `General` / `Financial` / `Health` / `Biometric` / `Children` |
| `State_Jurisdiction` | Identity | User's state |
| `PHI_Flag` | Identity, Beliefs | `Yes` / `No` (HIPAA Protected Health Information) |

### Sector notes

**HIPAA:** Do not write health data without user consent. `PHI_Flag = "Yes"` triggers 7-year minimum retention (`Retention_Policy = 2555`). Enable LibreOffice file encryption for HIPAA-adjacent deployments.

**COPPA:** Do not use OpenYantra to store data about users under 13 without verifiable parental consent.

**State laws:** Illinois BIPA — do not write biometric identifiers without explicit consent. New York financial data — tag `Sensitivity_Tag = "Financial"`.

---

## OpenYantra-CN 🇨🇳 — China

*Applicable: PIPL, Data Security Law, Cybersecurity Law*

### Three-tier data hierarchy

Chinese enterprise AI deploys across teams, not just individuals. OpenYantra-CN adds a hierarchical ownership model:

```
User Layer    → Svarupa, Ruchi, Personal Sankalpa   (individual, private)
Team Layer    → Karma, Kartavya, Sambandha, Anishtha (role-gated)
Org Layer     → Vishwas, Niyama, Compliance          (admin-managed)
Audit Layer   → Agrasandhanī, Dinacharya             (immutable, compliance)
```

### PIPL / DSL Alignment

| Principle | OpenYantra-CN |
|---|---|
| **Consent** | Explicit consent required before writing any personal data |
| **Data localisation** | File stored on mainland China servers (Alibaba Cloud, Tencent Cloud, Huawei Cloud) |
| **Cross-border transfer** | Requires Security Assessment (PIPL Art. 38) — flagged by `Cross_Border = "Restricted"` |
| **Sensitive data** | `Data_Classification = "Confidential"` triggers approval workflow |

### Additional columns (OpenYantra-CN)

| Column | Sheet | Values |
|---|---|---|
| `Owner_Role` | All sheets | `Individual` / `Team` / `Organisation` |
| `Data_Classification` | All sheets | `Public` / `Internal` / `Confidential` |
| `Domain_Tag` | Karma, Kartavya | `E-commerce` / `Logistics` / `Finance` / `Social` |
| `Cross_Border` | All sheets | `Permitted` / `Restricted` / `Prohibited` |

---

## Security Recommendations (All Profiles)

| Risk | Mitigation |
|---|---|
| Unauthorised file access | LibreOffice password protection |
| LLM hallucination corrupting data | Chitragupta validates all writes; Agrasandhanī provides audit trail |
| Adversarial memory injection | All writes signed with Mudra — unsigned edits flagged |
| Accidental data loss | Daily backup: `chitrapat.YYYY-MM-DD.ods` auto-created |
| Multi-agent write conflict | Chitragupta single-writer pattern + Vivada escalation |
| Process crash mid-write | Sanchitta (WriteQueue) auto-replays on next init |

---

## Digital Will

Until a formal mechanism is implemented:

1. Include the Chitrapat path and decryption key in your password manager
2. Add to `⚙️ Agent Config`: `Posthumous_Access = "[name] may access after my death"`
3. Include in estate planning documentation

OpenYantra v1.1 roadmap includes a formal `digital_will.json` specification.

---

## Summary

OpenYantra is the only AI memory standard where:
- The user is the sole data controller (GDPR Article 4)
- All data lives in a file the user owns and can delete
- Every AI write is signed, timestamped, and auditable (Agrasandhanī)
- No proprietary format, no vendor lock-in, no subscription
- Four regional compliance profiles: IN · EU · US · CN

*In OpenYantra, privacy is not a feature. It is the architecture.*  
*Chitragupta serves the soul. The record belongs to the remembered.*
