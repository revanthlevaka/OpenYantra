"""
openyantra.py — OpenYantra Core Library
Version: 2.1
Project: OpenYantra — The Sacred Memory Machine
Inspired by Chitragupta (चित्रगुप्त), the Hindu God of Data

v2.1 additions over v2.0:
    - 📥 Inbox sheet         — catch-all for unclassified writes
    - Importance column       — 1-10 on every sheet
    - TTL column on Anishtha  — loop expiry in days
    - Admission rules         — filter low-value writes before commit
    - Belief diffing          — contradiction detection on Beliefs/Identity
    - memory_correction()     — agents propose edits, user approves
    - Dead man's switch       — alert if Chitragupta silent > N minutes
    - route_inbox()           — route Inbox rows to correct sheets
    - VidyaKosha incremental  — O(1) sync hook (requires vidyakosha v2.1)
    - Bootstrap interview     — terminal cold-start conversation
"""

from __future__ import annotations

import hashlib
import json
import threading
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

try:
    import pandas as pd
except ImportError:
    raise ImportError("OpenYantra requires: pip install odfpy pandas")

# VidyaKosha — graceful fallback
try:
    from vidyakosha import VidyaKosha as _VK, get_snapshot_mode as _get_snap_mode
    _VIDYAKOSHA_AVAILABLE = True
except ImportError:
    _VIDYAKOSHA_AVAILABLE = False
    _VK = None
    _get_snap_mode = None

# Raksha security engine — graceful fallback
try:
    from yantra_security import (
        Raksha, ScanResult, ThreatLevel, TrustTier,
        get_raksha, run_security_audit
    )
    _RAKSHA_AVAILABLE = True
except ImportError:
    _RAKSHA_AVAILABLE = False
    Raksha = None

# ── Controlled vocabulary ──────────────────────────────────────────────────────

PROJECT_STATUS = {"Active", "Paused", "Completed", "Cancelled"}
TASK_STATUS    = {"Pending", "In Progress", "Done", "Blocked"}
GOAL_STATUS    = {"Active", "In Progress", "Achieved", "Abandoned"}
PRIORITY       = {"Critical", "High", "Medium", "Low"}
RESOLVED       = {"Yes", "No"}
STRENGTH       = {"Strong", "Mild", "Uncertain"}
CONFIDENCE_V   = {"High", "Medium", "Low", "Inferred"}
SENTIMENT      = {"Positive", "Neutral", "Negative", "Complex"}
SOURCE         = {"User-stated", "Agent-observed", "Agent-inferred", "System"}
OPERATIONS     = {"add", "update", "resolve", "archive", "delete", "inbox"}

# ── Canonical sheet names ──────────────────────────────────────────────────────

SHEET_INDEX        = "🗂 INDEX"
SHEET_IDENTITY     = "👤 Identity"
SHEET_GOALS        = "🎯 Goals"
SHEET_PROJECTS     = "🚀 Projects"
SHEET_PEOPLE       = "👥 People"
SHEET_PREFERENCES  = "💡 Preferences"
SHEET_BELIEFS      = "🧠 Beliefs"
SHEET_TASKS        = "✅ Tasks"
SHEET_OPEN_LOOPS   = "🔓 Open Loops"
SHEET_SESSION_LOG  = "📅 Session Log"
SHEET_AGENT_CONFIG = "⚙️ Agent Config"
SHEET_LEDGER       = "📒 Agrasandhanī"
SHEET_INBOX        = "📥 Inbox"           # NEW v2.1
SHEET_CORRECTIONS  = "✏️ Corrections"     # NEW v2.1
SHEET_QUARANTINE   = "🔒 Quarantine"       # NEW v2.4 — blocked writes
SHEET_SECURITY_LOG = "🛡️ Security Log"     # NEW v2.4 — threat audit trail

ALL_SHEETS = [
    SHEET_INDEX, SHEET_IDENTITY, SHEET_GOALS, SHEET_PROJECTS,
    SHEET_PEOPLE, SHEET_PREFERENCES, SHEET_BELIEFS, SHEET_TASKS,
    SHEET_OPEN_LOOPS, SHEET_SESSION_LOG, SHEET_AGENT_CONFIG,
    SHEET_LEDGER, SHEET_INBOX, SHEET_CORRECTIONS,
]

TODAY = date.today().isoformat()

# ── Admission rules ────────────────────────────────────────────────────────────

NOISE_PATTERNS = [
    "user said thanks", "user greeted", "user said hello",
    "user said goodbye", "user said ok", "acknowledged",
    "noted", "understood", "sure", "great", "awesome",
]

def _is_worth_remembering(fields: dict, sheet: str) -> tuple[bool, str]:
    """
    Admission gate — filter low-value writes before Chitragupta commits.
    Returns (admit: bool, reason: str)
    """
    # Session log and ledger always admitted
    if sheet in (SHEET_SESSION_LOG, SHEET_LEDGER, SHEET_INBOX):
        return True, "always admit"

    # Check for noise patterns
    text = " ".join(str(v).lower() for v in fields.values() if v)
    for pattern in NOISE_PATTERNS:
        if pattern in text:
            return False, f"noise pattern: '{pattern}'"

    # Require minimum content
    meaningful = [v for v in fields.values()
                  if v and str(v).strip() and len(str(v)) > 3]
    if len(meaningful) < 1:
        return False, "insufficient content"

    # Check importance if provided
    importance = fields.get("Importance", 5)
    try:
        if int(importance) < 2:
            return False, f"importance too low: {importance}"
    except (ValueError, TypeError):
        pass

    return True, "admitted"


# ══════════════════════════════════════════════════════════════════════════════
# WriteRequest (Karma-Lekha)
# ══════════════════════════════════════════════════════════════════════════════

class WriteRequest:
    """Karma-Lekha — a deed submitted to Chitragupta for recording."""

    def __init__(self, requesting_agent: str, sheet: str, operation: str,
                 fields: dict, row_identifier: Optional[str] = None,
                 confidence: str = "High", source: str = "Agent-observed",
                 session_id: Optional[str] = None, importance: int = 5):
        assert operation  in OPERATIONS,   f"operation must be one of {OPERATIONS}"
        assert confidence in CONFIDENCE_V, f"confidence must be one of {CONFIDENCE_V}"
        assert source     in SOURCE,       f"source must be one of {SOURCE}"
        assert 1 <= importance <= 10,      f"importance must be 1-10"

        self.requesting_agent = requesting_agent
        self.sheet            = sheet
        self.operation        = operation
        self.fields           = {**fields, "Importance": str(importance)}
        self.row_identifier   = row_identifier
        self.confidence       = confidence
        self.source           = source
        self.session_id       = session_id or TODAY
        self.importance       = importance
        self.timestamp        = datetime.utcnow().isoformat()
        self.request_id       = self._make_id()

    def _make_id(self) -> str:
        payload = f"{self.requesting_agent}{self.sheet}{self.timestamp}"
        return hashlib.sha256(payload.encode()).hexdigest()[:16]

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id, "requesting_agent": self.requesting_agent,
            "sheet": self.sheet, "operation": self.operation,
            "row_identifier": self.row_identifier, "fields": self.fields,
            "confidence": self.confidence, "source": self.source,
            "importance": self.importance, "session_id": self.session_id,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "WriteRequest":
        req = cls(
            requesting_agent = d["requesting_agent"], sheet = d["sheet"],
            operation = d["operation"], fields = d["fields"],
            row_identifier = d.get("row_identifier"),
            confidence = d.get("confidence", "High"),
            source = d.get("source", "Agent-observed"),
            session_id = d.get("session_id"),
            importance = d.get("importance", 5),
        )
        req.request_id = d.get("request_id", req.request_id)
        req.timestamp  = d.get("timestamp", req.timestamp)
        return req


# ══════════════════════════════════════════════════════════════════════════════
# WriteQueue (Sanchitta)
# ══════════════════════════════════════════════════════════════════════════════

