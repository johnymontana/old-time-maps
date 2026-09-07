"""Static download integration checks; run with the printing test suite."""
from html.parser import HTMLParser
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from assemble_all import SHEETS, gallery
from lib.print_downloads import copy_models, load_catalog, viewer_downloads


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.anchor_depth = 0
        self.nested = False

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.nested |= self.anchor_depth > 0
            self.anchor_depth += 1
            self.links.append(dict(attrs))

    def handle_endtag(self, tag):
        if tag == "a":
            self.anchor_depth -= 1


class DownloadTests(unittest.TestCase):
    def test_gallery_has_two_downloads_per_terrain_card_and_no_nested_anchors(self):
        models = load_catalog()
        self.assertEqual(set(models), {s["d"] for s in SHEETS if s["d"] != "art"})
        page = Links()
        page.feed(gallery(models))
        self.assertFalse(page.nested)
        downloads = [a for a in page.links if "download" in a]
        self.assertEqual(len(downloads), 2 * len(models))
        self.assertEqual({a["href"] for a in downloads},
                         {f"{slug}/models/{slug}.{kind}" for slug in models for kind in ("3mf", "stl")})
        self.assertTrue(all("aria-label" in a for a in downloads))
        self.assertTrue(any(a["href"] == "art/" for a in page.links))

    def test_individual_and_repository_builds_use_their_own_relative_paths(self):
        record = load_catalog()["flathead"]
        for served, prefix in ((True, "models/"), (False, "../printing/models/")):
            body = viewer_downloads("<section><!-- PRINT_DOWNLOADS --></section>", record, served)
            page = Links()
            page.feed(body)
            self.assertEqual({a["href"] for a in page.links},
                             {f"{prefix}flathead.3mf", f"{prefix}flathead.stl"})
            self.assertNotIn("<!-- PRINT_DOWNLOADS -->", body)
            self.assertIn("3D print this map", body)
            self.assertIn("3 mm base", body)
        with self.assertRaisesRegex(ValueError, "exactly one"):
            viewer_downloads("<section></section>", record, True)

    def test_copy_and_reject_missing_or_truncated_download(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "printing"
            (source / "models").mkdir(parents=True)
            record = {"sheet": "test", "files": {}}
            for kind in ("3mf", "stl"):
                data = f"test {kind}".encode()
                relative = f"models/test.{kind}"
                (source / relative).write_bytes(data)
                record["files"][kind] = {"path": relative, "bytes": len(data)}
            (source / "manifest.json").write_text(json.dumps({"models": [record]}))
            loaded = load_catalog(source)["test"]
            copy_models(loaded, root / "dist", source)
            for file in record["files"].values():
                self.assertEqual((source / file["path"]).read_bytes(),
                                 (root / "dist" / file["path"]).read_bytes())
            (source / "models/test.stl").write_bytes(b"short")
            with self.assertRaisesRegex(ValueError, "incomplete"):
                load_catalog(source)
            (source / "models/test.stl").unlink()
            with self.assertRaisesRegex(ValueError, "Missing"):
                load_catalog(source)


if __name__ == "__main__":
    unittest.main()
