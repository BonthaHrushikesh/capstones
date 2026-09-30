"""Render the architecture SVG sheets as a multi-page vector PDF using Python stdlib."""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SVG_PATH = ROOT / "project-architecture.svg"
PDF_PATH = ROOT / "project-architecture.pdf"
SVG_PAGES = [ROOT / name for name in (
    "project-architecture.svg",
    "analytics-engine.svg",
    "assistant-workflow.svg",
)]
SVG_NS = "{http://www.w3.org/2000/svg}"
SCALE = 0.6


def pdf_color(value: str | None, operator: str) -> str:
    if not value or value == "none":
        return ""
    value = value.lstrip("#")
    if len(value) != 6:
        return ""
    channels = [int(value[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return " ".join(f"{channel:.3f}" for channel in channels) + f" {operator}"


def css_classes(root: ET.Element) -> dict[str, dict[str, str]]:
    style = root.find(f"{SVG_NS}defs/{SVG_NS}style")
    rules: dict[str, dict[str, str]] = {}
    if style is None or not style.text:
        return rules
    for selector, body in re.findall(r"\.([\w-]+)\s*\{([^}]*)\}", style.text):
        rules[selector] = dict(
            (key.strip(), value.strip())
            for key, value in (item.split(":", 1) for item in body.split(";") if ":" in item)
        )
    return rules


def svg_points(path_data: str) -> list[tuple[float, float]]:
    tokens = re.findall(r"[A-Za-z]|-?\d+(?:\.\d+)?", path_data)
    points: list[tuple[float, float]] = []
    command = ""
    x = y = 0.0
    i = 0
    while i < len(tokens):
        if tokens[i].isalpha():
            command = tokens[i]
            i += 1
            continue
        if command == "M" or command == "L":
            x, y = float(tokens[i]), float(tokens[i + 1])
            i += 2
            points.append((x, y))
        elif command == "H":
            x = float(tokens[i])
            i += 1
            points.append((x, y))
        elif command == "V":
            y = float(tokens[i])
            i += 1
            points.append((x, y))
        else:
            raise ValueError(f"Unsupported SVG path command {command!r}: {path_data}")
    return points


def safe_pdf_text(text: str) -> str:
    text = text.replace("→", "->").replace("–", "-").replace("—", "-")
    encoded = text.encode("cp1252", errors="replace").decode("cp1252")
    return encoded.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def approximate_text_width(text: str, font_size: float) -> float:
    narrow = set(" ilI.,:;!'|`")
    wide = set("MW@%&")
    total = 0
    for char in text:
        if char == " ":
            total += 278
        elif char in narrow:
            total += 250
        elif char in wide:
            total += 820
        elif char.isupper() or char.isdigit():
            total += 590
        else:
            total += 500
    return total / 1000 * font_size


def render_svg(svg_path: Path) -> tuple[bytes, float, float]:
    root = ET.parse(svg_path).getroot()
    width = float(root.attrib["width"])
    height = float(root.attrib["height"])
    rules = css_classes(root)
    page_width, page_height = width * SCALE, height * SCALE
    stream: list[str] = []

    def style_for(element: ET.Element) -> dict[str, str]:
        classes = element.attrib.get("class", "").split()
        style: dict[str, str] = {}
        for name in classes:
            style.update(rules.get(name, {}))
        for prop in ("fill", "stroke", "stroke-width", "font-size", "font-weight"):
            if prop in element.attrib:
                style[prop] = element.attrib[prop]
        return style

    def py(y: float) -> float:
        return page_height - y * SCALE

    for element in root.iter():
        tag = element.tag.removeprefix(SVG_NS)
        if tag == "rect":
            style = style_for(element)
            x, y = float(element.attrib.get("x", 0)), float(element.attrib.get("y", 0))
            w, h = float(element.attrib["width"]), float(element.attrib["height"])
            stream.extend(["q", pdf_color(style.get("fill"), "rg"), pdf_color(style.get("stroke"), "RG")])
            stream.append(f"{float(style.get('stroke-width', 1)) * SCALE:.2f} w")
            stream.append(f"{x*SCALE:.2f} {py(y+h):.2f} {w*SCALE:.2f} {h*SCALE:.2f} re")
            stream.append("B" if style.get("stroke") and style.get("fill") != "none" else "f")
            stream.append("Q")
        elif tag == "path" and element.attrib.get("d"):
            style = style_for(element)
            points = svg_points(element.attrib["d"])
            if len(points) < 2:
                continue
            stream.extend(["q", pdf_color(style.get("stroke"), "RG"), f"{float(style.get('stroke-width', 1)) * SCALE:.2f} w"])
            commands = [f"{points[0][0]*SCALE:.2f} {py(points[0][1]):.2f} m"]
            commands.extend(f"{x*SCALE:.2f} {py(y):.2f} l" for x, y in points[1:])
            commands.append("S")
            stream.extend(commands)
            # Draw an arrowhead aligned to the final segment.
            (x1, y1), (x2, y2) = points[-2], points[-1]
            dx, dy = x2 - x1, -(y2 - y1)
            length = max((dx * dx + dy * dy) ** 0.5, 1)
            ux, uy = dx / length, dy / length
            tip_x, tip_y = x2 * SCALE, py(y2)
            base_x, base_y = tip_x - ux * 9, tip_y - uy * 9
            perp_x, perp_y = -uy * 4, ux * 4
            stream.extend([
                pdf_color(style.get("stroke"), "rg"),
                f"{tip_x:.2f} {tip_y:.2f} m {base_x+perp_x:.2f} {base_y+perp_y:.2f} l {base_x-perp_x:.2f} {base_y-perp_y:.2f} l h f",
                "Q",
            ])
        elif tag == "text":
            style = style_for(element)
            x, y = float(element.attrib["x"]), float(element.attrib["y"])
            font_size = str(style.get("font-size", "14")).removesuffix("px")
            size = float(font_size) * SCALE
            font = "F2" if int(float(style.get("font-weight", "400"))) >= 600 else "F1"
            raw_content = "".join(element.itertext())
            anchor = element.attrib.get("text-anchor", "start")
            if anchor == "middle":
                x -= approximate_text_width(raw_content, size) / (2 * SCALE)
            elif anchor == "end":
                x -= approximate_text_width(raw_content, size) / SCALE
            content = safe_pdf_text(raw_content)
            stream.extend([
                "BT", f"/{font} {size:.2f} Tf", pdf_color(style.get("fill"), "rg"),
                f"1 0 0 1 {x*SCALE:.2f} {py(y):.2f} Tm", f"({content}) Tj", "ET",
            ])

    content = "\n".join(line for line in stream if line).encode("cp1252", errors="replace")
    return content, page_width, page_height


def render() -> bytes:
    rendered = [render_svg(path) for path in SVG_PAGES]
    page_width, page_height = rendered[0][1:]
    if any((width, height) != (page_width, page_height) for _, width, height in rendered):
        raise ValueError("All architecture pages must use the same SVG dimensions.")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>",
    ]
    page_ids = []
    for index, (content, width, height) in enumerate(rendered):
        page_id = 5 + 2 * index
        content_id = page_id + 1
        page_ids.append(page_id)
        objects.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {width:.2f} {height:.2f}] /Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> /Contents {content_id} 0 R >>".encode())
        objects.append(f"<< /Length {len(content)} >>\nstream\n".encode() + content + b"\nendstream")
    kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
    objects[1] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>".encode()
    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, obj in enumerate(objects, 1):
        offsets.append(len(pdf))
        pdf.extend(f"{number} 0 obj\n".encode() + obj + b"\nendobj\n")
    xref = len(pdf)
    pdf.extend(f"xref\n0 {len(offsets)}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode())
    pdf.extend(f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
    return bytes(pdf)


if __name__ == "__main__":
    PDF_PATH.write_bytes(render())
    print(f"Created {PDF_PATH}")
