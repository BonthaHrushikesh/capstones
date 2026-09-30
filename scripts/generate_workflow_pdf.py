from pathlib import Path

OUTPUT_PATH = Path(__file__).resolve().parents[1] / 'frontend' / 'public' / 'workflow-diagram.pdf'


def esc_pdf_text(value: str) -> str:
    return value.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')


def wrap_lines(text: str, width: int = 20):
    words = text.split()
    lines = []
    current = ''
    for word in words:
        candidate = f'{current} {word}'.strip()
        if len(candidate) <= width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or ['']


def make_pdf_bytes():
    width, height = 595, 842
    page_x = 60
    title_y = 780
    box_w = 92
    box_h = 74
    gap = 10
    start_x = page_x
    nodes = [
        ('01', 'INPUT', 'User query'),
        ('02', 'UNDERSTAND', 'Intent routing'),
        ('03', 'ANALYZE', 'Data and evidence'),
        ('04', 'SYNTHESIZE', 'Cross-agent brief'),
        ('05', 'GUIDANCE', 'Decision support'),
        ('06', 'VERIFY', 'Guardrails'),
        ('07', 'OUTPUT', 'Final answer'),
    ]

    stream_lines = [
        'q',
        '0.96 0.98 1 rg',
        f'0 0 {width} {height} re f',
        'Q',
        'BT',
        '/F1 20 Tf',
        f'1 0 0 1 {page_x} {title_y} Tm',
        f'({esc_pdf_text("GridSense Copilot Workflow")}) Tj',
        'ET',
    ]

    for idx, (code, title, subtitle) in enumerate(nodes):
        x = start_x + idx * (box_w + gap)
        y = 670
        stream_lines.extend([
            'q',
            '0.94 0.97 1 RG',
            '0.96 0.99 1 rg',
            f'{x} {y} {box_w} {box_h} re b',
            'Q',
            'q',
            '0.17 0.31 0.59 RG',
            f'{x + 8} {y + box_h - 18} 1 0 0 1 0 0 Tm',
            f'({esc_pdf_text(code)}) Tj',
            'Q',
            'BT',
            '/F1 9 Tf',
            f'1 0 0 1 {x + 16} {y + 32} Tm',
            f'({esc_pdf_text(title)}) Tj',
            'ET',
        ])
        for line_no, line in enumerate(wrap_lines(subtitle, 13)[:2]):
            stream_lines.extend([
                'BT',
                '/F1 7 Tf',
                f'1 0 0 1 {x + 12} {y + 18 - line_no * 11} Tm',
                f'({esc_pdf_text(line)}) Tj',
                'ET',
            ])

    for idx in range(len(nodes) - 1):
        x1 = start_x + idx * (box_w + gap) + box_w
        x2 = start_x + (idx + 1) * (box_w + gap)
        y = 670 + box_h / 2
        stream_lines.extend([
            'q',
            '0.38 0.53 0.85 RG',
            f'{x1} {y} m {x2} {y} l S',
            'Q',
            'q',
            '0.38 0.53 0.85 RG',
            f'{x2 - 7} {y - 6} m {x2} {y} l {x2 - 7} {y + 6} l f',
            'Q',
        ])

    stream_lines.extend([
        'BT',
        '/F1 10 Tf',
        f'1 0 0 1 {page_x} {620} Tm',
        f'({esc_pdf_text("Specialist branch routing")}) Tj',
        'ET',
        'BT',
        '/F1 8 Tf',
        f'1 0 0 1 {page_x} {600} Tm',
        f'({esc_pdf_text("Anomaly, Forecast, Analytics, and evidence checks are combined into one answer.")}) Tj',
        'ET',
    ])

    content = '\n'.join(stream_lines).encode('latin-1')
    objects = [
        b'<< /Type /Catalog /Pages 2 0 R >>',
        b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
        b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>',
        b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
        f'<< /Length {len(content)} >>\nstream\n'.encode('latin-1') + content + b'\nendstream',
    ]

    pdf = bytearray(b'%PDF-1.4\n')
    offsets = [0]
    for idx, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f'{idx} 0 obj\n'.encode('latin-1'))
        pdf.extend(obj)
        pdf.extend(b'\nendobj\n')

    xref_pos = len(pdf)
    pdf.extend(f'xref\n0 {len(objects) + 1}\n'.encode('latin-1'))
    pdf.extend(b'0000000000 65535 f \n')
    for off in offsets[1:]:
        pdf.extend(f'{off:010d} 00000 n \n'.encode('latin-1'))
    pdf.extend(f'trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n'.encode('latin-1'))
    return bytes(pdf)


if __name__ == '__main__':
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_bytes(make_pdf_bytes())
    print(f'Generated PDF: {OUTPUT_PATH}')
