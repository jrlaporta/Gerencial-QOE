import pandas as pd

def classificar_qoe(v):
    if pd.isna(v): return "—"
    if v < 40: return "🔴"
    if v < 80: return "🟡"
    return "🟢"

def calcular_metricas(df):
    # Cria cópia para não modificar o DataFrame original
    df_calc = df.copy()
    
    # Valida colunas necessárias
    colunas_necessarias = ["QOE ANTES", "QOE DEP"]
    if not all(col in df_calc.columns for col in colunas_necessarias):
        raise ValueError(f"Colunas necessárias não encontradas: {colunas_necessarias}")
    
    # Converte colunas QOE para numérico, tratando valores inválidos
    df_calc["QOE ANTES"] = pd.to_numeric(df_calc["QOE ANTES"], errors="coerce")
    df_calc["QOE DEP"] = pd.to_numeric(df_calc["QOE DEP"], errors="coerce")
    
    # Remove linhas onde ambas as colunas QOE são NaN
    df_calc = df_calc.dropna(subset=["QOE ANTES", "QOE DEP"], how="all")
    
    # Verifica se há dados válidos
    if len(df_calc) == 0:
        return {
            "acoes": 0,
            "qoe_antes": 0,
            "qoe_depois": 0,
            "melhoraram": 0,
            "pioraram": 0,
            "mantiveram": 0,
            "nodes_80": 0,
            "atingiram_80": 0,
            "perc_atingiram_80": 0,
            "perc_total_80": 0
        }
    
    # Agrupa por Node se a coluna existir, senão usa índice
    if "Node" in df_calc.columns:
        node = df_calc.groupby("Node").agg({
            "QOE ANTES": "mean",
            "QOE DEP": "mean"
        }).reset_index()
    else:
        # Se não houver coluna Node, cria um grupo único
        node = pd.DataFrame({
            "Node": ["Todos"],
            "QOE ANTES": [df_calc["QOE ANTES"].mean()],
            "QOE DEP": [df_calc["QOE DEP"].mean()]
        })

    node["Evolucao"] = node["QOE DEP"] - node["QOE ANTES"]

    melhoraram = (node["Evolucao"] > 0).sum()
    pioraram = (node["Evolucao"] < 0).sum()
    mantiveram = (node["Evolucao"] == 0).sum()

    atingiram_80 = ((node["QOE ANTES"] < 80) & (node["QOE DEP"] >= 80)).sum()
    base_abaixo = (node["QOE ANTES"] < 80).sum()

    return {
        "acoes": len(df_calc),
        "qoe_antes": round(df_calc["QOE ANTES"].mean(), 1) if not df_calc["QOE ANTES"].isna().all() else 0,
        "qoe_depois": round(df_calc["QOE DEP"].mean(), 1) if not df_calc["QOE DEP"].isna().all() else 0,
        "melhoraram": melhoraram,
        "pioraram": pioraram,
        "mantiveram": mantiveram,
        "nodes_80": (node["QOE DEP"] >= 80).sum(),
        "atingiram_80": atingiram_80,
        "perc_atingiram_80": round((atingiram_80 / base_abaixo) * 100, 1) if base_abaixo else 0,
        "perc_total_80": round(((node["QOE DEP"] >= 80).sum() / len(node)) * 100, 1) if len(node) else 0
    }
