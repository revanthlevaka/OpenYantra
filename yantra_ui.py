"""
yantra_ui.py — OpenYantra Browser Dashboard v2.11
Run: yantra ui -> http://localhost:7331

v2.11:
  - Serves the canonical UI/v3/dashboard.html via FileResponse
  - Keeps the v2.10 API surface intact for the rebuilt Briefing Room dashboard
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

try:
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.responses import FileResponse
    import uvicorn
except ImportError:
    print("pip install fastapi uvicorn")
    sys.exit(1)

try:
    from openyantra import (
        OpenYantra,
        WriteRequest,
        SHEET_BELIEFS,
        SHEET_CORRECTIONS,
        SHEET_GOALS,
        SHEET_INBOX,
        SHEET_LEDGER,
        SHEET_OPEN_LOOPS,
        SHEET_PEOPLE,
        SHEET_PREFERENCES,
        SHEET_PROJECTS,
        SHEET_QUARANTINE,
        SHEET_SECURITY_LOG,
        SHEET_SESSION_LOG,
        SHEET_TASKS,
    )
except ImportError:
    print("openyantra.py not found.")
    sys.exit(1)

app = FastAPI(title="OpenYantra", version="2.11", docs_url=None, redoc_url=None)
_oy: OpenYantra | None = None

DASHBOARD_PATH = BASE_DIR / "UI" / "v3" / "dashboard.html"

SHEET_MAP = {
    "projects": SHEET_PROJECTS,
    "tasks": SHEET_TASKS,
    "open_loops": SHEET_OPEN_LOOPS,
    "people": SHEET_PEOPLE,
    "goals": SHEET_GOALS,
    "preferences": SHEET_PREFERENCES,
    "beliefs": SHEET_BELIEFS,
    "session_log": SHEET_SESSION_LOG,
    "inbox": SHEET_INBOX,
    "corrections": SHEET_CORRECTIONS,
    "ledger": SHEET_LEDGER,
    "quarantine": SHEET_QUARANTINE,
    "security_log": SHEET_SECURITY_LOG,
}


def get_oy() -> OpenYantra:
    if _oy is None:
        raise HTTPException(500, "OpenYantra UI not initialised")
    return _oy


def get_dashboard_path() -> Path:
    if not DASHBOARD_PATH.exists():
        raise HTTPException(
            500,
            f"Dashboard file not found at {DASHBOARD_PATH}. Phase 1 output is missing.",
        )
    return DASHBOARD_PATH


@app.get("/")
async def root() -> FileResponse:
    return FileResponse(get_dashboard_path(), media_type="text/html")


@app.get("/api/health")
async def api_health():
    return get_oy().health_check()


@app.get("/api/sheet/{name}")
async def api_sheet(name: str):
    sheet = SHEET_MAP.get(name)
    if not sheet:
        raise HTTPException(404, f"Unknown sheet alias: {name}")
    rows = get_oy()._read_sheet(sheet)
    return {"sheet": sheet, "rows": rows, "count": len(rows)}


@app.post("/api/inbox")
async def api_inbox(req: Request):
    data = await req.json()
    text = data.get("text", "").strip()
    if not text:
        raise HTTPException(400, "text required")
    return get_oy().inbox(text, importance=int(data.get("importance", 5)))


@app.post("/api/inbox/route")
async def api_route():
    routing = get_oy().route_inbox(dry_run=False)
    return {"routed": sum(1 for row in routing if row.get("routed")), "decisions": routing}


@app.post("/api/corrections/review")
async def api_review(req: Request):
    data = await req.json()
    index = int(data.get("index", 0))
    decision = data.get("decision", "Rejected")
    oy = get_oy()
    corrections = [
        row for row in oy._read_sheet(SHEET_CORRECTIONS) if row.get("Status") == "Pending"
    ]
    if index >= len(corrections):
        raise HTTPException(404, "Pending correction not found")

    correction = corrections[index]
    oy.request_write(
        WriteRequest(
            "Yantra-UI",
            SHEET_CORRECTIONS,
            "update",
            {
                "Status": decision,
                "Reviewed By": "User",
                "Reviewed At": datetime.utcnow().isoformat(timespec="seconds"),
            },
            row_identifier=str(correction.get("Target Sheet", ""))[:50],
            confidence="High",
            source="User-stated",
            importance=8,
        )
    )

    if decision == "Approved":
        target_sheet = correction.get("Target Sheet", "")
        field = correction.get("Field", "")
        proposed_value = correction.get("Proposed Value", "")
        row_identifier = correction.get("Row Identifier", "")
        if target_sheet and field and row_identifier:
            oy.request_write(
                WriteRequest(
                    "Chitragupta",
                    target_sheet,
                    "update",
                    {field: proposed_value},
                    row_identifier=row_identifier,
                    confidence="High",
                    source="User-stated",
                    importance=8,
                )
            )

    return {"status": "ok", "decision": decision}


@app.post("/api/loops/{topic}/resolve")
async def api_resolve_loop(topic: str, req: Request):
    data = await req.json()
    return get_oy().resolve_open_loop(topic, data.get("resolution", "Resolved via UI"))


@app.post("/api/tasks/complete")
async def api_complete_task(req: Request):
    data = await req.json()
    task = data.get("task", "")
    return get_oy().request_write(
        WriteRequest(
            "Yantra-UI",
            SHEET_TASKS,
            "update",
            {"Status": "Done"},
            row_identifier=task,
            confidence="High",
            source="User-stated",
            importance=7,
        )
    )


@app.post("/api/security/scan")
async def api_security_scan():
    return get_oy().security_scan()


@app.post("/api/security/quarantine/release")
async def api_release_quarantine(req: Request):
    data = await req.json()
    return get_oy().release_quarantine(data.get("request_id", ""))


@app.get("/api/stats")
async def api_stats():
    return get_oy().stats()


@app.get("/api/morning")
async def api_morning():
    oy = get_oy()
    brief = oy.morning_brief(format="markdown")
    stats = oy.stats()
    return {
        "brief": brief,
        "streak": stats.get("writes_last_7_days", 0),
        "loops": stats.get("open_loops_total", 0),
        "inbox": stats.get("chitrapat_size_kb", 0),
    }


@app.get("/api/context/markdown")
async def api_context_markdown():
    markdown = get_oy().build_context_markdown()
    return {"markdown": markdown, "length": len(markdown)}


@app.post("/api/context/copy")
async def api_context_copy():
    markdown = get_oy().build_context_markdown()
    return {"markdown": markdown, "status": "ready"}


@app.get("/api/security/trust/{agent_name}")
async def api_trust(agent_name: str):
    return {"agent": agent_name, "trust_tier": get_oy().get_trust_tier(agent_name)}


def main():
    parser = argparse.ArgumentParser(description="OpenYantra Dashboard v2.11")
    parser.add_argument(
        "--file", "-f", default=str(Path.home() / "openyantra" / "chitrapat.ods")
    )
    parser.add_argument("--port", "-p", type=int, default=7331)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()

    global _oy
    path = Path(args.file).expanduser()
    if not path.exists():
        print("[OpenYantra] Chitrapat not found. Run: yantra bootstrap")
        sys.exit(1)

    if not DASHBOARD_PATH.exists():
        print(f"[OpenYantra] Dashboard file missing: {DASHBOARD_PATH}")
        sys.exit(1)

    _oy = OpenYantra(str(path), agent_name="Yantra-UI")
    health = _oy.health_check()
    print(
        f"\n{'='*50}\n  OpenYantra Dashboard v2.11\n"
        f"  -> http://{args.host}:{args.port}\n"
        f"  Loops:{health.get('open_loops', 0)} Inbox:{health.get('inbox_pending', 0)}\n"
        f"{'='*50}\n"
    )
    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
