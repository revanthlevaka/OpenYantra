"""
yantra_sutra.py -- Sutra Context Pruning Engine (v5.0.0)
Calculates memory weights and greedy-packs context items to fit token budgets.
"""

from __future__ import annotations

import math
from datetime import datetime
from pathlib import Path
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from openyantra.core import OpenYantra

EMOJI_TO_SECTION = {
    "👤 Identity": "identity",
    "🎯 Goals": "goals",
    "🚀 Projects": "projects",
    "👥 People": "people",
    "💡 Preferences": "preferences",
    "🧠 Beliefs": "beliefs",
    "✅ Tasks": "tasks",
    "🔓 Open Loops": "loops"
}
SECTION_TO_EMOJI = {v: k for k, v in EMOJI_TO_SECTION.items()}


def estimate_tokens(text: str) -> int:
    """Estimate token count for a text string, using tiktoken if available."""
    try:
        import tiktoken
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except ImportError:
        # Heuristic: 4 characters per token
        return max(1, len(text) // 4)


def parse_date(val) -> Optional[datetime]:
    """Parse date from value, trying various common formats."""
    if not val:
        return None
    val_str = str(val).strip()
    for fmt in (
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%m/%d/%Y"
    ):
        try:
            return datetime.strptime(val_str, fmt)
        except ValueError:
            continue
    return None


class SutraCompiler:
    def __init__(self, oy: OpenYantra, settings: Optional[dict] = None):
        self.oy = oy
        self.settings = settings or {}

        # Default preset weights
        self.preset_weights = {
            "conversational": {"semantic": 0.3, "recency": 0.5, "importance": 0.1, "relation": 0.1},
            "analytical":     {"semantic": 0.5, "recency": 0.1, "importance": 0.3, "relation": 0.1},
            "creative":       {"semantic": 0.3, "recency": 0.2, "importance": 0.2, "relation": 0.3},
            "default":        {"semantic": 0.4, "recency": 0.3, "importance": 0.2, "relation": 0.1}
        }

    def compile(self,
                query_text: Optional[str] = None,
                budget: int = 4096,
                mode: str = "default",
                sections: Optional[list[str]] = None) -> dict:
        """
        Compile context to fit within the token budget using weighted scoring.
        Returns:
            dict containing:
                "markdown": The compiled markdown string.
                "tokens": Total token count of the compiled markdown.
                "packed": List of items that were included.
                "discarded": List of items that were pruned.
        """
        if sections is None:
            sections = ["identity", "goals", "projects", "people", "preferences", "beliefs", "tasks", "loops", "instructions"]

        # 1. Determine weights
        weights = self.preset_weights.get(mode, self.preset_weights["default"]).copy()
        if "sutra_weights" in self.settings:
            weights.update(self.settings["sutra_weights"])

        # 2. Extract static/non-pruned elements (Identity & Instructions)
        ctx = self.oy.load_session_context()
        identity_lines = []
        if "identity" in sections and ctx.get("identity"):
            id_map = ctx["identity"]
            name = (id_map.get("Preferred Name") or id_map.get("Full Name") or "")
            occ = id_map.get("Occupation", "")
            loc = id_map.get("Location", "")
            lang = id_map.get("Primary Language", "")
            hours = id_map.get("Working Hours", "")

            identity_lines.append("### Identity")
            if name: identity_lines.append(f"- **Name:** {name}")
            if occ:  identity_lines.append(f"- **Role:** {occ}")
            if loc:  identity_lines.append(f"- **Location:** {loc}")
            if lang and lang.lower() != "english":
                identity_lines.append(f"- **Language:** {lang}")
            if hours:
                identity_lines.append(f"- **Working Hours:** {hours}")
            identity_lines.append("")

        instruction_lines = []
        if "instructions" in sections and ctx.get("agent_instructions"):
            instruction_lines.append("### Instructions")
            for inst in ctx["agent_instructions"]:
                instruction_lines.append(f"- {inst}")
            instruction_lines.append("")

        header_lines = [
            f"<!-- OpenYantra Compiled Context | Mode: {mode} | Budget: {budget} tokens | {datetime.utcnow().isoformat()[:10]} -->",
            "",
            "## My AI Memory Context",
            "",
        ]

        static_markdown = "\n".join(header_lines + identity_lines + instruction_lines)
        static_tokens = estimate_tokens(static_markdown)

        # 3. Gather dynamic candidate entities
        candidates = []
        
        # Load sheets directly to get all raw entries
        sheet_configs = {
            "projects": ("🚀 Projects", self._format_project),
            "loops": ("🔓 Open Loops", self._format_loop),
            "goals": ("🎯 Goals", self._format_goal),
            "tasks": ("✅ Tasks", self._format_task),
            "preferences": ("💡 Preferences", self._format_preference),
            "beliefs": ("🧠 Beliefs", self._format_belief),
            "people": ("👥 People", self._format_person)
        }

        # Query VidyaKosha for semantic similarities if a query is provided
        semantic_scores = {}
        if query_text and self.oy._vidyakosha:
            try:
                # Query with large top_k to score as many entities as possible
                hits = self.oy._vidyakosha.query(query_text, top_k=500)
                for hit in hits:
                    sheet = hit.get("sheet")
                    prim = hit.get("primary_value")
                    vec_score = hit.get("vector_score", 0.0)
                    semantic_scores[(sheet, prim)] = vec_score
            except Exception:
                pass

        # Load relation proximity mapping from the database if edges exist
        proximity_scores = {}
        if getattr(self.oy, "db_engine", None):
            try:
                # Check if edges table exists
                with self.oy.db_engine._connect() as conn:
                    table_exists = conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name='edges'"
                    ).fetchone()
                    
                    if table_exists:
                        # Find source entities that are semantically relevant
                        start_nodes = []
                        if query_text and self.oy._vidyakosha:
                            # Start BFS from top 5 semantic hits
                            for hit in hits[:5]:
                                s_type = EMOJI_TO_SECTION.get(hit.get("sheet"), "other")
                                s_id = hit.get("primary_value")
                                if s_id:
                                    start_nodes.append((s_type, s_id))
                        
                        # Add active projects as starts
                        for proj in ctx.get("active_projects", []):
                            p_name = proj.get("Project")
                            if p_name:
                                start_nodes.append(("projects", p_name))

                        if start_nodes:
                            # Run multi-source BFS up to 2 hops
                            visited = {}
                            queue = []
                            for s_type, s_id in start_nodes:
                                queue.append((s_type, s_id, 0))
                                visited[(s_type, s_id)] = 0
                            
                            while queue:
                                curr_type, curr_id, dist = queue.pop(0)
                                if dist >= 2:
                                    continue
                                
                                # Query direct edges from current node
                                rows = conn.execute(
                                    "SELECT target_type, target_id FROM edges WHERE source_type=? AND source_id=?",
                                    (curr_type, curr_id)
                                ).fetchall()
                                for t_type, t_id in rows:
                                    if (t_type, t_id) not in visited:
                                        visited[(t_type, t_id)] = dist + 1
                                        queue.append((t_type, t_id, dist + 1))
                                        
                                # Also query incoming edges (undirected logic)
                                rows_in = conn.execute(
                                    "SELECT source_type, source_id FROM edges WHERE target_type=? AND target_id=?",
                                    (curr_type, curr_id)
                                ).fetchall()
                                for s_type, s_id in rows_in:
                                    if (s_type, s_id) not in visited:
                                        visited[(s_type, s_id)] = dist + 1
                                        queue.append((s_type, s_id, dist + 1))

                            for (node_type, node_id), dist in visited.items():
                                proximity_scores[(node_type, node_id)] = 1.0 / (1.0 + dist)
            except Exception:
                pass

        now = datetime.utcnow()

        for sec_name in sections:
            if sec_name not in sheet_configs:
                continue
            sheet_emoji, formatter = sheet_configs[sec_name]
            rows = self.oy._read_sheet(sheet_emoji)

            # Filter rows based on status
            if sec_name == "projects":
                rows = [r for r in rows if r.get("Status") == "Active"]
            elif sec_name == "loops":
                rows = [r for r in rows if r.get("Resolved?") == "No"]
            elif sec_name == "goals":
                rows = [r for r in rows if r.get("Status") in ("Active", "In Progress")]
            elif sec_name == "tasks":
                rows = [r for r in rows if r.get("Status") not in ("Done", None)]

            for row in rows:
                if not any(v for v in row.values() if v and str(v).strip()):
                    continue

                text = formatter(row)
                tokens = estimate_tokens(text)
                primary_val = str(list(row.values())[0]) if row else ""

                # --- 1. Semantic Sim ---
                semantic_sim = semantic_scores.get((sheet_emoji, primary_val), 0.0)

                # --- 2. Recency Decay ---
                date_val = None
                for date_key in ("Opened", "Updated", "Last Updated", "Date", "Timestamp", "Samay"):
                    if row.get(date_key):
                        date_val = parse_date(row[date_key])
                        if date_val:
                            break
                if date_val:
                    days_old = max(0.0, (now - date_val).days)
                    recency_decay = math.exp(-days_old / 30.0)
                else:
                    recency_decay = 1.0  # Default to no decay

                # --- 3. Importance Weight ---
                importance_val = 0.5
                if row.get("Importance"):
                    try:
                        importance_val = float(row["Importance"]) / 10.0
                    except ValueError:
                        pass
                elif row.get("Priority"):
                    p = str(row["Priority"]).lower()
                    if "high" in p: importance_val = 0.8
                    elif "low" in p: importance_val = 0.2
                    else: importance_val = 0.5
                elif row.get("Strength"):
                    s = str(row["Strength"]).lower()
                    if "strong" in s: importance_val = 0.8
                    elif "weak" in s: importance_val = 0.2
                    else: importance_val = 0.5
                else:
                    # Sheet specific defaults
                    if sec_name in ("projects", "goals"):
                        importance_val = 0.7

                # --- 4. Relation Proximity ---
                relation_prox = proximity_scores.get((sec_name, primary_val), 0.0)

                # Compute unified score
                total_score = (
                    weights["semantic"] * semantic_sim +
                    weights["recency"] * recency_decay +
                    weights["importance"] * importance_val +
                    weights["relation"] * relation_prox
                )

                candidates.append({
                    "sheet": sec_name,
                    "sheet_emoji": sheet_emoji,
                    "primary_value": primary_val,
                    "row": row,
                    "text": text,
                    "tokens": tokens,
                    "scores": {
                        "semantic": round(semantic_sim, 3),
                        "recency": round(recency_decay, 3),
                        "importance": round(importance_val, 3),
                        "relation": round(relation_prox, 3),
                        "total": round(total_score, 3)
                    }
                })

        # 4. Greedy packing
        # Sort candidates descending by total score
        candidates.sort(key=lambda x: -x["scores"]["total"])

        remaining_budget = budget - static_tokens
        packed = []
        discarded = []

        for c in candidates:
            if remaining_budget >= c["tokens"]:
                packed.append(c)
                remaining_budget -= c["tokens"]
            else:
                discarded.append(c)

        # 5. Re-group packed items by sheet to generate clean markdown
        grouped: dict[str, list[dict]] = {}
        for c in packed:
            grouped.setdefault(c["sheet"], []).append(c)

        lines = [static_markdown]
        
        # Order sheets logically
        sheet_order = ["projects", "loops", "goals", "tasks", "preferences", "beliefs", "people"]
        for sec in sheet_order:
            if sec in grouped:
                emoji = SECTION_TO_EMOJI[sec]
                # Map section name to appropriate markdown header
                header_map = {
                    "projects": "### Active Projects",
                    "loops": "### Open Loops (Unresolved)",
                    "goals": "### Goals",
                    "tasks": "### Pending Tasks",
                    "preferences": "### Preferences",
                    "beliefs": "### Key Beliefs & Principles",
                    "people": "### Key People"
                }
                lines.append(header_map[sec])
                for item in grouped[sec]:
                    lines.append(item["text"])
                lines.append("")

        final_markdown = "\n".join(lines).strip() + "\n"
        final_tokens = estimate_tokens(final_markdown)

        return {
            "markdown": final_markdown,
            "tokens": final_tokens,
            "packed": packed,
            "discarded": discarded
        }

    # Formatting helpers
    def _format_project(self, row: dict) -> str:
        proj = row.get("Project", "?")
        ns = row.get("Next Step", "")
        dom = row.get("Domain", "")
        pri = row.get("Priority", "")
        line = f"- **{proj}**"
        if pri: line += f" [{pri}]"
        if dom: line += f" ({dom})"
        if ns:  line += f" -- next: {ns}"
        return line

    def _format_loop(self, row: dict) -> str:
        topic = row.get("Topic", "?")
        context = row.get("Context / What's Unresolved", "")
        pri = row.get("Priority", "?")
        line = f"- [{pri}] **{topic}**"
        if context: line += f": {context[:120]}"
        return line

    def _format_goal(self, row: dict) -> str:
        goal = row.get("Goal", "?")
        gtype = row.get("Type", "")
        return f"- {goal}" + (f" ({gtype})" if gtype else "")

    def _format_task(self, row: dict) -> str:
        task = row.get("Task", "?")
        proj = row.get("Project", "")
        pri = row.get("Priority", "Medium")
        line = f"- [{pri}] {task}"
        if proj: line += f" ({proj})"
        return line

    def _format_preference(self, row: dict) -> str:
        cat = row.get("Category", "?")
        pref = row.get("Preference", "?")
        return f"- **{cat}:** {pref}"

    def _format_belief(self, row: dict) -> str:
        topic = row.get("Topic", "?")
        position = row.get("Position", "?")
        return f"- **{topic}:** {position}"

    def _format_person(self, row: dict) -> str:
        name = row.get("Name", "?")
        rel = row.get("Relationship", "")
        ctx_text = row.get("Context", "")
        line = f"- **{name}**"
        if rel: line += f" ({rel})"
        if ctx_text: line += f": {ctx_text[:100]}"
        return line
