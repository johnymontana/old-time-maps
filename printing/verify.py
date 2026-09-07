#!/usr/bin/env python3
"""Independent checks using trimesh and the 3MF Consortium's reference reader.

From the repository root:
    uv run --project printing --locked --group qa printing/verify.py
"""
import argparse
import hashlib
import json
from pathlib import Path

import lib3mf
import numpy as np
import trimesh


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    manifest = json.loads((args.directory / "manifest.json").read_text())
    wrapper = lib3mf.get_wrapper()
    reports = []
    for record in manifest["models"]:
        for f in record["files"].values():
            data = (args.directory / f["path"]).read_bytes()
            assert len(data) == f["bytes"]
            assert hashlib.sha256(data).hexdigest() == f["sha256"]
        mesh = trimesh.load_mesh(args.directory / record["files"]["stl"]["path"], process=True)
        assert mesh.is_watertight and mesh.is_winding_consistent and mesh.is_volume
        assert mesh.body_count == 1 and mesh.euler_number == 2
        assert len(mesh.faces) == record["checks"]["triangles"]
        assert np.allclose(mesh.bounds[0], [0, 0, 0], atol=1e-5)
        assert np.allclose(mesh.extents, record["dimensions_mm"], atol=2e-5)
        assert np.max(mesh.extents[:2]) <= manifest["size_mm"] + 2e-5
        assert np.isclose(mesh.volume, record["checks"]["volume_mm3"], rtol=1e-6)
        bottom_faces = mesh.vertices[mesh.faces][:, :, 2] == 0
        assert np.any(np.all(bottom_faces, axis=1))
        # A slice through the solid base must recover the complete rectangle.
        base_section = trimesh.intersections.mesh_plane(mesh, [0, 0, 1], [0, 0, record["base_mm"] / 2])
        length = np.linalg.norm(base_section[:, 1] - base_section[:, 0], axis=1).sum()
        assert np.isclose(length, 2 * sum(record["dimensions_mm"][:2]), rtol=1e-6)
        model = wrapper.CreateModel()
        reader = model.QueryReader("3mf")
        reader.SetStrictModeActive(True)
        reader.ReadFromFile(str(args.directory / record["files"]["3mf"]["path"]))
        assert reader.GetWarningCount() == 0
        assert model.GetUnit() == lib3mf.ModelUnit.MilliMeter
        obj = model.GetMeshObjectByID(1)
        assert obj.IsValid() and obj.IsManifoldAndOriented()
        assert obj.GetVertexCount() == record["checks"]["vertices"]
        assert obj.GetTriangleCount() == len(mesh.faces)
        assert model.GetBuildItems().Count() == 1
        reports.append(dict(sheet=record["sheet"], stl_single_body=True, stl_positive_volume=True,
                            stl_watertight=True, base_slice_perimeter_mm=round(float(length), 6),
                            mf_strict_reader_warnings=0, mf_manifold_and_oriented=True,
                            dimensions_mm=mesh.extents.tolist()))
        print(f'{record["sheet"]}: one watertight solid; base slice correct; strict 3MF: zero warnings', flush=True)
    output = dict(trimesh_version=trimesh.__version__, lib3mf_version=list(wrapper.GetLibraryVersion()),
                  models=reports, physical_print_tested=False)
    (args.directory / "validation.json").write_text(json.dumps(output, indent=2) + "\n")
    print(f"Verified all {len(reports)} models", flush=True)


if __name__ == "__main__":
    main()
