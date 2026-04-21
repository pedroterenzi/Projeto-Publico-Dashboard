import streamlit as st
import pandas as pd
import calendar
import plotly.graph_objects as go
from datetime import datetime
import re
import numpy as np

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(layout="wide", page_title="Bet Analytics Pro | Login", page_icon="💎")

# --- ESTILIZAÇÃO CSS (LOGIN + DASHBOARD) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #020617; }
    
    /* Centralizar Login */
    .login-container {
        max-width: 400px; margin: auto; padding: 40px;
        background: #0f172a; border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        text-align: center; margin-top: 100px;
    }

    /* Estilo dos Botões e Cards (Mantido do anterior) */
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label {
        background-color: #1e293b; border: 1px solid rgba(255, 255, 255, 0.05);
        padding: 12px 20px !important; border-radius: 12px !important;
        margin-bottom: 8px !important; width: 100% !important;
        display: block !important; cursor: pointer;
    }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label[data-checked="true"] {
        background: linear-gradient(135deg, #10b981 0%, #064e3b 100%) !important;
    }
    .metric-card {
        display: flex; flex-direction: column; justify-content: center; align-items: center;
        padding: 20px; border-radius: 20px; color: white; font-weight: 800;
        background: #0f172a; border: 1px solid rgba(255, 255, 255, 0.05);
    }
    .val-pos { color: #10b981; font-weight: 800; }
    .val-neg { color: #f43f5e; font-weight: 800; }
    .step-box { background: #1e293b; padding: 20px; border-radius: 15px; margin-bottom: 10px; border-left: 5px solid #10b981; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES DE APOIO ---
def format_br(val):
    prefix = "-" if val < 0 else ""
    return f"{prefix}R$ {abs(val):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def clean_money(val):
    if val == '--' or pd.isna(val): return 0.0
    return float(str(val).replace(',', ''))

# --- SISTEMA DE LOGIN ---
if 'auth' not in st.session_state:
    st.session_state.auth = False

def check_login():
    # Tenta pegar os usuários dos Secrets (Configuração do Streamlit Cloud)
    try:
        users = st.secrets["users"]
        if user_input in users and users[user_input] == pass_input:
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos.")
    except Exception:
        st.error("Erro técnico: Lista de usuários não configurada.")

# --- TELA DE ACESSO ---
if not st.session_state.auth:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("""
            <div style='text-align: center; margin-top: 50px;'>
                <h1 style='color: #10b981; font-size: 3rem;'>💎</h1>
                <h2 style='color: white; margin-bottom: 0;'>BET ANALYTICS PRO</h2>
                <p style='color: #64748b;'>Área Restrita para Assinantes</p>
            </div>
        """, unsafe_allow_html=True)
        
        user_input = st.text_input("E-mail")
        pass_input = st.text_input("Senha", type="password")
        
        if st.button("ACESSAR DASHBOARD", use_container_width=True):
            check_login()
        
        st.markdown("---")
        st.markdown("<p style='text-align: center; color: #94a3b8;'>Ainda não tem acesso?</p>", unsafe_allow_html=True)
        if st.button("FALAR COM SUPORTE / ASSINAR"):
            st.info("Aqui você pode colocar um link para o seu WhatsApp ou Checkout de pagamento.")
    st.stop()

# =============================================================================
# A PARTIR DAQUI SÓ APARECE SE ESTIVER LOGADO
# =============================================================================

# --- SIDEBAR (DASHBOARD LOGADO) ---
with st.sidebar:
    st.markdown("<h2 style='color: #10b981; margin-bottom: 0;'>💎 BET PRO</h2>", unsafe_allow_html=True)
    st.write(f"👤 {datetime.now().strftime('%d/%m/%Y')}")
    if st.button("Sair"):
        st.session_state.auth = False
        st.rerun()
    
    st.markdown("---")
    uploaded_file = st.file_uploader("Suba seu extrato Betfair (.csv)", type=["csv"])
    stake_padrao = st.number_input("Sua Stake Padrão (R$)", value=600.0)
    
    st.markdown("---")
    menu = st.radio("Menu", ["📈 Performance Geral", "📅 Diário de Operações", "📊 Evolução Patrimonial", "⏰ Análise de Janelas"], label_visibility="collapsed")

# --- LÓGICA DE PROCESSAMENTO E GRÁFICOS (MESMA DO ANTERIOR) ---
# [O restante do código de processamento de dados e abas entra aqui...]
if uploaded_file is not None:
    try:
        # (O código de processamento de dados e geração de gráficos continua exatamente igual ao anterior)
        st.success("Dados carregados com sucesso!")
        # ... [Inserir aqui toda a lógica de tratamento de dados que já validamos] ...
    except Exception as e:
        st.error("Erro ao processar o arquivo.")
else:
    # Guia de instrução para o usuário logado
    st.markdown("<h2 style='color: white;'>Bem-vindo ao Ambiente Pro</h2>", unsafe_allow_html=True)
    # [Guia Passo a Passo 1, 2, 3 que criamos antes]
