"""
yantra_ui.py — OpenYantra Browser Dashboard
Version: 2.1

A lightweight local web UI for reviewing, correcting, and managing
your Chitrapat without opening LibreOffice.

Usage:
    python yantra_ui.py                          # default port 7331
    python yantra_ui.py --port 8080
    python yantra_ui.py --file ~/my/chitrapat.ods

Then open: http://localhost:7331
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent dir to path for openyantra import
sys.path.insert(0, str(Path(__file__).parent))

try:
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.responses import HTMLResponse, JSONResponse
    import uvicorn
except ImportError:
    print("yantra_ui requires: pip install fastapi uvicorn")
    sys.exit(1)

try:
    from openyantra import OpenYantra, WriteRequest, _build_ods_template
    from openyantra import (SHEET_PROJECTS, SHEET_TASKS, SHEET_OPEN_LOOPS,
                             SHEET_PEOPLE, SHEET_GOALS, SHEET_PREFERENCES,
                             SHEET_BELIEFS, SHEET_SESSION_LOG, SHEET_INBOX,
                             SHEET_CORRECTIONS, SHEET_LEDGER)
except ImportError:
    print("openyantra.py not found. Ensure it's in the same directory.")
    sys.exit(1)

# ── App setup ─────────────────────────────────────────────────────────────────

app  = FastAPI(title="OpenYantra", version="2.1", docs_url=None, redoc_url=None)
_oy: Optional[OpenYantra] = None

def get_oy() -> OpenYantra:
    global _oy
    if _oy is None:
        raise HTTPException(status_code=500, detail="OpenYantra not initialised")
    return _oy

# ── HTML template ─────────────────────────────────────────────────────────────

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>OpenYantra — The Sacred Memory Machine</title>
<style>
  :root {
    --ink:      #0c0812;
    --saffron:  #ff9933;
    --gold:     #d4af37;
    --cream:    #fff8e6;
    --dim:      #b4a078;
    --surface:  #1a1228;
    --surface2: #241832;
    --border:   #3d2a55;
    --green:    #4caf7d;
    --red:      #e05032;
    --blue:     #5b8dd9;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: 'Segoe UI', system-ui, sans-serif;
    background: var(--ink); color: var(--cream);
    min-height: 100vh;
  }
  header {
    background: var(--surface);
    border-bottom: 2px solid var(--saffron);
    padding: 14px 24px;
    display: flex; align-items: center; gap: 16px;
  }
  header h1 { font-size: 1.4rem; color: var(--saffron); }
  header h1 span { color: var(--cream); font-weight: 300; }
  header small { color: var(--dim); font-size: 0.75rem; }
  .badge {
    background: var(--surface2); border: 1px solid var(--border);
    border-radius: 12px; padding: 3px 10px;
    font-size: 0.7rem; color: var(--dim);
  }
  .badge.warn { border-color: var(--saffron); color: var(--saffron); }
  .badge.ok   { border-color: var(--green);   color: var(--green);   }
  nav {
    background: var(--surface2);
    display: flex; gap: 4px; padding: 8px 16px;
    border-bottom: 1px solid var(--border);
    flex-wrap: wrap;
  }
  nav button {
    background: transparent; border: 1px solid var(--border);
    color: var(--dim); padding: 6px 14px; border-radius: 6px;
    cursor: pointer; font-size: 0.82rem; transition: all 0.15s;
  }
  nav button:hover, nav button.active {
    background: var(--surface); border-color: var(--saffron);
    color: var(--saffron);
  }
  main { padding: 20px 24px; max-width: 1200px; }

  /* Dashboard cards */
  .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px,1fr)); gap: 12px; margin-bottom: 24px; }
  .card {
    background: var(--surface2); border: 1px solid var(--border);
    border-radius: 10px; padding: 16px; cursor: pointer;
    transition: border-color 0.15s;
  }
  .card:hover { border-color: var(--saffron); }
  .card .num  { font-size: 2rem; font-weight: 700; color: var(--saffron); }
  .card .lbl  { font-size: 0.78rem; color: var(--dim); margin-top: 4px; }
  .card.warn  { border-color: var(--saffron); }
  .card.alert { border-color: var(--red); }

  /* Tables */
  .section-title {
    font-size: 1rem; color: var(--gold);
    margin: 20px 0 10px; font-weight: 600;
  }
  table { width: 100%; border-collapse: collapse; font-size: 0.82rem; }
  th {
    background: var(--surface2); color: var(--gold);
    padding: 8px 10px; text-align: left; font-weight: 600;
    border-bottom: 1px solid var(--border);
  }
  td {
    padding: 7px 10px; border-bottom: 1px solid var(--border);
    color: var(--cream); max-width: 300px;
    overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  }
  tr:hover td { background: var(--surface2); }
  .tag {
    display: inline-block; padding: 2px 8px; border-radius: 10px;
    font-size: 0.7rem; font-weight: 600;
  }
  .tag-active  { background:#1a3a2a; color: var(--green);   }
  .tag-pending { background:#3a2a1a; color: var(--saffron); }
  .tag-done    { background:#1a2a3a; color: var(--blue);    }
  .tag-high    { background:#3a1a1a; color: var(--red);     }

  /* Actions */
  .btn {
    background: var(--surface); border: 1px solid var(--border);
    color: var(--cream); padding: 6px 14px; border-radius: 6px;
    cursor: pointer; font-size: 0.8rem; transition: all 0.15s;
  }
  .btn:hover { border-color: var(--saffron); color: var(--saffron); }
  .btn-primary {
    background: var(--saffron); color: var(--ink); border: none;
    padding: 8px 18px; border-radius: 6px; font-weight: 600;
    cursor: pointer;
  }
  .btn-danger { border-color: var(--red); color: var(--red); }
  .btn-success { border-color: var(--green); color: var(--green); }

  /* Inbox */
  .inbox-form {
    display: flex; gap: 10px; margin-bottom: 16px; align-items: center;
  }
  .inbox-form input {
    flex: 1; background: var(--surface2); border: 1px solid var(--border);
    color: var(--cream); padding: 9px 14px; border-radius: 6px;
    font-size: 0.9rem;
  }
  .inbox-form input:focus { outline: none; border-color: var(--saffron); }

  /* Health */
  .health-grid {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(220px,1fr));
    gap: 12px; margin-top: 16px;
  }
  .health-item {
    background: var(--surface2); border: 1px solid var(--border);
    border-radius: 8px; padding: 12px 16px;
    display: flex; justify-content: space-between; align-items: center;
  }
  .health-item .key { color: var(--dim); font-size: 0.8rem; }
  .health-item .val { color: var(--cream); font-weight: 600; }
  .health-item .val.warn { color: var(--saffron); }
  .health-item .val.ok   { color: var(--green);   }

  /* Toast */
  #toast {
    position: fixed; bottom: 24px; right: 24px;
    background: var(--surface); border: 1px solid var(--green);
    color: var(--green); padding: 10px 18px; border-radius: 8px;
    font-size: 0.85rem; display: none; z-index: 999;
  }
  .empty { color: var(--dim); text-align: center; padding: 32px; font-size: 0.85rem; }
</style>
</head>
<body>
<header>
  <div>
    <h1>Open<span>Yantra</span></h1>
    <small>The Sacred Memory Machine · v2.1 · Chitragupta-secured</small>
  </div>
  <div id="status-badges" style="margin-left:auto;display:flex;gap:8px"></div>
</header>
<nav>
  <button class="active" onclick="showTab('dashboard')">🏠 Dashboard</button>
  <button onclick="showTab('inbox')">📥 Inbox</button>
  <button onclick="showTab('projects')">🚀 Projects</button>
  <button onclick="showTab('loops')">🔓 Open Loops</button>
  <button onclick="showTab('tasks')">✅ Tasks</button>
  <button onclick="showTab('corrections')">✏️ Corrections</button>
  <button onclick="showTab('ledger')">📒 Ledger</button>
  <button onclick="showTab('health')">💚 Health</button>
  <button onclick="showTab('security')">🔒 Security</button>
</nav>
<main>
  <!-- DASHBOARD -->
  <div id="tab-dashboard">
    <div class="cards" id="stat-cards"></div>
    <div class="section-title">Recent Session Log</div>
    <div id="recent-sessions"></div>
  </div>

  <!-- INBOX -->
  <div id="tab-inbox" style="display:none">
    <div class="section-title">📥 Inbox — Quick Capture</div>
    <div class="inbox-form">
      <input id="inbox-input" placeholder="Capture a thought, task, or observation..." />
      <button class="btn-primary" onclick="submitInbox()">Save to Inbox</button>
    </div>
    <div id="inbox-table"></div>
  </div>

  <!-- PROJECTS -->
  <div id="tab-projects" style="display:none">
    <div class="section-title">🚀 Active Projects (Karma)</div>
    <div id="projects-table"></div>
  </div>

  <!-- OPEN LOOPS -->
  <div id="tab-loops" style="display:none">
    <div class="section-title">🔓 Open Loops (Anishtha)</div>
    <div id="loops-table"></div>
  </div>

  <!-- TASKS -->
  <div id="tab-tasks" style="display:none">
    <div class="section-title">✅ Pending Tasks (Kartavya)</div>
    <div id="tasks-table"></div>
  </div>

  <!-- CORRECTIONS -->
  <div id="tab-corrections" style="display:none">
    <div class="section-title">✏️ Pending Corrections</div>
    <p style="color:var(--dim);font-size:0.8rem;margin-bottom:12px">
      Review agent-proposed edits. Approve to apply, Reject to discard.
    </p>
    <div id="corrections-table"></div>
  </div>

  <!-- LEDGER -->
  <div id="tab-ledger" style="display:none">
    <div class="section-title">📒 Agrasandhanī — Audit Trail</div>
    <div id="ledger-table"></div>
  </div>

  <!-- SECURITY -->
  <div id="tab-security" style="display:none">
    <div class="section-title">🔒 Security — Raksha (रक्षा)</div>
    <p style="color:var(--dim);font-size:0.8rem;margin-bottom:12px">
      Quarantined writes · Threat log · Agent trust levels
    </p>
    <div style="display:flex;gap:10px;margin-bottom:16px">
      <button class="btn-primary" onclick="runSecurityScan()">🔍 Run Full Scan</button>
      <button class="btn" onclick="loadTab('security')">↺ Refresh</button>
    </div>
    <div id="security-scan-result" style="margin-bottom:16px"></div>
    <div class="section-title" style="margin-top:8px">🔒 Quarantined Writes</div>
    <div id="quarantine-table"></div>
    <div class="section-title" style="margin-top:16px">🛡️ Security Log</div>
    <div id="security-log-table"></div>
  </div>

  <!-- HEALTH -->
  <div id="tab-health" style="display:none">
    <div class="section-title">💚 System Health</div>
    <div class="health-grid" id="health-grid"></div>
  </div>
</main>
<div id="toast"></div>

<script>
let currentTab = 'dashboard';

function showTab(name) {
  document.querySelectorAll('[id^="tab-"]').forEach(el => el.style.display = 'none');
  document.getElementById('tab-' + name).style.display = 'block';
  document.querySelectorAll('nav button').forEach(b => b.classList.remove('active'));
  event.target.classList.add('active');
  currentTab = name;
  loadTab(name);
}

function toast(msg, ok=true) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.style.borderColor = ok ? 'var(--green)' : 'var(--red)';
  t.style.color = ok ? 'var(--green)' : 'var(--red)';
  t.style.display = 'block';
  setTimeout(() => t.style.display = 'none', 2500);
}

function tag(text, cls) {
  return `<span class="tag ${cls}">${text}</span>`;
}

function statusTag(s) {
  if (!s) return '';
  const map = {
    'Active':'tag-active','Pending':'tag-pending','In Progress':'tag-pending',
    'Done':'tag-done','Completed':'tag-done','High':'tag-high','Critical':'tag-high'
  };
  return tag(s, map[s] || '');
}

function tableOf(rows, cols) {
  if (!rows || rows.length === 0)
    return '<div class="empty">No data yet.</div>';
  let h = '<table><tr>' + cols.map(c=>`<th>${c}</th>`).join('') + '</tr>';
  rows.forEach(r => {
    h += '<tr>' + cols.map(c => {
      const v = r[c] || '';
      if (c === 'Status' || c === 'Priority') return `<td>${statusTag(v)}</td>`;
      return `<td title="${v}">${v}</td>`;
    }).join('') + '</tr>';
  });
  return h + '</table>';
}

async function loadTab(name) {
  if (name === 'dashboard')   await loadDashboard();
  if (name === 'inbox')       await loadInbox();
  if (name === 'projects')    await loadSheet('projects', ['Project','Domain','Status','Priority','Next Step','Last Updated']);
  if (name === 'loops')       await loadLoops();
  if (name === 'tasks')       await loadSheet('tasks', ['Task','Project','Priority','Status','Deadline','Added By']);
  if (name === 'corrections') await loadCorrections();
  if (name === 'ledger')      await loadSheet('ledger', ['Timestamp','Agent','Sheet','Operation','Status','Signature']);
  if (name === 'health')      await loadHealth();
  if (name === 'security')    await loadSecurity();
}

async function loadDashboard() {
  const h = await fetch('/api/health').then(r=>r.json());
  const cards = document.getElementById('stat-cards');
  cards.innerHTML = [
    {n: h.open_loops||0,         l: 'Open Loops',            cls: (h.open_loops||0)>10 ? 'warn' : ''},
    {n: h.inbox_pending||0,      l: 'Inbox Pending',         cls: (h.inbox_pending||0)>0 ? 'warn' : ''},
    {n: h.corrections_pending||0,l: 'Corrections',           cls: (h.corrections_pending||0)>0 ? 'warn' : ''},
    {n: h.stale_projects||0,     l: 'Stale Projects',        cls: (h.stale_projects||0)>0 ? 'alert' : ''},
    {n: h.chitrapat_size_kb||0,  l: 'File Size (KB)',        cls: ''},
  ].map(c => `
    <div class="card ${c.cls}" onclick="showTab('${c.l.includes('Loop') ? 'loops' : c.l.includes('Inbox') ? 'inbox' : c.l.includes('Correction') ? 'corrections' : 'dashboard'}')">
      <div class="num">${c.n}</div>
      <div class="lbl">${c.l}</div>
    </div>`).join('');

  const badges = document.getElementById('status-badges');
  badges.innerHTML = `
    <span class="badge ${h.chitragupta_alive ? 'ok' : 'warn'}">
      Chitragupta ${h.chitragupta_alive ? '● alive' : '⚠ silent'}
    </span>
    <span class="badge">${h.vidyakosha}</span>
    <span class="badge">v${h.version||'2.1'}</span>`;

  const sessions = await fetch('/api/sheet/session_log').then(r=>r.json());
  const recent = (sessions.rows||[]).slice(-5).reverse();
  document.getElementById('recent-sessions').innerHTML =
    tableOf(recent, ['Date','Topics Discussed','Decisions Made','Agent']);
}

async function loadSheet(name, cols) {
  const data = await fetch(`/api/sheet/${name}`).then(r=>r.json());
  const el = document.getElementById(`${name}-table`) ||
             document.getElementById(`tab-${name}`);
  if (el) el.innerHTML = tableOf(data.rows||[], cols);
}

async function loadInbox() {
  const data = await fetch('/api/sheet/inbox').then(r=>r.json());
  const rows = (data.rows||[]).filter(r => r['Routed?'] === 'No');
  let html = tableOf(rows, ['Content','Captured','Importance','Source']);
  if (rows.length > 0) {
    html += `<br><button class="btn" onclick="routeInbox()">🔀 Route All Inbox Items</button>`;
  }
  document.getElementById('inbox-table').innerHTML = html;
}

async function loadLoops() {
  const data = await fetch('/api/sheet/open_loops').then(r=>r.json());
  const open = (data.rows||[]).filter(r => r['Resolved?'] === 'No');
  let html = tableOf(open, ['Topic','Context / What\'s Unresolved','Priority','Importance','Opened','TTL_Days']);
  document.getElementById('loops-table').innerHTML = html;
}

async function loadCorrections() {
  const data = await fetch('/api/sheet/corrections').then(r=>r.json());
  const pending = (data.rows||[]).filter(r => r['Status'] === 'Pending');
  if (!pending.length) {
    document.getElementById('corrections-table').innerHTML =
      '<div class="empty">No pending corrections.</div>';
    return;
  }
  let html = '<table><tr><th>Sheet</th><th>Field</th><th>Proposed Value</th><th>Reason</th><th>By</th><th>Actions</th></tr>';
  pending.forEach((c,i) => {
    html += `<tr>
      <td>${c['Target Sheet']||''}</td>
      <td>${c['Field']||''}</td>
      <td>${c['Proposed Value']||''}</td>
      <td title="${c['Reason']||''}">${(c['Reason']||'').substring(0,60)}</td>
      <td>${c['Proposed By']||''}</td>
      <td>
        <button class="btn btn-success" onclick="reviewCorrection(${i},'Approved')">✓ Approve</button>
        <button class="btn btn-danger"  onclick="reviewCorrection(${i},'Rejected')">✗ Reject</button>
      </td>
    </tr>`;
  });
  html += '</table>';
  document.getElementById('corrections-table').innerHTML = html;
}

async function loadHealth() {
  const h = await fetch('/api/health').then(r=>r.json());
  const items = [
    {k:'Status',              v: h.status,              ok: h.status==='healthy'},
    {k:'Chitragupta',         v: h.chitragupta_alive ? 'alive' : 'silent',
                              ok: h.chitragupta_alive},
    {k:'VidyaKosha',          v: h.vidyakosha,          ok: h.vidyakosha==='available'},
    {k:'File Size',           v: (h.chitrapat_size_kb||0) + ' KB', ok: true},
    {k:'Open Loops',          v: h.open_loops||0,       ok: (h.open_loops||0) < 20},
    {k:'Inbox Pending',       v: h.inbox_pending||0,    ok: (h.inbox_pending||0) === 0},
    {k:'Corrections Pending', v: h.corrections_pending||0, ok: (h.corrections_pending||0)===0},
    {k:'Stale Projects',      v: h.stale_projects||0,   ok: (h.stale_projects||0)===0},
  ];
  document.getElementById('health-grid').innerHTML = items.map(i => `
    <div class="health-item">
      <span class="key">${i.k}</span>
      <span class="val ${i.ok ? 'ok' : 'warn'}">${i.v}</span>
    </div>`).join('');

  if (h.rows) {
    const rowItems = Object.entries(h.rows).map(([s,n]) => `
      <div class="health-item">
        <span class="key" style="font-size:0.72rem">${s}</span>
        <span class="val">${n} rows</span>
      </div>`).join('');
    document.getElementById('health-grid').innerHTML +=
      '<div style="grid-column:1/-1"><div class="section-title">Row Counts</div><div class="health-grid">' + rowItems + '</div></div>';
  }
}

async function submitInbox() {
  const input = document.getElementById('inbox-input');
  const text  = input.value.trim();
  if (!text) return;
  const res = await fetch('/api/inbox', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({text})
  }).then(r=>r.json());
  if (res.status === 'written') {
    toast('✓ Captured to Inbox');
    input.value = '';
    await loadInbox();
  } else {
    toast('Failed: ' + (res.reason || res.status), false);
  }
}

async function routeInbox() {
  const res = await fetch('/api/inbox/route', {method:'POST'}).then(r=>r.json());
  toast(`✓ Routed ${res.routed} items`);
  await loadInbox();
}

async function reviewCorrection(idx, decision) {
  const res = await fetch('/api/corrections/review', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({index: idx, decision})
  }).then(r=>r.json());
  toast(decision === 'Approved' ? '✓ Correction approved and applied' : '✗ Correction rejected');
  await loadCorrections();
}

// Keyboard shortcut: i = focus inbox
document.addEventListener('keydown', e => {
  if (e.key === 'i' && document.activeElement.tagName !== 'INPUT') {
    showTab('inbox');
    setTimeout(() => document.getElementById('inbox-input').focus(), 100);
  }
});

async function loadSecurity() {
  // Quarantine
  const q = await fetch('/api/sheet/quarantine').then(r=>r.json());
  const qRows = (q.rows||[]).filter(r => r['Status']==='Quarantined');
  if (!qRows.length) {
    document.getElementById('quarantine-table').innerHTML = '<div class="empty">✓ No quarantined writes.</div>';
  } else {
    let html = '<table><tr><th>Agent</th><th>Sheet</th><th>Threat</th><th>Found</th><th>Action</th></tr>';
    qRows.forEach((r,i) => {
      html += `<tr>
        <td>${r['Agent']||''}</td>
        <td>${r['Target Sheet']||''}</td>
        <td><span class="tag tag-high">${r['Threat Level']||''}</span></td>
        <td title="${r['Threats Found']||''}">${(r['Threats Found']||'').substring(0,50)}</td>
        <td>
          <button class="btn btn-success" onclick="releaseQuarantine('${r['Request ID']||''}')">✓ Release</button>
        </td>
      </tr>`;
    });
    html += '</table>';
    document.getElementById('quarantine-table').innerHTML = html;
  }
  // Security log
  const sl = await fetch('/api/sheet/security_log').then(r=>r.json());
  document.getElementById('security-log-table').innerHTML =
    tableOf((sl.rows||[]).slice(-20).reverse(),
            ['Timestamp','Agent','Sheet','Threat Level','Threat Type','Status']);
}

async function runSecurityScan() {
  const el = document.getElementById('security-scan-result');
  el.innerHTML = '<span style="color:var(--dim)">Scanning...</span>';
  try {
    const res = await fetch('/api/security/scan', {method:'POST'}).then(r=>r.json());
    const total = res.total_findings||0;
    const color = total===0 ? 'var(--green)' : (res.confirmed||0)>0 ? 'var(--red)' : 'var(--saffron)';
    el.innerHTML = `<div style="color:${color};padding:10px;border:1px solid ${color};border-radius:6px;font-size:0.85rem">
      ${total===0 ? '✓ Clean — no threats detected' :
        `⚠ ${total} findings: ${res.critical||0} critical · ${res.confirmed||0} confirmed · ${res.suspicious||0} suspicious`}
    </div>`;
    await loadSecurity();
  } catch(e) { el.innerHTML = `<span style="color:var(--red)">Scan failed: ${e}</span>`; }
}

async function releaseQuarantine(reqId) {
  const res = await fetch('/api/security/quarantine/release', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({request_id: reqId})
  }).then(r=>r.json());
  toast(res.status==='released' ? '✓ Write released — Dharma-Adesh applied' : `Status: ${res.status}`);
  await loadSecurity();
}

// Auto-refresh dashboard every 30s
setInterval(() => { if (currentTab === 'dashboard') loadDashboard(); }, 30000);

// Load dashboard on start
loadDashboard();
</script>
</body>
</html>"""


