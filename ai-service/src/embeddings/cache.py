from typing import Dict, List, Optional
import hashlib
import logging

logger = logging.getLogger(__name__)

class EmbeddingCache:
    """Simple in-memory cache for embeddings during Phase 0."""
    
    def __init__(self):
        self.cache: Dict[str, List[float]] = {}
    
    def _get_key(self, text: str) -> str:
        """Generate cache key from text hash."""
        return hashlib.sha256(text.encode()).hexdigest()[:16]
    
    def get(self, text: str) -> Optional[List[float]]:
        """Retrieve embedding from cache."""
        key = self._get_key(text)
        return self.cache.get(key)
    
    def set(self, text: str, embedding: List[float]):
        """Store embedding in cache."""
        key = self._get_key(text)
        self.cache[key] = embedding
        logger.debug(f"Cached embedding for key: {key}")
    
    def clear(self):
        """Clear all cached embeddings."""
        self.cache.clear()
        logger.info("Embedding cache cleared")
    
    def stats(self) -> Dict:
        """Get cache statistics."""
        return {
            "total_entries": len(self.cache),
            "cache_size_kb": sum(len(str(v)) for v in self.cache.values()) / 1024
        }

# Global cache instance
_embedding_cache = EmbeddingCache()

def get_cache() -> EmbeddingCache:
    return _embedding_cache
