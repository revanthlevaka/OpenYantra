"""
openyantra.py — OpenYantra, Core Library
Protocol v2.0 | https://github.com/yourusername/universal-agent-memory

A vendor-neutral, human-readable memory standard for agentic AI systems.
Any agent. Any framework. Any model.

Key changes in v2:
- Format: .ods (OpenDocument Spreadsheet) — ISO/IEC 26300 open standard
  Works natively on LibreOffice, OpenOffice, Collabora (Mac/Linux/Windows/Android/iOS)
- LedgerAgent: the ONLY writer to the memory file.
  All other agents are read-only. They submit write requests to LedgerAgent.
- WriteQueue: disk-persisted queue that survives process crashes.
  Replayed automatically on next OpenYantra init.
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
    from odf.style import Style, TableCellProperties, TextProperties, TableColumnProperties
    from odf import style as odf_style
except ImportError:
    raise ImportError(
        "UAM v2 requires: pip install odfpy pandas openpyxl\n"
        "For full ODS support: pip install odfpy"
    )

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
SHEET_LEDGER       = "📒 Ledger"          # append-only audit log — NEW in v2

ALL_SHEETS = [
    SHEET_INDEX, SHEET_IDENTITY, SHEET_GOALS, SHEET_PROJECTS,
    SHEET_PEOPLE, SHEET_PREFERENCES, SHEET_BELIEFS, SHEET_TASKS,
    SHEET_OPEN_LOOPS, SHEET_SESSION_LOG, SHEET_AGENT_CONFIG, SHEET_LEDGER,
]

TODAY = date.today().isoformat()


# ══════════════════════════════════════════════════════════════════════════════
# WriteRequest — the only way any agent communicates a write intention
# ══════════════════════════════════════════════════════════════════════════════

class WriteRequest:
    """
    A structured write request submitted by any agent to LedgerAgent.
    Agents NEVER write to the .ods file directly — they submit WriteRequests.
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
        assert operation in OPERATIONS, f"operation must be one of {OPERATIONS}"
        assert confidence in CONFIDENCE_V, f"confidence must be one of {CONFIDENCE_V}"
        assert source in SOURCE, f"source must be one of {SOURCE}"

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
        req.timestamp  = d.get("timestamp", req.timestamp)
        return req


# ══════════════════════════════════════════════════════════════════════════════
# WriteQueue — disk-persisted, crash-safe write buffer
# ══════════════════════════════════════════════════════════════════════════════

class WriteQueue:
    """
    Disk-persisted queue of pending WriteRequests.
    If the process crashes before LedgerAgent commits a write,
    the queue survives on disk and replays on next OpenYantra init.
    """

    def __init__(self, queue_path: Path):
        self.path = queue_path
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
# LedgerAgent — the ONLY writer to the .ods file
# ══════════════════════════════════════════════════════════════════════════════

