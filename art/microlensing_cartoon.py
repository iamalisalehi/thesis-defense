"""Ink-and-watercolour cartoon of an isolated black hole microlensing a star.

The picture is ray traced through a point lens. Every pixel at image-plane position theta (measured
from the lens) sees the source plane at

    beta = theta * (1 - theta_E^2 / |theta|^2),

so everything drawn in the source plane -- the watercolour bulge sky, its stars, the yellow source
star and the ink ripples around it -- appears exactly as a point lens would show it: the source as
two images, one outside and one inside the Einstein ring, and the ripples as the nested ovals they
become, crowding into a dark vortex around the black hole.

    python art/microlensing_cartoon.py [-o img/microlensing-cartoon.jpg] [--seed 7]

Needs numpy, scipy, matplotlib (for contourpy) and Pillow. Takes about half a minute.
"""
import argparse

import contourpy
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

W, H = 1920, 1200                 # 16:10, the beamer page
LX, LY = 0.585 * W, 0.385 * H      # lens position (pixels)
TE = 0.175 * H                     # Einstein radius (pixels)
U0 = (0.47, -0.17)                 # source offset from the lens, in Einstein radii (x, y)
RS = 0.20                         # source-star radius, in Einstein radii
RBH = 0.20                         # drawn size of the black hole, in Einstein radii
PAD = 500                          # source-texture padding, for rays deflected off the frame
INK = np.array([10, 12, 20]) / 255.0


def hexrgb(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)]) / 255.0


def noise(rng, shape, sigma):
    """Smooth Gaussian random field, normalised to zero mean and unit variance."""
    f = ndimage.gaussian_filter(rng.standard_normal(shape), sigma, mode='wrap')
    return (f - f.mean()) / f.std()


def palette(v, stops):
    """Piecewise-linear colour map: stops = [(position, '#rrggbb'), ...]."""
    pos = np.array([s[0] for s in stops])
    cols = np.array([hexrgb(s[1]) for s in stops])
    out = np.empty(v.shape + (3,))
    for c in range(3):
        out[..., c] = np.interp(v, pos, cols[:, c])
    return out


# --------------------------------------------------------------------------------------------------
# The source plane: a watercolour Galactic bulge with dust lanes and a spatter of stars.
# --------------------------------------------------------------------------------------------------
def source_sky(rng):
    h, w = H + 2 * PAD, W + 2 * PAD
    yy, xx = np.mgrid[0:h, 0:w].astype(float)
    x, y = xx - PAD, yy - PAD                         # frame coordinates

    big = noise(rng, (h, w), 170)
    mid = noise(rng, (h, w), 55)
    small = noise(rng, (h, w), 16)
    fine = noise(rng, (h, w), 4)

    # the Milky Way band, tilted and wavy, passing behind the lens
    slope = -0.18
    d = (y - LY - slope * (x - LX) - 40 * mid) / np.sqrt(1 + slope ** 2)
    band = np.exp(-0.5 * (d / 260.0) ** 2)
    core = np.exp(-0.5 * (np.hypot(x - LX - 120, (y - LY) * 1.6) / 520.0) ** 2)   # the bulge glow

    # dust lanes: the zero-crossings of a mid-scale field, thin and filamentary
    lanefield = 0.8 * noise(rng, (h, w), 45) + 0.2 * small
    lanes = np.clip((lanefield - 0.35) / 0.9, 0, 1) ** 1.2 * band

    v = 0.22 + 0.10 * big + 0.04 * mid
    v += (0.40 + 0.10 * mid + 0.04 * small) * band + 0.12 * core
    v *= 1.0 - 0.55 * lanes
    v = np.clip(v, 0, 1)

    # watercolour: soft pigment levels with darker wet edges, and granulation
    levels = 7
    vq = ndimage.gaussian_filter(np.floor(v * levels) / levels, 2.0)
    edge = np.hypot(*np.gradient(vq))
    v = v * 0.75 + vq * 0.25
    rgb = palette(np.clip(v, 0, 1), [
        (0.00, '#070d1c'), (0.20, '#111f3d'), (0.35, '#1c355c'), (0.50, '#29597a'),
        (0.63, '#3a8592'), (0.76, '#64b1ad'), (0.88, '#a9d8cf'), (1.00, '#eef3e2')])
    lilac = hexrgb('#7d6fa6')
    tint = np.clip(0.5 + 0.5 * big, 0, 1)[..., None] * (1 - band[..., None]) * 0.22
    rgb = rgb * (1 - tint) + lilac * tint                          # violet washes away from the band
    warm = hexrgb('#e8d9b0')
    wt = (0.18 * core * band * np.clip(0.6 + 0.4 * mid, 0, 1))[..., None]
    rgb = rgb * (1 - wt) + warm * wt                               # a warm bulge core
    rgb *= (1 - 1.0 * np.clip(edge, 0, 0.12))[..., None]           # wet edges
    rgb *= (1 + 0.05 * fine)[..., None]                            # granulation

    # stars: a white spatter, denser in the band
    n = 9000
    sx = rng.uniform(0, w, n)
    sy = rng.uniform(0, h, n)
    keep = rng.uniform(0, 1, n) < 0.18 + 0.82 * band[sy.astype(int), sx.astype(int)]
    sx, sy = sx[keep], sy[keep]
    amp = rng.pareto(2.2, sx.size) * 0.35 + 0.15
    stars = np.zeros((h, w))
    np.add.at(stars, (sy.astype(int), sx.astype(int)), np.clip(amp, 0, 6))
    stars = ndimage.gaussian_filter(stars, 0.9) * 6.5
    # a few big paint drops
    drops = np.zeros((h, w))
    for _ in range(70):
        cx, cy, r = rng.uniform(0, w), rng.uniform(0, h), rng.uniform(1.6, 4.2)
        y0, y1 = int(max(cy - 8, 0)), int(min(cy + 9, h))
        x0, x1 = int(max(cx - 8, 0)), int(min(cx + 9, w))
        sub = np.hypot(xx[y0:y1, x0:x1] - cx, yy[y0:y1, x0:x1] - cy)
        drops[y0:y1, x0:x1] = np.maximum(drops[y0:y1, x0:x1], np.clip(r + 0.5 - sub, 0, 1) * 0.9)
    starlight = np.clip(stars + drops, 0, 1)[..., None]
    rgb = rgb * (1 - starlight) + hexrgb('#f4f7ef') * starlight
    return np.clip(rgb, 0, 1)


