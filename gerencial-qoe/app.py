import streamlit as st
import pandas as pd
from datetime import datetime

from modules.auth import autenticar
from modules.loader import carregar_excel, salvar_dados_atual, carregar_dados_salvos
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
menu = st.sidebar.radio(
    "Gerencial QOE",
    [
        "Dashboard Geral",
        "Setor MDU",
        "Setor IaT",
        "Setor Rede",
        "Setor DTC",
        "Análise por Cidade",
        "Exportar Relatórios",
        "Upload de Dados",
        "Histórico"
    ]
)

# UPLOAD - carrega dados salvos se não houver no session_state
if "df" not in st.session_state:
    df_salvo = carregar_dados_salvos()
    if df_salvo is not None:
        st.session_state.df = df_salvo
    else:
        # Não há dados salvos nem no session_state
        if st.session_state.perfil == "admin":
            st.info("📁 Faça o upload de uma planilha Excel (.xlsx) para começar a análise.")
            arq = st.sidebar.file_uploader("Upload Excel", type=["xlsx"])
            if arq:
                try:
                    df = carregar_excel(arq)
                    
                    # Validação de colunas essenciais
                    colunas_obrigatorias = ["QOE ANTES", "QOE DEP", "SETOR"]
                    colunas_faltando = [col for col in colunas_obrigatorias if col not in df.columns]
                    
                    if colunas_faltando:
                        st.error(f"❌ A planilha está faltando as seguintes colunas obrigatórias: {', '.join(colunas_faltando)}")
                        st.info(f"📋 Colunas obrigatórias: {', '.join(colunas_obrigatorias)}")
                    else:
                        # Garante que Node existe, criando se necessário
                        if "Node" not in df.columns:
                            df["Node"] = df.index.astype(str)
                        
                        # Converte Data Execução se existir
                        if "Data Execução" in df.columns:
                            df["Data Execução"] = pd.to_datetime(df["Data Execução"], errors="coerce")
                            df["Mes"] = df["Data Execução"].dt.to_period("M").astype(str)
                        
                        st.session_state.df = df
                        salvar_dados_atual(df)  # Salva para persistir
                        st.success(f"✅ Planilha carregada com sucesso! {len(df)} registros encontrados.")
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ Erro ao processar a planilha: {str(e)}")
                    st.info("Por favor, verifique se o arquivo está no formato correto (.xlsx)")
            st.stop()
        else:
            # Usuário comum: informa que precisa que admin carregue dados
            st.warning("⚠️ Nenhum dado foi carregado no sistema ainda.")
            st.info("Por favor, solicite ao administrador que faça o upload de uma planilha para começar a análise.")
            st.stop()

