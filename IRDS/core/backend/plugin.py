# File: core/backend/plugin.py
"""
Plugin registry for backend IR filters.
Supports both horizontal (triple-based) filters and vertical (list-based) filters.
Horizontal filters decide whether to keep a (pre, post, log) triple.
Vertical filters perform list-based deduplication/filtering.
"""
from typing import Callable, Dict, List, Any

# ========= Registries =========
_H_RULES: Dict[str, Callable[[str, str, str], bool]] = {}
_V_RULES: Dict[str, Callable[[List[str]], List[str]]] = {}

# ========= Decorators =========
def register_hfilter(name: str) -> Callable[[Callable[[str, str, str], bool]], Callable[[str, str, str], bool]]:
    """
    Decorator to register a horizontal IR filter (pre_ir, post_ir, log) -> bool.
    """
    def decorator(func: Callable[[str, str, str], bool]) -> Callable[[str, str, str], bool]:
        _H_RULES[name] = func
        return func
    return decorator

def register_vfilter(name: str) -> Callable[[Callable[[List[str]], List[str]]], Callable[[List[str]], List[str]]]:
    """
    Decorator to register a vertical filter operating on list of file paths.
    """
    def decorator(func: Callable[[List[str]], List[str]]) -> Callable[[List[str]], List[str]]:
        _V_RULES[name] = func
        return func
    return decorator

# ========= Getters =========
def get_hfilter(name: str) -> Callable[[str, str, str], bool]:
    """Retrieve a registered horizontal filter by name."""
    try:
        return _H_RULES[name]
    except KeyError:
        raise KeyError(f"Unknown horizontal filter: {name}")

def get_vfilter(name: str) -> Callable[[List[str]], List[str]]:
    """Retrieve a registered vertical filter by name."""
    try:
        return _V_RULES[name]
    except KeyError:
        raise KeyError(f"Unknown vertical filter: {name}")

# ========= Listers =========
def list_hfilters() -> List[str]:
    """List all available horizontal filter names."""
    return list(_H_RULES.keys())

def list_vfilters() -> List[str]:
    """List all available vertical filter names."""
    return list(_V_RULES.keys())

# Import builtin filters to register them
from .builtin_filters import *