import re
from typing import List


def extract_keywords(prompt: str) -> List[str]:
    tokens = re.findall(r"[a-zA-Z]{3,}", prompt.lower())
    return list(dict.fromkeys(tokens))


def analyze_sentiment(prompt: str) -> float:
    lowered = prompt.lower()
    if any(word in lowered for word in ["love", "great", "favorite"]):
        return 0.8
    if any(word in lowered for word in ["hate", "boring", "bad"]):
        return -0.6
    return 0.0
