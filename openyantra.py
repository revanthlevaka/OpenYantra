"""
openyantra.py — OpenYantra Core Library
Version: 2.0
Project: OpenYantra — The Sacred Memory Machine
Inspired by Chitragupta (चित्रगुप्त), the Hindu God of Data

A vendor-neutral, human-readable persistent memory standard
for agentic AI systems. Any agent. Any framework. Any model.

v2.0 additions over v1.0:
    - VidyaKosha (vidyakosha.py) sidecar semantic index integration
    - oy.search()              — hybrid semantic + keyword search
    - oy.search_open_loops()   — scoped search on Anishtha sheet
    - oy.search_projects()     — scoped search on Karma sheet
    - oy.take_pratibimba()     — per-agent frozen snapshot (multi-agent safety)
    - oy.release_pratibimba()  — release snapshot at session end
    - oy.get_agrasandhani()    — alias for get_ledger() (Sanskrit name)
    - Auto-sync VidyaKosha on every Chitragupta write
    - sanchitta.json renamed from write_queue.json

Sanskrit ↔ English reference:
    Chitragupta   / LedgerAgent    — sole writer
    Agrasandhanī  / Ledger         — immutable audit trail sheet
    Chitrapat     / Memory file    — chitrapat.ods
    Karma-Lekha   / WriteRequest   — write submitted to LedgerAgent
    Sanchitta     / WriteQueue     — crash-safe queue (sanchitta.json)
    Smarana       / Session Load   — load context at session start
    Anishtha      / Open Loops     — unresolved threads
    Mudra         / Signature      — SHA-256 seal on every write
    Vivada        / Conflict       — escalated to user
    Dharma-Adesh  / User Override  — user edits always win
    VidyaKosha    / Sidecar Index  — semantic search engine
    Pratibimba    / Snapshot       — per-agent frozen index view
"""

from __future__ import annotations

import hashlib
import json
import shutil
import threading
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional

try:
    import pandas as pd
    from odf.opendocument import OpenDocumentSpreadsheet, load as odf_load
    from odf.table import Table, TableRow, TableCell
    from odf.text import P
except ImportError:
    raise ImportError(
        "OpenYantra v2.0 requires: pip install odfpy pandas\n"
    )

# VidyaKosha — graceful fallback if not installed
try:
    from vidyakosha import VidyaKosha as _VK, get_snapshot_mode as _get_snap_mode
    _VIDYAKOSHA_AVAILABLE = True
except ImportError:
    _VIDYAKOSHA_AVAILABLE = False
    _VK = None
    _get_snap_mode = None

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
OPERATIONS     = {"add", "update", "resolve", "archive", "delete"}

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

ALL_SHEETS = [
    SHEET_INDEX, SHEET_IDENTITY, SHEET_GOALS, SHEET_PROJECTS,
    SHEET_PEOPLE, SHEET_PREFERENCES, SHEET_BELIEFS, SHEET_TASKS,
    SHEET_OPEN_LOOPS, SHEET_SESSION_LOG, SHEET_AGENT_CONFIG, SHEET_LEDGER,
]

TODAY = date.today().isoformat()


# ══════════════════════════════════════════════════════════════════════════════
# WriteRequest (Karma-Lekha) — the only way agents submit writes
# ══════════════════════════════════════════════════════════════════════════════

