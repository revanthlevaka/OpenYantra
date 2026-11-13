"""
tests/test_sutradhar.py -- Unit tests for Sutradhar Graph Layer v6.2.0
Tests: edges table, add_edge, delete_edge, get_edges, traverse CTE, infer_edges
"""

import pytest

from openyantra.yantra_sqlite import SyncEngine


@pytest.fixture
def engine(tmp_path):
    """Create a fresh SyncEngine with an ephemeral SQLite DB."""
    db = tmp_path / "test.db"
    eng = SyncEngine(str(db))
    return eng


class TestEdgeCRUD:
    """Test add_edge, get_edges, delete_edge."""

    def test_add_edge_creates(self, engine):
        result = engine.add_edge("projects", "OpenYantra", "tasks", "Build UI", "belongs_to")
        assert result["status"] == "created"
        assert result["edge_id"] is not None

    def test_add_edge_idempotent(self, engine):
        r1 = engine.add_edge("projects", "OpenYantra", "tasks", "Build UI", "belongs_to")
        r2 = engine.add_edge("projects", "OpenYantra", "tasks", "Build UI", "belongs_to")
        assert r1["status"] == "created"
        assert r2["status"] == "exists"
        assert r1["edge_id"] == r2["edge_id"]

    def test_get_edges_unfiltered(self, engine):
        engine.add_edge("projects", "A", "tasks", "T1", "belongs_to")
        engine.add_edge("projects", "B", "tasks", "T2", "belongs_to")
        edges = engine.get_edges()
        assert len(edges) == 2

    def test_get_edges_filtered(self, engine):
        engine.add_edge("projects", "A", "tasks", "T1", "belongs_to")
        engine.add_edge("people", "Alice", "tasks", "T2", "mentions")
        edges = engine.get_edges(source_type="projects")
        assert len(edges) == 1
        assert edges[0]["source_id"] == "A"

    def test_delete_edge(self, engine):
        r = engine.add_edge("projects", "A", "tasks", "T1", "belongs_to")
        eid = r["edge_id"]
        assert engine.delete_edge(eid) is True
        assert engine.get_edges() == []

    def test_delete_nonexistent(self, engine):
        assert engine.delete_edge(9999) is False


class TestTraverse:
    """Test recursive CTE traversal."""

    def test_simple_traverse(self, engine):
        engine.add_edge("projects", "P1", "tasks", "T1", "belongs_to")
        engine.add_edge("tasks", "T1", "people", "Alice", "assigned_to")

        nodes = engine.traverse("projects", "P1", max_hops=3)
        # Should find T1 at hop 1, Alice at hop 2
        node_ids = [(n["node_type"], n["node_id"]) for n in nodes]
        assert ("tasks", "T1") in node_ids
        assert ("people", "Alice") in node_ids

    def test_traverse_respects_max_hops(self, engine):
        engine.add_edge("projects", "P1", "tasks", "T1", "belongs_to")
        engine.add_edge("tasks", "T1", "people", "Alice", "assigned_to")
        engine.add_edge("people", "Alice", "goals", "G1", "related_to")

        nodes_1hop = engine.traverse("projects", "P1", max_hops=1)
        node_ids_1 = [(n["node_type"], n["node_id"]) for n in nodes_1hop]
        assert ("tasks", "T1") in node_ids_1
        assert ("people", "Alice") not in node_ids_1

    def test_traverse_cycle_guard(self, engine):
        """A -> B -> C -> A should not loop infinitely."""
        engine.add_edge("projects", "A", "projects", "B", "related_to")
        engine.add_edge("projects", "B", "projects", "C", "related_to")
        engine.add_edge("projects", "C", "projects", "A", "related_to")

        nodes = engine.traverse("projects", "A", max_hops=5)
        # Should terminate and not contain the seed
        node_ids = [(n["node_type"], n["node_id"]) for n in nodes]
        # B and C should be found
        assert ("projects", "B") in node_ids
        assert ("projects", "C") in node_ids
        # Should not have infinite results
        assert len(nodes) <= 10

    def test_traverse_bidirectional(self, engine):
        """Traversal should find nodes linked in reverse direction."""
        engine.add_edge("tasks", "T1", "projects", "P1", "belongs_to")

        # Start from P1 -- should find T1 via reverse edge
        nodes = engine.traverse("projects", "P1", max_hops=2)
        node_ids = [(n["node_type"], n["node_id"]) for n in nodes]
        assert ("tasks", "T1") in node_ids

    def test_traverse_empty(self, engine):
        """Traversal from a node with no edges returns empty."""
        nodes = engine.traverse("projects", "NonExistent", max_hops=3)
        assert nodes == []


