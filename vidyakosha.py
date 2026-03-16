"""
vidyakosha.py — VidyaKosha (विद्याकोश — Knowledge Repository)
OpenYantra v1.1 — Sidecar Semantic Index

The VidyaKosha sits beside the Chitrapat and enables agents to query
memory by meaning, not just keyword matching.

Architecture:
    chitrapat.ods  ←  source of truth (Chitragupta writes)
          │
          │ sync on every Chitragupta commit
          ▼
    VidyaKosha
    ├── faiss.index       ← vector index (one embedding per row)
    ├── bm25.pkl          ← BM25 keyword index
    ├── manifest.json     ← row registry + change detection
    └── pratibimba/       ← per-agent frozen snapshots (Pratibimba)
          ├── Claude.snapshot
          └── AutoGen.snapshot

Embedding backends (pluggable):
    1. sentence-transformers/all-MiniLM-L6-v2  (best — install separately)
    2. TF-IDF via scikit-learn                 (built-in fallback, zero extra deps)

Usage:
    from vidyakosha import VidyaKosha

    vk = VidyaKosha("~/openyantra/")
    vk.sync("chitrapat.ods")          # rebuild index from Chitrapat

    results = vk.query(
        "screenplay structure conflict",
        agent_name="Claude",
        top_k=5
    )
    for r in results:
        print(r["sheet"], r["text"], r["score"])
"""

from __future__ import annotations

import hashlib
import json
import pickle
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional

import faiss
import numpy as np
import pandas as pd

# ── Embedding backends ────────────────────────────────────────────────────────

class TFIDFEmbedder:
    """
    Pure scikit-learn TF-IDF + SVD embedder. Zero extra dependencies.
    Dimension auto-sized to min(384, n_features) to avoid corpus-size errors.
    """
    TARGET_DIM = 384

    def __init__(self):
        from sklearn.feature_extraction.text import TfidfVectorizer
        self._tfidf   = TfidfVectorizer(
            max_features=8000,
            ngram_range=(1, 2),
            sublinear_tf=True,
            strip_accents="unicode",
        )
        self._svd     = None
        self._dim     = self.TARGET_DIM
        self._fitted  = False
        self._corpus  = []
        self._lock    = threading.Lock()

    def fit(self, texts: list[str]):
        from sklearn.decomposition import TruncatedSVD
        with self._lock:
            self._corpus = [t for t in texts if t and t.strip()]
            if not self._corpus:
                return
            tfidf_mat = self._tfidf.fit_transform(self._corpus)
            # Auto-size SVD dim to avoid n_components > n_features error
            n_feat = tfidf_mat.shape[1]
            self._dim = min(self.TARGET_DIM, n_feat - 1, len(self._corpus) - 1)
            self._dim = max(self._dim, 2)
            self._svd = TruncatedSVD(n_components=self._dim, random_state=42)
            self._svd.fit(tfidf_mat)
            self._fitted = True

    def encode(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self._dim), dtype=np.float32)
        if not self._fitted:
            self.fit(texts)
        tfidf_mat = self._tfidf.transform(texts)
        vecs = self._svd.transform(tfidf_mat).astype(np.float32)
        norms = np.linalg.norm(vecs, axis=1, keepdims=True)
        norms[norms == 0] = 1
        return vecs / norms

    @property
    def dim(self): return self._dim


class SentenceTransformerEmbedder:
    """
    sentence-transformers/all-MiniLM-L6-v2 embedder.
    Install: pip install sentence-transformers
    Falls back gracefully to TFIDFEmbedder if not available.
    """
    DIM = 384

    def __init__(self):
        from sentence_transformers import SentenceTransformer
        self._model = SentenceTransformer("all-MiniLM-L6-v2")

    def fit(self, texts: list[str]):
        pass  # no fitting needed

    def encode(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.DIM), dtype=np.float32)
        vecs = self._model.encode(texts, show_progress_bar=False,
                                  normalize_embeddings=True)
        return vecs.astype(np.float32)

    @property
    def dim(self): return self.DIM


def get_embedder(prefer: str = "auto") -> TFIDFEmbedder | SentenceTransformerEmbedder:
    """
    Return the best available embedder.
    prefer="sentence-transformers" forces ST if available.
    prefer="tfidf" forces TF-IDF.
    prefer="auto" tries ST first, falls back to TF-IDF.
    """
    if prefer == "tfidf":
        return TFIDFEmbedder()
    try:
        embedder = SentenceTransformerEmbedder()
        print("[VidyaKosha] Using sentence-transformers/all-MiniLM-L6-v2")
        return embedder
    except ImportError:
        if prefer == "sentence-transformers":
            raise ImportError(
                "sentence-transformers not installed. "
                "Run: pip install sentence-transformers"
            )
        print("[VidyaKosha] sentence-transformers not found — using TF-IDF embedder")
        print("[VidyaKosha] For better results: pip install sentence-transformers")
        return TFIDFEmbedder()


