from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np

from ..models.comic import Comic
from ..models.interaction import UserComic
from .. import db

from .catalog import CatalogPaths, build_source_id_map, best_effort_match_row_id, load_catalog
from .embedding import OptionalReranker, load_embedder
from .query import parse_query
from .vector_index import VectorIndex


@dataclass
class RecommenderConfig:
    catalog_path: str
    index_dir: str
    embedding_model: str
    enable_reranker: bool
    rerank_model: str
    prompt_weight: float
    profile_weight: float
    cf_weight: float = 0.0


class ComicRecommender:
    """
    2026-style recommender:
      - bi-encoder embeddings + ANN (FAISS) for fast retrieval
      - optional cross-encoder reranker (FlagEmbedding bge reranker family)
      - personalization via user profile embedding from implicit library interactions
    """

    def __init__(self, cfg: RecommenderConfig):
        self.cfg = cfg
        self.paths = CatalogPaths(catalog_csv=cfg.catalog_path, index_dir=cfg.index_dir)

        self.comics_df = load_catalog(self.paths.catalog_csv)
        self._source_id_to_row_id = build_source_id_map(self.comics_df)

        self.embedder = load_embedder(cfg.embedding_model)
        self.index = VectorIndex(
            faiss_index_path=self.paths.faiss_index,
            embeddings_path=self.paths.embeddings_npy,
            meta_path=self.paths.meta_json,
        )

        self.reranker = OptionalReranker(cfg.rerank_model)
        self._ensure_index()

        self._cf_cache = None  # built lazily

    def _ensure_index(self) -> None:
        if self.comics_df.empty:
            return
        if self.index.is_stale(self.embedder.model_name, self.paths.catalog_csv):
            texts = self.comics_df["search_text"].fillna("").astype(str).tolist()
            emb = self.embedder.encode(texts, batch_size=32)
            self.index.build(embeddings=emb, embedding_model=self.embedder.model_name, catalog_path=self.paths.catalog_csv)
        else:
            try:
                self.index.load()
            except Exception:
                texts = self.comics_df["search_text"].fillna("").astype(str).tolist()
                emb = self.embedder.encode(texts, batch_size=32)
                self.index.build(embeddings=emb, embedding_model=self.embedder.model_name, catalog_path=self.paths.catalog_csv)

    def process_prompt(self, user_prompt: str, user_id: Optional[int] = None) -> Dict:
        q = parse_query(user_prompt)
        recs, explanation = self.recommend(prompt=q.raw, user_id=user_id)
        return {
            "keywords": q.keywords,
            "recommendations": recs[:10],
            "explanation": explanation,
        }

    def recommend(self, prompt: str, user_id: Optional[int]) -> Tuple[List[Dict], str]:
        if self.comics_df.empty:
            return [], "Catalog is empty."

        prompt = (prompt or "").strip()
        if not prompt:
            # Personalized feed without prompt.
            recs = self._personalized_only(user_id=user_id, top_k=10)
            if recs:
                return recs, "Recommendations based on your library."
            return self.comics_df.head(10).to_dict("records"), "Popular picks from the catalog."

        prompt_vec = self.embedder.encode([prompt], batch_size=1)
        idx, scores = self.index.search(prompt_vec[0], top_k=200)

        # Optional personalization blend
        blended = None
        if user_id is not None and self.cfg.profile_weight > 0:
            prof = self._user_profile_embedding(user_id)
            if prof is not None:
                pidx, pscores = self.index.search(prof, top_k=200)
                blended = self._blend_results(
                    (idx, scores),
                    (pidx, pscores),
                    w_prompt=self.cfg.prompt_weight,
                    w_profile=self.cfg.profile_weight,
                    top_k=100,
                )

        # Optional collaborative filtering blend (implicit ALS)
        if user_id is not None and self.cfg.cf_weight > 0:
            cf = self._cf_recommend(user_id=user_id, top_k=200)
            if cf is not None:
                cidx, cscores = cf
                base_idx, base_scores = blended if blended is not None else (idx, scores)
                blended = self._blend_3way(
                    (base_idx, base_scores),
                    (cidx, cscores),
                    w_base=(self.cfg.prompt_weight + self.cfg.profile_weight),
                    w_cf=self.cfg.cf_weight,
                    top_k=100,
                )

        final_idx, final_scores = blended if blended is not None else (idx, scores)
        candidates = self._rows_to_records(final_idx, final_scores)

        # Optional reranking (slow but more accurate ordering)
        if self.cfg.enable_reranker:
            candidates = self._rerank(prompt, candidates, top_n=50)

        explanation = "Recommendations based on your prompt."
        if user_id is not None and blended is not None:
            if self.cfg.cf_weight > 0:
                explanation = "Recommendations based on your prompt, your library, and community patterns."
            else:
                explanation = "Recommendations based on your prompt and your library."
        return candidates[:10], explanation

    def _rows_to_records(self, row_ids: np.ndarray, scores: np.ndarray) -> List[Dict]:
        out = []
        for rid, sc in zip(row_ids.tolist(), scores.tolist()):
            if rid < 0:
                continue
            try:
                r = self.comics_df.iloc[int(rid)].to_dict()
                r["score"] = float(sc)
                out.append(r)
            except Exception:
                continue
        return out

    def _rerank(self, prompt: str, candidates: List[Dict], top_n: int) -> List[Dict]:
        if not candidates:
            return candidates
        docs = []
        keep = candidates[:top_n]
        for c in keep:
            docs.append(str(c.get("search_text") or c.get("title") or ""))
        scores = self.reranker.rerank(prompt, docs)
        if scores is None:
            return candidates
        reranked = list(zip(keep, scores))
        reranked.sort(key=lambda x: x[1], reverse=True)
        keep2 = []
        for c, s in reranked:
            c2 = dict(c)
            c2["rerank_score"] = float(s)
            keep2.append(c2)
        return keep2 + candidates[top_n:]

    def _blend_results(
        self,
        a: Tuple[np.ndarray, np.ndarray],
        b: Tuple[np.ndarray, np.ndarray],
        w_prompt: float,
        w_profile: float,
        top_k: int,
    ) -> Tuple[np.ndarray, np.ndarray]:
        idx_a, sc_a = a
        idx_b, sc_b = b

        score_map = {}
        for i, s in zip(idx_a.tolist(), sc_a.tolist()):
            if i < 0:
                continue
            score_map[int(i)] = score_map.get(int(i), 0.0) + w_prompt * float(s)
        for i, s in zip(idx_b.tolist(), sc_b.tolist()):
            if i < 0:
                continue
            score_map[int(i)] = score_map.get(int(i), 0.0) + w_profile * float(s)

        items = sorted(score_map.items(), key=lambda x: x[1], reverse=True)[:top_k]
        idx = np.array([i for i, _ in items], dtype=np.int64)
        sc = np.array([s for _, s in items], dtype=np.float32)
        return idx, sc

    def _blend_3way(
        self,
        base: Tuple[np.ndarray, np.ndarray],
        cf: Tuple[np.ndarray, np.ndarray],
        w_base: float,
        w_cf: float,
        top_k: int,
    ) -> Tuple[np.ndarray, np.ndarray]:
        idx_a, sc_a = base
        idx_b, sc_b = cf

        score_map = {}
        for i, s in zip(idx_a.tolist(), sc_a.tolist()):
            if i < 0:
                continue
            score_map[int(i)] = score_map.get(int(i), 0.0) + w_base * float(s)
        for i, s in zip(idx_b.tolist(), sc_b.tolist()):
            if i < 0:
                continue
            score_map[int(i)] = score_map.get(int(i), 0.0) + w_cf * float(s)

        items = sorted(score_map.items(), key=lambda x: x[1], reverse=True)[:top_k]
        idx = np.array([i for i, _ in items], dtype=np.int64)
        sc = np.array([s for _, s in items], dtype=np.float32)
        return idx, sc

    def _personalized_only(self, user_id: Optional[int], top_k: int) -> List[Dict]:
        if user_id is None:
            return []
        prof = self._user_profile_embedding(user_id)
        if prof is None:
            return []
        idx, scores = self.index.search(prof, top_k=top_k)
        return self._rows_to_records(idx, scores)[:top_k]

    def _user_profile_embedding(self, user_id: int) -> Optional[np.ndarray]:
        # Create an embedding from user's implicit interactions.
        # We map DB comics back to catalog rows using Comic.source_id when available,
        # otherwise fall back to title+author matching.
        weights = {
            "favorite": 2.0,
            "completed": 1.5,
            "reading": 1.0,
            "trash": -1.0,
        }

        rows = (
            db.session.query(UserComic.status, Comic.source_id, Comic.title, Comic.author)
            .join(Comic, Comic.id == UserComic.comic_id)
            .filter(UserComic.user_id == user_id)
            .all()
        )
        if not rows:
            return None

        emb = self.index.get_embeddings()
        vecs = []
        ws = []
        for status, source_id, title, author in rows:
            w = float(weights.get(status, 0.0))
            if w == 0.0:
                continue

            rid = None
            if source_id:
                rid = self._source_id_to_row_id.get(str(source_id))
            if rid is None:
                rid = best_effort_match_row_id(self.comics_df, title=title, author=author)
            if rid is None:
                continue

            try:
                vecs.append(emb[int(rid)])
                ws.append(w)
            except Exception:
                continue

        if not vecs:
            return None

        v = np.vstack(vecs).astype(np.float32)
        w = np.array(ws, dtype=np.float32).reshape(-1, 1)
        prof = (v * w).sum(axis=0) / (np.abs(w).sum() + 1e-6)
        return prof.astype(np.float32)

    def _cf_recommend(self, user_id: int, top_k: int) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        try:
            cache = self._get_or_build_cf()
            if cache is None:
                return None
            col = cache["user_id_to_col"].get(int(user_id))
            if col is None:
                return None
            model = cache["model"]
            user_items = cache["user_items"]

            ids, scores = model.recommend(
                col,
                user_items,
                N=top_k,
                filter_already_liked_items=True,
            )
            return np.asarray(ids, dtype=np.int64), np.asarray(scores, dtype=np.float32)
        except Exception:
            return None

    def _get_or_build_cf(self):
        # Build once per process (small apps). Rebuild if interactions change.
        import time

        # Only useful if you have multiple users/interactions.
        count = db.session.query(UserComic.id).count()
        if count < 20:
            return None

        last_ts = db.session.query(db.func.max(UserComic.updated_at)).scalar()
        last_ts_val = float(last_ts.timestamp()) if last_ts is not None else 0.0

        if self._cf_cache and self._cf_cache.get("last_ts") == last_ts_val:
            # cache fresh for 10 minutes
            if time.time() - self._cf_cache.get("built_at", 0) < 600:
                return self._cf_cache

        try:
            import scipy.sparse  # type: ignore
            import implicit  # type: ignore
        except Exception:
            return None

        users = db.session.query(Comic.id, UserComic.user_id, UserComic.status, Comic.source_id, Comic.title, Comic.author).join(
            UserComic, UserComic.comic_id == Comic.id
        ).all()
        if not users:
            return None

        # Map user ids to dense columns
        user_ids = sorted({int(r[1]) for r in users if r[1] is not None})
        if len(user_ids) < 2:
            return None
        user_id_to_col = {uid: i for i, uid in enumerate(user_ids)}

        n_items = int(len(self.comics_df))
        n_users = int(len(user_ids))

        weights = {
            "favorite": 3.0,
            "completed": 2.0,
            "reading": 1.0,
            "trash": -1.0,
        }

        rows = []
        cols = []
        data = []

        for _, uid, status, source_id, title, author in users:
            w = float(weights.get(status, 0.0))
            if w <= 0:
                continue
            rid = None
            if source_id:
                rid = self._source_id_to_row_id.get(str(source_id))
            if rid is None:
                rid = best_effort_match_row_id(self.comics_df, title=title, author=author)
            if rid is None:
                continue
            rows.append(int(rid))
            cols.append(int(user_id_to_col[int(uid)]))
            data.append(w)

        if len(data) < 20:
            return None

        item_user = scipy.sparse.coo_matrix((data, (rows, cols)), shape=(n_items, n_users)).tocsr()
        user_item = item_user.T.tocsr()

        model = implicit.als.AlternatingLeastSquares(
            factors=64,
            regularization=0.01,
            iterations=15,
        )
        model.fit(item_user)

        self._cf_cache = {
            "model": model,
            "user_id_to_col": user_id_to_col,
            "user_items": user_item,
            "built_at": time.time(),
            "last_ts": last_ts_val,
        }
        return self._cf_cache
