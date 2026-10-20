"""H8: Haltestelle Letzigrund, Schirmdach (Foto cm_Gem_serabatte_Letzigrund, research/zones/z5/area_letzi.md Z5c-1): one big thin
roof slab (parallelogram, tilted, light grey top) on two slanted grey blade columns, glass cabin + bench + ticket machine underneath.
Local frame: long axis = x (12 m), open side faces +z, origin = centre on ground. Not a mushroom roof in the strict sense; the
catalog key keeps 'pilz' for the ticket wording."""
from model_core import Mesh


def strut(m, cell, a, b, w=0.55, d=0.28):
    """Slanted blade column from centre a (bottom) to b (top), cross-section w (x) by d (z)."""
    def ring(c): return [(c[0] - w / 2, c[1], c[2] - d / 2), (c[0] + w / 2, c[1], c[2] - d / 2), (c[0] + w / 2, c[1], c[2] + d / 2), (c[0] - w / 2, c[1], c[2] + d / 2)]
    A, B = ring(a), ring(b)
    for i in range(4):
        j = (i + 1) % 4
        m.quad(cell, [A[j], A[i], B[i], B[j]])


def pilz_dach():
    m = Mesh("H8")
    # roof slab: parallelogram, back edge higher than the front (3.7 -> 3.2), 0.22 m thick
    c = [(-6.0, -3.6), (4.6, -3.9), (6.0, 3.3), (-4.6, 3.6)]
    zb = lambda x, z: 3.75 - 0.5 * (z + 3.9) / 7.5
    top = [(x, zb(x, z) + 0.0, z) for x, z in c]
    bot = [(x, zb(x, z) - 0.22, z) for x, z in c]
    m.quad("white", [top[3], top[2], top[1], top[0]])
    m.quad("concrete", [bot[0], bot[1], bot[2], bot[3]])
    for i in range(4):
        j = (i + 1) % 4
        m.quad("white", [bot[i], bot[j], top[j], top[i]])
    # two slanted blade columns (steel grey), leaning outwards, carrying the roof near the back
    strut(m, "steel_grey", (-2.9, 0.0, -0.4), (-3.4, zb(-3.4, -1.2) - 0.22, -1.2))
    strut(m, "steel_grey", (1.6, 0.0, -0.4), (2.3, zb(2.3, -1.2) - 0.22, -1.2))
    # glass cabin (3.4 x 1.6, 2.3 high), open towards +z at the front corner
    cx, cz, L, D, H = 0.0, -1.0, 4.6, 1.8, 2.3
    for x in (cx - L / 2, cx + L / 2):
        m.box("steel_dark", (x, H / 2, cz - D / 2), (0.08, H, 0.08))
        m.box("steel_dark", (x, H / 2, cz + D / 2), (0.08, H, 0.08))
    m.box("steel_dark", (cx, H, cz), (L + 0.1, 0.08, D + 0.1))
    m.quad("glass_green", [(cx - L / 2, 0.15, cz - D / 2), (cx + L / 2, 0.15, cz - D / 2), (cx + L / 2, H - 0.05, cz - D / 2), (cx - L / 2, H - 0.05, cz - D / 2)])
    m.quad("glass_green", [(cx + L / 2, 0.15, cz - D / 2), (cx - L / 2, 0.15, cz - D / 2), (cx - L / 2, H - 0.05, cz - D / 2), (cx + L / 2, H - 0.05, cz - D / 2)])
    for sx in (cx - L / 2, cx + L / 2):
        for a, b in (((sx, cz - D / 2), (sx, cz + D / 2)), ((sx, cz + D / 2), (sx, cz - D / 2))):
            m.quad("glass_green", [(a[0], 0.15, a[1]), (b[0], 0.15, b[1]), (b[0], H - 0.05, b[1]), (a[0], H - 0.05, a[1])])
    # bench (wood slats) in front of the glass back wall, ticket machine at the east end
    m.box("steel_dark", (cx - 0.8, 0.22, cz), (0.05, 0.44, 0.45)); m.box("steel_dark", (cx + 0.8, 0.22, cz), (0.05, 0.44, 0.45))
    for k in range(3):
        m.box("bank_wood", (cx, 0.45, cz - 0.15 + k * 0.15), (2.4, 0.045, 0.12))
    m.box("steel_dark", (L / 2 + 0.9, 0.70, -0.9), (0.50, 1.25, 0.34), front="ticket")
    # poster panel on a post at the west end, base slab
    m.box("steel_dark", (-L / 2 - 0.9, 1.1, -0.9), (1.1, 2.0, 0.10), front="poster_a", back="poster_b")
    m.box("concrete", (0, 0.02, -0.2), (11.0, 0.04, 6.4))
    return m
