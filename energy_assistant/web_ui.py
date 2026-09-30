from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILT_INDEX = ROOT / "frontend" / "dist" / "index.html"

# Serve the built React dashboard directly. This is the project UI with the
# light themed agent sections and data panels, not the temporary static fallback.
HTML = BUILT_INDEX.read_text(encoding="utf-8") if BUILT_INDEX.exists() else """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>GridSense AI</title>
  </head>
  <body>
    <h1>GridSense AI</h1>
    <p>Project frontend build missing.</p>
  </body>
</html>
"""
