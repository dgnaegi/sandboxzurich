"""'The Docks' office block at the Langstrasse underpass (Langstrasse/Duttweilerbruecke side): five-floor grey metal-panel office block with silver horizontal window bands,
dark-clad top floor, glazed ground floor, antenna mast on the roof. Photos: research/v3/docks_langstrasse.md (Commons #16 #17 #18 by Moritz Twente)"""
from k4w4_kit import *


def build():
    def extra(m, ctx):
        zt = max(z for z, g in [(v[0], v[1]) for v in ctx["vols"]]) + 0.4
        q = ctx["vols"][-1][1].representative_point()
        m.box(ctx["mf"], q.x, q.y, 0.35, 0.35, zt, zt + 7.0, col=(150, 150, 152, 255))
        m.box(ctx["mf"], q.x + 1.4, q.y, 2.0, 1.6, zt, zt + 2.2, col=(120, 124, 126, 255))
    block_model("docks", "The Docks Langstrassen-Unterfuehrung", ["ID_FB9C1D94"], wall="#9aa0a6", frame="#cfd3d6", glass="#3b4650", sky="#9fb2c0", cols=3, rows=1,
                fh=3.4, bayw=2.4, win=(2.0, 1.35, 0.95), eg_h=4.2, eg_kind="shop", cornice=("#6d7378", 0.2, 0.5), floor_bands=("#7f858a", 0.14, 0.35), roof=("flat", "#6a6d70"), parapet=0.3,
                seed=91, lit=0.4, base_col="#6a6e72", surround="#cfd3d6", deep_z=6.0, extra=extra)


if __name__ == "__main__":
    build()
