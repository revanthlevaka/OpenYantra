"""
examples/bootstrap.py — The Chitragupta Puja
Quickstart: create and populate an OpenYantra Chitrapat

Run once:
    python examples/bootstrap.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from openyantra import OpenYantra

oy = OpenYantra("~/openyantra/chitrapat.ods", agent_name="Chitragupta")

oy.bootstrap(
    user_name  = "Your Name",
    occupation = "Your Occupation",
    location   = "Your City, Country",
)

oy.add_project(
    project    = "My First Project",
    domain     = "Work",
    status     = "Active",
    priority   = "High",
    next_step  = "Define scope",
)

oy.add_task(
    task     = "Push OpenYantra to GitHub",
    project  = "OpenYantra",
    priority = "High",
    status   = "Pending",
)

print("\n" + "="*60)
print("CHITRAGUPTA CONTEXT BLOCK:")
print("="*60)
print(oy.build_system_prompt_block())
print(f"\nChitrapat ready at ~/openyantra/chitrapat.ods")
print("Open with: libreoffice ~/openyantra/chitrapat.ods")
