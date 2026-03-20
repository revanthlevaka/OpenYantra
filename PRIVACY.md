# UAM Privacy & Regional Compliance Guide

> How UAM handles data privacy, compliance, and data sovereignty across regions.  
> Four official regional profiles: UAM-IN · UAM-EU · UAM-US · UAM-CN

---

## The Core Privacy Claim

In UAM, **the user is the sole data controller**. The memory file lives on the user's device or in storage they own. No third party has access. No data processing agreements required. No cloud jurisdiction risks.

This is structurally different from every other AI memory system -- Mem0, Zep, OpenAI Memory, and AWS AgentCore all store your memory on infrastructure they control. UAM puts the file in your hands.

LedgerAgent (Chitragupta) is the sole writer -- every write is signed with SHA-256 and recorded permanently in the Agrasandhanī (Ledger sheet). The record is transparent, auditable, and owned by the user.

---

## GDPR Alignment (All Profiles)

| GDPR Principle | How UAM addresses it |
|---|---|
| **Data control** | User owns the `.ods` file -- no third-party access |
| **Right of access** | Open the file in LibreOffice -- everything is visible |
| **Right to rectification** | Edit any cell directly -- respected next session |
| **Right to erasure** | Delete rows/sheets -- LedgerAgent logs the deletion |
| **Data portability** | ISO/IEC 26300 `.ods` -- export to CSV or JSON at any time |
| **Privacy by design** | Local by default, minimal by structure |
| **Transparency** | Every write signed and logged in Agrasandhanī |

---

## UAM-IN -- India Profile

*Applicable law: Digital Personal Data Protection Act 2023 (DPDP Act), IT Act 2000*

India is UAM's home country. The UAM-IN profile is the reference implementation.

### DPDP Act 2023 Alignment

| DPDP Principle | UAM-IN implementation |
|---|---|
| **Consent** | `Consent_Flag` column on Identity and Beliefs sheets -- explicit user consent before sensitive data is written |
| **Purpose limitation** | Each sheet scoped to a named purpose -- agents must not read sheets beyond current task |
| **Data minimisation** | Agents write only what the user explicitly shares (`Source = "User-stated"` preferred) |
| **Data localisation** | File stored on user device or Indian cloud providers (AWS Mumbai, Azure India, GCP Mumbai) by default |
| **Right to correction** | User edits any cell -- LedgerAgent's conflict resolution respects user-stated data above all |
| **Right to erasure** | Delete the `.ods` file or specific rows -- LedgerAgent records the erasure in Agrasandhanī |
| **Grievance redressal** | `Disputes` tab in Agrasandhanī sheet logs all conflicts for user review |

### Additional columns (UAM-IN)

| Column | Sheet | Values |
|---|---|---|
| `Consent_Flag` | Identity, Beliefs | `Explicit` / `Implied` / `Pending` |
| `Data_Fiduciary` | Agent Config | Name of the data fiduciary (agent/org name) |
| `Localisation_Tag` | All sheets | `India-only` / `Cross-border-permitted` |

### Cultural context

UAM-IN carries the Chitragupta heritage explicitly. The memory file is the **Chitrapat** (चित्रपट -- life scroll). The LedgerAgent is **Chitragupta** (चित्रगुप्त -- the hidden recorder). The Ledger sheet is the **Agrasandhanī** (अग्रसंधानी -- the cosmic register).

India has a 3,000-year tradition of the trusted record keeper -- impartial, incorruptible, serving the subject rather than the judge. UAM-IN carries that tradition into the age of AI.

### Recommended deployment

```
~/uam-in/
├── chitrapat.ods          ← the life scroll (memory file)
├── write_queue.json       ← sanchitta (accumulated pending karma)
└── archive/
    └── chitrapat_2025.ods ← archived scrolls
```

---

## UAM-EU -- Europe Profile

*Applicable law: GDPR, EU AI Act, Data Act 2023*

### GDPR

The user is the sole data controller under GDPR Article 4. No data processing agreement required. No cross-border transfer unless user explicitly moves the file. The Agrasandhanī (Ledger sheet) serves as the GDPR-compliant audit log with full write history.

### EU AI Act

The EU AI Act requires transparency and auditability. UAM's Agrasandhanī provides a complete timestamped record of every AI write, signed and immutable. This satisfies Article 13 (transparency) for general-purpose AI systems using UAM as their memory backend.

### Additional columns (UAM-EU)

| Column | Sheet | Values |
|---|---|---|
| `Data_Classification` | All sheets | `Personal` / `Sensitive` / `Professional` |
| `Retention_Policy` | All sheets | Days until archival (integer) |
| `Legal_Basis` | Identity, Beliefs | GDPR Article 6 basis: `Consent` / `Legitimate Interest` / `Contract` |

### Data sovereignty

File stays on EU-jurisdiction storage by default. Compatible with Gaia-X, EUCS-certified cloud providers, and on-premises deployment. No data leaves EU jurisdiction unless user explicitly configures cross-border sync.

---

## UAM-US -- United States Profile

*Applicable law: CCPA/CPRA (California), HIPAA (health data), COPPA (children), FTC Act, state privacy laws*

### CCPA / CPRA Alignment

| CCPA Right | UAM-US implementation |
|---|---|
| **Right to know** | Open the `.ods` file -- everything the AI knows is visible |
| **Right to delete** | Delete rows or the entire file -- fully user-controlled |
| **Right to correct** | Edit any cell -- LedgerAgent respects user edits |
| **Right to opt-out of sale** | UAM does not sell data -- file is local, not cloud |
| **Right to limit sensitive data use** | `Sensitivity_Tag` column controls which agents read which sheets |