# ── API routes ─────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def root():
    return HTML


@app.get("/api/health")
async def api_health():
    return get_oy().health_check()


@app.get("/api/sheet/{name}")
async def api_sheet(name: str):
    from openyantra import SHEET_QUARANTINE, SHEET_SECURITY_LOG
    sheet_map = {
        "projects":    SHEET_PROJECTS,
        "tasks":       SHEET_TASKS,
        "open_loops":  SHEET_OPEN_LOOPS,
        "people":      SHEET_PEOPLE,
        "goals":       SHEET_GOALS,
        "preferences": SHEET_PREFERENCES,
        "beliefs":     SHEET_BELIEFS,
        "session_log": SHEET_SESSION_LOG,
        "inbox":       SHEET_INBOX,
        "corrections": SHEET_CORRECTIONS,
        "ledger":      SHEET_LEDGER,
        "quarantine":  SHEET_QUARANTINE,
        "security_log":SHEET_SECURITY_LOG,
    }
    sheet = sheet_map.get(name)
    if not sheet:
        raise HTTPException(status_code=404, detail=f"Unknown sheet: {name}")
    oy   = get_oy()
    rows = oy._read_sheet(sheet)
    return {"sheet": sheet, "rows": rows, "count": len(rows)}


@app.post("/api/inbox")
async def api_inbox(req: Request):
    data = await req.json()
    text = data.get("text", "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text required")
    oy      = get_oy()
    receipt = oy.inbox(text, importance=int(data.get("importance", 5)))
    return receipt


