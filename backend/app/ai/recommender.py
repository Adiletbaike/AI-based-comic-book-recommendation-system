from typing import Dict, List

import os
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from .nlp_processor import analyze_sentiment, extract_keywords


class ComicRecommender:
    def __init__(self, dataset_path: str, embeddings_path: str):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.dataset_path = dataset_path
        self.embeddings_path = embeddings_path
        if dataset_path and os.path.exists(dataset_path):
            self.comics_df = pd.read_csv(dataset_path)
        else:
            self.comics_df = pd.DataFrame()

        if not self.comics_df.empty:
            self._normalize_columns()

        self.comic_embeddings = self._load_or_build_embeddings()

    def process_prompt(self, user_prompt: str) -> Dict:
        keywords = extract_keywords(user_prompt)
        sentiment = analyze_sentiment(user_prompt)

        content_recs = self.content_based_recommendation(keywords)
        final_recs = self.hybrid_recommendation(content_recs, sentiment)

        return {
            "keywords": keywords,
            "recommendations": final_recs[:10],
            "explanation": self.generate_explanation(keywords, final_recs),
        }

    def _normalize_columns(self) -> None:
        df = self.comics_df

        if "cover_image" not in df.columns and "cover_url" in df.columns:
            df["cover_image"] = df["cover_url"]

        if "description" not in df.columns and "summary" in df.columns:
            df["description"] = df["summary"]

        if "genre" not in df.columns and "genres" in df.columns:
            df["genre"] = df["genres"]

        if "author" not in df.columns and "authors" in df.columns:
            df["author"] = df["authors"]

        if "title" not in df.columns and "name" in df.columns:
            df["title"] = df["name"]

        if "tags" not in df.columns:
            df["tags"] = df.get("genre", "")

        df["tags"] = df["tags"].fillna("").apply(
            lambda x: [t.strip().lower() for t in str(x).split(",") if t.strip()]
        )

        df["genre"] = df.get("genre", "").fillna("")
        df["title"] = df.get("title", "").fillna("")
        df["author"] = df.get("author", "").fillna("")
        df["series"] = df.get("series", "").fillna("")
        df["description"] = df.get("description", "").fillna("")

        df["search_text"] = (
            df["title"].astype(str)
            + " "
            + df["author"].astype(str)
            + " "
            + df["series"].astype(str)
            + " "
            + df["genre"].astype(str)
            + " "
            + df["tags"].apply(lambda x: " ".join(x) if isinstance(x, list) else str(x))
            + " "
            + df["description"].astype(str)
        )

        if "id" not in df.columns:
            df["id"] = range(1, len(df) + 1)

        df = df.where(pd.notnull(df), None)
        self.comics_df = df

    def content_based_recommendation(self, keywords: List[str]) -> List[Dict]:
        if self.comics_df.empty:
            return []
        if self.comic_embeddings is None:
            return self._keyword_fallback(keywords)

        query_embedding = self.model.encode(" ".join(keywords))
        similarities = cosine_similarity([query_embedding], self.comic_embeddings)[0]
        top_indices = similarities.argsort()[-50:][::-1]
        filtered = [idx for idx in top_indices if similarities[idx] >= 0.22]
        if not filtered:
            return self._keyword_fallback(keywords)
        return self.comics_df.iloc[filtered[:10]].to_dict("records")

    def hybrid_recommendation(self, content_recs: List[Dict], sentiment: float) -> List[Dict]:
        if not content_recs:
            return []
        if sentiment < 0:
            return list(reversed(content_recs))
        return content_recs

    def generate_explanation(self, keywords: List[str], recs: List[Dict]) -> str:
        if not recs:
            return "No matching comics yet."
        if keywords:
            return f"Matched keywords: {', '.join(keywords[:5])}"
        return "Recommendations based on your preferences."

    def _load_or_build_embeddings(self):
        if self.comics_df.empty:
            return None
        if not self.embeddings_path:
            return None
        if os.path.exists(self.embeddings_path):
            try:
                embeddings = np.load(self.embeddings_path)
                if len(embeddings) == len(self.comics_df):
                    return embeddings
            except Exception:
                pass

        texts = self.comics_df["search_text"].fillna("").astype(str).tolist()
        if not texts:
            return None
        embeddings = self.model.encode(texts, show_progress_bar=False)
        try:
            np.save(self.embeddings_path, embeddings)
        except Exception:
            pass
        return embeddings

    def _keyword_fallback(self, keywords: List[str]) -> List[Dict]:
        if not keywords:
            return self.comics_df.head(10).to_dict("records")
        lowered = [k.lower() for k in keywords]

        def match_row(row):
            hay = " ".join(
                [
                    str(row.get("title", "")),
                    str(row.get("author", "")),
                    str(row.get("series", "")),
                    str(row.get("genre", "")),
                    " ".join(row.get("tags", []) or []),
                    str(row.get("description", "")),
                ]
            ).lower()
            return any(k in hay for k in lowered)

        filtered = self.comics_df[self.comics_df.apply(match_row, axis=1)]
        if filtered.empty:
            return self.comics_df.head(10).to_dict("records")
        return filtered.head(10).to_dict("records")
