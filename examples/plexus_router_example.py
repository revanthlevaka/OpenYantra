"""
examples/plexus_router_example.py -- External Routing Adapter Example (Plexus / Apical Arbor)

Demonstrates how to connect an external low-latency routing layer to OpenYantra
via the VidyaKosha.set_external_router() hook.
"""

from typing import List, Dict, Optional
from openyantra.core import OpenYantra, SHEET_TASKS, SHEET_BELIEFS, SHEET_OPEN_LOOPS


class MockPlexusRouter:
    """
    Mock implementation of a low-latency hierarchical router (e.g. Plexus / Apical Arbor).
    Performs coarse centroid projection followed by leaf filtering in sub-millisecond time.
    """

    def __init__(self):
        # Mapping domain keywords or centroids to target sheets
        self.rules = {
            "deploy": SHEET_TASKS,
            "kubernetes": SHEET_TASKS,
            "architecture": SHEET_BELIEFS,
            "principle": SHEET_BELIEFS,
            "unresolved": SHEET_OPEN_LOOPS,
            "bug": SHEET_OPEN_LOOPS,
        }

    def route(self, prompt: str, top_k: int = 2) -> Optional[List[Dict[str, float]]]:
        """
        External router entrypoint.
        Returns [{"sheet": sheet_name, "score": float}, ...] or None to trigger fallback.
        """
        p_lower = prompt.lower()
        matched_sheets = []

        for keyword, sheet in self.rules.items():
            if keyword in p_lower and sheet not in matched_sheets:
                matched_sheets.append(sheet)

        if matched_sheets:
            return [{"sheet": s, "score": 0.99 - (i * 0.05)} for i, s in enumerate(matched_sheets[:top_k])]

        return None  # Triggers graceful fallback to OpenYantra's internal centroid router


def main():
    print("\n🔌 OpenYantra External Router Integration Example")
    oy = OpenYantra("~/openyantra/chitrapat.ods")

    # 1. Instantiate the external router
    plexus = MockPlexusRouter()

    # 2. Hook into OpenYantra's VidyaKosha routing pipeline
    oy.set_external_router(plexus.route)
    print("  ✓ External router successfully attached to VidyaKosha hook.")

    # 3. Test routing through the external engine
    test_prompt = "Deploy the Kubernetes cluster to AWS"
    routes = oy.route(test_prompt, top_k=2)
    print(f"\n  Prompt: '{test_prompt}'")
    print(f"  Routed to: {[r['sheet'] for r in routes]} (Score: {routes[0]['score']:.2f})")

    # 4. Test fallback on unmatched prompt
    unmatched_prompt = "Random conversational question about yesterday"
    fallback_routes = oy.route(unmatched_prompt, top_k=2)
    print(f"\n  Prompt: '{unmatched_prompt}'")
    print(f"  Fallback internal router selected: {[r['sheet'] for r in fallback_routes] if fallback_routes else 'None (Clean Prune)'}")

    # 5. Cleanly detach external router
    oy.set_external_router(None)
    print("\n  ✓ Detached external router. Returned to default centroid subspace router.\n")


if __name__ == "__main__":
    main()
