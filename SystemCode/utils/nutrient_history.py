import matplotlib.pyplot as plt
from matplotlib import cm
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
import numpy as np
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Image
from io import BytesIO
import datetime
from decimal import Decimal


def create_history_pdf(history_df):
    tlist = history_df.values.tolist()

    tmp_file = BytesIO()
    doc = SimpleDocTemplate(tmp_file, pagesize=letter)
    story = []

    nutrients_head = ['Date', 'Calories\n(kcal)', 'Protein\n(g)', 'Fat\n(g)', 'Carbs\n(g)', 'Calcium\n(mg)', 'Iron\n(mg)',
                      'VC\n(mg)', 'VA\n(ug)', 'Fiber\n(g)']
    # 添加营养表格
    data = [nutrients_head]
    data = data + tlist

    table = Table(data, colWidths=[doc.width / len(data[0]) + 5] * len(data[0]))  # 自动设置列宽
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    story.append(Paragraph("Nutrition History", getSampleStyleSheet()['Heading1']))
    story.append(table)

    doc.build(story)
    tmp_file.seek(0)

    return tmp_file


if __name__ == '__main__':
    pdf = create_history_pdf('')
    with open('history.pdf', 'wb') as f:
        f.write(pdf.read())