# ── BM25 (keyword search) ─────────────────────────────────────────────────────

class BM25Index:
    """
    Pure Python BM25 implementation. No extra dependencies.
    Complements vector search for exact/partial keyword matches.
    """
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b  = b
        self._docs:   list[list[str]] = []
        self._idf:    dict[str, float] = {}
        self._avgdl:  float = 0.0

    def fit(self, corpus: list[str]):
        import math
        self._docs = [doc.lower().split() for doc in corpus]
        N = len(self._docs)
        self._avgdl = sum(len(d) for d in self._docs) / max(N, 1)
        df: dict[str, int] = {}
        for doc in self._docs:
            for term in set(doc):
                df[term] = df.get(term, 0) + 1
        self._idf = {
            term: math.log((N - freq + 0.5) / (freq + 0.5) + 1)
            for term, freq in df.items()
        }

    def score(self, query: str, doc_idx: int) -> float:
        terms = query.lower().split()
        doc   = self._docs[doc_idx]
        dl    = len(doc)
        score = 0.0
        tf_map: dict[str, int] = {}
        for t in doc:
            tf_map[t] = tf_map.get(t, 0) + 1
        for term in terms:
            if term not in self._idf:
                continue
            tf  = tf_map.get(term, 0)
            idf = self._idf[term]
            num = tf * (self.k1 + 1)
            den = tf + self.k1 * (1 - self.b + self.b * dl / max(self._avgdl, 1))
            score += idf * num / den
        return score

    def query(self, text: str, top_k: int = 10) -> list[tuple[int, float]]:
        scores = [(i, self.score(text, i)) for i in range(len(self._docs))]
        scores.sort(key=lambda x: -x[1])
        return [(i, s) for i, s in scores[:top_k] if s > 0]


# ── Row registry ──────────────────────────────────────────────────────────────

def _row_to_text(sheet: str, row: dict) -> str:
    """Convert a sheet row into a searchable text string."""
    parts = [f"[{sheet}]"]
    for k, v in row.items():
        if v and str(v).strip() and k not in ("Confidence", "Source", "Last Updated",
                                               "Signature", "Mudra", "Samay"):
            parts.append(f"{k}: {v}")
    return " ".join(parts)


def _row_id(sheet: str, row: dict) -> str:
    """Stable ID for a row — used for change detection."""
    primary = str(list(row.values())[0]) if row else ""
    payload = f"{sheet}::{primary}"
    return hashlib.md5(payload.encode()).hexdigest()[:16]


# ══════════════════════════════════════════════════════════════════════════════
# VidyaKosha — the sidecar index
# ══════════════════════════════════════════════════════════════════════════════

INDEXABLE_SHEETS = [
    "👤 Identity", "🎯 Goals", "🚀 Projects", "👥 People",
    "💡 Preferences", "🧠 Beliefs", "✅ Tasks", "🔓 Open Loops",
]

SNAPSHOT_MODES = {"per-session", "live", "none"}


