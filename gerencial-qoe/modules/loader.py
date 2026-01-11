import pandas as pd
import os
import pickle

DATA_FILE = "data/current_data.pkl"

def carregar_excel(arquivo):
    df = pd.read_excel(arquivo)
    return df

def salvar_dados_atual(df):
    """Salva os dados atuais em arquivo para persistir entre sessões"""
    os.makedirs("data", exist_ok=True)
    try:
        with open(DATA_FILE, "wb") as f:
            pickle.dump(df, f)
    except Exception as e:
        print(f"Erro ao salvar dados: {e}")

def carregar_dados_salvos():
    """Carrega os dados salvos anteriormente"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "rb") as f:
                return pickle.load(f)
        except Exception as e:
            print(f"Erro ao carregar dados: {e}")
            return None
    return None
