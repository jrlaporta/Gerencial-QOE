import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def grafico_acoes_por_cidade(df):
    """Gráfico de barras horizontal com ações por cidade, ordenado do maior para o menor, com rótulos"""
    if "Cidade" not in df.columns or len(df) == 0:
        st.info("Não há dados para exibir")
        return
    
    df_agrupado = df.groupby("Cidade").size().reset_index(name="Ações")
    df_agrupado = df_agrupado.sort_values("Ações", ascending=False)  # Ordena do maior para o menor
    
    fig = px.bar(
        df_agrupado,
        x="Ações",
        y="Cidade",
        orientation="h",
        title="Ações por Cidade",
        labels={"Ações": "Número de Ações", "Cidade": ""},
        color="Ações",
        color_continuous_scale="Teal",
        text="Ações"
    )
    fig.update_traces(texttemplate='%{text}', textposition='outside')
    fig.update_layout(showlegend=False, height=300, yaxis={'categoryorder': 'total descending'})
    st.plotly_chart(fig, use_container_width=True)

def grafico_motivos(df):
    """Gráfico de colunas com top 10 motivos, mostrando total e porcentagem"""
    if "Motivo" not in df.columns or len(df) == 0:
        st.info("Não há dados para exibir")
        return
    
    df_agrupado = df.groupby("Motivo").size().reset_index(name="Quantidade")
    df_agrupado = df_agrupado.sort_values("Quantidade", ascending=False)
    
    # Pega apenas os top 10
    df_top10 = df_agrupado.head(10).copy()
    
    # Calcula porcentagem do total geral
    total_geral = df_agrupado["Quantidade"].sum()
    df_top10["Porcentagem"] = (df_top10["Quantidade"] / total_geral * 100).round(1)
    
    # Cria texto para rótulos (quantidade e porcentagem)
    df_top10["Texto"] = df_top10.apply(lambda row: f"{row['Quantidade']}<br>({row['Porcentagem']}%)", axis=1)
    
    fig = go.Figure(data=[go.Bar(
        x=df_top10["Motivo"],
        y=df_top10["Quantidade"],
        marker_color="#00E5A8",
        text=df_top10["Texto"],
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Quantidade: %{y}<br>Porcentagem: %{customdata}%<extra></extra>",
        customdata=df_top10["Porcentagem"]
    )])
    
    fig.update_layout(
        title="Principais Motivos das Ações (Top 10)",
        xaxis_title="Motivo",
        yaxis_title="Quantidade",
        height=400,
        xaxis=dict(tickangle=-45),
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)

def grafico_evolucao_nodes(df):
    """Gráfico donut mostrando evolução dos nodes (Melhoraram, Pioraram, Mantiveram) com rótulos"""
    if "Node" not in df.columns or len(df) == 0:
        st.info("Não há dados para exibir")
        return
    
    # Converte QOE para numérico
    df_calc = df.copy()
    df_calc["QOE ANTES"] = pd.to_numeric(df_calc["QOE ANTES"], errors="coerce")
    df_calc["QOE DEP"] = pd.to_numeric(df_calc["QOE DEP"], errors="coerce")
    df_calc = df_calc.dropna(subset=["QOE ANTES", "QOE DEP"])
    
    if len(df_calc) == 0:
        st.info("Não há dados válidos para exibir")
        return
    
    # Agrupa por Node e calcula evolução
    node = df_calc.groupby("Node").agg({
        "QOE ANTES": "mean",
        "QOE DEP": "mean"
    }).reset_index()
    
    node["Evolucao"] = node["QOE DEP"] - node["QOE ANTES"]
    
    melhoraram = (node["Evolucao"] > 0).sum()
    pioraram = (node["Evolucao"] < 0).sum()
    mantiveram = (node["Evolucao"] == 0).sum()
    
    labels = []
    values = []
    colors = []
    text_labels = []
    
    if melhoraram > 0:
        labels.append("Melhoraram")
        values.append(melhoraram)
        colors.append("#00E5A8")  # Verde
        percent = round(melhoraram / (melhoraram + pioraram + mantiveram) * 100)
        text_labels.append(f"Melhoraram<br>{melhoraram} ({percent}%)")
    
    if pioraram > 0:
        labels.append("Pioraram")
        values.append(pioraram)
        colors.append("#FF4444")  # Vermelho
        percent = round(pioraram / (melhoraram + pioraram + mantiveram) * 100)
        text_labels.append(f"Pioraram<br>{pioraram} ({percent}%)")
    
    if mantiveram > 0:
        labels.append("Mantiveram")
        values.append(mantiveram)
        colors.append("#888888")  # Cinza
        percent = round(mantiveram / (melhoraram + pioraram + mantiveram) * 100)
        text_labels.append(f"Mantiveram<br>{mantiveram} ({percent}%)")
    
    if len(values) == 0:
        st.info("Não há dados para exibir")
        return
    
    fig = go.Figure(data=[go.Pie(
        labels=text_labels,
        values=values,
        hole=0.5,
        marker_colors=colors,
        textinfo="label",
        textposition="inside",
        hovertemplate="<b>%{label}</b><br>Quantidade: %{value}<extra></extra>"
    )])
    
    fig.update_layout(
        title="Evolução dos Nodes",
        showlegend=True,
        height=350,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.1,
            xanchor="center",
            x=0.5
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)
