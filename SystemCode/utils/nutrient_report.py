import matplotlib.pyplot as plt
from matplotlib import cm
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import numpy as np
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Image
from io import BytesIO


# 创建饼状图
def create_pie_chart(food_dict):
    tmp_file = BytesIO()
    labels = food_dict.keys()
    sizes = [food_dict[food]['Calories'] for food in food_dict]

    # 计算总卡路里
    total_calories = sum(sizes)

    # 使用颜色映射生成颜色
    cmap = cm.get_cmap('viridis')
    colors = cmap(np.linspace(0, 1, len(food_dict)))

    fig1, ax1 = plt.subplots()
    ax1.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors)
    ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    plt.title('Calories Distribution')

    # 在图中添加总卡路里文本
    ax1.text(0, -1.1, f'Total Calories: {total_calories:.1f}', ha='center', va='center', fontsize=18, color='black')

    plt.savefig(tmp_file)
    plt.close()

    tmp_file.seek(0)

    return tmp_file


# 创建柱状图
def create_bar_chart(food_dict, nutrients):
    tmp_file = BytesIO()

    fig, ax = plt.subplots()
    x = np.arange(len(nutrients))
    width = 0.5

    # 使用颜色映射生成颜色
    cmap = cm.get_cmap('viridis')
    colors = cmap(np.linspace(0, 1, len(food_dict)))

    # 创建堆积柱状图
    bottom = [0] * len(nutrients)
    for i, food in enumerate(food_dict):
        values = [food_dict[food][nutrient] for nutrient in nutrients]
        ax.bar(x, values, width, label=food, bottom=bottom, color=colors[i])
        bottom = [bottom[j] + values[j] for j in range(len(nutrients))]

    ax.set_ylabel('Amount')
    ax.set_title('Nutrient Distribution')
    ax.set_xticks(x)
    ax.set_xticklabels(nutrients)
    ax.legend()
    plt.savefig(tmp_file)
    plt.close()

    tmp_file.seek(0)

    return tmp_file


# 创建PDF
def create_pdf(food_dict, total_nutrition):
    tmp_file = BytesIO()
    doc = SimpleDocTemplate(tmp_file, pagesize=letter)
    story = []

    # 添加饼状图
    pie = create_pie_chart(food_dict)
    story.append(Paragraph("Calories Distribution", getSampleStyleSheet()['Heading1']))
    story.append(Paragraph("The following pie chart shows the distribution of calories among different foods.",
                           getSampleStyleSheet()['Normal']))
    story.append(Image(pie, width=400, height=300))  # 使用Image类

    # 添加柱状图
    nutrients_bar = ['Protein', 'Fat', 'Carbs', 'Calcium', 'Iron', 'VC', 'VA', 'Fiber']
    nutrients = ['Calories', 'Protein', 'Fat', 'Carbs', 'Calcium', 'Iron', 'VC', 'VA', 'Fiber']
    nutrients_head = ['Calories\n(kcal)', 'Protein\n(g)', 'Fat\n(g)', 'Carbs\n(g)', 'Calcium\n(mg)', 'Iron\n(mg)', 'VC\n(mg)', 'VA\n(ug)', 'Fiber\n(g)']
    bar = create_bar_chart(food_dict, nutrients_bar)
    story.append(Paragraph("Nutrient Distribution", getSampleStyleSheet()['Heading1']))
    story.append(Paragraph("The following bar chart shows the distribution of nutrients among different foods.",
                           getSampleStyleSheet()['Normal']))
    story.append(Image(bar, width=400, height=300))  # 使用Image类

    # 添加营养表格
    data = [['Food'] + nutrients_head]
    for food in food_dict:
        data.append([food] + [str(round(food_dict[food][nutrient], 1)) for nutrient in nutrients])
    data.append(['Total'] + [str(round(total_nutrition[nutrient], 1)) for nutrient in nutrients])

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

    story.append(Paragraph("Nutrition Table", getSampleStyleSheet()['Heading1']))
    story.append(table)

    doc.build(story)
    tmp_file.seek(0)

    return tmp_file


if __name__ == '__main__':
    result = {
        'credit_card_area': 0,
        'food_dict': {
            'bread': {'Calories': 530.0, 'Protein': 18.0, 'Fat': 6.4, 'Carbs': 98.0, 'Calcium': 200.0, 'Iron': 7.2,
                      'VC': 0.0, 'VA': 0.0, 'Fiber': 5.4},
            'french fries': {'Calories': 249.6, 'Protein': 2.72, 'Fat': 12.0, 'Carbs': 32.8, 'Calcium': 16.0,
                             'Iron': 0.64, 'VC': 3.2, 'VA': 0.0, 'Fiber': 3.04},
            'steak': {'Calories': 894.3, 'Protein': 82.5, 'Fat': 61.05000000000001, 'Carbs': 0.0,
                      'Calcium': 59.400000000000006, 'Iron': 8.580000000000002, 'VC': 0.0, 'VA': 9.9, 'Fiber': 0.0},
            'cheese butter': {'Calories': 215.1, 'Protein': 0.27, 'Fat': 24.3, 'Carbs': 0.03, 'Calcium': 7.2,
                              'Iron': 0.0, 'VC': 0.0, 'VA': 74.7, 'Fiber': 0.0},
            'lettuce': {'Calories': 3.0, 'Protein': 0.28, 'Fat': 0.04, 'Carbs': 0.58, 'Calcium': 7.2, 'Iron': 0.18,
                        'VC': 1.84, 'VA': 148.0, 'Fiber': 0.26}
        },
        'total_nutrition': {
            'Calories': 1892.0, 'Protein': 103.77, 'Fat': 103.79000000000002, 'Carbs': 131.41000000000003,
            'Calcium': 289.79999999999995, 'Iron': 16.6, 'VC': 5.04, 'VA': 232.60000000000002,
            'Fiber': 8.700000000000001
        }
    }

    pdf = create_pdf(result['food_dict'], result['total_nutrition'])

    with open('report.pdf', 'wb') as f:
        f.write(pdf.getvalue())