class WriteQueue:
    """Sanchitta — accumulated karma awaiting reckoning. Crash-safe."""

    def __init__(self, queue_path: Path):
        self.path  = queue_path
        self._lock = threading.Lock()
        if not self.path.exists():
            self._save([])

    def _load(self) -> list[dict]:
        try: return json.loads(self.path.read_text())
        except Exception: return []

    def _save(self, items: list[dict]):
        self.path.write_text(json.dumps(items, indent=2))

    def enqueue(self, req: WriteRequest):
        with self._lock:
            items = self._load(); items.append(req.to_dict()); self._save(items)

    def dequeue_all(self) -> list[WriteRequest]:
        with self._lock:
            items = self._load(); self._save([])
            return [WriteRequest.from_dict(d) for d in items]

    def peek(self) -> list[dict]: return self._load()
    def is_empty(self) -> bool: return len(self._load()) == 0


# ══════════════════════════════════════════════════════════════════════════════
# LedgerAgent (Chitragupta) — sole writer
# ══════════════════════════════════════════════════════════════════════════════

class LedgerAgent:
    """
    Chitragupta — the divine scribe. Sole writer to the Chitrapat.
    v2.1: admission rules, dead man's switch, belief diffing support.
    """

    def __init__(self, memory_path: Path, queue: WriteQueue,
                 dead_switch_minutes: int = 30):
        self.path              = memory_path
        self.queue             = queue
        self._lock             = threading.Lock()
        self._last_write_time  = time.time()
        self._dead_switch_mins = dead_switch_minutes

    def submit(self, req: WriteRequest) -> dict:
        """Submit a Karma-Lekha. Enqueue first for crash safety."""
        self.queue.enqueue(req)
        return self._process(req)

    def replay_queue(self) -> int:
        pending = self.queue.dequeue_all()
        for req in pending: self._process(req)
        return len(pending)

    def is_alive(self) -> bool:
        elapsed = (time.time() - self._last_write_time) / 60
        return elapsed < self._dead_switch_mins

    def _process(self, req: WriteRequest) -> dict:
        with self._lock:
            # Admission gate (v2.1)
            if req.sheet not in (SHEET_SESSION_LOG, SHEET_LEDGER,
                                  SHEET_INBOX, SHEET_CORRECTIONS):
                admit, reason = _is_worth_remembering(req.fields, req.sheet)
                if not admit:
                    return {"status": "filtered", "request_id": req.request_id,
                            "reason": reason}

            validation = self._validate(req)
            if validation["status"] == "rejected":
                self._log_audit(req, "rejected", validation["reason"])
                return validation

            conflict = self._check_conflict(req)
            if conflict:
                self._log_audit(req, "conflict", str(conflict))
                return {
                    "status": "conflict", "request_id": req.request_id,
                    "existing_value": conflict.get("existing"),
                    "requested_value": conflict.get("requested"),
                    "resolution": "pending_user",
                    "message": "Vivada — Dharma-Adesh required",
                }

            mudra = self._seal(req)
            self._commit(req, mudra)
            self._log_audit(req, "written", signature=mudra)
            self._last_write_time = time.time()

            return {
                "status": "written", "request_id": req.request_id,
                "sheet": req.sheet, "operation": req.operation,
                "timestamp": req.timestamp, "signature": mudra,
            }

    def _validate(self, req: WriteRequest) -> dict:
        if req.sheet not in ALL_SHEETS:
            return {"status": "rejected", "reason": f"Unknown sheet: {req.sheet}"}
        if req.sheet == SHEET_LEDGER:
            return {"status": "rejected", "reason": "Agrasandhanī is system-managed"}
        vocab = {
            "Status":     PROJECT_STATUS | TASK_STATUS | GOAL_STATUS,
            "Priority":   PRIORITY, "Resolved?": RESOLVED,
            "Strength":   STRENGTH, "Confidence": CONFIDENCE_V,
            "Sentiment":  SENTIMENT,
        }
        for field, allowed in vocab.items():
            if field in req.fields and req.fields[field] not in allowed:
                return {"status": "rejected",
                        "reason": f"Invalid {field}: '{req.fields[field]}'"}
        return {"status": "valid"}

    def _check_conflict(self, req: WriteRequest) -> Optional[dict]:
        if req.operation != "update" or not req.row_identifier:
            return None
        try:
            df = pd.read_excel(str(self.path), sheet_name=req.sheet,
                               engine="odf", header=0, dtype=str)
            if df.empty: return None
            match = df[df.iloc[:, 0].astype(str) == req.row_identifier]
            if match.empty: return None
            row = match.iloc[0]
            for field, new_val in req.fields.items():
                if field in row.index:
                    if (str(row[field]) != str(new_val) and
                            row.get("Confidence", "Low") == "High" and
                            req.confidence != "High"):
                        return {"field": field, "existing": str(row[field]),
                                "requested": str(new_val)}
        except Exception: pass
        return None

    def _seal(self, req: WriteRequest) -> str:
        payload = json.dumps(req.to_dict(), sort_keys=True)
        return "sha256:" + hashlib.sha256(payload.encode()).hexdigest()[:32]

    def _commit(self, req: WriteRequest, mudra: str):
        try:
            try:
                df = pd.read_excel(str(self.path), sheet_name=req.sheet,
                                   engine="odf", header=0, dtype=str)
            except Exception:
                df = pd.DataFrame()

            now = datetime.utcnow().isoformat(timespec="seconds")

            if req.operation in ("add", "inbox"):
                new_row = {**req.fields, "Confidence": req.confidence,
                           "Source": req.source, "Added By": req.requesting_agent,
                           "Last Updated": now}
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

            elif req.operation == "update" and req.row_identifier:
                mask = (df.iloc[:, 0].astype(str) == req.row_identifier
                        if not df.empty and len(df.columns) > 0
                        else pd.Series([], dtype=bool))
                if mask.any():
                    for f, v in req.fields.items():
                        if f in df.columns: df.loc[mask, f] = v
                    if "Last Updated" in df.columns:
                        df.loc[mask, "Last Updated"] = now
                    if "Confidence" in df.columns:
                        df.loc[mask, "Confidence"] = req.confidence
                else:
                    new_row = {**req.fields, "Confidence": req.confidence,
                               "Source": req.source, "Last Updated": now}
                    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

            elif req.operation == "resolve" and req.row_identifier:
                mask = (df.iloc[:, 0].astype(str) == req.row_identifier
                        if not df.empty and len(df.columns) > 0
                        else pd.Series([], dtype=bool))
                if "Resolved?" in df.columns: df.loc[mask, "Resolved?"] = "Yes"
                if "Resolution" in df.columns:
                    df.loc[mask, "Resolution"] = req.fields.get("Resolution", "")
                if "Last Updated" in df.columns:
                    df.loc[mask, "Last Updated"] = now

            elif req.operation == "archive" and req.row_identifier:
                mask = (df.iloc[:, 0].astype(str) == req.row_identifier
                        if not df.empty and len(df.columns) > 0
                        else pd.Series([], dtype=bool))
                if "Status" in df.columns: df.loc[mask, "Status"] = "Archived"
                if "Last Updated" in df.columns:
                    df.loc[mask, "Last Updated"] = now

            self._write_sheet(req.sheet, df)
        except Exception as e:
            raise RuntimeError(f"Chitragupta commit failed: {e}") from e

    def _write_sheet(self, sheet_name: str, df: pd.DataFrame):
        existing = {}
        try:
            xl = pd.ExcelFile(str(self.path), engine="odf")
            for name in xl.sheet_names:
                if name != sheet_name:
                    try:
                        existing[name] = pd.read_excel(
                            str(self.path), sheet_name=name,
                            engine="odf", header=None)
                    except Exception:
                        existing[name] = pd.DataFrame()
        except Exception: pass

        with pd.ExcelWriter(str(self.path), engine="odf") as writer:
            for name, sdf in existing.items():
                sdf.to_excel(writer, sheet_name=name, index=False, header=False)
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    def _log_audit(self, req: WriteRequest, status: str,
                   reason: str = "", signature: str = ""):
        entry = {
            "Timestamp": req.timestamp, "Request ID": req.request_id,
            "Agent": req.requesting_agent, "Sheet": req.sheet,
            "Operation": req.operation, "Row Identifier": req.row_identifier or "",
            "Status": status, "Confidence": req.confidence,
            "Source": req.source, "Importance": req.importance,
            "Signature": signature, "Reason / Notes": reason,
        }
        try:
            try:
                ledger_df = pd.read_excel(str(self.path),
                                          sheet_name=SHEET_LEDGER,
                                          engine="odf", header=0, dtype=str)
            except Exception:
                ledger_df = pd.DataFrame(columns=list(entry.keys()))
            ledger_df = pd.concat([ledger_df, pd.DataFrame([entry])],
                                   ignore_index=True)
            self._write_sheet(SHEET_LEDGER, ledger_df)
        except Exception: pass


