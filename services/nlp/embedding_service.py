import os
import logging
import math
import threading
from collections import OrderedDict
from typing import Dict, List, Optional

logger = logging.getLogger("resume_analyzer.nlp")

# Global singleton model cache
_MODEL_INSTANCE = None
_MODEL_LOAD_ATTEMPTED = False
_IS_MODEL_AVAILABLE = False

# Configurable embedding cache parameters
DEFAULT_MODEL_NAME = "all-MiniLM-L6-v2"
DEFAULT_CACHE_SIZE = 2000

# Thread-safe LRU Cache implementation using OrderedDict
_CACHE_LOCK = threading.Lock()
_EMBEDDING_CACHE: OrderedDict[str, List[float]] = OrderedDict()
_CACHE_HITS = 0
_CACHE_MISSES = 0


def _get_config():
    model_name = os.getenv("NLP_MODEL_NAME", DEFAULT_MODEL_NAME)
    try:
        cache_size = int(os.getenv("EMBEDDING_CACHE_SIZE", str(DEFAULT_CACHE_SIZE)))
    except ValueError:
        cache_size = DEFAULT_CACHE_SIZE
    return model_name, cache_size


def _load_model():
    """
    Lazy loader for sentence-transformers model.
    Catches any import or initialization failure cleanly without crashing process.
    On Vercel environment, bypasses model loading to run lightweight Jaccard fallback mode.
    """
    global _MODEL_INSTANCE, _MODEL_LOAD_ATTEMPTED, _IS_MODEL_AVAILABLE
    if _MODEL_LOAD_ATTEMPTED:
        return _MODEL_INSTANCE

    _MODEL_LOAD_ATTEMPTED = True

    # Detect Vercel serverless environment
    if os.getenv("VERCEL"):
        logger.info("Vercel runtime environment detected. Bypassing SentenceTransformer model load; running lightweight Jaccard fallback mode.")
        _MODEL_INSTANCE = None
        _IS_MODEL_AVAILABLE = False
        return None

    model_name, _ = _get_config()

    try:
        from sentence_transformers import SentenceTransformer
        logger.info(f"Loading sentence-transformers embedding model '{model_name}'...")
        _MODEL_INSTANCE = SentenceTransformer(model_name)
        _IS_MODEL_AVAILABLE = True
        logger.info("SentenceTransformer model loaded successfully.")
    except Exception as e:
        logger.warning(f"SentenceTransformer embedding model unavailable ({e}). Falling back to token similarity.")
        _MODEL_INSTANCE = None
        _IS_MODEL_AVAILABLE = False

    return _MODEL_INSTANCE


def is_available() -> bool:
    """
    Returns True if local embedding model is loaded and operational.
    """
    if not _MODEL_LOAD_ATTEMPTED:
        _load_model()
    return _IS_MODEL_AVAILABLE


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """
    Computes cosine similarity between two 1D float vectors.
    """
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return max(0.0, min(1.0, dot / (norm_a * norm_b)))


def _token_jaccard_similarity(text_a: str, text_b: str) -> float:
    """
    Fallback deterministic token overlap similarity when NLP model is unavailable.
    """
    tokens_a = set(text_a.lower().split())
    tokens_b = set(text_b.lower().split())
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a.intersection(tokens_b)
    union = tokens_a.union(tokens_b)
    return len(intersection) / float(len(union))


def embed(text: str) -> Optional[List[float]]:
    """
    Generates embedding vector for text using sentence-transformers with thread-safe LRU memory caching.
    Returns None if text is empty or model unavailable.
    """
    global _CACHE_HITS, _CACHE_MISSES

    if not text or not text.strip():
        return None

    clean_text = text.strip()
    _, max_cache_size = _get_config()

    # Thread-safe LRU lookup
    with _CACHE_LOCK:
        if clean_text in _EMBEDDING_CACHE:
            _CACHE_HITS += 1
            # Move key to end to mark as recently used
            _EMBEDDING_CACHE.move_to_end(clean_text)
            return _EMBEDDING_CACHE[clean_text]
        _CACHE_MISSES += 1

    model = _load_model()
    if model is None:
        return None

    try:
        embedding = model.encode(clean_text, convert_to_numpy=True).tolist()
        
        with _CACHE_LOCK:
            _EMBEDDING_CACHE[clean_text] = embedding
            _EMBEDDING_CACHE.move_to_end(clean_text)
            # Evict oldest entry if capacity exceeded
            if len(_EMBEDDING_CACHE) > max_cache_size:
                _EMBEDDING_CACHE.popitem(last=False)
                
        return embedding
    except Exception as e:
        logger.warning(f"Error encoding text embedding: {e}")
        return None


def get_cache_stats() -> dict:
    """
    Returns thread-safe internal embedding cache statistics.
    """
    with _CACHE_LOCK:
        total = _CACHE_HITS + _CACHE_MISSES
        hit_rate = round((_CACHE_HITS / total), 4) if total > 0 else 0.0
        return {
            "size": len(_EMBEDDING_CACHE),
            "hits": _CACHE_HITS,
            "misses": _CACHE_MISSES,
            "hit_rate": hit_rate
        }


def clear_cache():
    """
    Clears internal embedding cache.
    """
    global _CACHE_HITS, _CACHE_MISSES
    with _CACHE_LOCK:
        _EMBEDDING_CACHE.clear()
        _CACHE_HITS = 0
        _CACHE_MISSES = 0


def similarity(text_a: str, text_b: str) -> float:
    """
    Calculates semantic similarity between two text snippets (0.0 to 1.0).
    Uses sentence embeddings if available, or token Jaccard fallback.
    """
    if not text_a or not text_b or not text_a.strip() or not text_b.strip():
        return 0.0

    if not is_available():
        return _token_jaccard_similarity(text_a, text_b)

    try:
        emb_a = embed(text_a)
        emb_b = embed(text_b)
        if emb_a and emb_b:
            return round(cosine_similarity(emb_a, emb_b), 4)
    except Exception as e:
        logger.warning(f"Error computing semantic similarity: {e}")

    return round(_token_jaccard_similarity(text_a, text_b), 4)
