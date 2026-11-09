"""Ink-and-watercolour closing image: an isolated black hole in a well of spacetime, lensing a star.

A sheet of spacetime, drawn as concentric ink bands with hatched edges and teal watercolour between
them, sinks into a well with a black hole at its bottom. A star far behind the black hole is seen
through it as the two images a point lens makes, two golden arcs hugging the hole. The style follows
the gravitational-wave cartoon that closed the M.Sc. defense.

The sheet is the height field z = -A / sqrt(R^2 + c^2), ray-cast from a camera looking down on it, so it
occludes itself and the black hole correctly; the band pattern lives on the sheet, in its own (R, phi)
coordinates, and is anti-aliased with its screen-space derivatives. The two images obey the lens
equation, in the plane of the sky around the hole.

    python art/microlensing_well.py [-o img/microlensing-well.jpg] [--scale 1] [--seed 3]

--scale 0.25 renders a quick preview. Needs numpy, scipy and Pillow.
"""
import argparse

import numpy as np
from PIL import Image
from scipy import ndimage

A_WELL, C_WELL = 1.45, 0.55        # depth and width of the well
EL = np.radians(52)                 # camera elevation above the sheet
DIST = 6.2                          # camera distance from the centre of the well
VFOV = np.radians(56)               # vertical field of view
BH_SCREEN = (0.585, 0.40)           # where the black hole sits on the page (fraction of W, H)
R_BH = 0.42                         # black-hole sphere radius (sheet units)
BAND0, BAND_DR = 0.42, 0.50         # first band radius and spacing (sheet units)
INK = np.array([10, 12, 20]) / 255.0


def hexrgb(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)]) / 255.0


def noise(rng, shape, sigma):
    f = ndimage.gaussian_filter(rng.standard_normal(shape), sigma, mode='wrap')
    return (f - f.mean()) / f.std()


def height(R):
    return -A_WELL / np.sqrt(R ** 2 + C_WELL ** 2)


def camera(W, H):
    """Camera position, rotation (rows: right, up, forward) and focal length in pixels."""
    pos = np.array([0.0, -DIST * np.cos(EL), DIST * np.sin(EL)])
    target = np.array([0.0, 0.0, height(0.0) * 0.35])
    fwd = target - pos
    fwd /= np.linalg.norm(fwd)
    right = np.cross(fwd, [0, 0, 1.0])
    right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    f = 0.5 * H / np.tan(VFOV / 2)
    return pos, np.stack([right, up, fwd]), f


def rays(W, H, pos, rot, f, centre_px):
    """Ray directions for every pixel; centre_px is where the optical axis meets the page."""
    v, u = np.mgrid[0:H, 0:W].astype(float) + 0.5
    x = (u - centre_px[0]) / f
    y = -(v - centre_px[1]) / f
    d = x[..., None] * rot[0] + y[..., None] * rot[1] + rot[2]
    return d / np.linalg.norm(d, axis=-1, keepdims=True)


def cast(pos, d, nstep=220, nbis=14):
    """First intersection of every ray with the sheet z = height(R)."""
    dz = np.minimum(d[..., 2], -1e-4)
    zmin = height(0.0) - 0.05
    t0 = (0.0 - pos[2]) / dz                     # where the ray crosses z = 0 (above the sheet until then)
    t1 = (zmin - pos[2]) / dz                    # where it would reach the bottom of the well
    hit = np.full(dz.shape, np.nan)
    lo = t0.copy()
    for k in range(1, nstep + 1):
        t = t0 + (t1 - t0) * k / nstep
        x, y, z = pos[0] + t * d[..., 0], pos[1] + t * d[..., 1], pos[2] + t * dz
        below = (z <= height(np.hypot(x, y))) & np.isnan(hit)
        hit[below] = t[below]
        still = np.isnan(hit)
        lo[still] = t[still]
    hi = np.where(np.isnan(hit), t1, hit)
    for _ in range(nbis):
        mid = 0.5 * (lo + hi)
        x, y, z = pos[0] + mid * d[..., 0], pos[1] + mid * d[..., 1], pos[2] + mid * dz
        below = z <= height(np.hypot(x, y))
        hi = np.where(below, mid, hi)
        lo = np.where(below, lo, mid)
    t = 0.5 * (lo + hi)
    return t, pos[0] + t * d[..., 0], pos[1] + t * d[..., 1]


def aa(dist_px):
    """Coverage of an edge from a signed distance in pixels (positive = inside)."""
    return np.clip(dist_px + 0.5, 0, 1)


