import os
import pandas as pd

def carregar_planilha_local():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    excel_path = os.path.join(base_dir, "..", "data", "Gerencial_QOE.xlsx")

    excel_path = os.path.normpath(excel_path)

    if os.path.exists(excel_path):
        return pd.read_excel(excel_path)

    return None


