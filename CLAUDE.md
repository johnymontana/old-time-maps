# CLAUDE.md

Read [AGENTS.md](AGENTS.md) before making changes. It is the authoritative
source for project instructions, quality gates and Git conventions.

The project currently has 25 terrain viewers, 25 printable terrain models
in both STL and 3MF, and the Flat Wing's 21 illustrations. Use
`assemble_all.SHEETS` as the inventory and keep the print manifest complete.

- Public-domain sources only; automated georeferencing, honest residuals,
  and specific Indigenous history in each sheet's About panel and tours.
- Commit generated map assets, one-file HTML and printing outputs. Caches,
  environments, `dist/` and printing ZIP bundles are gitignored.
- Shared viewer changes start in `flathead/src` and propagate to the other
  v2 sheets. Port changes to the diverged `montana/src` by hand.
- Website assembly uses `python3 assemble_all.py` with the standard library.
  Printing uses the locked uv project in `printing/`; keep its dependencies
  out of the website build. Download UI and copying live in
  `lib/print_downloads.py`.
- Follow the QA gates in AGENTS.md. Pushes, PRs and deployments require the
  maintainer's explicit request.

See [README.md](README.md#rebuilding) for setup and serving, and
[printing/README.md](printing/README.md) for uv commands, model regeneration,
validation, custom sizes and packaging. The dated memos in `docs/` are
research history; their proposed work is not necessarily the current state.
