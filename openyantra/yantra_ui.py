"""
yantra_ui.py -- OpenYantra Browser Dashboard v4.1.0
Run: yantra ui -> http://localhost:7331

v4.1.0:
  - Serves UI/v4/dashboard.html (Briefing Room) via FileResponse
  - /api/oracle endpoint wired to oracle-card
  - /api/export endpoint
  - 13 tabs: Today, Inbox, Loops, Projects, Oracle, Review, Timeline, Security, Ledger, Health, Memories, Hierarchy, Graph
"""


from __future__ import annotations
import argparse, sys, json
from datetime import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
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

from openyantra.cognitive_db import CognitiveMemoryStore
import secrets
from openyantra.yantra_passkey import (
    make_registration_options,
    check_registration_response,
    make_authentication_options,
    check_authentication_response
)

app = FastAPI(title="OpenYantra", version="5.0.0", docs_url=None, redoc_url=None)
_oy = None
_cog_store = None

active_challenges: dict[str, str] = {}
authenticated_sessions: set[str] = set()

def get_oy() -> OpenYantra:
    if _oy is None: raise HTTPException(500, "Not initialised")
    return _oy

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
    "oauthClientSecret": "",
    "passkeyEnabled": False,
    "passkeys": [],
    "embedder": "auto",
    "sutra_weights": {
        "semantic": 0.4,
        "recency": 0.3,
        "importance": 0.2,
        "relation": 0.1
    }
}

def get_settings_data() -> dict:
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
            return DEFAULT_SETTINGS.copy()
    return DEFAULT_SETTINGS.copy()

@app.middleware("http")
async def check_auth_middleware(request: Request, call_next):
    path = request.url.path
    if path.startswith("/api") and not (
        path == "/api/passkey/status" or
        path == "/api/passkey/login/options" or
        path == "/api/passkey/login/verify" or
        path == "/api/health"
    ):
        settings = get_settings_data()
        if settings.get("passkeyEnabled", False):
            session_token = request.cookies.get("yantra_session")
            if not session_token or session_token not in authenticated_sessions:
                from fastapi.responses import JSONResponse
                return JSONResponse(status_code=401, content={"error": "Unauthorized: Passkey verification required"})
                
    return await call_next(request)

def get_cog_store() -> CognitiveMemoryStore:
    global _cog_store
    if _cog_store is None:
        _cog_store = CognitiveMemoryStore()
    return _cog_store

# Dashboard served from UI/v4/dashboard.html
_DASHBOARD = Path(__file__).parent.parent / "UI" / "v4" / "dashboard.html"

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
    oy = get_oy()
    # v5.0.0: prefer SQLite via db_engine for 2ms reads
    if getattr(oy, 'db_engine', None):
        from openyantra.yantra_sqlite import SHEET_TABLE_MAP
        table = SHEET_TABLE_MAP.get(sheet)
        if table:
            db_rows = oy.db_engine.read(table)
            # Convert to Title Case keys and boolean fields for frontend compat
            title_rows = []
            for r in db_rows:
                tr = {}
                for k, v in r.items():
                    if k in ('id', 'last_updated', 'added_by'):
                        continue
                    tk = k.replace('_', ' ').title()
                    # Boolean field conversions
                    if k == 'resolved':
                        v = 'Yes' if v else 'No'
                    elif k == 'routed':
                        v = 'Yes' if v else 'No'
                    elif k == 'active':
                        v = 'Yes' if v else 'No'
                    tr[tk] = v
                title_rows.append(tr)
            return {"sheet": sheet, "rows": title_rows, "count": len(title_rows)}
    rows = oy._read_sheet(sheet)
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
async def get_cognitive_memories(query: str = None, type: str = None, tags: str = None, start_date: str = None, end_date: str = None):
    tags_list = None
    if tags:
        tags_list = [t.strip() for t in tags.split(",") if t.strip()]
    return {"memories": get_cog_store().search(query=query, type_val=type, tags=tags_list, start_date=start_date, end_date=end_date)}

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


@app.get("/api/settings")
async def get_settings():
    return get_settings_data()

@app.post("/api/settings")
async def post_settings(req: Request):
    d = await req.json()
    sf = get_settings_file()
    current = get_settings_data()
    # Update current settings with only what's provided in request
    for k in DEFAULT_SETTINGS.keys():
        if k in d:
            current[k] = d[k]
    try:
        sf.parent.mkdir(parents=True, exist_ok=True)
        with open(sf, "w") as f:
            json.dump(current, f, indent=2)
        
        # Re-initialize VidyaKosha in _oy to apply the new embedder preference
        oy = get_oy()
        try:
            from openyantra.core import _VIDYAKOSHA_AVAILABLE
            if _VIDYAKOSHA_AVAILABLE:
                from vidyakosha import VidyaKosha as _VK
                oy._vidyakosha = _VK(str(Path(oy.path).parent), embedder_pref=current.get("embedder", "auto"))
                oy._vidyakosha.sync(oy.path)
        except Exception as e:
            print(f"[Yantra-UI] Error updating VidyaKosha: {e}")

        return {"status": "ok", "settings": current}
    except Exception as e:
        raise HTTPException(500, f"Failed to save settings: {e}")

