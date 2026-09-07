#!/usr/bin/env python3
"""Make closed terrain solids from the committed viewer height fields.

From the repository root:
    uv run --project printing --locked printing/build.py

No scans, DEM downloads, or viewer rebuilds needed.
See README.md in this directory for dimensions, provenance, and limitations.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape, quoteattr
import zipfile

import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from assemble_all import SHEETS

NS = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
STL_DTYPE = np.dtype([("normal", "<f4", (3,)), ("vertices", "<f4", (3, 3)),
                      ("attribute", "<u2")])


def positive(value):
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError("must be a finite number greater than zero")
    return number


def decode_height(path, meta):
    """Same 12-bit R/G decoding as src/app1.js; B is a boundary, not height."""
    with Image.open(path) as image:
        rgb = np.asarray(image.convert("RGB"), dtype=np.uint16)
    expected = (meta["hm"]["h"], meta["hm"]["w"], 3)
    if rgb.shape != expected:
        raise ValueError(f"{path}: expected {expected}, found {rgb.shape}")
    lo, hi = float(meta["hmin"]), float(meta["hmax"])
    if not (math.isfinite(lo) and math.isfinite(hi) and hi >= lo):
        raise ValueError("invalid elevation range")
    if np.any(rgb[:, :, 1] & 15):
        raise ValueError("height image is not lossless 12-bit R/G packing")
    q = (rgb[:, :, 0] << 4) | (rgb[:, :, 1] >> 4)
    return lo + q.astype(np.float64) * ((hi - lo) / 4095)


def sample_terrain(height, width_mm, depth_mm, pitch_mm):
    """Low-pass before decimation, then sample the raster's pixel-centre grid.

    The outer mesh vertices are exactly on the geographic grid edges. Heights
    there clamp to the nearest pixel centre, matching the viewer sampler.
    """
    nx = max(2, math.ceil(width_mm / pitch_mm) + 1)
    ny = max(2, math.ceil(depth_mm / pitch_mm) + 1)
    if nx * ny > 2_000_000:
        raise ValueError("mesh exceeds 2 million vertices; increase --pitch-mm")
    h, w = height.shape
    sigma = (max(0, h / (ny - 1) - 1) * 0.35,
             max(0, w / (nx - 1) - 1) * 0.35)
    filtered = ndimage.gaussian_filter(height, sigma, mode="nearest")
    y, x = np.meshgrid(np.linspace(-0.5, h - 0.5, ny),
                       np.linspace(-0.5, w - 0.5, nx), indexing="ij")
    return ndimage.map_coordinates(filtered, [y, x], order=1, mode="nearest")


def solid_mesh(z, width_mm, depth_mm):
    """A height-field graph plus boundary walls and a downward bottom fan.

    Raster row zero is grid north (+Y); X increases east; Z points upward.
    Shared boundary indices avoid cracks, T-junctions and coincident shells.
    """
    z = np.asarray(z, dtype=np.float64)
    if z.ndim != 2 or min(z.shape) < 2 or not np.isfinite(z).all() or z.min() <= 0:
        raise ValueError("top must be a finite positive height grid of at least 2 by 2")
    if not all(math.isfinite(v) and v > 0 for v in (width_mm, depth_mm)):
        raise ValueError("footprint dimensions must be finite and positive")
    ny, nx = z.shape
    x, y = np.meshgrid(np.linspace(0, width_mm, nx),
                       np.linspace(depth_mm, 0, ny))
    top = np.column_stack((x.ravel(), y.ravel(), z.ravel()))
    ids = np.arange(nx * ny).reshape(ny, nx)
    a, b = ids[:-1, :-1].ravel(), ids[:-1, 1:].ravel()
    c, d = ids[1:, :-1].ravel(), ids[1:, 1:].ravel()
    faces_top = np.concatenate((np.column_stack((a, c, b)),
                                np.column_stack((b, c, d))))
    # Counterclockwise outline viewed from above, with each corner once.
    edge = np.concatenate((ids[:, 0], ids[-1, 1:], ids[-2::-1, -1], ids[0, -2:0:-1]))
    bottom = top[edge].copy()
    bottom[:, 2] = 0
    lower = np.arange(len(top), len(top) + len(edge))
    next_top, next_lower = np.roll(edge, -1), np.roll(lower, -1)
    center = len(top) + len(edge)
    faces_wall = np.concatenate((np.column_stack((edge, lower, next_lower)),
                                 np.column_stack((edge, next_lower, next_top))))
    faces_bottom = np.column_stack((np.full(len(edge), center), next_lower, lower))
    vertices = np.vstack((top, bottom, [[width_mm / 2, depth_mm / 2, 0]]))
    faces = np.vstack((faces_top, faces_wall, faces_bottom)).astype(np.int32)
    return vertices, faces


def validate_mesh(vertices, faces):
    """Fail closed on bad indices, open edges, winding, degeneracy or volume."""
    if not np.isfinite(vertices).all() or faces.min() < 0 or faces.max() >= len(vertices):
        raise ValueError("invalid vertices or face indices")
    triangles = vertices[faces]
    crosses = np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])
    if np.any(np.linalg.norm(crosses, axis=1) <= 1e-10):
        raise ValueError("degenerate triangles")
    directed = np.concatenate((faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]))
    edge_ids = np.sort(directed, axis=1).astype(np.int64)
    keys = edge_ids[:, 0] * len(vertices) + edge_ids[:, 1]
    _, inverse, counts = np.unique(keys, return_inverse=True, return_counts=True)
    if np.any(counts != 2):
        raise ValueError("mesh is not watertight: each edge must belong to two faces")
    orientation = np.where(directed[:, 0] < directed[:, 1], 1, -1)
    if np.any(np.bincount(inverse, weights=orientation)):
        raise ValueError("inconsistent face winding")
    if len(np.unique(faces)) != len(vertices) or len(vertices) - len(counts) + len(faces) != 2:
        raise ValueError("unexpected topology")
    volume = float(np.einsum("ij,ij->i", triangles[:, 0], crosses).sum() / 6)
    if volume <= 0:
        raise ValueError("inside-out mesh or nonpositive volume")
    return dict(watertight=True, consistent_winding=True, euler_number=2,
                degenerate_faces=0, vertices=len(vertices), triangles=len(faces),
                volume_mm3=round(volume, 5))


def write_stl(path, vertices, faces, slug):
    triangles = vertices[faces].astype("<f4")
    normal = np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])
    normal /= np.linalg.norm(normal, axis=1)[:, None]
    records = np.zeros(len(faces), dtype=STL_DTYPE)
    records["normal"], records["vertices"] = normal, triangles
    header = f"old-time-maps {slug}; millimeters; +Y grid north; +Z up".encode("ascii")
    with path.open("wb") as stream:
        stream.write(header[:80].ljust(80, b"\0"))
        stream.write(struct.pack("<I", len(faces)))
        records.tofile(stream)


def zip_entry(archive, name, content):
    """Fixed metadata makes repeated exports byte-identical in one environment."""
    info = zipfile.ZipInfo(name, (2020, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    archive.writestr(info, content, compresslevel=6)


def write_3mf(path, vertices, faces, title, description):
    xml = [f'<?xml version="1.0" encoding="UTF-8"?>\n'
           f'<model unit="millimeter" xml:lang="en-US" xmlns="{NS}">\n',
           f'<metadata name="Title">{escape(title)}</metadata>\n',
           '<metadata name="Application">old-time-maps printing/build.py</metadata>\n',
           f'<metadata name="Description">{escape(description)}</metadata>\n',
           f'<resources><object id="1" type="model" name={quoteattr(title)}><mesh><vertices>\n']
    xml.extend(f'<vertex x="{x:.6f}" y="{y:.6f}" z="{z:.6f}"/>\n' for x, y, z in vertices)
    xml.append('</vertices><triangles>\n')
    xml.extend(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>\n' for a, b, c in faces)
    xml.append('</triangles></mesh></object></resources><build><item objectid="1"/></build></model>\n')
    with zipfile.ZipFile(path, "w") as archive:
        zip_entry(archive, "[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8"?>'
                  '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                  '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                  '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
                  '</Types>')
        zip_entry(archive, "_rels/.rels", '<?xml version="1.0" encoding="UTF-8"?>'
                  '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                  '<Relationship Id="rel0" Target="/3D/3dmodel.model" '
                  'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
        zip_entry(archive, "3D/3dmodel.model", "".join(xml))


def verify_exports(stl_path, mf_path, vertices, faces):
    """Re-read both on-disk formats; check that serialization kept the solid."""
    with stl_path.open("rb") as stream:
        stream.read(80)
        count = struct.unpack("<I", stream.read(4))[0]
        records = np.fromfile(stream, dtype=STL_DTYPE)
    if count != len(faces) or len(records) != count or stl_path.stat().st_size != 84 + count * 50:
        raise ValueError("invalid binary STL length")
    if not np.array_equal(records["vertices"], vertices[faces].astype("<f4")):
        raise ValueError("STL changed geometry")
    welded, inverse = np.unique(records["vertices"].reshape(-1, 3), axis=0, return_inverse=True)
    validate_mesh(welded.astype(np.float64), inverse.reshape(-1, 3))
    with zipfile.ZipFile(mf_path) as archive:
        if archive.testzip():
            raise ValueError("corrupt 3MF ZIP")
        model = ET.fromstring(archive.read("3D/3dmodel.model"))
    if model.get("unit") != "millimeter":
        raise ValueError("3MF must declare millimeters")
    mesh = model.find(f"{{{NS}}}resources/{{{NS}}}object/{{{NS}}}mesh")
    out_vertices = np.array([[float(v.get(k)) for k in ("x", "y", "z")]
                             for v in mesh.find(f"{{{NS}}}vertices")])
    out_faces = np.array([[int(f.get(k)) for k in ("v1", "v2", "v3")]
                          for f in mesh.find(f"{{{NS}}}triangles")])
    if not np.array_equal(out_faces, faces) or not np.allclose(out_vertices, vertices, atol=5.1e-7, rtol=0):
        raise ValueError("3MF changed geometry")
    validate_mesh(out_vertices, out_faces)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def export_sheet(sheet, args):
    slug = sheet["d"]
    assets = ROOT / slug / "assets"
    meta = json.loads((assets / "meta.json").read_text())
    kmw, kmh = float(meta["kmw"]), float(meta["kmh"])
    if not all(math.isfinite(v) and v > 0 for v in (kmw, kmh)):
        raise ValueError(f"{slug}: invalid geographic extent")
    mm_per_m = args.size_mm / (max(kmw, kmh) * 1000)
    width, depth = kmw * 1000 * mm_per_m, kmh * 1000 * mm_per_m
    exag = args.exaggeration or float(meta.get("ui", {}).get("exagDef", 5.0))
    if not math.isfinite(exag) or exag <= 0:
        raise ValueError(f"{slug}: invalid vertical exaggeration")
    elevation = decode_height(assets / "height.webp", meta)
    sampled = sample_terrain(elevation, width, depth, args.pitch_mm)
    # Keep the lowest printable terrain at the specified base thickness.
    datum = float(sampled.min())
    z = args.base_mm + (sampled - datum) * mm_per_m * exag
    vertices, faces = solid_mesh(z, width, depth)
    checks = validate_mesh(vertices, faces)
    model_dir = args.output / "models"
    model_dir.mkdir(parents=True, exist_ok=True)
    stl, mf = model_dir / f"{slug}.stl", model_dir / f"{slug}.3mf"
    description = (f"{width:.3f} x {depth:.3f} x {z.max():.3f} mm; "
                   f"{args.base_mm:g} mm minimum base; {exag:g}x vertical exaggeration. "
                   "Modern terrain from committed height.webp; full rectangular viewer grid. "
                   "Historical map ink and labels are not embossed. +Y is grid north, +Z is up. "
                   f"Source and homeland history: {slug}/src/body.html About panel.")
    write_stl(stl, vertices, faces, slug)
    write_3mf(mf, vertices, faces, sheet["title"], description)
    verify_exports(stl, mf, vertices, faces)
    record = dict(sheet=slug, title=sheet["title"], dimensions_mm=[round(v, 6) for v in (width, depth, z.max())],
                  base_mm=args.base_mm, exaggeration=exag, horizontal_scale_denominator=round(1000 / mm_per_m, 3),
                  geographic_extent_km=[kmw, kmh], source_elevation_range_m=[float(elevation.min()), float(elevation.max())],
                  sampled_elevation_range_m=[datum, float(sampled.max())],
                  elevation_datum_m=datum, mesh_grid=[z.shape[1], z.shape[0]],
                  mesh_spacing_mm=[width / (z.shape[1] - 1), depth / (z.shape[0] - 1)],
                  source_height=f"{slug}/assets/height.webp", source_height_sha256=sha256(assets / "height.webp"),
                  source_meta=f"{slug}/assets/meta.json", source_meta_sha256=sha256(assets / "meta.json"),
                  about=f"{slug}/src/body.html", description=description, checks=checks,
                  files={p.suffix[1:]: dict(path=f"models/{p.name}", bytes=p.stat().st_size, sha256=sha256(p)) for p in (stl, mf)})
    print(f"{slug:13s} {width:6.1f} x {depth:6.1f} x {z.max():5.1f} mm  "
          f"{exag:g}x  {len(faces):,} faces  STL + 3MF verified", flush=True)
    return record


def write_catalog(output, records):
    lines = ["# Terrain print catalog", "", "All dimensions are millimeters: east–west × north–south × total height.",
             "Each file is a separate model. See [printing instructions](README.md).", "",
             "| Map | Dimensions (mm) | Vertical exaggeration | Files |",
             "|---|---|---|---|"]
    for r in records:
        dims = " × ".join(f"{v:.1f}" for v in r["dimensions_mm"])
        slug = r["sheet"]
        lines.append(f'| {r["title"]} | {dims} | {r["exaggeration"]:g}× | '
                     f'[3MF](models/{slug}.3mf) · [STL](models/{slug}.stl) |')
    (output / "CATALOG.md").write_text("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sheet", action="append", help="one terrain sheet slug; repeat to select several")
    parser.add_argument("--size-mm", type=positive, default=180, help="longest footprint side (default: 180)")
    parser.add_argument("--base-mm", type=positive, default=3, help="minimum solid thickness (default: 3)")
    parser.add_argument("--pitch-mm", type=positive, default=0.5, help="maximum XY mesh spacing (default: 0.5)")
    parser.add_argument("--exaggeration", type=positive, help="override each sheet's viewer exaggeration; 1 = true scale")
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    terrain = [s for s in SHEETS if s["d"] != "art"]
    # A missing asset is an error, never a reason to silently omit a map.
    if args.sheet:
        unknown = set(args.sheet) - {s["d"] for s in terrain}
        if unknown:
            parser.error("unknown terrain sheet(s): " + ", ".join(sorted(unknown)))
        terrain = [s for s in terrain if s["d"] in args.sheet]
    args.output.mkdir(parents=True, exist_ok=True)
    records = [export_sheet(sheet, args) for sheet in terrain]
    manifest = dict(format_version=1, units="millimeter", footprint="full rectangular viewer grid",
                    orientation="X east, Y grid north, Z up; bottom at Z=0", size_mm=args.size_mm,
                    base_mm=args.base_mm, maximum_mesh_spacing_mm=args.pitch_mm,
                    terrain_only=True, excluded=dict(art="Flat Wing illustrations have no elevation grids"),
                    models=records)
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    write_catalog(args.output, records)
    print(f"Wrote {len(records)} terrain models to {args.output}", flush=True)


if __name__ == "__main__":
    main()
