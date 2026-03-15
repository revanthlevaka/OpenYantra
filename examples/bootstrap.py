"""
examples/bootstrap.py — Chitragupta Puja quickstart v2.2
Run once: python examples/bootstrap.py
Or use the CLI: yantra bootstrap
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from openyantra import OpenYantra, run_bootstrap_interview

# Option 1: Terminal interview (recommended)
run_bootstrap_interview("~/openyantra/chitrapat.ods")

# Option 2: Programmatic
# oy = OpenYantra("~/openyantra/chitrapat.ods", agent_name="Claude")
# oy.bootstrap(user_name="Your Name", occupation="Your Role", location="City, Country")
# oy.add_project("My First Project", domain="Work", status="Active", priority="High")
# print(oy.build_system_prompt_block())
