import os
import numpy as np


def load_embeddings(path: str):
    if os.path.exists(path):
        return np.load(path)
    return None