# --------------------------------------------------------------------------------------------------
# The lens mapping.
# --------------------------------------------------------------------------------------------------
def lens_map():
    yy, xx = np.mgrid[0:H, 0:W].astype(float) + 0.5
    tx, ty = xx - LX, yy - LY
    r2 = np.maximum(tx ** 2 + ty ** 2, 1e-6)
    k = 1 - TE ** 2 / r2
    return tx, ty, tx * k, ty * k                                  # theta, beta (pixels)


def lensed(texture, bx, by):
    """Sample the padded source-plane texture along the deflected rays."""
    coords = [by + LY + PAD, bx + LX + PAD]
    out = np.empty((H, W, 3))
    for c in range(3):
        out[..., c] = ndimage.map_coordinates(texture[..., c], coords, order=1, mode='mirror')
    return out


# --------------------------------------------------------------------------------------------------
# Ink: ripples around the source, drawn in the source plane and seen through the lens.
# --------------------------------------------------------------------------------------------------
def ripple_levels():
    """Ripple radii and widths in Einstein radii: spacing and width grow outward."""
    rho, out = 0.31, []          # the first ripple encloses the source but not the lens
    while rho < 9.0:
        width = 0.075 + 0.048 * rho
        out.append((rho, width))
        rho += 0.34 + 0.21 * rho
    return out


