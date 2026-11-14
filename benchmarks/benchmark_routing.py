"""
benchmarks/benchmark_routing.py -- Routing & Latency Benchmark for OpenYantra
Compares:
1. Full unpruned prompt compilation (baseline)
2. Sub-millisecond zero-retention centroid subspace routing (Apical Arbor pattern)
3. Full hybrid semantic search (FAISS + BM25)
"""

from __future__ import annotations

import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List

from openyantra.core import (
    OpenYantra,
    WriteRequest,
    SHEET_TASKS,
    SHEET_OPEN_LOOPS,
    SHEET_BELIEFS,
    SHEET_PROJECTS,
    SHEET_GOALS,
    SHEET_PREFERENCES,
)
from openyantra.yantra_sutra import SutraCompiler


def populate_benchmark_workspace(oy: OpenYantra):
    """Seed benchmark workspace with diverse entries across multiple sheets."""
    oy.bootstrap(user_name="Benchmark Agent", occupation="Systems Architect")

    # Tasks
    tasks = [
        ("Deploy Kubernetes cluster on AWS EKS", "CloudOps", "High"),
        ("Optimize PostgreSQL query execution plan", "Database", "High"),
        ("Refactor OAuth2 token refresh pipeline", "Security", "Medium"),
        ("Implement zero-retention routing layer", "OpenYantra", "High"),
        ("Set up Prometheus and Grafana dashboards", "Observability", "Medium"),
    ]
    for task, proj, prio in tasks:
        oy.add_task(task=task, project=proj, priority=prio)

    # Open Loops
    loops = [
        ("Unresolved bug in user authentication token expiry", "Investigate refresh timing", "Security"),
        ("Memory leak in long-lived WebSocket connections", "Audit socket handlers", "Backend"),
        ("Missing API rate limiter on public endpoints", "Define token bucket parameters", "Security"),
    ]
    for topic, ctx, proj in loops:
        oy.add_open_loop(topic=topic, context=ctx, related_project=proj)

    # Beliefs
    beliefs = [
        ("Architecture", "Local-first plain-text and spreadsheet files are durable ground truth"),
        ("Design", "Prefer functional purity and immutable data structures whenever practical"),
        ("Privacy", "Zero retention of conversational prompts preserves epistemic privacy"),
    ]
    for topic, pos in beliefs:
        oy.request_write(WriteRequest(
            requesting_agent="Benchmark",
            sheet=SHEET_BELIEFS,
            operation="add",
            fields={"Topic": topic, "Position": pos, "Domain": "Engineering"},
            confidence="High",
            source="User-stated",
            importance=9,
        ))

    # Projects
    projects = [
        ("OpenYantra", "Core memory runtime", "Active"),
        ("CloudOps", "Infrastructure automation", "Active"),
        ("Observability", "Telemetry and logs", "Active"),
    ]
    for proj, domain, status in projects:
        oy.add_project(project=proj, domain=domain, status=status)

    # Goals
    goals = [
        ("Achieve 100k Monthly Active Users milestone", "Quarterly OKR", "High"),
        ("Reduce p99 memory query latency below 2ms", "Engineering SLA", "Critical"),
    ]
    for g, gtype, prio in goals:
        oy.request_write(WriteRequest(
            requesting_agent="Benchmark",
            sheet=SHEET_GOALS,
            operation="add",
            fields={"Goal": g, "Type": gtype, "Priority": prio, "Status": "Active"},
            confidence="High",
            source="User-stated",
            importance=9,
        ))

    # Preferences
    prefs = [
        ("Editor", "Prefer Neovim with Lua configurations and minimal plugins"),
        ("CLI", "Prefer terminal commands with JSON outputs for scriptability"),
    ]
    for cat, pref in prefs:
        oy.request_write(WriteRequest(
            requesting_agent="Benchmark",
            sheet=SHEET_PREFERENCES,
            operation="add",
            fields={"Category": cat, "Preference": pref, "Strength": "Strong"},
            confidence="High",
            source="User-stated",
            importance=8,
        ))


