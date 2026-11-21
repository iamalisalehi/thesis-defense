"""Point-source observables for the off-axis example in the seminar."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


U0 = 0.35  # Closest approach in units of the angular Einstein radius.
FLUX_COLOR = "#9c4c14"
SHIFT_COLOR = "#235b91"


def point_lens_observables(time):
    """Return total magnification and centroid shift magnitude for this trajectory."""
    separation = np.hypot(U0, time)
    magnification = (separation**2 + 2) / (separation * np.sqrt(separation**2 + 4))
    shift = separation / (separation**2 + 2)
    return magnification, shift


def main():
    time = np.linspace(-4.0, 4.0, 801)  # Units of the Einstein crossing time.
    magnification, shift = point_lens_observables(time)

    plt.rcParams.update({"font.size": 12, "mathtext.fontset": "dejavusans"})
    fig, (photometry, astrometry) = plt.subplots(2, 1, figsize=(5.6, 4.0), sharex=True)
    fig.subplots_adjust(left=0.16, bottom=0.14, right=0.97, top=0.97, hspace=0.22)

    photometry.plot(time, magnification, color=FLUX_COLOR, linewidth=2.5)
    photometry.set(ylim=(0.95, 3.3), yticks=[1, 2, 3], ylabel="Magnification")
    photometry.annotate(rf"closest approach $(u_0={U0:g})$", (0, magnification.max()),
                        xytext=(0.55, 2.7), fontsize=10,
                        arrowprops={"arrowstyle": "-", "color": "#555555"})

    astrometry.plot(time, shift, color=SHIFT_COLOR, linewidth=2.5)
    astrometry.set(ylim=(0.0, 0.42), yticks=[0, 0.2, 0.4],
                   ylabel=r"Shift / $\theta_{\rm E}$",
                   xlabel=r"Time from closest approach in units of $t_{\rm E}$")
    astrometric_peak = np.sqrt(2 - U0**2)
    astrometry.scatter([-astrometric_peak, astrometric_peak], [1 / np.sqrt(8)] * 2,
                       s=20, color=SHIFT_COLOR, zorder=3)

    for axis in (photometry, astrometry):
        axis.axvline(0, linestyle=":", color="#77818a", linewidth=1)
        axis.set(xlim=(-4, 4), xticks=[-4, -2, 0, 2, 4])
        axis.spines[["top", "right"]].set_visible(False)
        axis.grid(axis="y", color="#e0e5e9")

    output = Path(__file__).resolve().parents[1] / "img" / "sim" / "point_lens_curves.pdf"
    fig.savefig(output)


if __name__ == "__main__":
    main()
