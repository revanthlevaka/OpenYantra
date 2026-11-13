from openyantra.core import (
    OpenYantra, WriteRequest, detect_active_project,
    SHEET_TASKS, SHEET_OPEN_LOOPS, SHEET_PROJECTS, SHEET_BELIEFS
)
from openyantra import cognitive_mcp as mcp_mod


def test_detect_active_project(tmp_path, monkeypatch):
    # 1. Inside git directory
    git_dir = tmp_path / "mock-saas-repo"
    (git_dir / ".git").mkdir(parents=True)
    detected = detect_active_project(start_path=git_dir / "src")
    assert detected == "mock-saas-repo"

    # 2. Env variable override
    monkeypatch.setenv("OPENYANTRA_PROJECT", "custom-client-portal")
    assert detect_active_project() == "custom-client-portal"


def test_workspace_isolation_load_session_context(tmp_path):
    ods_path = tmp_path / "chitrapat.ods"
    oy = OpenYantra(path=ods_path)
    oy.bootstrap("WorkspaceUser")

    # Add Project Alpha & Project Beta
    oy.request_write(WriteRequest(
        "User", SHEET_PROJECTS, "add",
        {"Project": "Project Alpha", "Domain": "AI", "Status": "Active"},
        confidence="High", source="User-stated", importance=8
    ))
    oy.request_write(WriteRequest(
        "User", SHEET_PROJECTS, "add",
        {"Project": "Project Beta", "Domain": "FinTech", "Status": "Active"},
        confidence="High", source="User-stated", importance=8
    ))

    # Add Project-specific and global tasks
    oy.request_write(WriteRequest(
        "User", SHEET_TASKS, "add",
        {"Task": "Fix OAuth login in Alpha", "Project": "Project Alpha", "Status": "Pending"},
        confidence="High", source="User-stated", importance=9
    ))
    oy.request_write(WriteRequest(
        "User", SHEET_TASKS, "add",
        {"Task": "Migrate database for Beta", "Project": "Project Beta", "Status": "Pending"},
        confidence="High", source="User-stated", importance=9
    ))
    oy.request_write(WriteRequest(
        "User", SHEET_TASKS, "add",
        {"Task": "Renew global SSL certificate", "Status": "Pending"},
        confidence="High", source="User-stated", importance=8
    ))

    # Add Project-specific loops
    oy.request_write(WriteRequest(
        "User", SHEET_OPEN_LOOPS, "add",
        {"Topic": "Alpha JWT token expiry", "Related Project": "Project Alpha", "Resolved?": "No"},
        confidence="Medium", source="User-stated", importance=7
    ))
    oy.request_write(WriteRequest(
        "User", SHEET_OPEN_LOOPS, "add",
        {"Topic": "Beta audit compliance checklist", "Related Project": "Project Beta", "Resolved?": "No"},
        confidence="Medium", source="User-stated", importance=7
    ))

    # Add Global Belief
    oy.request_write(WriteRequest(
        "User", SHEET_BELIEFS, "add",
        {"Topic": "Security", "Position": "Rotate API keys quarterly", "Domain": "Security"},
        confidence="High", source="User-stated", importance=9
    ))

    # 1. Unscoped (global) context contains everything
    ctx_global = oy.load_session_context()
    global_task_texts = [t.get("Task") for t in ctx_global["tasks"]]
    assert "Fix OAuth login in Alpha" in global_task_texts
    assert "Migrate database for Beta" in global_task_texts
    assert "Renew global SSL certificate" in global_task_texts

    # 2. Scoped to Project Alpha
    ctx_alpha = oy.load_session_context(project_scope="Project Alpha")
    alpha_tasks = [t.get("Task") for t in ctx_alpha["tasks"]]
    alpha_loops = [l.get("Topic") for l in ctx_alpha["open_loops"]]

    assert "Fix OAuth login in Alpha" in alpha_tasks
    assert "Renew global SSL certificate" in alpha_tasks  # Global tasks preserved
    assert "Migrate database for Beta" not in alpha_tasks  # Isolated!

    assert "Alpha JWT token expiry" in alpha_loops
    assert "Beta audit compliance checklist" not in alpha_loops  # Isolated!

    # Global beliefs remain shared
    assert any("Rotate API keys quarterly" in str(b.get("Position", "")) for b in ctx_alpha["beliefs"])

    # 3. Scoped to Project Beta
    ctx_beta = oy.load_session_context(project_scope="Project Beta")
    beta_tasks = [t.get("Task") for t in ctx_beta["tasks"]]
    beta_loops = [l.get("Topic") for l in ctx_beta["open_loops"]]

    assert "Migrate database for Beta" in beta_tasks
    assert "Fix OAuth login in Alpha" not in beta_tasks  # Isolated!
    assert "Beta audit compliance checklist" in beta_loops
    assert "Alpha JWT token expiry" not in beta_loops  # Isolated!


def test_workspace_isolation_context_markdown(tmp_path):
    ods_path = tmp_path / "chitrapat.ods"
    oy = OpenYantra(path=ods_path)
    oy.bootstrap("MarkdownUser")

    oy.request_write(WriteRequest(
        "User", SHEET_TASKS, "add",
        {"Task": "Alpha-specific task item", "Project": "AppAlpha", "Priority": "High", "Status": "Pending"},
        confidence="High", source="User-stated", importance=9
    ))
    oy.request_write(WriteRequest(
        "User", SHEET_TASKS, "add",
        {"Task": "Beta-specific task item", "Project": "AppBeta", "Priority": "High", "Status": "Pending"},
        confidence="High", source="User-stated", importance=9
    ))

    md_alpha = oy.build_context_markdown(project_scope="AppAlpha")
    assert "Alpha-specific task item" in md_alpha
    assert "Beta-specific task item" not in md_alpha

    md_beta = oy.build_context_markdown(project_scope="AppBeta")
    assert "Beta-specific task item" in md_beta
    assert "Alpha-specific task item" not in md_beta


def test_workspace_isolation_mcp(tmp_path, monkeypatch):
    ods_path = tmp_path / "chitrapat.ods"
    oy = OpenYantra(path=ods_path)
    oy.bootstrap("MCPUser")

    oy.request_write(WriteRequest(
        "User", SHEET_TASKS, "add",
        {"Task": "Alpha MCP Secret Task", "Project": "SecretAlpha", "Priority": "High", "Status": "Pending"},
        confidence="High", source="User-stated", importance=9
    ))
    oy.request_write(WriteRequest(
        "User", SHEET_TASKS, "add",
        {"Task": "Beta MCP Secret Task", "Project": "SecretBeta", "Priority": "High", "Status": "Pending"},
        confidence="High", source="User-stated", importance=9
    ))

    monkeypatch.setattr(mcp_mod, "oy", oy)

    # Scoped request for SecretAlpha
    res = mcp_mod.handle_call_tool(1, {
        "name": "get_system_context",
        "arguments": {"project": "SecretAlpha"}
    })
    text = res["result"]["content"][0]["text"]
    assert "Alpha MCP Secret Task" in text
    assert "Beta MCP Secret Task" not in text