# Passkey Endpoints

@app.get("/api/passkey/status")
async def get_passkey_status(req: Request):
    settings = get_settings_data()
    session_token = req.cookies.get("yantra_session")
    is_authenticated = False
    if session_token and session_token in authenticated_sessions:
        is_authenticated = True
    return {
        "passkeyEnabled": settings.get("passkeyEnabled", False),
        "hasPasskeys": len(settings.get("passkeys", [])) > 0,
        "authenticated": is_authenticated
    }

@app.post("/api/passkey/register/options")
async def post_register_options(req: Request):
    try:
        d = await req.json()
    except Exception:
        d = {}
    label = d.get("label", "My Authenticator")
    
    settings = get_settings_data()
    rp_id = req.url.hostname or "localhost"
    username = "OpenYantra User"
    existing_creds = settings.get("passkeys", [])
    
    try:
        options = make_registration_options(
            username=username,
            rp_id=rp_id,
            existing_credentials=existing_creds
        )
        
        state_id = secrets.token_hex(16)
        active_challenges[state_id] = options["challenge"]
        
        return {
            "options": options,
            "state_id": state_id
        }
    except Exception as e:
        raise HTTPException(400, f"Failed to generate registration options: {e}")

@app.post("/api/passkey/register/verify")
async def post_register_verify(req: Request):
    d = await req.json()
    state_id = d.get("state_id")
    credential_data = d.get("credential")
    label = d.get("label", "My Authenticator")
    
    if not state_id or not credential_data:
        raise HTTPException(400, "Missing state_id or credential data")
        
    expected_challenge = active_challenges.pop(state_id, None)
    if not expected_challenge:
        raise HTTPException(400, "Invalid or expired session challenge")
        
    rp_id = req.url.hostname or "localhost"
    origin = f"{req.url.scheme}://{req.url.netloc}"
    
    try:
        verification = check_registration_response(
            credential_data=credential_data,
            expected_challenge=expected_challenge,
            expected_rp_id=rp_id,
            expected_origin=origin
        )
        
        sf = get_settings_file()
        settings = get_settings_data()
        
        new_passkey = {
            "label": label,
            "credential_id": verification["credential_id"],
            "public_key": verification["public_key"],
            "sign_count": verification["sign_count"],
            "added_at": datetime.now().isoformat()
        }
        
        if "passkeys" not in settings:
            settings["passkeys"] = []
        settings["passkeys"].append(new_passkey)
        
        settings["passkeyEnabled"] = True
        
        with open(sf, "w") as f:
            json.dump(settings, f, indent=2)
            
        session_token = secrets.token_hex(32)
        authenticated_sessions.add(session_token)
        
        response = JSONResponse(content={"status": "ok", "settings": settings})
        response.set_cookie(
            key="yantra_session",
            value=session_token,
            httponly=True,
            samesite="strict",
            max_age=3600 * 24 * 30  # 30 days
        )
        return response
    except Exception as e:
        raise HTTPException(400, f"Registration verification failed: {e}")

@app.post("/api/passkey/login/options")
async def post_login_options(req: Request):
    settings = get_settings_data()
    rp_id = req.url.hostname or "localhost"
    
    registered_creds = settings.get("passkeys", [])
    if not registered_creds:
        raise HTTPException(400, "No passkeys registered on this system")
        
    try:
        options = make_authentication_options(
            rp_id=rp_id,
            registered_credentials=registered_creds
        )
        
        state_id = secrets.token_hex(16)
        active_challenges[state_id] = options["challenge"]
        
        return {
            "options": options,
            "state_id": state_id
        }
    except Exception as e:
        raise HTTPException(400, f"Failed to generate login options: {e}")

