from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, PageBreak, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import HorizontalBarChart
from datetime import date
from math import ceil


EXPENSES_TABLE_HEADERS = ['ID', 'Date', 'Type', 'Description', 'Amount']
TABLE_STYLE = [('BACKGROUND', (0, 0), (-1, 0), colors.grey),
               ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
               ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
               ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
               ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
               ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
               ('GRID', (0, 0), (-1, -1), 1, colors.black)]


def create_report(filename, expenses):
    """
    Create a PDF expenses Report
    
    :param str filename: Report file path
    :param dict expenses: Dict of expenses dicts. e.g.:
    {
        2: {
            'date': 20200102,
            'user': 'user2',
            'expense_type': 'TYPE_2',
            'expense_description': 'DESCRIPTION 2',
            'expense_amount': 21.0
        },
        1: {
            'date': 20200101,
            'user': 'user1',
            'expense_type': 'TYPE_1',
            'expense_description': 'DESCRIPTION 1',
            'expense_amount': 12.0
        }
    }
    """
    bar_chart_expense = []
    bar_chart_date = []
    # Get different expense_types
    expense_types = set()
    
    # Create a new dict sorting the expenses by month
    month_dict = {}
    for k, v in expenses.items():
        month = str(v.get('date'))[:6]
        # Initialize an empty dict if there is no entry in the output_dict
        if month not in month_dict:
            month_dict[month] = {}
        month_dict[month][k] = v
        expense_types.add(v.get('expense_type'))

    # Create a PDF document
    doc = SimpleDocTemplate(filename, pagesize=letter)    

    # Styles for paragraphs
    styles = getSampleStyleSheet()
    title_style = styles['Title']

    # Create Story with the title of the Report
    story = []
    story.append(
        Paragraph(f"{date.today().strftime('%Y %m %d')}", title_style))
    story.append(Paragraph("Expenses Report", title_style))
    story.append(PageBreak())
    
    # Iterate through the elements in order to create a the differnt tables and charts
    for k, v in month_dict.items():
        # All expenses of the month K
        story.append(Paragraph(f"Expenses {k[:4]}-{k[4:6]}:",
                               styles['Heading2']))
        table_dict = create_table(month_dict[k])
        table = Table(table_dict.get('table'))
        table.setStyle(TableStyle(TABLE_STYLE))
        story.append(table)
        total_amount = ceil(table_dict.get('total_amount'))
        story.append(Paragraph(f"Total: {total_amount} €",
                               styles['Heading3']))
        # Add blank space
        story.append(Spacer(1, 12))
        
        # Save the total and the month in order to use it in the bar chart
        # Saving it in inverted order to represent a historical evolution towards today
        # The date will have the format yyyy-mm
        bar_chart_date.insert(0, f"{k[:4]}-{k[-2:]} - {total_amount}€")
        bar_chart_expense.insert(0, total_amount)

        # Expenses by type
        pie_labels = []
        pie_data = []
        for e_type in expense_types:
            filtered_expenses = {key: value for key, value in v.items() if value.get('expense_type') == e_type}
            type_table_dict = create_table(filtered_expenses)
            if len(type_table_dict.get('table')) > 1:
                story.append(Paragraph(f"{e_type}:", styles['Heading2']))
                table = Table(type_table_dict.get('table'))
                table.setStyle(TableStyle(TABLE_STYLE))
                story.append(table)
                type_total_expense = ceil(type_table_dict.get('total_amount'))
                story.append(Paragraph(f"Total: {type_total_expense} €", 
                                       styles['Heading3']))
                story.append(Spacer(1, 12))
                
                # Save the data to use it in the pie chart
                pie_labels.append(f"{e_type} \n{type_total_expense} €")
                pie_data.append(type_total_expense)
        
        # Create a Pie chart with the month expenses by type
        pie_chart = Pie()
        pie_chart.data = pie_data
        pie_chart.labels = pie_labels
        pie_chart.width = 400
        pie_chart.height = 200
        pie_chart.slices.strokeWidth = 0.5
        story.append(Paragraph("Expenses By Type:", title_style))
        drawing = Drawing(400, 220)
        drawing.add(pie_chart)
        story.append(drawing)
        
        story.append(PageBreak())
    
    # Create a Bar Chart to show all months expenses history
    bar_chart = HorizontalBarChart()
    bar_chart.data = [bar_chart_expense]
    bar_chart.categoryAxis.categoryNames = bar_chart_date
    bar_chart.valueAxis.valueMin = 0
    bar_chart.width = 400
    bar_chart_height = 15 * len(bar_chart_expense)
    bar_chart.height = bar_chart_height
    story.append(Paragraph("Expense History:", title_style))
    drawing = Drawing(400, bar_chart_height+20)
    drawing.add(bar_chart)
    story.append(drawing)

    # Add story to document
    doc.build(story)


def create_table(expenses_dict, table_headers=EXPENSES_TABLE_HEADERS):
    """
    Create table rows from the expenses dict
    
    :param str filename: Report file path
    :param dict expenses: Dict of expenses dicts
    :return dict return_dict: Dict with the table rows and the total amount. e.g.:
    {
        'table': [
            ['ID', 'Date', 'Type', 'Description', 'Amount'], # Table Headers
            [2, 20200102, 'TYPE_2','DESCRIPTION 2', 21.0 ],
            [1, 20200101, 'TYPE_1','DESCRIPTION 1'', 12.0 ]
        ],
        'total_amount': 33.0
    }
    """    
    # Create one total expenses table per month
    return_dict = {'table': [table_headers], 'total_amount': 0.0}
    for key, value in expenses_dict.items():
        expense = [key,
                   value.get('date'),
                   value.get('expense_type'),
                   # Limit the description to 15 chars
                   value.get('expense_description')[:15],
                   round(value.get('expense_amount'), 2)]
        return_dict['table'].append(expense)
        return_dict['total_amount'] += value.get('expense_amount')
    return return_dict
