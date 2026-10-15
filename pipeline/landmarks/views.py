"""Build free_shot.mjs views for a site frame. Usage: python views.py site name  (prints JSON)"""
import json, math, sys
def frame(cx, cy, ang_deg):
    a = math.radians(ang_deg); ca, sa = math.cos(a), math.sin(a)
    return lambda u, v, h: [round(cx + u * ca - v * sa, 2), round(cy + u * sa + v * ca, 2), h]
