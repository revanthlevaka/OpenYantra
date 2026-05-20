import os
import json
import pytest
import shutil
import tempfile
from cognitive_db import CognitiveMemoryStore
from cognitive_mcp import handle_call_tool

@pytest.fixture
def temp_db():
    # Setup temporary directory and database file
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "cognitive_memories.json")
    store = CognitiveMemoryStore(file_path=db_path)
    yield store
    # Cleanup
    shutil.rmtree(temp_dir)

def test_write_and_read_memory(temp_db):
    # Test basic write and read
    mem = temp_db.write(
        key="test-key",
        type_val="fact",
        agent="CEO",
        content="This is a test memory content",
        tags=["test", "pytest"]
    )
    assert mem["key"] == "test-key"
    assert mem["type"] == "fact"
    assert mem["agent"] == "CEO"
    assert mem["content"] == "This is a test memory content"
    assert "test" in mem["tags"]
    
    # Read back
    retrieved = temp_db.read("test-key")
    assert retrieved is not None
    assert retrieved["content"] == "This is a test memory content"

def test_delete_memory(temp_db):
    # Write memory
    temp_db.write("key-to-delete", "decision", "CTO", "Should be deleted")
    assert temp_db.read("key-to-delete") is not None
    
    # Delete
    success = temp_db.delete("key-to-delete")
    assert success is True
    assert temp_db.read("key-to-delete") is None

def test_search_memories(temp_db):
    # Write some memories
    temp_db.write("m1", "fact", "CEO", "Blue sky", ["color", "weather"])
    temp_db.write("m2", "decision", "CTO", "Green grass", ["color", "nature"])
    temp_db.write("m3", "observation", "CEO", "Cloudy sky", ["weather"])
    
    # Search by query matching content/key
    results = temp_db.search(query="sky")
    assert len(results) == 2
    assert any(m["key"] == "m1" for m in results)
    assert any(m["key"] == "m3" for m in results)
    
    # Search by type
    results_type = temp_db.search(type_val="decision")
    assert len(results_type) == 1
    assert results_type[0]["key"] == "m2"
    
    # Search by tags
    results_tag = temp_db.search(tags=["color"])
    assert len(results_tag) == 2

def test_stats(temp_db):
    temp_db.write("m1", "fact", "CEO", "Content 1")
    temp_db.write("m2", "decision", "CTO", "Content 2")
    temp_db.write("m3", "fact", "CEO", "Content 3")
    
    s = temp_db.stats()
    assert s["totalMemories"] == 3
    assert s["countByType"]["fact"] == 2
    assert s["countByType"]["decision"] == 1
    assert s["countByAgent"]["CEO"] == 2
    assert s["countByAgent"]["CTO"] == 1

def test_hierarchy(temp_db):
    # Get hierarchy (should be empty initially)
    h = temp_db.get_hierarchy()
    assert len(h["agents"]) == 0
    
    # Set parent (adds agents and connections)
    temp_db.set_agent_parent("CEO", "System")
    temp_db.set_agent_parent("CTO", "CEO")
    temp_db.set_agent_parent("CFO", "CEO")
    temp_db.set_agent_parent("Architect", "CTO")
    
    # Get solved hierarchy
    h = temp_db.get_hierarchy()
    assert "CEO" in h["agents"]
    assert "CTO" in h["agents"]
    assert "CFO" in h["agents"]
    assert "Architect" in h["agents"]
    assert "System" not in h["agents"]
    
    levels = h["levels"]
    assert levels["CEO"] == 0
    assert levels["CTO"] == 1
    assert levels["CFO"] == 1
    assert levels["Architect"] == 2

def test_mcp_tool_calls(temp_db):
    # Test via MCP tool calling handler
    # Write
    resp = handle_call_tool(1, {
        "name": "memory_write",
        "arguments": {
            "key": "mcp-key",
            "type": "fact",
            "agent": "System",
            "content": "MCP written value",
            "tags": ["mcp"]
        }
    }, store=temp_db)
    
    assert "error" not in resp
    res_data = json.loads(resp["result"]["content"][0]["text"])
    assert res_data["key"] == "mcp-key"
    
    # Read
    resp_read = handle_call_tool(2, {
        "name": "memory_read",
        "arguments": {"key": "mcp-key"}
    }, store=temp_db)
    assert "error" not in resp_read
    read_data = json.loads(resp_read["result"]["content"][0]["text"])
    assert read_data["content"] == "MCP written value"
    
    # Search
    resp_search = handle_call_tool(3, {
        "name": "memory_search",
        "arguments": {"query": "value"}
    }, store=temp_db)
    assert "error" not in resp_search
    search_data = json.loads(resp_search["result"]["content"][0]["text"])
    assert len(search_data) == 1
    
    # Stats
    resp_stats = handle_call_tool(4, {
        "name": "memory_stats",
        "arguments": {}
    }, store=temp_db)
    assert "error" not in resp_stats
    stats_data = json.loads(resp_stats["result"]["content"][0]["text"])
    assert stats_data["totalMemories"] >= 1
    
    # Delete
    resp_del = handle_call_tool(5, {
        "name": "memory_delete",
        "arguments": {"key": "mcp-key"}
    }, store=temp_db)
    assert "error" not in resp_del
    assert "successful: True" in resp_del["result"]["content"][0]["text"]
    assert temp_db.read("mcp-key") is None
