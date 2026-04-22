"""
Payslip Generator
Creates a professional PDF payslip using reportlab.
"""

import io
from datetime import datetime
import calendar

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm, cm
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle, Paragraph,
        Spacer, HRFlowable
    )
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


COMPANY_NAME = "Acme Technologies Pvt. Ltd."
COMPANY_ADDRESS = "123, Tech Park, Bengaluru - 560001, Karnataka"
COMPANY_CIN = "U72900KA2020PTC123456"


def _rupee(amount: float) -> str:
    return f"₹ {amount:,.2f}"


def generate_payslip_pdf(employee: dict, payroll: dict, month: int, year: int) -> bytes:
    if not REPORTLAB_AVAILABLE:
        raise ImportError("reportlab is not installed. Run: pip install reportlab")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )

    # ── Colors ──────────────────────────────────────────
    DARK_BLUE = colors.HexColor("#1a237e")
    MID_BLUE  = colors.HexColor("#3949ab")
    LIGHT_BG  = colors.HexColor("#e8eaf6")
    ACCENT    = colors.HexColor("#00acc1")
    GREEN     = colors.HexColor("#2e7d32")
    RED_LIGHT = colors.HexColor("#ffebee")
    GREEN_LIGHT = colors.HexColor("#e8f5e9")
    GREY      = colors.HexColor("#f5f5f5")
    TEXT      = colors.HexColor("#212121")

    styles = getSampleStyleSheet()
    story = []

    # ── Header ──────────────────────────────────────────
    header_data = [[
        Paragraph(
            f"<font color='#ffffff' size='16'><b>{COMPANY_NAME}</b></font><br/>"
            f"<font color='#b3c5ff' size='8'>{COMPANY_ADDRESS}</font><br/>"
            f"<font color='#b3c5ff' size='7'>CIN: {COMPANY_CIN}</font>",
            ParagraphStyle("hdr", fontName="Helvetica", alignment=TA_LEFT)
        ),
        Paragraph(
            f"<font color='#ffffff' size='13'><b>PAY SLIP</b></font><br/>"
            f"<font color='#b3c5ff' size='9'>{calendar.month_name[month]} {year}</font>",
            ParagraphStyle("hdr2", fontName="Helvetica-Bold", alignment=TA_RIGHT)
        ),
    ]]
    header_table = Table(header_data, colWidths=[120 * mm, 55 * mm])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), DARK_BLUE),
        ("TEXTCOLOR",  (0, 0), (-1, -1), colors.white),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (0, 0), 8),
        ("RIGHTPADDING", (-1, 0), (-1, 0), 8),
        ("ROUNDEDCORNERS", [4, 4, 0, 0]),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 4 * mm))

    # ── Employee Details ─────────────────────────────────
    doj = employee.get("date_of_joining", "")
    emp_info = [
        ["Employee ID", employee.get("emp_id", ""),
         "Department", employee.get("department", "")],
        ["Employee Name", employee.get("name", ""),
         "Designation", employee.get("designation", "")],
        ["Date of Joining", doj,
         "PAN Number", employee.get("pan_number", "N/A")],
        ["Bank Account", employee.get("bank_account", ""),
         "Bank Name", employee.get("bank_name", "")],
    ]
    emp_table = Table(emp_info, colWidths=[35 * mm, 50 * mm, 35 * mm, 55 * mm])
    emp_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), LIGHT_BG),
        ("BACKGROUND", (2, 0), (2, -1), LIGHT_BG),
        ("FONTNAME",   (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME",   (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, -1), 8),
        ("TEXTCOLOR",  (0, 0), (0, -1), DARK_BLUE),
        ("TEXTCOLOR",  (2, 0), (2, -1), DARK_BLUE),
        ("GRID",       (0, 0), (-1, -1), 0.3, colors.HexColor("#c5cae9")),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, GREY]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(emp_table)
    story.append(Spacer(1, 4 * mm))

    # ── Attendance Summary ───────────────────────────────
    att_data = [
        [
            Paragraph("<b>Working Days</b>", ParagraphStyle("a", fontSize=8)),
            Paragraph(f"<b>{payroll.get('working_days', 26)}</b>", ParagraphStyle("a", fontSize=9, alignment=TA_CENTER)),
            Paragraph("<b>Present Days</b>", ParagraphStyle("a", fontSize=8)),
            Paragraph(f"<b>{payroll.get('present_days', 26)}</b>", ParagraphStyle("a", fontSize=9, alignment=TA_CENTER)),
            Paragraph("<b>Leaves Taken</b>", ParagraphStyle("a", fontSize=8)),
            Paragraph(f"<b>{payroll.get('leaves_taken', 0)}</b>", ParagraphStyle("a", fontSize=9, alignment=TA_CENTER)),
            Paragraph("<b>LOP Days</b>", ParagraphStyle("a", fontSize=8)),
            Paragraph(f"<b>{payroll.get('lop_days', 0)}</b>", ParagraphStyle("a", fontSize=9, alignment=TA_CENTER)),
            Paragraph("<b>Attendance %</b>", ParagraphStyle("a", fontSize=8)),
            Paragraph(f"<b>{payroll.get('attendance_percentage', 100):.1f}%</b>", ParagraphStyle("a", fontSize=9, alignment=TA_CENTER)),
        ]
    ]
    att_table = Table(att_data, colWidths=[28 * mm] * 10)
    att_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
        ("FONTNAME",   (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE",   (0, 0), (-1, -1), 8),
        ("GRID",       (0, 0), (-1, -1), 0.3, colors.HexColor("#c5cae9")),
        ("ALIGN",      (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(att_table)
    story.append(Spacer(1, 4 * mm))

    # ── Earnings & Deductions ────────────────────────────
    col_label = ParagraphStyle("col", fontName="Helvetica-Bold",
                               fontSize=9, textColor=colors.white, alignment=TA_CENTER)
    earnings_header = [
        Paragraph("EARNINGS", col_label),
        Paragraph("AMOUNT (₹)", col_label),
        Paragraph("DEDUCTIONS", col_label),
        Paragraph("AMOUNT (₹)", col_label),
    ]

    def fmt(v): return f"{v:,.2f}"

    rows_earn = [
        ("Basic Salary",        payroll.get("basic_salary", 0)),
        ("House Rent Allowance",payroll.get("hra", 0)),
        ("Dearness Allowance",  payroll.get("da", 0)),
        ("Medical Allowance",   payroll.get("medical_allowance", 0)),
        ("Transport Allowance", payroll.get("transport_allowance", 0)),
        ("Overtime Pay",        payroll.get("overtime_pay", 0)),
        ("Other Allowances",    payroll.get("other_allowances", 0)),
    ]
    rows_ded = [
        ("Provident Fund",      payroll.get("pf_employee", 0)),
        ("ESI",                 payroll.get("esi", 0)),
        ("Professional Tax",    payroll.get("professional_tax", 0)),
        ("Income Tax (TDS)",    payroll.get("income_tax", 0)),
        ("Other Deductions",    payroll.get("other_deductions", 0)),
    ]

    max_rows = max(len(rows_earn), len(rows_ded))
    rows_earn += [("", 0)] * (max_rows - len(rows_earn))
    rows_ded  += [("", 0)] * (max_rows - len(rows_ded))

    table_data = [earnings_header]
    for i in range(max_rows):
        e_label, e_val = rows_earn[i]
        d_label, d_val = rows_ded[i]
        table_data.append([
            e_label,
            fmt(e_val) if e_label else "",
            d_label,
            fmt(d_val) if d_label else "",
        ])

    # Totals row
    table_data.append([
        Paragraph("<b>GROSS SALARY</b>", ParagraphStyle("tot", fontSize=9, fontName="Helvetica-Bold")),
        Paragraph(f"<b>{fmt(payroll.get('gross_salary', 0))}</b>", ParagraphStyle("tot", fontSize=9, fontName="Helvetica-Bold", alignment=TA_RIGHT)),
        Paragraph("<b>TOTAL DEDUCTIONS</b>", ParagraphStyle("tot", fontSize=9, fontName="Helvetica-Bold")),
        Paragraph(f"<b>{fmt(payroll.get('total_deductions', 0))}</b>", ParagraphStyle("tot", fontSize=9, fontName="Helvetica-Bold", alignment=TA_RIGHT)),
    ])

    ed_table = Table(table_data, colWidths=[57 * mm, 28 * mm, 57 * mm, 33 * mm])
    n = len(table_data)
    ed_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (1, 0), MID_BLUE),
        ("BACKGROUND",    (2, 0), (3, 0), MID_BLUE),
        ("TEXTCOLOR",     (0, 0), (-1, 0), colors.white),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS",(0, 1), (1, n - 2), [colors.white, GREY]),
        ("ROWBACKGROUNDS",(2, 1), (3, n - 2), [colors.white, GREY]),
        ("BACKGROUND",    (0, n - 1), (-1, n - 1), GREEN_LIGHT),
        ("FONTNAME",      (0, n - 1), (-1, n - 1), "Helvetica-Bold"),
        ("GRID",          (0, 0), (-1, -1), 0.3, colors.HexColor("#c5cae9")),
        ("ALIGN",         (1, 0), (1, -1), "RIGHT"),
        ("ALIGN",         (3, 0), (3, -1), "RIGHT"),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
    ]))
    story.append(ed_table)
    story.append(Spacer(1, 4 * mm))

    # ── Net Salary Banner ────────────────────────────────
    net_data = [[
        Paragraph(
            f"<font color='#ffffff' size='11'><b>NET SALARY PAYABLE</b></font>",
            ParagraphStyle("ns", fontName="Helvetica-Bold", alignment=TA_LEFT)
        ),
        Paragraph(
            f"<font color='#ffffff' size='13'><b>₹ {payroll.get('net_salary', 0):,.2f}</b></font>",
            ParagraphStyle("ns2", fontName="Helvetica-Bold", alignment=TA_RIGHT)
        ),
    ]]
    net_table = Table(net_data, colWidths=[120 * mm, 55 * mm])
    net_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), GREEN),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (0, 0), 10),
        ("RIGHTPADDING",  (-1, 0), (-1, 0), 10),
    ]))
    story.append(net_table)
    story.append(Spacer(1, 4 * mm))

    # ── Employer PF (informational) ──────────────────────
    emp_pf = payroll.get("pf_employer", 0)
    if emp_pf > 0:
        story.append(Paragraph(
            f"<font size='7' color='grey'>Employer PF Contribution: ₹ {emp_pf:,.2f} &nbsp;|&nbsp; "
            f"Total CTC includes employer PF.</font>",
            ParagraphStyle("note", alignment=TA_CENTER)
        ))
        story.append(Spacer(1, 2 * mm))

    # ── Footer ───────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#9fa8da")))
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph(
        "<font size='7' color='grey'>This is a computer-generated payslip and does not require a signature. "
        "For queries, contact HR at hr@acmetech.com</font>",
        ParagraphStyle("footer", alignment=TA_CENTER)
    ))
    story.append(Paragraph(
        f"<font size='7' color='grey'>Generated on {datetime.now().strftime('%d %b %Y, %I:%M %p')}</font>",
        ParagraphStyle("footer2", alignment=TA_CENTER)
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
