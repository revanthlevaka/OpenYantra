"""
yantra_ui.py — OpenYantra Browser Dashboard v2.10
Run: yantra ui → http://localhost:7331

New in v2.10:
  - Today tab: unified daily view with one-click actions
  - Timeline tab: chronological activity feed
  - Conflict Resolver tab: visual diff agent vs user
  - Floating capture button: persistent + keyboard shortcut i
  - Mobile-responsive CSS
  - Task complete from Today view
  - Loop resolve from Today view
"""

from __future__ import annotations
import argparse, sys
from datetime import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.responses import HTMLResponse
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

app = FastAPI(title="OpenYantra", version="2.10", docs_url=None, redoc_url=None)
_oy = None

def get_oy() -> OpenYantra:
    if _oy is None: raise HTTPException(500, "Not initialised")
    return _oy

HTML = open(__file__).read().split("# --HTML--")[1].split("# --END--")[0] if "# --HTML--" in open(__file__).read() else ""

# Since we can't use the marker trick cleanly, define HTML inline
DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>OpenYantra v2.10</title>
<style>
:root{--ink:#0c0812;--saffron:#ff9933;--gold:#d4af37;--cream:#fff8e6;
  --dim:#b4a078;--surface:#1a1228;--surface2:#241832;--border:#3d2a55;
  --green:#4caf7d;--red:#e05032;--blue:#5b8dd9;--warn:#f0a030;}
*{box-sizing:border-box;margin:0;padding:0;}
body{font-family:'Segoe UI',system-ui,sans-serif;background:var(--ink);color:var(--cream);min-height:100vh;}
header{background:var(--surface);border-bottom:2px solid var(--saffron);padding:12px 20px;display:flex;align-items:center;gap:12px;position:sticky;top:0;z-index:100;}
header h1{font-size:1.3rem;color:var(--saffron);}
header h1 span{color:var(--cream);font-weight:300;}
header small{color:var(--dim);font-size:0.7rem;}
.badge{background:var(--surface2);border:1px solid var(--border);border-radius:10px;padding:2px 8px;font-size:0.68rem;color:var(--dim);}
.badge.ok{border-color:var(--green);color:var(--green);}
.badge.warn{border-color:var(--saffron);color:var(--saffron);}
nav{background:var(--surface2);display:flex;gap:3px;padding:6px 12px;border-bottom:1px solid var(--border);flex-wrap:wrap;position:sticky;top:53px;z-index:99;}
nav button{background:transparent;border:1px solid var(--border);color:var(--dim);padding:5px 11px;border-radius:5px;cursor:pointer;font-size:0.76rem;transition:all 0.15s;white-space:nowrap;}
nav button:hover,nav button.active{background:var(--surface);border-color:var(--saffron);color:var(--saffron);}
main{padding:16px 20px;max-width:1200px;margin:0 auto;padding-bottom:80px;}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px;margin-bottom:20px;}
.card{background:var(--surface2);border:1px solid var(--border);border-radius:8px;padding:14px;cursor:pointer;transition:border-color 0.15s;}
.card:hover{border-color:var(--saffron);}
.card .num{font-size:1.9rem;font-weight:700;color:var(--saffron);}
.card .lbl{font-size:0.73rem;color:var(--dim);margin-top:3px;}
.card.warn{border-color:var(--warn);}
.card.alert{border-color:var(--red);}
.sec{font-size:0.93rem;color:var(--gold);margin:16px 0 8px;font-weight:600;}
table{width:100%;border-collapse:collapse;font-size:0.79rem;}
th{background:var(--surface2);color:var(--gold);padding:7px 9px;text-align:left;font-weight:600;border-bottom:1px solid var(--border);}
td{padding:6px 9px;border-bottom:1px solid var(--border);max-width:260px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
tr:hover td{background:var(--surface2);}
.tag{display:inline-block;padding:2px 7px;border-radius:8px;font-size:0.68rem;font-weight:600;}
.tag-active{background:#1a3a2a;color:var(--green);}
.tag-pending{background:#3a2a1a;color:var(--saffron);}
.tag-done{background:#1a2a3a;color:var(--blue);}
.tag-high,.tag-confirmed{background:#3a1a1a;color:var(--red);}
.tag-suspicious{background:#3a2a10;color:var(--warn);}
.tag-clean{background:#1a3a2a;color:var(--green);}
.btn{background:var(--surface);border:1px solid var(--border);color:var(--cream);padding:5px 11px;border-radius:5px;cursor:pointer;font-size:0.77rem;transition:all 0.15s;}
.btn:hover{border-color:var(--saffron);color:var(--saffron);}
.btn-p{background:var(--saffron);color:var(--ink);border:none;padding:8px 18px;border-radius:6px;font-weight:600;cursor:pointer;font-size:0.84rem;}
.btn-p:hover{background:#e68a00;}
.btn-ok{border-color:var(--green);color:var(--green);}
.btn-x{border-color:var(--red);color:var(--red);}
/* Today */
.ts-card{background:var(--surface2);border:1px solid var(--border);border-radius:8px;padding:13px;margin-bottom:10px;}
.ts-card h3{color:var(--gold);font-size:0.85rem;margin-bottom:9px;}
.ti{display:flex;align-items:flex-start;gap:9px;padding:6px 0;border-bottom:1px solid var(--border);}
.ti:last-child{border-bottom:none;}
.ti .pri{min-width:55px;font-size:0.68rem;text-align:center;}
.ti .con{flex:1;font-size:0.8rem;}
.ti .con small{color:var(--dim);font-size:0.7rem;display:block;margin-top:2px;}
.ti .act button{background:transparent;border:1px solid var(--border);color:var(--dim);padding:3px 7px;border-radius:4px;cursor:pointer;font-size:0.7rem;}
.ti .act button:hover{border-color:var(--saffron);color:var(--saffron);}
/* Timeline */
.tl{position:relative;padding-left:22px;}
.tl::before{content:'';position:absolute;left:7px;top:0;bottom:0;width:2px;background:var(--border);}
.tli{position:relative;margin-bottom:12px;}
.tli::before{content:'';position:absolute;left:-18px;top:5px;width:7px;height:7px;border-radius:50%;background:var(--saffron);border:2px solid var(--ink);}
.tli .ts{font-size:0.68rem;color:var(--dim);margin-bottom:2px;}
.tli .body{background:var(--surface2);border:1px solid var(--border);border-radius:6px;padding:7px 11px;font-size:0.79rem;}
.tli .body .ag{color:var(--saffron);font-size:0.7rem;margin-bottom:2px;}
/* Conflict */
.cf-card{background:var(--surface2);border:1px solid var(--warn);border-radius:8px;padding:13px;margin-bottom:10px;}
.cf-card h4{color:var(--warn);font-size:0.83rem;margin-bottom:8px;}
.cf-diff{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:8px 0;}
.cf-side{border-radius:6px;padding:9px;}
.cf-side.ag{background:#1a1a0a;border:1px solid var(--warn);}
.cf-side.usr{background:#0a1a0a;border:1px solid var(--green);}
.cf-side .lbl{font-size:0.68rem;font-weight:600;margin-bottom:3px;}
.cf-side.ag .lbl{color:var(--warn);}
.cf-side.usr .lbl{color:var(--green);}
.cf-side .val{font-size:0.83rem;word-break:break-word;}
.cf-acts{display:flex;gap:7px;margin-top:9px;}
/* Inbox */
.ibf{display:flex;gap:7px;margin-bottom:12px;}
.ibf input{flex:1;background:var(--surface2);border:1px solid var(--border);color:var(--cream);padding:8px 11px;border-radius:5px;font-size:0.86rem;}
.ibf input:focus{outline:none;border-color:var(--saffron);}
/* Float */
#fcap{position:fixed;bottom:20px;right:20px;z-index:200;}
#fbtn{background:var(--saffron);color:var(--ink);border:none;width:50px;height:50px;border-radius:50%;font-size:1.3rem;cursor:pointer;box-shadow:0 4px 16px rgba(255,153,51,0.4);}
#fbtn:hover{transform:scale(1.08);}
#fform{display:none;position:absolute;bottom:58px;right:0;background:var(--surface);border:1px solid var(--saffron);border-radius:9px;padding:11px;width:270px;box-shadow:0 8px 24px rgba(0,0,0,0.5);}
#fform.open{display:block;}
#fform p{font-size:0.72rem;color:var(--dim);margin-bottom:5px;}
#finput{width:100%;background:var(--surface2);border:1px solid var(--border);color:var(--cream);padding:7px;border-radius:5px;font-size:0.83rem;margin-bottom:7px;resize:none;height:55px;}
#finput:focus{outline:none;border-color:var(--saffron);}
.fbtns{display:flex;gap:5px;}
#toast{position:fixed;bottom:78px;right:22px;background:var(--surface);border:1px solid var(--green);color:var(--green);padding:8px 14px;border-radius:7px;font-size:0.8rem;display:none;z-index:300;}
.empty{color:var(--dim);text-align:center;padding:26px;font-size:0.8rem;}
.hgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:8px;margin-top:9px;}
.hi{background:var(--surface2);border:1px solid var(--border);border-radius:7px;padding:9px 13px;display:flex;justify-content:space-between;align-items:center;}
.hi .k{color:var(--dim);font-size:0.77rem;}
.hi .v{font-weight:600;}
.hi .v.ok{color:var(--green);}
.hi .v.warn{color:var(--warn);}
@media(max-width:600px){
  .cards{grid-template-columns:repeat(2,1fr);}
  .cf-diff{grid-template-columns:1fr;}
  #fform{width:220px;}
  table{font-size:0.71rem;}
  td,th{padding:4px 6px;}
}
</style>
</head>
<body>
<header>
  <div>
    <h1>Open<span>Yantra</span></h1>
    <small>Sacred Memory Machine · v2.10 · Chitragupta-secured</small>
  </div>
  <div id="badges" style="margin-left:auto;display:flex;gap:5px;flex-wrap:wrap;"></div>
</header>
<nav>
  <button class="active" onclick="go('today',this)">🌅 Today</button>
  <button onclick="go('inbox',this)">📥 Inbox</button>
  <button onclick="go('projects',this)">🚀 Projects</button>
  <button onclick="go('loops',this)">🔓 Loops</button>
  <button onclick="go('tasks',this)">✅ Tasks</button>
  <button onclick="go('timeline',this)">📅 Timeline</button>
  <button onclick="go('conflicts',this)">⚡ Conflicts</button>
  <button onclick="go('corrections',this)">✏️ Corrections</button>
  <button onclick="go('security',this)">🔒 Security</button>
  <button onclick="go('ledger',this)">📒 Ledger</button>
  <button onclick="go('health',this)">💚 Health</button>
  <button onclick="go('stats',this)">📊 Stats</button>
</nav>
<main>
  <div id="today"></div>
  <div id="context-toast" style="display:none;position:fixed;top:70px;right:20px;z-index:500;background:#1a1228;border:1px solid #ff9933;border-radius:10px;padding:16px 20px;max-width:320px;box-shadow:0 8px 32px rgba(0,0,0,0.6)"><div style="color:#ff9933;font-weight:600;margin-bottom:8px">Context copied to clipboard</div><div style="color:#b4a078;font-size:0.8rem;margin-bottom:12px">Paste into Claude.ai, ChatGPT, or any AI chat to share your full context.</div><button onclick="document.getElementById('context-toast').style.display='none'" style="background:transparent;border:1px solid #3d2a55;color:#b4a078;padding:4px 12px;border-radius:5px;cursor:pointer;font-size:0.75rem">Done</button></div>
  <div id="inbox" style="display:none"></div>
  <div id="projects" style="display:none"></div>
  <div id="loops" style="display:none"></div>
  <div id="tasks" style="display:none"></div>
  <div id="timeline" style="display:none"></div>
  <div id="conflicts" style="display:none"></div>
  <div id="corrections" style="display:none"></div>
  <div id="security" style="display:none"></div>
  <div id="ledger" style="display:none"></div>
  <div id="health" style="display:none"></div>
  <div id="stats" style="display:none"></div>
</main>
<div id="fcap">
  <div id="fform">
    <p>Quick capture → Inbox</p>
    <textarea id="finput" placeholder="Capture anything..."></textarea>
    <div class="fbtns">
      <button class="btn-p" onclick="floatSave()" style="flex:1">Save</button>
      <button class="btn" onclick="floatClose()">✕</button>
    </div>
  </div>
  <button id="fbtn" onclick="floatToggle()" title="Quick capture (i)">＋</button>
</div>
<div id="toast"></div>
<script>
let cur='today';
const api=async(url,opts)=>{try{const r=await fetch(url,opts);return await r.json();}catch(e){return{};}};
const toast=(m,ok=true)=>{const t=document.getElementById('toast');t.textContent=m;t.style.borderColor=ok?'var(--green)':'var(--red)';t.style.color=ok?'var(--green)':'var(--red)';t.style.display='block';setTimeout(()=>t.style.display='none',2500);};
const stag=(s,cls)=>`<span class="tag ${cls||''}">${s||''}</span>`;
const ptag=s=>{if(!s)return'';const m={'Active':'tag-active','Pending':'tag-pending','In Progress':'tag-pending','Done':'tag-done','Completed':'tag-done','High':'tag-high','Critical':'tag-high','confirmed':'tag-confirmed','suspicious':'tag-suspicious','clean':'tag-clean','written':'tag-active'};return stag(s,m[s]||'');};

function go(name, btn) {
  document.querySelectorAll('main>div').forEach(d=>d.style.display='none');
  document.getElementById(name).style.display='block';
  document.querySelectorAll('nav button').forEach(b=>b.classList.remove('active'));
  if(btn)btn.classList.add('active');
  cur=name; load(name);
}

async function load(name) {
  const loaders={today:loadToday,inbox:loadInbox,projects:()=>loadTable('projects',['Project','Domain','Status','Priority','Next Step'],'projects'),loops:loadLoops,tasks:()=>loadTable('tasks',['Task','Project','Priority','Status','Deadline'],'tasks'),timeline:loadTimeline,conflicts:loadConflicts,corrections:loadCorrections,security:loadSecurity,ledger:()=>loadTable('ledger',['Timestamp','Agent','Sheet','Operation','Status'],'ledger'),health:loadHealth,stats:loadStats};
  if(loaders[name])await loaders[name]();
}

function tbl(rows,cols){
  if(!rows||!rows.length)return'<div class="empty">No data yet.</div>';
  let h='<table><tr>'+cols.map(c=>`<th>${c}</th>`).join('')+'</tr>';
  rows.forEach(r=>{h+='<tr>'+cols.map(c=>{const v=r[c]||'';if(c==='Status'||c==='Priority'||c==='Threat Level')return`<td>${ptag(v)}</td>`;return`<td title="${v}">${String(v).substring(0,55)}</td>`;}).join('')+'</tr>';});
  return h+'</table>';
}

async function loadTable(sheet,cols,elId){
  const d=await api(`/api/sheet/${sheet}`);
  document.getElementById(elId).innerHTML='<div class="sec">'+sheet+'</div>'+tbl(d.rows||[],cols);
}

async function loadToday(){
  const h=await api('/api/health');
  const [ld,pd,td,id]=await Promise.all([
    api('/api/sheet/open_loops'),api('/api/sheet/projects'),
    api('/api/sheet/tasks'),api('/api/sheet/inbox')
  ]);
  document.getElementById('badges').innerHTML=`
    <span class="badge ${h.chitragupta_alive?'ok':'warn'}">Chitragupta ${h.chitragupta_alive?'●':'⚠'}</span>
    <span class="badge">${h.vidyakosha||'?'}</span>
    <span class="badge">v${h.version||'2.5'}</span>`;
  const cards=[
    {n:h.open_loops||0,l:'Open Loops',t:'loops',c:(h.open_loops||0)>10?'warn':''},
    {n:h.inbox_pending||0,l:'Inbox',t:'inbox',c:(h.inbox_pending||0)>0?'warn':''},
    {n:h.corrections_pending||0,l:'Corrections',t:'corrections',c:(h.corrections_pending||0)>0?'warn':''},
    {n:h.stale_projects||0,l:'Stale Projects',t:'projects',c:(h.stale_projects||0)>0?'alert':''},
    {n:h.chitrapat_size_kb||0,l:'File KB',t:'health',c:''},
  ].map(c=>`<div class="card ${c.c}" onclick="goTo('${c.t}')"><div class="num">${c.n}</div><div class="lbl">${c.l}</div></div>`).join('');

  const cutoff=new Date(Date.now()-7*86400000).toISOString().slice(0,10);
  const loops=(ld.rows||[]).filter(r=>r['Resolved?']==='No').sort((a,b)=>(b['Importance']||5)-(a['Importance']||5)).slice(0,5);
  const stale=(pd.rows||[]).filter(r=>r['Status']==='Active'&&(r['Last Updated']||'')<cutoff).slice(0,3);
  const uTasks=(td.rows||[]).filter(r=>r['Status']==='Pending'&&r['Priority']==='High').slice(0,3);
  const inbox=(id.rows||[]).filter(r=>r['Routed?']==='No').slice(0,3);

  let body='';
  if(loops.length){
    body+='<div class="ts-card"><h3>🔓 Open Loops needing attention</h3>';
    loops.forEach(l=>{body+=`<div class="ti"><div class="pri">${ptag(l['Priority']||'?')}</div><div class="con"><div>${(l['Topic']||'').substring(0,65)}</div><small>${(l["Context / What's Unresolved"]||'').substring(0,75)}</small></div><div class="act"><button onclick="resolveLoop('${(l['Topic']||'').replace(/'/g,"\\'")}')">✓ Resolve</button></div></div>`;});
    body+='</div>';
  }
  if(stale.length){
    body+='<div class="ts-card"><h3>🚀 Stale Projects — no update 7+ days</h3>';
    stale.forEach(p=>{body+=`<div class="ti"><div class="pri">${ptag(p['Priority']||'?')}</div><div class="con"><div>${(p['Project']||'').substring(0,60)}</div><small>Next: ${(p['Next Step']||'not set').substring(0,65)}</small></div><div class="act"><button onclick="goTo('projects')">View</button></div></div>`;});
    body+='</div>';
  }
  if(uTasks.length){
    body+='<div class="ts-card"><h3>✅ High Priority Tasks</h3>';
    uTasks.forEach(t=>{body+=`<div class="ti"><div class="pri">${ptag('High')}</div><div class="con"><div>${(t['Task']||'').substring(0,65)}</div><small>${t['Project']||''}</small></div><div class="act"><button onclick="doneTask('${(t['Task']||'').replace(/'/g,"\\'")}')">✓ Done</button></div></div>`;});
    body+='</div>';
  }
  if(inbox.length){
    body+=`<div class="ts-card"><h3>📥 Inbox — ${inbox.length} items need routing</h3>`;
    inbox.forEach(i=>{body+=`<div class="ti"><div class="pri" style="color:var(--dim);font-size:0.68rem">Inbox</div><div class="con"><div>${(i['Content']||'').substring(0,75)}</div></div><div class="act"><button onclick="routeAll()">Route all</button></div></div>`;});
    body+='</div>';
  }
  if(!body)body='<div class="ts-card"><h3 style="color:var(--green)">✓ All clear — nothing urgent today</h3></div>';
  const ctxBtn = `<div style="margin-bottom:14px;display:flex;gap:10px;align-items:center">
      <button id="copy-ctx-btn" class="btn-p" onclick="copyContext()" style="padding:9px 20px;font-size:0.85rem">
        📋 Copy Context
      </button>
      <span style="color:var(--dim);font-size:0.78rem">Paste into Claude.ai · ChatGPT · any AI chat</span>
    </div>`;
    // Daily Insight card
    const brief = await api('/api/morning');
    let insightCard = '';
    if(brief && brief.brief) {
      // Convert markdown to readable HTML
      const briefHtml = brief.brief
        .replace(/\*\*(.*?)\*\*/g,'<strong style="color:var(--saffron)">$1</strong>')
        .replace(/\*(.*?)\*/g,'<em style="color:var(--dim)">$1</em>')
        .replace(/^## (.*)/gm,'')
        .replace(/^\*(.*?)\*$/gm,'')
        .replace(/^- /gm,'• ')
        .split('\n').filter(l=>l.trim()).join('<br>');

      insightCard = `<div style="background:linear-gradient(135deg,#1e1630,#241832);border:1px solid rgba(255,153,51,0.3);border-radius:10px;padding:16px 20px;margin-bottom:14px">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
          <span style="color:var(--gold);font-weight:600;font-size:0.9rem">🌅 Daily Insight</span>
          ${brief.streak>0?`<span style="color:var(--saffron);font-size:0.78rem;font-weight:600">🔥 ${brief.streak} day streak</span>`:''}
        </div>
        <div style="color:var(--cream);font-size:0.82rem;line-height:1.7">${briefHtml}</div>
      </div>`;
    }
    document.getElementById('today').innerHTML='<div class="cards">'+cards+'</div>'+insightCard+ctxBtn+body;
}

function goTo(name){
  const btns=document.querySelectorAll('nav button');
  const tabs=['today','inbox','projects','loops','tasks','timeline','conflicts','corrections','security','ledger','health'];
  const i=tabs.indexOf(name);
  if(i>=0)go(name,btns[i]);
}

async function loadTimeline(){
  const d=await api('/api/sheet/ledger');
  const rows=(d.rows||[]).filter(r=>r['Status']==='written').slice(-60).reverse();
  const emoji={'🚀 Projects':'🚀','✅ Tasks':'✅','🔓 Open Loops':'🔓','👤 Identity':'👤','🎯 Goals':'🎯','👥 People':'👥','💡 Preferences':'💡','🧠 Beliefs':'🧠','📥 Inbox':'📥','📅 Session Log':'📅'};
  if(!rows.length){document.getElementById('timeline').innerHTML='<div class="sec">📅 Timeline</div><div class="empty">No activity yet.</div>';return;}
  let html='<div class="sec">📅 Timeline — Activity Feed</div><div class="tl">';
  rows.forEach(r=>{
    const sh=r['Sheet']||'';const em=emoji[sh]||'📝';
    const ts=(r['Timestamp']||'').substring(0,16).replace('T',' ');
    const rid=r['Row Identifier']||'';
    html+=`<div class="tli"><div class="ts">${ts}</div><div class="body"><div class="ag">${r['Agent']||'?'} · ${r['Operation']||'?'}</div><div>${em} ${sh.split(' ').slice(1).join(' ')}${rid?' — '+rid.substring(0,45):''}</div></div></div>`;
  });
  html+='</div>';
  document.getElementById('timeline').innerHTML=html;
}

async function loadConflicts(){
  const d=await api('/api/sheet/corrections');
  const pending=(d.rows||[]).filter(r=>r['Status']==='Pending');
  const el=document.getElementById('conflicts');
  if(!pending.length){el.innerHTML='<div class="sec">⚡ Conflict Resolver</div><div class="empty">✓ No conflicts pending.</div>';return;}
  let html='<div class="sec">⚡ Conflict Resolver (Vivada)</div><p style="color:var(--dim);font-size:0.77rem;margin-bottom:12px">Choose which value to keep — your choice is Dharma-Adesh.</p>';
  pending.forEach((c,i)=>{
    html+=`<div class="cf-card">
      <h4>⚡ ${c['Target Sheet']||'?'} · ${c['Row Identifier']||'?'} · ${c['Field']||'?'}</h4>
      <p style="color:var(--dim);font-size:0.76rem;margin-bottom:6px">Reason: ${c['Reason']||'Agent proposed change'}</p>
      <div class="cf-diff">
        <div class="cf-side ag"><div class="lbl">🤖 ${c['Proposed By']||'agent'} proposes:</div><div class="val">${c['Proposed Value']||'?'}</div></div>
        <div class="cf-side usr"><div class="lbl">👤 Current (yours):</div><div class="val">—</div></div>
      </div>
      <div class="cf-acts">
        <button class="btn btn-ok" onclick="resolveC(${i},'Approved')">✓ Accept change</button>
        <button class="btn btn-x" onclick="resolveC(${i},'Rejected')">✗ Keep my version</button>
      </div></div>`;
  });
  el.innerHTML=html;
}

async function resolveC(idx,decision){
  await api('/api/corrections/review',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({index:idx,decision})});
  toast(decision==='Approved'?'✓ Change applied':'✓ Your version kept');
  await loadConflicts();
}

async function loadLoops(){
  const d=await api('/api/sheet/open_loops');
  const open=(d.rows||[]).filter(r=>r['Resolved?']==='No');
  document.getElementById('loops').innerHTML='<div class="sec">🔓 Open Loops (Anishtha)</div>'+tbl(open,['Topic',"Context / What's Unresolved",'Priority','Importance','Opened','TTL_Days']);
}

async function loadInbox(){
  const d=await api('/api/sheet/inbox');
  const rows=(d.rows||[]).filter(r=>r['Routed?']==='No');
  let html=`<div class="sec">📥 Inbox — Quick Capture</div>
  <div class="ibf"><input id="ii" placeholder="Capture a thought..."/><button class="btn-p" onclick="saveInbox()">Save</button></div>`;
  html+=tbl(rows,['Content','Captured','Importance','Source']);
  if(rows.length)html+=`<br><button class="btn" onclick="routeAll()">🔀 Route All</button>`;
  document.getElementById('inbox').innerHTML=html;
}

async function saveInbox(){
  const el=document.getElementById('ii');const t=el.value.trim();if(!t)return;
  const r=await api('/api/inbox',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:t})});
  if(r.status==='written'){toast('✓ Captured');el.value='';await loadInbox();}
  else toast('Failed: '+(r.reason||r.status),false);
}

async function routeAll(){
  const r=await api('/api/inbox/route',{method:'POST'});
  toast(`✓ Routed ${r.routed||0} items`);await loadInbox();
}

async function loadCorrections(){
  const d=await api('/api/sheet/corrections');
  const pending=(d.rows||[]).filter(r=>r['Status']==='Pending');
  if(!pending.length){document.getElementById('corrections').innerHTML='<div class="sec">✏️ Corrections</div><div class="empty">No pending corrections.</div>';return;}
  let html='<div class="sec">✏️ Corrections (Sanshodhan)</div><table><tr><th>Sheet</th><th>Field</th><th>Proposed</th><th>Reason</th><th>By</th><th>Actions</th></tr>';
  pending.forEach((c,i)=>{html+=`<tr><td>${c['Target Sheet']||''}</td><td>${c['Field']||''}</td><td>${(c['Proposed Value']||'').substring(0,35)}</td><td title="${c['Reason']||''}">${(c['Reason']||'').substring(0,35)}</td><td>${c['Proposed By']||''}</td><td><button class="btn btn-ok" onclick="revC(${i},'Approved')">✓</button> <button class="btn btn-x" onclick="revC(${i},'Rejected')">✗</button></td></tr>`;});
  document.getElementById('corrections').innerHTML=html+'</table>';
}

async function revC(idx,d){
  await api('/api/corrections/review',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({index:idx,decision:d})});
  toast(d==='Approved'?'✓ Applied':'✗ Rejected');await loadCorrections();await loadConflicts();
}

async function loadSecurity(){
  const q=await api('/api/sheet/quarantine');
  const sl=await api('/api/sheet/security_log');
  const qr=(q.rows||[]).filter(r=>r['Status']==='Quarantined');
  let html='<div class="sec">🔒 Security — Raksha</div>';
  html+=`<div style="display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap;">
    <button class="btn-p" onclick="scanSec()">🔍 Run Full Scan</button>
    <button class="btn" onclick="load('security')">↺ Refresh</button></div>
  <div id="scanres" style="margin-bottom:12px"></div>`;
  html+='<div class="sec">🔒 Quarantined Writes</div>';
  if(!qr.length){html+='<div class="empty">✓ No quarantined writes.</div>';}
  else{
    html+='<table><tr><th>Agent</th><th>Sheet</th><th>Threat</th><th>Found</th><th>Action</th></tr>';
    qr.forEach(r=>{html+=`<tr><td>${r['Agent']||''}</td><td>${r['Target Sheet']||''}</td><td>${ptag(r['Threat Level']||'')}</td><td title="${r['Threats Found']||''}">${(r['Threats Found']||'').substring(0,45)}</td><td><button class="btn btn-ok" onclick="releaseQ('${r['Request ID']||''}')">↑ Release</button></td></tr>`;});
    html+='</table>';
  }
  html+='<div class="sec" style="margin-top:14px">🛡️ Security Log</div>';
  html+=tbl((sl.rows||[]).slice(-20).reverse(),['Timestamp','Agent','Sheet','Threat Level','Status']);
  document.getElementById('security').innerHTML=html;
}

async function scanSec(){
  const el=document.getElementById('scanres');
  el.innerHTML='<span style="color:var(--dim)">Scanning...</span>';
  const r=await api('/api/security/scan',{method:'POST'});
  const t=r.total_findings||0;
  const col=t===0?'var(--green)':(r.confirmed||0)>0?'var(--red)':'var(--warn)';
  el.innerHTML=`<div style="color:${col};padding:9px;border:1px solid ${col};border-radius:6px;font-size:0.81rem">${t===0?'✓ Clean — no threats detected':`⚠ ${t} findings: ${r.critical||0} critical · ${r.confirmed||0} confirmed · ${r.suspicious||0} suspicious`}</div>`;
  await loadSecurity();
}

async function releaseQ(id){
  const r=await api('/api/security/quarantine/release',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({request_id:id})});
  toast(r.status==='released'?'✓ Released':'Status: '+r.status);await loadSecurity();
}

async function loadHealth(){
  const h=await api('/api/health');
  const items=[{k:'Status',v:h.status,ok:h.status==='healthy'},{k:'Chitragupta',v:h.chitragupta_alive?'alive':'silent',ok:h.chitragupta_alive},{k:'VidyaKosha',v:h.vidyakosha,ok:h.vidyakosha==='available'},{k:'File Size',v:(h.chitrapat_size_kb||0)+' KB',ok:true},{k:'Open Loops',v:h.open_loops||0,ok:(h.open_loops||0)<20},{k:'Inbox Pending',v:h.inbox_pending||0,ok:(h.inbox_pending||0)===0},{k:'Corrections',v:h.corrections_pending||0,ok:(h.corrections_pending||0)===0},{k:'Stale Projects',v:h.stale_projects||0,ok:(h.stale_projects||0)===0}];
  let html='<div class="sec">💚 System Health</div><div class="hgrid">'+items.map(i=>`<div class="hi"><span class="k">${i.k}</span><span class="v ${i.ok?'ok':'warn'}">${i.v}</span></div>`).join('');
  if(h.rows){html+='</div><div class="sec" style="margin-top:14px">Row Counts</div><div class="hgrid">'+Object.entries(h.rows).map(([s,n])=>`<div class="hi"><span class="k" style="font-size:0.71rem">${s}</span><span class="v">${n}</span></div>`).join('');}
  html+='</div>';
  document.getElementById('health').innerHTML=html;
}

async function resolveLoop(topic){
  const r=await api(`/api/loops/${encodeURIComponent(topic)}/resolve`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({resolution:'Resolved via Today view'})});
  toast(r.status==='written'?'✓ Loop resolved':'Status: '+r.status);await loadToday();await loadLoops();
}

async function doneTask(task){
  const r=await api('/api/tasks/complete',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({task})});
  toast(r.status==='written'?'✓ Task marked done':'Status: '+r.status);await loadToday();
}

function floatToggle(){const f=document.getElementById('fform');f.classList.toggle('open');if(f.classList.contains('open'))setTimeout(()=>document.getElementById('finput').focus(),80);}
function floatClose(){document.getElementById('fform').classList.remove('open');}
async function floatSave(){
  const el=document.getElementById('finput');const t=el.value.trim();if(!t)return;
  const r=await api('/api/inbox',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:t})});
  if(r.status==='written'){toast('✓ Captured');el.value='';floatClose();}else toast('Failed',false);
}