def run_benchmark(iterations: int = 10) -> Dict[str, Any]:
    """Execute comparative benchmark and return statistics."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        ods_path = Path(tmp_dir) / "chitrapat.ods"
        oy = OpenYantra(ods_path)
        populate_benchmark_workspace(oy)

        # Ensure VidyaKosha is synced
        if hasattr(oy, "_vidyakosha") and oy._vidyakosha:
            oy._vidyakosha.sync(oy.path)

        compiler = SutraCompiler(oy)

        test_queries = [
            ("Deploy Kubernetes cluster with terraform", SHEET_TASKS),
            ("Functional purity and immutable data structures", SHEET_BELIEFS),
            ("Unresolved token expiration authentication bug", SHEET_OPEN_LOOPS),
            ("Achieve 100k Monthly Active Users SLA", SHEET_GOALS),
        ]

        # 1. Benchmark Baseline (Full unpruned prompt compilation)
        full_latencies: List[float] = []
        full_tokens: List[int] = []
        for _ in range(iterations):
            for q, _ in test_queries:
                t0 = time.perf_counter()
                compiled = compiler.compile(query_text=q, auto_route=False)
                t1 = time.perf_counter()
                full_latencies.append((t1 - t0) * 1000.0)
                full_tokens.append(compiled["tokens"])

        # 2. Benchmark Sub-Millisecond Zero-Retention Routing
        route_latencies: List[float] = []
        routed_tokens: List[int] = []
        routing_accuracy: List[bool] = []
        for _ in range(iterations):
            for q, expected_sheet in test_queries:
                t0 = time.perf_counter()
                routes = oy.route(q, top_k=2)
                t1 = time.perf_counter()
                route_latencies.append((t1 - t0) * 1000.0)

                # Check if expected sheet was routed
                routed_sheets = [r["sheet"] for r in routes]
                routing_accuracy.append(expected_sheet in routed_sheets)

                # Compile with auto_route=True
                compiled_routed = compiler.compile(query_text=q, auto_route=True, top_k_routes=2)
                routed_tokens.append(compiled_routed["tokens"])

        # 3. Benchmark Full Hybrid Search (FAISS + BM25)
        search_latencies: List[float] = []
        if hasattr(oy, "_vidyakosha") and oy._vidyakosha:
            for _ in range(iterations):
                for q, _ in test_queries:
                    t0 = time.perf_counter()
                    _ = oy._vidyakosha.query(q, top_k=5)
                    t1 = time.perf_counter()
                    search_latencies.append((t1 - t0) * 1000.0)

        avg_full_lat = sum(full_latencies) / max(1, len(full_latencies))
        avg_full_tok = sum(full_tokens) / max(1, len(full_tokens))

        avg_route_lat = sum(route_latencies) / max(1, len(route_latencies))
        avg_routed_tok = sum(routed_tokens) / max(1, len(routed_tokens))
        acc_pct = (sum(1 for a in routing_accuracy if a) / max(1, len(routing_accuracy))) * 100.0
        tok_savings = ((avg_full_tok - avg_routed_tok) / max(1, avg_full_tok)) * 100.0

        avg_search_lat = (sum(search_latencies) / max(1, len(search_latencies))) if search_latencies else 0.0

        return {
            "iterations": iterations * len(test_queries),
            "baseline": {
                "avg_latency_ms": round(avg_full_lat, 3),
                "avg_tokens": round(avg_full_tok, 1),
            },
            "zero_retention_routing": {
                "avg_latency_ms": round(avg_route_lat, 3),
                "avg_tokens": round(avg_routed_tok, 1),
                "token_savings_pct": round(tok_savings, 1),
                "accuracy_pct": round(acc_pct, 1),
            },
            "hybrid_search": {
                "avg_latency_ms": round(avg_search_lat, 3),
            },
        }


def format_benchmark_table(stats: Dict[str, Any]) -> str:
    """Format benchmark metrics into a Markdown comparison table."""
    base = stats["baseline"]
    zrr = stats["zero_retention_routing"]
    hs = stats["hybrid_search"]

    lines = [
        "| Evaluation Metric | Baseline (Full Unpruned) | Zero-Retention Subspace Router | Hybrid FAISS+BM25 |",
        "| :--- | :--- | :--- | :--- |",
        f"| **Average Latency** | {base['avg_latency_ms']:.2f} ms | **{zrr['avg_latency_ms']:.3f} ms** | {hs['avg_latency_ms']:.2f} ms |",
        f"| **Prompt Token Size** | {base['avg_tokens']:.0f} tokens | **{zrr['avg_tokens']:.0f} tokens** | N/A (Row Hits) |",
        f"| **Token Reduction** | 0.0% | **-{zrr['token_savings_pct']:.1f}%** | N/A |",
        f"| **Target Precision** | N/A | **{zrr['accuracy_pct']:.1f}%** | N/A |",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    print("\n⚡ Running OpenYantra Routing & Latency Benchmark...")
    results = run_benchmark(iterations=10)
    print("\n" + format_benchmark_table(results) + "\n")
