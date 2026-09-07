#!/usr/bin/env python3
"""Package the default models, sources, documentation and optional previews.

From the repository root:
    uv run --project printing --locked printing/package.py
"""
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import zipfile

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


class AboutText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.skip = False
        self.parts = []
        self.href = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "div" and (self.depth or attrs.get("id") == "info"):
            self.depth += 1
        if not self.depth:
            return
        if tag == "button":
            self.skip = True
        if tag in ("p", "h2", "h3", "li", "br", "tr", "dt"):
            self.parts.append("\n\n")
        if tag in ("td", "dd"):
            self.parts.append(": ")
        if tag == "a":
            self.href = attrs.get("href")

    def handle_data(self, data):
        if self.depth and not self.skip:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if not self.depth:
            return
        if tag == "a" and self.href:
            self.parts.append(f" ({self.href})")
            self.href = None
        if tag == "button":
            self.skip = False
        if tag in ("p", "h2", "h3", "li"):
            self.parts.append("\n\n")
        if tag == "div":
            self.depth -= 1

    def paragraphs(self):
        return [" ".join(p.split()) for p in "".join(self.parts).split("\n\n") if p.strip()]


def main():
    manifest = json.loads((HERE / "manifest.json").read_text())
    records = manifest["models"]
    assert len(records) == 25 and manifest["size_mm"] == 180, "package.py bundles the default collection"
    source_lines = ["# The maps' sources and history", "",
                    "The following text is copied from each map viewer's existing About panel.",
                    "It describes the historical sheets and viewer pipelines. The printable models",
                    "use the modern terrain only; print scale and sampling are documented separately",
                    "in README.md and manifest.json. External links are retained in parentheses.", ""]
    for r in records:
        parser = AboutText()
        parser.feed((ROOT / r["about"]).read_text())
        paragraphs = parser.paragraphs()
        assert sum(map(len, paragraphs)) > 300, f"Missing About text for {r['sheet']}"
        source_lines += [f"## {r['title']}", "", f"Source: `{r['about']}`", "", "\n\n".join(paragraphs), ""]
    (HERE / "SOURCES.md").write_text("\n".join(source_lines))
    previews = [HERE / "previews" / f"{r['sheet']}.png" for r in records]
    if all(p.exists() for p in previews):
        cw, ch, margin, header = 400, 334, 24, 120
        sheet = Image.new("RGB", (margin * 2 + cw * 5, header + margin + ch * 5), "#f3f0ea")
        draw = ImageDraw.Draw(sheet)
        font = ImageFont.load_default(size=16)
        small = ImageFont.load_default(size=14)
        title = ImageFont.load_default(size=33)
        draw.text((margin, 22), "OLD TIME MAPS / 25 TERRAIN PRINTS", font=title, fill="#302d27")
        draw.text((margin, 73), "180 mm maximum footprint · 3 mm base · STL + 3MF · rendered from the exported solids",
                  font=font, fill="#696154")
        for i, (r, preview) in enumerate(zip(records, previews)):
            x, y = margin + i % 5 * cw, header + i // 5 * ch
            with Image.open(preview) as im:
                sheet.paste(im.convert("RGB").resize((400, 285), Image.Resampling.LANCZOS), (x, y))
            draw.text((x + 12, y + 281), r["sheet"].upper(), font=font, fill="#302d27")
            dims = " x ".join(f"{v:.1f}" for v in r["dimensions_mm"])
            draw.text((x + 12, y + 304), f"{dims} mm   /   {r['exaggeration']:g}x relief", font=small, fill="#696154")
        sheet.save(HERE / "preview.jpg", quality=93)
    names = ["README.md", "CATALOG.md", "SOURCES.md", "manifest.json"]
    for name in ["validation.json", "preview.jpg"]:
        if (HERE / name).exists():
            names.append(name)
    for r in records:
        for f in r["files"].values():
            path = HERE / f["path"]
            assert hashlib.sha256(path.read_bytes()).hexdigest() == f["sha256"], f"Stale export: {path}"
            names.append(f["path"])
    destination = HERE / "old-time-maps-180mm.zip"
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name in names:
            info = zipfile.ZipInfo(f"old-time-maps-180mm/{name}", (2020, 1, 1, 0, 0, 0))
            info.external_attr = 0o644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, (HERE / name).read_bytes())
    with zipfile.ZipFile(destination) as archive:
        assert archive.testzip() is None
        assert len([n for n in archive.namelist() if n.endswith((".stl", ".3mf"))]) == 50
    print(f"Packaged 50 model files, source notes and catalog: {destination} ({destination.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
