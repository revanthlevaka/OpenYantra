"""
tests/test_nidra_apple_fm.py -- Unit tests for Apple Foundation Model (AFM) inference integration
and user opt-out controls in OpenYantra Nidra.
"""

import os
import subprocess
import sys
from unittest.mock import MagicMock, patch
import pytest

from openyantra.core import OpenYantra
from openyantra.yantra_nidra import NidraConsolidator


@pytest.fixture
def mock_oy(tmp_path):
    oy_file = tmp_path / "chitrapat.ods"
    oy = OpenYantra(oy_file)
    oy.bootstrap(user_name="Apple Dev", occupation="Software Architect")
    return oy


# ── AFM Availability & License Checks ─────────────────────────────────────────

def test_afm_not_darwin(mock_oy):
    nidra = NidraConsolidator(mock_oy)
    with patch("sys.platform", "linux"):
        avail, status = nidra.is_apple_fm_available()
        assert avail is False
        assert status is None


def test_afm_binary_missing(mock_oy):
    nidra = NidraConsolidator(mock_oy)
    with patch("sys.platform", "darwin"), patch("shutil.which", return_value=None), patch("os.path.exists", return_value=False):
        avail, status = nidra.is_apple_fm_available()
        assert avail is False
        assert status is None


def test_afm_unlicensed(mock_oy):
    nidra = NidraConsolidator(mock_oy)
    mock_run = MagicMock()
    mock_run.returncode = 69
    mock_run.stdout = "Not agreed. Run 'sudo fm license' to review and agree."
    mock_run.stderr = ""

    with patch("sys.platform", "darwin"), \
         patch("shutil.which", return_value="/usr/bin/fm"), \
         patch("os.path.exists", return_value=True), \
         patch("os.access", return_value=True), \
         patch("subprocess.run", return_value=mock_run):
        avail, status = nidra.is_apple_fm_available()
        assert avail is False
        assert status == "license_required"


def test_afm_licensed_and_ready(mock_oy):
    nidra = NidraConsolidator(mock_oy)
    mock_run = MagicMock()
    mock_run.returncode = 0
    mock_run.stdout = "License status: Agreed"
    mock_run.stderr = ""

    with patch("sys.platform", "darwin"), \
         patch("shutil.which", return_value="/usr/bin/fm"), \
         patch("os.path.exists", return_value=True), \
         patch("os.access", return_value=True), \
         patch("subprocess.run", return_value=mock_run):
        avail, status = nidra.is_apple_fm_available()
        assert avail is True
        assert status == "system"


# ── AFM Query Execution ───────────────────────────────────────────────────────

def test_query_apple_fm_success(mock_oy):
    nidra = NidraConsolidator(mock_oy)
    mock_run = MagicMock()
    mock_run.returncode = 0
    mock_run.stdout = "  Consolidated 2 sessions on ANE. All systems operational.  \n"
    mock_run.stderr = ""

    with patch("subprocess.run", return_value=mock_run):
        res = nidra.query_apple_fm("Test prompt")
        assert res == "Consolidated 2 sessions on ANE. All systems operational."


def test_query_apple_fm_failure(mock_oy):
    nidra = NidraConsolidator(mock_oy)
    mock_run = MagicMock()
    mock_run.returncode = 1
    mock_run.stdout = ""
    mock_run.stderr = "Error: model unavailable"

    with patch("subprocess.run", return_value=mock_run):
        res = nidra.query_apple_fm("Test prompt")
        assert res is None


def test_query_apple_fm_default_timeout(mock_oy):
    nidra = NidraConsolidator(mock_oy)
    mock_run = MagicMock(returncode=0, stdout="Success", stderr="")

    with patch("subprocess.run", return_value=mock_run) as mock_sub:
        nidra.query_apple_fm("Test prompt")
        assert mock_sub.call_args is not None
        assert mock_sub.call_args[1].get("timeout") == 5.0


def test_query_apple_fm_custom_timeout_env(mock_oy):
    nidra = NidraConsolidator(mock_oy)
    mock_run = MagicMock(returncode=0, stdout="Success", stderr="")

    with patch.dict(os.environ, {"OPENYANTRA_NIDRA_TIMEOUT": "2.5"}), \
         patch("subprocess.run", return_value=mock_run) as mock_sub:
        nidra.query_apple_fm("Test prompt")
        assert mock_sub.call_args is not None
        assert mock_sub.call_args[1].get("timeout") == 2.5


# ── Provider Resolution & Cascade ─────────────────────────────────────────────

def test_resolve_provider_auto_on_mac_with_afm(mock_oy):
    nidra = NidraConsolidator(mock_oy)
    with patch("sys.platform", "darwin"), \
         patch.object(nidra, "is_apple_fm_available", return_value=(True, "system")), \
         patch.dict(os.environ, {}, clear=True):
        provider, model, notice = nidra.resolve_provider("auto")
        assert provider == "apple-fm"
        assert model == "system"
        assert notice is None


