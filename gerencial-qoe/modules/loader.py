import pandas as pd
import os

PLANILHA_FILE = "data/Gerencial_QOE.xlsx"

def carregar_planilha_local():
    """Carrega a planilha da pasta data/Gerencial_QOE.xlsx"""
    if os.path.exists(PLANILHA_FILE):
        try:
            df = pd.read_excel(PLANILHA_FILE)
            return df
        except Exception as e:
            print(f"Erro ao carregar planilha: {e}")
            return None
    return None
