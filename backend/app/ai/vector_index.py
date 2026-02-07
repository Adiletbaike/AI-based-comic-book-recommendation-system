import json
import os
import time
from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np


def _try_import_faiss():
    try:
        import faiss  # type: ignore

        return faiss
    except Exception:
        return None


@dataclass
class IndexMeta:
    embedding_model: str
    catalog_mtime: float
    built_at: float
    dim: int
    count: int

    def to_dict(self) -> dict:
        return {
            "embedding_model": self.embedding_model,
            "catalog_mtime": self.catalog_mtime,
            "built_at": self.built_at,
            "dim": self.dim,
            "count": self.count,
        }

    @staticmethod
    def from_dict(d: dict) -> "IndexMeta":
        return IndexMeta(
            embedding_model=str(d.get("embedding_model") or ""),
            catalog_mtime=float(d.get("catalog_mtime") or 0),
            built_at=float(d.get("built_at") or 0),
            dim=int(d.get("dim") or 0),
            count=int(d.get("count") or 0),
        )


def _read_meta(meta_path: str) -> Optional[IndexMeta]:
    try:
        with open(meta_path, "r", encoding="utf-8") as f:
            return IndexMeta.from_dict(json.load(f))
    except Exception:
        return None


def _write_meta(meta_path: str, meta: IndexMeta) -> None:
    tmp = meta_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(meta.to_dict(), f)
    os.replace(tmp, meta_path)


def _l2_normalize(x: np.ndarray) -> np.ndarray:
    denom = np.linalg.norm(x, axis=1, keepdims=True) + 1e-12
    return x / denom


class VectorIndex:
    def __init__(self, faiss_index_path: str, embeddings_path: str, meta_path: str):
        self.faiss_index_path = faiss_index_path
        self.embeddings_path = embeddings_path
        self.meta_path = meta_path

        self._faiss = _try_import_faiss()
        self._index = None
        self._embeddings = None

    def is_available(self) -> bool:
        return self._faiss is not None

    def load(self) -> None:
        if not os.path.exists(self.embeddings_path):
            raise FileNotFoundError(self.embeddings_path)
        self._embeddings = np.load(self.embeddings_path)

        if self._faiss and os.path.exists(self.faiss_index_path):
            self._index = self._faiss.read_index(self.faiss_index_path)
        else:
            self._index = None

    def build(self, embeddings: np.ndarray, embedding_model: str, catalog_path: str) -> None:
        os.makedirs(os.path.dirname(self.embeddings_path), exist_ok=True)
        emb = np.asarray(embeddings, dtype=np.float32)
        emb = _l2_normalize(emb)
        np.save(self.embeddings_path, emb)

        if self._faiss:
            dim = emb.shape[1]
            index = self._faiss.IndexFlatIP(dim)
            index.add(emb)
            self._faiss.write_index(index, self.faiss_index_path)
            self._index = index
        else:
            self._index = None

        meta = IndexMeta(
            embedding_model=embedding_model,
            catalog_mtime=os.path.getmtime(catalog_path) if os.path.exists(catalog_path) else 0,
            built_at=time.time(),
            dim=int(emb.shape[1]),
            count=int(emb.shape[0]),
        )
        _write_meta(self.meta_path, meta)
        self._embeddings = emb

    def is_stale(self, embedding_model: str, catalog_path: str) -> bool:
        meta = _read_meta(self.meta_path)
        if not meta:
            return True
        if meta.embedding_model != embedding_model:
            return True
        if not os.path.exists(catalog_path):
            return True
        if meta.catalog_mtime != os.path.getmtime(catalog_path):
            return True
        if not os.path.exists(self.embeddings_path):
            return True
        if self._faiss and not os.path.exists(self.faiss_index_path):
            return True
        return False

    def search(self, query_vec: np.ndarray, top_k: int = 50) -> Tuple[np.ndarray, np.ndarray]:
        """
        Returns (indices, scores). Indices are row offsets into the embeddings array.
        """
        if self._embeddings is None:
            self.load()

        q = np.asarray(query_vec, dtype=np.float32).reshape(1, -1)
        q = _l2_normalize(q)

        if self._faiss and self._index is not None:
            scores, idx = self._index.search(q, top_k)
            return idx[0], scores[0]

        # Fallback: brute-force cosine via dot product (already normalized).
        scores = (self._embeddings @ q.T).reshape(-1)
        top = np.argsort(scores)[-top_k:][::-1]
        return top, scores[top]

    def get_embeddings(self) -> np.ndarray:
        if self._embeddings is None:
            self.load()
        return self._embeddings

