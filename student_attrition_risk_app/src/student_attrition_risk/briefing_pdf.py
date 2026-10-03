"""Human-readable PDF export for advisor briefings."""

from __future__ import annotations

import re
from datetime import datetime
from html import escape
from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from .models import (
    SUPPRESSED,
    UNAVAILABLE,
    StudentRiskProfile,
    ValidatedBriefing,
)
from .student_repository import STUDENT_ID_LENGTH

# Keep these labels aligned with ui.py.
LABELS = {
    "age_band": "Age band",
    "attendance_mode": "Attendance mode",
    "course_admission_load_category": "Study load",
    "eftsl": "EFTSL",
    "enrolment_year": "Enrolment year",
    "commencing_continuing": "Student stage",
    "commencing_continuing_period": "Commencing/continuing period",
    "international_domestic_student": "International/domestic",
    "cumulative_credit_points_enrolled": "Credit points enrolled",
    "cumulative_credit_points_passed": "Credit points passed",
    "cumulative_credit_points_failed": "Credit points failed",
    "cumulative_credit_points_withdrawn": "Credit points withdrawn",
    "course_group": "Course Group",
    "broad_primary_field_of_education": "Field of Education",
    "socioeconomic_status": "Socioeconomic Status",
    "regional_remote_status": "Regional or Remote Status",
}

BRIEFING_HEADINGS = {
    "Risk Summary",
    "Relevant Student Context",
    "Recommended Advisor Actions",
    "Suggested Next Steps",
}

BLUE = colors.HexColor("#00558c")
DARK_BLUE = colors.HexColor("#172033")
TEXT = colors.HexColor("#344054")
MUTED = colors.HexColor("#667085")
BORDER = colors.HexColor("#e4e7ec")
LIGHT_BLUE = colors.HexColor("#eff8ff")
VERY_LIGHT = colors.HexColor("#f8fafc")


def _normalise_text(value: Any) -> str:
    """Normalise common generated punctuation for reliable PDF rendering."""
    text = str(value)

    replacements = {
      "\u00a0": " ",
      "\u202f": " ",
      "\u2010": "-",  # hyphen
      "\u2011": "-",  # non-breaking hyphen
      "\u2012": "-",  # figure dash
      "\u2013": "-",  # en dash
      "\u2014": "-",  # em dash
      "\u2212": "-",  # minus sign
      "\u2018": "'",
      "\u2019": "'",
      "\u201c": '"',
      "\u201d": '"',
    }
    
    for original, replacement in replacements.items():
        text = text.replace(original, replacement)

    return text


def _display_value(value: Any) -> str:
    if value == SUPPRESSED:
        return "Suppressed for privacy"

    if value in (None, UNAVAILABLE):
        return "Unavailable"

    return _normalise_text(value)


def _display_label(name: str) -> str:
    return LABELS.get(name, name.replace("_", " ").title())


def _format_datetime(value: datetime | None) -> str:
    if value is None:
        return "Unavailable"

    timezone = value.strftime("%Z")
    rendered = value.strftime("%d %b %Y %H:%M")

    return f"{rendered} {timezone}".strip()


def _inline_markup(text: str) -> str:
    """Convert the small amount of Markdown used by generated briefings."""
    safe = escape(_normalise_text(text), quote=False)

    # ReportLab Paragraph understands simple HTML-like bold markup.
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", safe)


