import os
from dataclasses import dataclass
from typing import Dict, Optional

import pandas as pd


@dataclass(frozen=True)
class CatalogPaths:
    catalog_csv: str
    index_dir: str

    @property
    def embeddings_npy(self) -> str:
        return os.path.join(self.index_dir, "catalog_embeddings.npy")

    @property
    def faiss_index(self) -> str:
        return os.path.join(self.index_dir, "catalog.faiss")

    @property
    def meta_json(self) -> str:
        return os.path.join(self.index_dir, "catalog_meta.json")


def load_catalog(csv_path: str) -> pd.DataFrame:
    if not csv_path or not os.path.exists(csv_path):
        return pd.DataFrame()

    df = pd.read_csv(
        csv_path,
        engine="python",
        on_bad_lines="skip",
        quotechar='"',
        escapechar="\\",
    )
    if df.empty:
        return df
    return normalize_catalog(df)


def normalize_catalog(df: pd.DataFrame) -> pd.DataFrame:
    # Column aliases
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

    # Required cols
    for col, default in [
        ("id", None),
        ("title", ""),
        ("author", ""),
        ("publisher", ""),
        ("genre", ""),
        ("year", None),
        ("rating", None),
        ("description", ""),
        ("tags", ""),
        ("cover_image", None),
        ("series", ""),
    ]:
        if col not in df.columns:
            df[col] = default

    # Tags normalization
    def _to_tags(x) -> list:
        if x is None:
            return []
        if isinstance(x, list):
            return [str(t).strip().lower() for t in x if str(t).strip()]
        s = str(x)
        return [t.strip().lower() for t in s.split(",") if t.strip()]

    df["tags"] = df["tags"].fillna("").apply(_to_tags)

    # Fill text columns
    for col in ["title", "author", "publisher", "genre", "series", "description"]:
        df[col] = df[col].fillna("").astype(str)

    # Build searchable text (single field used for embedding)
    df["search_text"] = (
        df["title"]
        + " "
        + df["author"]
        + " "
        + df["publisher"]
        + " "
        + df["series"]
        + " "
        + df["genre"]
        + " "
        + df["tags"].apply(lambda x: " ".join(x) if isinstance(x, list) else str(x))
        + " "
        + df["description"]
    ).astype(str)

    # Ensure stable string source_id (original dataset id can be non-numeric)
    df["source_id"] = df["id"].astype(str)

    # Provide numeric row ids for internal index mapping
    df["row_id"] = range(len(df))

    df = df.where(pd.notnull(df), None)
    return df


def build_source_id_map(df: pd.DataFrame) -> Dict[str, int]:
    # source_id -> row_id
    if df.empty or "source_id" not in df.columns or "row_id" not in df.columns:
        return {}
    out = {}
    for _, r in df[["source_id", "row_id"]].iterrows():
        sid = str(r["source_id"])
        out[sid] = int(r["row_id"])
    return out


def best_effort_match_row_id(df: pd.DataFrame, title: str, author: Optional[str]) -> Optional[int]:
    if df.empty:
        return None
    t = (title or "").strip().lower()
    if not t:
        return None
    a = (author or "").strip().lower()
    subset = df[df["title"].str.lower().str.strip() == t]
    if subset.empty:
        return None
    if a:
        subset2 = subset[subset["author"].str.lower().str.strip() == a]
        if not subset2.empty:
            return int(subset2.iloc[0]["row_id"])
    return int(subset.iloc[0]["row_id"])