def screen_scale(field):
    """Size of one pixel in the units of `field` (its screen-space gradient magnitude)."""
    gy, gx = np.gradient(field)
    return np.hypot(gx, gy) + 1e-9


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('-o', '--out', default='img/microlensing-well.jpg')
    ap.add_argument('--scale', type=float, default=1.0)
    ap.add_argument('--seed', type=int, default=3)
    args = ap.parse_args()
    rng = np.random.default_rng(args.seed)
    W, H = int(1920 * args.scale), int(1200 * args.scale)
    px = 1920 * args.scale / 1920.0                     # pixel scale relative to the full render

    pos, rot, f = camera(W, H)
    # place the optical axis so that the black hole lands at BH_SCREEN
    zb = height(0.0) + R_BH * 0.75
    bh = np.array([0.0, 0.0, zb])
    pc = rot @ (bh - pos)
    centre = (BH_SCREEN[0] * W - f * pc[0] / pc[2], BH_SCREEN[1] * H + f * pc[1] / pc[2])
    bh_px = np.array([BH_SCREEN[0] * W, BH_SCREEN[1] * H])
    bh_rad_px = f * R_BH / pc[2]

    d = rays(W, H, pos, rot, f, centre)
    t, X, Y = cast(pos, d)
    R = np.hypot(X, Y)
    phi = np.arctan2(Y, X)

    # ---- watercolour on the sheet -------------------------------------------------------------------
    tex = 1024
    span = 16.0                                          # the texture covers [-span, span]^2 of the sheet
    big = noise(rng, (tex, tex), 40)
    mid = noise(rng, (tex, tex), 12)
    fine = noise(rng, (tex, tex), 3)
    coords = [(Y + span) / (2 * span) * (tex - 1), (X + span) / (2 * span) * (tex - 1)]
    def onsheet(field):
        return ndimage.map_coordinates(field, coords, order=1, mode='wrap')
    nb, nm, nf = onsheet(big), onsheet(mid), onsheet(fine)

    # bands: ink rings at R_k with hatched edges; position within the gap sets the wash
    k = np.floor((R - BAND0) / BAND_DR + 0.5)
    Rk = BAND0 + k * BAND_DR
    wob = 0.022 * nm + 0.007 * nf + 0.03 * nb
    s = R - Rk + wob                                     # signed distance from the band centre (sheet units)
    half = np.minimum(0.085 + 0.004 * np.clip(k, 0, 12), 0.12) * (1 + 0.15 * nb)
    gap = np.clip((np.abs(s) - half) / (BAND_DR / 2 - half), 0, 1)   # 0 at the ink edge, 1 mid-gap

    navy, deep = hexrgb('#16294a'), hexrgb('#0b1630')
    teal, pale = hexrgb('#3f9a9c'), hexrgb('#9fd6cf')
    lilac = hexrgb('#6f6aa0')
    wash = np.sin(np.pi * gap) ** 0.35
    blue = hexrgb('#4a7fb5')
    tint = np.clip(0.5 + 0.45 * nb, 0, 1)[..., None] * 0.45   # watercolour drifts from teal to blue
    stripe = teal * (1 - tint) + blue * tint
    col = navy[None, None] * (1 - wash[..., None]) + stripe * wash[..., None]
    hi = np.clip(wash - 0.75, 0, 1)[..., None] / 0.25 * (0.35 + 0.2 * nm[..., None])
    col = col * (1 - hi) + pale * hi                     # a lighter core in each teal stripe
    lt = np.clip(0.25 + 0.2 * nb, 0, 0.5)[..., None] * (1 - wash[..., None])
    col = col * (1 - lt) + lilac * lt                    # violet in the darks, like the cartoon's washes
    col *= (1 + 0.06 * nf)[..., None]                    # pigment granulation

    # light: the sheet's slope against a light from the upper left
    dh = A_WELL * R / (R ** 2 + C_WELL ** 2) ** 1.5      # dh/dR
    nx, ny = -dh * X / np.maximum(R, 1e-6), -dh * Y / np.maximum(R, 1e-6)
    nrm = np.sqrt(nx ** 2 + ny ** 2 + 1)
    light = np.array([-0.45, 0.35, 0.82]); light /= np.linalg.norm(light)
    lam = (nx * light[0] + ny * light[1] + light[2]) / nrm
    col *= (0.78 + 0.38 * lam)[..., None]
    # depth haze toward the horizon, and the well's throat darkening
    fog = np.clip((t - DIST * 0.9) / (DIST * 2.2), 0, 1)[..., None] ** 1.2
    col = col * (1 - 0.55 * fog) + navy * 0.55 * fog
    throat = np.exp(-(R / 0.55) ** 2)[..., None]
    col = col * (1 - 0.6 * throat) + deep * 0.6 * throat

    # ---- ink: bands and their hatching ----------------------------------------------------------------
    ps = screen_scale(R)                                 # sheet units per pixel across the bands
    band = aa((half - np.abs(s)) / ps)
    # hatching: tapered ticks along both edges, constant spacing along the ring on the sheet
    period = 0.055
    N = np.maximum(np.round(2 * np.pi * np.maximum(Rk, 0.2) / period), 8)
    q = phi * N / (2 * np.pi) + 7.3 * k                  # tick phase (integer at a tick)
    dq = np.abs((q + 0.5) % 1.0 - 0.5)                   # distance to the nearest tick, in periods
    gXy, gXx = np.gradient(X)
    gYy, gYx = np.gradient(Y)
    R2 = np.maximum(R ** 2, 1e-9)
    dphi = np.hypot((X * gYx - Y * gXx) / R2, (X * gYy - Y * gXy) / R2)
    qs = N / (2 * np.pi) * dphi + 1e-9                  # periods per pixel along the ring
    jit = 0.65 + 0.45 * (0.5 + 0.5 * np.sin(phi * (3 + k % 4) + 1.7 * k)) * (1 + 0.25 * nm)
    out_len = (0.30 * half + 0.025) * jit                # tick length beyond the outer edge
    in_len = 0.6 * out_len
    edge = np.abs(s) - half                              # > 0 outside the band
    along = np.where(s > 0, edge / out_len, edge / in_len)
    taper = np.clip(1 - along, 0, 1) ** 0.6
    tick_w = 0.15 * taper                                # half-width in periods
    ticks = aa((tick_w - dq) / qs) * (edge > -ps) * (along < 1)
    ink = np.clip(np.maximum(band, ticks), 0, 1)
    ink *= 1 - 0.85 * fog[..., 0] ** 0.7                 # bands fade into the haze
    img = col * (1 - 0.96 * ink[..., None]) + INK * 0.96 * ink[..., None]

    # ---- the black hole: a sphere at the bottom of the well, drawn in ink ---------------------------
    oc = pos - bh
    bq = np.einsum('ijk,k->ij', d, oc)
    disc = bq ** 2 - (oc @ oc - R_BH ** 2)
    tsph = -bq - np.sqrt(np.maximum(disc, 0))
    on = (disc > 0) & (tsph < t)
    # soft edge in pixels from the distance to the sphere's silhouette
    sil = np.sqrt(np.maximum(disc, 0)) / screen_scale(np.sqrt(np.maximum(disc, 0)))
    cover = np.where(on, np.clip(sil, 0, 1), 0)[..., None]
    rim = np.where(on, np.exp(-np.clip(sil, 0, None) / (2.2 * px + 0.5)), 0)[..., None] * 0.55
    img = img * (1 - cover) + hexrgb('#040508') * cover
    img = img * (1 - rim) + hexrgb('#a9dcd6') * rim

    # ---- the lensed star: two golden arcs, by the lens equation around the hole on the sky ----------
    vv, uu = np.mgrid[0:H, 0:W].astype(float) + 0.5
    thE = 1.75 * bh_rad_px
    tx, ty = (uu - bh_px[0]) / thE, (vv - bh_px[1]) / thE
    r2 = np.maximum(tx ** 2 + ty ** 2, 1e-9)
    bx, by = tx - tx / r2, ty - ty / r2
    src = np.array([0.33, -0.24])                        # source offset, in Einstein radii
    rho = 0.27
    ds = np.hypot(bx - src[0], by - src[1])
    star = aa((rho - ds) / screen_scale(ds))
    shade = np.clip(1 - np.hypot(bx - src[0] + 0.07, by - src[1] + 0.09) / (1.25 * rho), 0, 1)
    gold = hexrgb('#d9c43c') * (1 - 0.55 * shade[..., None]) + hexrgb('#fbf3a8') * 0.55 * shade[..., None]
    halo = ndimage.gaussian_filter(star, 10 * px + 1) * 2.0 + ndimage.gaussian_filter(star, 50 * px + 1) * 2.6
    g = np.clip(halo, 0, 1)[..., None] * 0.8
    img = 1 - (1 - img) * (1 - hexrgb('#f6e98a') * g)    # screen-blended glow
    outline = aa((rho + 0.035 - ds) / screen_scale(ds)) * (1 - star)
    img = img * (1 - 0.9 * outline[..., None]) + INK * 0.9 * outline[..., None]
    img = img * (1 - star[..., None]) + gold * star[..., None]

    # ---- spatter and paper ---------------------------------------------------------------------------
    n = int(2200 * px ** 2) + 80
    sx, sy = rng.uniform(0, W, n), rng.uniform(0, H, n)
    rr = (rng.pareto(3.0, n) * 0.8 + 0.5) * px + 0.3
    al = rng.uniform(0.35, 0.95, n)
    spat = np.zeros((H, W))
    for x0, y0, r0, a0 in zip(sx, sy, rr, al):
        y_, x_ = int(y0), int(x0)
        rad = int(r0 + 2)
        ys, xs = slice(max(y_ - rad, 0), min(y_ + rad + 1, H)), slice(max(x_ - rad, 0), min(x_ + rad + 1, W))
        dd = np.hypot(uu[ys, xs] - x0, vv[ys, xs] - y0)
        spat[ys, xs] = np.maximum(spat[ys, xs], aa(r0 - dd) * a0)
    spat *= 1 - 0.8 * star - 0.6 * cover[..., 0]
    img = img * (1 - spat[..., None]) + hexrgb('#f2f6ee') * spat[..., None]

    paper = 1 + 0.03 * noise(rng, (H, W), 0.8 * px + 0.3)
    yy, xx = vv / H - 0.5, uu / W - 0.5
    vig = 1 - 0.30 * np.clip(np.hypot(xx * 1.05, yy * 1.25) - 0.25, 0, 1) ** 1.3
    img = np.clip(img * (paper * vig)[..., None], 0, 1)

    Image.fromarray((img * 255).astype(np.uint8)).save(args.out, quality=93, subsampling=0)
    print('wrote', args.out, W, 'x', H)


if __name__ == '__main__':
    main()
