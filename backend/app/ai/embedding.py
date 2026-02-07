from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import numpy as np


@dataclass
class Embedder:
    model_name: str
    _model: object

    def encode(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        # SentenceTransformer returns np.ndarray (float32/float64 depending on backend).
        return self._model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            normalize_embeddings=False,
        )


def load_embedder(model_name: str) -> Embedder:
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(model_name)
    return Embedder(model_name=model_name, _model=model)


class OptionalReranker:
    def __init__(self, model_name: str):
        self.model_name = model_name
        self._model = None

    def available(self) -> bool:
        return True

    def load(self) -> None:
        if self._model is not None:
            return
        from sentence_transformers import CrossEncoder

        self._model = CrossEncoder(self.model_name)

    def rerank(self, query: str, docs: List[str]) -> Optional[List[float]]:
        if not docs:
            return []
        self.load()
        pairs = [(query, d) for d in docs]
        scores = self._model.predict(pairs)  # higher is better
        return [float(s) for s in scores]