@app.post("/api/passkey/login/verify")
async def post_login_verify(req: Request):
    d = await req.json()
    state_id = d.get("state_id")
    credential_data = d.get("credential")
    
    if not state_id or not credential_data:
        raise HTTPException(400, "Missing state_id or credential data")
        
    expected_challenge = active_challenges.pop(state_id, None)
    if not expected_challenge:
        raise HTTPException(400, "Invalid or expired session challenge")
        
    rp_id = req.url.hostname or "localhost"
    origin = f"{req.url.scheme}://{req.url.netloc}"
    
    settings = get_settings_data()
    registered_creds = settings.get("passkeys", [])
    
    cred_id = credential_data.get("id")
    matching_cred = None
    matching_index = -1
    for i, cred in enumerate(registered_creds):
        if cred["credential_id"] == cred_id:
            matching_cred = cred
            matching_index = i
            break
            
    if not matching_cred:
        raise HTTPException(400, "Credential not recognized")
        
    try:
        verification = check_authentication_response(
            credential_data=credential_data,
            expected_challenge=expected_challenge,
            expected_rp_id=rp_id,
            expected_origin=origin,
            public_key_b64=matching_cred["public_key"],
            current_sign_count=matching_cred.get("sign_count", 0)
        )
        
        settings["passkeys"][matching_index]["sign_count"] = verification["new_sign_count"]
        
        sf = get_settings_file()
        with open(sf, "w") as f:
            json.dump(settings, f, indent=2)
            
        session_token = secrets.token_hex(32)
        authenticated_sessions.add(session_token)
        
        response = JSONResponse(content={"status": "ok"})
        response.set_cookie(
            key="yantra_session",
            value=session_token,
            httponly=True,
            samesite="strict",
            max_age=3600 * 24 * 30  # 30 days
        )
        return response
    except Exception as e:
        raise HTTPException(400, f"Login verification failed: {e}")

@app.post("/api/passkey/logout")
async def post_logout(req: Request):
    session_token = req.cookies.get("yantra_session")
    if session_token in authenticated_sessions:
        authenticated_sessions.remove(session_token)
        
    response = JSONResponse(content={"status": "ok"})
    response.delete_cookie(key="yantra_session")
    return response

@app.post("/api/passkey/delete")
async def post_delete_passkey(req: Request):
    d = await req.json()
    cred_id = d.get("credential_id")
    if not cred_id:
        raise HTTPException(400, "credential_id is required")
        
    settings = get_settings_data()
    passkeys = settings.get("passkeys", [])
    
    new_passkeys = [pk for pk in passkeys if pk["credential_id"] != cred_id]
    
    settings["passkeys"] = new_passkeys
    if not new_passkeys:
        settings["passkeyEnabled"] = False
        
    sf = get_settings_file()
    with open(sf, "w") as f:
        json.dump(settings, f, indent=2)
        
    return {"status": "ok", "settings": settings}


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


@app.post("/api/context/compile")
async def api_context_compile(req: Request):
    d = await req.json()
    query = d.get("query")
    budget = int(d.get("budget", 4096))
    mode = d.get("mode", "default")
    sections = d.get("sections")
    
    oy = get_oy()
    res = oy.compile_context(
        query_text=query,
        budget=budget,
        mode=mode,
        sections=sections
    )
    return res


@app.get("/api/context/preview")
async def api_context_preview(
    query: str | None = None,
    budget: int = 4096,
    mode: str = "default",
    sections: str | None = None
):
    oy = get_oy()
    sections_list = None
    if sections:
        sections_list = [s.strip() for s in sections.split(",") if s.strip()]
    res = oy.compile_context(
        query_text=query,
        budget=budget,
        mode=mode,
        sections=sections_list
    )
    return res


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


# ── Graph API (Sutradhar) ─────────────────────────────────────────────────────

@app.get("/api/graph/edges")
async def api_graph_edges(source_type: str = None, source_id: str = None, target_type: str = None):
    oy = get_oy()
    if not getattr(oy, 'db_engine', None):
        return {"edges": [], "error": "db_engine not available"}
    edges = oy.db_engine.get_edges(source_type=source_type, source_id=source_id, target_type=target_type)
    return {"edges": edges, "count": len(edges)}

@app.post("/api/graph/edge")
async def api_graph_add_edge(req: Request):
    d = await req.json()
    oy = get_oy()
    if not getattr(oy, 'db_engine', None):
        raise HTTPException(500, "db_engine not available")
    result = oy.db_engine.add_edge(
        d.get("source_type", ""), d.get("source_id", ""),
        d.get("target_type", ""), d.get("target_id", ""),
        d.get("edge_type", "related_to")
    )
    return result

@app.delete("/api/graph/edge/{edge_id}")
async def api_graph_delete_edge(edge_id: int):
    oy = get_oy()
    if not getattr(oy, 'db_engine', None):
        raise HTTPException(500, "db_engine not available")
    success = oy.db_engine.delete_edge(edge_id)
    return {"deleted": success}

@app.get("/api/graph/traverse")
async def api_graph_traverse(source_type: str, source_id: str, max_hops: int = 3):
    oy = get_oy()
    if not getattr(oy, 'db_engine', None):
        return {"nodes": [], "error": "db_engine not available"}
    nodes = oy.db_engine.traverse(source_type, source_id, max_hops)
    return {"nodes": nodes, "source_type": source_type, "source_id": source_id}


def main():
    parser = argparse.ArgumentParser(description="OpenYantra Dashboard v5.0.0")
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
    print(f"\n{'='*50}\n  OpenYantra Dashboard v5.0.0\n  → http://{args.host}:{args.port}\n  Loops:{h.get('open_loops',0)} Inbox:{h.get('inbox_pending',0)}\n{'='*50}\n")
    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")

if __name__ == "__main__":
    main()
