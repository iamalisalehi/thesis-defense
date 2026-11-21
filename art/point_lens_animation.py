"""Animate the geometry and observables of the seminar's off-axis example."""

from pathlib import Path

import numpy as np

from point_lens_curves import FLUX_COLOR, SHIFT_COLOR, U0, point_lens_observables

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.lines import Line2D


def image_geometry(time, magnification):
    """Return the source, image positions, image fluxes and observed centroid."""
    source = np.array([time, U0])
    separation = np.linalg.norm(source)
    direction = source / separation
    image_distances = (separation + np.array([1, -1]) * np.sqrt(separation**2 + 4)) / 2
    positions = image_distances[:, None] * direction
    fluxes = (magnification + np.array([1, -1])) / 2
    centroid = np.average(positions, axis=0, weights=fluxes)
    return source, positions, fluxes, centroid


def main():
    times = np.linspace(-3.0, 3.0, 65)
    curve_times = np.linspace(-3.0, 3.0, 601)
    magnification, shift = point_lens_observables(curve_times)
    plt.rcParams.update({"font.size": 13, "mathtext.fontset": "dejavusans", "pdf.fonttype": 42})
    fig = plt.figure(figsize=(12, 4.4))
    sky = fig.add_axes([0.06, 0.22, 0.46, 0.65])
    photometry = fig.add_axes([0.61, 0.58, 0.36, 0.27])
    astrometry = fig.add_axes([0.61, 0.16, 0.36, 0.27], sharex=photometry)

    sky.set(title="Two images on the sky", xlim=(-3.5, 3.5), ylim=(-1.5, 1.5),
            xticks=[-3, -2, -1, 0, 1, 2, 3], yticks=[-1, 0, 1],
            xlabel=r"Sky offset / $\theta_{\rm E}$")
    sky.set_aspect("equal", adjustable="box")
    sky.set_facecolor("#f6f8fb")
    sky.grid(color="#e4e9ef", linewidth=0.8)
    sky.axhline(U0, color="#717a86", linestyle="--", linewidth=1.4)
    sky.set_axisbelow(True)
    sky.scatter(0, 0, marker="x", s=70, color="#202934", linewidths=2)
    images = sky.scatter([0, 0], [0, 0], color="#be641e", alpha=0.95, zorder=4, linewidths=0)
    source_marker = sky.scatter(0, 0, s=47, facecolors="white", edgecolors="#525e69",
                                linewidths=1.6, zorder=5)
    centroid_marker, = sky.plot([], [], "D", markersize=6, markeredgecolor="white",
                                markeredgewidth=0.7, color=SHIFT_COLOR, zorder=6)
    shift_segment, = sky.plot([], [], linewidth=1.5, color=SHIFT_COLOR, zorder=5)

    fig.legend(handles=[
        Line2D([], [], marker="x", color="#202934", linestyle="none", label="Dark lens"),
        Line2D([], [], marker="o", markerfacecolor="white", markeredgecolor="#525e69",
               linestyle="none", label="Unlensed source"),
        Line2D([], [], marker="o", color="#be641e", linestyle="none", label="Images"),
        Line2D([], [], marker="D", color=SHIFT_COLOR, linestyle="none", label="Centroid"),
    ], loc="lower left", bbox_to_anchor=(0.047, 0.035), ncols=4, frameon=False,
        fontsize=11, handletextpad=0.28, handlelength=1.3, columnspacing=0.85)

    photometry.set(title="Photometry · summed image flux", ylabel="Magnification",
                   ylim=(0.95, 3.25), yticks=[1, 2, 3])
    photometry.tick_params(labelbottom=False)
    astrometry.set(title="Astrometry · centroid shift", ylabel=r"Shift / $\theta_{\rm E}$",
                   ylim=(0, 0.42), yticks=[0, 0.2, 0.4],
                   xlabel=r"Time from closest approach / $t_{\rm E}$")
    panels = (
        (photometry, magnification, FLUX_COLOR),
        (astrometry, shift, SHIFT_COLOR),
    )
    cursors = []
    for axis, curve, color in panels:
        axis.set(xlim=(-3, 3), xticks=[-3, -2, -1, 0, 1, 2, 3])
        axis.spines[["right", "top"]].set_visible(False)
        axis.grid(axis="y", color="#e4e9ef")
        axis.plot(curve_times, curve, color=color, linewidth=2.4)
        line = axis.axvline(0, color="#717a86", linestyle=":", linewidth=1.2)
        dot, = axis.plot([], [], "o", color=color, markersize=7, markeredgecolor="white")
        cursors.append((line, dot))

    output = Path(__file__).resolve().parents[1] / "img" / "sim" / "point_lens_animation.pdf"
    with PdfPages(output) as pdf:
        for time, flux, displacement in zip(times, *point_lens_observables(times), strict=True):
            source, positions, fluxes, centroid = image_geometry(time, flux)
            images.set_offsets(positions)
            images.set_sizes(115 * fluxes)
            source_marker.set_offsets(source)
            centroid_marker.set_data([centroid[0]], [centroid[1]])
            shift_segment.set_data([source[0], centroid[0]], [source[1], centroid[1]])
            for (line, dot), observable in zip(cursors, (flux, displacement), strict=True):
                line.set_xdata([time, time])
                dot.set_data([time], [observable])
            pdf.savefig(fig)
    plt.close(fig)


if __name__ == "__main__":
    main()