df = st.session_state.df

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
    m = calcular_metricas(df_filtrado)
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total de Ações",
            m["acoes"],
            help="Total de intervenções realizadas"
        )
    
    with col2:
        st.metric(
            "QOE Médio Antes",
            f'{m["qoe_antes"]}',
            help="Média antes das ações"
        )
    
    with col3:
        evolucao_qoe = m["qoe_depois"] - m["qoe_antes"]
        percent_evolucao = ((m["qoe_depois"] - m["qoe_antes"]) / m["qoe_antes"] * 100) if m["qoe_antes"] > 0 else 0
        st.metric(
            "QOE Médio Depois",
            f'{m["qoe_depois"]}',
            f"+{percent_evolucao:.1f}%",
            help="Média depois das ações"
        )
    
    with col4:
        st.metric(
            "Nodes Melhoraram",
            m["melhoraram"],
            help=f"De {m['acoes']} ações totais"
        )
    
    # Segunda linha de métricas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Nodes QOE ≥ 80 (Depois)",
            m["nodes_80"],
            help=f"De {m['acoes']} ações totais"
        )
    
    with col2:
        st.metric(
            "Atingiram ≥ 80",
            m["atingiram_80"],
            help=f"Nodes que estavam < 80"
        )
    
    with col3:
        st.metric(
            "% Atingiram ≥ 80",
            f"{m['perc_atingiram_80']}%",
            help="Dos que estavam abaixo de 80"
        )
    
    with col4:
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
        # Calcula métricas
        m = calcular_metricas(df_setor)
        
        # Métricas principais
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total de Ações",
                m["acoes"],
                help="Intervenções no setor"
            )
        
        with col2:
            st.metric(
                "QOE Médio Antes",
                f'{m["qoe_antes"]}',
                help="Média antes das ações"
            )
        
        with col3:
            evolucao_qoe = m["qoe_depois"] - m["qoe_antes"]
            percent_evolucao = ((m["qoe_depois"] - m["qoe_antes"]) / m["qoe_antes"] * 100) if m["qoe_antes"] > 0 else 0
            st.metric(
                "QOE Médio Depois",
                f'{m["qoe_depois"]}',
                f"+{percent_evolucao:.1f}%",
                help="Média depois das ações"
            )
        
        with col4:
            st.metric(
                "Nodes Melhoraram",
                m["melhoraram"],
                help=f"De {m['acoes']} ações totais"
            )
        
        # Segunda linha de métricas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Nodes QOE ≥ 80 (Depois)",
                m["nodes_80"],
                help=f"De {m['acoes']} ações totais"
            )
        
        with col2:
            st.metric(
                "Atingiram ≥ 80",
                m["atingiram_80"],
                help=f"De {m['acoes']} ações totais"
            )
        
        with col3:
            st.metric(
                "% Atingiram ≥ 80",
                f"{m['perc_atingiram_80']}%",
                help=f"De {m['acoes']} ações totais"
            )
        
        with col4:
            st.metric(
                "% Total com QOE ≥ 80",
                f"{m['perc_total_80']}%",
                help="Do total de ações"
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

# ANÁLISE POR CIDADE
elif menu == "Análise por Cidade":
    st.title("Análise por Cidade")
    st.caption("Análise detalhada por cidade")
    
    # Filtros
    df_filtrado, _, _ = criar_filtros(df)
    
    if "Cidade" not in df_filtrado.columns:
        st.warning("Não há coluna 'Cidade' nos dados.")
    else:
        cidades = sorted(df_filtrado["Cidade"].dropna().unique().tolist())
        cidade_selecionada = st.selectbox("Selecione a cidade", cidades)
        
        df_cidade = df_filtrado[df_filtrado["Cidade"] == cidade_selecionada].copy()
        
        if len(df_cidade) == 0:
            st.warning(f"Não há dados para a cidade {cidade_selecionada}.")
        else:
            m = calcular_metricas(df_cidade)
            
            # Métricas
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total de Ações", m["acoes"])
            with col2:
                st.metric("QOE Médio Antes", f'{m["qoe_antes"]}')
            with col3:
                st.metric("QOE Médio Depois", f'{m["qoe_depois"]}')
            with col4:
                st.metric("Nodes Melhoraram", m["melhoraram"])
            
            st.divider()
            
            col1, col2 = st.columns(2)
            with col1:
                grafico_evolucao_nodes(df_cidade)
            with col2:
                grafico_motivos(df_cidade)

# UPLOAD DE DADOS
elif menu == "Upload de Dados":
    if st.session_state.perfil == "admin":
        st.title("📁 Upload de Dados")
        st.info("Faça upload de uma nova planilha Excel (.xlsx) para substituir os dados atuais.")
        
        arq = st.file_uploader("Selecione o arquivo Excel", type=["xlsx"])
        if arq:
            try:
                df_novo = carregar_excel(arq)
                
                # Validação de colunas essenciais
                colunas_obrigatorias = ["QOE ANTES", "QOE DEP", "SETOR"]
                colunas_faltando = [col for col in colunas_obrigatorias if col not in df_novo.columns]
                
                if colunas_faltando:
                    st.error(f"❌ A planilha está faltando as seguintes colunas obrigatórias: {', '.join(colunas_faltando)}")
                    st.info(f"📋 Colunas obrigatórias: {', '.join(colunas_obrigatorias)}")
                else:
                    # Garante que Node existe
                    if "Node" not in df_novo.columns:
                        df_novo["Node"] = df_novo.index.astype(str)
                    
                    # Converte Data Execução se existir
                    if "Data Execução" in df_novo.columns:
                        df_novo["Data Execução"] = pd.to_datetime(df_novo["Data Execução"], errors="coerce")
                        df_novo["Mes"] = df_novo["Data Execução"].dt.to_period("M").astype(str)
                    
                    st.session_state.df = df_novo
                    salvar_dados_atual(df_novo)  # Salva para persistir
                    st.success(f"✅ Planilha carregada com sucesso! {len(df_novo)} registros encontrados.")
                    st.rerun()
            except Exception as e:
                st.error(f"❌ Erro ao processar a planilha: {str(e)}")
                st.info("Por favor, verifique se o arquivo está no formato correto (.xlsx)")
    else:
        st.warning("⚠️ Apenas administradores podem fazer upload de dados.")
        st.info("Você está visualizando os dados já carregados no sistema.")

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
