"""
cognitive_mcp.py -- Model Context Protocol (MCP) Stdio Server
Exposes tools to read, write, search, delete, and inspect memories from the Cognitive Memory Store,
as well as managing OpenYantra tasks, projects, open loops, morning briefs, and spreadsheet rows.
"""

import sys
import json
import traceback
import argparse
from pathlib import Path
from cognitive_db import CognitiveMemoryStore

# Map short sheet names to correct OpenYantra SHEET constants
SHEET_MAP = {
    "index": "🗂 INDEX",
    "identity": "👤 Identity",
    "goals": "🎯 Goals",
    "projects": "🚀 Projects",
    "people": "👥 People",
    "preferences": "💡 Preferences",
    "beliefs": "🧠 Beliefs",
    "tasks": "✅ Tasks",
    "open_loops": "🔓 Open Loops",
    "session_log": "📅 Session Log",
    "agent_config": "⚙️ Agent Config",
    "ledger": "📒 Agrasandhanī",
    "inbox": "📥 Inbox",
    "corrections": "✏️ Corrections",
    "quarantine": "🔒 Quarantine",
    "security_log": "🛡️ Security Log"
}

# Parse command line arguments
parser = argparse.ArgumentParser(description="OpenYantra Cognitive & Sheet MCP Server")
parser.add_argument("--file", "-f", default=str(Path.home() / "openyantra" / "chitrapat.ods"))
args, unknown = parser.parse_known_args()

# Expand and resolve spreadsheet path
sheet_path = Path(args.file).expanduser()

# Initialize cognitive db store
# Database path lives in the same folder as the sheet
db_dir = sheet_path.parent
db_dir.mkdir(parents=True, exist_ok=True)
db = CognitiveMemoryStore(db_dir / "cognitive_memories.json")

def log(msg: str):
    """Log to stderr so it does not interfere with stdout JSON-RPC."""
    sys.stderr.write(f"[Cognitive-MCP] {msg}\n")
    sys.stderr.flush()

# Load the main OpenYantra sheet engine
oy = None
try:
    sys.path.insert(0, str(Path(__file__).parent))
    from openyantra import OpenYantra, WriteRequest
    log(f"Attempting to load OpenYantra sheet: {sheet_path}")
    if sheet_path.exists():
        oy = OpenYantra(str(sheet_path), agent_name="Cognitive-MCP")
        log("OpenYantra sheet engine successfully loaded.")
    else:
        log(f"Warning: Sheet file '{sheet_path}' does not exist. Sheet tools will fail until created.")
except Exception as e:
    log(f"Error importing or loading OpenYantra: {e}")
    log(traceback.format_exc())

def send_response(response: dict):
    sys.stdout.write(json.dumps(response) + "\n")
    sys.stdout.flush()

def make_error(req_id, code: int, message: str, data: dict = None) -> dict:
    err = {"code": code, "message": message}
    if data:
        err["data"] = data
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": err
    }

def make_text_response(req_id, text: str) -> dict:
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {
            "content": [{"type": "text", "text": text}]
        }
    }

def make_error_response(req_id, message: str) -> dict:
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {
            "content": [{"type": "text", "text": f"Error: {message}"}],
            "isError": True
        }
    }

def handle_initialize(req_id, params):
    log("Received initialize request")
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "openyantra-mcp-server",
                "version": "1.1.0"
            }
        }
    }

