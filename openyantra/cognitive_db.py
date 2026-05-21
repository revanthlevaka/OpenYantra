"""
cognitive_db.py -- Cognitive Memory Engine Database Controller
Manages the flat-file JSON database storing memories and agent hierarchy relationships.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any, Union

class CognitiveMemoryStore:
    def __init__(self, file_path: Optional[Union[str, Path]] = None):
        if file_path is None:
            self.file_path = Path.home() / "openyantra" / "cognitive_memories.json"
        else:
            self.file_path = Path(file_path).expanduser()
            
        # Ensure parent directory exists
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            self._save([])

    def _load(self) -> List[Dict[str, Any]]:
        try:
            if self.file_path.exists():
                content = self.file_path.read_text(encoding="utf-8").strip()
                if content:
                    return json.loads(content)
            return []
        except Exception as e:
            print(f"[CognitiveMemoryStore] Error loading database: {e}")
            return []

    def _save(self, memories: List[Dict[str, Any]]):
        try:
            self.file_path.write_text(json.dumps(memories, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            print(f"[CognitiveMemoryStore] Error saving database: {e}")

    def write(self, key: str, type_val: str, agent: str, content: str, tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Creates or updates a memory key (case-insensitive).
        """
        # Schema validation
        valid_types = {"decision", "fact", "context", "observation"}
        if type_val not in valid_types:
            raise ValueError(f"Invalid type: {type_val}. Must be one of {list(valid_types)}")

        if not key or not key.strip():
            raise ValueError("Key cannot be empty")
        if not agent or not agent.strip():
            raise ValueError("Agent cannot be empty")
        if not content:
            content = ""

        tags = tags or []
        # Ensure tags are a clean list of strings
        tags = [str(t).strip() for t in tags if str(t).strip()]

        memories = self._load()
        now_iso = datetime.utcnow().isoformat() + "Z"
        
        # Search case-insensitively for key
        key_lower = key.strip().lower()
        found_idx = -1
        for idx, m in enumerate(memories):
            if m.get("key", "").strip().lower() == key_lower:
                found_idx = idx
                break

        new_memory = {
            "key": key.strip(), # Keep original casing of first insert/latest update
            "type": type_val,
            "agent": agent.strip(),
            "content": content,
            "tags": tags,
            "timestamp": now_iso
        }

        if found_idx >= 0:
            memories[found_idx] = new_memory
        else:
            memories.append(new_memory)

        self._save(memories)
        return new_memory

    def read(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a memory by key (case-insensitive).
        """
        memories = self._load()
        key_lower = key.strip().lower()
        for m in memories:
            if m.get("key", "").strip().lower() == key_lower:
                return m
        return None

    def delete(self, key: str) -> bool:
        """
        Removes a memory key (case-insensitive). Returns True if deleted, False otherwise.
        """
        memories = self._load()
        key_lower = key.strip().lower()
        initial_len = len(memories)
        memories = [m for m in memories if m.get("key", "").strip().lower() != key_lower]
        
        if len(memories) < initial_len:
            self._save(memories)
            return True
        return False

    def search(self, query: Optional[str] = None, type_val: Optional[str] = None, tags: Optional[List[str]] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search memories with partial match on key/content, type match, tag intersection, and date range.
        """
        memories = self._load()
        filtered = []

        for m in memories:
            # Skip special internal keys in regular searches unless requested
            is_internal = m.get("key", "") == "agent-hierarchy-connections"
            if is_internal and not (query and "hierarchy" in query.lower()):
                continue

            # Query filter (matches key or content substring, case-insensitive)
            if query and query.strip():
                q = query.strip().lower()
                key_match = q in m.get("key", "").lower()
                content_match = q in m.get("content", "").lower()
                if not (key_match or content_match):
                    continue

            # Type filter
            if type_val and type_val.strip():
                if m.get("type", "").lower() != type_val.strip().lower():
                    continue

            # Date filters (lexicographical string prefix matching)
            ts = m.get("timestamp", "")
            if start_date and start_date.strip():
                if not ts or ts[:10] < start_date.strip():
                    continue
            if end_date and end_date.strip():
                if not ts or ts[:10] > end_date.strip():
                    continue

            # Tags filter (memory must match ALL requested tags)
            if tags:
                memory_tags = {t.lower() for t in m.get("tags", [])}
                req_tags = {t.lower() for t in tags if t.strip()}
                if not req_tags.issubset(memory_tags):
                    continue

            filtered.append(m)

        return filtered

    def stats(self) -> Dict[str, Any]:
        """
        Aggregates metrics for countByType and countByAgent.
        """
        memories = self._load()
        count_by_type = {}
        count_by_agent = {}
        total = 0

        for m in memories:
            # Exclude hierarchy connections from general metrics
            if m.get("key") == "agent-hierarchy-connections":
                continue
            
            t = m.get("type", "unknown")
            a = m.get("agent", "unknown")
            
            count_by_type[t] = count_by_type.get(t, 0) + 1
            count_by_agent[a] = count_by_agent.get(a, 0) + 1
            total += 1

        return {
            "totalMemories": total,
            "countByType": count_by_type,
            "countByAgent": count_by_agent
        }

    # ── Agent Hierarchy & BFS Solver ──────────────────────────────────────────────

    def get_connections(self) -> List[Dict[str, str]]:
        """
        Helper to parse the agent-hierarchy-connections list from database.
        """
        m = self.read("agent-hierarchy-connections")
        if not m or not m.get("content"):
            return []
        try:
            return json.loads(m["content"])
        except Exception:
            return []

    def save_connections(self, connections: List[Dict[str, str]]):
        """
        Helper to serialize and write connections list.
        """
        self.write(
            key="agent-hierarchy-connections",
            type_val="decision",
            agent="System",
            content=json.dumps(connections),
            tags=["hierarchy", "system-connections"]
        )

    def get_hierarchy(self) -> Dict[str, Any]:
        """
        Calculates levels for all active agents using BFS (Breadth-First Search).
        Returns a dict containing agent levels, connections, and list of all agents.
        """
        connections = self.get_connections()
        memories = self._load()

        # Build list of unique agents (exclude System)
        agents_set = set()
        for m in memories:
            a = m.get("agent")
            if a and a != "System" and a != "Chitragupta":
                agents_set.add(a)

        for conn in connections:
            if conn.get("from") and conn.get("from") != "System":
                agents_set.add(conn["from"])
            if conn.get("to") and conn.get("to") != "System":
                agents_set.add(conn["to"])

        agents_list = sorted(list(agents_set))

        # Build adjacency list: parent -> children (from -> to)
        adj: Dict[str, List[str]] = {a: [] for a in agents_list}
        in_degree: Dict[str, int] = {a: 0 for a in agents_list}

        for conn in connections:
            parent = conn.get("from")
            child = conn.get("to")
            if parent in adj and child in adj:
                adj[parent].append(child)
                in_degree[child] += 1

        # Roots are agents with in-degree = 0 (no parents)
        roots = [a for a in agents_list if in_degree[a] == 0]

        # BFS Queue initialization
        # Queue elements are (node, level)
        queue = []
        levels = {}
        visited = set()

        for root in roots:
            queue.append((root, 0))
            visited.add(root)
            levels[root] = 0

        # Run BFS
        head = 0
        while head < len(queue):
            curr, level = queue[head]
            head += 1
            levels[curr] = level

            for child in adj.get(curr, []):
                if child not in visited:
                    visited.add(child)
                    queue.append((child, level + 1))

        # Handle cycles or disconnected components that didn't get visited
        unvisited = [a for a in agents_list if a not in visited]
        for node in unvisited:
            # Check if it has a resolved parent that was visited
            resolved_parent = False
            for conn in connections:
                if conn.get("to") == node and conn.get("from") in visited:
                    p_level = levels[conn["from"]]
                    levels[node] = p_level + 1
                    visited.add(node)
                    resolved_parent = True
                    break
            
            if not resolved_parent:
                # Cycle fallback or separate root
                levels[node] = 0
                visited.add(node)

        return {
            "agents": agents_list,
            "levels": levels,
            "connections": connections
        }

    def set_agent_parent(self, agent_name: str, parent_name: Optional[str]):
        """
        Updates the hierarchy connections: sets the parent for a given agent.
        """
        agent_name = agent_name.strip()
        connections = self.get_connections()

        # Remove existing connection pointing to this agent (an agent has max 1 parent)
        connections = [c for c in connections if c.get("to") != agent_name]

        if parent_name and parent_name.strip():
            parent_name = parent_name.strip()
            if agent_name != parent_name: # Prevent self-loops
                connections.append({"from": parent_name, "to": agent_name})

        self.save_connections(connections)