document.addEventListener('keydown',e=>{
  if(document.activeElement.tagName==='INPUT'||document.activeElement.tagName==='TEXTAREA')return;
  if(e.key==='i')floatToggle();
  if(e.key==='Escape')floatClose();
});


async function copyContext() {
  const btn = document.getElementById('copy-ctx-btn');
  if(btn){ btn.textContent='Copying...'; btn.disabled=true; }
  try {
    const res = await api('/api/context/markdown');
    const md  = res.markdown || '';
    if(!md){ toast('No context found', false); return; }

    // Try clipboard API
    let copied = false;
    try {
      await navigator.clipboard.writeText(md);
      copied = true;
    } catch(e) {
      // Fallback: textarea select
      const ta = document.createElement('textarea');
      ta.value = md; ta.style.position='fixed'; ta.style.opacity='0';
      document.body.appendChild(ta); ta.select();
      copied = document.execCommand('copy');
      document.body.removeChild(ta);
    }

    if(copied) {
      document.getElementById('context-toast').style.display = 'block';
      setTimeout(()=>document.getElementById('context-toast').style.display='none', 5000);
    } else {
      // Show modal with text to copy manually
      const modal = document.createElement('div');
      modal.style.cssText='position:fixed;inset:0;background:rgba(10,6,18,0.95);z-index:1000;display:flex;align-items:center;justify-content:center;padding:20px';
      modal.innerHTML=`<div style="background:#1a1228;border:1px solid #ff9933;border-radius:10px;padding:24px;max-width:700px;width:100%">
        <div style="color:#ff9933;font-weight:600;margin-bottom:12px">Copy this context</div>
        <textarea readonly style="width:100%;height:300px;background:#0c0812;border:1px solid #3d2a55;color:#fff8e6;padding:10px;border-radius:6px;font-size:0.75rem;font-family:monospace">${md}</textarea>
        <div style="margin-top:12px;display:flex;gap:10px">
          <button onclick="this.closest('div[style*=fixed]').remove()" style="background:#ff9933;color:#0c0812;border:none;padding:8px 20px;border-radius:6px;font-weight:600;cursor:pointer">Close</button>
        </div>
      </div>`;
      document.body.appendChild(modal);
    }
  } finally {
    if(btn){ btn.textContent='📋 Copy Context'; btn.disabled=false; }
  }
}

