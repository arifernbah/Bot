"""Minimal exit decision stub.  Always hold position (no exit)."""

from typing import Dict

__all__ = ["should_exit"]

def should_exit(position_data: Dict, current_price: float, *_, **__) -> Dict:
    """Return a no-action decision compatible with the caller expectations."""
    return {
        "action": "hold",
        "reason": "stub",
        "urgency": "NONE",
    }