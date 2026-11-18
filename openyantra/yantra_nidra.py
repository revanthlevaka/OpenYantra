"""
yantra_nidra.py -- OpenYantra Autonomous Sleep & Memory Consolidation Engine (Nidra) v6.0
Periodically clusters episodic session logs, resolves expired/stale open loops,
synthesizes long-term semantic narratives, and promotes repeated user preferences
into foundational beliefs.
"""

from __future__ import annotations

import json
import logging
import os
import re
import shutil
import signal
import subprocess
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
import logging as _oy_logging
_oy_log = _oy_logging.getLogger("openyantra")

logger = logging.getLogger("openyantra.nidra")


class NidraConsolidator:
    """
    Cognitive Consolidation Engine that mimics biological slow-wave sleep (Nidra).
    Runs offline or on schedule to distill noisy episodic memory into enduring semantic knowledge.
    """

    def __init__(self, oy: Any, ollama_url: str = "http://localhost:11434"):
        self.oy = oy
        self.ollama_url = ollama_url.rstrip("/")

    def is_apple_fm_available(self, timeout_sec: float = 1.0) -> Tuple[bool, Optional[str]]:
        """
        Check if Apple Foundation Model (AFM) via /usr/bin/fm is available and licensed on macOS.
        Returns:
            (True, "system") if available and licensed,
            (False, "license_required") if installed but legal terms not agreed,
            (False, None) if not on macOS or fm CLI not found.
        """
        if sys.platform != "darwin":
            return False, None

        fm_path = shutil.which("fm") or "/usr/bin/fm"
        if not os.path.exists(fm_path) or not os.access(fm_path, os.X_OK):
            return False, None

        try:
            res = subprocess.run(
                [fm_path, "license", "--status"],
                capture_output=True,
                text=True,
                timeout=timeout_sec
            )
            out = (res.stdout + res.stderr).lower()
            if "not agreed" in out or res.returncode == 69:
                return False, "license_required"
            if res.returncode == 0 or "agreed" in out:
                return True, "system"
        except Exception:
            _oy_log.debug("ignored fm license check error", exc_info=True)
            return False, None

        return False, None

    def query_apple_fm(self, prompt: str, timeout_sec: float = 15.0) -> Optional[str]:
        """Query Apple Foundation Model via /usr/bin/fm respond."""
        fm_path = shutil.which("fm") or "/usr/bin/fm"
        try:
            res = subprocess.run(
                [fm_path, "respond", "--no-stream", prompt],
                capture_output=True,
                text=True,
                timeout=timeout_sec
            )
            if res.returncode == 0 and res.stdout.strip():
                return res.stdout.strip()
            logger.debug(f"Apple FM query exited with code {res.returncode}: {res.stderr}")
        except Exception as e:
            logger.debug(f"Apple FM query failed: {e}")
        return None

    def resolve_provider(self, requested_provider: str = "auto") -> Tuple[str, Optional[str], Optional[str]]:
        """
        Resolve the effective inference provider and model name.
        Returns: (provider_name, model_name, notice_str)

        Resolution hierarchy:
        1. requested_provider (if != 'auto')
        2. OPENYANTRA_NIDRA_PROVIDER env var (if set and != 'auto')
        3. 'auto' cascade:
           - On macOS: check Apple Foundation Model. If licensed -> ('apple-fm', 'system', None).
             If unlicensed -> log/return notice to run 'sudo fm license' and check Ollama.
           - Check Ollama (:11434). If active -> ('ollama', model_name, notice).
           - Fallback -> ('heuristic', None, notice).
        """
        notice = None
        effective = requested_provider.lower().strip() if requested_provider else "auto"

        # Check environment variable override when auto is requested
        if effective == "auto":
            env_override = os.environ.get("OPENYANTRA_NIDRA_PROVIDER", "").lower().strip()
            if env_override in ("apple-fm", "afm", "apple"):
                effective = "apple-fm"
            elif env_override in ("ollama", "heuristic"):
                effective = env_override

        if effective in ("apple-fm", "afm", "apple"):
            afm_avail, status = self.is_apple_fm_available()
            if afm_avail:
                return "apple-fm", "system", None
            if status == "license_required":
                notice = "Apple Foundation Model found at /usr/bin/fm, but legal terms not agreed. Run 'sudo fm license' to enable."
            else:
                notice = "Apple Foundation Model (/usr/bin/fm) is not available on this system."
            logger.warning(f"[Nidra] {notice} Falling back to heuristic.")
            return "heuristic", None, notice

        if effective == "ollama":
            ollama_avail, model = self.is_ollama_available()
            if ollama_avail and model:
                return "ollama", model, None
            notice = f"Ollama not reachable at {self.ollama_url}. Falling back to heuristic."
            logger.warning(f"[Nidra] {notice}")
            return "heuristic", None, notice

        if effective == "heuristic":
            return "heuristic", None, None

        # Effective is "auto": Cascade
        # 1. On macOS: prefer Apple Foundation Model
        if sys.platform == "darwin":
            afm_avail, status = self.is_apple_fm_available()
            if afm_avail:
                return "apple-fm", "system", None
            if status == "license_required":
                notice = "Apple Foundation Model found at /usr/bin/fm. Run 'sudo fm license' to enable native zero-RAM on-device inference without Ollama."
                logger.info(f"[Nidra] {notice}")

        # 2. Check Ollama
        ollama_avail, model = self.is_ollama_available()
        if ollama_avail and model:
            return "ollama", model, notice

        # 3. Fallback to heuristic
        return "heuristic", None, notice

    def is_ollama_available(self, timeout_sec: float = 1.0) -> Tuple[bool, Optional[str]]:
        """Check if local Ollama daemon is active and return the first available model name."""
        try:
            req = urllib.request.Request(
                f"{self.ollama_url}/api/tags",
                headers={"User-Agent": "OpenYantra-Nidra/6.0"}
            )
            with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    models = data.get("models", [])
                    if models:
                        return True, models[0].get("name", "llama3")
                    return True, "llama3"
        except Exception:
            _oy_log.debug("ignored error", exc_info=True)
        return False, None

    def query_ollama(self, prompt: str, model: str, timeout_sec: float = 10.0) -> Optional[str]:
        """Query local Ollama instance for text generation."""
        try:
            payload = json.dumps({
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.3, "num_predict": 256}
            }).encode("utf-8")
            req = urllib.request.Request(
                f"{self.ollama_url}/api/generate",
                data=payload,
                headers={"Content-Type": "application/json", "User-Agent": "OpenYantra-Nidra/6.0"}
            )
            with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
                if resp.status == 200:
                    res_json = json.loads(resp.read().decode("utf-8"))
                    return res_json.get("response", "").strip()
        except Exception as e:
            logger.debug(f"Ollama query failed: {e}")
        return None

    def cluster_sessions(self, limit: int = 25) -> Dict[str, Any]:
        """Clusters recent session logs into primary topics, key decisions, and touched projects."""
        sessions = self.oy.get_sheet("Session Log")
        if not sessions:
            return {"count": 0, "topics": [], "decisions": [], "projects": []}

        recent = sessions[-limit:]
        all_topics: List[str] = []
        all_decisions: List[str] = []
        all_projects: set = set()

        for s in recent:
            topic = str(s.get("Topics Discussed") or s.get("Topic") or s.get("Task") or "").strip()
            if topic and topic.lower() != "nan":
                all_topics.append(topic)
            
            dec = str(s.get("Decisions Made") or s.get("Decisions") or s.get("Decisions / Outputs") or "").strip()
            if dec and dec.lower() != "nan":
                all_decisions.append(dec)

            proj = str(s.get("Related Project") or s.get("Project") or "").strip()
            if proj and proj.lower() not in ("nan", "", "none"):
                all_projects.add(proj)

        return {
            "count": len(recent),
            "topics": all_topics,
            "decisions": all_decisions,
            "projects": sorted(list(all_projects)),
        }

    def detect_promotable_preferences(self) -> List[Dict[str, str]]:
        """
        Scans recent session logs and inbox notes for recurring user preferences or principles
        that should be promoted into the Beliefs sheet.
        """
        from openyantra.core import SHEET_BELIEFS
        existing_beliefs = self.oy.get_sheet(SHEET_BELIEFS)
        known_statements = set()
        for b in existing_beliefs:
            pos = str(b.get("Position") or b.get("Belief / Principle") or "").strip().lower()
            if pos:
                known_statements.add(pos)
                if pos.startswith("user preference:"):
                    known_statements.add(pos[len("user preference:"):].strip())
            top = str(b.get("Topic") or "").strip().lower()
            if top:
                known_statements.add(top)

        sessions = self.oy.get_sheet("Session Log")
        inbox_items = self.oy.get_sheet("Inbox")

        candidates: List[Dict[str, str]] = []
        preference_regex = re.compile(
            r"(?:user\s+(?:prefers?|always|never|likes|wants)|preference:\s*|rule:\s*|always\s+(?:use|prefer)\s+|never\s+(?:use|prefer)\s+)([^.\n;]+)",
            re.IGNORECASE
        )

        # Collect reverted / superseded decisions across all recent sessions to exclude undone choices
        reverted_phrases = set()
        for s in sessions[-50:]:
            dec_text = str(s.get("Decisions Made") or s.get("Decisions") or s.get("Decisions / Outputs") or "")
            notes = str(s.get("Notes") or "")
            if "reverted" in dec_text.lower() or "superseded" in dec_text.lower() or "reverted" in notes.lower():
                for part in dec_text.split(";"):
                    if "reverted" in part.lower():
                        p_clean = re.sub(r'reverted\s*(?:/\s*superseded)?\s*decision\s*(?:\[[^\]]+\])?\s*:?', '', part, flags=re.IGNORECASE).strip().lower()
                        p_clean = re.sub(r'^revert\s*\"?', '', p_clean).strip().rstrip('\"').strip()
                        if p_clean and len(p_clean) >= 4:
                            reverted_phrases.add(p_clean)

        texts_to_scan = []
        for s in sessions[-30:]:
            dec_text = str(s.get("Decisions Made") or s.get("Decisions") or s.get("Decisions / Outputs") or "")
            notes = str(s.get("Notes") or "")
            # Skip session if marked reverted
            if "reverted" in dec_text.lower() or "superseded" in dec_text.lower() or "reverted" in notes.lower():
                continue
            dec_lower = dec_text.lower().strip()
            if dec_lower and any(rev and (rev in dec_lower or (len(dec_lower) >= 3 and dec_lower in rev)) for rev in reverted_phrases):
                continue
            texts_to_scan.append(dec_text)
            texts_to_scan.append(str(s.get("Topics Discussed") or s.get("Topic") or ""))
            texts_to_scan.append(str(s.get("Notes") or s.get("Next Actions") or ""))
        for i in inbox_items[-20:]:
            texts_to_scan.append(str(i.get("Item") or i.get("Raw Input") or i.get("Content") or ""))

        for text in texts_to_scan:
            if not text or text.lower() == "nan":
                continue
            matches = preference_regex.findall(text)
            for m in matches:
                clean_pref = m.strip()
                clean_lower = clean_pref.lower()
                # Skip if preference was part of an undone / reverted decision
                if clean_lower and any(rev and (rev in clean_lower or (len(clean_lower) >= 3 and clean_lower in rev)) for rev in reverted_phrases):
                    continue

                if (len(clean_pref) > 8 and
                    clean_lower not in known_statements and
                    f"user preference: {clean_lower}" not in known_statements):

                    topic_title = f"Pref: {clean_pref.strip()[:35]}"
                    candidate = {
                        "Topic": topic_title,
                        "Belief / Principle": f"User Preference: {clean_pref.strip()}",
                        "Position": f"User Preference: {clean_pref.strip()}",
                        "Domain": "Operational",
                        "Confidence": "High",
                        "Source": "Nidra Session Consolidation"
                    }
                    if candidate not in candidates:
                        candidates.append(candidate)
                        known_statements.add(clean_lower)
                        known_statements.add(f"user preference: {clean_lower}")

        return candidates

    def prune_and_resolve_loops(self, dry_run: bool = False) -> List[Dict[str, str]]:
        """
        Identifies open loops that have been addressed in session logs or marked complete,
        and marks them resolved.
        """
        open_loops = self.oy.get_sheet("Open Loops")
        sessions = self.oy.get_sheet("Session Log")
        resolved_actions: List[Dict[str, str]] = []

        if not open_loops:
            return resolved_actions

        # Build a corpus of decisions from recent sessions
        decisions_corpus = " ".join([
            str(s.get("Decisions Made") or s.get("Decisions") or s.get("Decisions / Outputs") or "") + " " +
            str(s.get("Topics Discussed") or s.get("Topic") or "")
            for s in sessions[-30:]
        ]).lower()

        for loop in open_loops:
            topic = str(loop.get("Topic", "")).strip()
            status = str(loop.get("Resolved?", "")).strip().lower()
            if status in ("yes", "resolved", "closed", "true") or not topic:
                continue

            # Check if topic or keyword clearly matches decisions corpus
            clean_topic = re.sub(r"[^\w\s]", "", topic.lower()).strip()
            topic_words = [w for w in clean_topic.split() if len(w) > 3]

            should_resolve = False
            match_reason = ""

            if topic.lower() in decisions_corpus:
                should_resolve = True
                match_reason = "Exact topic found in session decisions log"
            elif len(topic_words) >= 2 and all(w in decisions_corpus for w in topic_words[:3]):
                should_resolve = True
                match_reason = f"Keywords {topic_words[:3]} found in session decisions"

            if should_resolve:
                resolved_info = {
                    "topic": topic,
                    "reason": match_reason,
                    "resolution": f"Auto-resolved during Nidra consolidation: {match_reason}"
                }
                resolved_actions.append(resolved_info)
                if not dry_run:
                    try:
                        self.oy.resolve_open_loop(topic, resolution=resolved_info["resolution"])
                    except Exception as e:
                        logger.warning(f"Could not resolve open loop '{topic}': {e}")

        return resolved_actions

    def consolidate(self, dry_run: bool = False, provider: str = "auto") -> Dict[str, Any]:
        """
        Executes full sleep consolidation pass.
        Returns detailed consolidation telemetry.
        """
        # 1. Cluster sessions
        cluster_info = self.cluster_sessions(limit=25)

        # 2. Open Loops Pruning
        resolved_loops = self.prune_and_resolve_loops(dry_run=dry_run)

        # 3. Preference Promotion
        promoted = self.detect_promotable_preferences()
        promoted_applied = []
        if not dry_run and promoted:
            for p in promoted:
                from openyantra.core import WriteRequest, SHEET_BELIEFS
                belief_text = p.get("Position") or p.get("Belief / Principle") or ""
                topic = p.get("Topic") or f"Pref: {belief_text[:35]}"
                req = WriteRequest(
                    requesting_agent="NidraConsolidator",
                    sheet=SHEET_BELIEFS,
                    operation="add",
                    fields={
                        "Topic": topic,
                        "Position": belief_text,
                        "Confidence": p.get("Confidence", "High"),
                        "Domain": p.get("Domain", "Operational"),
                        "Last Updated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                        "Notes": "Auto-promoted during cognitive sleep consolidation",
                        "Source": "Agent-inferred",
                        "Importance": 8,
                        "Contradiction_Flag": "No"
                    },
                    row_identifier=topic,
                    confidence="High",
                    source="Agent-inferred",
                    importance=8
                )
                res = self.oy.request_write(req)
                if res.get("status") in ("written", "committed", "queued"):
                    promoted_applied.append(p)

        # 3.1. Revert check for existing beliefs -- supersede previously promoted beliefs if origin was reverted
        if not dry_run:
            from openyantra.core import WriteRequest, SHEET_BELIEFS, SHEET_SESSION_LOG
            sessions = self.oy._read_sheet(SHEET_SESSION_LOG)
            reverted_phrases = set()
            for s in sessions[-50:]:
                dec_text = str(s.get("Decisions Made") or s.get("Decisions") or "")
                for part in dec_text.split(";"):
                    if "reverted" in part.lower():
                        p_clean = re.sub(r'reverted\s*(?:/\s*superseded)?\s*decision\s*(?:\[[^\]]+\])?\s*:?', '', part, flags=re.IGNORECASE).strip().lower()
                        p_clean = re.sub(r'^revert\s*\"?', '', p_clean).strip().rstrip('\"').strip()
                        if p_clean and len(p_clean) >= 4:
                            reverted_phrases.add(p_clean)
            if reverted_phrases:
                existing_beliefs = self.oy._read_sheet(SHEET_BELIEFS)
                for b in existing_beliefs:
                    pos = str(b.get("Position") or b.get("Belief / Principle") or "").lower()
                    clean_pos = pos.replace("user preference:", "").strip()
                    topic = b.get("Topic")
                    if not b.get("Superseded_By") and clean_pos:
                        is_undone = False
                        for rev in reverted_phrases:
                            clean_rev = re.sub(r'^(?:always|never)\s+(?:use|prefer)\s+', '', rev).strip()
                            if (clean_rev and clean_rev in pos) or (clean_pos and len(clean_pos) >= 4 and clean_pos in rev):
                                is_undone = True
                                break
                        if is_undone:
                            req = WriteRequest(
                                requesting_agent="NidraConsolidator",
                                sheet=SHEET_BELIEFS,
                                operation="supersede",
                                row_identifier=topic,
                                fields={"Superseded_By": "Reverted in session log"},
                                confidence="High",
                                source="System"
                            )
                            self.oy.request_write(req)

        # 4. Synthesize Narrative
        provider_used = "heuristic"
        chosen_provider, model_name, license_notice = self.resolve_provider(provider)

        summary_text = ""
        prompt = (
            "You are the subconscious memory consolidation daemon (Nidra) for an AI knowledge system.\n"
            f"Recent topics touched: {', '.join(cluster_info['topics'][-10:])}\n"
            f"Recent decisions made: {'; '.join(cluster_info['decisions'][-8:])}\n"
            f"Active projects: {', '.join(cluster_info['projects'])}\n"
            "Synthesize a concise 2-sentence episodic memory summary capturing key progress, changes, and focus areas."
        )

        if chosen_provider == "apple-fm":
            llm_summary = self.query_apple_fm(prompt)
            if llm_summary:
                summary_text = llm_summary
                provider_used = "apple-fm (system)"

        elif chosen_provider == "ollama" and model_name:
            llm_summary = self.query_ollama(prompt, model=model_name)
            if llm_summary:
                summary_text = llm_summary
                provider_used = f"ollama ({model_name})"

        if not summary_text:
            # Heuristic synthesis fallback
            topics_snippet = ", ".join(cluster_info["topics"][-5:]) if cluster_info["topics"] else "Routine operations"
            proj_snippet = ", ".join(cluster_info["projects"]) if cluster_info["projects"] else "General"
            dec_snippet = f"Captured {len(cluster_info['decisions'])} decisions" if cluster_info["decisions"] else "No major architectural decisions"
            summary_text = (
                f"Consolidated {cluster_info['count']} recent sessions across projects [{proj_snippet}]. "
                f"Core focus areas: {topics_snippet}. {dec_snippet}."
            )
            provider_used = "heuristic"

        # 5. Commit consolidated session note if not dry_run
        if not dry_run and cluster_info["count"] > 0:
            decisions_list = [summary_text]
            if resolved_loops:
                decisions_list.append(f"Auto-resolved {len(resolved_loops)} loops: {', '.join(r['topic'] for r in resolved_loops[:3])}")
            if promoted_applied:
                decisions_list.append(f"Promoted {len(promoted_applied)} preferences to Beliefs")

            try:
                self.oy.log_session(
                    topics=["Nidra Memory Consolidation"],
                    decisions=decisions_list,
                    notes="Resume daylight operations with distilled memory"
                )
            except Exception as e:
                logger.warning(f"Failed to log Nidra consolidation session: {e}")

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "dry_run": dry_run,
            "provider_used": provider_used,
            "license_notice": license_notice,
            "sessions_clustered": cluster_info["count"],
            "projects_active": cluster_info["projects"],
            "summary": summary_text,
            "loops_resolved": resolved_loops,
            "promoted_preferences": promoted_applied if not dry_run else promoted,
        }


