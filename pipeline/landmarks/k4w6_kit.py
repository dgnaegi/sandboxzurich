"""Shared helpers for wave-6 landmarks (k4w6_*.py): public buildings. Additive: re-uses k4w4_kit (block_model ...); nothing there is changed.
- registers into pipeline/overrides/landmarks_k4w6.json (block6 redirects k4w4_kit.OVR4)"""
import k4w4_kit as _k4
from k4w4_kit import *   # noqa: F401,F403

OVR6 = ROOT / "pipeline" / "overrides" / "landmarks_k4w6.json"


def block6(*a, **k):
    """block_model with the wave-6 override file as registry."""
    _k4.OVR4 = OVR6
    return _k4.block_model(*a, **k)