class VidyaKosha:
    """
    VidyaKosha (विद्याकोश) — Knowledge Repository
    Sidecar semantic index for OpenYantra.

    Sits beside the Chitrapat. Rebuilt automatically when Chitragupta
    commits new writes. Queried by any agent for semantic search.

    Usage:
        vk = VidyaKosha("~/openyantra/")
        vk.sync("~/openyantra/chitrapat.ods")

        results = vk.query("screenplay structure", agent_name="Claude", top_k=5)
        for r in results:
            print(r["sheet"], r["primary_value"], f"score={r['score']:.3f}")

    Multi-agent snapshot modes (set per-agent in ⚙️ Agent Config sheet):
        per-session  → each agent gets a frozen snapshot at session start
        live         → all agents share one real-time index
        none         → agent does not use VidyaKosha
    """

    def __init__(self, yantra_dir: str | Path, embedder_pref: str = "auto"):
        self.dir      = Path(yantra_dir).expanduser()
        self.dir.mkdir(parents=True, exist_ok=True)

        self._embedder   = get_embedder(embedder_pref)
        self._lock       = threading.RLock()

        # Paths
        self._faiss_path    = self.dir / "vidyakosha.faiss"
        self._bm25_path     = self.dir / "vidyakosha_bm25.pkl"
        self._manifest_path = self.dir / "vidyakosha_manifest.json"
        self._snapshot_dir  = self.dir / "pratibimba"
        self._snapshot_dir.mkdir(exist_ok=True)

        # In-memory state
        self._index:    Optional[faiss.IndexFlatIP] = None
        self._bm25:     Optional[BM25Index]          = None
        self._registry: list[dict]                   = []  # row metadata

        self._load()

    # ── Public API ─────────────────────────────────────────────────────────────

    def sync(self, chitrapat_path: str | Path) -> int:
        """
        Rebuild the index from the Chitrapat.
        Called automatically after each Chitragupta commit.
        Returns number of rows indexed.
        """
        path = Path(chitrapat_path).expanduser()
        if not path.exists():
            print(f"[VidyaKosha] Chitrapat not found at {path}")
            return 0

        with self._lock:
            rows, texts, registry = [], [], []

            for sheet in INDEXABLE_SHEETS:
                try:
                    df = pd.read_excel(str(path), sheet_name=sheet,
                                       engine="odf", header=0, dtype=str)
                    df = df.where(pd.notna(df), None)
                    for _, row in df.iterrows():
                        rec = row.to_dict()
                        if not any(v for v in rec.values() if v and str(v).strip()):
                            continue
                        text = _row_to_text(sheet, rec)
                        rid  = _row_id(sheet, rec)
                        primary = str(list(rec.values())[0]) if rec else ""
                        meta = {
                            "id":            rid,
                            "sheet":         sheet,
                            "primary_value": primary,
                            "text":          text,
                            "row":           rec,
                            "indexed_at":    datetime.utcnow().isoformat(),
                        }
                        rows.append(meta)
                        texts.append(text)
                        registry.append(meta)
                except Exception:
                    pass  # Sheet may not exist yet

            if not texts:
                print("[VidyaKosha] No rows to index")
                return 0

            # Build embedder corpus for TF-IDF (sentence-transformers ignores this)
            if isinstance(self._embedder, TFIDFEmbedder):
                self._embedder.fit(texts)

            # Build FAISS index
            vecs = self._embedder.encode(texts)
            dim  = self._embedder.dim
            self._index = faiss.IndexFlatIP(dim)
            self._index.add(vecs)

            # Build BM25
            self._bm25 = BM25Index()
            self._bm25.fit(texts)

            self._registry = registry
            self._save()

            print(f"[VidyaKosha] Synced — {len(texts)} rows indexed across "
                  f"{len(INDEXABLE_SHEETS)} sheets")
            return len(texts)

    def query(
        self,
        text: str,
        agent_name: str = "agent",
        top_k: int = 5,
        sheets: Optional[list[str]] = None,
        snapshot_mode: str = "live",
        hybrid_alpha: float = 0.7,
    ) -> list[dict]:
        """
        Hybrid semantic + keyword search across the Chitrapat.

        Args:
            text:           Natural language query
            agent_name:     Name of the requesting agent
            top_k:          Number of results to return
            sheets:         Filter to specific sheets (None = all)
            snapshot_mode:  "live" | "per-session" | configurable
            hybrid_alpha:   Weight for vector score vs BM25 (0=BM25 only, 1=vector only)

        Returns:
            List of result dicts sorted by hybrid score:
            [{sheet, primary_value, text, score, vector_score, bm25_score, row}, ...]
        """
        registry = self._get_registry(agent_name, snapshot_mode)
        if not registry or self._index is None:
            return []

        # Filter by sheet if requested
        indices = list(range(len(registry)))
        if sheets:
            indices = [i for i, r in enumerate(registry) if r["sheet"] in sheets]
        if not indices:
            return []

        # Vector search
        query_vec = self._embedder.encode([text])
        if isinstance(self._embedder, TFIDFEmbedder) and not self._embedder._fitted:
            return []

        # Search full index then filter
        k_search = min(len(registry), top_k * 4)
        D, I = self._index.search(query_vec, k_search)
        vec_hits: dict[int, float] = {int(idx): float(score)
                                       for idx, score in zip(I[0], D[0])
                                       if idx in indices and score > 0}

        # BM25 search
        bm25_hits: dict[int, float] = {}
        if self._bm25:
            for idx, score in self._bm25.query(text, top_k=k_search):
                if idx in indices:
                    bm25_hits[idx] = score

        # Normalise scores to [0, 1]
        def normalise(scores: dict[int, float]) -> dict[int, float]:
            if not scores: return {}
            mx = max(scores.values())
            return {k: v/mx for k, v in scores.items()} if mx > 0 else scores

        vec_norm  = normalise(vec_hits)
        bm25_norm = normalise(bm25_hits)

        # Hybrid score
        all_idx = set(vec_norm) | set(bm25_norm)
        hybrid: list[tuple[int, float, float, float]] = []
        for idx in all_idx:
            vs = vec_norm.get(idx, 0.0)
            bs = bm25_norm.get(idx, 0.0)
            hs = hybrid_alpha * vs + (1 - hybrid_alpha) * bs
            hybrid.append((idx, hs, vs, bs))

        hybrid.sort(key=lambda x: -x[1])

        results = []
        for idx, hs, vs, bs in hybrid[:top_k]:
            if idx >= len(registry):
                continue
            rec = registry[idx].copy()
            rec["score"]        = round(hs, 4)
            rec["vector_score"] = round(vs, 4)
            rec["bm25_score"]   = round(bs, 4)
            results.append(rec)

        return results

    def take_snapshot(self, agent_name: str):
        """
        Pratibimba — take a frozen snapshot of the current index for this agent.
        Called at session start when snapshot_mode = "per-session".
        """
        with self._lock:
            snap_path = self._snapshot_dir / f"{agent_name}.snapshot"
            snapshot  = {
                "agent":      agent_name,
                "taken_at":   datetime.utcnow().isoformat(),
                "registry":   self._registry,
            }
            snap_path.write_text(json.dumps(snapshot, indent=2, default=str))
            print(f"[VidyaKosha] Pratibimba taken for {agent_name} "
                  f"({len(self._registry)} rows)")

    def release_snapshot(self, agent_name: str):
        """Release a Pratibimba snapshot after the agent's session ends."""
        snap_path = self._snapshot_dir / f"{agent_name}.snapshot"
        if snap_path.exists():
            snap_path.unlink()
            print(f"[VidyaKosha] Pratibimba released for {agent_name}")

    def explain(self, query: str, result: dict) -> str:
        """
        Return a human-readable explanation of why a result was returned.
        Useful for debugging and agent transparency.
        """
        lines = [
            f"Query:        '{query}'",
            f"Sheet:        {result['sheet']}",
            f"Row:          {result['primary_value']}",
            f"Hybrid score: {result['score']:.4f}  "
            f"(vector={result['vector_score']:.4f}, bm25={result['bm25_score']:.4f})",
            f"Indexed text: {result['text'][:120]}...",
        ]
        return "\n".join(lines)

    def stats(self) -> dict:
        """Return index statistics."""
        return {
            "total_rows":       len(self._registry),
            "sheets_indexed":   list({r["sheet"] for r in self._registry}),
            "embedder":         type(self._embedder).__name__,
            "embedding_dim":    self._embedder.dim,
            "faiss_index":      str(self._faiss_path) if self._faiss_path.exists() else None,
            "snapshots":        [p.stem for p in self._snapshot_dir.glob("*.snapshot")],
        }

    # ── Internal ───────────────────────────────────────────────────────────────

    def _get_registry(self, agent_name: str, snapshot_mode: str) -> list[dict]:
        """Return the appropriate registry for this agent."""
        if snapshot_mode == "per-session":
            snap_path = self._snapshot_dir / f"{agent_name}.snapshot"
            if snap_path.exists():
                try:
                    data = json.loads(snap_path.read_text())
                    return data.get("registry", self._registry)
                except Exception:
                    pass
        return self._registry

    def _save(self):
        """Persist index to disk."""
        if self._index is not None:
            faiss.write_index(self._index, str(self._faiss_path))
        if self._bm25 is not None:
            with open(self._bm25_path, "wb") as f:
                pickle.dump(self._bm25, f)
        manifest = {
            "rows":       len(self._registry),
            "updated_at": datetime.utcnow().isoformat(),
            "embedder":   type(self._embedder).__name__,
        }
        self._manifest_path.write_text(json.dumps(manifest, indent=2))
        # Save registry separately (large)
        reg_path = self.dir / "vidyakosha_registry.json"
        reg_path.write_text(json.dumps(self._registry, indent=2, default=str))

    def _load(self):
        """Load existing index from disk if available."""
        try:
            if self._faiss_path.exists():
                self._index = faiss.read_index(str(self._faiss_path))
            if self._bm25_path.exists():
                with open(self._bm25_path, "rb") as f:
                    self._bm25 = pickle.load(f)
            reg_path = self.dir / "vidyakosha_registry.json"
            if reg_path.exists():
                self._registry = json.loads(reg_path.read_text())
                print(f"[VidyaKosha] Loaded existing index — "
                      f"{len(self._registry)} rows")
        except Exception as e:
            print(f"[VidyaKosha] Could not load existing index: {e}")


# ── OpenYantra integration hook ───────────────────────────────────────────────

def get_snapshot_mode(agent_name: str, chitrapat_path: str | Path) -> str:
    """
    Read the snapshot mode for this agent from ⚙️ Agent Config sheet.
    Default: "live"
    """
    try:
        df = pd.read_excel(str(chitrapat_path), sheet_name="⚙️ Agent Config",
                           engine="odf", header=0, dtype=str)
        for _, row in df.iterrows():
            if row.get("Agent") in (agent_name, "ALL"):
                instr = str(row.get("Instruction", "")).lower()
                if "per-session" in instr or "snapshot" in instr:
                    return "per-session"
                if "live" in instr:
                    return "live"
    except Exception:
        pass
    return "live"