### Sector-specific compliance

**HIPAA (health data):**
- Do not write health information to UAM without explicit user consent
- If health data is written: encrypt the `.ods` file at rest using LibreOffice password protection
- Add `PHI_Flag = "Yes"` to any row containing Protected Health Information
- Health data rows have `Retention_Policy = 2555` (7 years, HIPAA minimum)

**COPPA (children under 13):**
- UAM must not be used to store data about users under 13 without verifiable parental consent
- Add `Age_Verified = "Yes"` to Identity sheet before writing any data for a user who may be a minor

**State privacy laws:**
- Virginia (VCDPA), Colorado (CPA), Texas (TDPSA): broadly compatible with UAM's user-control model
- Illinois (BIPA): do not write biometric identifiers to UAM without consent
- New York: financial data written to UAM should be tagged `Sensitivity_Tag = "Financial"`

### Additional columns (UAM-US)

| Column | Sheet | Values |
|---|---|---|
| `Sensitivity_Tag` | All sheets | `General` / `Financial` / `Health` / `Biometric` / `Children` |
| `State_Jurisdiction` | Identity | User's state (for state-specific compliance) |
| `Opt_Out_Flag` | Agent Config | `Sale-opted-out` / `Sensitive-limited` / `None` |

### Recommended deployment

UAM-US defaults to local file storage. For enterprise deployments, use US-based cloud providers with data residency agreements (AWS us-east-1, Azure eastus, GCP us-central1). Never store UAM files on servers outside US jurisdiction without user consent.

---

## UAM-CN -- China Profile

*Applicable law: PIPL (Personal Information Protection Law), DSL (Data Security Law), Cybersecurity Law*

### Three-tier data hierarchy

Chinese enterprise AI deploys across teams and organisations, not just individuals. UAM-CN adds a three-tier ownership model:

```
User Layer    → Identity, Preferences, Personal Goals   (user-owned, private)
Team Layer    → Projects, Tasks, People, Open Loops     (role-gated, manager-readable)
Org Layer     → Beliefs, Agent Config, Compliance       (admin-managed, org-owned)
Audit Layer   → Agrasandhanī, Session Log               (immutable, compliance)
```

### PIPL / DSL Alignment

| Principle | UAM-CN implementation |
|---|---|
| **Consent** | Explicit consent required before writing any personal data |
| **Purpose limitation** | `Domain_Tag` scopes each row to a specific use context |
| **Data localisation** | File stored on mainland China servers by default (Alibaba Cloud, Tencent Cloud, Huawei Cloud) |
| **Cross-border transfer** | Requires Security Assessment (PIPL Article 38) -- flagged by `Cross_Border = "Restricted"` |
| **Sensitive personal data** | `Data_Classification = "Confidential"` triggers additional approval workflow |

### Additional columns (UAM-CN)

| Column | Sheet | Values |
|---|---|---|
| `Owner_Role` | All sheets | `Individual` / `Team` / `Organisation` |
| `Data_Classification` | All sheets | `Public` / `Internal` / `Confidential` |
| `Domain_Tag` | Projects, Tasks | Business domain (e.g. `E-commerce` / `Logistics` / `Finance`) |
| `Cross_Border` | All sheets | `Permitted` / `Restricted` / `Prohibited` |
| `Approval_Status` | Confidential rows | `Pending` / `Approved` / `Rejected` |

### Integration with Chinese enterprise platforms

UAM-CN supports integration with DingTalk, Feishu (Lark), and WeCom permission models. Team Layer sheets use role-based access aligned with these platforms' built-in group structures.

---

## Security Recommendations (All Profiles)

| Risk | Mitigation |
|---|---|
| Unauthorised file access | LibreOffice password protection (Tools → Macro → Basic) |
| LLM hallucination corrupting data | LedgerAgent validates all writes; Agrasandhanī provides audit trail |
| Adversarial memory injection | All writes signed by LedgerAgent -- unsigned edits are flagged |
| Accidental data loss | Daily backup: `chitrapat.YYYY-MM-DD.ods` auto-created each session |
| Multi-device conflict | WriteQueue and LedgerAgent conflict resolution handles this |
| Data after user death | See Digital Will section below |

---

## Digital Will

UAM files persist after the user is no longer alive. Until a formal mechanism is implemented, users are advised to:

1. Include the UAM file location and decryption key in their password manager
2. Add a `Posthumous_Access` row to `⚙️ Agent Config`:
   - `Agent = "ALL"`, `Instruction = "Posthumous access: [name] may access this file after my death"`
3. Include the file in estate planning documentation

UAM v2.12 roadmap includes a formal `digital_will.json` specification alongside `chitrapat.ods`.

---

## Summary -- UAM Is Privacy by Architecture

| Property | UAM | Cloud memory systems |
|---|---|---|
| Data controller | User | AI provider |
| Storage location | User's device | Provider's cloud |
| Audit trail | Agrasandhanī -- complete, signed | Opaque or nonexistent |
| Right to erasure | Delete the file | Submit deletion request |
| Format | ISO open standard | Proprietary |
| Jurisdiction | User's | Provider's |

*In UAM, privacy is not a feature. It is the architecture.*  
*Chitragupta serves the soul. The record belongs to the remembered.*
