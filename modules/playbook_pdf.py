"""Render a Playbook to PDF bytes with reportlab."""

from __future__ import annotations

from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from modules.playbook import Playbook

# Built-in PDF fonts can't draw these glyphs; swap for plain equivalents.
_GLYPHS = {"→": "->", "≤": "<=", "≥": ">=", "×": "x", "÷": "/"}


def _t(text: str) -> str:
    for glyph, plain in _GLYPHS.items():
        text = text.replace(glyph, plain)
    return escape(text)


def playbook_to_pdf(pb: Playbook) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=LETTER, leftMargin=0.7 * inch, rightMargin=0.7 * inch,
        topMargin=0.7 * inch, bottomMargin=0.7 * inch,
        title=f"DCP Rollout Plan — {pb.merchant}",
    )
    styles = getSampleStyleSheet()
    body, small = styles["BodyText"], styles["BodyText"].clone("small", fontSize=8.5, leading=11)
    story = [
        Paragraph(_t(f"DCP Rollout Plan: {pb.merchant}"), styles["Title"]),
        Paragraph(_t(pb.stack), body),
    ]

    summary = f"<b>Integration complexity:</b> {_t(pb.complexity_label)} &nbsp;&nbsp; " \
              f"<b>Total timeline:</b> ~{pb.total_weeks} weeks"
    if pb.extra_sales_per_year is not None:
        summary += f" &nbsp;&nbsp; <b>Extra sales per year:</b> ${pb.extra_sales_per_year:,.0f}"
        if pb.sss_growth_pct is not None:
            summary += f" (+{pb.sss_growth_pct:.1f}%)"
    elif pb.sss_growth_pct is not None:
        summary += f" &nbsp;&nbsp; <b>Sales growth:</b> +{pb.sss_growth_pct:.1f}%"
    story += [Spacer(1, 6), Paragraph(summary, body)]
    for note in pb.notes:
        story.append(Paragraph(f"<i>{_t(note)}</i>", small))

    story += [Spacer(1, 12), Paragraph("Rollout plan", styles["Heading2"])]
    rows = [["Phase", "Weeks", "Key activities", "Exit criteria"]]
    for p in pb.phases:
        acts = "<br/>".join(f"• {_t(a)}" for a in p.activities)
        rows.append([
            Paragraph(f"<b>{p.name}</b>", small),
            Paragraph(f"{p.start_week}–{p.end_week}<br/>({p.weeks} wks)", small),
            Paragraph(acts, small),
            Paragraph(_t(p.exit_criteria), small),
        ])
    table = Table(rows, colWidths=[0.95 * inch, 0.8 * inch, 3.6 * inch, 1.75 * inch], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2a78d6")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d0d0cc")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f3")]),
    ]))
    story.append(table)

    if pb.risks:
        story += [Spacer(1, 12), Paragraph("Risk register", styles["Heading2"])]
        for r in pb.risks:
            story.append(Paragraph(f"<b>{_t(r.title)}</b>: {_t(r.detail)}", small))
            story.append(Spacer(1, 3))

    doc.build(story)
    return buf.getvalue()