def ink_layer(rng, dist, grad_x, grad_y, scale):
    """Black bands with hatched, furry edges. `dist` is the source-plane distance from the source,
    in Einstein radii, at every pixel; ticks are drawn on a 2x canvas and downsampled."""
    ss = 2
    canvas = Image.new('L', (W * ss, H * ss), 0)
    draw = ImageDraw.Draw(canvas)
    bands = np.zeros((H, W))
    gmag = np.hypot(grad_x, grad_y) + 1e-9
    # brush pressure: each band swells and thins along its length
    press = 1 + 0.24 * noise(rng, (H, W), 150)
    xs, ys = np.arange(W) + 0.5, np.arange(H) + 0.5

    for rho, width in ripple_levels():
        s = (dist - rho) / press                      # band coordinate, with the width modulated
        edge_px = (width / 2 - np.abs(s)) * press / gmag
        bands = np.maximum(bands, np.clip(edge_px + 0.5, 0, 1))
        gen = contourpy.contour_generator(xs, ys, s)
        for level, sign, longest in ((width / 2, +1, 9.0), (-width / 2, -1, 5.0)):
            for path in gen.lines(level):
                if len(path) < 4:
                    continue
                seg = np.hypot(*np.diff(path, axis=0).T)
                s = np.concatenate([[0], np.cumsum(seg)])
                if s[-1] < 6:
                    continue
                step = rng.uniform(3.4, 3.9)
                pts = np.arange(rng.uniform(0, step), s[-1], step)
                px = np.interp(pts, s, path[:, 0])
                py = np.interp(pts, s, path[:, 1])
                ix = np.clip(px.astype(int), 0, W - 1)
                iy = np.clip(py.astype(int), 0, H - 1)
                nx, ny = grad_x[iy, ix] / gmag[iy, ix], grad_y[iy, ix] / gmag[iy, ix]
                # the band's own width on the image sets the scale of its fur
                local = np.clip(width / gmag[iy, ix], 1.0, 60.0)
                length = longest * np.clip(local / 14.0, 0.25, 1.6) * rng.uniform(0.75, 1.1, pts.size)
                length *= 0.8 + 0.4 * np.sin(pts / rng.uniform(30, 70)) ** 2   # rhythm
                jit = rng.normal(0, 0.07, pts.size)
                dx = sign * (nx * np.cos(jit) - ny * np.sin(jit))
                dy = sign * (nx * np.sin(jit) + ny * np.cos(jit))
                lws = np.maximum(1, np.rint(ss * np.clip(local / 10.0, 0.8, 1.5))).astype(int)
                for x0, y0, ddx, ddy, L, lw in zip(px, py, dx, dy, length, lws):
                    draw.line([((x0 - ddx * 1.5) * ss, (y0 - ddy * 1.5) * ss),
                               ((x0 + ddx * L) * ss, (y0 + ddy * L) * ss)],
                              fill=255, width=int(lw))
    fur = np.asarray(canvas.resize((W, H), Image.LANCZOS), dtype=float) / 255.0
    return np.clip(np.maximum(bands, fur), 0, 1)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('-o', '--out', default='img/microlensing-cartoon.jpg')
    ap.add_argument('--seed', type=int, default=7)
    args = ap.parse_args()
    rng = np.random.default_rng(args.seed)

    tx, ty, bx, by = lens_map()
    r = np.hypot(tx, ty)

    # 1. the lensed sky
    img = lensed(source_sky(rng), bx, by)

    # 2. distance from the source star in the source plane, in Einstein radii, with a hand-drawn wobble
    sxp, syp = U0[0] * TE, U0[1] * TE
    dist = np.hypot(bx - sxp, by - syp) / TE
    wob = noise(rng, (H, W), 14)
    distw = dist * (1 + 0.004 * wob) + 0.002 * wob
    gy, gx = np.gradient(distw)

    # 3. teal washes beside each ripple, the colour between the cartoon's ink bands
    wash = np.zeros((H, W))
    for rho, width in ripple_levels():
        t = (distw - rho - width / 2) / (0.14 + 0.05 * rho)
        wash = np.maximum(wash, np.where(t > 0, np.exp(-t * 2.2) * (1 - np.exp(-t * 14)), 0))
    teal = hexrgb('#4fb7b2')
    wa = (0.55 * wash)[..., None]
    img = img * (1 - wa) + (img * 0.35 + teal * 0.65) * wa

    # 4. the source star's two images, in flat watercolour yellow with a soft highlight
    srcmask = np.clip((RS - dist) / 0.012, 0, 1)
    shade = np.clip(1 - np.hypot(bx - sxp + 0.05 * TE, by - syp + 0.06 * TE) / (RS * TE * 1.25), 0, 1)
    yel = hexrgb('#cfd03c') * (1 - shade[..., None] * 0.6) + hexrgb('#f3f19a') * shade[..., None] * 0.6
    img = img * (1 - srcmask[..., None]) + yel * srcmask[..., None]

    # the Einstein ring, as a faint dashed line under the ink
    phi = np.arctan2(ty, tx)
    dash = (np.sin(phi * 60) > 0.15) & (np.abs(r - TE) < 1.3)
    img[dash] = img[dash] * 0.45 + hexrgb('#e6f4ee') * 0.55
    # 5. the ink
    ink = ink_layer(rng, distw, gx, gy, TE)
    ink *= np.clip((r / TE - RBH) / 0.02, 0, 1)                    # nothing drawn over the hole
    ink *= 1 - srcmask
    ink = np.maximum(ink, np.clip(1 - np.abs(dist - RS - 0.012) / 0.009, 0, 1) * 0.9)   # outline
    img = img * (1 - 0.97 * ink[..., None]) + INK * 0.97 * ink[..., None]

    # 6. glow of the images (screen blend)
    glow = ndimage.gaussian_filter(srcmask, 14) * 1.3 + ndimage.gaussian_filter(srcmask, 55) * 1.4
    glowcol = hexrgb('#f1ec8a')
    g = np.clip(glow, 0, 1)[..., None] * 0.8
    img = 1 - (1 - img) * (1 - glowcol * g)

    # 7. the black hole: an ink disc with a thin pale rim
    hole = np.clip((RBH * TE - r) / 1.5, 0, 1)[..., None]
    rim = np.exp(-0.5 * ((r - RBH * TE - 2.5) / 1.6) ** 2)[..., None] * 0.55
    img = img * (1 - rim) + hexrgb('#cfe9e4') * rim
    img = img * (1 - hole) + hexrgb('#040508') * hole

    # 8. paper: a gentle vignette and grain
    vy, vx = (np.mgrid[0:H, 0:W] / np.array([H, W])[:, None, None]) - 0.5
    vig = 1 - 0.35 * np.clip(np.hypot(vx * 1.1, vy * 1.3) - 0.22, 0, 1) ** 1.4
    grain = 1 + 0.025 * ndimage.gaussian_filter(rng.standard_normal((H, W)), 0.7)
    img = np.clip(img * (vig * grain)[..., None], 0, 1)

    Image.fromarray((img * 255).astype(np.uint8)).save(args.out, quality=93, subsampling=0)
    print('wrote', args.out)


if __name__ == '__main__':
    main()