class LedgerAgent:
    """
    LedgerAgent is the single, trusted writer for all UAM memory operations.

    Responsibilities:
    - Validate every WriteRequest (schema, vocab, conflict detection)
    - Sign each write with a SHA-256 signature
    - Commit writes to the .ods file atomically
    - Maintain the append-only Ledger sheet (audit trail)
    - Replay the WriteQueue on startup

    No other agent or class may write to the .ods file directly.
    All writes must go through LedgerAgent.submit().
    """

    def __init__(self, memory_path: Path, queue: WriteQueue):
        self.path  = memory_path
        self.queue = queue
        self._lock = threading.Lock()

    # ── Public interface ───────────────────────────────────────────────────────

    def submit(self, req: WriteRequest) -> dict:
        """
        Submit a WriteRequest for validation and commit.
        Returns a receipt dict with status, timestamp, and signature.

        This is the ONLY public entry point for writes.
        """
        # Enqueue first — ensures crash safety
        self.queue.enqueue(req)

        # Then process immediately
        return self._process(req)

    def replay_queue(self) -> int:
        """
        Replay any requests that were queued but not committed
        (e.g. from a previous crashed session).
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
                    "status":             "conflict",
                    "request_id":         req.request_id,
                    "existing_value":     conflict.get("existing"),
                    "requested_value":    conflict.get("requested"),
                    "resolution":         "pending_user",
                    "message":            "Conflict escalated — user must resolve",
                }

            signature = self._sign(req)
            self._commit(req, signature)
            self._log_audit(req, "written", signature=signature)

            return {
                "status":     "written",
                "request_id": req.request_id,
                "sheet":      req.sheet,
                "operation":  req.operation,
                "timestamp":  req.timestamp,
                "signature":  signature,
            }

    def _validate(self, req: WriteRequest) -> dict:
        """Validate sheet name, operation, and controlled vocab fields."""
        if req.sheet not in ALL_SHEETS:
            return {"status": "rejected", "reason": f"Unknown sheet: {req.sheet}"}
        if req.sheet == SHEET_LEDGER:
            return {"status": "rejected", "reason": "Ledger sheet is append-only and system-managed"}

        # Vocab checks per sheet
        fields = req.fields
        checks = {
            "Status":    (PROJECT_STATUS | TASK_STATUS | GOAL_STATUS, "Status"),
            "Priority":  (PRIORITY, "Priority"),
            "Resolved?": (RESOLVED, "Resolved?"),
            "Strength":  (STRENGTH, "Strength"),
            "Confidence":(CONFIDENCE_V, "Confidence"),
            "Sentiment": (SENTIMENT, "Sentiment"),
        }
        for field, (allowed, label) in checks.items():
            if field in fields and fields[field] not in allowed:
                return {
                    "status": "rejected",
                    "reason": f"Invalid {label} value '{fields[field]}'. Allowed: {allowed}",
                }
        return {"status": "valid"}

    def _check_conflict(self, req: WriteRequest) -> Optional[dict]:
        """
        Detect conflicts: agent wants to update a row the user
        has edited more recently (higher confidence or newer timestamp).
        Returns conflict dict if conflict exists, None if safe to write.
        """
        if req.operation != "update" or not req.row_identifier:
            return None

        try:
            df = pd.read_excel(str(self.path), sheet_name=req.sheet,
                               engine="odf", header=0, dtype=str)
            if df.empty or df.columns[0] not in df.columns:
                return None

            match = df[df.iloc[:, 0].astype(str) == req.row_identifier] if not df.empty and len(df.columns) > 0 else df
            if match.empty:
                return None

            existing_row = match.iloc[0]

            # Check if user has a higher-confidence version of the same field
            for field, new_val in req.fields.items():
                if field in existing_row.index:
                    existing_val = existing_row[field]
                    existing_conf = existing_row.get("Confidence", "Low")

                    if (str(existing_val) != str(new_val) and
                            existing_conf == "High" and
                            req.confidence != "High"):
                        return {
                            "field":    field,
                            "existing": str(existing_val),
                            "requested": str(new_val),
                        }
        except Exception:
            pass

        return None

    def _sign(self, req: WriteRequest) -> str:
        """Generate a SHA-256 signature for this write."""
        payload = json.dumps(req.to_dict(), sort_keys=True)
        return "sha256:" + hashlib.sha256(payload.encode()).hexdigest()[:32]

    def _commit(self, req: WriteRequest, signature: str):
        """Write to the .ods file. This is the ONLY place file writes happen."""
        try:
            # Read current sheet
            try:
                df = pd.read_excel(str(self.path), sheet_name=req.sheet,
                                   engine="odf", header=0, dtype=str)
            except Exception:
                df = pd.DataFrame()

            now = datetime.utcnow().isoformat(timespec="seconds")

            if req.operation == "add":
                new_row = {**req.fields}
                new_row["Confidence"]    = req.confidence
                new_row["Source"]        = req.source
                new_row["Added By"]      = req.requesting_agent
                new_row["Last Updated"]  = now
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

            elif req.operation == "update" and req.row_identifier:
                mask = df.iloc[:, 0].astype(str) == req.row_identifier if not df.empty and len(df.columns) > 0 else pd.Series([], dtype=bool)
                if mask.any():
                    for field, val in req.fields.items():
                        if field in df.columns:
                            df.loc[mask, field] = val
                    if "Last Updated" in df.columns:
                        df.loc[mask, "Last Updated"] = now
                    if "Confidence" in df.columns:
                        df.loc[mask, "Confidence"] = req.confidence
                else:
                    # Row not found — treat as add
                    new_row = {**req.fields, "Confidence": req.confidence,
                               "Source": req.source, "Last Updated": now}
                    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

            elif req.operation == "resolve" and req.row_identifier:
                mask = df.iloc[:, 0].astype(str) == req.row_identifier if not df.empty and len(df.columns) > 0 else pd.Series([], dtype=bool)
                if "Resolved?" in df.columns:
                    df.loc[mask, "Resolved?"] = "Yes"
                if "Resolution" in df.columns:
                    df.loc[mask, "Resolution"] = req.fields.get("Resolution", "")
                if "Last Updated" in df.columns:
                    df.loc[mask, "Last Updated"] = now

            elif req.operation == "archive" and req.row_identifier:
                mask = df.iloc[:, 0].astype(str) == req.row_identifier if not df.empty and len(df.columns) > 0 else pd.Series([], dtype=bool)
                if "Status" in df.columns:
                    df.loc[mask, "Status"] = "Archived"
                if "Last Updated" in df.columns:
                    df.loc[mask, "Last Updated"] = now

            # Write all sheets back — pandas ExcelWriter with odf engine
            self._write_sheet(req.sheet, df)

        except Exception as e:
            raise RuntimeError(f"LedgerAgent commit failed: {e}") from e

    def _write_sheet(self, sheet_name: str, df: pd.DataFrame):
        """Write a single sheet back to the .ods file preserving all other sheets."""
        existing_sheets = {}
        try:
            xl = pd.ExcelFile(str(self.path), engine="odf")
            for name in xl.sheet_names:
                if name != sheet_name:
                    try:
                        existing_sheets[name] = pd.read_excel(
                            str(self.path), sheet_name=name,
                            engine="odf", header=None
                        )
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
        """Append an entry to the Ledger sheet — the immutable audit trail."""
        entry = {
            "Timestamp":       req.timestamp,
            "Request ID":      req.request_id,
            "Agent":           req.requesting_agent,
            "Sheet":           req.sheet,
            "Operation":       req.operation,
            "Row Identifier":  req.row_identifier or "",
            "Status":          status,
            "Confidence":      req.confidence,
            "Source":          req.source,
            "Signature":       signature,
            "Reason / Notes":  reason,
        }
        try:
            try:
                ledger_df = pd.read_excel(str(self.path), sheet_name=SHEET_LEDGER,
                                          engine="odf", header=0, dtype=str)
            except Exception:
                ledger_df = pd.DataFrame(columns=list(entry.keys()))

            ledger_df = pd.concat(
                [ledger_df, pd.DataFrame([entry])], ignore_index=True
            )
            self._write_sheet(SHEET_LEDGER, ledger_df)
        except Exception:
            pass  # Audit log failure must never block the main write


# ══════════════════════════════════════════════════════════════════════════════
# OpenYantra — public API (READ + write-request only)
# ══════════════════════════════════════════════════════════════════════════════

class OpenYantra:
    """
    OpenYantra — public interface for all agents.

    READ operations: all agents may call freely.
    WRITE operations: agents call request_write() — routed through LedgerAgent.
    Direct file writes are prohibited.

    Usage:
        mem = OpenYantra("~/uam/chitrapat.ods", agent_name="Claude")

        # Session start
        context = mem.load_session_context()

        # Write via LedgerAgent
        receipt = mem.request_write(WriteRequest(
            requesting_agent = "Claude",
            sheet            = SHEET_PROJECTS,
            operation        = "add",
            fields           = {"Project": "UAM v2", "Status": "Active"},
            confidence       = "High",
            source           = "User-stated",
        ))

        # Session end
        mem.log_session(topics=["UAM v2 design"], decisions=["Switch to ODS"])
    """

    def __init__(self, path: str | Path, agent_name: str = "Agent"):
        self.path       = Path(path).expanduser()
        self.agent_name = agent_name
        self._queue     = WriteQueue(self.path.parent / "sanchitta.json")
        self._ledger    = LedgerAgent(self.path, self._queue)

        # Replay any pending writes from a previous crashed session
        replayed = self._ledger.replay_queue()
        if replayed:
            print(f"[OpenYantra] Replayed {replayed} queued write(s) from previous session.")

    # ── Bootstrap ──────────────────────────────────────────────────────────────

    def bootstrap(self, user_name: str = "", occupation: str = "",
                  location: str = ""):
        """
        Create a new UAM .ods file from the standard schema.
        Safe to call even if file already exists (skips if present).
        """
        if self.path.exists():
            print(f"[OpenYantra] Memory file already exists at {self.path}. Skipping.")
            return

        self.path.parent.mkdir(parents=True, exist_ok=True)
        _build_ods_template(str(self.path))

        if any([user_name, occupation, location]):
            identity_updates = {
                "Preferred Name": user_name,
                "Occupation":     occupation,
                "Location":       location,
            }
            for attr, val in identity_updates.items():
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
            topics      = ["UAM bootstrap"],
            decisions   = ["Memory file created — .ods format (ISO/IEC 26300)"],
            new_memory  = [f"Identity: {user_name}" if user_name else "Identity stub"],
        )
        print(f"[OpenYantra] Memory file created at {self.path}")
        print(f"[OpenYantra] Open with LibreOffice Calc, OnlyOffice, or Collabora.")

    # ── Write interface — ALL writes go through here ───────────────────────────

    def request_write(self, req: WriteRequest) -> dict:
        """
        Submit a write request to LedgerAgent.
        This is the ONLY way any agent may write to the memory file.
        Returns a receipt dict: {status, request_id, signature, ...}
        """
        return self._ledger.submit(req)

    # ── Convenience write helpers (wrap request_write) ─────────────────────────

    def flush_open_loop(self, topic: str, context: str,
                        priority: str = "Medium",
                        related_project: str = "") -> dict:
        """Flush an unresolved thread to Open Loops before compaction."""
        return self.request_write(WriteRequest(
            requesting_agent = self.agent_name,
            sheet            = SHEET_OPEN_LOOPS,
            operation        = "add",
            fields           = {
                "Topic":                      topic,
                "Context / What's Unresolved": context,
                "Opened":                     TODAY,
                "Priority":                   priority,
                "Related Project":            related_project,
                "Resolved?":                  "No",
                "Resolution":                 "",
            },
            confidence = "High",
            source     = "Agent-observed",
        ))

    def resolve_open_loop(self, topic: str, resolution: str = "") -> dict:
        """Mark an open loop as resolved."""
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
        """Write session summary to Session Log."""
        return self.request_write(WriteRequest(
            requesting_agent = self.agent_name,
            sheet            = SHEET_SESSION_LOG,
            operation        = "add",
            fields           = {
                "Date":                TODAY,
                "Topics Discussed":    "; ".join(topics),
                "Decisions Made":      "; ".join(decisions or []),
                "New Memory Added":    "; ".join(new_memory or []),
                "Open Loops Created":  str(open_loops_created),
                "Agent":               self.agent_name,
                "Notes":               notes,
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
                "Project":          project, "Domain": domain,
                "Status":           status,  "Priority": priority,
                "Key Decision Made": key_decision,
                "Next Step":        next_step, "Notes": notes,
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
                "Task": task, "Project": project, "Priority": priority,
                "Deadline": deadline, "Status": status, "Notes": notes,
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

    # ── Read interface — open to all agents ───────────────────────────────────

    def _read_sheet(self, sheet_name: str) -> list[dict]:
        try:
            df = pd.read_excel(str(self.path), sheet_name=sheet_name,
                               engine="odf", header=0, dtype=str)
            return df.where(pd.notna(df), None).to_dict("records")
        except Exception:
            return []

    def load_session_context(self, agent_name: Optional[str] = None) -> dict:
        """
        Execute the UAM Session Load Sequence.
        Returns structured context ready for system prompt injection.
        All agents may call this freely — read-only.
        """
        agent = agent_name or self.agent_name

        identity_rows = self._read_sheet(SHEET_IDENTITY)
        id_map = {r.get("Attribute"): r.get("Value")
                  for r in identity_rows if r.get("Value")}

        config_rows = self._read_sheet(SHEET_AGENT_CONFIG)
        instructions = [
            r.get("Instruction") for r in config_rows
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
            "identity":          id_map,
            "agent_instructions": instructions,
            "active_projects":   projects,
            "open_loops":        open_loops,
            "active_goals":      goals,
            "pending_tasks":     tasks,
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
            for p in ctx["active_projects"]
        ) or "None"

        loops_line = "; ".join(
            "{} — {}".format(l.get("Topic","?"), l.get("Context / What's Unresolved",""))
            for l in ctx["open_loops"]
        ) or "None"

        goals_line = "; ".join(
            g.get("Goal","") for g in ctx["active_goals"]
        ) or "None"

        tasks_line = "; ".join(
            t.get("Task","") for t in ctx["pending_tasks"]
        ) or "None"

        instructions_line = "\n  ".join(
            str(i) for i in ctx["agent_instructions"]
        ) or "None"

        return f"""[OPENYANTRA CONTEXT — v2 | LedgerAgent-secured]
