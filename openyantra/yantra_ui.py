"""
yantra_ui.py -- OpenYantra Browser Dashboard v3.0.1
Run: yantra ui -> http://localhost:7331

v3.0.1:
  - Serves UI/v3/dashboard.html (Briefing Room) via FileResponse
  - /api/oracle endpoint wired to oracle-card
  - /api/export endpoint
  - 13 tabs: Today, Inbox, Loops, Projects, Oracle, Review, Timeline, Security, Ledger, Health, Memories, Hierarchy, Graph
"""


from __future__ import annotations
import argparse, sys, json
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

from cognitive_db import CognitiveMemoryStore

app = FastAPI(title="OpenYantra", version="3.0.1", docs_url=None, redoc_url=None)
_oy = None
_cog_store = None

def get_oy() -> OpenYantra:
    if _oy is None: raise HTTPException(500, "Not initialised")
    return _oy

def get_cog_store() -> CognitiveMemoryStore:
    global _cog_store
    if _cog_store is None:
        _cog_store = CognitiveMemoryStore()
    return _cog_store

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


@app.get("/api/cognitive/memories")
async def get_cognitive_memories(query: str = None, type: str = None, tags: str = None):
    tags_list = None
    if tags:
        tags_list = [t.strip() for t in tags.split(",") if t.strip()]
    return {"memories": get_cog_store().search(query=query, type_val=type, tags=tags_list)}

@app.post("/api/cognitive/write")
async def post_cognitive_write(req: Request):
    d = await req.json()
    key = d.get("key")
    type_val = d.get("type")
    agent = d.get("agent")
    content = d.get("content")
    tags = d.get("tags", [])
    if not key or not type_val or not agent:
        raise HTTPException(400, "key, type, and agent are required")
    try:
        res = get_cog_store().write(key, type_val, agent, content, tags)
        return res
    except ValueError as e:
        raise HTTPException(400, str(e))

@app.post("/api/cognitive/delete")
async def post_cognitive_delete(req: Request):
    d = await req.json()
    key = d.get("key")
    if not key:
        raise HTTPException(400, "key is required")
    success = get_cog_store().delete(key)
    return {"success": success}

@app.get("/api/cognitive/stats")
async def get_cognitive_stats():
    return get_cog_store().stats()

@app.get("/api/cognitive/hierarchy")
async def get_cognitive_hierarchy():
    return get_cog_store().get_hierarchy()

@app.post("/api/cognitive/hierarchy/set-parent")
async def post_cognitive_set_parent(req: Request):
    d = await req.json()
    agent = d.get("agent")
    parent = d.get("parent")
    if not agent:
        raise HTTPException(400, "agent is required")
    get_cog_store().set_agent_parent(agent, parent)
    return {"status": "ok"}

@app.post("/api/cognitive/agent/add")
async def post_cognitive_add_agent(req: Request):
    d = await req.json()
    name = d.get("name")
    system_prompt = d.get("system_prompt", "")
    parent = d.get("parent")
    if not name or not name.strip():
        raise HTTPException(400, "name is required")
    name = name.strip()
    key = f"{name}-agent-profile"
    get_cog_store().write(
        key=key,
        type_val="context",
        agent=name,
        content=system_prompt,
        tags=["agent-profile"]
    )
    if parent:
        get_cog_store().set_agent_parent(name, parent)
    return {"status": "ok", "agent": name}


def get_settings_file() -> Path:
    oy = get_oy()
    return Path(oy.path).parent / "settings.json"

DEFAULT_SETTINGS = {
    "fontSize": "11px",
    "aiProvider": "local",
    "aiModelName": "llama3",
    "localEndpoint": "http://localhost:11434/v1",
    "openaiKey": "",
    "anthropicKey": "",
    "geminiKey": "",
    "oauthClientId": "",
    "oauthClientSecret": ""
}

@app.get("/api/settings")
async def get_settings():
    sf = get_settings_file()
    if sf.exists():
        try:
            with open(sf, "r") as f:
                data = json.load(f)
            # Ensure all keys exist
            for k, v in DEFAULT_SETTINGS.items():
                if k not in data:
                    data[k] = v
            return data
        except Exception:
            return DEFAULT_SETTINGS
    return DEFAULT_SETTINGS

@app.post("/api/settings")
async def post_settings(req: Request):
    d = await req.json()
    sf = get_settings_file()
    settings = {}
    for k, v in DEFAULT_SETTINGS.items():
        settings[k] = d.get(k, v)
    try:
        sf.parent.mkdir(parents=True, exist_ok=True)
        with open(sf, "w") as f:
            json.dump(settings, f, indent=2)
        return {"status": "ok", "settings": settings}
    except Exception as e:
        raise HTTPException(500, f"Failed to save settings: {e}")


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


@app.get("/api/mcp-config")
async def api_mcp_config():
    import sys
    oy = get_oy()
    mcp_path = Path(__file__).parent / "cognitive_mcp.py"
    return {
        "mcp_script_path": str(mcp_path.resolve()),
        "chitrapat_path": str(Path(oy.path).resolve()),
        "python_executable": sys.executable
    }


def main():
    parser = argparse.ArgumentParser(description="OpenYantra Dashboard v3.0.1")
    parser.add_argument("--file","-f",default=str(Path.home()/"openyantra"/"chitrapat.ods"))
    parser.add_argument("--port","-p",type=int,default=7331)
    parser.add_argument("--host",default="127.0.0.1")
    args = parser.parse_args()
    global _oy, _cog_store
    path = Path(args.file).expanduser()
    if not path.exists():
        print("[OpenYantra] Chitrapat not found. Run: yantra bootstrap"); sys.exit(1)
    _oy = OpenYantra(str(path), agent_name="Yantra-UI")
    _cog_store = CognitiveMemoryStore(path.parent / "cognitive_memories.json")
    h = _oy.health_check()
    print(f"\n{'='*50}\n  OpenYantra Dashboard v3.0.1\n  → http://{args.host}:{args.port}\n  Loops:{h.get('open_loops',0)} Inbox:{h.get('inbox_pending',0)}\n{'='*50}\n")
    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")

if __name__ == "__main__":
    main()
