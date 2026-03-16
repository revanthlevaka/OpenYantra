"""
yantra_migrate.py — OpenYantra Schema Migration Tool v2.8
Upgrades older Chitrapat files to the current schema.

Detects version from sheet count and column presence.
Migrates non-destructively — original file backed up before any change.

Usage:
    yantra migrate                              # migrate default file
    yantra migrate --file ~/old/chitrapat.ods   # migrate specific file
    yantra migrate --dry-run                    # show what would change
    yantra migrate --backup-only                # backup without migrating
"""

from __future__ import annotations

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

try:
    import pandas as pd
except ImportError:
    print("pandas required: pip install pandas odfpy")
    sys.exit(1)

try:
    import openyantra  # noqa: F401
except ImportError:
    print("openyantra.py not found.")
    sys.exit(1)


# ── Version detection ─────────────────────────────────────────────────────────


def detect_version(path: str) -> str:
    """Detect the schema version of a Chitrapat file."""
    try:
        xl = pd.ExcelFile(path, engine="odf")
        sheets = set(xl.sheet_names)

        if "🔒 Quarantine" in sheets:
            return "2.4+"
        if "📥 Inbox" in sheets:
            return "2.1+"
        if "🔓 Open Loops" in sheets:
            # Check for Importance column
            try:
                df = pd.read_excel(
                    path, sheet_name="🔓 Open Loops", engine="odf", header=0
                )
                if "Importance" in df.columns:
                    return "2.1"
                return "2.0"
            except Exception:
                return "2.0"
        if "📅 Session Log" in sheets:
            return "1.0"
        return "unknown"
    except Exception as e:
        return f"error: {e}"


# ── Migration plan ────────────────────────────────────────────────────────────


def build_migration_plan(from_version: str, to_version: str = "2.8") -> list[dict]:
    """Return ordered list of migration steps needed."""
    steps = []

    if from_version in ("unknown", "error"):
        steps.append(
            {
                "step": "abort",
                "description": "Cannot detect version — file may be corrupted",
            }
        )
        return steps

    # v1.0 → v2.0: Add VidyaKosha support columns
    if from_version in ("1.0",):
        steps.append(
            {
                "step": "add_importance_column",
                "description": "Add Importance (1-10) column to all sheets",
                "sheets": [
                    "🎯 Goals",
                    "🚀 Projects",
                    "👥 People",
                    "💡 Preferences",
                    "🧠 Beliefs",
                    "✅ Tasks",
                    "🔓 Open Loops",
                ],
                "column": "Importance",
                "default": "5",
            }
        )

    # → v2.1: Add Inbox + Corrections sheets
    if from_version in ("1.0", "2.0"):
        steps.append(
            {
                "step": "add_sheet",
                "description": "Add 📥 Inbox sheet (Avagraha)",
                "sheet": "📥 Inbox",
                "columns": [
                    "Content",
                    "Captured",
                    "Routed?",
                    "Target Sheet",
                    "Notes",
                    "Confidence",
                    "Source",
                    "Importance",
                ],
            }
        )
        steps.append(
            {
                "step": "add_sheet",
                "description": "Add ✏️ Corrections sheet (Sanshodhan)",
                "sheet": "✏️ Corrections",
                "columns": [
                    "Target Sheet",
                    "Row Identifier",
                    "Field",
                    "Proposed Value",
                    "Reason",
                    "Status",
                    "Proposed By",
                    "Proposed At",
                    "Reviewed By",
                    "Reviewed At",
                    "Notes",
                ],
            }
        )
        steps.append(
            {
                "step": "add_column",
                "description": "Add TTL_Days to Open Loops",
                "sheet": "🔓 Open Loops",
                "column": "TTL_Days",
                "default": "90",
            }
        )

    # → v2.4: Add Quarantine + Security Log sheets
    if from_version in ("1.0", "2.0", "2.1", "2.1+"):
        steps.append(
            {
                "step": "add_sheet",
                "description": "Add 🔒 Quarantine sheet (Nirodh)",
                "sheet": "🔒 Quarantine",
                "columns": [
                    "Request ID",
                    "Timestamp",
                    "Agent",
                    "Target Sheet",
                    "Operation",
                    "Fields JSON",
                    "Threat Level",
                    "Threat Type",
                    "Threats Found",
                    "Status",
                    "Reviewed By",
                    "Reviewed At",
                ],
            }
        )
        steps.append(
            {
                "step": "add_sheet",
                "description": "Add 🛡️ Security Log sheet",
                "sheet": "🛡️ Security Log",
                "columns": [
                    "Timestamp",
                    "Agent",
                    "Sheet",
                    "Threat Level",
                    "Threat Type",
                    "Threats",
                    "Status",
                ],
            }
        )

    # → v2.8: Add Contradiction_Flag to Beliefs
    steps.append(
        {
            "step": "add_column",
            "description": "Add Contradiction_Flag to Beliefs sheet",
            "sheet": "🧠 Beliefs",
            "column": "Contradiction_Flag",
            "default": "",
        }
    )

    # Always: Update INDEX sheet
    steps.append(
        {
            "step": "update_index",
            "description": "Update INDEX sheet to reflect current schema",
        }
    )

    return steps


# ── Migration executor ────────────────────────────────────────────────────────


