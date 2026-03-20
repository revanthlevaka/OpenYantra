"""
yantra_ui.py -- OpenYantra Browser Dashboard v2.12
Run: yantra ui -> http://localhost:7331

v2.12:
  - Serves UI/v3/dashboard.html (Briefing Room) via FileResponse
  - /api/oracle endpoint wired to oracle-card
  - /api/export endpoint
  - 10 tabs: Today, Inbox, Loops, Projects, Oracle, Review, Timeline, Security, Ledger, Health
"""


from __future__ import annotations
import argparse, sys
from datetime import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.responses import HTMLResponse, FileResponse
    import uvicorn
except ImportError:
    print("pip install fastapi uvicorn"); sys.exit(1)

try:
    from openyantra import (
        OpenYantra, WriteRequest,
        SHEET_PROJECTS, SHEET_TASKS, SHEET_OPEN_LOOPS,
        SHEET_PEOPLE, SHEET_GOALS, SHEET_PREFERENCES,
        SHEET_BELIEFS, SHEET_SESSION_LOG, SHEET_INBOX,
        SHEET_CORRECTIONS, SHEET_LEDGER,
        SHEET_QUARANTINE, SHEET_SECURITY_LOG,
    )
except ImportError:
    print("openyantra.py not found."); sys.exit(1)

app = FastAPI(title="OpenYantra", version="2.12", docs_url=None, redoc_url=None)
_oy = None

def get_oy() -> OpenYantra:
    if _oy is None: raise HTTPException(500, "Not initialised")
    return _oy

# Dashboard served from UI/v3/dashboard.html
_DASHBOARD = Path(__file__).parent / "UI" / "v3" / "dashboard.html"

@app.get("/", response_class=HTMLResponse)
async def root():
    if _DASHBOARD.exists():
        return FileResponse(str(_DASHBOARD))
    return HTMLResponse("<h1>OpenYantra</h1><p>Dashboard not found. Run yantra bootstrap first.</p>")

@app.get("/api/health")
async def api_health(): return get_oy().health_check()

@app.get("/api/sheet/{name}")
async def api_sheet(name: str):
    m = {"projects":SHEET_PROJECTS,"tasks":SHEET_TASKS,"open_loops":SHEET_OPEN_LOOPS,
         "people":SHEET_PEOPLE,"goals":SHEET_GOALS,"preferences":SHEET_PREFERENCES,
         "beliefs":SHEET_BELIEFS,"session_log":SHEET_SESSION_LOG,"inbox":SHEET_INBOX,
         "corrections":SHEET_CORRECTIONS,"ledger":SHEET_LEDGER,
         "quarantine":SHEET_QUARANTINE,"security_log":SHEET_SECURITY_LOG}
    sheet = m.get(name)
    if not sheet: raise HTTPException(404, f"Unknown: {name}")
    rows = get_oy()._read_sheet(sheet)
    return {"sheet": sheet, "rows": rows, "count": len(rows)}

@app.post("/api/inbox")
async def api_inbox(req: Request):
    d = await req.json()
    t = d.get("text","").strip()
    if not t: raise HTTPException(400, "text required")
    return get_oy().inbox(t, importance=int(d.get("importance",5)))

@app.post("/api/inbox/route")
async def api_route():
    routing = get_oy().route_inbox(dry_run=False)
    return {"routed": sum(1 for r in routing if r.get("routed")), "decisions": routing}

@app.post("/api/corrections/review")
async def api_review(req: Request):
    d = await req.json(); idx = d.get("index",0); decision = d.get("decision","Rejected")
    oy = get_oy()
    corrections = [r for r in oy._read_sheet(SHEET_CORRECTIONS) if r.get("Status")=="Pending"]
    if idx >= len(corrections): raise HTTPException(404,"Not found")
    c = corrections[idx]
    oy.request_write(WriteRequest("Yantra-UI",SHEET_CORRECTIONS,"update",
        {"Status":decision,"Reviewed By":"User","Reviewed At":datetime.utcnow().isoformat(timespec="seconds")},
        row_identifier=str(c.get("Target Sheet",""))[:50],
        confidence="High",source="User-stated",importance=8))
    if decision=="Approved":
        t,f,v,r=c.get("Target Sheet",""),c.get("Field",""),c.get("Proposed Value",""),c.get("Row Identifier","")
        if t and f and r:
            oy.request_write(WriteRequest("Chitragupta",t,"update",{f:v},
                row_identifier=r,confidence="High",source="User-stated",importance=8))
    return {"status":"ok","decision":decision}