def handle_list_tools(req_id):
    log("Received tools/list request")
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "result": {
            "tools": [
                {
                    "name": "memory_write",
                    "description": "Creates or updates a memory key (case-insensitive). Use this to persist agent state, identity context, design decisions, and facts.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "key": {"type": "string", "description": "Unique identifier for the memory (case-insensitive)"},
                            "type": {"type": "string", "enum": ["decision", "fact", "context", "observation"], "description": "Type of memory"},
                            "agent": {"type": "string", "description": "Agent name writing the memory"},
                            "content": {"type": "string", "description": "Text details of the memory"},
                            "tags": {"type": "array", "items": {"type": "string"}, "description": "Optional list of tags for metadata filtering"}
                        },
                        "required": ["key", "type", "agent", "content"]
                    }
                },
                {
                    "name": "memory_read",
                    "description": "Retrieves details of a specific memory key.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "key": {"type": "string", "description": "Unique key of the memory to fetch"}
                        },
                        "required": ["key"]
                    }
                },
                {
                    "name": "memory_search",
                    "description": "Searches cognitive memories with filters (substring search on key/content, type, and tags).",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Substring matching memory key or content"},
                            "type": {"type": "string", "description": "Filter by type (decision, fact, context, observation)"},
                            "tags": {"type": "array", "items": {"type": "string"}, "description": "Filter by tags (memory must match ALL tags)"}
                        }
                    }
                },
                {
                    "name": "memory_delete",
                    "description": "Permanently deletes a memory by its key.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "key": {"type": "string", "description": "The unique key to delete"}
                        },
                        "required": ["key"]
                    }
                },
                {
                    "name": "memory_stats",
                    "description": "Retrieves aggregate database statistics including total count, counts by type, and counts by agent.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {}
                    }
                },
                # OpenYantra Sheets and Operations Tools
                {
                    "name": "get_system_context",
                    "description": "Returns the complete formatted system prompt block for OpenYantra, containing active loops, projects, tasks, beliefs, preferences, and identity parameters.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {}
                    }
                },
                {
                    "name": "health_check",
                    "description": "Checks system health, returning database/sheet status and counts of pending loops, inbox items, and stale projects.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {}
                    }
                },
                {
                    "name": "morning_brief",
                    "description": "Generates the morning brief summary for the day, detailing streaks and outstanding items.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {}
                    }
                },
                {
                    "name": "read_sheet",
                    "description": "Reads raw rows from a specific OpenYantra sheet (e.g., 'projects', 'tasks', 'open_loops', 'people', 'goals', 'beliefs', 'preferences', 'inbox', 'ledger', 'identity').",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "sheet": {
                                "type": "string",
                                "enum": ["index", "identity", "goals", "projects", "people", "preferences", "beliefs", "tasks", "open_loops", "session_log", "agent_config", "ledger", "inbox", "corrections", "quarantine", "security_log"],
                                "description": "Name of the sheet to read"
                            }
                        },
                        "required": ["sheet"]
                    }
                },
                {
                    "name": "add_inbox_item",
                    "description": "Appends a raw item or thought to the Inbox sheet for future routing.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "content": {"type": "string", "description": "The item text or message to add"},
                            "source": {"type": "string", "description": "Source or agent name posting this item", "default": "MCP-agent"}
                        },
                        "required": ["content"]
                    }
                },
                {
                    "name": "add_open_loop",
                    "description": "Logs a new open loop in the system.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "topic": {"type": "string", "description": "Unique topic title"},
                            "context": {"type": "string", "description": "Details or unresolved context"},
                            "priority": {"type": "string", "enum": ["High", "Medium", "Low"], "default": "Medium"},
                            "importance": {"type": "integer", "description": "Importance level (1-10)", "default": 5}
                        },
                        "required": ["topic", "context"]
                    }
                },
                {
                    "name": "resolve_open_loop",
                    "description": "Resolves an existing open loop by topic name.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "topic": {"type": "string", "description": "Topic title to resolve"},
                            "resolution": {"type": "string", "description": "Resolution details (optional)", "default": ""}
                        },
                        "required": ["topic"]
                    }
                },
                {
                    "name": "add_task",
                    "description": "Creates a new task in the Tasks sheet.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "task": {"type": "string", "description": "Task title"},
                            "project": {"type": "string", "description": "Associated project name (optional)", "default": ""},
                            "priority": {"type": "string", "enum": ["High", "Medium", "Low"], "default": "Medium"},
                            "deadline": {"type": "string", "description": "Deadline (YYYY-MM-DD) (optional)", "default": ""}
                        },
                        "required": ["task"]
                    }
                },
                {
                    "name": "complete_task",
                    "description": "Marks a task as completed ('Status' -> 'Done').",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "task": {"type": "string", "description": "Task title to complete"}
                        },
                        "required": ["task"]
                    }
                },
                {
                    "name": "add_project",
                    "description": "Creates a new project in the Projects sheet.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "project": {"type": "string", "description": "Name of the project"},
                            "domain": {"type": "string", "description": "Domain of the project (optional)", "default": ""},
                            "status": {"type": "string", "enum": ["Active", "Completed", "On Hold"], "default": "Active"},
                            "next_step": {"type": "string", "description": "Next actions/step description (optional)", "default": ""}
                        },
                        "required": ["project"]
                    }
                }
            ]
        }
    }