def _heading_from_line(line: str) -> str | None:
    stripped = line.strip()

    if stripped in BRIEFING_HEADINGS:
        return stripped

    for prefix in ("### ", "## ", "# "):
        if stripped.startswith(prefix):
            candidate = stripped[len(prefix):].strip()
            return candidate if candidate in BRIEFING_HEADINGS else None

    if stripped.startswith("**") and stripped.endswith("**"):
        candidate = stripped[2:-2].strip()
        return candidate if candidate in BRIEFING_HEADINGS else None

    return None


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()

    return {
        "top_bar": ParagraphStyle(
            "TopBar",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=10,
            textColor=colors.white,
            leading=13,
        ),
        "title": ParagraphStyle(
            "Title",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=27,
            textColor=DARK_BLUE,
            spaceAfter=5,
        ),
        "subtitle": ParagraphStyle(
            "Subtitle",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=14,
            textColor=MUTED,
            spaceAfter=12,
        ),
        "eyebrow": ParagraphStyle(
            "Eyebrow",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=7.5,
            leading=10,
            textColor=MUTED,
            spaceAfter=5,
        ),
        "summary": ParagraphStyle(
            "Summary",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=16,
            textColor=DARK_BLUE,
            spaceAfter=6,
        ),
        "meta": ParagraphStyle(
            "Meta",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            textColor=MUTED,
            spaceAfter=3,
        ),
        "risk_label": ParagraphStyle(
            "RiskLabel",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=7,
            leading=9,
            textColor=MUTED,
            alignment=TA_CENTER,
            spaceAfter=6,
        ),
        "risk_score": ParagraphStyle(
            "RiskScore",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            textColor=BLUE,
            alignment=TA_CENTER,
        ),
        "section": ParagraphStyle(
            "Section",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=16,
            textColor=DARK_BLUE,
            spaceBefore=6,
            spaceAfter=7,
        ),
        "privacy": ParagraphStyle(
            "Privacy",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=MUTED,
            spaceAfter=7,
        ),
        "snapshot_label": ParagraphStyle(
            "SnapshotLabel",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=12,
            textColor=DARK_BLUE,
        ),
        "snapshot_value": ParagraphStyle(
            "SnapshotValue",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            textColor=TEXT,
        ),
        "notice": ParagraphStyle(
            "Notice",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=12,
            textColor=BLUE,
        ),
        "briefing_heading": ParagraphStyle(
            "BriefingHeading",
            parent=base["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=10.5,
            leading=14,
            textColor=DARK_BLUE,
            spaceBefore=8,
            spaceAfter=4,
        ),
        "briefing_body": ParagraphStyle(
            "BriefingBody",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=13.5,
            textColor=TEXT,
            spaceAfter=5,
        ),
        "briefing_bullet": ParagraphStyle(
            "BriefingBullet",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=13.5,
            textColor=TEXT,
            leftIndent=12,
            firstLineIndent=-8,
            spaceAfter=3,
        ),
        "briefing_meta": ParagraphStyle(
            "BriefingMeta",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=7.8,
            leading=11,
            textColor=MUTED,
            spaceBefore=8,
        ),
    }


def _briefing_flowables(
    text: str,
    styles: dict[str, ParagraphStyle],
) -> list[Any]:
    flowables: list[Any] = []
    paragraph_lines: list[str] = []

    def flush_paragraph() -> None:
        if not paragraph_lines:
            return

        joined = " ".join(paragraph_lines)
        flowables.append(
            Paragraph(
                _inline_markup(joined),
                styles["briefing_body"],
            )
        )
        paragraph_lines.clear()

    for raw_line in text.splitlines():
        line = raw_line.strip()

        if not line:
            flush_paragraph()
            continue

        heading = _heading_from_line(line)

        if heading:
            flush_paragraph()
            flowables.append(
                Paragraph(
                    escape(heading),
                    styles["briefing_heading"],
                )
            )
            continue

        if line.startswith(("- ", "* ")):
            flush_paragraph()
            flowables.append(
                Paragraph(
                    f"&bull; {_inline_markup(line[2:].strip())}",
                    styles["briefing_bullet"],
                )
            )
            continue

        paragraph_lines.append(line)

    flush_paragraph()

    return flowables


def _draw_footer(canvas, doc) -> None:
    canvas.saveState()
    canvas.setTitle("Student Advisor Briefing")
    canvas.setAuthor("Student Attrition Risk App")
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 7)

    canvas.drawString(
        doc.leftMargin,
        8 * mm,
        "Deidentified student information. "
        "AI-generated briefing - review before taking action.",
    )

    canvas.drawRightString(
        A4[0] - doc.rightMargin,
        8 * mm,
        f"Page {canvas.getPageNumber()}",
    )

    canvas.restoreState()


