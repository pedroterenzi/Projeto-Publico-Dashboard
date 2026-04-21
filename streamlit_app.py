import streamlit as st
import pandas as pd
import calendar
import plotly.graph_objects as go
from datetime import datetime
import re
import numpy as np
import json

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(layout="wide", page_title="Bet Analytics Pro", page_icon="💎")

# --- ESTILIZAÇÃO CSS (IGUAL À ANTERIOR) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #020617; }
    .main .block-container { max-width: 1200px; padding-top: 1.5rem; margin: auto; }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label > div:first-child { display: none !important; }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label {
        background-color: #1e293b; border: 1px solid rgba(255, 255, 255, 0.05);
        padding: 12px 20px !important; border-radius: 12px !important;
        margin-bottom: 8px !important; width: 100% !important;
        display: block !important; transition: all 0.3s ease; cursor: pointer;
    }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label[data-checked="true"] {
        background: linear-gradient(135deg, #10b981 0%, #064e3b 100%) !important;
        border: none !important; box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
    }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label div[data-testid="stMarkdownContainer"] p {
        color: white !important; font-weight: 700 !important; font-size: 0.9rem !important;
        margin: 0 !important; text-align: center;
    }
    .metric-card {
        display: flex; flex-direction: column; justify-content: center; align-items: center;
        padding: 20px 10px; border-radius: 20px; color: white; font-weight: 800;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3); border: 1px solid rgba(255, 255, 255, 0.05);
        height: 110px; width: 100%; margin-bottom: 15px;
    }
    .perf-card { 
        background: #0f172a; border-radius: 12px; padding: 15px 20px; 
        display: flex; align-items: center; justify-content: space-between; 
        border: 1px solid rgba(255, 255, 255, 0.05); margin-bottom: 8px;
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
    try: return float(str(val).replace(',', ''))
    except: return 0.0

# --- INICIALIZAÇÃO DE ESTADO ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'metodos_salvos' not in st.session_state: st.session_state.metodos_salvos = {}
if 'lista_metodos' not in st.session_state: 
    st.session_state.lista_metodos = ["Match Odds", "Under 2.5", "Over 2.5", "Under 1.5", "Over 1.5", "Correct Score", "Sem Categoria"]

# --- FUNÇÃO DE PROCESSAMENTO COM CACHE (CORRIGE O DUPLO CLIQUE) ---
@st.cache_data(show_spinner=False)
def processar_extrato(file_content, stake_padrao):
    df_raw = pd.read_csv(file_content)
    map_cols = {
        'Data': ['Data', 'Date', 'data'],
        'Desc': ['Descrição', 'Description', 'Evento', 'Market'],
        'Val': ['Valor (R$)', 'Amount', 'Profit/Loss', 'Valor'],
        'Ent': ['Entrada de Dinheiro (R$)', 'In'],
        'Sai': ['Saída de Dinheiro (R$)', 'Out']
    }
    def get_c(key):
        for c in df_raw.columns:
            if c in map_cols[key]: return c
        return None

    c_data, c_desc, c_val, c_ent, c_sai = get_c('Data'), get_c('Desc'), get_c('Val'), get_c('Ent'), get_c('Sai')
    
    if c_val: df_raw['Valor_Final'] = df_raw[c_val].apply(clean_money)
    else: df_raw['Valor_Final'] = df_raw[c_ent].apply(clean_money) + df_raw[c_sai].apply(clean_money)

    meses_pt = {'jan': 'Jan', 'fev': 'Feb', 'mar': 'Mar', 'abr': 'Apr', 'mai': 'May', 'jun': 'Jun', 'jul': 'Jul', 'ago': 'Aug', 'set': 'Sep', 'out': 'Oct', 'nov': 'Nov', 'dez': 'Dec'}
    df_raw[c_data] = df_raw[c_data].astype(str)
    for pt, en in meses_pt.items(): df_raw[c_data] = df_raw[c_data].str.replace(pt, en, case=False)
    
    df_raw['Dt_Obj'] = pd.to_datetime(df_raw[c_data], errors='coerce')
    df_raw = df_raw.dropna(subset=['Dt_Obj'])
    df_raw = df_raw[~df_raw[c_desc].str.contains('Depósito|Deposit|Withdraw|Saque|Transferência', case=False, na=False)].copy()
    df_raw['ID_Ref'] = df_raw[c_desc].apply(lambda x: re.search(r'Ref: (\d+)', str(x)).group(1) if re.search(r'Ref: (\d+)', str(x)) else str(x))
    
    df_clean = df_raw.groupby(['ID_Ref', 'Dt_Obj', c_desc]).agg({'Valor_Final': 'sum'}).reset_index()
    df_clean['Data_Apenas'] = df_clean['Dt_Obj'].dt.date
    df_clean['Hora'] = df_clean['Dt_Obj'].dt.hour
    df_clean['Dia_Num'] = df_clean['Dt_Obj'].dt.dayofweek
    return df_clean, c_desc

# --- LOGIN ---
if not st.session_state.auth:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("<div style='text-align: center; margin-top: 100px;'><h1 style='color: #10b981;'>💎 BET ANALYTICS PRO</h1></div>", unsafe_allow_html=True)
        u_in = st.text_input("E-mail")
        p_in = st.text_input("Senha", type="password")
        if st.button("ACESSAR", use_container_width=True):
            if u_in in st.secrets["users"] and st.secrets["users"][u_in] == p_in:
                st.session_state.auth = True
                st.rerun()
            else: st.error("Erro no login.")
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h2 style='color: #10b981; margin-bottom: 0;'>💎 BET PRO</h2>", unsafe_allow_html=True)
    if st.button("Sair"):
        st.session_state.auth = False
        st.rerun()
    st.markdown("---")
    uploaded_file = st.file_uploader("1. Suba o Extrato Betfair (.csv)", type=["csv"])
    
    uploaded_backup = st.file_uploader("2. Opcional: Suba seu Backup (.json)", type=["json"])
    if uploaded_backup:
        st.session_state.metodos_salvos = json.load(uploaded_backup)

    stake_padrao = st.number_input("Sua Stake Padrão (R$)", value=600.0)
    st.markdown("---")
    menu = st.radio("Navegação", ["📈 Performance Geral", "📅 Diário de Operações", "📋 Log de Entradas", "⏰ Análise de Janelas", "⚙️ Gestão de Métodos", "📖 Como Extrair"], label_visibility="collapsed")

# --- LÓGICA DE DADOS ---
if uploaded_file is not None:
    try:
        df_clean, c_desc = processar_extrato(uploaded_file, stake_padrao)
        
        # Atribuição de Método
        def get_metodo(row):
            if row['ID_Ref'] in st.session_state.metodos_salvos:
                return st.session_state.metodos_salvos[row['ID_Ref']]
            return str(row[c_desc]).split('Ref:')[0].split('/')[-1].strip() if '/' in str(row[c_desc]) else "Sem Categoria"
        
        df_clean['Metodo'] = df_clean.apply(get_metodo, axis=1)

        # --- RENDERIZAÇÃO DAS ABAS ---
        if menu == "📈 Performance Geral":
            total_l = df_clean['Valor_Final'].sum()
            bg = "linear-gradient(135deg, #10b981 0%, #064e3b 100%)" if total_l >= 0 else "linear-gradient(135deg, #ef4444 0%, #7f1d1d 100%)"
            st.markdown(f'<div class="metric-card" style="background: {bg};"><div>LUCRO LÍQUIDO TOTAL</div><div style="font-size: 2.5rem;">{format_br(total_l)}</div></div>', unsafe_allow_html=True)
            res = df_clean.groupby('Metodo').agg({'Valor_Final': 'sum', 'ID_Ref': 'count'}).rename(columns={'Valor_Final': 'Lucro', 'ID_Ref': 'Qtd'}).sort_values('Lucro', ascending=False)
            for m, row in res.iterrows():
                cor = "val-pos" if row['Lucro'] >= 0 else "val-neg"
                st.markdown(f'<div class="perf-card"><div><b>{m}</b><br><small>{int(row["Qtd"])} entradas</small></div><div style="text-align:right"><span class="{cor}">{format_br(row["Lucro"])}</span></div></div>', unsafe_allow_html=True)

        elif menu == "📋 Log de Entradas":
            st.subheader("📋 Log de Apostas")
            itens_por_pag = 20
            if 'pag' not in st.session_state: st.session_state.pag = 0
            
            start = st.session_state.pag * itens_por_pag
            end = start + itens_por_pag
            
            df_view = df_clean.sort_values('Dt_Obj', ascending=False)
            for idx, row in df_view.iloc[start:end].iterrows():
                with st.expander(f"{row['Dt_Obj'].strftime('%d/%m %H:%M')} | {row[c_desc][:50]}... | {format_br(row['Valor_Final'])}"):
                    novo = st.selectbox(f"Método:", st.session_state.lista_metodos, 
                                      index=st.session_state.lista_metodos.index(row['Metodo']) if row['Metodo'] in st.session_state.lista_metodos else 0,
                                      key=f"btn_{row['ID_Ref']}")
                    if novo != row['Metodo']:
                        st.session_state.metodos_salvos[row['ID_Ref']] = novo
                        st.rerun()
            
            c_p, c_n = st.columns(2)
            if c_p.button("⬅️ Anterior") and st.session_state.pag > 0:
                st.session_state.pag -= 1
                st.rerun()
            if c_n.button("Próximo ➡️") and end < len(df_view):
                st.session_state.pag += 1
                st.rerun()

        elif menu == "📅 Diário de Operações":
            ano_c = st.sidebar.selectbox("Ano", sorted(df_clean['Dt_Obj'].dt.year.unique(), reverse=True))
            meses_n = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
            mes_sel = st.sidebar.selectbox("Mês", meses_n, index=datetime.now().month - 1)
            mes_num = meses_n.index(mes_sel) + 1
            df_mes = df_clean[(df_clean['Dt_Obj'].dt.year == ano_c) & (df_clean['Dt_Obj'].dt.month == mes_num)]
            l_mes = df_mes['Valor_Final'].sum()
            st.markdown(f'<div class="monthly-profit-card" style="border: 2px solid {"#10b981" if l_mes>=0 else "#f43f5e"};">LUCRO {mes_sel.upper()}: {format_br(l_mes)}</div>', unsafe_allow_html=True)
            cal = calendar.Calendar(firstweekday=0)
            dias = list(cal.itermonthdays(ano_c, mes_num))
            l_dia = df_mes.groupby(df_mes['Dt_Obj'].dt.day)['Valor_Final'].sum()
            html = '<div class="calendar-grid">'
            for n in ['SEG','TER','QUA','QUI','SEX','SAB','DOM']: html += f'<div class="day-name">{n}</div>'
            for d in dias:
                if d == 0: html += '<div style="opacity:0"></div>'
                else:
                    v = l_dia.get(d, 0)
                    cl = "day-card green-card" if v > 0.05 else "day-card red-card" if v < -0.05 else "day-card"
                    html += f'<div class="{cl}"><span class="day-number">{d}</span><span class="day-value">{format_br(v) if abs(v)>0.05 else ""}</span></div>'
            st.markdown(html + '</div>', unsafe_allow_html=True)

        elif menu == "⚙️ Gestão de Métodos":
            novo_m = st.text_input("Novo método:")
            if st.button("Adicionar"): st.session_state.lista_metodos.append(novo_m)
            st.download_button("BAIXAR BACKUP (.JSON)", json.dumps(st.session_state.metodos_salvos), file_name="backup_bet.json")

        elif menu == "📊 Evolução Patrimonial":
            df_ev = df_clean.groupby('Data_Apenas')['Valor_Final'].sum().reset_index()
            df_ev['Acumulado'] = df_ev['Valor_Final'].cumsum()
            fig = go.Figure(go.Scatter(x=df_ev['Data_Apenas'], y=df_ev['Acumulado'], mode='lines', line=dict(color='#10b981', width=3, shape='spline')))
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=500)
            st.plotly_chart(fig, use_container_width=True)

        elif menu == "⏰ Análise de Janelas":
            res_d = df_clean.groupby('Dia_Num')['Valor_Final'].sum().sort_index()
            d_s = {0: 'Segunda', 1: 'Terça', 2: 'Quarta', 3: 'Quinta', 4: 'Sexta', 5: 'Sábado', 6: 'Domingo'}
            for idx, val in res_d.items():
                st.markdown(f'<div class="perf-card"><b>{d_s[idx]}</b><span>{format_br(val)}</span></div>', unsafe_allow_html=True)

    except Exception as e: st.error("Erro ao carregar dados.")
else:
    st.info("Suba seu CSV na barra lateral.")