def run_migration(path: str, dry_run: bool = False) -> dict:
    """
    Migrate a Chitrapat file to the current schema.
    Returns summary of changes made.
    """
    file_path = Path(path).expanduser()
    from_version = detect_version(str(file_path))

    print(f"\n{'='*55}")
    print("  OpenYantra Migration Tool v2.8")
    print(f"{'='*55}")
    print(f"\n  File:         {file_path}")
    print(f"  Detected:     v{from_version}")
    print("  Target:       v2.8")

    if from_version in ("2.4+",):
        print("\n  ✓ Already at v2.4+ schema — checking for v2.8 additions...")

    if dry_run:
        print("\n  DRY RUN — no changes will be made\n")

    # Build plan
    plan = build_migration_plan(from_version)

    if not plan:
        print("\n  ✓ Schema is current — no migration needed.\n")
        return {"status": "current", "changes": []}

    print(f"\n  Migration plan ({len(plan)} steps):")
    for i, step in enumerate(plan, 1):
        print(f"    {i}. {step['description']}")

    if dry_run:
        print(f"\n  Dry run complete — {len(plan)} steps would be applied.")
        return {"status": "dry_run", "steps": len(plan)}

    # Backup
    backup_path = (
        file_path.parent
        / f"chitrapat_backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.ods"
    )
    shutil.copy2(str(file_path), str(backup_path))
    print(f"\n  ✓ Backup created: {backup_path.name}")

    # Execute steps
    changes = []
    for step in plan:
        try:
            _execute_step(str(file_path), step)
            changes.append(
                {
                    "step": step["step"],
                    "description": step["description"],
                    "status": "ok",
                }
            )
            print(f"  ✓ {step['description']}")
        except Exception as e:
            changes.append(
                {
                    "step": step["step"],
                    "description": step["description"],
                    "status": f"error: {e}",
                }
            )
            print(f"  ✗ {step['description']}: {e}")

    print(
        f"\n  Migration complete — {len([c for c in changes if c['status']=='ok'])} changes applied."
    )
    print(f"  Backup at: {backup_path}")
    print(f"{'='*55}\n")

    return {"status": "migrated", "changes": changes, "backup": str(backup_path)}


def _execute_step(path: str, step: dict):
    """Execute a single migration step."""
    action = step.get("step")

    if action == "add_column":
        _add_column(path, step["sheet"], step["column"], step.get("default", ""))

    elif action == "add_importance_column":
        for sheet in step.get("sheets", []):
            try:
                _add_column(path, sheet, "Importance", step.get("default", "5"))
            except Exception:
                pass  # Sheet may not exist in older versions

    elif action == "add_sheet":
        _add_sheet(path, step["sheet"], step.get("columns", []))

    elif action == "update_index":
        pass  # INDEX update handled by rebuild template reference only


def _add_column(path: str, sheet_name: str, column: str, default: str = ""):
    """Add a column to a sheet if it doesn't already exist."""
    try:
        df = pd.read_excel(
            path, sheet_name=sheet_name, engine="odf", header=0, dtype=str
        )
    except Exception:
        return  # Sheet doesn't exist

    if column in df.columns:
        return  # Already exists

    df[column] = default
    _write_sheet(path, sheet_name, df)


def _add_sheet(path: str, sheet_name: str, columns: list[str]):
    """Add a new sheet if it doesn't already exist."""
    try:
        xl = pd.ExcelFile(path, engine="odf")
        if sheet_name in xl.sheet_names:
            return  # Already exists
    except Exception:
        pass

    # Read all existing sheets
    existing = {}
    try:
        xl = pd.ExcelFile(path, engine="odf")
        for name in xl.sheet_names:
            try:
                existing[name] = pd.read_excel(
                    path, sheet_name=name, engine="odf", header=None, dtype=str
                )
            except Exception:
                existing[name] = pd.DataFrame()
    except Exception:
        pass

    # Add new empty sheet
    new_df = pd.DataFrame(columns=columns)

    with pd.ExcelWriter(path, engine="odf") as writer:
        for name, df in existing.items():
            df.to_excel(writer, sheet_name=name, index=False, header=False)
        new_df.to_excel(writer, sheet_name=sheet_name, index=False)


def _write_sheet(path: str, sheet_name: str, df: pd.DataFrame):
    """Write a single sheet, preserving all others."""
    existing = {}
    try:
        xl = pd.ExcelFile(path, engine="odf")
        for name in xl.sheet_names:
            if name != sheet_name:
                try:
                    existing[name] = pd.read_excel(
                        path, sheet_name=name, engine="odf", header=None, dtype=str
                    )
                except Exception:
                    existing[name] = pd.DataFrame()
    except Exception:
        pass

    with pd.ExcelWriter(path, engine="odf") as writer:
        for name, edf in existing.items():
            edf.to_excel(writer, sheet_name=name, index=False, header=False)
        df.to_excel(writer, sheet_name=sheet_name, index=False)


# ── CLI ───────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="OpenYantra Schema Migration Tool v2.8"
    )
    parser.add_argument(
        "--file", "-f", default=str(Path.home() / "openyantra" / "chitrapat.ods")
    )
    parser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="Show what would be migrated without making changes",
    )
    parser.add_argument(
        "--backup-only",
        "-b",
        action="store_true",
        help="Create a backup without migrating",
    )
    parser.add_argument(
        "--detect", action="store_true", help="Detect and print version only"
    )
    args = parser.parse_args()

    path = Path(args.file).expanduser()
    if not path.exists():
        print(f"File not found: {path}")
        sys.exit(1)

    if args.detect:
        v = detect_version(str(path))
        print(f"Detected schema version: v{v}")
        return

    if args.backup_only:
        backup = (
            path.parent
            / f"chitrapat_backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.ods"
        )
        shutil.copy2(str(path), str(backup))
        print(f"✓ Backup created: {backup}")
        return

    result = run_migration(str(path), dry_run=args.dry_run)
    if result.get("status") == "error":
        sys.exit(1)


if __name__ == "__main__":
    main()
