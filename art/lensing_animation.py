"""Frames for the in-PDF animation of a point lens crossing a limb-darkened star.

The lensing model is the one in Ali's reverse ray tracer
(~/Documents/PhD/WD-WD/Reverse Ray Tracing/microlens_movie.c): a point lens with theta_E = 0.5
moves straight across a limb-darkened source disc (radius R = 0.3, linear limb darkening u = 0.6,
centred on the origin), and every image-plane ray theta is traced back to

    beta = theta - theta_E^2 (theta - theta_L) / |theta - theta_L|^2.

Here the same model is re-rendered with numpy, and the magnification and the shift of the light
centroid are measured from the ray-traced images themselves (total flux, and flux-weighted mean
position), so the two curves on the right are exactly what the left panel shows. The point-source
formulas are drawn for comparison.

    python art/lensing_animation.py [--frames 81] [-o img/anim]

writes frame_00.jpg ... frame_NN.jpg; the slide shows them with \\animategraphics (animate package).
"""
import argparse
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Circle

TE, R, I0, ULD = 0.5, 0.3, 1.0, 0.6           # microlens_movie.c
XL0, XL1 = -2.0, 2.0                          # lens path (the C code sweeps -2.5 .. 2.5)
VIEW = 1.35                                   # half-width of the displayed field
FLUXBOX = 2.8                                 # half-width of the field summed for the flux
STAR = LinearSegmentedColormap.from_list('star', [
    (0.00, '#07101f'), (0.45, '#4b2a19'), (0.66, '#b5651d'), (0.82, '#eab543'), (1.00, '#fff7dc')])
INKC, TEAL, ORANGE, BLUE = '#14171f', '#3a9a98', '#d0602a', '#2c5f9e'


def brightness(bx, by):
    r2 = (bx ** 2 + by ** 2) / R ** 2
    mu = np.sqrt(np.clip(1 - r2, 0, 1))
    return np.where(r2 < 1, I0 * (1 - ULD * (1 - mu)), 0.0)


def trace(xl, half, n):
    """Ray-trace an n x n grid of pixel centres over [-half, half]^2 with the lens at (xl, 0)."""
    c = (np.arange(n) + 0.5) / n * 2 * half - half
    tx, ty = np.meshgrid(c, c)
    rx, ry = tx - xl, ty
    r2 = np.maximum(rx ** 2 + ry ** 2, 1e-12)
    f = TE ** 2 / r2
    return tx, ty, brightness(tx - f * rx, ty - f * ry)


def measure(xl, n=2400):
    """Magnification and centroid shift (x, y), measured from the ray-traced image."""
    tx, ty, img = trace(xl, FLUXBOX, n)
    pix = (2 * FLUXBOX / n) ** 2
    flux = img.sum() * pix
    flux0 = np.pi * R ** 2 * I0 * (1 - ULD / 3)          # the unlensed disc
    return flux / flux0, (img * tx).sum() * pix / flux, (img * ty).sum() * pix / flux


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--frames', type=int, default=81)
    ap.add_argument('-o', '--outdir', default='img/anim')
    args = ap.parse_args()
    os.makedirs(args.outdir, exist_ok=True)

    xl = np.linspace(XL0, XL1, args.frames)
    tt = xl / TE                                          # time in units of t_E (lens moves theta_E per t_E)
    meas = np.array([measure(x) for x in xl])
    amp, cx = meas[:, 0], meas[:, 1] / TE
    tfine = np.linspace(tt[0], tt[-1], 2001)
    u = np.abs(tfine)
    a_ps = (u ** 2 + 2) / (u * np.sqrt(u ** 2 + 4))
    d_ps = -tfine / (u ** 2 + 2)                         # point source: away from the lens, theta_E u/(u^2+2)
    print('peak magnification (finite source): %.3f' % amp.max())

    plt.rcParams.update({'font.size': 15, 'font.family': 'DejaVu Sans', 'axes.linewidth': 1.0,
                         'mathtext.fontset': 'dejavusans'})
    for k, (x, t) in enumerate(zip(xl, tt)):
        fig = plt.figure(figsize=(12.0, 5.2), dpi=110)
        ax = fig.add_axes([0.005, 0.03, 0.40, 0.94])
        _, _, img = trace(x, VIEW, 660)
        ax.imshow(img ** (1 / 2.2), cmap=STAR, vmin=0, vmax=1, origin='lower',
                  extent=[-VIEW, VIEW, -VIEW, VIEW], interpolation='bilinear')
        ax.add_patch(Circle((0, 0), R, fill=False, ls=':', lw=1.0, color='w', alpha=0.45))
        ax.add_patch(Circle((x, 0), TE, fill=False, ls='--', lw=1.3, color='#8fd6d1', alpha=0.9))
        ax.add_patch(Circle((x, 0), 0.045, color='k', ec='#cfe9e4', lw=1.0, zorder=5))
        ax.plot(meas[k, 1], meas[k, 2], marker='+', ms=16, mew=2.2, color='#8fd6d1', zorder=6)
        ax.set_xlim(-VIEW, VIEW); ax.set_ylim(-VIEW, VIEW)
        ax.set_xticks([]); ax.set_yticks([])
        ax.text(-VIEW + 0.07, VIEW - 0.1, r'$t-t_0 = %+.2f\,t_{\rm E}$' % t, color='w', va='top', fontsize=15)
        ax.text(-VIEW + 0.07, -VIEW + 0.08, 'dashed: Einstein ring   dotted: the star unlensed   +: light centroid',
                color='#cfe9e4', fontsize=9.5, va='bottom')

        a1 = fig.add_axes([0.49, 0.56, 0.495, 0.40])
        a2 = fig.add_axes([0.49, 0.12, 0.495, 0.40], sharex=a1)
        a1.plot(tfine, a_ps, '--', color='0.55', lw=1.3, label='point source')
        a1.plot(tt, amp, color='0.82', lw=2.0)
        a1.plot(tt[:k + 1], amp[:k + 1], color=ORANGE, lw=2.8, label='this star (ray traced)')
        a1.plot(t, amp[k], 'o', color=ORANGE, ms=9, mec='k', mew=0.8)
        a1.set_ylim(0.85, 4.6); a1.set_ylabel('magnification $A$')
        a1.legend(loc='upper right', fontsize=11.5, frameon=False)
        a1.tick_params(labelbottom=False)
        a2.axhline(0, color='0.75', lw=0.8)
        a2.plot(tfine, d_ps, '--', color='0.55', lw=1.3)
        a2.plot(tt, cx, color='0.82', lw=2.0)
        a2.plot(tt[:k + 1], cx[:k + 1], color=BLUE, lw=2.8)
        a2.plot(t, cx[k], 'o', color=BLUE, ms=9, mec='k', mew=0.8)
        a2.set_ylim(-0.42, 0.42); a2.set_ylabel(r'centroid shift $\delta\theta_x/\theta_{\rm E}$')
        a2.set_xlabel(r'time $(t-t_0)/t_{\rm E}$'); a2.set_xlim(tt[0], tt[-1])
        for a in (a1, a2):
            a.grid(alpha=0.25); a.spines[['top', 'right']].set_visible(False)
        fig.savefig(os.path.join(args.outdir, 'frame_%02d.jpg' % k), dpi=110,
                    pil_kwargs={'quality': 88})
        plt.close(fig)
    print('wrote %d frames to %s' % (args.frames, args.outdir))


if __name__ == '__main__':
    main()
