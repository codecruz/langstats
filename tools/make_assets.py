#!/usr/bin/env python3
"""Generate the images used when the project is shared: Open Graph card, GitHub
social preview, square post image and icons.

    python3 tools/make_assets.py

Needs Google Chrome or Chromium (headless) to render, and Pillow to check the
sizes. The output goes to docs/assets/. The bars come from make_bar, so the
images show the same block the plugin writes.
"""

from __future__ import annotations

import html
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "assets"
sys.path.insert(0, str(ROOT / "scripts"))

from langstats import make_bar  # noqa: E402

ROWS = [("Python", 41.62), ("TypeScript", 24.10), ("Go", 14.35), ("PHP", 9.80), ("Rust", 6.03)]
TITLE = "Your languages, from the code Claude writes with you"
SUBTITLE = "A Claude Code plugin that turns them into text bars for your GitHub profile README."
URL = "codecruz.github.io/langstats"

# The same palette as docs/index.html (light theme).
BG = "#fbfaf7"
SURFACE = "#ffffff"
TEXT = "#1d1c1a"
MUTED = "#63605a"
BORDER = "#e4e1da"
ACCENT = "#b4446c"
CODE_BG = "#f3f1ec"
MONO = '"DejaVu Sans Mono", "Ubuntu Mono", ui-monospace, monospace'
SANS = '"Ubuntu Sans", "Noto Sans", system-ui, sans-serif'

# The icon: three bars of a stats block on the accent colour.
ICON_SVG = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <rect width="64" height="64" rx="14" fill="{ACCENT}"/>
  <rect x="13" y="16" width="38" height="8" rx="2" fill="#fff"/>
  <rect x="13" y="28" width="26" height="8" rx="2" fill="#fff" fill-opacity=".8"/>
  <rect x="13" y="40" width="15" height="8" rx="2" fill="#fff" fill-opacity=".6"/>
</svg>
"""


def block(bar_length: int) -> str:
    lines = []
    for name, percent in ROWS:
        bar = make_bar(percent, bar_length, "bars")
        lines.append("%s%s   %05.2f %%" % (name.ljust(12), bar, percent))
    return html.escape("\n".join(lines))


def card_page(width: int, height: int, square: bool) -> str:
    pad = 72 if not square else 80
    if square:
        layout = "flex-direction: column; justify-content: center; gap: 56px; padding-bottom: 24px;"
        text_w, title_px, sub_px, code_px, bar_len = "100%", 64, 28, 25, 22
    else:
        layout = "flex-direction: row; align-items: center; gap: 56px;"
        text_w, title_px, sub_px, code_px = "47%", 50 if width < 1250 else 54, 23, 17 if width < 1250 else 18
        bar_len = 16
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
  * {{ box-sizing: border-box; margin: 0; }}
  html, body {{ width: {width}px; height: {height}px; overflow: hidden; }}
  body {{ background: {BG}; color: {TEXT}; font-family: {SANS}; position: relative; }}
  body::before {{ content: ""; position: absolute; inset: 0 0 auto 0; height: 10px; background: {ACCENT}; }}
  .main {{ position: absolute; inset: {pad}px; display: flex; {layout} }}
  .text {{ width: {text_w}; flex: none; }}
  .brand {{ display: flex; align-items: center; gap: 14px; font: 600 30px {MONO}; margin-bottom: 30px; }}
  .brand svg {{ width: 44px; height: 44px; }}
  h1 {{ font-size: {title_px}px; line-height: 1.12; letter-spacing: -0.02em; font-weight: 700; }}
  p {{ font-size: {sub_px}px; line-height: 1.45; color: {MUTED}; margin-top: 22px; }}
  .card {{ flex: {"none" if square else "1"}; background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 18px; overflow: hidden;
          box-shadow: 0 18px 40px -24px rgba(29, 28, 26, .35); }}
  .head {{ display: flex; gap: 8px; padding: 14px 18px; border-bottom: 1px solid {BORDER}; }}
  .head i {{ width: 12px; height: 12px; border-radius: 50%; background: {BORDER}; }}
  pre {{ font: {code_px}px/1.75 {MONO}; padding: 24px 26px; background: {CODE_BG}; white-space: pre; }}
  .url {{ position: absolute; left: {pad}px; bottom: {pad // 2 - 6}px; font: 20px {MONO}; color: {MUTED}; }}
  .url b {{ color: {ACCENT}; font-weight: 600; }}
</style></head><body>
  <div class="main">
    <div class="text">
      <div class="brand">{ICON_SVG}langstats</div>
      <h1>{html.escape(TITLE)}</h1>
      <p>{html.escape(SUBTITLE)}</p>
    </div>
    <div class="card"><div class="head"><i></i><i></i><i></i></div><pre>{block(bar_len)}</pre></div>
  </div>
  <div class="url"><b>→</b> {URL}</div>
</body></html>"""


def icon_page(size: int) -> str:
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
  * {{ margin: 0; }} html, body {{ width: {size}px; height: {size}px; overflow: hidden; background: transparent; }}
  svg {{ display: block; width: {size}px; height: {size}px; }}
</style></head><body>{ICON_SVG}</body></html>"""


def find_chrome() -> str:
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome"):
        path = shutil.which(name)
        if path:
            return path
    sys.exit("Google Chrome or Chromium is needed to render the images.")


def render(chrome: str, page: str, out: Path, width: int, height: int, tmp: Path) -> None:
    src = tmp / (out.stem + ".html")
    src.write_text(page, encoding="utf-8")
    subprocess.run(
        [chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
         "--default-background-color=00000000", f"--window-size={width},{height}",
         f"--screenshot={out}", src.as_uri()],
        check=True, capture_output=True,
    )


def main() -> None:
    from PIL import Image

    chrome = find_chrome()
    OUT.mkdir(parents=True, exist_ok=True)
    jobs = [
        ("og-image.png", card_page(1200, 630, False), 1200, 630),
        ("social-preview.png", card_page(1280, 640, False), 1280, 640),
        ("square.png", card_page(1080, 1080, True), 1080, 1080),
        ("apple-touch-icon.png", icon_page(180), 180, 180),
        ("icon-192.png", icon_page(192), 192, 192),
        ("icon-512.png", icon_page(512), 512, 512),
    ]
    with tempfile.TemporaryDirectory() as tmp:
        for name, page, width, height in jobs:
            out = OUT / name
            render(chrome, page, out, width, height, Path(tmp))
            with Image.open(out) as img:
                if img.size != (width, height):
                    sys.exit("%s is %dx%d, expected %dx%d" % (name, *img.size, width, height))
                if name.startswith(("og-", "social-", "square")):
                    img.convert("RGB").save(out, optimize=True)
            print("%-22s %dx%d" % (name, width, height))
    (OUT / "icon.svg").write_text(ICON_SVG, encoding="utf-8")
    print("icon.svg")


if __name__ == "__main__":
    main()
