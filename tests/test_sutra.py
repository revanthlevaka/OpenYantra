import os
import shutil
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch

from openyantra.core import OpenYantra
from openyantra.yantra_sutra import SutraCompiler, estimate_tokens

@pytest.fixture
def temp_dir():
    d = tempfile.mkdtemp()
    yield Path(d)
    shutil.rmtree(d)

@pytest.fixture
def test_oy(temp_dir):
    ods_path = temp_dir / "chitrapat.ods"
    db_path = temp_dir / "chitrapat.db"
    
    # Copy template
    template_src = Path(__file__).parent.parent / "openyantra" / "chitrapat_template.ods"
    if template_src.exists():
        shutil.copy2(template_src, ods_path)
        
    oy = OpenYantra(ods_path)
    yield oy

def test_sutra_compiler_presets(test_oy):
    compiler = SutraCompiler(test_oy)
    
    # 1. Test conversational preset weights
    w_conv = compiler.preset_weights["conversational"]
    assert w_conv["semantic"] == 0.3
    assert w_conv["recency"] == 0.5
    assert w_conv["importance"] == 0.1
    assert w_conv["relation"] == 0.1
    
    # 2. Test analytical preset weights
    w_ana = compiler.preset_weights["analytical"]
    assert w_ana["semantic"] == 0.5
    assert w_ana["recency"] == 0.1
    assert w_ana["importance"] == 0.3
    assert w_ana["relation"] == 0.1

    # 3. Test creative preset weights
    w_crea = compiler.preset_weights["creative"]
    assert w_crea["semantic"] == 0.3
    assert w_crea["recency"] == 0.2
    assert w_crea["importance"] == 0.2
    assert w_crea["relation"] == 0.3

    # 4. Test default preset weights
    w_def = compiler.preset_weights["default"]
    assert w_def["semantic"] == 0.4
    assert w_def["recency"] == 0.3
    assert w_def["importance"] == 0.2
    assert w_def["relation"] == 0.1

def test_sutra_estimate_tokens():
    assert estimate_tokens("hello") == 1
    assert estimate_tokens("hello world standard") == 5

def test_sutra_compiler_greedy_packing(test_oy):
    mock_projects = [
        {"Project": "Alpha", "Status": "Active", "Priority": "High", "Domain": "AI", "Next Step": "Implement UI"},
        {"Project": "Beta", "Status": "Active", "Priority": "Low", "Domain": "Web", "Next Step": "Design logo"},
    ]
    mock_loops = [
        {"Topic": "Loop 1", "Resolved?": "No", "Priority": "High", "Context / What's Unresolved": "An unresolved issue"},
        {"Topic": "Loop 2", "Resolved?": "No", "Priority": "Low", "Context / What's Unresolved": "Another issue"},
    ]
    
    def mock_read(sheet_emoji):
        if "Projects" in sheet_emoji:
            return mock_projects
        elif "Loops" in sheet_emoji:
            return mock_loops
        return []
        
    with patch.object(test_oy, "_read_sheet", side_effect=mock_read):
        compiler = SutraCompiler(test_oy)
        res = compiler.compile(budget=150, sections=["projects", "loops"])
        
        assert "markdown" in res
        assert "packed" in res
        assert "discarded" in res
        
        packed_names = [item["primary_value"] for item in res["packed"]]
        assert "Alpha" in packed_names
        
        # Test with tight budget
        res_tiny = compiler.compile(budget=30, sections=["projects", "loops"])
        assert len(res_tiny["packed"]) < len(mock_projects) + len(mock_loops)

def test_sutra_compiler_settings_override(test_oy):
    custom_settings = {
        "sutra_weights": {
            "semantic": 0.8,
            "recency": 0.0,
            "importance": 0.1,
            "relation": 0.1
        }
    }
    compiler = SutraCompiler(test_oy, settings=custom_settings)
    
    mock_projects = [
        {"Project": "Alpha", "Status": "Active", "Priority": "High", "Domain": "AI", "Next Step": "Implement UI"}
    ]
    with patch.object(test_oy, "_read_sheet", return_value=mock_projects):
        res = compiler.compile(budget=500, sections=["projects"])
        assert len(res["packed"]) == 1