class NidraDaemon:
    """
    NidraDaemon -- Autonomous Soul-Engine Background Worker.
    Detached background watcher that periodically inspects Chitrapat state.
    When a quiet period (inactivity >= idle_threshold) follows recorded activity,
    it executes offline sleep consolidation, loop pruning, semantic indexing, and WAL checkpointing.
    """

    def __init__(
        self,
        oy: Any,
        interval_seconds: int = 60,
        idle_threshold_seconds: int = 300,
        provider: str = "auto",
        dry_run: bool = False,
        logger_func: Optional[Callable[[str], None]] = None,
    ):
        self.oy = oy
        self.interval = interval_seconds
        self.idle_threshold = idle_threshold_seconds
        self.provider = provider
        self.dry_run = dry_run
        self.log = logger_func or print
        self._running = False
        self._last_consolidated_time = time.time()
        self._consolidator = NidraConsolidator(oy)

    def get_latest_mtime(self) -> float:
        """Return the newest mtime among ODS workbook and SQLite DB."""
        mtimes = [0.0]
        if hasattr(self.oy, "path") and self.oy.path:
            p = Path(self.oy.path)
            if p.exists():
                mtimes.append(p.stat().st_mtime)
                db_path = p.with_suffix(".db")
                if db_path.exists():
                    mtimes.append(db_path.stat().st_mtime)
        return max(mtimes)

    def check_and_consolidate(self) -> Optional[dict]:
        """
        Check if quiet idle condition is satisfied and run consolidation.
        Returns consolidation report dict if executed, None otherwise.
        """
        now = time.time()
        latest_mtime = self.get_latest_mtime()

        # If there were writes since our last consolidation, check if they are settled
        if latest_mtime > self._last_consolidated_time:
            idle_duration = now - latest_mtime
            if idle_duration >= self.idle_threshold:
                self.log(
                    f"[Soul-Engine] Inactivity detected ({idle_duration:.1f}s >= {self.idle_threshold}s). "
                    "Beginning autonomous Nidra consolidation..."
                )
                report = self._consolidator.consolidate(
                    provider=self.provider, dry_run=self.dry_run
                )

                # Sync VidyaKosha semantic index if enabled
                if hasattr(self.oy, "_vidyakosha") and self.oy._vidyakosha:
                    try:
                        self.oy._vidyakosha.sync(self.oy.path)
                    except Exception:
                        _oy_log.debug("ignored error syncing vidyakosha", exc_info=True)

                # Reconcile WAL if DB engine enabled
                if hasattr(self.oy, "db_engine") and self.oy.db_engine:
                    try:
                        self.oy.db_engine.reconcile()
                    except Exception:
                        _oy_log.debug("ignored error reconciling db", exc_info=True)

                # Set last consolidated time to include any writes from consolidation itself
                self._last_consolidated_time = max(time.time(), self.get_latest_mtime())

                self.log(
                    f"[Soul-Engine] Consolidation finished: "
                    f"{report.get('sessions_clustered', 0)} sessions, "
                    f"{len(report.get('loops_resolved', []))} loops resolved, "
                    f"{len(report.get('promoted_preferences', []))} preferences promoted."
                )
                return report

        return None

    def run_loop(self, max_cycles: Optional[int] = None):
        """Run the monitoring daemon loop until interrupted or max_cycles reached."""
        self._running = True

        def _handle_exit(signum, frame):
            self.log("\n[Soul-Engine] Received shutdown signal. Stopping daemon gracefully...")
            self._running = False

        try:
            signal.signal(signal.SIGINT, _handle_exit)
            signal.signal(signal.SIGTERM, _handle_exit)
        except (ValueError, AttributeError):
            pass

        cycles = 0
        while self._running:
            try:
                self.check_and_consolidate()
            except Exception as e:
                self.log(f"[Soul-Engine] Error during consolidation cycle: {e}")

            cycles += 1
            if max_cycles is not None and cycles >= max_cycles:
                break

            for _ in range(max(1, int(self.interval))):
                if not self._running:
                    break
                time.sleep(1)

        self._running = False
