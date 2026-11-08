"""Tests for first-class decision lineage and Superseded_By tracking."""

import pytest
from pathlib import Path
from openyantra.core import OpenYantra, WriteRequest, SHEET_BELIEFS


def test_supersede_belief_lifecycle(tmp_path: Path):
    chitrapat = tmp_path / "chitrapat.ods"
    oy = OpenYantra(chitrapat)

    # 1. Add an initial architectural decision / belief
    req1 = WriteRequest(
        requesting_agent="architect",
        sheet=SHEET_BELIEFS,
        operation="add",
        fields={
            "Topic": "Database Engine",
            "Position": "Use MongoDB for document storage",
            "Domain": "Architecture",
        },
        confidence="High",
        source="User-stated",
    )
    res1 = oy.request_write(req1)
    assert res1["status"] in ("written", "committed", "queued")

    # Verify it is present in active context
    ctx = oy.load_session_context()
    active_topics = [b.get("Topic") for b in ctx.get("beliefs", [])]
    assert "Database Engine" in active_topics

    # 2. Supersede the decision with a newer architectural choice
    req2 = WriteRequest(
        requesting_agent="architect",
        sheet=SHEET_BELIEFS,
        operation="supersede",
        row_identifier="Database Engine",
        fields={
            "Superseded_By": "PostgreSQL with JSONB (decided 2026-11-08)",
            "Notes": "Migrated from Mongo to Postgres for ACID guarantees",
        },
        confidence="High",
        source="User-stated",
    )
    res2 = oy.request_write(req2)
    assert res2["status"] in ("written", "committed", "queued")

    # 3. Verify that load_session_context() strictly excludes the superseded belief
    ctx_after = oy.load_session_context()
    active_after = [b.get("Topic") for b in ctx_after.get("beliefs", [])]
    assert "Database Engine" not in active_after

    # 4. Verify sheet inspection preserves the full lineage and pointer
    beliefs_raw = oy._read_sheet(SHEET_BELIEFS)
    superseded_row = next((r for r in beliefs_raw if r.get("Topic") == "Database Engine"), None)
    assert superseded_row is not None
    assert "PostgreSQL" in str(superseded_row.get("Superseded_By", ""))
