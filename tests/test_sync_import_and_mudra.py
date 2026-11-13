"""
tests/test_sync_import_and_mudra.py -- Verification tests for:
1. SyncEngine.import_ods() full sync from ODS to SQLite tables and edge inference
2. Mudra cryptographic seal verification and tamper detection
3. Pluggable external routing hook (Plexus / Apical Arbor pattern)
"""

from openyantra.core import OpenYantra, WriteRequest, SHEET_TASKS, SHEET_BELIEFS
from openyantra.yantra_security import get_raksha
from openyantra.yantra_sqlite import SyncEngine


def test_import_ods_syncs_to_sqlite(tmp_path):
    chitrapat = tmp_path / "chitrapat.ods"
    db_file = tmp_path / "chitrapat.db"

    oy = OpenYantra(chitrapat)
    oy.bootstrap(user_name="Sync Tester", occupation="Developer")

    # Add task and open loop directly via OpenYantra workbook
    oy.add_task(task="Refactor SQLite bridge", project="OpenYantra", priority="High")
    oy.add_open_loop(topic="Cache invalidation protocol", context="Review TTL", related_project="OpenYantra")

    engine = SyncEngine(db_file, chitrapat)
    report = engine.import_ods(chitrapat)

    assert "error" not in report
    assert report.get("imported", 0) >= 2

    # Verify rows in SQLite tables
    tasks = engine.read("tasks")
    assert any(t.get("task") == "Refactor SQLite bridge" for t in tasks)

    loops = engine.read("open_loops")
    assert any(l.get("topic") == "Cache invalidation protocol" for l in loops)

    # Verify edge auto-inference during import
    edges = engine.get_edges(source_type="tasks")
    assert any(e.get("source_id") == "Refactor SQLite bridge" and e.get("target_id") == "OpenYantra" for e in edges)


def test_verify_mudra_cryptographic_seal(tmp_path):
    chitrapat = tmp_path / "chitrapat.ods"
    oy = OpenYantra(chitrapat)
    oy.bootstrap(user_name="Seal Tester", occupation="Cryptographer")

    req = WriteRequest(
        requesting_agent="AuditAgent",
        sheet=SHEET_BELIEFS,
        operation="add",
        fields={"Topic": "Decentralized State", "Position": "Local-first files are king"},
        confidence="High",
        source="Agent-observed",
        importance=8,
    )
    res = oy.request_write(req)
    assert res["status"] == "written"
    mudra = res["signature"]

    # Verify with OpenYantra and LedgerAgent
    assert oy.verify_request_signature(req, mudra) is True

    # Tampering with request field MUST invalidate signature
    tampered_req = WriteRequest(
        requesting_agent="AuditAgent",
        sheet=SHEET_BELIEFS,
        operation="add",
        fields={"Topic": "Decentralized State", "Position": "Cloud-first is king"},  # Tampered
        confidence="High",
        source="Agent-observed",
        importance=8,
        request_id=req.request_id,
        timestamp=req.timestamp,
    )
    assert oy.verify_request_signature(tampered_req, mudra) is False

    # Verify with Raksha
    raksha = get_raksha()
    assert raksha.verify_mudra(
        req.fields, req.requesting_agent, req.sheet, req.operation, mudra, request_dict=req.to_dict()
    ) is True
    assert raksha.verify_mudra(
        tampered_req.fields, tampered_req.requesting_agent, tampered_req.sheet, tampered_req.operation, mudra, request_dict=tampered_req.to_dict()
    ) is False


def test_pluggable_external_router(tmp_path):
    chitrapat = tmp_path / "chitrapat.ods"
    oy = OpenYantra(chitrapat)
    oy.bootstrap(user_name="Router Tester", occupation="Architect")

    # Define mock external router function (simulating Plexus / Apical Arbor hook)
    def mock_plexus_router(prompt: str, top_k: int = 2):
        if "fast path" in prompt:
            return [{"sheet": SHEET_TASKS, "score": 0.999}]
        return None

    oy.set_external_router(mock_plexus_router)

    routed = oy.route("Execute fast path immediately")
    assert len(routed) == 1
    assert routed[0]["sheet"] == SHEET_TASKS
    assert routed[0]["score"] == 0.999

    # Unplug router and verify normal centroid fallback works without crashing
    oy.set_external_router(None)
    fallback_routed = oy.route("Any prompt")
    assert isinstance(fallback_routed, list)
