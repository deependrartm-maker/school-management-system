from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from django.conf import settings
import os
from .grade_utils import (
    calculate_grade,
    calculate_pass_fail,
    calculate_division,
    calculate_class_ranks
)
from .qr_utils import generate_verification_token
import qrcode
from io import BytesIO
from profiles.models import StudentProfile
from .models import MarkRecord


def watermark(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 60)
    canvas.setFillColorRGB(0.9, 0.9, 0.9)
    canvas.drawCentredString(300, 400, "OFFICIAL")
    canvas.restoreState()


def generate_professional_marksheet_pdf(student, marks, exam_name, response):

    doc = SimpleDocTemplate(response, pagesize=A4)
    elements = []

    styles = getSampleStyleSheet()
    centered = ParagraphStyle(
        name="Centered",
        parent=styles["Heading1"],
        alignment=1
    )

    normal_bold = ParagraphStyle(
        name="NormalBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold"
    )

    # ---- Logo ----
    logo_path = os.path.join(settings.BASE_DIR, "static/logo.jpg")
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=1.2*inch, height=1.2*inch)
        logo.hAlign = 'CENTER'
        elements.append(logo)

    elements.append(Spacer(1, 10))

    # ---- School Header ----
    elements.append(Paragraph("YOUR SCHOOL NAME", centered))
    elements.append(Paragraph("Academic Performance Report", styles["Normal"]))
    elements.append(Spacer(1, 20))

    # ---- Student Info ----
    info_data = [
        ["Name:", student.user.email],
        ["Class:", student.class_name],
        ["Exam:", exam_name],
        ["Admission No:", student.admission_no],
    ]

    info_table = Table(info_data, colWidths=[120, 300])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.lightgrey),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
    ]))

    elements.append(info_table)
    elements.append(Spacer(1, 25))

    # ---- Marks Table ----
    data = [["Subject", "Marks Obtained", "Total Marks"]]
    total_obtained = 0
    total_max = 0

    for mark in marks:
        data.append([
            mark.subject.name,
            mark.marks_obtained,
            mark.total_marks
        ])
        total_obtained += mark.marks_obtained
        total_max += mark.total_marks

    percentage = (total_obtained / total_max) * 100 if total_max else 0
    grade = calculate_grade(percentage)

    # ==============================
    # ✅ PASS / FAIL + DIVISION
    # ==============================
    result_status, calculated_percentage = calculate_pass_fail(marks)
    division = calculate_division(calculated_percentage)

    # ==============================
    # ✅ RANK CALCULATION (Class-wise, exam-wise)
    # ==============================
    students_data = []
    class_students = StudentProfile.objects.filter(class_name=student.class_name)

    for s in class_students:
        records = MarkRecord.objects.filter(
            student=s,
            exam_name=exam_name
        )

        if records.exists():
            status_temp, percentage_temp = calculate_pass_fail(records)
        else:
            percentage_temp = 0

        students_data.append({
            "student_id": s.id,
            "percentage": percentage_temp
        })

    rank_dict = calculate_class_ranks(students_data)
    student_rank = rank_dict.get(student.id, "N/A")

    # ---- Append Totals ----
    data.append(["TOTAL", total_obtained, total_max])
    data.append(["PERCENTAGE", f"{percentage:.2f}%", ""])
    data.append(["GRADE", grade, ""])
    data.append(["RESULT", result_status, ""])
    data.append(["DIVISION", division, ""])
    data.append(["RANK", student_rank, ""])

    marks_table = Table(data, colWidths=[200, 150, 150])
    marks_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('BACKGROUND', (0,-6), (-1,-1), colors.whitesmoke),
    ]))

    elements.append(marks_table)
    elements.append(Spacer(1, 40))

    # ---- QR Code ----
    token = generate_verification_token(student.id, exam_name)
    qr = qrcode.make(token)
    buffer = BytesIO()
    qr.save(buffer)
    buffer.seek(0)

    qr_image = Image(buffer, width=1.3*inch, height=1.3*inch)
    qr_image.hAlign = 'LEFT'
    elements.append(qr_image)

    elements.append(Spacer(1, 20))

    # ---- Signature ----
    sign_path = os.path.join(settings.BASE_DIR, "static/sign.png")
    if os.path.exists(sign_path):
        sign = Image(sign_path, width=2*inch, height=1*inch)
        sign.hAlign = 'RIGHT'
        elements.append(sign)
        elements.append(Paragraph("Principal Signature", normal_bold))

    doc.build(elements, onFirstPage=watermark)
