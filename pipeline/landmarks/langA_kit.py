"""Shared helpers for the Langstrasse-Nord landmarks (langA_*.py). Additive: re-uses k4w4_kit.block_model, registry = overrides/landmarks_langA.json"""
import k4w4_kit as _k4
from k4w4_kit import *   # noqa: F401,F403

OVRA = ROOT / "pipeline" / "overrides" / "landmarks_langA.json"


def blockA(*a, **k):
    _k4.OVR4 = OVRA
    return _k4.block_model(*a, **k)
