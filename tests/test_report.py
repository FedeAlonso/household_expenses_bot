import os
from utils.report import create_report


"""
This is not really a test file.
Just used to test manually the results of the generation of new reports

Run:
    From the root: $ pytest

"""
TEST_TILENAME = '_output/reports/test_report.pdf'
EXPENSES = {
        20: {
            'date': 20240328,
            'user': 'Nook',
            'expense_type': 'OTROS',
            'expense_description': 'SSSAAA',
            'expense_amount': 211.0
        },
        19: {
            'date': 20240328,
            'user': 'Nook',
            'expense_type': 'YOLI',
            'expense_description': 'YOLIPOLI2',
            'expense_amount': 122.0
        },
        18: {
            'date': 20240328,
            'user': 'Nook',
            'expense_type': 'YOLI',
            'expense_description': 'YOLIPOLI',
            'expense_amount': 12.0
        },
        17: {
            'date': 20240328,
            'user': 'Nook',
            'expense_type': 'YOLI',
            'expense_description': 'MES MARZO',
            'expense_amount': 23.0
        },
        16: {
            'date': 20240323,
            'user': 'Nook',
            'expense_type': 'ALIMENTACION',
            'expense_description': 'CARREFOUR',
            'expense_amount': 34.4
        },
        15: {
            'date': 20240321,
            'user': 'Nook',
            'expense_type': 'OTROS',
            'expense_description': 'PETRONOR',
            'expense_amount': 22.11
        },
        13: {
            'date': 20240321,
            'user': 'Nook',
            'expense_type': 'CASA FIJOS',
            'expense_description': 'LUZ',
            'expense_amount': 22.33
        },
        11: {
            'date': 20240321,
            'user': 'Nook',
            'expense_type': 'OTROS',
            'expense_description': 'REPSOL',
            'expense_amount': 221.0
        },
        10: {
            'date': 20240321,
            'user': 'Nook',
            'expense_type': 'YOLI',
            'expense_description': 'MES MARZO',
            'expense_amount': 132.0
        },
        9: {
            'date': 20240321,
            'user': 'Nook',
            'expense_type': 'CASA FIJOS',
            'expense_description': 'LUZ',
            'expense_amount': 22.11
        },
        8: {
            'date': 20240321,
            'user': 'Nook',
            'expense_type': 'ALIMENTACION',
            'expense_description': 'DIA',
            'expense_amount': 123.22
        },
        7: {
            'date': 20240320,
            'user': 'Nook',
            'expense_type': 'ALIMENTACION',
            'expense_description': 'CARREFUL',
            'expense_amount': 123.32
        },
        6: {
            'date': 20240320,
            'user': 'Nook',
            'expense_type': 'ALIMENTACION',
            'expense_description': 'AAA',
            'expense_amount': 222.2
        },
        5: {
            'date': 20240320,
            'user': 'Nook',
            'expense_type': 'YOLI',
            'expense_description': 'MES MARZO',
            'expense_amount': 123.222222
        },
        4: {
            'date': 20240220,
            'user': 'Nook',
            'expense_type': 'ALIMENTACION',
            'expense_description': 'AAA',
            'expense_amount': 222.2
        },
        3: {
            'date': 20240220,
            'user': 'Nook',
            'expense_type': 'YOLI',
            'expense_description': 'MES MARZO',
            'expense_amount': 123.222222
        },
        2: {
            'date': 20240120,
            'user': 'Nook',
            'expense_type': 'ALIMENTACION',
            'expense_description': 'AAA',
            'expense_amount': 222.2
        },
        1: {
            'date': 20240120,
            'user': 'Nook',
            'expense_type': 'YOLI',
            'expense_description': 'MES MARZO',
            'expense_amount': 123.222222
        }
    }
    
    
# Delete report if exist
try:
    os.remove(TEST_TILENAME)
except OSError:
    pass

def test_create_report():
    # Create the Report
    create_report(TEST_TILENAME, EXPENSES)
        
    assert os.path.exists(TEST_TILENAME)