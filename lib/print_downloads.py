"""Static print download UI and asset copying; standard library only."""
from html import escape
import json
from pathlib import Path
import shutil

PRINTING = Path(__file__).resolve().parents[1] / "printing"
MARKER = "<!-- PRINT_DOWNLOADS -->"


def load_catalog(directory=PRINTING):
    """Fail the site build if a promised download is missing or incomplete."""
    directory = Path(directory)
    records = json.loads((directory / "manifest.json").read_text())["models"]
    catalog = {}
    for record in records:
        slug = record["sheet"]
        if slug in catalog:
            raise ValueError(f"Duplicate printable map: {slug}")
        for kind in ("3mf", "stl"):
            file = record["files"][kind]
            expected = f"models/{slug}.{kind}"
            if file["path"] != expected:
                raise ValueError(f"Unexpected print model path: {file['path']}")
            path = directory / expected
            if not path.is_file() or path.stat().st_size != file["bytes"]:
                raise ValueError(f"Missing or incomplete print model: {path}. Run printing/build.py with uv.")
        catalog[slug] = record
    return catalog


def copy_models(record, destination, directory=PRINTING):
    destination = Path(destination) / "models"
    destination.mkdir(parents=True, exist_ok=True)
    for file in record["files"].values():
        source = Path(directory) / file["path"]
        shutil.copyfile(source, destination / source.name)


def download_links(record, prefix):
    links = []
    for kind in ("3mf", "stl"):
        file = record["files"][kind]
        filename = Path(file["path"]).name
        size = f"{file['bytes'] / 1e6:.1f} MB"
        label = f"Download {record['title']} as {kind.upper()} ({size})"
        links.append(f'<a class="print-file" href="{escape(prefix + filename, quote=True)}" '
                     f'download="{escape(filename, quote=True)}" aria-label="{escape(label, quote=True)}">'
                     f'{kind.upper()} <span>{size}</span></a>')
    return '<div class="print-files">' + "".join(links) + '</div>'


def viewer_downloads(body, record, served):
    if body.count(MARKER) != 1:
        raise ValueError("Map body must contain exactly one print downloads marker")
    prefix = "models/" if served else "../printing/models/"
    dimensions = " × ".join(f"{v:.1f}" for v in record["dimensions_mm"])
    block = ('<details class="print-downloads">'
             '<summary>3D print this map</summary>'
             f'<p class="print-size">{dimensions} mm<br>'
             f'{record["base_mm"]:g} mm base · {record["exaggeration"]:g}× relief</p>'
             + download_links(record, prefix)
             + '<p class="print-note">Print flat-side down. Terrain relief only; '
               'map colors and labels are not included.</p></details>')
    return body.replace(MARKER, block)


def gallery_downloads(record):
    return ('<div class="card-downloads">'
            '<span class="print-label">3D print</span>'
            + download_links(record, f'{record["sheet"]}/models/') + '</div>')


DOWNLOAD_CSS = """
/* Printable terrain downloads */
.print-downloads{margin-top:10px;border-top:1px solid var(--line);padding-top:6px}
.print-downloads summary{padding:6px 0;cursor:pointer;color:var(--accent);font-size:12px}
.print-downloads summary:hover{color:var(--paper)}
.print-size,.print-note{font-size:11px;line-height:1.55;color:var(--muted);margin:6px 0 9px}
.print-note{margin-bottom:0}
.print-files{display:flex;flex-wrap:wrap;gap:7px}
.print-file{display:inline-flex;align-items:center;justify-content:center;gap:7px;
  border:1px solid var(--line);border-radius:3px;padding:8px 10px;
  font-size:11px;line-height:1.4;color:var(--accent);text-decoration:none}
.print-file span{color:var(--muted);font-size:10px}
.print-file:hover{border-color:var(--accent);background:rgba(111,179,205,.08)}
.print-file:focus-visible,.print-downloads summary:focus-visible{
  outline:2px solid var(--accent);outline-offset:3px}
.card-downloads{border-top:1px solid var(--line2);padding:12px 18px 15px}
.print-label{display:block;margin-bottom:7px;font-size:9px;letter-spacing:.14em;
  text-transform:uppercase;color:var(--muted)}
"""