@app.post("/api/inbox/route")
async def api_route_inbox():
    oy      = get_oy()
    routing = oy.route_inbox(dry_run=False)
    routed  = sum(1 for r in routing if r.get("routed"))
    return {"routed": routed, "decisions": routing}


@app.post("/api/corrections/review")
async def api_review_correction(req: Request):
    data     = await req.json()
    idx      = data.get("index", 0)
    decision = data.get("decision", "Rejected")
    oy       = get_oy()

    corrections = [r for r in oy._read_sheet(SHEET_CORRECTIONS)
                   if r.get("Status") == "Pending"]
    if idx >= len(corrections):
        raise HTTPException(status_code=404, detail="Correction not found")

    c = corrections[idx]
    # Update status
    from openyantra import WriteRequest, SHEET_CORRECTIONS
    oy.request_write(WriteRequest(
        "Yantra-UI", SHEET_CORRECTIONS, "update",
        {"Status": decision,
         "Reviewed By": "User",
         "Reviewed At": datetime.utcnow().isoformat(timespec="seconds")},
        row_identifier=str(c.get("Target Sheet",""))[:50],
        confidence="High", source="User-stated", importance=8,
    ))

    # Apply if approved
    if decision == "Approved":
        target = c.get("Target Sheet", "")
        field  = c.get("Field", "")
        value  = c.get("Proposed Value", "")
        row_id = c.get("Row Identifier", "")
        if target and field and row_id:
            oy.request_write(WriteRequest(
                "Chitragupta", target, "update", {field: value},
                row_identifier=row_id,
                confidence="High", source="User-stated", importance=8,
            ))

    return {"status": "ok", "decision": decision}


