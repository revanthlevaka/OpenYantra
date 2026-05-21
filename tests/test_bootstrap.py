import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch
import pytest

from openyantra.core import OpenYantra, run_bootstrap_interview, SHEET_IDENTITY

@pytest.fixture
def temp_ods_path():
    temp_dir = tempfile.mkdtemp()
    ods_path = os.path.join(temp_dir, "chitrapat.ods")
    yield ods_path
    shutil.rmtree(temp_dir)

def test_bootstrap_first_time(temp_ods_path):
    # Mock inputs for the bootstrap interview (all 12 questions/steps)
    mock_inputs = [
        "forgotten projects", # Q1: pain
        "Revanth", "Engineer", "Hyderabad, India", "Telugu", # Q2: name, occupation, location, language
        "coding, fitness", # Q3: domains
        "OpenYantra", "Work", "add WebAuthn", # Q4: project 1
        "", # Q4: project 2 skip
        "Finish OpenYantra v4", "Verify NaN fix", "Clean green test suite", # Q5: long_goal, short_goal, success
        "Sita", "Colleague", "React developer", "waiting for design assets", # Q6: person 1
        "", # Q6: person 2 skip
        "casual", "VS Code", "10am-7pm IST", # Q7: comm_style, tools, work_hours
        "never suggest phone calls", # Q8: anti
        "build in public", "AI cannot code", # Q9: principle, old_belief
        "switching databases", "procrastination", # Q10: decision, recurring
        "Telegram bot", # Q11: reminder
    ]

    with patch("builtins.input", side_effect=mock_inputs):
        oy = run_bootstrap_interview(temp_ods_path, agent_name="Chitragupta")
        assert oy is not None
        assert Path(temp_ods_path).exists()
        
        # Verify identity attributes were stored
        identity = oy._read_sheet(SHEET_IDENTITY)
        name_row = next(r for r in identity if r["Attribute"] == "Full Name")
        assert name_row["Value"] is None
        
        pref_name_row = next(r for r in identity if r["Attribute"] == "Preferred Name")
        assert pref_name_row["Value"] == "Revanth"
        
        lang_row = next(r for r in identity if r["Attribute"] == "Primary Language")
        assert lang_row["Value"] == "Telugu"

def test_bootstrap_re_run_decline(temp_ods_path):
    # Create the file first to simulate existing
    oy_init = OpenYantra(temp_ods_path)
    oy_init.bootstrap(user_name="Initial Name")
    assert Path(temp_ods_path).exists()
    
    # Run bootstrap and decline re-run
    with patch("builtins.input", return_value="n"):
        oy = run_bootstrap_interview(temp_ods_path, agent_name="Chitragupta")
        assert oy is not None
        
        # Identity should still have initial name
        identity = oy._read_sheet(SHEET_IDENTITY)
        pref_name_row = next(r for r in identity if r["Attribute"] == "Preferred Name")
        assert pref_name_row["Value"] == "Initial Name"

def test_bootstrap_re_run_accept(temp_ods_path):
    # Create the file first to simulate existing
    oy_init = OpenYantra(temp_ods_path)
    oy_init.bootstrap(user_name="Initial Name")
    assert Path(temp_ods_path).exists()
    
    # Run bootstrap and accept re-run, then provide inputs for fresh interview
    mock_inputs = [
        "y", # Accept re-run
        "forgotten projects", # Q1: pain
        "Revanth New", "Engineer", "Hyderabad, India", "Telugu", # Q2: name, occupation, location, language
        "coding, fitness", # Q3: domains
        "OpenYantra", "Work", "add WebAuthn", # Q4: project 1
        "", # Q4: project 2 skip
        "Finish OpenYantra v4", "Verify NaN fix", "Clean green test suite", # Q5: long_goal, short_goal, success
        "Sita", "Colleague", "React developer", "waiting for design assets", # Q6: person 1
        "", # Q6: person 2 skip
        "casual", "VS Code", "10am-7pm IST", # Q7: comm_style, tools, work_hours
        "never suggest phone calls", # Q8: anti
        "build in public", "AI cannot code", # Q9: principle, old_belief
        "switching databases", "procrastination", # Q10: decision, recurring
        "Telegram bot", # Q11: reminder
    ]
    
    with patch("builtins.input", side_effect=mock_inputs):
        oy = run_bootstrap_interview(temp_ods_path, agent_name="Chitragupta")
        assert oy is not None
        
        # Identity should now have the new name
        identity = oy._read_sheet(SHEET_IDENTITY)
        pref_name_row = next(r for r in identity if r["Attribute"] == "Preferred Name")
        assert pref_name_row["Value"] == "Revanth New"