# ══════════════════════════════════════════════════════════════════════════════
# OpenYantra — public API v2.1
# ══════════════════════════════════════════════════════════════════════════════

class OpenYantra:
    """
    OpenYantra v2.1 — The Sacred Memory Machine

    New in v2.1:
        oy.inbox(text)           — quick capture to Inbox sheet
        oy.route_inbox()         — route Inbox rows to correct sheets
        oy.propose_correction()  — agent proposes edit for user approval
        oy.apply_corrections()   — apply approved corrections
        oy.diff_beliefs()        — detect belief contradictions
        oy.check_anishtha_ttl()  — expire old open loops
        oy.health_check()        — system status + stats
    """

    VERSION = "2.8"

    def __init__(self, path: str | Path, agent_name: str = "Agent",
                 dead_switch_minutes: int = 30):
        self.path       = Path(path).expanduser()
        self.agent_name = agent_name
        self._queue     = WriteQueue(self.path.parent / "sanchitta.json")
        self._ledger    = LedgerAgent(self.path, self._queue,
                                      dead_switch_minutes)
        replayed = self._ledger.replay_queue()
        if replayed:
            print(f"[OpenYantra] Replayed {replayed} Karma-Lekha from Sanchitta.")

        self._vidyakosha = None
        if _VIDYAKOSHA_AVAILABLE and self.path.exists():
            try:
                self._vidyakosha = _VK(str(self.path.parent), embedder_pref="auto")
            except Exception: pass

        # Raksha — security engine (v2.4)
        self._raksha = get_raksha() if _RAKSHA_AVAILABLE else None

    # ── Bootstrap ──────────────────────────────────────────────────────────────

    def bootstrap(self, user_name: str = "", occupation: str = "",
                  location: str = ""):
        if self.path.exists():
            print(f"[OpenYantra] Chitrapat already exists at {self.path}.")
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        _build_ods_template(str(self.path))
        for attr, val in {"Preferred Name": user_name, "Occupation": occupation,
                          "Location": location}.items():
            if val:
                self.request_write(WriteRequest(
                    "System", SHEET_IDENTITY, "update", {"Value": val},
                    row_identifier=attr, confidence="High",
                    source="User-stated", importance=9))
        self.log_session(["Chitragupta Puja — bootstrap"],
                         [f"Chitrapat created — OpenYantra v{self.VERSION}"],
                         [f"Identity: {user_name}" if user_name else "Identity stub"])
        print(f"[OpenYantra] Chitrapat created at {self.path}")
        print("[OpenYantra] Run `yantra ui` to open the browser dashboard.")

    # ── Write interface ────────────────────────────────────────────────────────

    def request_write(self, req: WriteRequest) -> dict:
        """
        All writes go through Chitragupta.
        v2.4: Raksha security scan before submission.
        VidyaKosha syncs after commit.
        """
        # Raksha scan — check for injection before commit
        if self._raksha is not None:
            scan = self._raksha.scan_write(
                req.fields, req.requesting_agent, req.sheet)
            if scan.should_block:
                self._quarantine(req, scan)
                return {
                    "status":       "quarantined",
                    "request_id":   req.request_id,
                    "threat_level": scan.threat_level.value,
                    "threat_type":  scan.threat_type.value if scan.threat_type else None,
                    "threats":      scan.threats_found,
                    "message":      "Write blocked by Raksha. Review in Security tab.",
                }
            elif scan.should_warn:
                self._log_security(req, scan)
                # Allow but flag — add security note to fields
                req.fields["_security_flag"] = (
                    f"SUSPICIOUS: {'; '.join(scan.threats_found[:2])}")

        receipt = self._ledger.submit(req)
        if receipt.get("status") == "written" and self._vidyakosha is not None:
            try:
                # v2.7: O(1) incremental update — only changed row synced
                row_text = " ".join(
                    f"{k}: {v}" for k, v in req.fields.items() if v)
                if hasattr(self._vidyakosha, "incremental_update"):
                    self._vidyakosha.incremental_update(
                        req.request_id, row_text, req.sheet)
                else:
                    self._vidyakosha.sync(self.path)
            except Exception: pass
        return receipt

    # ── v2.1 new methods ───────────────────────────────────────────────────────

    def inbox(self, text: str, source: str = "User-stated",
              importance: int = 5) -> dict:
        """
        📥 Quick capture — dump anything to Inbox without categorisation.
        Chitragupta routes to correct sheet later via route_inbox().

        Usage:
            oy.inbox("Priya mentioned the budget needs revision by Friday")
            oy.inbox("I want to learn Rust in 2026")
        """
        return self.request_write(WriteRequest(
            requesting_agent = self.agent_name,
            sheet            = SHEET_INBOX,
            operation        = "inbox",
            fields           = {
                "Content":    text,
                "Captured":   datetime.utcnow().isoformat(timespec="seconds"),
                "Routed?":    "No",
                "Target Sheet": "",
                "Notes":      "",
            },
            confidence = "High", source = source, importance = importance,
        ))

    def route_inbox(self, dry_run: bool = False) -> list[dict]:
        """
        Route unprocessed Inbox rows to their correct sheets.
        Uses simple heuristics — override with custom router if needed.

        Returns list of routing decisions.
        """
        routing_log = []
        inbox_rows  = self._read_sheet(SHEET_INBOX)
        unrouted    = [r for r in inbox_rows if r.get("Routed?") == "No"]

        for row in unrouted:
            content  = str(row.get("Content", "")).lower()
            target   = _infer_sheet(content)
            decision = {"content": row.get("Content"), "target": target}

            if not dry_run and target:
                self.request_write(WriteRequest(
                    requesting_agent = "Chitragupta",
                    sheet            = target,
                    operation        = "add",
                    fields           = {"Notes": row.get("Content", ""),
                                        "Source": "Routed from Inbox"},
                    confidence       = "Low",
                    source           = "Agent-inferred",
                    importance       = max(1, min(10, int(row.get("Importance", 5) or 5))),
                ))
                # Mark as routed
                self.request_write(WriteRequest(
                    "Chitragupta", SHEET_INBOX, "update",
                    {"Routed?": "Yes", "Target Sheet": target or "Unknown"},
                    row_identifier = str(row.get("Content", ""))[:50],
                    confidence = "High", source = "System", importance = 5,
                ))
                decision["routed"] = True
            routing_log.append(decision)
        return routing_log

    def propose_correction(self, sheet: str, row_identifier: str,
                           field: str, new_value: str,
                           reason: str = "") -> dict:
        """
        Any agent proposes a correction — goes to Corrections sheet for approval.
        User reviews via `yantra ui` and approves/rejects.
        """
        return self.request_write(WriteRequest(
            requesting_agent = self.agent_name,
            sheet            = SHEET_CORRECTIONS,
            operation        = "add",
            fields           = {
                "Target Sheet":    sheet,
                "Row Identifier":  row_identifier,
                "Field":           field,
                "Proposed Value":  new_value,
                "Reason":          reason,
                "Status":          "Pending",
                "Proposed By":     self.agent_name,
                "Proposed At":     datetime.utcnow().isoformat(timespec="seconds"),
            },
            confidence = "Medium", source = "Agent-inferred", importance = 6,
        ))

    def apply_corrections(self, approved_only: bool = True) -> int:
        """Apply approved corrections from the Corrections sheet."""
        corrections = self._read_sheet(SHEET_CORRECTIONS)
        applied = 0
        for c in corrections:
            if approved_only and c.get("Status") != "Approved":
                continue
            self.request_write(WriteRequest(
                requesting_agent = "Chitragupta",
                sheet            = c.get("Target Sheet", ""),
                operation        = "update",
                fields           = {c.get("Field", ""): c.get("Proposed Value", "")},
                row_identifier   = c.get("Row Identifier", ""),
                confidence       = "High", source = "User-stated", importance = 8,
            ))
            applied += 1
        return applied

    def diff_beliefs(self) -> list[dict]:
        """
        Belief diffing — detect potential contradictions in Beliefs + Identity.
        Returns list of flagged pairs for user review.
        Called monthly or at session start.
        """
        contradictions = []
        beliefs = self._read_sheet(SHEET_BELIEFS)
        identity = self._read_sheet(SHEET_IDENTITY)

        # Simple contradiction detection: same topic, different positions
        by_topic: dict[str, list] = {}
        for row in beliefs:
            topic = str(row.get("Topic", "")).lower().strip()
            if topic:
                by_topic.setdefault(topic, []).append(row)

        for topic, rows in by_topic.items():
            if len(rows) > 1:
                positions = [r.get("Position", "") for r in rows]
                dates     = [r.get("Last Updated", "") for r in rows]
                contradictions.append({
                    "type":      "belief_evolution",
                    "topic":     topic,
                    "positions": positions,
                    "dates":     dates,
                    "message":   f"Topic '{topic}' has {len(rows)} different positions. "
                                 f"Review and consolidate?",
                })

        return contradictions

    def check_anishtha_ttl(self, default_ttl_days: int = 90) -> list[dict]:
        """
        Check Open Loops for expired TTL.
        Returns list of loops to archive or action.
        """
        expired = []
        loops   = self._read_sheet(SHEET_OPEN_LOOPS)
        cutoff  = datetime.utcnow() - timedelta(days=default_ttl_days)

        for loop in loops:
            if loop.get("Resolved?") == "Yes":
                continue
            ttl_days = loop.get("TTL_Days", default_ttl_days)
            opened   = loop.get("Opened", "")
            try:
                ttl    = int(ttl_days or default_ttl_days)
                opened_dt = datetime.fromisoformat(str(opened)[:10])
                age_days  = (datetime.utcnow() - opened_dt).days
                if age_days > ttl:
                    expired.append({
                        "topic":     loop.get("Topic", ""),
                        "age_days":  age_days,
                        "ttl_days":  ttl,
                        "message":   f"Open loop '{loop.get('Topic', '')}' is "
                                     f"{age_days} days old (TTL: {ttl}). "
                                     f"Resolve, delegate, or archive?",
                    })
            except Exception:
                pass
        return expired

    def health_check(self) -> dict:
        """System status and memory stats."""
        try:
            sheets_data = {}
            for sheet in [SHEET_PROJECTS, SHEET_TASKS, SHEET_OPEN_LOOPS,
                          SHEET_SESSION_LOG, SHEET_INBOX, SHEET_CORRECTIONS]:
                rows = self._read_sheet(sheet)
                sheets_data[sheet] = len(rows)

            open_loops    = sheets_data.get(SHEET_OPEN_LOOPS, 0)
            inbox_pending = len([r for r in self._read_sheet(SHEET_INBOX)
                                 if r.get("Routed?") == "No"])
            corrections   = len([r for r in self._read_sheet(SHEET_CORRECTIONS)
                                  if r.get("Status") == "Pending"])
            stale_projects = len([r for r in self._read_sheet(SHEET_PROJECTS)
                                   if r.get("Status") == "Active" and
                                   r.get("Last Updated", "") < (
                                       datetime.utcnow() - timedelta(days=30)
                                   ).isoformat()[:10]])

            file_size_kb = (self.path.stat().st_size // 1024
                            if self.path.exists() else 0)

            return {
                "status":           "healthy" if self._ledger.is_alive() else "warning",
                "version":          self.VERSION,
                "chitrapat_size_kb": file_size_kb,
                "open_loops":       open_loops,
                "inbox_pending":    inbox_pending,
                "corrections_pending": corrections,
                "stale_projects":   stale_projects,
                "chitragupta_alive": self._ledger.is_alive(),
                "vidyakosha":       "available" if _VIDYAKOSHA_AVAILABLE else "not installed",
                "rows":             sheets_data,
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    # ── Convenience write helpers ──────────────────────────────────────────────

    def flush_open_loop(self, topic: str, context: str,
                        priority: str = "Medium", related_project: str = "",
                        ttl_days: int = 90, importance: int = 7) -> dict:
        return self.request_write(WriteRequest(
            self.agent_name, SHEET_OPEN_LOOPS, "add",
            {"Topic": topic, "Context / What's Unresolved": context,
             "Opened": TODAY, "Priority": priority,
             "Related Project": related_project,
             "Resolved?": "No", "Resolution": "", "TTL_Days": str(ttl_days)},
            confidence="High", source="Agent-observed", importance=importance,
        ))

    def resolve_open_loop(self, topic: str, resolution: str = "") -> dict:
        return self.request_write(WriteRequest(
            self.agent_name, SHEET_OPEN_LOOPS, "resolve",
            {"Resolution": resolution}, row_identifier=topic,
            confidence="High", source="Agent-observed", importance=7,
        ))

    def log_session(self, topics: list[str], decisions: list[str] = None,
                    new_memory: list[str] = None,
                    open_loops_created: int = 0, notes: str = "") -> dict:
        return self.request_write(WriteRequest(
            self.agent_name, SHEET_SESSION_LOG, "add",
            {"Date": TODAY, "Topics Discussed": "; ".join(topics),
             "Decisions Made": "; ".join(decisions or []),
             "New Memory Added": "; ".join(new_memory or []),
             "Open Loops Created": str(open_loops_created),
             "Agent": self.agent_name, "Notes": notes},
            confidence="High", source="System", importance=5,
        ))

    def add_project(self, project: str, domain: str = "", status: str = "Active",
                    priority: str = "High", key_decision: str = "",
                    next_step: str = "", notes: str = "",
                    importance: int = 7) -> dict:
        return self.request_write(WriteRequest(
            self.agent_name, SHEET_PROJECTS, "add",
            {"Project": project, "Domain": domain, "Status": status,
             "Priority": priority, "Key Decision Made": key_decision,
             "Next Step": next_step, "Notes": notes},
            confidence="High", source="User-stated", importance=importance,
        ))

    def add_task(self, task: str, project: str = "", priority: str = "Medium",
                 deadline: str = "", status: str = "Pending",
                 notes: str = "", importance: int = 6) -> dict:
        return self.request_write(WriteRequest(
            self.agent_name, SHEET_TASKS, "add",
            {"Task": task, "Project": project, "Priority": priority,
             "Deadline": deadline, "Status": status, "Notes": notes},
            confidence="High", source="User-stated", importance=importance,
        ))

    def add_person(self, name: str, relationship: str = "", context: str = "",
                   sentiment: str = "Neutral", notes: str = "",
                   importance: int = 6) -> dict:
        return self.request_write(WriteRequest(
            self.agent_name, SHEET_PEOPLE, "add",
            {"Name": name, "Relationship": relationship, "Context": context,
             "Sentiment": sentiment, "Last Mentioned": TODAY, "Notes": notes},
            confidence="Medium", source="Agent-observed", importance=importance,
        ))

    def update_identity(self, attribute: str, value: str,
                        importance: int = 8) -> dict:
        return self.request_write(WriteRequest(
            self.agent_name, SHEET_IDENTITY, "update", {"Value": value},
            row_identifier=attribute, confidence="High",
            source="User-stated", importance=importance,
        ))

    # ── Read interface (Smarana) ───────────────────────────────────────────────

    def _read_sheet(self, sheet_name: str) -> list[dict]:
        try:
            df = pd.read_excel(str(self.path), sheet_name=sheet_name,
                               engine="odf", header=0, dtype=str)
            return df.where(pd.notna(df), None).to_dict("records")
        except Exception: return []

    def load_session_context(self, agent_name: Optional[str] = None) -> dict:
        agent = agent_name or self.agent_name
        id_map = {r.get("Attribute"): r.get("Value")
                  for r in self._read_sheet(SHEET_IDENTITY) if r.get("Value")}
        instructions = [
            r.get("Instruction") for r in self._read_sheet(SHEET_AGENT_CONFIG)
            if r.get("Active") == "Yes"
            and r.get("Agent") in (agent, "ALL") and r.get("Instruction")
        ]
        projects   = [r for r in self._read_sheet(SHEET_PROJECTS)
                      if r.get("Status") == "Active"]

        # v2.1: filter open loops by importance + recency
        all_loops  = [r for r in self._read_sheet(SHEET_OPEN_LOOPS)
                      if r.get("Resolved?") == "No"]
        open_loops = sorted(
            all_loops,
            key=lambda r: (
                -(int(r.get("Importance", 5) or 5)),
                str(r.get("Opened", ""))
            )
        )[:15]  # max 15 loops in context to prevent bloat

        goals  = [r for r in self._read_sheet(SHEET_GOALS)
                  if r.get("Status") in ("Active", "In Progress")]
        tasks  = [r for r in self._read_sheet(SHEET_TASKS)
                  if r.get("Status") not in ("Done", None)]

        # v2.1: surface pending corrections and inbox
        corrections = [r for r in self._read_sheet(SHEET_CORRECTIONS)
                       if r.get("Status") == "Pending"]
        inbox_count = len([r for r in self._read_sheet(SHEET_INBOX)
                           if r.get("Routed?") == "No"])

        return {
            "identity": id_map, "agent_instructions": instructions,
            "active_projects": projects, "open_loops": open_loops,
            "active_goals": goals, "pending_tasks": tasks,
            "pending_corrections": corrections, "inbox_pending": inbox_count,
        }

    def build_system_prompt_block(self,
                                  agent_name: Optional[str] = None) -> str:
        ctx    = self.load_session_context(agent_name)
        id_map = ctx["identity"]

        user_line = " | ".join(filter(None, [
            id_map.get("Preferred Name") or id_map.get("Full Name"),
            id_map.get("Occupation"), id_map.get("Location"),
        ])) or "Unknown user"

        projects_line = "; ".join(
            f"{p.get('Project','?')} → {p.get('Next Step','?')}"
            for p in ctx["active_projects"]) or "None"

        loops_line = "; ".join(
            "[{}] {} — {}".format(
                l.get("Priority","?"), l.get("Topic","?"),
                l.get("Context / What's Unresolved",""))
            for l in ctx["open_loops"]) or "None"

        goals_line = "; ".join(
            g.get("Goal","") for g in ctx["active_goals"]) or "None"

        tasks_line = "; ".join(
            t.get("Task","") for t in ctx["pending_tasks"]) or "None"

        instructions_line = "\n  ".join(
            str(i) for i in ctx["agent_instructions"]) or "None"

        alerts = []
        if ctx["inbox_pending"] > 0:
            alerts.append(f"📥 {ctx['inbox_pending']} unrouted Inbox items")
        if ctx["pending_corrections"]:
            alerts.append(f"✏️ {len(ctx['pending_corrections'])} corrections pending approval")
        alerts_line = " · ".join(alerts) if alerts else "None"

        return (
            f"[OPENYANTRA CONTEXT — v{self.VERSION} | Chitragupta-secured]\n"
            f"User: {user_line}\n"
            f"Active Projects (Karma): {projects_line}\n"
            f"Open Loops (Anishtha, top 15): {loops_line}\n"
            f"Goals (Sankalpa): {goals_line}\n"
            f"Tasks (Kartavya): {tasks_line}\n"
            f"Alerts: {alerts_line}\n"
            f"Agent Instructions (Niyama):\n  {instructions_line}\n"
            f"[/OPENYANTRA CONTEXT]"
        )

    def get_person(self, name: str) -> Optional[dict]:
        for r in self._read_sheet(SHEET_PEOPLE):
            if str(r.get("Name","")).lower() == name.lower(): return r
        return None

    # ── VidyaKosha search ──────────────────────────────────────────────────────

    def search(self, query: str, top_k: int = 5, sheets: list = None,
               snapshot_mode: str = None, hybrid_alpha: float = 0.7,
               importance_weight: float = 0.3) -> list[dict]:
        """
        VidyaKosha semantic search — v2.7: importance-weighted results.

        Final score = relevance_score × (1 + importance_weight × normalised_importance)
        High-importance memories surface first when relevance is equal.
        importance_weight=0.0 disables weighting (pure relevance).
        """
        if not _VIDYAKOSHA_AVAILABLE:
            print("[OpenYantra] VidyaKosha not available.")
            return []
        if self._vidyakosha is None:
            self._vidyakosha = _VK(str(self.path.parent), embedder_pref="auto")
            self._vidyakosha.sync(self.path)
        if snapshot_mode is None and _get_snap_mode:
            snapshot_mode = _get_snap_mode(self.agent_name, self.path)

        results = self._vidyakosha.query(
            text=query, agent_name=self.agent_name, top_k=top_k * 3,
            sheets=sheets, snapshot_mode=snapshot_mode or "live",
            hybrid_alpha=hybrid_alpha)

        # v2.7 — re-rank by importance × relevance × recency
        if importance_weight > 0 and results:
            from datetime import datetime as _dt
            now = _dt.utcnow()
            for r in results:
                raw_imp = r.get("importance") or r.get("Importance") or 5
                try:
                    imp = min(10, max(1, int(raw_imp))) / 10.0  # normalise 0-1
                except (ValueError, TypeError):
                    imp = 0.5

                # Recency decay — older entries score lower
                last_updated = str(r.get("last_updated") or r.get("Last Updated") or "")[:10]
                try:
                    age_days = (now - _dt.fromisoformat(last_updated)).days
                    recency = max(0.1, 1.0 - (age_days / 365))
                except Exception:
                    recency = 0.5

                base = float(r.get("score", 0.5))
                r["score"] = base * (1 + importance_weight * imp) * (1 + 0.1 * recency)

            results.sort(key=lambda r: -r.get("score", 0))

        return results[:top_k]

    def search_open_loops(self, query: str, top_k: int = 5) -> list[dict]:
        return self.search(query, top_k=top_k, sheets=[SHEET_OPEN_LOOPS])

    def search_projects(self, query: str, top_k: int = 5) -> list[dict]:
        return self.search(query, top_k=top_k, sheets=[SHEET_PROJECTS])

    def search_people(self, query: str, top_k: int = 5) -> list[dict]:
        return self.search(query, top_k=top_k, sheets=[SHEET_PEOPLE])

    def take_pratibimba(self):
        if self._vidyakosha: self._vidyakosha.take_snapshot(self.agent_name)

    def release_pratibimba(self):
        if self._vidyakosha: self._vidyakosha.release_snapshot(self.agent_name)

    # ── Security (Raksha) v2.4 ────────────────────────────────────────────────

    def security_scan(self, text: str = None) -> dict:
        """Run security audit on Chitrapat or specific text. CLI: yantra security"""
        if not _RAKSHA_AVAILABLE:
            return {"status": "Raksha not available"}
        if text:
            scan = self._raksha.scan_write({"text": text}, self.agent_name, "manual")
            return scan.to_dict()
        else:
            findings = self._raksha.audit_chitrapat(str(self.path))
            return {
                "total_findings": len(findings),
                "critical":  len([f for f in findings if f["threat_level"]=="critical"]),
                "confirmed": len([f for f in findings if f["threat_level"]=="confirmed"]),
                "suspicious":len([f for f in findings if f["threat_level"]=="suspicious"]),
                "findings":  findings,
            }

    def get_trust_tier(self, agent_name: str) -> str:
        """Return trust tier for an agent."""
        if self._raksha: return self._raksha.get_trust_tier(agent_name).name
        return "UNKNOWN"

    def register_trusted_agent(self, agent_name: str, tier_name: str = "KNOWN_AGENT"):
        """Register an agent with a trust tier."""
        if self._raksha:
            self._raksha.register_agent(agent_name, TrustTier[tier_name])

    def get_quarantine(self) -> list[dict]:
        """Return all quarantined writes."""
        return self._read_sheet(SHEET_QUARANTINE)

    def get_security_log(self) -> list[dict]:
        """Return the security event log."""
        return self._read_sheet(SHEET_SECURITY_LOG)

    def release_quarantine(self, request_id: str) -> dict:
        """Dharma-Adesh — user releases a quarantined write."""
        quarantined = self._read_sheet(SHEET_QUARANTINE)
        for item in quarantined:
            if item.get("Request ID") == request_id:
                import json as _json
                try:
                    fields = _json.loads(item.get("Fields JSON", "{}"))
                    sheet  = item.get("Target Sheet", "")
                    op     = item.get("Operation", "add")
                    if sheet and fields:
                        receipt = self._ledger.submit(WriteRequest(
                            requesting_agent="User", sheet=sheet, operation=op,
                            fields=fields, confidence="High",
                            source="User-stated", importance=8,
                        ))
                        return {"status": "released", "receipt": receipt}
                except Exception as e:
                    return {"status": "error", "error": str(e)}
        return {"status": "not_found"}

    def _quarantine(self, req: WriteRequest, scan) -> None:
        """Move blocked write to Quarantine sheet."""
        import json as _json, pandas as _pd
        try:
            try:
                df = _pd.read_excel(str(self.path), sheet_name=SHEET_QUARANTINE,
                                    engine="odf", header=0, dtype=str)
            except Exception:
                df = _pd.DataFrame()
            entry = {
                "Request ID": req.request_id, "Timestamp": req.timestamp,
                "Agent": req.requesting_agent, "Target Sheet": req.sheet,
                "Operation": req.operation, "Fields JSON": _json.dumps(req.fields),
                "Threat Level": scan.threat_level.value,
                "Threat Type": scan.threat_type.value if scan.threat_type else "",
                "Threats Found": "; ".join(scan.threats_found[:3]),
                "Status": "Quarantined", "Reviewed By": "", "Reviewed At": "",
            }
            df = _pd.concat([df, _pd.DataFrame([entry])], ignore_index=True)
            self._ledger._write_sheet(SHEET_QUARANTINE, df)
        except Exception: pass

    def _log_security(self, req: WriteRequest, scan) -> None:
        """Log suspicious (allowed) write to Security Log."""
        import pandas as _pd
        try:
            try:
                df = _pd.read_excel(str(self.path), sheet_name=SHEET_SECURITY_LOG,
                                    engine="odf", header=0, dtype=str)
            except Exception:
                df = _pd.DataFrame()
            entry = {
                "Timestamp": req.timestamp, "Agent": req.requesting_agent,
                "Sheet": req.sheet, "Threat Level": scan.threat_level.value,
                "Threat Type": scan.threat_type.value if scan.threat_type else "",
                "Threats": "; ".join(scan.threats_found[:3]),
                "Status": "Warned — allowed",
            }
            df = _pd.concat([df, _pd.DataFrame([entry])], ignore_index=True)
            self._ledger._write_sheet(SHEET_SECURITY_LOG, df)
        except Exception: pass


    def stats(self) -> dict:
        """
        yantra stats — memory growth analytics (v2.7).
        Shows row counts, growth trends, top contributors.
        CLI: yantra stats
        """
        from datetime import datetime as _dt, timedelta as _td
        result = {}

        # Row counts per sheet
        sheet_counts = {}
        for sheet in [
            SHEET_IDENTITY, SHEET_GOALS, SHEET_PROJECTS, SHEET_PEOPLE,
            SHEET_PREFERENCES, SHEET_BELIEFS, SHEET_TASKS, SHEET_OPEN_LOOPS,
            SHEET_SESSION_LOG, SHEET_INBOX, SHEET_CORRECTIONS,
        ]:
            rows = self._read_sheet(sheet)
            sheet_counts[sheet] = len(rows)
        result["sheet_counts"] = sheet_counts
        result["total_rows"] = sum(sheet_counts.values())

        # Session activity — writes per day over last 30 days
        ledger = self._read_sheet(SHEET_LEDGER)
        cutoff_30 = (_dt.utcnow() - _td(days=30)).isoformat()[:10]
        cutoff_7  = (_dt.utcnow() - _td(days=7)).isoformat()[:10]

        recent_30 = [r for r in ledger if str(r.get("Timestamp",""))[:10] >= cutoff_30 and r.get("Status") == "written"]
        recent_7  = [r for r in ledger if str(r.get("Timestamp",""))[:10] >= cutoff_7  and r.get("Status") == "written"]

        result["writes_last_30_days"] = len(recent_30)
        result["writes_last_7_days"]  = len(recent_7)
        result["total_writes"]        = len([r for r in ledger if r.get("Status") == "written"])

        # Top contributing agents
        agent_counts: dict[str, int] = {}
        for r in ledger:
            if r.get("Status") == "written":
                agent = r.get("Agent", "Unknown")
                agent_counts[agent] = agent_counts.get(agent, 0) + 1
        result["writes_by_agent"] = dict(sorted(agent_counts.items(), key=lambda x: -x[1])[:5])

        # Most active sheets
        sheet_writes: dict[str, int] = {}
        for r in ledger:
            if r.get("Status") == "written":
                sheet = r.get("Sheet", "Unknown")
                sheet_writes[sheet] = sheet_writes.get(sheet, 0) + 1
        result["writes_by_sheet"] = dict(sorted(sheet_writes.items(), key=lambda x: -x[1])[:5])

        # Open loop health
        all_loops = self._read_sheet(SHEET_OPEN_LOOPS)
        open_loops = [r for r in all_loops if r.get("Resolved?") == "No"]
        closed_loops = [r for r in all_loops if r.get("Resolved?") == "Yes"]
        result["open_loops_total"]   = len(open_loops)
        result["closed_loops_total"] = len(closed_loops)
        result["loop_resolution_rate"] = (
            round(len(closed_loops) / max(1, len(all_loops)) * 100, 1)
        )

        # High importance items
        all_rows = []
        for sheet in [SHEET_PROJECTS, SHEET_GOALS, SHEET_TASKS, SHEET_OPEN_LOOPS]:
            all_rows.extend(self._read_sheet(sheet))
        high_imp = [r for r in all_rows if int(r.get("Importance", 0) or 0) >= 8]
        result["high_importance_items"] = len(high_imp)

        result["chitrapat_size_kb"] = (
            self.path.stat().st_size // 1024 if self.path.exists() else 0
        )
        return result


    def get_ledger(self) -> list[dict]:
        return self._read_sheet(SHEET_LEDGER)

    def get_agrasandhani(self) -> list[dict]:
        return self.get_ledger()

    def get_vidyakosha_stats(self) -> dict:
        if self._vidyakosha: return self._vidyakosha.stats()
        return {"status": "not initialised"}


# ── Sheet routing heuristic ────────────────────────────────────────────────────

def _infer_sheet(text: str) -> Optional[str]:
    """Simple keyword-based sheet inference for Inbox routing."""
    text = text.lower()
    if any(w in text for w in ["project", "build", "working on", "developing",
                                 "feature", "milestone"]):
        return SHEET_PROJECTS
    if any(w in text for w in ["task", "todo", "need to", "should do",
                                 "remember to", "don't forget"]):
        return SHEET_TASKS
    if any(w in text for w in ["goal", "want to", "aim to", "aspire",
                                 "dream", "achieve"]):
        return SHEET_GOALS
    if any(w in text for w in ["person", "friend", "colleague", "met",
                                 "talked to", "knows", "works at"]):
        return SHEET_PEOPLE
    if any(w in text for w in ["prefer", "like", "hate", "love", "enjoy",
                                 "dislike", "favourite"]):
        return SHEET_PREFERENCES
    if any(w in text for w in ["believe", "think", "opinion", "value",
                                 "principle", "philosophy"]):
        return SHEET_BELIEFS
    return None


# ══════════════════════════════════════════════════════════════════════════════
# Bootstrap Interview Agent
# ══════════════════════════════════════════════════════════════════════════════

def run_bootstrap_interview(path: str, agent_name: str = "Chitragupta"):
    """
    Terminal Bootstrap Interview v2.6 — Chitragupta Puja
    Cold start via conversation, not empty spreadsheets.

    12 questions from 8-model consensus — covers all key sheets:
    Identity, Goals, Projects, People, Preferences, Beliefs, Open Loops

    Features:
    - Progress bar (Q3/12)
    - Skip any question with Enter
    - Sheet preview after completion (the aha moment)
    - Anti-goals, belief evolution, decision principles
    """
    oy = OpenYantra(path, agent_name=agent_name)
    if oy.path.exists():
        print(f"\n[OpenYantra] Chitrapat already exists at {oy.path}")
        print("[OpenYantra] Run `yantra ui` to review and edit it.")
        return oy

    print("\n" + "="*62)
    print("  OpenYantra — Chitragupta Puja")
    print("  The Sacred Memory Machine v2.6")
    print("  Inspired by Chitragupta, the Hindu God of Data")
    print("="*62)
    print("\nNamaste. I am Chitragupta, your memory keeper.")
    print("Answer what feels right. Press Enter to skip any question.")
    print("This takes about 5 minutes.\n")

    total_q = 12

    def ask(question: str, q_num: int, hint: str = "") -> str:
        progress = f"[{q_num}/{total_q}]"
        bar_filled = int((q_num / total_q) * 20)
        bar = "█" * bar_filled + "░" * (20 - bar_filled)
        print(f"  {progress} {bar}")
        if hint:
            print(f"  {hint}")
        try:
            return input(f"  → ").strip()
        except (EOFError, KeyboardInterrupt):
            return ""

    def multi(question: str, q_num: int, hint: str = "") -> list[str]:
        raw = ask(question, q_num, hint)
        if not raw:
            return []
        return [x.strip() for x in raw.replace(";", ",").split(",") if x.strip()]

    # ── Q1: The pain point ──────────────────────────────────────────────────
    print(f"\n  Q1 — Your AI Memory Pain Point")
    pain = ask("What does your AI always forget that you wish it remembered?", 1,
               "This tells me where to focus most. (e.g. 'my current projects', 'my preferences')")

    # ── Q2: Identity ────────────────────────────────────────────────────────
    print(f"\n  Q2 — Who you are")
    name       = ask("Your name:", 2)
    occupation = ask("Your occupation / role:", 2)
    location   = ask("Where are you based? (city, country)", 2)
    language   = ask("Primary language (default: English):", 2)

    oy.bootstrap(user_name=name, occupation=occupation, location=location)
    if language and language.lower() != "english":
        oy.update_identity("Primary Language", language)

    # ── Q3: Life domains ────────────────────────────────────────────────────
    print(f"\n  Q3 — Life Domains")
    domains = multi(
        "What are your 3–5 most important life areas right now?", 3,
        "(e.g. career, health, creative work, family, learning — comma separated)")
    for domain in domains[:5]:
        oy.request_write(WriteRequest(
            agent_name, SHEET_BELIEFS, "add",
            {"Topic": f"Life domain: {domain}",
             "Position": f"{domain} is a core area of focus",
             "Domain": domain, "Confidence": "High"},
            confidence="High", source="User-stated", importance=8,
        ))

    # ── Q4: Active projects ─────────────────────────────────────────────────
    print(f"\n  Q4 — Active Projects")
    print("  Tell me about your top projects. I'll ask for each one.")
    for i in range(1, 4):
        project = ask(f"Active project {i} name (or Enter to skip):", 4)
        if not project:
            break
        domain  = ask(f"  Domain for '{project}'? (Work/Creative/Personal/Learning)", 4)
        nextstep= ask(f"  Next concrete step for '{project}'?", 4)
        oy.add_project(project, domain=domain or "Work",
                       next_step=nextstep, importance=8)

    # ── Q5: Goals ───────────────────────────────────────────────────────────
    print(f"\n  Q5 — Goals")
    long_goal  = ask("Your most important long-term goal:", 5,
                     "(e.g. 'complete my debut feature film', 'launch my startup')")
    short_goal = ask("A short-term goal you're working on right now:", 5)
    success    = ask(f"How will you know you've achieved '{long_goal or 'your goal'}'?", 5,
                     "(What's the specific success signal?)")

    for goal, gtype, note in [
        (long_goal, "Long-term", success),
        (short_goal, "Short-term", ""),
    ]:
        if goal:
            oy.request_write(WriteRequest(
                agent_name, SHEET_GOALS, "add",
                {"Goal": goal, "Type": gtype, "Priority": "High",
                 "Status": "Active", "Notes": note},
                confidence="High", source="User-stated", importance=9,
            ))

    # ── Q6: People ──────────────────────────────────────────────────────────
    print(f"\n  Q6 — Your People")
    print("  Tell me about important people in your work and life.")
    for i in range(1, 4):
        person = ask(f"Important person {i} name (or Enter to skip):", 6)
        if not person:
            break
        role    = ask(f"  Your relationship with {person}?", 6,
                      "  (e.g. producer, co-founder, mentor, close friend)")
        context = ask(f"  One key thing to remember about {person}?", 6)
        loop    = ask(f"  Any unresolved thread with {person}?", 6,
                      "  (e.g. 'waiting for budget approval', 'need to follow up')")
        oy.add_person(person, relationship=role or "Contact",
                      context=context, importance=7)
        if loop:
            oy.flush_open_loop(
                topic=f"Follow up with {person}",
                context=loop, priority="Medium",
                related_project="", ttl_days=30, importance=6,
            )

    # ── Q7: Preferences ─────────────────────────────────────────────────────
    print(f"\n  Q7 — Preferences & Rules")
    comm_style = ask("Communication style? (direct / formal / casual / thoughtful)", 7)
    tools_pref = ask("Preferred tools or software?", 7,
                     "(e.g. 'VS Code', 'Notion', 'LibreOffice', 'terminal')")
    work_hours = ask("Working hours?", 7, "(e.g. 10am–7pm IST)")

    for cat, pref in [
        ("Communication", comm_style),
        ("Tools", tools_pref),
        ("Working Hours", work_hours),
    ]:
        if pref:
            oy.request_write(WriteRequest(
                agent_name, SHEET_PREFERENCES, "add",
                {"Category": cat, "Preference": pref, "Strength": "Strong"},
                confidence="High", source="User-stated", importance=7,
            ))
    if work_hours:
        oy.update_identity("Working Hours", work_hours)

    # ── Q8: Anti-goals ──────────────────────────────────────────────────────
    print(f"\n  Q8 — Anti-Goals (what to avoid)")
    anti = ask("What should your AI never suggest or do?", 8,
               "(e.g. 'never suggest phone calls', 'avoid enterprise tools', 'no social media')")
    if anti:
        oy.request_write(WriteRequest(
            agent_name, SHEET_BELIEFS, "add",
            {"Topic": "Anti-goal", "Position": anti,
             "Domain": "Constraints", "Confidence": "High"},
            confidence="High", source="User-stated", importance=8,
        ))

    # ── Q9: Beliefs ─────────────────────────────────────────────────────────
    print(f"\n  Q9 — Beliefs & Principles")
    principle = ask("What principle guides your most important decisions?", 9,
                    "(e.g. 'creative freedom over short-term money', 'build in public')")
    old_belief = ask("What belief did you hold 5 years ago that you no longer hold?", 9,
                     "(This seeds your belief evolution history)")

    for topic, position in [
        ("Decision principle", principle),
        ("Past belief (evolved)", old_belief),
    ]:
        if position:
            oy.request_write(WriteRequest(
                agent_name, SHEET_BELIEFS, "add",
                {"Topic": topic, "Position": position,
                 "Domain": "Values", "Confidence": "High"},
                confidence="High", source="User-stated", importance=8,
            ))

    # ── Q10: Open loops ─────────────────────────────────────────────────────
    print(f"\n  Q10 — Current Open Loops")
    decision = ask("What decision are you currently second-guessing?", 10,
                   "(Unresolved decisions become Open Loops — the system's strongest feature)")
    recurring = ask("What problem keeps returning in your life?", 10)

    for topic, ctx in [
        ("Second-guessing: " + (decision[:50] if decision else ""), decision),
        ("Recurring problem: " + (recurring[:50] if recurring else ""), recurring),
    ]:
        if ctx:
            oy.flush_open_loop(topic, ctx, priority="High", ttl_days=60, importance=8)

    # ── Q11: Reminder preference ────────────────────────────────────────────
    print(f"\n  Q11 — How You Want to Be Reminded")
    reminder = ask("How do you prefer to be reminded about pending items?", 11,
                   "(e.g. 'morning digest', 'Telegram bot', 'dashboard', 'weekly summary')")
    if reminder:
        oy.request_write(WriteRequest(
            agent_name, SHEET_AGENT_CONFIG, "add",
            {"Agent": "ALL", "Instruction": f"User prefers reminders via: {reminder}",
             "Priority": "High", "Active": "Yes"},
            confidence="High", source="User-stated", importance=7,
        ))

    # ── Q12: The aha moment — sheet preview ─────────────────────────────────
    print(f"\n  Q12 — Verify")
    ctx = oy.load_session_context()

    print("\n" + "="*62)
    print("  ✓ Chitragupta has recorded your memory.")
    print("="*62)
    print(f"\n  Identity:    {name} | {occupation} | {location}")
    print(f"  Life domains: {', '.join(domains[:3]) if domains else 'none recorded'}")

    projects = ctx.get('active_projects', [])
    if projects:
        print(f"  Projects ({len(projects)}):")
        for p in projects[:3]:
            print(f"    • {p.get('Project','')} → {p.get('Next Step','')[:50]}")

    loops = ctx.get('open_loops', [])
    if loops:
        print(f"  Open Loops ({len(loops)}):")
        for l in loops[:3]:
            print(f"    • [{l.get('Priority','?')}] {l.get('Topic','')[:55]}")

    goals_list = oy._read_sheet(SHEET_GOALS)
    if goals_list:
        print(f"  Goals ({len(goals_list)}):")
        for g in goals_list[:2]:
            print(f"    • {g.get('Goal','')[:60]}")

    if pain:
        print(f"\n  Your pain point: '{pain}'")
        print(f"  → I'll prioritise {pain[:40]} in every session.")

    print(f"\n  {'─'*58}")
    print(f"  Chitrapat: {oy.path}")
    print(f"  Open it:   libreoffice '{oy.path}'")
    print(f"  Dashboard: yantra ui")
    print("="*62 + "\n")
    return oy
# ══════════════════════════════════════════════════════════════════════════════
# ODS template builder v2.1
# ══════════════════════════════════════════════════════════════════════════════

def _build_ods_template(path: str):
    """Build a blank OpenYantra Chitrapat with all 14 sheets (v2.1)."""
    sheets = {
        SHEET_INDEX: [
            ["Sheet", "Sanskrit", "English", "Purpose", "v2.1 additions"],
            ["👤 Identity",     "Svarupa",      "Identity",    "Who you are",              "Importance column"],
            ["🎯 Goals",        "Sankalpa",      "Goals",       "What you want",            "Importance, TTL"],
            ["🚀 Projects",     "Karma",         "Projects",    "Active work",              "Importance column"],
            ["👥 People",       "Sambandha",     "People",      "Relationships",            "Importance column"],
            ["💡 Preferences",  "Ruchi",         "Preferences", "Taste and habits",         "Importance column"],
            ["🧠 Beliefs",      "Vishwas",       "Beliefs",     "Values, worldview",        "Contradiction_Flag"],
            ["✅ Tasks",        "Kartavya",      "Tasks",       "Action items",             "Importance column"],
            ["🔓 Open Loops",   "Anishtha",      "Open Loops",  "Unresolved threads",       "TTL_Days column"],
            ["📅 Session Log",  "Dinacharya",    "Session Log", "Per-session history",      "—"],
            ["⚙️ Agent Config", "Niyama",        "Agent Config","Per-agent settings",       "VidyaKosha mode"],
            ["📒 Agrasandhanī", "Agrasandhanī",  "Ledger",      "Immutable audit trail",    "Importance logged"],
            ["📥 Inbox",        "Avagraha",      "Inbox",       "Quick capture — NEW v2.1", "Route to sheets"],
            ["✏️ Corrections",  "Sanshodhan",    "Corrections", "Pending edits — NEW v2.1", "Agent proposals"],
        ],
        SHEET_IDENTITY: [
            ["Attribute","Value","Last Updated","Notes","Confidence","Source","Importance"],
            ["Full Name","","","","High","User-stated","9"],
            ["Preferred Name","","","","High","User-stated","9"],
            ["Location","","","City/Region/Country","High","User-stated","8"],
            ["Timezone","","","e.g. IST, PST","High","User-stated","7"],
            ["Primary Language","","","","High","User-stated","8"],
            ["Occupation","","","","High","User-stated","8"],
            ["Industry","","","","High","User-stated","7"],
            ["Life Stage","","","e.g. early career","Medium","Agent-inferred","6"],
            ["Communication Style","","","e.g. direct, casual","Medium","Agent-observed","7"],
            ["Working Hours","","","e.g. 10am-7pm IST","Medium","User-stated","6"],
        ],
        SHEET_GOALS: [
            ["Goal","Type","Priority","Deadline","Status","Last Updated",
             "Notes","Confidence","Source","Importance"],
        ],
        SHEET_PROJECTS: [
            ["Project","Domain","Status","Priority","Key Decision Made",
             "Next Step","Last Updated","Notes","Confidence","Source","Importance"],
        ],
        SHEET_PEOPLE: [
            ["Name","Relationship","Context","Sentiment","Last Mentioned",
             "Notes","Confidence","Source","Importance"],
        ],
        SHEET_PREFERENCES: [
            ["Category","Preference","Strength","Source","Notes",
             "Confidence","Last Updated","Importance"],
        ],
        SHEET_BELIEFS: [
            ["Topic","Position","Confidence","Domain","Last Updated",
             "Notes","Source","Importance","Contradiction_Flag"],
        ],
        SHEET_TASKS: [
            ["Task","Project","Priority","Deadline","Status","Added By",
             "Notes","Confidence","Source","Importance"],
        ],
        SHEET_OPEN_LOOPS: [
            ["Topic","Context / What's Unresolved","Opened","Priority",
             "Related Project","Resolved?","Resolution","TTL_Days",
             "Confidence","Source","Importance"],
        ],
        SHEET_SESSION_LOG: [
            ["Date","Topics Discussed","Decisions Made","New Memory Added",
             "Open Loops Created","Agent","Notes"],
        ],
        SHEET_AGENT_CONFIG: [
            ["Agent","Instruction","Priority","Active","Notes"],
            ["ALL","Load Svarupa + Anishtha + Karma at session start","Critical","Yes",""],
            ["ALL","Flush Anishtha before context compaction","Critical","Yes",""],
            ["ALL","All writes via Chitragupta — no direct file writes","Critical","Yes",""],
            ["ALL","Write Dinacharya to Session Log at session end","High","Yes",""],
            ["ALL","Use inbox() for quick captures without categorisation","High","Yes",""],
            ["Claude","Match communication style from Ruchi (Preferences)","High","Yes",""],
            ["Claude","Use per-session snapshot mode for VidyaKosha","Medium","Yes",""],
        ],
        SHEET_LEDGER: [
            ["Timestamp","Request ID","Agent","Sheet","Operation",
             "Row Identifier","Status","Confidence","Source",
             "Importance","Signature","Reason / Notes"],
        ],
        SHEET_INBOX: [
            ["Content","Captured","Routed?","Target Sheet",
             "Notes","Confidence","Source","Importance"],
        ],
        SHEET_CORRECTIONS: [
            ["Target Sheet","Row Identifier","Field","Proposed Value",
             "Reason","Status","Proposed By","Proposed At",
             "Reviewed By","Reviewed At","Notes"],
        ],
    }

    with pd.ExcelWriter(path, engine="odf") as writer:
        for sheet_name, rows in sheets.items():
            df = pd.DataFrame(rows[1:], columns=rows[0])
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    print(f"[OpenYantra] Template built: {path}")
