import pytest
from openyantra.core import OpenYantra, WriteRequest, SHEET_BELIEFS, SHEET_LEDGER
from openyantra.cognitive_db import CognitiveMemoryStore
from openyantra import cognitive_mcp as mcp_mod


@pytest.fixture
def temp_cognitive_db(tmp_path):
    db_file = tmp_path / "cognitive_memories.json"
    return CognitiveMemoryStore(file_path=str(db_file))


def test_cognitive_db_tombstone(temp_cognitive_db):
    store = temp_cognitive_db
    # 1. Write an initial memory
    store.write("database_arch", "decision", "CTO", "Use CockroachDB for multi-region")
    assert store.read("database_arch") is not None

    # 2. Delete with tombstone
    deleted = store.delete("database_arch", tombstone=True)
    assert deleted is True
    assert store.read("database_arch") is None
    assert store.is_tombstoned("database_arch") is True

    # 3. Attempt to re-write without override -> rejected via ValueError
    with pytest.raises(ValueError, match="Tombstone exists"):
        store.write("database_arch", "decision", "CTO", "Revive CockroachDB")

    # 4. Attempt to re-write with override_tombstone=True -> succeeds
    res = store.write("database_arch", "decision", "CTO", "Deliberately reviving CockroachDB", override_tombstone=True)
    assert res is not None
    assert res["content"] == "Deliberately reviving CockroachDB"
    assert store.is_tombstoned("database_arch") is False


def test_workbook_belief_tombstone(tmp_path):
    ods_path = tmp_path / "chitrapat.ods"
    oy = OpenYantra(path=ods_path)
    oy.bootstrap("TestUser")

    # 1. Add active belief
    res1 = oy.request_write(WriteRequest(
        requesting_agent="User",
        sheet=SHEET_BELIEFS,
        operation="add",
        fields={
            "Topic": "ORM Choice",
            "Position": "Always use Prisma ORM",
            "Domain": "Engineering",
            "Confidence": "High",
            "Source": "User-stated",
            "Importance": 8,
        },
        confidence="High",
        source="User-stated",
        importance=8
    ))
    assert res1.get("status") == "written"

    # 2. Supersede the belief
    res2 = oy.request_write(WriteRequest(
        requesting_agent="User",
        sheet=SHEET_BELIEFS,
        operation="supersede",
        row_identifier="ORM Choice",
        fields={"Superseded_By": "Adopted Drizzle ORM in ADR 004"},
        confidence="High",
        source="User-stated"
    ))
    assert res2.get("status") == "written"

    # 3. Attempt to add or re-assert the exact superseded position -> Tombstone rejection
    res3 = oy.request_write(WriteRequest(
        requesting_agent="JuniorDev",
        sheet=SHEET_BELIEFS,
        operation="add",
        fields={
            "Topic": "ORM Preference",
            "Position": "Always use Prisma ORM",
            "Domain": "Engineering",
            "Confidence": "Medium",
        },
        confidence="Medium",
        source="Agent-observed"
    ))
    assert res3.get("status") == "rejected"
    assert "Tombstone conflict" in res3.get("reason", "")

    # Verify rejection is audited in Agrasandhanī ledger
    ledger = oy._read_sheet(SHEET_LEDGER)
    rejections = [r for r in ledger if r.get("Status") == "rejected" and "Tombstone" in str(r.get("Reason / Notes", "") or r.get("Reason", ""))]
    assert len(rejections) >= 1

    # 4. Attempt to write with explicit override_tombstone -> succeeds
    res4 = oy.request_write(WriteRequest(
        requesting_agent="CTO",
        sheet=SHEET_BELIEFS,
        operation="add",
        fields={
            "Topic": "ORM Preference Revival",
            "Position": "Always use Prisma ORM",
            "Domain": "Engineering",
            "Confidence": "High",
            "override_tombstone": True,
        },
        confidence="High",
        source="User-stated",
        importance=9
    ))
    assert res4.get("status") == "written"


def test_cognitive_mcp_tombstone(temp_cognitive_db, monkeypatch):
    monkeypatch.setattr(mcp_mod, "db", temp_cognitive_db)

    # 1. memory_write
    res = mcp_mod.handle_call_tool(1, {
        "name": "memory_write",
        "arguments": {
            "key": "cloud_provider",
            "type": "decision",
            "agent": "Architect",
            "content": "All services hosted on GCP"
        }
    })
    assert "content" in res["result"]["content"][0]["text"]

    # 2. memory_delete (tombstone)
    res_del = mcp_mod.handle_call_tool(2, {
        "name": "memory_delete",
        "arguments": {"key": "cloud_provider"}
    })
    assert "Delete successful: True" in res_del["result"]["content"][0]["text"]

    # 3. memory_write again -> returns error response due to tombstone
    res_fail = mcp_mod.handle_call_tool(3, {
        "name": "memory_write",
        "arguments": {
            "key": "cloud_provider",
            "type": "decision",
            "agent": "Architect",
            "content": "Hosting on AWS"
        }
    })
    assert res_fail["result"]["isError"] is True
    assert "Tombstone exists" in res_fail["result"]["content"][0]["text"]

    # 4. memory_write with override_tombstone -> succeeds
    res_override = mcp_mod.handle_call_tool(4, {
        "name": "memory_write",
        "arguments": {
            "key": "cloud_provider",
            "type": "decision",
            "agent": "Architect",
            "content": "Hosting on AWS",
            "override_tombstone": True
        }
    })
    assert "result" in res_override