class TestInferEdges:
    """Test auto-edge inference."""

    def test_infer_task_project_edge(self, engine):
        engine.infer_edges("tasks", {"task": "Build frontend", "project": "OpenYantra"})
        edges = engine.get_edges(source_type="tasks")
        assert len(edges) == 1
        assert edges[0]["target_type"] == "projects"
        assert edges[0]["target_id"] == "OpenYantra"

    def test_infer_loop_project_edge(self, engine):
        engine.infer_edges("open_loops", {"topic": "Missing API", "related_project": "OpenYantra"})
        edges = engine.get_edges(source_type="open_loops")
        assert len(edges) == 1
        assert edges[0]["edge_type"] == "related_to"

    def test_infer_mention_edge(self, engine):
        # Insert a person directly (write() requires ledger setup)
        with engine._connect() as conn:
            conn.execute(
                "INSERT INTO people (name, relationship) VALUES (?, ?)",
                ("Alice", "colleague"))
        engine.infer_edges("tasks", {"task": "Review PR", "notes": "Assigned to @Alice for feedback"})
        edges = engine.get_edges(target_type="people")
        assert len(edges) == 1
        assert edges[0]["target_id"] == "Alice"
        assert edges[0]["edge_type"] == "mentions"

    def test_infer_no_project_no_edge(self, engine):
        """Tasks without a project field should not create edges."""
        engine.infer_edges("tasks", {"task": "Random task"})
        edges = engine.get_edges()
        assert len(edges) == 0

    def test_infer_capitalized_fields(self, engine):
        """ODS field names (capitalized and spaced) should be mapped properly."""
        engine.infer_edges("tasks", {"Task": "Deploy cluster", "Project": "CloudOps"})
        edges = engine.get_edges(source_type="tasks")
        assert len(edges) == 1
        assert edges[0]["source_id"] == "Deploy cluster"
        assert edges[0]["target_id"] == "CloudOps"

        engine.infer_edges("open_loops", {"Topic": "Database failover", "Related Project": "CloudOps"})
        loop_edges = engine.get_edges(source_type="open_loops")
        assert len(loop_edges) == 1
        assert loop_edges[0]["source_id"] == "Database failover"
        assert loop_edges[0]["target_id"] == "CloudOps"

    def test_delete_node_edges(self, engine):
        """Deleting node edges cleans up both incoming and outgoing edges."""
        engine.add_edge("tasks", "T1", "projects", "P1", "belongs_to")
        engine.add_edge("projects", "P1", "tasks", "T2", "contains")
        assert len(engine.get_edges()) == 2

        deleted = engine.delete_node_edges("tasks", "T1")
        assert deleted == 1
        assert engine.get_edges(source_id="T1") == []


class TestSutradharEndToEnd:
    """Test full integration with OpenYantra workbook writes and edge inference."""

    def test_workbook_write_automatically_infers_edges(self, tmp_path):
        from openyantra.core import OpenYantra
        chitrapat = tmp_path / "chitrapat.ods"
        oy = OpenYantra(chitrapat)
        oy.bootstrap(user_name="Graph Tester", occupation="Engineer")

        # 1. Add a task with project
        res_task = oy.add_task(task="Ship Sutradhar v6.2", project="OpenYantra", priority="High")
        assert res_task["status"] == "written"

        edges = oy.db_engine.get_edges(source_type="tasks")
        assert len(edges) == 1
        assert edges[0]["source_id"] == "Ship Sutradhar v6.2"
        assert edges[0]["target_id"] == "OpenYantra"
        assert edges[0]["edge_type"] == "belongs_to"

        # 2. Add open loop with related project
        res_loop = oy.add_open_loop(topic="Security Audit Mudra", context="Check SHA256", related_project="OpenYantra")
        assert res_loop["status"] == "written"

        loop_edges = oy.db_engine.get_edges(source_type="open_loops")
        assert len(loop_edges) == 1
        assert loop_edges[0]["source_id"] == "Security Audit Mudra"
        assert loop_edges[0]["target_id"] == "OpenYantra"

        # 3. Delete task and verify edge cleanup and row removal
        res_del = oy.delete_row("tasks", "Ship Sutradhar v6.2", reason="Task completed and archived")
        assert res_del["status"] == "written"

        # Verify row removed from sheet
        active_tasks = oy.get_sheet("tasks")
        assert not any(t.get("Task") == "Ship Sutradhar v6.2" for t in active_tasks)

        # Verify edge removed
        remaining_edges = oy.db_engine.get_edges(source_id="Ship Sutradhar v6.2")
        assert len(remaining_edges) == 0

        # Verify deletion logged in Agrasandhanī ledger
        ledger = oy.get_sheet("ledger")
        delete_entries = [l for l in ledger if l.get("Operation") == "delete" and l.get("Row Identifier") == "Ship Sutradhar v6.2"]
        assert len(delete_entries) == 1
        assert delete_entries[0]["Status"] == "written"