class WriteRequest:
    """
    Karma-Lekha — a deed submitted to Chitragupta for recording.
    The only permitted path for any agent to write to the Chitrapat.
    """

    def __init__(
        self,
        requesting_agent: str,
        sheet: str,
        operation: str,
        fields: dict,
        row_identifier: Optional[str] = None,
        confidence: str = "High",
        source: str = "Agent-observed",
        session_id: Optional[str] = None,
    ):
        assert operation  in OPERATIONS,   f"operation must be one of {OPERATIONS}"
        assert confidence in CONFIDENCE_V, f"confidence must be one of {CONFIDENCE_V}"
        assert source     in SOURCE,       f"source must be one of {SOURCE}"

        self.requesting_agent = requesting_agent
        self.sheet            = sheet
        self.operation        = operation
        self.fields           = fields
        self.row_identifier   = row_identifier
        self.confidence       = confidence
        self.source           = source
        self.session_id       = session_id or TODAY
        self.timestamp        = datetime.utcnow().isoformat()
        self.request_id       = self._make_id()

    def _make_id(self) -> str:
        payload = f"{self.requesting_agent}{self.sheet}{self.timestamp}{json.dumps(self.fields)}"
        return hashlib.sha256(payload.encode()).hexdigest()[:16]

    def to_dict(self) -> dict:
        return {
            "request_id":       self.request_id,
            "requesting_agent": self.requesting_agent,
            "sheet":            self.sheet,
            "operation":        self.operation,
            "row_identifier":   self.row_identifier,
            "fields":           self.fields,
            "confidence":       self.confidence,
            "source":           self.source,
            "session_id":       self.session_id,
            "timestamp":        self.timestamp,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "WriteRequest":
        req = cls(
            requesting_agent = d["requesting_agent"],
            sheet            = d["sheet"],
            operation        = d["operation"],
            fields           = d["fields"],
            row_identifier   = d.get("row_identifier"),
            confidence       = d.get("confidence", "High"),
            source           = d.get("source", "Agent-observed"),
            session_id       = d.get("session_id"),
        )
        req.request_id = d.get("request_id", req.request_id)
        req.timestamp  = d.get("timestamp",  req.timestamp)
        return req


# ══════════════════════════════════════════════════════════════════════════════
# WriteQueue (Sanchitta) — disk-persisted crash-safe write buffer
# ══════════════════════════════════════════════════════════════════════════════

class WriteQueue:
    """
    Sanchitta — accumulated karma awaiting reckoning.
    Persists pending WriteRequests to sanchitta.json on disk.
    Auto-replayed on next OpenYantra() init after a crash.
    """

    def __init__(self, queue_path: Path):
        self.path  = queue_path
        self._lock = threading.Lock()
        self._ensure()

    def _ensure(self):
        if not self.path.exists():
            self._save([])

    def _load(self) -> list[dict]:
        try:
            return json.loads(self.path.read_text())
        except Exception:
            return []

    def _save(self, items: list[dict]):
        self.path.write_text(json.dumps(items, indent=2))

    def enqueue(self, req: WriteRequest):
        with self._lock:
            items = self._load()
            items.append(req.to_dict())
            self._save(items)

    def dequeue_all(self) -> list[WriteRequest]:
        with self._lock:
            items = self._load()
            self._save([])
            return [WriteRequest.from_dict(d) for d in items]

    def peek(self) -> list[dict]:
        return self._load()

    def is_empty(self) -> bool:
        return len(self._load()) == 0


# ══════════════════════════════════════════════════════════════════════════════
# LedgerAgent (Chitragupta) — the ONLY writer to the Chitrapat
# ══════════════════════════════════════════════════════════════════════════════

class LedgerAgent:
    """
    Chitragupta — the divine scribe. Sole writer to the Chitrapat.

    Responsibilities:
    - Validate every Karma-Lekha (WriteRequest)
    - Seal with Mudra (SHA-256 signature)
    - Commit to the Chitrapat (.ods file)
    - Record every write in the Agrasandhanī (Ledger sheet)
    - Replay the Sanchitta (WriteQueue) on startup
    - Detect Vivada (conflicts) and escalate Dharma-Adesh to user

    No other agent or class may write to the .ods file directly.
    All writes MUST go through LedgerAgent.submit().
    """

    def __init__(self, memory_path: Path, queue: WriteQueue):
        self.path  = memory_path
        self.queue = queue
        self._lock = threading.Lock()

    # ── Public interface ───────────────────────────────────────────────────────

    def submit(self, req: WriteRequest) -> dict:
        """
        Submit a Karma-Lekha for validation and commit.
        Enqueues first (crash safety), then processes immediately.
        Returns a receipt dict with status, timestamp, and Mudra.
        """
        self.queue.enqueue(req)
        return self._process(req)

    def replay_queue(self) -> int:
        """
        Replay Sanchitta entries from a previous crashed session.
        Called automatically on OpenYantra() init.
        Returns number of requests replayed.
        """
        pending = self.queue.dequeue_all()
        for req in pending:
            self._process(req)
        return len(pending)

    # ── Internal processing ────────────────────────────────────────────────────

    def _process(self, req: WriteRequest) -> dict:
        with self._lock:
            validation = self._validate(req)
            if validation["status"] == "rejected":
                self._log_audit(req, "rejected", validation["reason"])
                return validation

            conflict = self._check_conflict(req)
            if conflict:
                self._log_audit(req, "conflict", str(conflict))
                return {
                    "status":          "conflict",
                    "request_id":      req.request_id,
                    "existing_value":  conflict.get("existing"),
                    "requested_value": conflict.get("requested"),
                    "resolution":      "pending_user",
                    "message":         "Vivada detected — Dharma-Adesh required from user",
                }

            mudra = self._seal(req)
            self._commit(req, mudra)
            self._log_audit(req, "written", signature=mudra)

            return {
                "status":     "written",
                "request_id": req.request_id,
                "sheet":      req.sheet,
                "operation":  req.operation,
                "timestamp":  req.timestamp,
                "signature":  mudra,
            }

    def _validate(self, req: WriteRequest) -> dict:
        if req.sheet not in ALL_SHEETS:
            return {"status": "rejected", "reason": f"Unknown sheet: {req.sheet}"}
        if req.sheet == SHEET_LEDGER:
            return {"status": "rejected",
                    "reason": "Agrasandhanī is append-only and system-managed"}
        vocab_checks = {
            "Status":     (PROJECT_STATUS | TASK_STATUS | GOAL_STATUS),
            "Priority":   PRIORITY,
            "Resolved?":  RESOLVED,
            "Strength":   STRENGTH,
            "Confidence": CONFIDENCE_V,
            "Sentiment":  SENTIMENT,
        }
        for field, allowed in vocab_checks.items():
            if field in req.fields and req.fields[field] not in allowed:
                return {
                    "status": "rejected",
                    "reason": f"Invalid {field} value '{req.fields[field]}'. "
                              f"Allowed: {sorted(allowed)}",
                }
        return {"status": "valid"}

    def _check_conflict(self, req: WriteRequest) -> Optional[dict]:
        if req.operation != "update" or not req.row_identifier:
            return None
        try:
            df = pd.read_excel(str(self.path), sheet_name=req.sheet,
                               engine="odf", header=0, dtype=str)
            if df.empty:
                return None
            match = df[df.iloc[:, 0].astype(str) == req.row_identifier]
            if match.empty:
                return None
            existing_row = match.iloc[0]
            for field, new_val in req.fields.items():
                if field in existing_row.index:
                    existing_val  = existing_row[field]
                    existing_conf = existing_row.get("Confidence", "Low")
                    if (str(existing_val) != str(new_val) and
                            existing_conf == "High" and
                            req.confidence != "High"):
                        return {"field": field,
                                "existing": str(existing_val),
                                "requested": str(new_val)}
        except Exception:
            pass
        return None

    def _seal(self, req: WriteRequest) -> str:
        """Mudra — SHA-256 seal authenticating this write."""
        payload = json.dumps(req.to_dict(), sort_keys=True)
        return "sha256:" + hashlib.sha256(payload.encode()).hexdigest()[:32]

    def _commit(self, req: WriteRequest, mudra: str):
        """Write to the Chitrapat. Only place file writes happen."""
        try:
            try:
                df = pd.read_excel(str(self.path), sheet_name=req.sheet,
                                   engine="odf", header=0, dtype=str)
            except Exception:
                df = pd.DataFrame()

            now = datetime.utcnow().isoformat(timespec="seconds")

            if req.operation == "add":
                new_row = {**req.fields,
                           "Confidence":   req.confidence,
                           "Source":       req.source,
                           "Added By":     req.requesting_agent,
                           "Last Updated": now}
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

            elif req.operation == "update" and req.row_identifier:
                mask = (df.iloc[:, 0].astype(str) == req.row_identifier
                        if not df.empty and len(df.columns) > 0
                        else pd.Series([], dtype=bool))
                if mask.any():
                    for field, val in req.fields.items():
                        if field in df.columns:
                            df.loc[mask, field] = val
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
                if "Resolved?" in df.columns:
                    df.loc[mask, "Resolved?"] = "Yes"
                if "Resolution" in df.columns:
                    df.loc[mask, "Resolution"] = req.fields.get("Resolution", "")
                if "Last Updated" in df.columns:
                    df.loc[mask, "Last Updated"] = now

            elif req.operation == "archive" and req.row_identifier:
                mask = (df.iloc[:, 0].astype(str) == req.row_identifier
                        if not df.empty and len(df.columns) > 0
                        else pd.Series([], dtype=bool))
                if "Status" in df.columns:
                    df.loc[mask, "Status"] = "Archived"
                if "Last Updated" in df.columns:
                    df.loc[mask, "Last Updated"] = now

            self._write_sheet(req.sheet, df)

        except Exception as e:
            raise RuntimeError(f"Chitragupta commit failed: {e}") from e

    def _write_sheet(self, sheet_name: str, df: pd.DataFrame):
        """Write one sheet back preserving all other sheets."""
        existing_sheets = {}
        try:
            xl = pd.ExcelFile(str(self.path), engine="odf")
            for name in xl.sheet_names:
                if name != sheet_name:
                    try:
                        existing_sheets[name] = pd.read_excel(
                            str(self.path), sheet_name=name,
                            engine="odf", header=None)
                    except Exception:
                        existing_sheets[name] = pd.DataFrame()
        except Exception:
            pass

        with pd.ExcelWriter(str(self.path), engine="odf") as writer:
            for name, sdf in existing_sheets.items():
                sdf.to_excel(writer, sheet_name=name, index=False, header=False)
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    def _log_audit(self, req: WriteRequest, status: str,
                   reason: str = "", signature: str = ""):
        """Append an entry to the Agrasandhanī — the immutable audit trail."""
        entry = {
            "Timestamp":      req.timestamp,
            "Request ID":     req.request_id,
            "Agent":          req.requesting_agent,
            "Sheet":          req.sheet,
            "Operation":      req.operation,
            "Row Identifier": req.row_identifier or "",
            "Status":         status,
            "Confidence":     req.confidence,
            "Source":         req.source,
            "Signature":      signature,
            "Reason / Notes": reason,
        }
        try:
            try:
                ledger_df = pd.read_excel(str(self.path), sheet_name=SHEET_LEDGER,
                                          engine="odf", header=0, dtype=str)
            except Exception:
                ledger_df = pd.DataFrame(columns=list(entry.keys()))
            ledger_df = pd.concat(
                [ledger_df, pd.DataFrame([entry])], ignore_index=True)
            self._write_sheet(SHEET_LEDGER, ledger_df)
        except Exception:
            pass  # Audit log failure must never block the main write


# ══════════════════════════════════════════════════════════════════════════════
# OpenYantra — public API
# ══════════════════════════════════════════════════════════════════════════════

class OpenYantra:
    """
    OpenYantra v2.0 — The Sacred Memory Machine

    READ operations:  all agents may call freely (Smarana)
    WRITE operations: agents call request_write() → routed through Chitragupta
    SEARCH:           oy.search() → VidyaKosha hybrid semantic + keyword index

    Usage:
        oy = OpenYantra("~/openyantra/chitrapat.ods", agent_name="Claude")
        oy.bootstrap(user_name="Revanth", occupation="Filmmaker", location="Hyderabad, IN")

        # Session start (Smarana)
        print(oy.build_system_prompt_block())

        # Writes via Chitragupta
        oy.add_project("My Film", status="Active", priority="High", next_step="Write act 2")
        oy.flush_open_loop("Script structure", "3-act vs 5-act undecided", "High")

        # v2.0 — Semantic search (VidyaKosha)
        results = oy.search("screenplay structure decisions")
        for r in results:
            print(r["sheet"], r["primary_value"], r["score"])

        # Session end (Dinacharya)
        oy.log_session(topics=["screenplay"], decisions=["Use 3-act"])
    """

    VERSION = "2.0"

    def __init__(self, path: str | Path, agent_name: str = "Agent"):
        self.path       = Path(path).expanduser()
        self.agent_name = agent_name
        self._queue     = WriteQueue(self.path.parent / "sanchitta.json")
        self._ledger    = LedgerAgent(self.path, self._queue)

        # Replay any pending Sanchitta from a previous crashed session
        replayed = self._ledger.replay_queue()
        if replayed:
            print(f"[OpenYantra] Replayed {replayed} pending Karma-Lekha "
                  f"from Sanchitta.")

        # VidyaKosha — sidecar semantic index (v2.0)
        self._vidyakosha = None
        if _VIDYAKOSHA_AVAILABLE and self.path.exists():
            try:
                self._vidyakosha = _VK(str(self.path.parent), embedder_pref="auto")
            except Exception:
                pass

    # ── Bootstrap (Chitragupta Puja) ──────────────────────────────────────────

    def bootstrap(self, user_name: str = "", occupation: str = "",
                  location: str = ""):
        """
        Chitragupta Puja — consecrate the Chitrapat.
        Creates a new memory file from the standard schema.
        Safe to call even if file already exists (skips if present).
        """
        if self.path.exists():
            print(f"[OpenYantra] Chitrapat already exists at {self.path}.")
            return

        self.path.parent.mkdir(parents=True, exist_ok=True)
        _build_ods_template(str(self.path))

        if any([user_name, occupation, location]):
            for attr, val in {
                "Preferred Name": user_name,
                "Occupation":     occupation,
                "Location":       location,
            }.items():
                if val:
                    self.request_write(WriteRequest(
                        requesting_agent = "System",
                        sheet            = SHEET_IDENTITY,
                        operation        = "update",
                        row_identifier   = attr,
                        fields           = {"Value": val},
                        confidence       = "High",
                        source           = "User-stated",
                    ))

        self.log_session(
            topics     = ["Chitragupta Puja — memory bootstrap"],
            decisions  = [f"Chitrapat created — OpenYantra v{self.VERSION}"],
            new_memory = [f"Identity: {user_name}" if user_name else "Identity stub"],
        )
        print(f"[OpenYantra] Chitrapat created at {self.path}")
        print(f"[OpenYantra] Open with LibreOffice, OnlyOffice, or Collabora.")

    # ── Write interface (Karma-Lekha → Chitragupta) ───────────────────────────

    def request_write(self, req: WriteRequest) -> dict:
        """
        Submit a Karma-Lekha to Chitragupta.
        THE ONLY WAY any agent may write to the Chitrapat.
        VidyaKosha auto-syncs after every successful write.
        """
        receipt = self._ledger.submit(req)
        if receipt.get("status") == "written" and self._vidyakosha is not None:
            try:
                self._vidyakosha.sync(self.path)
            except Exception:
                pass  # Index sync failure must never block writes
        return receipt

    # ── Convenience write helpers ──────────────────────────────────────────────

    def flush_open_loop(self, topic: str, context: str,
                        priority: str = "Medium",
                        related_project: str = "") -> dict:
        """Anishtha flush — preserve unresolved thread before compaction."""
        return self.request_write(WriteRequest(
            requesting_agent = self.agent_name,
            sheet            = SHEET_OPEN_LOOPS,
            operation        = "add",
            fields           = {
                "Topic":                       topic,
                "Context / What's Unresolved": context,
                "Opened":                      TODAY,
                "Priority":                    priority,
                "Related Project":             related_project,
                "Resolved?":                   "No",
                "Resolution":                  "",
            },
            confidence = "High",
            source     = "Agent-observed",
        ))

    def resolve_open_loop(self, topic: str, resolution: str = "") -> dict:
        """Mark an Anishtha (Open Loop) as resolved."""
        return self.request_write(WriteRequest(
            requesting_agent = self.agent_name,
            sheet            = SHEET_OPEN_LOOPS,
            operation        = "resolve",
            row_identifier   = topic,
            fields           = {"Resolution": resolution},
            confidence       = "High",
            source           = "Agent-observed",
        ))

    def log_session(self, topics: list[str], decisions: list[str] = None,
                    new_memory: list[str] = None,
                    open_loops_created: int = 0, notes: str = "") -> dict:
        """Dinacharya — write session summary to Session Log."""
        return self.request_write(WriteRequest(
            requesting_agent = self.agent_name,
            sheet            = SHEET_SESSION_LOG,
            operation        = "add",
            fields           = {
                "Date":               TODAY,
                "Topics Discussed":   "; ".join(topics),
                "Decisions Made":     "; ".join(decisions or []),
                "New Memory Added":   "; ".join(new_memory or []),
                "Open Loops Created": str(open_loops_created),
                "Agent":              self.agent_name,
                "Notes":              notes,
            },
            confidence = "High",
            source     = "System",
        ))

    def add_project(self, project: str, domain: str = "",
                    status: str = "Active", priority: str = "High",
                    key_decision: str = "", next_step: str = "",
                    notes: str = "") -> dict:
        return self.request_write(WriteRequest(
            requesting_agent = self.agent_name,
            sheet            = SHEET_PROJECTS,
            operation        = "add",
            fields           = {
                "Project": project, "Domain": domain,
                "Status": status,   "Priority": priority,
                "Key Decision Made": key_decision,
                "Next Step": next_step, "Notes": notes,
            },
            confidence = "High", source = "User-stated",
        ))

    def add_task(self, task: str, project: str = "", priority: str = "Medium",
                 deadline: str = "", status: str = "Pending",
                 notes: str = "") -> dict:
        return self.request_write(WriteRequest(
            requesting_agent = self.agent_name,
            sheet            = SHEET_TASKS,
            operation        = "add",
            fields           = {
                "Task": task, "Project": project,
                "Priority": priority, "Deadline": deadline,
                "Status": status, "Notes": notes,
            },
            confidence = "High", source = "User-stated",
        ))

    def add_person(self, name: str, relationship: str = "",
                   context: str = "", sentiment: str = "Neutral",
                   notes: str = "") -> dict:
        return self.request_write(WriteRequest(
            requesting_agent = self.agent_name,
            sheet            = SHEET_PEOPLE,
            operation        = "add",
            fields           = {
                "Name": name, "Relationship": relationship,
                "Context": context, "Sentiment": sentiment,
                "Last Mentioned": TODAY, "Notes": notes,
            },
            confidence = "Medium", source = "Agent-observed",
        ))

    def update_identity(self, attribute: str, value: str) -> dict:
        return self.request_write(WriteRequest(
            requesting_agent = self.agent_name,
            sheet            = SHEET_IDENTITY,
            operation        = "update",
            row_identifier   = attribute,
            fields           = {"Value": value},
            confidence       = "High", source = "User-stated",
        ))

    # ── Read interface (Smarana) ───────────────────────────────────────────────

    def _read_sheet(self, sheet_name: str) -> list[dict]:
        try:
            df = pd.read_excel(str(self.path), sheet_name=sheet_name,
                               engine="odf", header=0, dtype=str)
            return df.where(pd.notna(df), None).to_dict("records")
        except Exception:
            return []

    def load_session_context(self, agent_name: Optional[str] = None) -> dict:
        """
        Smarana — execute the Session Load Sequence.
        Returns structured context for system prompt injection.
        """
        agent = agent_name or self.agent_name

        id_map = {r.get("Attribute"): r.get("Value")
                  for r in self._read_sheet(SHEET_IDENTITY) if r.get("Value")}

        instructions = [
            r.get("Instruction") for r in self._read_sheet(SHEET_AGENT_CONFIG)
            if r.get("Active") == "Yes"
            and r.get("Agent") in (agent, "ALL")
            and r.get("Instruction")
        ]

        projects   = [r for r in self._read_sheet(SHEET_PROJECTS)
                      if r.get("Status") == "Active"]
        open_loops = [r for r in self._read_sheet(SHEET_OPEN_LOOPS)
                      if r.get("Resolved?") == "No"]
        goals      = [r for r in self._read_sheet(SHEET_GOALS)
                      if r.get("Status") in ("Active", "In Progress")]
        tasks      = [r for r in self._read_sheet(SHEET_TASKS)
                      if r.get("Status") not in ("Done", None)]

        return {
            "identity":           id_map,
            "agent_instructions": instructions,
            "active_projects":    projects,
            "open_loops":         open_loops,
            "active_goals":       goals,
            "pending_tasks":      tasks,
        }

    def build_system_prompt_block(self,
                                  agent_name: Optional[str] = None) -> str:
        """Build the [OPENYANTRA CONTEXT] block for system prompt injection."""
        ctx    = self.load_session_context(agent_name)
        id_map = ctx["identity"]

        user_line = " | ".join(filter(None, [
            id_map.get("Preferred Name") or id_map.get("Full Name"),
            id_map.get("Occupation"),
            id_map.get("Location"),
        ])) or "Unknown user"

        projects_line = "; ".join(
            f"{p.get('Project','?')} → {p.get('Next Step','no next step')}"
            for p in ctx["active_projects"]) or "None"

        loops_line = "; ".join(
            "{} — {}".format(l.get("Topic","?"),
                             l.get("Context / What's Unresolved",""))
            for l in ctx["open_loops"]) or "None"

        goals_line = "; ".join(
            g.get("Goal","") for g in ctx["active_goals"]) or "None"

        tasks_line = "; ".join(
            t.get("Task","") for t in ctx["pending_tasks"]) or "None"

        instructions_line = "\n  ".join(
            str(i) for i in ctx["agent_instructions"]) or "None"

        return (
            f"[OPENYANTRA CONTEXT — v{self.VERSION} | Chitragupta-secured]\n"
            f"User: {user_line}\n"
            f"Active Projects (Karma): {projects_line}\n"
            f"Open Loops (Anishtha): {loops_line}\n"
            f"Goals (Sankalpa): {goals_line}\n"
            f"Tasks (Kartavya): {tasks_line}\n"
            f"Agent Instructions (Niyama):\n  {instructions_line}\n"
            f"[/OPENYANTRA CONTEXT]"
        )

    def get_person(self, name: str) -> Optional[dict]:
        for r in self._read_sheet(SHEET_PEOPLE):
            if str(r.get("Name","")).lower() == name.lower():
                return r
        return None

    def get_preferences(self, category: Optional[str] = None) -> list[dict]:
        rows = self._read_sheet(SHEET_PREFERENCES)
        if category:
            rows = [r for r in rows
                    if str(r.get("Category","")).lower() == category.lower()]
        return rows

    # ── VidyaKosha — Semantic Search (v2.0) ───────────────────────────────────

    def search(
        self,
        query: str,
        top_k: int = 5,
        sheets: list = None,
        snapshot_mode: str = None,
        hybrid_alpha: float = 0.7,
    ) -> list[dict]:
        """
        VidyaKosha — hybrid semantic + keyword search across the Chitrapat.

        Finds memory rows by meaning, not just exact keyword matching.
        Requires vidyakosha.py in the same directory.

        Args:
            query:          Natural language query
            top_k:          Number of results to return
            sheets:         Filter to specific sheets (None = all)
            snapshot_mode:  "live" | "per-session" | None (auto from Agent Config)
            hybrid_alpha:   Vector weight 0.0–1.0 (default 0.7)

        Returns:
            List of result dicts sorted by hybrid score:
            [{sheet, primary_value, text, score, vector_score, bm25_score, row}]

        Example:
            results = oy.search("unresolved screenplay decisions")
            for r in results:
                print(r["sheet"], r["primary_value"], f"score={r['score']:.3f}")
        """
        if not _VIDYAKOSHA_AVAILABLE:
            print("[OpenYantra] VidyaKosha not available. "
                  "Ensure vidyakosha.py is in the same directory.")
            return []

        if self._vidyakosha is None:
            self._vidyakosha = _VK(str(self.path.parent), embedder_pref="auto")
            self._vidyakosha.sync(self.path)

        if snapshot_mode is None and _get_snap_mode:
            snapshot_mode = _get_snap_mode(self.agent_name, self.path)

        return self._vidyakosha.query(
            text          = query,
            agent_name    = self.agent_name,
            top_k         = top_k,
            sheets        = sheets,
            snapshot_mode = snapshot_mode or "live",
            hybrid_alpha  = hybrid_alpha,
        )

    def search_open_loops(self, query: str, top_k: int = 5) -> list[dict]:
        """Semantic search across Anishtha (Open Loops) only."""
        return self.search(query, top_k=top_k, sheets=[SHEET_OPEN_LOOPS])

    def search_projects(self, query: str, top_k: int = 5) -> list[dict]:
        """Semantic search across Karma (Projects) only."""
        return self.search(query, top_k=top_k, sheets=[SHEET_PROJECTS])

    def search_people(self, query: str, top_k: int = 5) -> list[dict]:
        """Semantic search across Sambandha (People) only."""
        return self.search(query, top_k=top_k, sheets=[SHEET_PEOPLE])

    def take_pratibimba(self):
        """
        Pratibimba — take a frozen snapshot of the VidyaKosha index
        for this agent. Call at session start when snapshot_mode=per-session.
        """
        if self._vidyakosha:
            self._vidyakosha.take_snapshot(self.agent_name)

    def release_pratibimba(self):
        """Release this agent's Pratibimba snapshot at session end."""
        if self._vidyakosha:
            self._vidyakosha.release_snapshot(self.agent_name)

    # ── Audit ──────────────────────────────────────────────────────────────────

    def get_ledger(self) -> list[dict]:
        """Return the Agrasandhanī — full immutable audit trail."""
        return self._read_sheet(SHEET_LEDGER)

    def get_agrasandhani(self) -> list[dict]:
        """Agrasandhanī — the cosmic register. Alias for get_ledger()."""
        return self.get_ledger()

    def get_vidyakosha_stats(self) -> dict:
        """Return VidyaKosha index statistics."""
        if self._vidyakosha:
            return self._vidyakosha.stats()
        return {"status": "VidyaKosha not initialised"}


# ══════════════════════════════════════════════════════════════════════════════
# ODS template builder
# ══════════════════════════════════════════════════════════════════════════════

def _build_ods_template(path: str):
    """Build a blank OpenYantra Chitrapat with all 12 sheets."""
    sheets = {
        SHEET_INDEX: [
            ["Sheet", "Sanskrit", "English", "Purpose", "Mutability"],
            ["👤 Identity",     "Svarupa",       "Identity",    "Who the user is",         "Chitragupta-write, user-override"],
            ["🎯 Goals",        "Sankalpa",       "Goals",       "Long/short-term aims",    "Chitragupta-write, user-override"],
            ["🚀 Projects",     "Karma",          "Projects",    "Active work",             "Chitragupta-write, user-override"],
            ["👥 People",       "Sambandha",      "People",      "Relationships",           "Chitragupta-write, user-override"],
            ["💡 Preferences",  "Ruchi",          "Preferences", "Taste and style",         "Chitragupta-write, user-override"],
            ["🧠 Beliefs",      "Vishwas",        "Beliefs",     "Values and worldview",    "Chitragupta-write, user-override"],
            ["✅ Tasks",        "Kartavya",       "Tasks",       "Action items",            "Chitragupta-write, user-override"],
            ["🔓 Open Loops",   "Anishtha",       "Open Loops",  "Unresolved threads",      "Chitragupta-write, user-override"],
            ["📅 Session Log",  "Dinacharya",     "Session Log", "Per-session summaries",   "Chitragupta-write only"],
            ["⚙️ Agent Config", "Niyama",         "Agent Config","Per-agent instructions",  "User-write, agent-read"],
            ["📒 Agrasandhanī", "Agrasandhanī",   "Ledger",      "Immutable audit trail",   "Chitragupta-append only"],
        ],
        SHEET_IDENTITY: [
            ["Attribute", "Value", "Last Updated", "Notes", "Confidence", "Source"],
            ["Full Name",           "", "", "", "High", "User-stated"],
            ["Preferred Name",      "", "", "", "High", "User-stated"],
            ["Location",            "", "", "City / Region / Country", "High", "User-stated"],
            ["Timezone",            "", "", "e.g. IST, PST", "High", "User-stated"],
            ["Primary Language",    "", "", "", "High", "User-stated"],
            ["Occupation",          "", "", "", "High", "User-stated"],
            ["Industry",            "", "", "", "High", "User-stated"],
            ["Life Stage",          "", "", "e.g. early career, student", "Medium", "Agent-inferred"],
            ["Communication Style", "", "", "e.g. direct, casual", "Medium", "Agent-observed"],
            ["Working Hours",       "", "", "e.g. 10am–7pm IST", "Medium", "User-stated"],
        ],
        SHEET_GOALS: [
            ["Goal", "Type", "Priority", "Deadline", "Status", "Last Updated",
             "Notes", "Confidence", "Source"],
        ],
        SHEET_PROJECTS: [
            ["Project", "Domain", "Status", "Priority", "Key Decision Made",
             "Next Step", "Last Updated", "Notes", "Confidence", "Source"],
        ],
        SHEET_PEOPLE: [
            ["Name", "Relationship", "Context", "Sentiment",
             "Last Mentioned", "Notes", "Confidence", "Source"],
        ],
        SHEET_PREFERENCES: [
            ["Category", "Preference", "Strength", "Source",
             "Notes", "Confidence", "Last Updated"],
        ],
        SHEET_BELIEFS: [
            ["Topic", "Position", "Confidence", "Domain",
             "Last Updated", "Notes", "Source"],
        ],
        SHEET_TASKS: [
            ["Task", "Project", "Priority", "Deadline", "Status",
             "Added By", "Notes", "Confidence", "Source"],
        ],
        SHEET_OPEN_LOOPS: [
            ["Topic", "Context / What's Unresolved", "Opened", "Priority",
             "Related Project", "Resolved?", "Resolution", "Confidence", "Source"],
        ],
        SHEET_SESSION_LOG: [
            ["Date", "Topics Discussed", "Decisions Made", "New Memory Added",
             "Open Loops Created", "Agent", "Notes"],
        ],
        SHEET_AGENT_CONFIG: [
            ["Agent", "Instruction", "Priority", "Active", "Notes"],
            ["ALL",    "Load Svarupa + Anishtha + Karma at session start",      "Critical", "Yes", ""],
            ["ALL",    "Flush Anishtha before context compaction",               "Critical", "Yes", ""],
            ["ALL",    "All writes via Chitragupta — no direct file writes",     "Critical", "Yes", ""],
            ["ALL",    "Write Dinacharya to Session Log at session end",         "High",     "Yes", ""],
            ["Claude", "Match communication style from Ruchi (Preferences)",     "High",     "Yes", ""],
            ["Claude", "Use per-session snapshot mode for VidyaKosha",           "Medium",   "Yes", ""],
        ],
        SHEET_LEDGER: [
            ["Timestamp", "Request ID", "Agent", "Sheet", "Operation",
             "Row Identifier", "Status", "Confidence", "Source",
             "Signature", "Reason / Notes"],
        ],
    }

    with pd.ExcelWriter(path, engine="odf") as writer:
        for sheet_name, rows in sheets.items():
            df = pd.DataFrame(rows[1:], columns=rows[0])
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    print(f"[OpenYantra] Template built: {path}")
