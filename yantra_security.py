"""
yantra_security.py — OpenYantra Security Engine v2.4
The Raksha Layer (रक्षा — Protection)

Protects the Chitrapat from:
  1. Prompt injection — malicious payloads hijacking AI agents
  2. Mudra tampering — SHA-256 signature verification on reads
  3. Agent impersonation — trust tier enforcement
  4. Inbox poisoning — deep scan before routing
  5. VidyaKosha poisoning — anomalous embedding detection
  6. Schema corruption — structural integrity checks

Threat response (Permissive mode — user decides):
  CONFIRMED threat  → Block + Quarantine sheet + log
  SUSPICIOUS        → Warn + log + allow with flag
  CLEAN             → Pass through normally

Sanskrit naming:
  Raksha      (रक्षा)     — Protection, the security engine
  Kavach      (कवच)      — Armour, the injection scanner
  Pratishodh  (प्रतिशोध) — Scrutiny, the threat detector
  Shuddhi     (शुद्धि)   — Purification, the sanitiser
  Quarantine  sheet       — Nirodh (निरोध) — Containment
  Trust tier             — Vishwas-Shreni (विश्वास-श्रेणी)
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

# ── Threat levels ─────────────────────────────────────────────────────────────

class ThreatLevel(Enum):
    CLEAN       = "clean"
    SUSPICIOUS  = "suspicious"    # warn, allow with flag
    CONFIRMED   = "confirmed"     # block + quarantine
    CRITICAL    = "critical"      # block + quarantine + alert user


class ThreatType(Enum):
    PROMPT_INJECTION    = "prompt_injection"
    JAILBREAK           = "jailbreak"
    INSTRUCTION_OVERRIDE= "instruction_override"
    AGENT_IMPERSONATION = "agent_impersonation"
    MUDRA_TAMPER        = "mudra_tamper"
    SCHEMA_CORRUPTION   = "schema_corruption"
    VIDYAKOSHA_POISON   = "vidyakosha_poison"
    SUSPICIOUS_PATTERN  = "suspicious_pattern"
    ENCODING_ATTACK     = "encoding_attack"


# ── Trust tiers (Vishwas-Shreni) ──────────────────────────────────────────────

class TrustTier(Enum):
    """
    Agent trust hierarchy — Vishwas-Shreni
    Higher tier = more trusted = fewer restrictions
    """
    USER          = 5   # Human — Dharma-Adesh, always trusted
    CHITRAGUPTA   = 4   # LedgerAgent — system writer
    KNOWN_AGENT   = 3   # Claude, OpenClaw, registered agents
    UNKNOWN_AGENT = 2   # Unregistered agents
    EXTERNAL      = 1   # Telegram bot, email, browser extension
    UNTRUSTED     = 0   # Explicitly flagged agents


# Default known agents and their trust tiers
DEFAULT_KNOWN_AGENTS = {
    "User":           TrustTier.USER,
    "Chitragupta":    TrustTier.CHITRAGUPTA,
    "System":         TrustTier.CHITRAGUPTA,
    "Claude":         TrustTier.KNOWN_AGENT,
    "OpenClaw":       TrustTier.KNOWN_AGENT,
    "LangChain":      TrustTier.KNOWN_AGENT,
    "AutoGen":        TrustTier.KNOWN_AGENT,
    "CrewAI":         TrustTier.KNOWN_AGENT,
    "TelegramBot":    TrustTier.EXTERNAL,
    "Yantra-UI":      TrustTier.KNOWN_AGENT,
    "Digest":         TrustTier.KNOWN_AGENT,
}


# ── Threat signatures (Kavach — Armour) ───────────────────────────────────────

# Confirmed prompt injection patterns — block + quarantine
INJECTION_PATTERNS_CONFIRMED = [
    # Classic injection
    r"ignore\s+(all\s+)?(previous|prior|above|earlier)\s+(instructions?|prompts?|context)",
    r"forget\s+(everything|all|your|the)\s+(above|previous|prior)",
    r"disregard\s+(all\s+)?(previous|prior|your)\s+instructions?",
    r"you\s+are\s+now\s+(a\s+)?(?:different|new|unrestricted|free)",
    r"act\s+as\s+(if\s+you\s+(are|were)|a\s+)?(?:DAN|jailbreak|unrestricted|free\s+ai)",
    # System prompt overrides
    r"\[system\]|\[SYSTEM\]|<system>|<\|system\|>",
    r"<\|im_start\|>|<\|im_end\|>|\[INST\]|\[/INST\]",
    r"###\s*(instruction|system|prompt|override)",
    # Role injection
    r"your\s+(new\s+)?(role|purpose|function|task|goal)\s+is\s+to\s+(now\s+)?(ignore|bypass|override|hack|steal)",
    r"pretend\s+(you\s+are|to\s+be)\s+(a\s+)?(hacker|malicious|evil|unrestricted)",
    # Data extraction
    r"(print|output|show|reveal|expose|leak|dump)\s+(all\s+)?(your\s+)?(system\s+prompt|instructions?|training|memory|chitrapat|ledger)",
    r"what\s+(are\s+your|is\s+your)\s+(system\s+prompt|instructions?|hidden|secret)",
    # Privilege escalation
    r"(you\s+(now\s+)?have|grant\s+yourself)\s+(admin|root|full|unrestricted|sudo)\s+(access|privileges?|permissions?)",
    r"override\s+(the\s+)?(chitragupta|ledger|security|trust|dharma)",
]

# Suspicious patterns — warn, allow with flag
INJECTION_PATTERNS_SUSPICIOUS = [
    r"ignore\s+(this|the)\s+(rule|restriction|limit|filter)",
    r"bypass\s+(the\s+)?(filter|security|check|restriction|validation)",
    r"as\s+an?\s+(ai|language\s+model|llm)\s+(without|with\s+no)\s+(restriction|filter|limit)",
    r"developer\s+mode|jailbreak\s+mode|unrestricted\s+mode",
    r"do\s+not\s+(filter|sanitize|sanitise|check|validate)\s+this",
    r"(this\s+is\s+(a\s+)?)?(test|simulation|hypothetical|fictional)\s+(so\s+you\s+can|where\s+you\s+should)",
    r"respond\s+(only\s+)?in\s+(base64|hex|rot13|binary|encoded)",
    r"translate\s+this\s+to\s+(base64|hex|binary)\s+(and\s+execute|then\s+run)",
    # Indirect injection
    r"<script|<img\s+src|javascript:|data:text/html",
    r"eval\s*\(|exec\s*\(|__import__\s*\(",
    # CRLF injection
    r"\r\n|\n\r|%0d%0a|%0a%0d",
    # Unicode tricks
    r"[\u202e\u200f\u200b\u200c\u200d\ufeff]",  # RTL override, zero-width
]

# Jailbreak keywords — confirmed block
JAILBREAK_KEYWORDS = [
    "DAN ", "Do Anything Now", "STAN ", "DUDE ", "AIM ",
    "jailbreak", "jail break", "jailbreaking",
    "prompt injection", "prompt hacking", "prompt leaking",
    "ignore all instructions", "ignore previous instructions",
]

# Agent impersonation — confirmed block
IMPERSONATION_PATTERNS = [
    r"(i\s+am|this\s+is|speaking\s+as)\s+chitragupta",
    r"(i\s+am|acting\s+as)\s+(the\s+)?(ledger\s+agent|system\s+agent|admin\s+agent)",
    r"chitragupta\s+(says?|commands?|orders?|instructs?)",
    r"(as|i\s+am)\s+(the\s+)?(true|real|actual)\s+chitragupta",
]


# ── Scan result ───────────────────────────────────────────────────────────────

@dataclass
class ScanResult:
    """Result of a Raksha security scan."""
    threat_level:  ThreatLevel  = ThreatLevel.CLEAN
    threat_type:   Optional[ThreatType] = None
    threats_found: list[str]    = field(default_factory=list)
    sanitised_text: str         = ""
    original_text:  str         = ""
    agent_name:     str         = ""
    trust_tier:     TrustTier   = TrustTier.UNKNOWN_AGENT
    timestamp:      str         = field(
        default_factory=lambda: datetime.utcnow().isoformat(timespec="seconds"))
    scan_id:        str         = ""

    def __post_init__(self):
        if not self.scan_id:
            self.scan_id = hashlib.sha256(
                f"{self.timestamp}{self.original_text}".encode()
            ).hexdigest()[:12]

    @property
    def is_clean(self) -> bool:
        return self.threat_level == ThreatLevel.CLEAN

    @property
    def should_block(self) -> bool:
        return self.threat_level in (ThreatLevel.CONFIRMED, ThreatLevel.CRITICAL)

    @property
    def should_warn(self) -> bool:
        return self.threat_level == ThreatLevel.SUSPICIOUS

    def to_dict(self) -> dict:
        return {
            "scan_id":       self.scan_id,
            "threat_level":  self.threat_level.value,
            "threat_type":   self.threat_type.value if self.threat_type else None,
            "threats_found": self.threats_found,
            "agent":         self.agent_name,
            "trust_tier":    self.trust_tier.name,
            "timestamp":     self.timestamp,
        }


# ══════════════════════════════════════════════════════════════════════════════
# Raksha — the security engine
# ══════════════════════════════════════════════════════════════════════════════

class Raksha:
    """
    Raksha (रक्षा) — Protection
    The OpenYantra security engine.

    Protects Chitragupta and the Chitrapat from injection attacks,
    tampering, impersonation, and poisoning.

    Operates in Permissive mode:
      CONFIRMED threat → block + quarantine (user reviews in dashboard)
      SUSPICIOUS       → warn + flag + allow
      CLEAN            → pass through

    The user is always sovereign (Dharma-Adesh).
    They can review quarantined items and release them.
    """

    def __init__(self, known_agents: Optional[dict] = None,
                 sensitivity: str = "permissive"):
        self._known_agents = known_agents or DEFAULT_KNOWN_AGENTS.copy()
        self._sensitivity  = sensitivity  # permissive | balanced | strict
        self._compiled_confirmed   = [re.compile(p, re.IGNORECASE)
                                       for p in INJECTION_PATTERNS_CONFIRMED]
        self._compiled_suspicious  = [re.compile(p, re.IGNORECASE)
                                       for p in INJECTION_PATTERNS_SUSPICIOUS]
        self._compiled_impersonation = [re.compile(p, re.IGNORECASE)
                                         for p in IMPERSONATION_PATTERNS]

    # ── Public API ─────────────────────────────────────────────────────────────

    def scan_write(self, fields: dict, agent_name: str,
                   sheet: str = "") -> ScanResult:
        """
        Scan a WriteRequest's fields before Chitragupta commits.
        This is the primary injection protection point.
        """
        text = self._fields_to_text(fields)
        return self._scan(text, agent_name, context=f"write:{sheet}")

    def scan_inbox(self, content: str, agent_name: str) -> ScanResult:
        """Deep scan Inbox captures before routing to other sheets."""
        return self._scan(content, agent_name, context="inbox", deep=True)

    def scan_system_prompt(self, prompt: str) -> ScanResult:
        """
        Scan the system prompt block before injecting into an agent.
        Protects against memory-poisoned prompts.
        """
        return self._scan(prompt, "system", context="system_prompt", deep=True)

    def get_trust_tier(self, agent_name: str) -> TrustTier:
        """Return the trust tier for a given agent name."""
        return self._known_agents.get(agent_name, TrustTier.UNKNOWN_AGENT)

    def register_agent(self, agent_name: str, tier: TrustTier):
        """Register a new agent with a trust tier."""
        self._known_agents[agent_name] = tier

    def sanitise(self, text: str) -> str:
        """
        Shuddhi (शुद्धि) — Purification.
        Strip injection patterns from text, return clean version.
        """
        cleaned = text

        # Remove zero-width and RTL override characters
        cleaned = re.sub(r'[\u202e\u200f\u200b\u200c\u200d\ufeff]', '', cleaned)

        # Remove CRLF injection
        cleaned = re.sub(r'\r\n|\n\r|%0d%0a', '\n', cleaned)

        # Remove HTML/script tags
        cleaned = re.sub(r'<script[^>]*>.*?</script>', '', cleaned,
                          flags=re.IGNORECASE | re.DOTALL)
        cleaned = re.sub(r'<[^>]+>', '', cleaned)

        # Strip system prompt markers
        cleaned = re.sub(r'<\|im_start\|>|<\|im_end\|>|\[INST\]|\[/INST\]',
                          '', cleaned)
        cleaned = re.sub(r'<system>|</system>', '', cleaned, flags=re.IGNORECASE)

        # Normalise excessive whitespace
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        cleaned = cleaned.strip()

        return cleaned

    def verify_mudra(self, fields: dict, agent: str, sheet: str,
                     operation: str, stored_signature: str) -> bool:
        """
        Mudra verification — verify a write's SHA-256 signature.
        Returns True if signature matches (untampered).
        """
        if not stored_signature or not stored_signature.startswith("sha256:"):
            return False
        payload = json.dumps({
            "requesting_agent": agent,
            "sheet": sheet,
            "operation": operation,
            "fields": fields,
        }, sort_keys=True)
        expected = "sha256:" + hashlib.sha256(payload.encode()).hexdigest()[:32]
        return stored_signature == expected

    def audit_chitrapat(self, oy_path: str) -> list[dict]:
        """
        Full security audit of the Chitrapat.
        Returns list of findings — threats, tampered entries, anomalies.
        CLI: yantra security
        """
        findings = []
        try:
            import pandas as pd
            xl = pd.ExcelFile(str(oy_path), engine="odf")

            for sheet_name in xl.sheet_names:
                try:
                    df = pd.read_excel(str(oy_path), sheet_name=sheet_name,
                                       engine="odf", header=0, dtype=str)
                    for idx, row in df.iterrows():
                        row_text = " ".join(
                            str(v) for v in row.values() if v and str(v) != "nan"
                        )
                        result = self._scan(row_text, "audit",
                                            context=f"audit:{sheet_name}")
                        if not result.is_clean:
                            findings.append({
                                "sheet":         sheet_name,
                                "row":           idx,
                                "threat_level":  result.threat_level.value,
                                "threat_type":   result.threat_type.value if result.threat_type else None,
                                "threats_found": result.threats_found,
                                "preview":       row_text[:100],
                            })
                except Exception:
                    pass

            # Check Agrasandhanī for tampered signatures
            try:
                ledger_df = pd.read_excel(str(oy_path),
                                           sheet_name="📒 Agrasandhanī",
                                           engine="odf", header=0, dtype=str)
                for _, row in ledger_df.iterrows():
                    sig = str(row.get("Signature", "") or "")
                    if sig and not sig.startswith("sha256:"):
                        findings.append({
                            "sheet":        "📒 Agrasandhanī",
                            "threat_level": "confirmed",
                            "threat_type":  "mudra_tamper",
                            "threats_found":["Invalid signature format"],
                            "preview":      f"Row {row.get('Request ID','?')} — bad signature",
                        })
            except Exception:
                pass

        except Exception as e:
            findings.append({
                "sheet": "system",
                "threat_level": "suspicious",
                "threat_type": "schema_corruption",
                "threats_found": [f"Could not read Chitrapat: {e}"],
                "preview": str(oy_path),
            })

        return findings

    def scan_vidyakosha(self, vectors: list, labels: list) -> list[dict]:
        """
        VidyaKosha poisoning detection.
        Flags embeddings that are statistical outliers — potential poison vectors.
        Returns list of suspicious vector indices.
        """
        findings = []
        if not vectors:
            return findings
        try:
            import numpy as np
            vecs   = np.array(vectors)
            norms  = np.linalg.norm(vecs, axis=1)
            mean_n = float(np.mean(norms))
            std_n  = float(np.std(norms))

            for i, (norm, label) in enumerate(zip(norms, labels)):
                z_score = abs(float(norm) - mean_n) / (std_n + 1e-9)
                if z_score > 3.5:
                    findings.append({
                        "index":       i,
                        "label":       str(label)[:80],
                        "z_score":     round(float(z_score), 3),
                        "threat_type": "vidyakosha_poison",
                        "message":     f"Embedding norm {norm:.3f} is {z_score:.1f}σ "
                                        f"from mean — possible poisoned vector",
                    })
        except ImportError:
            pass  # numpy not available
        return findings

    # ── Internal ───────────────────────────────────────────────────────────────

    def _scan(self, text: str, agent_name: str,
              context: str = "", deep: bool = False) -> ScanResult:
        """Core scanning logic — Pratishodh (Scrutiny)."""

        if not text or not text.strip():
            return ScanResult(
                threat_level=ThreatLevel.CLEAN,
                original_text=text,
                sanitised_text=text,
                agent_name=agent_name,
                trust_tier=self.get_trust_tier(agent_name),
            )

        trust_tier    = self.get_trust_tier(agent_name)
        threats_found = []
        threat_level  = ThreatLevel.CLEAN
        threat_type   = None

        # Trust bypass — User tier is never blocked (Dharma-Adesh)
        if trust_tier == TrustTier.USER:
            return ScanResult(
                threat_level=ThreatLevel.CLEAN,
                original_text=text,
                sanitised_text=text,
                agent_name=agent_name,
                trust_tier=trust_tier,
            )

        # ── Check jailbreak keywords ──────────────────────────────────────────

        text_lower = text.lower()
        for kw in JAILBREAK_KEYWORDS:
            if kw.lower() in text_lower:
                threats_found.append(f"Jailbreak keyword: '{kw}'")
                threat_level = ThreatLevel.CONFIRMED
                threat_type  = ThreatType.JAILBREAK

        # ── Check agent impersonation ─────────────────────────────────────────

        for pattern in self._compiled_impersonation:
            if pattern.search(text):
                threats_found.append(
                    f"Agent impersonation: '{pattern.pattern[:50]}'")
                threat_level = ThreatLevel.CONFIRMED
                threat_type  = ThreatType.AGENT_IMPERSONATION

        # ── Check confirmed injection patterns ────────────────────────────────

        for pattern in self._compiled_confirmed:
            if pattern.search(text):
                threats_found.append(
                    f"Injection pattern: '{pattern.pattern[:60]}'")
                if threat_level != ThreatLevel.CRITICAL:
                    threat_level = ThreatLevel.CONFIRMED
                    threat_type  = ThreatType.PROMPT_INJECTION

        # ── Check suspicious patterns (only if not already confirmed) ─────────

        if threat_level == ThreatLevel.CLEAN:
            for pattern in self._compiled_suspicious:
                if pattern.search(text):
                    threats_found.append(
                        f"Suspicious pattern: '{pattern.pattern[:60]}'")
                    threat_level = ThreatLevel.SUSPICIOUS
                    threat_type  = ThreatType.SUSPICIOUS_PATTERN

        # ── Encoding attack detection ─────────────────────────────────────────

        if re.search(r'[\u202e\u200f\u200b\u200c\u200d\ufeff]', text):
            threats_found.append("Unicode attack: RTL override or zero-width chars")
            threat_level = ThreatLevel.CONFIRMED
            threat_type  = ThreatType.ENCODING_ATTACK

        # ── Trust tier amplification ──────────────────────────────────────────
        # Lower trust = lower threshold for blocking

        if trust_tier == TrustTier.EXTERNAL:
            # External sources (Telegram, email) get stricter treatment
            if threat_level == ThreatLevel.SUSPICIOUS:
                threat_level = ThreatLevel.CONFIRMED

        if trust_tier == TrustTier.UNTRUSTED:
            # Untrusted agents — any suspicion is a confirmed block
            if threat_level != ThreatLevel.CLEAN:
                threat_level = ThreatLevel.CONFIRMED

        # ── Sanitise if suspicious or higher ─────────────────────────────────

        sanitised = self.sanitise(text) if threat_level != ThreatLevel.CLEAN else text

        return ScanResult(
            threat_level   = threat_level,
            threat_type    = threat_type,
            threats_found  = threats_found,
            original_text  = text,
            sanitised_text = sanitised,
            agent_name     = agent_name,
            trust_tier     = trust_tier,
        )

    def _fields_to_text(self, fields: dict) -> str:
        """Convert WriteRequest fields to a single scannable string."""
        return " ".join(
            str(v) for v in fields.values()
            if v and str(v).strip() and str(v) != "nan"
        )


# ══════════════════════════════════════════════════════════════════════════════
# Security audit CLI
# ══════════════════════════════════════════════════════════════════════════════

def run_security_audit(oy_path: str) -> None:
    """
    yantra security — full Chitrapat security audit.
    Prints findings to terminal with severity levels.
    """
    path   = Path(oy_path).expanduser()
    raksha = Raksha()

    print(f"\n{'═'*60}")
    print(f"  🔒  OpenYantra Security Audit v2.4")
    print(f"  Chitrapat: {path}")
    print(f"  Scanned:   {datetime.utcnow().isoformat(timespec='seconds')} UTC")
    print(f"{'═'*60}")

    if not path.exists():
        print(f"\n  ✗ Chitrapat not found. Run: yantra bootstrap\n")
        return

    findings = raksha.audit_chitrapat(str(path))

    if not findings:
        print(f"\n  ✓ No threats detected — Chitrapat is clean")
        print(f"  ✓ All {_count_rows(str(path))} rows scanned")
        print(f"{'═'*60}\n")
        return

    # Group by severity
    critical   = [f for f in findings if f["threat_level"] == "critical"]
    confirmed  = [f for f in findings if f["threat_level"] == "confirmed"]
    suspicious = [f for f in findings if f["threat_level"] == "suspicious"]

    if critical:
        print(f"\n  🔴 CRITICAL ({len(critical)}):")
        for f in critical:
            print(f"     Sheet: {f['sheet']} | Row: {f['row']}")
            print(f"     Type:  {f['threat_type']}")
            print(f"     Found: {'; '.join(f['threats_found'][:2])}")
            print(f"     Data:  {f['preview'][:80]}")

    if confirmed:
        print(f"\n  🟠 CONFIRMED THREATS ({len(confirmed)}):")
        for f in confirmed:
            print(f"     Sheet: {f['sheet']} | Row: {f.get('row','?')}")
            print(f"     Type:  {f['threat_type']}")
            print(f"     Found: {'; '.join(f['threats_found'][:2])}")
            print(f"     Data:  {f['preview'][:80]}")

    if suspicious:
        print(f"\n  🟡 SUSPICIOUS ({len(suspicious)}):")
        for f in suspicious:
            print(f"     Sheet: {f['sheet']} | Row: {f.get('row','?')}")
            print(f"     Type:  {f['threat_type']}")
            print(f"     Data:  {f['preview'][:60]}")

    total = len(findings)
    print(f"\n  {'─'*58}")
    print(f"  Total findings: {total} "
          f"(critical={len(critical)}, "
          f"confirmed={len(confirmed)}, "
          f"suspicious={len(suspicious)})")
    print(f"  Review quarantined items: yantra ui → Security tab")
    print(f"{'═'*60}\n")


def _count_rows(oy_path: str) -> int:
    try:
        import pandas as pd
        xl = pd.ExcelFile(oy_path, engine="odf")
        total = 0
        for sheet in xl.sheet_names:
            try:
                df = pd.read_excel(oy_path, sheet_name=sheet,
                                   engine="odf", header=0)
                total += len(df)
            except Exception:
                pass
        return total
    except Exception:
        return 0


# ── Module-level singleton ─────────────────────────────────────────────────────

_default_raksha: Optional[Raksha] = None

def get_raksha(known_agents: Optional[dict] = None) -> Raksha:
    """Get or create the default Raksha instance."""
    global _default_raksha
    if _default_raksha is None:
        _default_raksha = Raksha(known_agents=known_agents)
    return _default_raksha