async function loadStats(){
  const s = await api('/api/stats');
  let html = '<div class="sec">📊 Memory Analytics</div>';

  // Metric cards
  const cards = [
    {n:s.total_rows||0,         l:'Total Rows'},
    {n:s.total_writes||0,       l:'Total Writes'},
    {n:s.writes_last_7_days||0, l:'Writes This Week'},
    {n:s.open_loops_total||0,   l:'Open Loops'},
    {n:(s.loop_resolution_rate||0)+'%', l:'Loop Resolution'},
    {n:s.high_importance_items||0, l:'High Importance'},
  ];
  html += '<div class="cards">'+cards.map(c=>
    `<div class="card"><div class="num">${c.n}</div><div class="lbl">${c.l}</div></div>`
  ).join('')+'</div>';

  // Writes by sheet
  if(s.writes_by_sheet && Object.keys(s.writes_by_sheet).length){
    html += '<div class="sec" style="margin-top:16px">Writes by Sheet</div>';
    const maxV = Math.max(...Object.values(s.writes_by_sheet));
    html += '<div style="margin-top:8px">';
    Object.entries(s.writes_by_sheet).forEach(([sheet,count])=>{
      const pct = Math.round((count/maxV)*100);
      html += `<div style="display:flex;align-items:center;gap:10px;margin-bottom:8px">
        <span style="min-width:180px;color:var(--dim);font-size:0.78rem">${sheet}</span>
        <div style="flex:1;height:18px;background:var(--surface2);border-radius:4px;overflow:hidden">
          <div style="width:${pct}%;height:100%;background:var(--saffron);opacity:0.7;border-radius:4px"></div>
        </div>
        <span style="min-width:24px;color:var(--saffron);font-size:0.78rem;font-weight:600">${count}</span>
      </div>`;
    });
    html += '</div>';
  }

  // Writes by agent
  if(s.writes_by_agent && Object.keys(s.writes_by_agent).length){
    html += '<div class="sec" style="margin-top:16px">Writes by Agent</div>';
    const maxA = Math.max(...Object.values(s.writes_by_agent));
    html += '<div style="margin-top:8px">';
    Object.entries(s.writes_by_agent).forEach(([agent,count])=>{
      const pct = Math.round((count/maxA)*100);
      html += `<div style="display:flex;align-items:center;gap:10px;margin-bottom:8px">
        <span style="min-width:140px;color:var(--dim);font-size:0.78rem">${agent}</span>
        <div style="flex:1;height:18px;background:var(--surface2);border-radius:4px;overflow:hidden">
          <div style="width:${pct}%;height:100%;background:var(--gold);opacity:0.7;border-radius:4px"></div>
        </div>
        <span style="min-width:24px;color:var(--gold);font-size:0.78rem;font-weight:600">${count}</span>
      </div>`;
    });
    html += '</div>';
  }

  // File size
  html += `<div class="sec" style="margin-top:16px">File</div>
    <div class="hi"><span class="k">Chitrapat size</span>
    <span class="v ok">${s.chitrapat_size_kb||0} KB</span></div>`;

  document.getElementById('stats').innerHTML = html;
}

