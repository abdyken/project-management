"""Printable checklists use the same current requirements as the portal and tracker."""

from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.applicant.schemas import SavedChecklistOut

pdfmetrics.registerFont(TTFont("DejaVu", str(Path(__file__).parent / "fonts" / "DejaVuSans.ttf")))

_LABELS = {
    "en": (
        "Document checklist",
        "Local applicant",
        "International applicant",
        "Prepared",
        "To prepare",
        "Original",
        "Copy",
        "Translation required",
        "Notarisation required",
        "Deadline",
        "Not published",
        "Official program page",
        "Document names and requirements follow the official published text. Confirm updates with the admissions office.",
        "This program is archived. Contact the admissions office.",
    ),
    "ru": (
        "Список документов",
        "Местный абитуриент",
        "Иностранный абитуриент",
        "Подготовлено",
        "Подготовить",
        "Оригинал",
        "Копия",
        "Требуется перевод",
        "Требуется нотариальное заверение",
        "Срок",
        "Не опубликовано",
        "Официальная страница программы",
        "Названия документов и требования приведены по официальному тексту. Уточните изменения в приёмной комиссии.",
        "Программа в архиве. Обратитесь в приёмную комиссию.",
    ),
    "kk": (
        "Құжаттар тізімі",
        "Отандық талапкер",
        "Шетелдік талапкер",
        "Дайын",
        "Дайындау керек",
        "Түпнұсқа",
        "Көшірме",
        "Аударма қажет",
        "Нотариалды куәландыру қажет",
        "Мерзімі",
        "Жарияланбаған",
        "Бағдарламаның ресми беті",
        "Құжаттардың атауы мен талаптары ресми мәтін бойынша берілген. Өзгерістерді қабылдау комиссиясынан нақтылаңыз.",
        "Бағдарлама мұрағатта. Қабылдау комиссиясына хабарласыңыз.",
    ),
}


def checklist_pdf(checklist: SavedChecklistOut, language: str, contact: str) -> bytes:
    labels = _LABELS[language]
    output = BytesIO()
    doc = SimpleDocTemplate(
        output,
        pagesize=A4,
        rightMargin=42,
        leftMargin=42,
        topMargin=40,
        bottomMargin=44,
        title=f"SDU - {labels[0]}",
        author="SDU Admissions Portal",
    )
    body = ParagraphStyle("body", fontName="DejaVu", fontSize=9, leading=14, spaceAfter=5)
    heading = ParagraphStyle("heading", parent=body, fontSize=20, leading=27, spaceAfter=14)

    def paragraph(value: str, style=body):
        return Paragraph(escape(value).replace("\n", "<br/>"), style)

    program = checklist.program
    title = getattr(program, f"title_{language}", None) or program.title
    deadline = getattr(program, f"deadline_{checklist.applicant_type}")
    parts = [
        paragraph(f"SDU | {labels[0]}", heading),
        paragraph(f"{title} ({program.program_id})"),
        paragraph(labels[1 if checklist.applicant_type == "local" else 2]),
        paragraph(f"{labels[9]}: {deadline.isoformat() if deadline else labels[10]}"),
        paragraph(f"{labels[3]}: {checklist.prepared}/{checklist.total}"),
        Spacer(1, 12),
    ]
    if not program.is_active:
        parts.append(paragraph(labels[13]))
    if checklist.warning:
        warnings = {
            "en": "The document list is not published. Contact the admissions office.",
            "ru": "Список документов не опубликован. Обратитесь в приёмную комиссию.",
            "kk": "Құжаттар тізімі жарияланбаған. Қабылдау комиссиясына хабарласыңыз.",
        }
        parts.append(paragraph(warnings[language]))
    for index, item in enumerate(checklist.items, 1):
        requirements = [labels[5 if item.format == "original" else 6]]
        if item.translation:
            requirements.append(labels[7])
        if item.notarisation:
            requirements.append(labels[8])
        requirements.append(f"{labels[9]}: {item.deadline}")
        row = Table(
            [
                [
                    paragraph(f"{index}. {item.name}\n{'; '.join(requirements)}"),
                    paragraph(labels[3 if item.prepared else 4]),
                ]
            ],
            colWidths=[doc.width - 106, 106],
        )
        row.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor("#d4dbe0")),
                    ("TOPPADDING", (0, 0), (-1, -1), 9),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
                ]
            )
        )
        parts.append(row)
    parts.extend([Spacer(1, 18), paragraph(labels[12]), paragraph(contact)])
    if program.source_url:
        parts.append(paragraph(f"{labels[11]}: {program.source_url}"))

    def footer(canvas, document):
        canvas.setFont("DejaVu", 8)
        canvas.drawRightString(A4[0] - 42, 24, f"SDU | {document.page}")

    doc.build(parts, onFirstPage=footer, onLaterPages=footer)
    return output.getvalue()
