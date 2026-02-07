import re
from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class ParsedQuery:
    raw: str
    keywords: List[str]


def parse_query(prompt: str) -> ParsedQuery:
    raw = (prompt or "").strip()
    tokens = re.findall(r"[a-zA-Z]{3,}", raw.lower())
    keywords = list(dict.fromkeys(tokens))
    return ParsedQuery(raw=raw, keywords=keywords)