def test_resolve_provider_auto_on_mac_unlicensed_falls_back_to_ollama(mock_oy):
    nidra = NidraConsolidator(mock_oy)
    with patch("sys.platform", "darwin"), \
         patch.object(nidra, "is_apple_fm_available", return_value=(False, "license_required")), \
         patch.object(nidra, "is_ollama_available", return_value=(True, "mistral")), \
         patch.dict(os.environ, {}, clear=True):
        provider, model, notice = nidra.resolve_provider("auto")
        assert provider == "ollama"
        assert model == "mistral"
        assert "sudo fm license" in notice


def test_resolve_provider_auto_on_mac_unlicensed_falls_back_to_heuristic(mock_oy):
    nidra = NidraConsolidator(mock_oy)
    with patch("sys.platform", "darwin"), \
         patch.object(nidra, "is_apple_fm_available", return_value=(False, "license_required")), \
         patch.object(nidra, "is_ollama_available", return_value=(False, None)), \
         patch.dict(os.environ, {}, clear=True):
        provider, model, notice = nidra.resolve_provider("auto")
        assert provider == "heuristic"
        assert model is None
        assert "sudo fm license" in notice


def test_resolve_provider_auto_on_linux(mock_oy):
    nidra = NidraConsolidator(mock_oy)
    with patch("sys.platform", "linux"), \
         patch.object(nidra, "is_ollama_available", return_value=(True, "llama3")), \
         patch.dict(os.environ, {}, clear=True):
        provider, model, notice = nidra.resolve_provider("auto")
        assert provider == "ollama"
        assert model == "llama3"


# ── User Opt-Out Tests ────────────────────────────────────────────────────────

def test_user_opt_out_via_provider_param_heuristic(mock_oy):
    """User specifies --provider heuristic; AFM must be bypassed even if ready."""
    nidra = NidraConsolidator(mock_oy)
    with patch.object(nidra, "is_apple_fm_available", return_value=(True, "system")):
        provider, model, notice = nidra.resolve_provider("heuristic")
        assert provider == "heuristic"
        assert model is None


def test_user_opt_out_via_provider_param_ollama(mock_oy):
    """User specifies --provider ollama; AFM must be bypassed in favor of Ollama."""
    nidra = NidraConsolidator(mock_oy)
    with patch.object(nidra, "is_apple_fm_available", return_value=(True, "system")), \
         patch.object(nidra, "is_ollama_available", return_value=(True, "qwen2.5")):
        provider, model, notice = nidra.resolve_provider("ollama")
        assert provider == "ollama"
        assert model == "qwen2.5"


def test_user_opt_out_via_env_var(mock_oy):
    """User sets OPENYANTRA_NIDRA_PROVIDER=ollama; auto request respects override."""
    nidra = NidraConsolidator(mock_oy)
    with patch.object(nidra, "is_apple_fm_available", return_value=(True, "system")), \
         patch.object(nidra, "is_ollama_available", return_value=(True, "codellama")), \
         patch.dict(os.environ, {"OPENYANTRA_NIDRA_PROVIDER": "ollama"}):
        provider, model, notice = nidra.resolve_provider("auto")
        assert provider == "ollama"
        assert model == "codellama"


def test_user_opt_out_via_env_var_heuristic(mock_oy):
    """User sets OPENYANTRA_NIDRA_PROVIDER=heuristic; strictly bypasses all LLMs."""
    nidra = NidraConsolidator(mock_oy)
    with patch.object(nidra, "is_apple_fm_available", return_value=(True, "system")), \
         patch.dict(os.environ, {"OPENYANTRA_NIDRA_PROVIDER": "heuristic"}):
        provider, model, notice = nidra.resolve_provider("auto")
        assert provider == "heuristic"
        assert model is None


# ── Full Consolidation Workflow with AFM ──────────────────────────────────────

def test_full_consolidation_with_apple_fm(mock_oy):
    mock_oy.log_session(
        topics=["Apple Neural Engine Integration"],
        decisions=["Configured AFM as default on-device inference engine"],
        notes="Project: OpenYantra"
    )

    nidra = NidraConsolidator(mock_oy)
    with patch("sys.platform", "darwin"), \
         patch.object(nidra, "is_apple_fm_available", return_value=(True, "system")), \
         patch.object(nidra, "query_apple_fm", return_value="AFM synthesized episodic summary on Apple Neural Engine."):
        report = nidra.consolidate(dry_run=False, provider="auto")
        assert report["provider_used"] == "apple-fm (system)"
        assert "AFM synthesized" in report["summary"]

        # Verify session log entry reflects the AFM summary
        sessions = mock_oy.get_sheet("Session Log")
        last_s = sessions[-1]
        assert "AFM synthesized" in str(last_s.get("Decisions Made", ""))
