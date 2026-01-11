def aplicar_filtros(df, setor=None, cidade=None, mes=None):
    if setor:
        df = df[df["SETOR"] == setor]
    if cidade:
        df = df[df["Cidade"] == cidade]
    if mes:
        df = df[df["Mes"] == mes]
    return df