setInterval(()=>{if(cur==='today')loadToday();},30000);
loadToday();

// ── First-launch onboarding tour ─────────────────────────────────────────────
function showTour() {
  const steps = [
    {title:"🌅 Today Tab", body:"Your daily command centre. Resolve open loops, complete tasks, and route inbox items — all with one click."},
    {title:"📥 Inbox", body:"Capture anything without categorisation. Chitragupta routes items to the right sheet later. CLI: yantra inbox 'text'. Telegram bot also sends here."},
    {title:"🔓 Open Loops (Anishtha)", body:"Unresolved threads. Flushed before context compaction and re-injected after — so your AI never forgets what's unfinished. The strongest feature."},
    {title:"📅 Timeline", body:"Chronological view of all memory activity — every write Chitragupta has made, by whom, and when."},
    {title:"⚡ Conflicts", body:"When an agent proposes a change that differs from your data. You decide which version wins — your choice is always Dharma-Adesh."},
    {title:"🔒 Security (Raksha)", body:"Prompt injection scanner, agent trust tiers, quarantine. Confirmed threats are blocked and held here for your review."},
    {title:"📒 Ledger (Agrasandhanī)", body:"The immutable audit trail. Every write is sealed with SHA-256 and permanently recorded here. Nothing is hidden, nothing lost."},
  ];
  let cur = 0;
  const overlay = document.createElement('div');
  overlay.style.cssText = 'position:fixed;inset:0;background:rgba(10,6,18,0.92);z-index:1000;display:flex;align-items:center;justify-content:center;';
  const box = document.createElement('div');
  box.style.cssText = 'background:#1a1228;border:1px solid #ff9933;border-radius:12px;padding:32px;max-width:440px;width:90%;text-align:center;';

  function render() {
    const s = steps[cur];
    box.innerHTML = `
      <div style="color:#d4af37;font-size:0.72rem;letter-spacing:0.1em;margin-bottom:12px">${cur+1} / ${steps.length}</div>
      <div style="background:#241832;border-radius:8px;height:4px;margin-bottom:20px;overflow:hidden">
        <div style="background:#ff9933;height:100%;width:${((cur+1)/steps.length)*100}%;transition:width 0.3s"></div>
      </div>
      <h2 style="color:#ff9933;font-size:1.2rem;margin-bottom:12px">${s.title}</h2>
      <p style="color:#b4a078;font-size:0.88rem;line-height:1.7;margin-bottom:24px">${s.body}</p>
      <div style="display:flex;gap:10px;justify-content:center">
        ${cur > 0 ? '<button onclick="tourNav(-1)" style="background:transparent;border:1px solid #3d2a55;color:#b4a078;padding:8px 16px;border-radius:6px;cursor:pointer">← Back</button>' : ''}
        ${cur < steps.length-1
          ? '<button onclick="tourNav(1)" style="background:#ff9933;color:#0a0612;border:none;padding:8px 20px;border-radius:6px;font-weight:600;cursor:pointer">Next →</button>'
          : '<button onclick="tourDone()" style="background:#ff9933;color:#0a0612;border:none;padding:8px 20px;border-radius:6px;font-weight:600;cursor:pointer">Start using OpenYantra ✓</button>'
        }
        <button onclick="tourDone()" style="background:transparent;border:1px solid #3d2a55;color:#b4a078;padding:8px 14px;border-radius:6px;cursor:pointer;font-size:0.75rem">Skip</button>
      </div>`;
  }

  window.tourNav = (dir) => { cur = Math.max(0, Math.min(steps.length-1, cur+dir)); render(); };
  window.tourDone = () => { overlay.remove(); localStorage.setItem('oy_toured','1'); };

  overlay.appendChild(box); document.body.appendChild(overlay);
  render();
}

// Show tour on first visit
if (!localStorage.getItem('oy_toured')) {
  setTimeout(showTour, 800);
}
</script>
</body>
</html>"""

@app.get("/", response_class=HTMLResponse)
async def root(): return DASHBOARD_HTML

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

def main():
    parser = argparse.ArgumentParser(description="OpenYantra Dashboard v2.10")
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
    print(f"\n{'='*50}\n  OpenYantra Dashboard v2.10\n  → http://{args.host}:{args.port}\n  Loops:{h.get('open_loops',0)} Inbox:{h.get('inbox_pending',0)}\n{'='*50}\n")
    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")

if __name__ == "__main__":
    main()
