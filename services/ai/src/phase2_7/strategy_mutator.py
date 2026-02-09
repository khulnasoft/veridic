"""
Strategy Mutator

Mutates attack payloads safely to bypass discovered filters or 
to explore variant vulnerabilities.
"""

import hashlib
from typing import List, Dict, Any

class StrategyMutator:
    """
    Handles deterministic payload mutation.
    """

    def mutate_payload(self, base_payload: str, mutation_type: str) -> str:
        """
        Applies a specific mutation to a payload.
        """
        if mutation_type == "case_swap":
            return "".join([c.swapcase() for c in base_payload])
        elif mutation_type == "url_encode":
            import urllib.parse
            return urllib.parse.quote(base_payload)
        elif mutation_type == "null_prefix":
            return f"%00{base_payload}"
            
        return base_payload

    def get_mutation_hash(self, mutation_results: str) -> str:
        """Hash of the mutated payload."""
        return hashlib.sha256(mutation_results.encode()).hexdigest()
