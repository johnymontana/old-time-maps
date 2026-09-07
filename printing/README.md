# Print the terrain

**25 terrain maps, each fitting within 180 × 180 mm.** Open an individual
3MF from [the catalog](CATALOG.md) in your slicer, select your printer and
filament, and slice with the flat base on the bed. STL copies are included;
import those in **millimeters**. The models are separate objects, one per
file, ready to arrange on your printer's build plate.

Every model has a 3 mm minimum base, closed vertical walls and a flat
underside at Z = 0. The footprint retains the map grid's proportions; its
longest side is 180 mm. The 0.5 mm maximum mesh spacing balances terrain
detail and file size. Each uses the sheet's initial viewer exaggeration
(1.4–5×), recorded in the catalog. The two horizontal axes use the same
scale. +X is east, +Y is **grid north** in the sheet's conic projection,
and +Z is up. The shape is designed to print base-down without supports.
Leave room on the build plate if your slicer adds a brim or skirt.

These are **terrain models**: the historical ink, colours, roads and place
labels remain in the map viewers. Each solid covers the full rectangular
elevation grid, including the surrounding terrain and water shown by the
viewer. The blue channel's state/park/map outline is a display mask; it
does not cut the printable footprint. Alternate historical layers use the
same terrain, so each sheet needs one solid. Gold and Rails have identical
terrain assets and therefore identical geometry, supplied under both names.
The Flat Wing's 21 illustrations have no elevation grids and are excluded.

The files contain modern terrain, not a reconstruction of elevation at the
map's publication date. Coastlines and lake surfaces follow the committed
DEM; there is no added underwater relief. Small peaks are softened by the
height raster and the print mesh's sampling. Printing a model has not been
physically tested here. These are model files, not printer-specific G-code
or saved slicer profiles.

## Files

- [CATALOG.md](CATALOG.md): dimensions, exaggeration and individual downloads.
- `models/<sheet>.3mf`: compressed geometry with millimeter units.
- `models/<sheet>.stl`: binary STL containing the same solid.
- [manifest.json](manifest.json): source hashes, model hashes, scales,
  sampled elevation ranges, mesh sizes and validation results.
- [SOURCES.md](SOURCES.md): the existing About panels, including map sources
  and the specific homeland and history notes for each sheet.
- [validation.json](validation.json): independent checks with trimesh and
  the 3MF Consortium's strict reference reader; all 25 models pass.
- `preview.jpg`: an overview rendered from the exported STL models.
- `old-time-maps-180mm.zip`: a convenience bundle of the models and documentation.
  The bundle can be regenerated and is excluded from Git to avoid duplicating
  the committed model files.

## Download from the web app

Every terrain card in the gallery has 3MF and STL download links. Each
map viewer also has a **3D print this map** disclosure in its controls,
with dimensions, base thickness, vertical exaggeration and file sizes.

`python3 assemble_all.py` includes both model files in each served map's
`models/` directory. Assembling a single sheet also includes its downloads.
The build reads the print manifest and fails if a model is missing or has
the wrong byte size. It uses only the standard library; generating new
terrain models remains a separate uv command.

The one-file HTML builds link to `../printing/models/` inside the repository.
Keep that sibling directory when using those download links from disk.
The models are separate downloads and are not embedded in the HTML.

## Rebuild or change the size

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then
run these commands from the repository root:

```sh
uv sync --project printing --locked
uv run --project printing --locked printing/build.py
uv run --project printing --locked python -m unittest discover -s printing -v
```

`printing/pyproject.toml` declares the dependencies and Python requirement
(3.10 or later). `printing/uv.lock` records the resolved package versions.
uv creates and manages `printing/.venv`, using a compatible Python already
installed or downloading one when needed. No environment activation is
required. `uv run` also syncs the environment automatically; the explicit
`uv sync` command is useful for preparing it in advance. `--locked` checks
that the dependency declarations and lockfile agree.

For the independent format checks, include the `qa` dependency group.
Packaging uses the base dependencies:

```sh
uv run --project printing --locked --group qa printing/verify.py
uv run --project printing --locked printing/package.py
```

To prepare the environment with the QA tools ahead of time, use
`uv sync --project printing --locked --group qa`.

`--project printing` selects the printing environment while keeping paths
relative to your current directory. If working inside `printing/`, omit
`--project printing` and the `printing/` prefix on script paths. For
example, `uv run --locked build.py --help` displays the exporter options.

The builder reads only committed `assets/height.webp` and `assets/meta.json`.
It discovers the terrain sheets from `assemble_all.SHEETS`; a missing asset
fails the build instead of silently omitting a sheet. It does not rebuild
the map pipelines or fetch terrain.

Write custom sizes into a separate directory so the default catalog stays
consistent. For example, a 150 mm Yellowstone with true-scale relief:

```sh
uv run --project printing --locked printing/build.py --sheet yellowstone --size-mm 150 --exaggeration 1 --output work/print-yellowstone
```

`--base-mm` changes the minimum solid thickness. `--pitch-mm` changes the
maximum distance between terrain vertices. `--sheet` can be repeated;
each run writes a catalog and manifest for just that selection.

## Manage dependencies

Use `uv add --project printing <package>` and
`uv remove --project printing <package>` to change runtime dependencies.
Add `--group qa` for a validation dependency. These commands update both
`pyproject.toml` and `uv.lock`; keep both files in version control.
`printing/.venv` is already excluded by the repository's `.gitignore`.

To upgrade the locked versions deliberately, then install and check them:

```sh
uv lock --project printing --upgrade
uv sync --project printing --locked --group qa
uv run --project printing --locked python -m unittest discover -s printing -v
uv run --project printing --locked --group qa printing/verify.py
```

See uv's [project guide](https://docs.astral.sh/uv/guides/projects/) for
environment and lockfile management.

## Geometry and validation

The builder decodes the same 12-bit R/G elevation as `lib/encode.py` and
the viewer, applies a small Gaussian filter before decimation, and samples
at the geographic grid edges with pixel-centre clamping. It subtracts the
lowest sampled elevation to set the minimum base thickness. Height above
that base is `(elevation - sampled minimum) × horizontal mm per meter ×
vertical exaggeration`. The sampled datum and scale are in the manifest.

The top, walls and bottom share vertices in one closed shell. Validation
checks finite coordinates, nonzero triangle areas, paired edges,
consistent outward winding, Euler characteristic 2 and positive volume.
Both on-disk exports are re-read and checked after writing. The STL check
welds identical vertices before checking topology. 3MF packaging follows
the [3MF Consortium's core specification](https://github.com/3MFConsortium/spec_core/blob/master/3MF%20Core%20Specification.md).

## Sources and history

The elevation comes from the repository's Terrarium-based terrain
pipelines. Source metadata and height rasters are identified by path and
SHA-256 in the manifest. Reuse each sheet's existing About panel for its
map sources, registration residuals and the specific Indigenous homeland,
treaty, removal and dispossession history of the land it depicts. Those
panels are part of the provenance of this collection; the printable shape
adds no new geographic or historical claims.
