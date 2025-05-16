# File: core/preprocessing/plugin.py
"""
Plugin registry for IR preprocessing transforms.
Users can register custom text transform functions under a rule name.
"""
from typing import Callable, Dict

# Internal registry mapping rule names to transform functions
_RULES: Dict[str, Callable[[str], str]] = {}

def register_rule(name: str) -> Callable[[Callable[[str], str]], Callable[[str], str]]:
    """
    Decorator to register a preprocessing rule under a unique name.

    Example:
        @register_rule('rm_whitespace')
        def rm_whitespace(text: str) -> str:
            return ' '.join(text.split())
    """
    def decorator(func: Callable[[str], str]) -> Callable[[str], str]:
        _RULES[name] = func
        return func
    return decorator


def get_rule(name: str) -> Callable[[str], str]:
    """
    Retrieve a registered rule by its name. Raises KeyError if not found.
    """
    try:
        return _RULES[name]
    except KeyError:
        raise KeyError(f"Unknown preprocessing rule: {name}")


def list_rules() -> Dict[str, Callable[[str], str]]:
    """
    Return a copy of all registered rule mappings.
    """
    return dict(_RULES)