@app.post("/api/loops/{topic}/resolve")
async def api_resolve_loop(topic: str, req: Request):
    d = await req.json()
    return get_oy().resolve_open_loop(topic, d.get("resolution","Resolved via UI"))

@app.post("/api/tasks/complete")
async def api_complete_task(req: Request):
    d = await req.json(); task = d.get("task","")
    return get_oy().request_write(WriteRequest(
        "Yantra-UI",SHEET_TASKS,"update",{"Status":"Done"},
        row_identifier=task,confidence="High",source="User-stated",importance=7))

@app.post("/api/security/scan")
async def api_sec_scan(): return get_oy().security_scan()

@app.post("/api/security/quarantine/release")
async def api_release_q(req: Request):
    d = await req.json()
    return get_oy().release_quarantine(d.get("request_id",""))

@app.get("/api/stats")
async def api_stats():
    return get_oy().stats()


@app.get("/api/morning")
async def api_morning():
    oy = get_oy()
    brief = oy.morning_brief(format="markdown")
    stats = oy.stats()
    return {
        "brief":  brief,
        "streak": stats.get("writes_last_7_days", 0),
        "loops":  stats.get("open_loops_total", 0),
        "inbox":  stats.get("chitrapat_size_kb", 0),
    }


@app.get("/api/context/markdown")
async def api_context_markdown():
    oy = get_oy()
    md = oy.build_context_markdown()
    return {"markdown": md, "length": len(md)}


@app.post("/api/context/copy")
async def api_context_copy():
    oy = get_oy()
    md = oy.build_context_markdown()
    return {"markdown": md, "status": "ready"}


@app.get("/api/security/trust/{agent_name}")
async def api_trust(agent_name: str):
    return {"agent":agent_name,"trust_tier":get_oy().get_trust_tier(agent_name)}


@app.get("/api/oracle")
async def api_oracle():
    """Oracle cross-reference engine -- v2.12. Populates oracle-card in Today tab."""
    oy = get_oy()
    try:
        insights = oy.oracle(max_insights=8)
        return {"insights": insights, "count": len(insights)}
    except Exception as e:
        return {"insights": [], "count": 0, "error": str(e)}


@app.get("/api/export")
async def api_export(sheet: str = "", fmt: str = "markdown", since: str = ""):
    """Export memory to markdown or JSON -- v2.12."""
    oy = get_oy()
    try:
        result = oy.export(
            sheet=sheet or None,
            fmt=fmt,
            since=since or None,
        )
        return {"content": result, "format": fmt, "sheet": sheet or "all"}
    except Exception as e:
        return {"error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="OpenYantra Dashboard v2.12")
    parser.add_argument("--file","-f",default=str(Path.home()/"openyantra"/"chitrapat.ods"))
    parser.add_argument("--port","-p",type=int,default=7331)
    parser.add_argument("--host",default="127.0.0.1")
    args = parser.parse_args()
    global _oy
    path = Path(args.file).expanduser()
    if not path.exists():
        print("[OpenYantra] Chitrapat not found. Run: yantra bootstrap"); sys.exit(1)
    _oy = OpenYantra(str(path), agent_name="Yantra-UI")
    h = _oy.health_check()
    print(f"\n{'='*50}\n  OpenYantra Dashboard v2.12\n  → http://{args.host}:{args.port}\n  Loops:{h.get('open_loops',0)} Inbox:{h.get('inbox_pending',0)}\n{'='*50}\n")
    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")

if __name__ == "__main__":
    main()
