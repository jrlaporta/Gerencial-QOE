from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from io import BytesIO
from datetime import datetime
import pandas as pd

def formatar_metrica(nome, valor):
    """Formata nome de métrica para exibição"""
    nomes_formatados = {
        "acoes": "Total de Ações",
        "qoe_antes": "QOE Médio Antes",
        "qoe_depois": "QOE Médio Depois",
        "melhoraram": "Nodes Melhoraram",
        "pioraram": "Nodes Pioraram",
        "mantiveram": "Nodes Mantiveram",
        "nodes_80": "Nodes QOE ≥ 80 (Depois)",
        "atingiram_80": "Atingiram ≥ 80",
        "perc_atingiram_80": "% Atingiram ≥ 80",
        "perc_total_80": "% Total com QOE ≥ 80"
    }
    return nomes_formatados.get(nome, nome.replace("_", " ").title())

def criar_tabela_metricas(resumo, styles):
    """Cria tabela com métricas"""
    data = []
    data.append(["Métrica", "Valor"])
    
    for key, value in resumo.items():
        nome_formatado = formatar_metrica(key, value)
        if isinstance(value, float):
            valor_formatado = f"{value:.1f}"
        else:
            valor_formatado = str(value)
        data.append([nome_formatado, valor_formatado])
    
    tabela = Table(data, colWidths=[4*inch, 2*inch])
    tabela.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
    ]))
    return tabela

def gerar_pdf_completo(df, calcular_metricas_func):
    """Gera PDF completo com dados do dashboard geral, separados por mês e cidade"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    styles = getSampleStyleSheet()
    
    # Estilo para título de seção
    titulo_secao = ParagraphStyle(
        'TituloSecao',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        textColor=colors.HexColor('#1f4e78'),
        fontName='Helvetica-Bold'
    )
    
    story = []
    
    # Título principal
    story.append(Paragraph("Relatório Gerencial QOE", styles['Title']))
    story.append(Paragraph(f"Data de Geração: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Resumo Geral
    story.append(Paragraph("Resumo Geral", titulo_secao))
    resumo_geral = calcular_metricas_func(df)
    tabela_geral = criar_tabela_metricas(resumo_geral, styles)
    story.append(tabela_geral)
    story.append(Spacer(1, 0.3*inch))
    
    # Análise por Mês
    if "Mes" in df.columns and len(df["Mes"].dropna().unique()) > 0:
        story.append(Paragraph("Análise por Mês", titulo_secao))
        meses = sorted(df["Mes"].dropna().unique().tolist())
        
        for mes in meses:
            df_mes = df[df["Mes"] == mes].copy()
            if len(df_mes) > 0:
                story.append(Paragraph(f"<b>Mês: {mes}</b>", styles['Heading3']))
                resumo_mes = calcular_metricas_func(df_mes)
                tabela_mes = criar_tabela_metricas(resumo_mes, styles)
                story.append(tabela_mes)
                story.append(Spacer(1, 0.2*inch))
        
        story.append(PageBreak())
    
    # Análise por Cidade
    if "Cidade" in df.columns and len(df["Cidade"].dropna().unique()) > 0:
        story.append(Paragraph("Análise por Cidade", titulo_secao))
        cidades = sorted(df["Cidade"].dropna().unique().tolist())
        
        for cidade in cidades:
            df_cidade = df[df["Cidade"] == cidade].copy()
            if len(df_cidade) > 0:
                story.append(Paragraph(f"<b>Cidade: {cidade}</b>", styles['Heading3']))
                resumo_cidade = calcular_metricas_func(df_cidade)
                tabela_cidade = criar_tabela_metricas(resumo_cidade, styles)
                story.append(tabela_cidade)
                story.append(Spacer(1, 0.2*inch))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

def gerar_pdf(titulo, resumo):
    """Função legada para compatibilidade - mantida para não quebrar código existente"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()

    story = [Paragraph(f"<b>{titulo}</b>", styles["Title"])]

    for k, v in resumo.items():
        story.append(Paragraph(f"{k}: {v}", styles["Normal"]))

    doc.build(story)
    buffer.seek(0)
    return buffer
