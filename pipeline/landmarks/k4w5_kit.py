"""Shared helpers for wave-5 landmarks (k4w5_*.py). Additive: re-uses k4w4_kit (block_model, hip_roof, textures ...); nothing there is changed.
- registers into pipeline/overrides/landmarks_k4w5.json (block5 redirects k4w4_kit.OVR4)"""
import k4w4_kit as _k4
from k4w4_kit import *   # noqa: F401,F403

OVR5 = ROOT / "pipeline" / "overrides" / "landmarks_k4w5.json"


def block5(*a, **k):
    """block_model with the wave-5 override file as registry."""
    _k4.OVR4 = OVR5
    return _k4.block_model(*a, **k)