def handle_call_tool(req_id, params, store=None):
    name = params.get("name")
    arguments = params.get("arguments", {})
    log(f"Calling tool: {name} with arguments: {arguments}")
    
    active_db = store or db

    try:
        # Cognitive database store operations
        if name == "memory_write":
            key = arguments.get("key")
            type_val = arguments.get("type")
            agent = arguments.get("agent")
            content = arguments.get("content")
            tags = arguments.get("tags")
            
            res = active_db.write(key, type_val, agent, content, tags)
            return make_text_response(req_id, json.dumps(res, indent=2))

        elif name == "memory_read":
            key = arguments.get("key")
            res = active_db.read(key)
            if not res:
                return make_error_response(req_id, f"Memory key '{key}' not found.")
            return make_text_response(req_id, json.dumps(res, indent=2))

        elif name == "memory_search":
            query = arguments.get("query")
            type_val = arguments.get("type")
            tags = arguments.get("tags")
            
            res = active_db.search(query, type_val, tags)
            return make_text_response(req_id, json.dumps(res, indent=2))

        elif name == "memory_delete":
            key = arguments.get("key")
            success = active_db.delete(key)
            return make_text_response(req_id, f"Delete successful: {success}")

        elif name == "memory_stats":
            res = active_db.stats()
            return make_text_response(req_id, json.dumps(res, indent=2))

        # OpenYantra spreadsheet engine operations
        elif name == "get_system_context":
            if not oy:
                return make_error_response(req_id, "OpenYantra sheet engine not initialized.")
            res = oy.build_context_markdown()
            return make_text_response(req_id, res)

        elif name == "health_check":
            if not oy:
                return make_error_response(req_id, "OpenYantra sheet engine not initialized.")
            res = oy.health_check()
            return make_text_response(req_id, json.dumps(res, indent=2))

        elif name == "morning_brief":
            if not oy:
                return make_error_response(req_id, "OpenYantra sheet engine not initialized.")
            res = oy.morning_brief(format="markdown")
            return make_text_response(req_id, res)

        elif name == "read_sheet":
            if not oy:
                return make_error_response(req_id, "OpenYantra sheet engine not initialized.")
            sheet_param = arguments.get("sheet")
            if not sheet_param:
                return make_error_response(req_id, "Missing required parameter: 'sheet'")
            real_sheet = SHEET_MAP.get(sheet_param.lower(), sheet_param)
            rows = oy._read_sheet(real_sheet)
            return make_text_response(req_id, json.dumps(rows, indent=2))

        elif name == "add_inbox_item":
            if not oy:
                return make_error_response(req_id, "OpenYantra sheet engine not initialized.")
            content = arguments.get("content")
            source = arguments.get("source", "MCP-agent")
            req = WriteRequest(
                requesting_agent=source,
                sheet=SHEET_MAP["inbox"],
                operation="add",
                fields={"Item": content, "Status": "Pending", "Source": source},
                confidence="High",
                source="MCP tool call"
            )
            success = oy.request_write(req)
            return make_text_response(req_id, json.dumps({"success": success, "item": content}, indent=2))

        elif name == "add_open_loop":
            if not oy:
                return make_error_response(req_id, "OpenYantra sheet engine not initialized.")
            topic = arguments.get("topic")
            context = arguments.get("context")
            priority = arguments.get("priority", "Medium")
            importance = arguments.get("importance", 5)
            success = oy.add_open_loop(topic, context, priority, importance)
            return make_text_response(req_id, json.dumps({"success": success, "topic": topic}, indent=2))

        elif name == "resolve_open_loop":
            if not oy:
                return make_error_response(req_id, "OpenYantra sheet engine not initialized.")
            topic = arguments.get("topic")
            resolution = arguments.get("resolution", "")
            success = oy.resolve_open_loop(topic, resolution)
            return make_text_response(req_id, json.dumps({"success": success, "topic": topic}, indent=2))

        elif name == "add_task":
            if not oy:
                return make_error_response(req_id, "OpenYantra sheet engine not initialized.")
            task = arguments.get("task")
            project = arguments.get("project", "")
            priority = arguments.get("priority", "Medium")
            deadline = arguments.get("deadline", "")
            success = oy.add_task(task, project, priority, deadline)
            return make_text_response(req_id, json.dumps({"success": success, "task": task}, indent=2))

        elif name == "complete_task":
            if not oy:
                return make_error_response(req_id, "OpenYantra sheet engine not initialized.")
            task = arguments.get("task")
            req = WriteRequest(
                requesting_agent="MCP-agent",
                sheet=SHEET_MAP["tasks"],
                operation="update",
                fields={"Status": "Done"},
                row_identifier=task,
                confidence="High",
                source="MCP tool call"
            )
            success = oy.request_write(req)
            return make_text_response(req_id, json.dumps({"success": success, "task": task}, indent=2))

        elif name == "add_project":
            if not oy:
                return make_error_response(req_id, "OpenYantra sheet engine not initialized.")
            project = arguments.get("project")
            domain = arguments.get("domain", "")
            status = arguments.get("status", "Active")
            next_step = arguments.get("next_step", "")
            success = oy.add_project(project, domain, status, next_step)
            return make_text_response(req_id, json.dumps({"success": success, "project": project}, indent=2))

        else:
            return make_error_response(req_id, f"Unknown tool: {name}")
    except Exception as e:
        log(f"Error executing tool {name}: {traceback.format_exc()}")
        return make_error_response(req_id, str(e))

def main():
    log("Cognitive Memory & OpenYantra Sheet MCP Server started.")
    
    # Simple line-by-line JSON-RPC reader loop
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            req_id = req.get("id")
            method = req.get("method")
            params = req.get("params", {})
            
            if method == "initialize":
                send_response(handle_initialize(req_id, params))
            elif method == "notifications/initialized":
                log("Client initialized.")
            elif method == "tools/list":
                send_response(handle_list_tools(req_id))
            elif method == "tools/call":
                send_response(handle_call_tool(req_id, params))
            elif method is not None:
                send_response(make_error(req_id, -32601, f"Method not found: {method}"))
        except Exception as e:
            log(f"Error handling request: {str(e)}")
            log(traceback.format_exc())

if __name__ == "__main__":
    main()
