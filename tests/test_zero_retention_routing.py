import time
from openyantra.core import OpenYantra, WriteRequest, SHEET_TASKS, SHEET_BELIEFS, SHEET_OPEN_LOOPS
from openyantra.yantra_sutra import SutraCompiler


def test_zero_retention_routing_accuracy_and_latency(tmp_path):
    ods_path = tmp_path / "chitrapat.ods"
    oy = OpenYantra(path=ods_path)
    oy.bootstrap("RoutingTestUser")

    # Add diverse items across sheets
    oy.request_write(WriteRequest(
        "User", SHEET_TASKS, "add",
        {"Task": "Fix critical buffer overflow in memory alloc", "Priority": "High", "Status": "Pending"},
        confidence="High", source="User-stated", importance=9
    ))
    oy.request_write(WriteRequest(
        "User", SHEET_BELIEFS, "add",
        {"Topic": "Architecture Philosophy", "Position": "Prefer immutability and functional purity", "Domain": "Engineering"},
        confidence="High", source="User-stated", importance=8
    ))
    oy.request_write(WriteRequest(
        "User", SHEET_OPEN_LOOPS, "add",
        {"Topic": "Evaluate ClickHouse vs DuckDB", "Priority": "Medium", "Resolved?": "No"},
        confidence="Medium", source="User-stated", importance=7
    ))

    # Ensure index and centroids are synced
    oy._vidyakosha.sync(ods_path)
    assert len(oy._vidyakosha._centroids) >= 3

    # Benchmark routing latency
    t0 = time.perf_counter()
    task_routes = oy.route("implement buffer fix for memory alloc", top_k=2)
    latency_ms = (time.perf_counter() - t0) * 1000.0

    # Latency should be sub-5ms (typically sub-millisecond)
    assert latency_ms < 50.0  # Generous upper bound for slow CI runners
    assert len(task_routes) >= 1
    # Top route should be Tasks
    assert task_routes[0]["sheet"] == SHEET_TASKS

    # Route belief query
    belief_routes = oy.route("principles of functional purity and clean code", top_k=2)
    assert len(belief_routes) >= 1
    assert belief_routes[0]["sheet"] == SHEET_BELIEFS

    # Zero-retention guarantee: verify prompt was never persisted
    assert not any("implement buffer fix" in str(r.get("text", "")) for r in oy._vidyakosha._registry)
    c_file = oy._vidyakosha.dir / "vidyakosha_centroids.json"
    assert c_file.exists()
    assert "buffer fix" not in c_file.read_text()


def test_sutra_compiler_auto_route(tmp_path):
    ods_path = tmp_path / "chitrapat.ods"
    oy = OpenYantra(path=ods_path)
    oy.bootstrap("SutraTestUser")

    oy.request_write(WriteRequest(
        "User", SHEET_TASKS, "add",
        {"Task": "Deploy Docker container to production", "Priority": "High", "Status": "Pending"},
        confidence="High", source="User-stated", importance=9
    ))
    oy.request_write(WriteRequest(
        "User", SHEET_BELIEFS, "add",
        {"Topic": "Design Philosophy", "Position": "Never compromise on data security", "Domain": "Security"},
        confidence="High", source="User-stated", importance=9
    ))

    oy._vidyakosha.sync(ods_path)

    compiler = SutraCompiler(oy)
    compiled = compiler.compile(query_text="Deploy Docker container", auto_route=True, top_k_routes=1)
    
    assert compiled["tokens"] > 0
    # Should include tasks
    assert "Deploy Docker container" in compiled["markdown"]
