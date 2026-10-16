"""Swissmill: Silo tower (118 m grain silo at Sihlquai/Limmat, pale grey concrete slab with narrow window slots, machine house on top) and the old Stadtmuehle block
(white-grey rendered 5-storey mill with regular windows, red brick stepped-gable sections, dark roof). Photos: research/v3/swissmill.md
(Mapillary #7 #1 #10 #14 #6 #12 till/Yha1/others, Commons #16 #17 #18)"""
from k4w4_kit import *


def build():
    block_model("swissmill_turm", "Swissmill Tower Silo", ["ID_CCF8F166"], wall_tex=tex_concrete("#a9aaa5", 256, (2, 4), seed=7, joint=0.10), wmod=(6.0, 12.0), frame="#7c7e80",
                glass="#3a4650", sky="#8fa4b2", cols=1, rows=1, fh=4.2, bayw=5.5, win=(0.7, 1.3, 1.4), eg_h=6.0, eg_kind="plain", cornice=("#8e8f8b", 0.25, 0.8), roof=("flat", "#7a7b78"),
                seed=93, lit=0.25, base_col="#7d7e7a", surround="#85878a", deep_z=2.0, parapet=0.8, min_area=30.0, simp=1.0)
    block_model("stadtmuehle", "Stadtmuehle Swissmill Altbau", ["ID_32C9B073"], wall="#e2dfd4", frame="#f3f1ea", glass="#35414b", sky="#8fa4b2", cols=2, rows=3, fh=3.4, bayw=2.5,
                win=(1.1, 1.8, 0.8), eg_h=4.4, eg_kind="plain", cornice=("#cfcabb", 0.3, 0.5), roof=("hip", "#5b524a", 4.5), roof_d=5.5, seed=95, lit=0.3, base_col="#85796c",
                surround="#d6d1c2", curtains=[(226, 222, 212), (176, 92, 70)], deep_z=9.0)


if __name__ == "__main__":
    build()
