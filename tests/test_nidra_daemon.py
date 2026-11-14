"""
tests/test_nidra_daemon.py -- Unit tests for NidraDaemon (Soul-Engine) and Routing Benchmark
"""

import time
from openyantra.core import OpenYantra
from openyantra.yantra_nidra import NidraDaemon
from benchmarks.benchmark_routing import run_benchmark, format_benchmark_table


def test_nidra_daemon_lifecycle(tmp_path):
    chitrapat = tmp_path / "chitrapat.ods"
    oy = OpenYantra(chitrapat)
    oy.bootstrap(user_name="Soul Tester", occupation="Engineer")

    logs = []
    def log_capture(msg: str):
        logs.append(msg)

    # 1. Daemon initialized with short idle threshold for test
    daemon = NidraDaemon(
        oy,
        interval_seconds=1,
        idle_threshold_seconds=0.1,  # 100ms idle threshold
        provider="heuristic",
        dry_run=False,
        logger_func=log_capture
    )

    assert daemon.interval == 1
    assert daemon.idle_threshold == 0.1

    # 2. Add an open loop and session log to create work
    oy.add_open_loop(topic="Pending loop to consolidate", context="Test context", ttl_days=0)  # Expired immediately
    oy.log_session(topics=["Daemon Architecture"], decisions=["Deploy autonomous daemon"])

    # Simulate quiet idle period
    time.sleep(0.2)

    # 3. Trigger check_and_consolidate
    report = daemon.check_and_consolidate()
    assert report is not None
    assert "sessions_clustered" in report
    assert any("[Soul-Engine]" in l for l in logs)

    # 4. Immediate second check should return None (already consolidated, no new writes)
    second_report = daemon.check_and_consolidate()
    assert second_report is None

    # 5. Test run_loop bounded by max_cycles
    daemon.run_loop(max_cycles=1)
    assert daemon._running is False


def test_routing_benchmark_execution():
    """Verify that the benchmark runs cleanly and returns valid metrics."""
    res = run_benchmark(iterations=1)
    assert "baseline" in res
    assert "zero_retention_routing" in res
    assert res["zero_retention_routing"]["accuracy_pct"] >= 75.0
    assert res["zero_retention_routing"]["token_savings_pct"] > 0

    table_md = format_benchmark_table(res)
    assert "| Evaluation Metric |" in table_md
    assert "Zero-Retention Subspace Router" in table_md
