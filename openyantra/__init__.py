"""OpenYantra -- The Sacred Memory Machine v6.2.0 (Akasha & Sutra)"""

from openyantra.core import (
    OpenYantra,
    WriteRequest,
    run_bootstrap_interview,
    is_superseded,
    detect_active_project,
    SHEET_IDENTITY, SHEET_GOALS, SHEET_PROJECTS, SHEET_PEOPLE,
    SHEET_PREFERENCES, SHEET_BELIEFS, SHEET_TASKS, SHEET_OPEN_LOOPS,
    SHEET_SESSION_LOG, SHEET_AGENT_CONFIG, SHEET_LEDGER,
    SHEET_INBOX, SHEET_CORRECTIONS, SHEET_QUARANTINE, SHEET_SECURITY_LOG
)
from openyantra.yantra_nidra import NidraConsolidator
from openyantra.yantra_vault import VaultSync
from openyantra.mcp_setup import setup_mcp_config, auto_setup_clients
from openyantra.yantra_git import install_git_hook, ingest_last_commit
from openyantra.desktop import launch_desktop
from openyantra.yantra_tui import render_tui

__version__ = "6.2.0"
__all__ = [
    "OpenYantra",
    "WriteRequest",
    "run_bootstrap_interview",
    "is_superseded",
    "detect_active_project",
    "NidraConsolidator",
    "VaultSync",
    "setup_mcp_config",
    "auto_setup_clients",
    "install_git_hook",
    "ingest_last_commit",
    "launch_desktop",
    "render_tui",
    "SHEET_IDENTITY",
    "SHEET_GOALS",
    "SHEET_PROJECTS",
    "SHEET_PEOPLE",
    "SHEET_PREFERENCES",
    "SHEET_BELIEFS",
    "SHEET_TASKS",
    "SHEET_OPEN_LOOPS",
    "SHEET_SESSION_LOG",
    "SHEET_AGENT_CONFIG",
    "SHEET_LEDGER",
    "SHEET_INBOX",
    "SHEET_CORRECTIONS",
    "SHEET_QUARANTINE",
    "SHEET_SECURITY_LOG",
    "__version__"
]
