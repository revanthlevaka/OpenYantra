import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import pandas as pd

from openyantra.yantra_sqlite import SyncEngine, validate_ods_headers
from openyantra.yantra_context import run_context, build_context_markdown

@pytest.fixture
def temp_dir():
    d = tempfile.mkdtemp()
    yield Path(d)
    shutil.rmtree(d)

@pytest.fixture
def sync_engine(temp_dir):
    db_path = temp_dir / "chitrapat.db"
    ods_path = temp_dir / "chitrapat.ods"
    
    # Create a basic ODS file to start with, or copy the template
    template_src = Path(__file__).parent.parent / "openyantra" / "chitrapat_template.ods"
    if template_src.exists():
        shutil.copy2(template_src, ods_path)
    else:
        # Fallback empty ODS creation
        with pd.ExcelWriter(str(ods_path), engine="odf") as writer:
            pd.DataFrame().to_excel(writer, sheet_name="👤 Identity")
            
    engine = SyncEngine(db_path, ods_path)
    yield engine

def test_libreoffice_lockfile_detection(sync_engine, temp_dir):
    ods_path = sync_engine.ods_path
    
    # 1. Create a dummy LibreOffice lockfile sidecar
    lockfile_path = ods_path.parent / f".~lock.{ods_path.name}#"
    lockfile_path.write_text("dummy lock content", encoding="utf-8")
    
    # Make a write to SQLite so there is something to export
    res = sync_engine.write(
        table="identity",
        fields={"attribute": "Name", "value": "Revanth"},
        request_id="req-123",
        operation="add"
    )
    assert res["status"] == "written"
    
    # Write to ledger to advance the sequence ID
    res_ledger = sync_engine.write(
        table="ledger",
        fields={
            "timestamp": "2026-05-21T12:00:00",
            "request_id": "req-123-ledger",
            "agent": "test-agent",
            "sheet": "identity",
            "operation": "add",
            "row_identifier": "Name",
            "status": "written",
            "confidence": "High",
            "source": "User-stated",
            "importance": 8,
            "signature": "dummy-sig",
            "reason_notes": ""
        },
        request_id="req-123-ledger",
        operation="add"
    )
    assert res_ledger["status"] == "written"
    
    # 2. Attempt to export ODS. Should fail/defer because of the lockfile.
    success = sync_engine.export_ods()
    assert success is False
    
    # 3. Verify failed entry in _sync_state
    failed_syncs = sync_engine.read("_sync_state", "status='failed'")
    assert len(failed_syncs) > 0
    assert failed_syncs[0]["sequence_id"] == res_ledger["row_id"]
    
    # 4. Remove LibreOffice lockfile
    lockfile_path.unlink()
    
    # 5. Export again. Should now succeed.
    success_retry = sync_engine.export_ods()
    assert success_retry is True
    
    # 6. Verify success entry in _sync_state
    success_syncs = sync_engine.read("_sync_state", "status='success'")
    assert len(success_syncs) > 0
    assert success_syncs[0]["sequence_id"] == res_ledger["row_id"]

def test_sync_wal_reconciliation(temp_dir):
    db_path = temp_dir / "chitrapat.db"
    ods_path = temp_dir / "chitrapat.ods"
    
    # Copy template to ODS path
    template_src = Path(__file__).parent.parent / "openyantra" / "chitrapat_template.ods"
    if template_src.exists():
        shutil.copy2(template_src, ods_path)
    else:
        # Fallback empty ODS creation
        with pd.ExcelWriter(str(ods_path), engine="odf") as writer:
            pd.DataFrame().to_excel(writer, sheet_name="👤 Identity")
            
    # Initialize engine
    engine = SyncEngine(db_path, ods_path)
    
    # Make a write to SQLite
    res = engine.write(
        table="identity",
        fields={"attribute": "Name", "value": "Revanth"},
        request_id="req-123",
        operation="add"
    )
    assert res["status"] == "written"
    
    res_ledger = engine.write(
        table="ledger",
        fields={
            "timestamp": "2026-05-21T12:00:00",
            "request_id": "req-123-ledger",
            "agent": "test-agent",
            "sheet": "identity",
            "operation": "add",
            "row_identifier": "Name",
            "status": "written",
            "confidence": "High",
            "source": "User-stated",
            "importance": 8,
            "signature": "dummy-sig",
            "reason_notes": ""
        },
        request_id="req-123-ledger",
        operation="add"
    )
    assert res_ledger["status"] == "written"
    
    # We do NOT export_ods yet, so _sync_state has no 'success' records.
    # Now simulate a crash/restart by creating a new SyncEngine instance with the same DB.
    # On startup, the new instance should call reconcile() and trigger export_ods() automatically.
    engine_restart = SyncEngine(db_path, ods_path)
    
    # Verify that a successful sync state was created for the write
    success_syncs = engine_restart.read("_sync_state", "status='success'")
    assert len(success_syncs) > 0
    assert success_syncs[0]["sequence_id"] == res_ledger["row_id"]

