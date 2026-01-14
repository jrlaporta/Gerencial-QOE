import sys
import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT_DIR)


import streamlit as st
import pandas as pd
from datetime import datetime

from modules.auth import autenticar
from modules.loader import carregar_planilha_local
from modules.metrics import calcular_metricas
from modules.charts import grafico_acoes_por_cidade, grafico_motivos, grafico_evolucao_nodes
from modules.pdf_export import gerar_pdf, gerar_pdf_completo

st.set_page_config("Gerencial QOE", layout="wide", page_icon="📊")

# CSS customizado
st.markdown("""
<style>
    .metric-card {
        background-color: var(--secondary-background-color);
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid rgba(250, 250, 250, 0.1);
    }
    .main-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# LOGIN
if "perfil" not in st.session_state:
    st.title("Login - Gerencial QOE")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        u = st.text_input("Usuário")
        s = st.text_input("Senha", type="password")
        if st.button("Entrar", type="primary", use_container_width=True):
            perfil = autenticar(u, s)
            if perfil:
                st.session_state.perfil = perfil
                st.rerun()
            else:
                st.error("Credenciais inválidas")
    st.stop()

# Botão de logout
st.sidebar.markdown("---")
if st.sidebar.button("🚪 Logout", use_container_width=True):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# MENU
# MENU DINÂMICO (por setor, em ordem alfabética)
setores_disponiveis = []
try:
    if "df" in st.session_state and isinstance(st.session_state.df, pd.DataFrame):
        df_tmp = st.session_state.df
        if "SETOR" in df_tmp.columns:
            setores_disponiveis = sorted(
                df_tmp["SETOR"]
                .dropna()
                .astype(str)
                .str.strip()
                .str.upper()
                .unique()
                .tolist()
            )
except Exception:
    setores_disponiveis = []

opcoes_menu = ["Dashboard Geral"] + [f"Setor {s}" for s in setores_disponiveis] + [
    "Exportar Relatórios",
    "Upload de Dados",
    "Histórico",
    "Metodologia"
]

menu = st.sidebar.radio("Gerencial QOE", opcoes_menu)


# CARREGA PLANILHA - carrega da pasta data/planilha.xlsx
def processar_dataframe(df):
    """Processa o DataFrame após carregamento"""
    # Validação de colunas essenciais
    colunas_obrigatorias = ["QOE ANTES", "QOE DEP", "SETOR"]
    colunas_faltando = [col for col in colunas_obrigatorias if col not in df.columns]
    
    if colunas_faltando:
        raise ValueError(f"A planilha está faltando as seguintes colunas obrigatórias: {', '.join(colunas_faltando)}")
    
    # Garante que Node existe, criando se necessário
    if "Node" not in df.columns:
        df["Node"] = df.index.astype(str)
    
    # Converte Data Execução se existir
    if "Data Execução" in df.columns:
        df["Data Execução"] = pd.to_datetime(df["Data Execução"], errors="coerce")
        df["Mes"] = df["Data Execução"].dt.to_period("M").astype(str)
    
    return df

# Carrega dados da planilha local (data/planilha.xlsx)
# O sistema sempre carrega a última versão do arquivo
df_carregado = carregar_planilha_local()
if df_carregado is not None:
    try:
        df = processar_dataframe(df_carregado)
        st.session_state.df = df
    except Exception as e:
        st.error(f"❌ Erro ao processar a planilha: {str(e)}")
        st.stop()
else:
    st.error("❌ Planilha não encontrada. Por favor, adicione o arquivo 'Gerencial_QOE.xlsx' na pasta 'data/' do projeto.")
    st.info("📋 O arquivo deve estar localizado em: data/Gerencial_QOE.xlsx")
    st.stop()

df = st.session_state.df

def consolidar_nodes(df_base):
    """
    Consolida dados por NODE (valor absoluto)
    Regras:
    - QOE ANTES: média
    - QOE DEP: melhor valor (máximo)
    """
    df_base = df_base.copy()
    
    # Converte QOE para numérico
    if "QOE ANTES" in df_base.columns:
        df_base["QOE ANTES"] = pd.to_numeric(df_base["QOE ANTES"], errors="coerce")
    if "QOE DEP" in df_base.columns:
        df_base["QOE DEP"] = pd.to_numeric(df_base["QOE DEP"], errors="coerce")
    
    df_nodes = (
        df_base
        .groupby("Node", as_index=False)
        .agg({
            "QOE ANTES": "mean",
            "QOE DEP": "max"
        })
    )

    df_nodes["Melhorou"] = df_nodes["QOE DEP"] > df_nodes["QOE ANTES"]
    df_nodes["Piorou"] = df_nodes["QOE DEP"] < df_nodes["QOE ANTES"]
    df_nodes["Manteve"] = df_nodes["QOE DEP"] == df_nodes["QOE ANTES"]
    df_nodes["Atingiu_80"] = df_nodes["QOE DEP"] >= 80
    df_nodes["Atingiu_80_pos"] = (df_nodes["QOE ANTES"] < 80) & (df_nodes["QOE DEP"] >= 80)

    return df_nodes


# Função auxiliar para criar filtros
def criar_filtros(df):
    """Cria filtros de mês e cidade"""
    col1, col2 = st.columns(2)
    
    meses = ["Todos os meses"] + sorted(df["Mes"].dropna().unique().tolist()) if "Mes" in df.columns else ["Todos os meses"]
    cidades = ["Todas as cidades"] + sorted(df["Cidade"].dropna().unique().tolist()) if "Cidade" in df.columns else ["Todas as cidades"]
    
    with col1:
        mes_selecionado = st.selectbox("Filtrar por Mês", meses)
    
    with col2:
        cidade_selecionada = st.selectbox("Filtrar por Cidade", cidades)
    
    # Aplica filtros
    df_filtrado = df.copy()
    if mes_selecionado != "Todos os meses":
        df_filtrado = df_filtrado[df_filtrado["Mes"] == mes_selecionado]
    if cidade_selecionada != "Todas as cidades":
        df_filtrado = df_filtrado[df_filtrado["Cidade"] == cidade_selecionada]
    
    return df_filtrado, mes_selecionado, cidade_selecionada

# DASHBOARD GERAL
if menu == "Dashboard Geral":
    st.title("Dashboard Geral")
    st.caption("Visão consolidada de todos os setores")
    
    # Filtros
    df_filtrado, _, _ = criar_filtros(df)
    
    # Calcula métricas
    df_nodes = consolidar_nodes(df_filtrado)

    m = {
        "total_nodes": len(df_nodes),
        "acoes": len(df_filtrado),
        "qoe_antes": round(df_nodes["QOE ANTES"].mean(), 1),
        "qoe_depois": round(df_nodes["QOE DEP"].mean(), 1),
        "melhoraram": int(df_nodes["Melhorou"].sum()),
        "pioraram": int(df_nodes["Piorou"].sum()),
        "mantiveram": int(df_nodes["Manteve"].sum()),
        "nodes_80": int(df_nodes["Atingiu_80"].sum()),
        "atingiram_80": int(df_nodes["Atingiu_80_pos"].sum()),
        "perc_atingiram_80": round(
            (df_nodes["Atingiu_80_pos"].sum() / max(1, (df_nodes["QOE ANTES"] < 80).sum())) * 100, 1
        )
    }

    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total de Nodes",
            m["total_nodes"],
            help="Total de nodes (valor absoluto)"
        )

    with col2:
        st.metric(
            "Total de Ações",
            m["acoes"],
            help="Total de intervenções realizadas"
        )

    with col3:
        st.metric(
            "QOE Médio Antes",
            f'{m["qoe_antes"]}',
            help="Média antes das ações"
        )

    with col4:
        evolucao_qoe = m["qoe_depois"] - m["qoe_antes"]
        percent_evolucao = (
            ((m["qoe_depois"] - m["qoe_antes"]) / m["qoe_antes"] * 100)
            if m["qoe_antes"] > 0 else 0
        )
        st.metric(
            "QOE Médio Depois",
            f'{m["qoe_depois"]}',
            f"+{percent_evolucao:.1f}%",
            help="Média depois das ações"
        )

    # Segunda linha de métricas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Nodes Melhoraram",
            m["melhoraram"],
            help=f"De {m['total_nodes']} nodes totais"
        )
    
    with col2:
        st.metric(
            "Nodes QOE ≥ 80 (Depois)",
            m["nodes_80"],
            help=f"De {m['total_nodes']} nodes totais"
        )
    
    with col3:
        st.metric(
            "Atingiram ≥ 80",
            m["atingiram_80"],
            help=f"Nodes que estavam < 80"
        )
    
    with col4:
        st.metric(
            "% Atingiram ≥ 80",
            f"{m['perc_atingiram_80']}%",
            help="Dos que estavam abaixo de 80"
        )
    
    # Terceira linha de métricas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        evolucao_texto = f"{m['melhoraram']}↑ {m['pioraram']}↓ {m['mantiveram']}="
        st.metric(
            "Evolução",
            evolucao_texto,
            help="Melhoraram ↑ | Pioraram ↓ | Mantiveram ="
        )
    
    st.divider()
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        grafico_acoes_por_cidade(df_filtrado)
    
    with col2:
        grafico_evolucao_nodes(df_filtrado)
    
    st.divider()
    
    # Gráfico de motivos
    grafico_motivos(df_filtrado)

# PÁGINAS DE SETORES
elif menu.startswith("Setor"):
    setor = menu.replace("Setor ", "")
    st.title(f"Setor {setor}")
    st.caption("Análise detalhada do setor")

    # Filtros
    df_filtrado, _, _ = criar_filtros(df)

    # Filtra por setor (case-insensitive)
    if "SETOR" in df_filtrado.columns:
        df_setor = df_filtrado[df_filtrado["SETOR"].astype(str).str.upper() == setor.upper()].copy()
    else:
        df_setor = pd.DataFrame()

    if len(df_setor) == 0:
        st.warning(f"Não há dados para o setor {setor} com os filtros selecionados.")
        st.info("Tente ajustar os filtros de mês ou cidade.")
    else:
        # Calcula métricas (POR NODE ABSOLUTO)
        df_nodes = consolidar_nodes(df_setor)

        m = {
            "total_nodes": len(df_nodes),
            "acoes": len(df_setor),
            "qoe_antes": round(df_nodes["QOE ANTES"].mean(), 1),
            "qoe_depois": round(df_nodes["QOE DEP"].mean(), 1),
            "melhoraram": int(df_nodes["Melhorou"].sum()),
            "pioraram": int(df_nodes["Piorou"].sum()),
            "mantiveram": int(df_nodes["Manteve"].sum()),
            "nodes_80": int(df_nodes["Atingiu_80"].sum()),
            "atingiram_80": int(df_nodes["Atingiu_80_pos"].sum()),
            "perc_atingiram_80": round(
                (df_nodes["Atingiu_80_pos"].sum() / max(1, (df_nodes["QOE ANTES"] < 80).sum())) * 100, 1
            ),
            "perc_total_80": round((df_nodes["Atingiu_80"].sum() / max(1, len(df_nodes))) * 100, 1)
        }

        # Métricas principais
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Total de Nodes",
                m["total_nodes"],
                help="Total de nodes (valor absoluto) no setor"
            )

        with col2:
            st.metric(
                "Total de Ações",
                m["acoes"],
                help="Intervenções no setor"
            )

        with col3:
            st.metric(
                "QOE Médio Antes",
                f'{m["qoe_antes"]}',
                help="Média antes das ações (por node absoluto)"
            )

        with col4:
            percent_evolucao = (
                ((m["qoe_depois"] - m["qoe_antes"]) / m["qoe_antes"] * 100)
                if m["qoe_antes"] > 0 else 0
            )
            st.metric(
                "QOE Médio Depois",
                f'{m["qoe_depois"]}',
                f"+{percent_evolucao:.1f}%",
                help="Média depois das ações (melhor QOE por node)"
            )

        # Segunda linha de métricas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Nodes Melhoraram",
                m["melhoraram"],
                help="Quantidade de nodes (valor absoluto) que melhoraram no período"
            )
        
        with col2:
            st.metric(
                "Nodes QOE ≥ 80 (Depois)",
                m["nodes_80"],
                help=f"De {m['total_nodes']} nodes totais"
            )
        
        with col3:
            st.metric(
                "Atingiram ≥ 80",
                m["atingiram_80"],
                help=f"Nodes que estavam < 80"
            )
        
        with col4:
            st.metric(
                "% Atingiram ≥ 80",
                f"{m['perc_atingiram_80']}%",
                help="Dos que estavam abaixo de 80"
            )
        
        st.divider()
        
        # Gráficos
        col1, col2 = st.columns(2)
        
        with col1:
            grafico_acoes_por_cidade(df_setor)
        
        with col2:
            grafico_evolucao_nodes(df_setor)
        
        st.divider()
        
        # Gráfico de motivos
        grafico_motivos(df_setor)
        
        st.divider()
        
        # Tabela de registros detalhados
        st.subheader("Registros Detalhados")
        
        # Prepara dados para exibição
        df_exibir = df_setor.copy()
        
        # Converte QOE para numérico
        df_exibir["QOE ANTES"] = pd.to_numeric(df_exibir["QOE ANTES"], errors="coerce")
        df_exibir["QOE DEP"] = pd.to_numeric(df_exibir["QOE DEP"], errors="coerce")
        
        # Calcula evolução
        df_exibir["Evolução"] = df_exibir["QOE DEP"] - df_exibir["QOE ANTES"]
        
        # Coluna >= 80
        df_exibir[">= 80"] = df_exibir["QOE DEP"].apply(lambda x: "✅" if pd.notna(x) and x >= 80 else "")
        
        # Seleciona colunas para exibir
        colunas_exibir = []
        if "Cidade" in df_exibir.columns:
            colunas_exibir.append("Cidade")
        if "Node" in df_exibir.columns:
            colunas_exibir.append("Node")
        if "Motivo" in df_exibir.columns:
            colunas_exibir.append("Motivo")
        colunas_exibir.extend(["QOE ANTES", "QOE DEP", "Evolução", ">= 80"])
        if "Responsável" in df_exibir.columns:
            colunas_exibir.append("Responsável")
        
        # Filtra apenas colunas que existem
        colunas_exibir = [col for col in colunas_exibir if col in df_exibir.columns]
        
        df_tabela = df_exibir[colunas_exibir].copy()
        
        # Formata valores
        df_tabela["QOE ANTES"] = df_tabela["QOE ANTES"].apply(lambda x: f"{x:.0f}" if pd.notna(x) else "-")
        df_tabela["QOE DEP"] = df_tabela["QOE DEP"].apply(lambda x: f"{x:.0f}" if pd.notna(x) else "-")
        df_tabela["Evolução"] = df_tabela["Evolução"].apply(
            lambda x: f"+{x:.0f}" if pd.notna(x) and x > 0 else (f"{x:.0f}" if pd.notna(x) else "-")
        )
        
        # Renomeia colunas
        df_tabela = df_tabela.rename(columns={
            "QOE ANTES": "QOE Antes",
            "QOE DEP": "QOE Depois",
            "Evolução": "Evolução",
            ">= 80": "≥ 80"
        })
        
        st.dataframe(df_tabela, use_container_width=True, hide_index=True)



# EXPORTAR RELATÓRIOS
elif menu == "Exportar Relatórios":
    st.title("📄 Exportar Relatórios")
    st.info("O relatório PDF incluirá:")
    st.markdown("""
    - **Resumo Geral**: Métricas consolidadas de todos os dados
    - **Análise por Mês**: Métricas separadas para cada mês
    - **Análise por Cidade**: Métricas separadas para cada cidade
    """)
    
    if st.button("📥 Gerar e Baixar Relatório PDF", type="primary", use_container_width=True):
        with st.spinner("Gerando relatório PDF... Isso pode levar alguns segundos."):
            try:
                pdf = gerar_pdf_completo(df, calcular_metricas)
                data_atual = datetime.now().strftime("%Y%m%d_%H%M%S")
                nome_arquivo = f"Relatorio_QOE_{data_atual}.pdf"
                st.download_button(
                    "⬇️ Baixar PDF",
                    pdf,
                    nome_arquivo,
                    mime="application/pdf",
                    use_container_width=True
                )
                st.success("✅ Relatório gerado com sucesso!")
            except Exception as e:
                st.error(f"❌ Erro ao gerar relatório: {str(e)}")

# METODOLOGIA
elif menu == "Metodologia":
    st.title("📚 Metodologia de Cálculo")
    st.markdown("""
    ## Metodologia de Cálculo:
    
    Cada linha da planilha representa uma ação técnica.
    
    Um Node pode possuir múltiplas ações no período.
    
    Para fins de análise gerencial:
    
    - **O QOE Antes de um Node é calculado pela média de suas ações.**
    
    - **O QOE Depois de um Node considera o melhor valor obtido.**
    
    - **A melhoria é avaliada comparando QOE Depois e QOE Antes.**
    
    - **No Dashboard Geral, os Nodes são consolidados globalmente.**
    
    - **Nas visões por setor, os Nodes são consolidados apenas dentro do setor selecionado.**
    
    - **O sistema sempre utiliza a última planilha carregada como base de dados ativa.**
    """)