User: {user_line}
Active Projects: {projects_line}
Open Loops: {loops_line}
Goals: {goals_line}
Pending Tasks: {tasks_line}
Agent Instructions:
  {instructions_line}
[/OPENYANTRA CONTEXT]"""

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

    def get_ledger(self) -> list[dict]:
        """Return the full audit trail from the Ledger sheet. Read-only."""
        return self._read_sheet(SHEET_LEDGER)


# ══════════════════════════════════════════════════════════════════════════════
# ODS template builder
# ══════════════════════════════════════════════════════════════════════════════

def _build_ods_template(path: str):
    """
    Build a blank UAM .ods file with all 12 sheets and correct headers.
    Uses pandas + odf engine — no LibreOffice required.
    """
    sheets = {
        SHEET_INDEX: [
            ["Sheet", "Domain", "Purpose", "Key Columns"],
            ["👤 Identity",    "Who the user is",      "Core identity",          "Attribute · Value · Last Updated"],
            ["🎯 Goals",       "What they want",        "Long/short-term aims",   "Goal · Type · Priority · Status"],
            ["🚀 Projects",    "Active work",           "Work in progress",       "Project · Status · Priority · Next Step"],
            ["👥 People",      "Their world",           "Relationships",          "Name · Relationship · Context · Sentiment"],
            ["💡 Preferences", "Taste and style",       "Habits and preferences", "Category · Preference · Strength"],
            ["🧠 Beliefs",     "What they think",       "Values and worldview",   "Topic · Position · Confidence"],
            ["✅ Tasks",       "What to do",            "Action items",           "Task · Project · Priority · Status"],
            ["🔓 Open Loops",  "Unresolved threads",    "Compaction safety net",  "Topic · Context · Priority · Resolved?"],
            ["📅 Session Log", "What happened",         "Per-session summary",    "Date · Topics · Decisions · Agent"],
            ["⚙️ Agent Config","Agent instructions",    "Per-agent behaviour",    "Agent · Instruction · Priority · Active"],
            ["📒 Ledger",      "Audit trail",           "All writes — immutable", "Timestamp · Agent · Sheet · Signature"],
        ],
        SHEET_IDENTITY: [
            ["Attribute", "Value", "Last Updated", "Notes", "Confidence", "Source"],
            ["Full Name",          "", "", "", "High", "User-stated"],
            ["Preferred Name",     "", "", "", "High", "User-stated"],
            ["Location",           "", "", "City / Region / Country", "High", "User-stated"],
            ["Timezone",           "", "", "e.g. IST, PST", "High", "User-stated"],
            ["Primary Language",   "", "", "", "High", "User-stated"],
            ["Occupation",         "", "", "", "High", "User-stated"],
            ["Industry",           "", "", "", "High", "User-stated"],
            ["Life Stage",         "", "", "e.g. early career, student", "Medium", "Agent-inferred"],
            ["Communication Style","", "", "e.g. direct, casual", "Medium", "Agent-observed"],
            ["Working Hours",      "", "", "e.g. 10am–7pm IST", "Medium", "User-stated"],
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
            ["Name", "Relationship", "Context", "Sentiment", "Last Mentioned",
             "Notes", "Confidence", "Source"],
        ],
        SHEET_PREFERENCES: [
            ["Category", "Preference", "Strength", "Source", "Notes",
             "Confidence", "Last Updated"],
        ],
        SHEET_BELIEFS: [
            ["Topic", "Position", "Confidence", "Domain", "Last Updated",
             "Notes", "Source"],
        ],
        SHEET_TASKS: [
            ["Task", "Project", "Priority", "Deadline", "Status", "Added By",
             "Notes", "Confidence", "Source"],
        ],
        SHEET_OPEN_LOOPS: [
            ["Topic", "Context / What's Unresolved", "Opened", "Priority",
             "Related Project", "Resolved?", "Resolution",
             "Confidence", "Source"],
        ],
        SHEET_SESSION_LOG: [
            ["Date", "Topics Discussed", "Decisions Made", "New Memory Added",
             "Open Loops Created", "Agent", "Notes"],
        ],
        SHEET_AGENT_CONFIG: [
            ["Agent", "Instruction", "Priority", "Active", "Notes"],
            ["ALL",    "Read Projects + Open Loops at session start",         "Critical", "Yes", ""],
            ["ALL",    "Flush open threads to Open Loops before compaction",  "Critical", "Yes", ""],
            ["ALL",    "Submit writes via LedgerAgent only — no direct writes","Critical", "Yes", ""],
            ["ALL",    "Write session summary to Session Log at end",         "High",     "Yes", ""],
            ["Claude", "Match communication style from Preferences sheet",    "High",     "Yes", ""],
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
