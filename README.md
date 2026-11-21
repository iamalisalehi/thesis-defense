# Ph.D. seminar on isolated black holes with Roman and Rubin

A 30-minute seminar at Isfahan University of Technology, *Detecting Isolated Black Holes through
Gravitational Microlensing with Next-Generation Telescopes*. Supervisor Dr. Sedighe Sajadian,
advisor Dr. Hamed Bakhshian. The Beamer theme is based on [Johannes Dorfner's template](https://github.com/ojdo).

The scientific endpoint is the first overview report and the Ph.D. proposal. The preliminary results
come from the September 24–25, 2026 simulations and the first overview's subsequent extinction
analysis. The proposal section presents the planned research at that milestone.

## Build and present

Run `latexmk -pdf seminar.tex` from this directory. Main slides are in `tex/00_overview.tex` through
`tex/07_closing.tex`. The backup slides start after the closing slide. In Beamer, a reveal occupies
a separate PDF page and keeps the same slide number.

| Elapsed | Main topic |
| --- | --- |
| 0–3 min | Motivation and research question |
| 3–11 min | Microlensing and the Hubble case |
| 11–14 min | Roman and Rubin |
| 14–19 min | Simulation, precision forecast and example event |
| 19–27 min | September results and limitations |
| 27–30 min | Proposal and summary |

Speaker notes add detail to the main results and worked examples. To print them or show them on a
second screen, see the Beamer options near the top of `seminar.tex`. Use the Hubble, Roman, Rubin
and Milky Way photo slides as short transitions within the same 30 minutes.

Slide 8 animates the off-axis event used in the theory slides. It starts automatically in a PDF
viewer that supports Beamer's `animate` package, such as Okular or Adobe Acrobat Reader. Each loop
takes about 6.5 seconds. The static poster shows the geometry at closest approach alongside both
complete curves. The appendix retains the central-transit animation of an extended source.

## Scientific source trail

The Roman–Rubin project paths below identify the historical outputs used to audit the numbers and
labels. The effective sample sizes quoted for dust-adjusted Rubin fractions describe the underlying
sample before the dust adjustment.

| Slide content | Source |
| --- | --- |
| Main results and modelling assumptions | `Report/overview/overview_report.tex`, `Proposal/sections/06_preliminary.tex` |
| Dust-adjusted yields, fractions and uncertainty | `figures/u1_20260929/u5_corrected_numbers.md` |
| As-simulated fractions, selections and effective sample sizes | `figures/u1_20260929/u1_numbers.md` |
| Paired Earth/L2 forecast and Roman gap comparison | First overview, sections on satellite parallax and gap filling |
| Example black-hole light curves and centroid tracks | First overview sample gallery, `both_011` and `bh_short_b002` |
| Proposed thesis work | `Proposal/sections/10_plan.tex` |
| Hubble case study | [Sahu et al. 2022](https://ui.adsabs.harvard.edu/abs/2022ApJ...933...83S), [Lam & Lu 2023](https://arxiv.org/abs/2308.03302), [Sahu et al. 2025](https://arxiv.org/abs/2503.07820) |

The first overview's absolute yields use the per-resolved-object convention and Roman's
1.47-square-degree model footprint. The adopted survey covers about 1.7 square degrees. The
dust-adjusted values reweight detection and precision outcomes after simulation. The precision bars
use the as-simulated set of Roman forecasts for each parameter. The slide includes the effective
sample size, and the notes give the separately dust-adjusted mass fraction.

## Generated figures

```bash
python art/point_lens_curves.py      # analytic curves for the off-axis point lens
python art/point_lens_animation.py # animated geometry and observables for the same event
python art/lensing_animation.py     # reverse ray tracing of a finite-source central transit
python art/microlensing_well.py      # alternate closing art
python art/microlensing_cartoon.py   # alternate face-on art
```

The figure scripts use NumPy and Matplotlib. The ray-traced illustrations also use SciPy and Pillow.
References and credits are linked from their slides.