def create_briefing_pdf(
    profile: StudentRiskProfile,
    briefing: ValidatedBriefing,
) -> bytes:
    """Create an advisor-facing offline PDF matching the important UI content."""

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=15 * mm,
        bottomMargin=20 * mm,
    )

    styles = _styles()
    content_width = A4[0] - doc.leftMargin - doc.rightMargin
    story: list[Any] = []

    top_bar = Table(
        [[Paragraph("Student Briefing", styles["top_bar"])]],
        colWidths=[content_width],
    )
    top_bar.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), BLUE),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
            ]
        )
    )

    story.append(top_bar)
    story.append(Spacer(1, 7 * mm))

    story.append(
        Paragraph(
            "Student Advisor Briefing",
            styles["title"],
        )
    )
    story.append(
        Paragraph(
            "Review model-generated risk information and prepare a supportive, "
            "human-led response.",
            styles["subtitle"],
        )
    )

    prediction = profile.prediction
    risk_label = "At Risk" if prediction.attrition_risk_flag else "Not At Risk"
    threshold_percentage = prediction.prediction_threshold * 100

    summary_left = [
        Paragraph("STUDENT SUMMARY", styles["eyebrow"]),
        Paragraph(
            f"Deidentified student - <b>{escape(risk_label)}</b>",
            styles["summary"],
        ),
        Paragraph(
            "Student ID (de-identified): "
            f"{escape(prediction.student_deidentified_hash[:STUDENT_ID_LENGTH])}",
            styles["meta"],
        ),
        Paragraph(
            f"Decision threshold: {threshold_percentage:.1f}%"
            f"<br/>Scored: {escape(_format_datetime(prediction.scored_at))}",
            styles["meta"],
        ),
    ]

    summary_right = [
        Paragraph("RELATIVE RISK SCORE", styles["risk_label"]),
        Paragraph(
            f"{prediction.attrition_risk_percentage:.1f}%",
            styles["risk_score"],
        ),
    ]

    summary_table = Table(
        [[summary_left, summary_right]],
        colWidths=[content_width * 0.74, content_width * 0.26],
    )
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.75, BORDER),
                ("LINEBEFORE", (0, 0), (0, 0), 4, BLUE),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )

    story.append(summary_table)
    story.append(Spacer(1, 7 * mm))

    story.append(
        Paragraph(
            "Available Student Information",
            styles["section"],
        )
    )
    story.append(
        Paragraph(
            "Approved cross-sectional student information.",
            styles["privacy"],
        )
    )

    snapshot_rows: list[list[Any]] = []

    if profile.snapshot:
        for name, value in profile.snapshot.attributes.items():
            # Match the UI: omit absent/unavailable values,
            # but retain explicit privacy suppression.
            if value is None or value == UNAVAILABLE:
                continue

            snapshot_rows.append(
                [
                    Paragraph(
                        escape(_display_label(name)),
                        styles["snapshot_label"],
                    ),
                    Paragraph(
                        escape(_display_value(value)),
                        styles["snapshot_value"],
                    ),
                ]
            )

    if snapshot_rows:
        snapshot_table = Table(
            snapshot_rows,
            colWidths=[content_width * 0.42, content_width * 0.58],
        )
        snapshot_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), VERY_LIGHT),
                    ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
                    ("INNERGRID", (0, 0), (-1, -1), 0.35, BORDER),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(snapshot_table)
    else:
        story.append(
            Paragraph(
                "No approved snapshot information is available.",
                styles["briefing_body"],
            )
        )

    story.append(Spacer(1, 7 * mm))

    story.append(
        Paragraph(
            "AI-Assisted Advisor Briefing",
            styles["section"],
        )
    )

    notice = Table(
        [
            [
                Paragraph(
                    "AI-generated - review before taking action.",
                    styles["notice"],
                )
            ]
        ],
        colWidths=[content_width],
    )
    notice.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BLUE),
                ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#b2ddff")),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )

    story.append(notice)
    story.append(Spacer(1, 3 * mm))

    story.extend(
        _briefing_flowables(
            briefing.text,
            styles,
        )
    )

    story.append(Spacer(1, 3 * mm))

    metadata = (
        f"Source: {escape(briefing.source.title())}"
        f" &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"Validation: {escape(briefing.validator_id)}"
        f" &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"Saved: {'Yes' if briefing.storage_confirmed else 'No'}"
        f"<br/>Generated: {escape(_format_datetime(briefing.generated_at))}"
    )

    story.append(
        Paragraph(
            metadata,
            styles["briefing_meta"],
        )
    )

    doc.build(
        story,
        onFirstPage=_draw_footer,
        onLaterPages=_draw_footer,
    )

    return buffer.getvalue()