# Ph.D. seminar: isolated black holes with Roman and Rubin

Beamer slides for a ~30-minute Ph.D. seminar at Isfahan University of Technology,
*Detecting Isolated Black Holes through Gravitational Microlensing with Next-Generation Telescopes*
(supervisor Dr. Sedighe Sajadian, advisor Dr. Hamed Bakhshian), with backup slides after the summary.
Made with the template by [Johannes Dorfner](https://github.com/ojdo), first used for my M.Sc. defense
(branch `master`).

## Build

```bash
latexmk -pdf seminar.tex
```

Slides are in `tex/` (one file per section, `08_backup.tex` for the backup slides); figures in `img/`.

- The slide "A lens crossing a star" is an in-PDF animation (`animate` package). It plays in Adobe
  Reader and Okular; other viewers show its Einstein-ring frame.
- References and image credits sit on each slide in small grey text, linked to NASA ADS.

## Generated figures

```bash
python art/lensing_animation.py      # img/anim/frame_00.jpg ... frame_80.jpg
python art/microlensing_well.py      # img/microlensing-well.jpg (closing slide)
python art/microlensing_cartoon.py   # img/microlensing-cartoon.jpg (earlier, face-on alternative)
```

All three need numpy, scipy, matplotlib and Pillow. The animation re-renders the reverse ray tracer
`microlens_movie.c` (point lens crossing a limb-darkened star) and measures the magnification and the
centroid shift from the traced images. The closing image ray-casts a sheet of spacetime sinking into a
black hole's well, drawn as hatched ink bands, with a background star seen as its two lensed arcs; the
earlier face-on version ray-traces a watercolour bulge sky and ink ripples through a point lens.

Speaker notes: every slide carries `\note{...}` with the details cut from the slide; `seminar.tex` says
how to show them.
