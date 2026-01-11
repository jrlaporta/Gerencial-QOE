# Gerencial QOE

Sistema de análise e gestão de métricas QOE (Quality of Experience) com dashboard interativo.

## 🚀 Funcionalidades

- **Dashboard Geral**: Visão consolidada de todos os setores
- **Análise por Setor**: MDU, IaT, Rede, DTC
- **Análise por Cidade**: Métricas detalhadas por cidade
- **Filtros**: Por mês e por cidade em todos os menus
- **Gráficos Interativos**: Visualizações com Plotly
- **Exportação de Relatórios**: PDF completo com análises por mês e cidade
- **Autenticação**: Sistema de login com perfis admin e usuário

## 📋 Pré-requisitos

- Python 3.8 ou superior
- pip

## 🔧 Instalação

1. Clone o repositório:
```bash
git clone <url-do-repositorio>
cd gerencial-qoe
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

## 🏃 Executando Localmente

```bash
streamlit run app.py
```

O sistema estará disponível em `http://localhost:8501`

## 👥 Credenciais

- **Administrador**: 
  - Usuário: `admin`
  - Senha: `admin123`

- **Usuário Comum**:
  - Usuário: `user`
  - Senha: `user123`

## 📦 Deploy no Streamlit Cloud

1. Faça push do código para o GitHub
2. Acesse [streamlit.io](https://streamlit.io)
3. Conecte seu repositório GitHub
4. Configure:
   - **Main file path**: `app.py`
   - **Python version**: 3.8 ou superior
5. Clique em "Deploy"

## 📝 Estrutura do Projeto

```
gerencial-qoe/
├── app.py                 # Aplicação principal
├── requirements.txt       # Dependências
├── modules/
│   ├── auth.py           # Autenticação
│   ├── charts.py         # Gráficos
│   ├── filters.py        # Filtros
│   ├── loader.py         # Carregamento de dados
│   ├── metrics.py        # Cálculo de métricas
│   └── pdf_export.py     # Exportação PDF
├── data/                 # Dados (gitignored)
└── reports/              # Relatórios gerados
```

## 🔒 Notas de Segurança

⚠️ **IMPORTANTE**: Altere as credenciais padrão antes de fazer deploy em produção!

Edite o arquivo `modules/auth.py` para alterar usuários e senhas.

## 📄 Licença

Este projeto é de uso interno.