def test_ods_header_validation(temp_dir):
    ods_path = temp_dir / "chitrapat.ods"
    
    # Copy template to ODS path
    template_src = Path(__file__).parent.parent / "openyantra" / "chitrapat_template.ods"
    assert template_src.exists(), "Template file must exist for this test"
    shutil.copy2(template_src, ods_path)
    
    # 1. Validation on the valid template should pass (no errors)
    errors = validate_ods_headers(ods_path)
    assert len(errors) == 0, f"Expected no errors on template, got: {errors}"
    
    # 2. Modify ODS to make headers invalid (e.g. read, drop a column, write back)
    # Read the '👤 Identity' sheet
    df = pd.read_excel(str(ods_path), sheet_name="👤 Identity", engine="odf")
    # Drop 'Confidence' column if it exists
    if "Confidence" in df.columns:
        df = df.drop(columns=["Confidence"])
    
    # Write it back to a modified ODS
    # We must write all sheets or at least the modified one
    xl = pd.ExcelFile(str(ods_path), engine="odf")
    sheets = {name: pd.read_excel(str(ods_path), sheet_name=name, engine="odf") for name in xl.sheet_names}
    sheets["👤 Identity"] = df
    
    with pd.ExcelWriter(str(ods_path), engine="odf") as writer:
        for name, sheet_df in sheets.items():
            sheet_df.to_excel(writer, sheet_name=name, index=False)
            
    # 3. Validation should now fail indicating missing columns
    errors_after = validate_ods_headers(ods_path)
    assert len(errors_after) > 0
    assert any("Identity" in err and "Confidence" in err for err in errors_after)
    
    # 4. import_ods() should return the header validation errors
    db_path = temp_dir / "chitrapat.db"
    engine = SyncEngine(db_path, ods_path)
    import_res = engine.import_ods()
    assert import_res["error"] == "ODS header validation failed"
    assert len(import_res["details"]) > 0

def test_1mb_clipboard_guard(temp_dir):
    ods_path = temp_dir / "chitrapat.ods"
    db_path = temp_dir / "chitrapat.db"
    
    template_src = Path(__file__).parent.parent / "openyantra" / "chitrapat_template.ods"
    if template_src.exists():
        shutil.copy2(template_src, ods_path)
        
    engine = SyncEngine(db_path, ods_path)
    
    # Mock OpenYantra load_session_context to return a very large payload
    # Or just mock build_context_markdown to return a >1MB string
    large_markdown = "A" * (1024 * 1024 + 10)  # > 1MB
    
    with patch("openyantra.yantra_context.build_context_markdown", return_value=large_markdown) as mock_build, \
         patch("openyantra.yantra_context.copy_to_clipboard", return_value=True) as mock_copy, \
         patch("openyantra.yantra_context.OpenYantra") as mock_oy:
         
        mock_oy.return_value.compile_context.return_value = {"markdown": large_markdown, "tokens": 1234}
        # Run context on the dummy file
        markdown_res = run_context(str(ods_path))
        
        # Verify fallback file creation
        fallback_file = Path("~/.openyantra/active_context.md").expanduser()
        assert fallback_file.exists()
        assert len(fallback_file.read_text(encoding="utf-8")) > 1024 * 1024
        
        # Verify that copy_to_clipboard was called with the path, not the content
        mock_copy.assert_called_once_with(str(fallback_file))
        
        # Clean up fallback file
        fallback_file.unlink(missing_ok=True)
