"""
examples/bootstrap.py — The Chitragupta Puja (quickstart)
Run once to set up your OpenYantra Chitrapat:
    python examples/bootstrap.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from openyantra import OpenYantra

oy = OpenYantra("~/openyantra/chitrapat.ods", agent_name="Chitragupta")
oy.bootstrap(user_name="Your Name", occupation="Your Occupation",
             location="Your City, Country")

oy.add_project("My First Project", domain="Work", status="Active",
               priority="High", next_step="Define scope")
oy.add_task("Push OpenYantra to GitHub", project="OpenYantra",
            priority="High", status="Pending")

print("\n" + "="*60)
print("CHITRAGUPTA CONTEXT BLOCK (v2.0):")
print("="*60)
print(oy.build_system_prompt_block())

# v2.0 — test semantic search
print("\nSEMANTIC SEARCH TEST:")
results = oy.search("project work active")
for r in results[:3]:
    print(f"  {r['sheet'].split()[-1]:12} {str(r['primary_value'])[:40]:40} score={r['score']:.3f}")

print(f"\nChitrapat ready: ~/openyantra/chitrapat.ods")
print("Open with: libreoffice ~/openyantra/chitrapat.ods")