@app.post("/api/loops/{topic}/resolve")
async def api_resolve_loop(topic: str, req: Request):
    data       = await req.json()
    resolution = data.get("resolution", "Resolved via UI")
    oy         = get_oy()
    receipt    = oy.resolve_open_loop(topic, resolution)
    return receipt


@app.get("/api/contradictions")
async def api_contradictions():
    oy = get_oy()
    return {"contradictions": oy.diff_beliefs()}


@app.get("/api/ttl_check")
async def api_ttl_check():
    oy = get_oy()
    return {"expired_loops": oy.check_anishtha_ttl()}



@app.post("/api/security/scan")
async def api_security_scan():
    oy = get_oy()
    return oy.security_scan()


@app.post("/api/security/quarantine/release")
async def api_release_quarantine(req: Request):
    data       = await req.json()
    request_id = data.get("request_id", "")
    oy         = get_oy()
    return oy.release_quarantine(request_id)


@app.get("/api/security/trust/{agent_name}")
async def api_trust_tier(agent_name: str):
    oy = get_oy()
    return {"agent": agent_name, "trust_tier": oy.get_trust_tier(agent_name)}


# ── CLI entry point ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="OpenYantra Browser Dashboard v2.1"
    )
    parser.add_argument(
        "--file", "-f",
        default=str(Path.home() / "openyantra" / "chitrapat.ods"),
        help="Path to chitrapat.ods (default: ~/openyantra/chitrapat.ods)"
    )
    parser.add_argument("--port", "-p", type=int, default=7331,
                        help="Port (default: 7331)")
    parser.add_argument("--host", default="127.0.0.1",
                        help="Host (default: 127.0.0.1 — local only)")
    args = parser.parse_args()

    global _oy
    path = Path(args.file).expanduser()

    if not path.exists():
        print(f"[OpenYantra] No Chitrapat found at {path}")
        print("[OpenYantra] Run `yantra bootstrap` first, or:")
        print(f"  python openyantra.py --bootstrap")
        sys.exit(1)

    _oy = OpenYantra(str(path), agent_name="Yantra-UI")
    health = _oy.health_check()

    print(f"\n{'='*55}")
    print(f"  OpenYantra Dashboard v2.1")
    print(f"  Chitrapat: {path}")
    print(f"  Status:    {health.get('status','unknown')}")
    print(f"  Open Loops: {health.get('open_loops',0)}  "
          f"Inbox: {health.get('inbox_pending',0)}  "
          f"Corrections: {health.get('corrections_pending',0)}")
    print(f"{'='*55}")
    print(f"\n  → http://{args.host}:{args.port}")
    print(f"  Press Ctrl+C to stop\n")

    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
