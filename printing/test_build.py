"""Geometry and encoding checks, run from the repository root:

uv run --project printing --locked python -m unittest discover -s printing -v
"""
from pathlib import Path
import tempfile
import unittest
from argparse import ArgumentTypeError, Namespace

import numpy as np
from PIL import Image

from build import (decode_height, sample_terrain, solid_mesh, validate_mesh,
                   write_stl, write_3mf, verify_exports, export_sheet, positive)


class TerrainPrintTests(unittest.TestCase):
    def test_all_4096_elevation_codes_and_boundary_channel(self):
        q = np.arange(4096, dtype=np.uint16).reshape(64, 64)
        rgb = np.dstack((q >> 4, (q & 15) << 4, q % 256)).astype(np.uint8)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "height.webp"
            Image.fromarray(rgb).save(path, lossless=True)
            meta = dict(hm=dict(w=64, h=64), hmin=-200, hmax=3895)
            np.testing.assert_array_equal(decode_height(path, meta), q.astype(float) - 200)

    def test_prism_has_expected_volume_and_closed_bottom(self):
        for shape in [(2, 2), (3, 5), (7, 3)]:
            v, f = solid_mesh(np.full(shape, 3.0), 40, 25)
            self.assertAlmostEqual(validate_mesh(v, f)["volume_mm3"], 3000)
            np.testing.assert_allclose(v.min(axis=0), [0, 0, 0])
            np.testing.assert_allclose(v.max(axis=0), [40, 25, 3])

    def test_north_south_and_sloping_volume(self):
        z = np.array([[8, 8, 8], [4, 4, 4], [2, 2, 2]], dtype=float)
        v, f = solid_mesh(z, 12, 20)
        self.assertEqual(v[0, 1], 20)
        self.assertEqual(v[6, 1], 0)
        self.assertAlmostEqual(validate_mesh(v, f)["volume_mm3"], 12 * 10 * (6 + 3))

    def test_sampler_clamps_pixel_centres_without_mirroring(self):
        height = np.array([[12, 14], [2, 4]], dtype=float)
        sampled = sample_terrain(height, 10, 10, 5)
        np.testing.assert_allclose(sampled, [[12, 13, 14], [7, 8, 9], [2, 3, 4]])

    def test_sampling_flat_land_and_resolution_limit(self):
        np.testing.assert_allclose(sample_terrain(np.full((100, 80), -30.), 18, 12, 0.5), -30)
        with self.assertRaisesRegex(ValueError, "2 million"):
            sample_terrain(np.ones((10, 10)), 180, 180, 0.001)

    def test_detects_open_mesh_and_reversed_face(self):
        v, f = solid_mesh(np.full((3, 4), 3.), 10, 10)
        with self.assertRaisesRegex(ValueError, "watertight"):
            validate_mesh(v, f[:-1])
        bad = f.copy()
        bad[0] = bad[0, ::-1]
        with self.assertRaisesRegex(ValueError, "winding"):
            validate_mesh(v, bad)
        with self.assertRaisesRegex(ValueError, "inside-out"):
            validate_mesh(v, f[:, ::-1])

    def test_invalid_parameters_and_heights(self):
        for number in ["nan", "inf", "-1", "0"]:
            with self.assertRaises(ArgumentTypeError):
                positive(number)
        for z in [np.zeros((2, 2)), np.full((2, 2), np.nan), np.ones((1, 3))]:
            with self.assertRaises(ValueError):
                solid_mesh(z, 10, 10)

    def test_formats_round_trip_and_determinism(self):
        v, f = solid_mesh(np.array([[3.1, 9.7], [4.2, 7.9]]), 180, 123.123456)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            stl, mf = root / "test.stl", root / "test.3mf"
            write_stl(stl, v, f, "test")
            write_3mf(mf, v, f, 'Title & "quotes"', "Description < > &")
            verify_exports(stl, mf, v, f)
            original = mf.read_bytes()
            write_3mf(mf, v, f, 'Title & "quotes"', "Description < > &")
            self.assertEqual(original, mf.read_bytes())

    def test_real_map_dimensions_and_millimeters_per_meter(self):
        with tempfile.TemporaryDirectory() as folder:
            record = export_sheet(dict(d="kilauea", title="Test"), Namespace(
                size_mm=180, base_mm=3, pitch_mm=10, exaggeration=1, output=Path(folder)))
            self.assertAlmostEqual(max(record["dimensions_mm"][:2]), 180, places=5)
            lo, hi = record["sampled_elevation_range_m"]
            expected = 3 + (hi - lo) * 180 / (1000 * max(record["geographic_extent_km"]))
            self.assertAlmostEqual(record["dimensions_mm"][2], expected, places=5)


if __name__ == "__main__":
    unittest.main()
