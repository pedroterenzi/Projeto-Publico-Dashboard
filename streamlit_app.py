import streamlit as st
import pandas as pd
import calendar
import plotly.graph_objects as go
from datetime import datetime, date
import re
import numpy as np
import json

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(layout="wide", page_title="Bet Analytics Pro", page_icon="💎")

# --- ESTILIZAÇÃO CSS PREMIUM REFINADA ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;900&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #020617; }
    .main .block-container { max-width: 1200px; padding-top: 1.5rem; margin: auto; }

    /* NAVEGAÇÃO SIDEBAR */
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

    /* CARDS DE MÉTRICAS */
    .metric-card {
        display: flex; flex-direction: column; justify-content: center; align-items: center;
        padding: 20px 10px; border-radius: 20px; color: white; font-weight: 800;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3); border: 1px solid rgba(255, 255, 255, 0.05);
        height: 110px; width: 100%; margin-bottom: 15px;
    }
    .metric-card-grande { height: 140px; margin-bottom: 20px; }
    .metric-title { font-size: 0.75rem; text-transform: uppercase; opacity: 0.7; letter-spacing: 1.5px; margin-bottom: 8px; }
    .metric-value { font-size: 1.8rem; margin: 0; letter-spacing: -1px; }
    .metric-value-grande { font-size: 2.8rem; }

    /* CALENDÁRIO */
    .monthly-profit-card {
        padding: 20px; border-radius: 15px; text-align: center; color: white; font-weight: 800;
        margin-bottom: 20px; border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .calendar-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 8px; margin-top: 15px; }
    .day-name { text-align: center; color: #475569; font-weight: 900; font-size: 0.65rem; text-transform: uppercase; padding-bottom: 5px; }
    .day-card { 
        background: #0f172a; border-radius: 10px; padding: 10px; min-height: 100px; 
        display: flex; flex-direction: column; justify-content: space-between; align-items: flex-start;
        border: 1px solid rgba(255, 255, 255, 0.03); overflow: hidden; box-sizing: border-box;
    }
    .green-card { background: linear-gradient(135deg, #059669 0%, #064e3b 100%); border: none; }
    .red-card { background: linear-gradient(135deg, #dc2626 0%, #7f1d1d 100%); border: none; }
    .day-number { font-size: 1.1rem; font-weight: 900; color: #ffffff !important; line-height: 1; text-shadow: 1px 1px 2px rgba(0,0,0,0.5); }
    .day-value { font-size: 0.75rem; font-weight: 800; color: white; width: 100%; text-align: right; white-space: nowrap; }

    /* PERFORMANCE E SEQUENCIAS */
    .perf-card { 
        background: #0f172a; border-radius: 12px; padding: 15px 18px; 
        display: flex; align-items: center; justify-content: space-between; 
        border: 1px solid rgba(255, 255, 255, 0.05); margin-bottom: 10px;
        height: 90px; width: 100%; box-sizing: border-box;
    }
    .val-pos { color: #10b981; font-weight: 800; }
    .val-neg { color: #f43f5e; font-weight: 800; }
    .section-title {
        color: white; font-size: 1.1rem; font-weight: 800; margin-bottom: 15px; 
        padding-left: 5px; border-left: 4px solid #10b981; line-height: 1;
    }
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

# --- ESTADOS DE SESSÃO ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'is_premium' not in st.session_state: st.session_state.is_premium = False
if 'metodos_salvos' not in st.session_state: st.session_state.metodos_salvos = {}
if 'lista_metodos' not in st.session_state: 
    st.session_state.lista_metodos = ["Match Odds", "Under 2.5", "Over 2.5", "Under 1.5", "Over 1.5", "Correct Score", "Sem Categoria"]
if 'pagina_atual' not in st.session_state: st.session_state.pagina_atual = 1

# --- LOGIN REFORMULADO (FACHADA) ---
if not st.session_state.auth:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("<div style='text-align: center; margin-top: 80px;'><h1 style='color: #10b981;'>💎 BET ANALYTICS PRO</h1><p style='color: #64748b;'>A inteligência por trás dos seus Greens</p></div>", unsafe_allow_html=True)
        
        with st.container():
            st.markdown("<div style='background: #1e293b; padding: 25px; border-radius: 20px; border: 1px solid rgba(255,255,255,0.05);'>", unsafe_allow_html=True)
            u_in = st.text_input("E-mail")
            p_in = st.text_input("Senha", type="password")
            if st.button("ACESSAR ÁREA PREMIUM", use_container_width=True):
                try:
                    users = st.secrets["users"]
                    if u_in in users and users[u_in] == p_in:
                        st.session_state.auth = True
                        st.session_state.is_premium = True
                        st.rerun()
                    else: st.error("Acesso Negado.")
                except: st.error("Erro de configuração de usuários nos Secrets.")
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div style='text-align: center; margin: 20px 0; color: #475569;'>OU</div>", unsafe_allow_html=True)
        
        if st.button("ENTRAR COM VERSÃO FREE (BÁSICA)", use_container_width=True):
            st.session_state.auth = True
            st.session_state.is_premium = False
            st.rerun()
    st.stop()

# --- SIDEBAR DINÂMICO ---
with st.sidebar:
    st.markdown(f"<h2 style='color: #10b981;'>💎 BET {'PRO' if st.session_state.is_premium else 'FREE'}</h2>", unsafe_allow_html=True)
    if st.button("Sair / Trocar Conta"):
        st.session_state.auth = False
        st.rerun()
    st.markdown("---")
    uploaded_file = st.file_uploader("1. Carregar Extrato Betfair (.csv)", type=["csv"])
    
    if st.session_state.is_premium:
        uploaded_backup = st.file_uploader("2. Carregar Backup de Métodos (.json)", type=["json"])
        if uploaded_backup:
            st.session_state.metodos_salvos = json.load(uploaded_backup)
            st.success("Backup Aplicado!")
    
    stake_padrao = st.number_input("Sua Stake Padrão (R$)", value=600.0)
    st.markdown("---")
    
    opcoes_menu = ["📈 Performance Geral"]
    if st.session_state.is_premium:
        opcoes_menu += ["📅 Diário de Operações", "📋 Log de Entradas", "📊 Evolução Patrimonial", "⏰ Análise de Janelas", "🔥 Sequências", "⚙️ Gestão de Métodos"]
    opcoes_menu += ["📖 Como Extrair"]
    
    menu = st.radio("Menu", opcoes_menu, label_visibility="collapsed")
    
    if not st.session_state.is_premium:
        st.markdown("---")
        st.markdown("<div style='background: #064e3b; padding: 15px; border-radius: 10px; font-size: 0.8rem; color: white; text-align: center;'><b>DICA PREMIUM:</b><br>Assine o Plano Pro para liberar o Calendário, Log e Análise por Horários.</div>", unsafe_allow_html=True)

# --- PROCESSAMENTO DE DADOS ---
if uploaded_file is not None:
    try:
        df_raw = pd.read_csv(uploaded_file)
        map_cols = {'Data':['Data','Date','data'],'Desc':['Descrição','Description','Evento','Market'],'Val':['Valor (R$)','Amount','Profit/Loss','Valor'],'Ent':['Entrada de Dinheiro (R$)', 'In'],'Sai':['Saída de Dinheiro (R$)', 'Out']}
        def get_c(key):
            for c in df_raw.columns:
                if c in map_cols[key]: return c
            return None
        c_data, c_desc, c_val, c_ent, c_sai = get_c('Data'), get_c('Desc'), get_c('Val'), get_c('Ent'), get_c('Sai')

        if c_val: df_raw['V_F'] = df_raw[c_val].apply(clean_money)
        else: df_raw['V_F'] = df_raw[c_ent].apply(clean_money) + df_raw[c_sai].apply(clean_money)

        meses_pt = {'jan':'Jan','fev':'Feb','mar':'Mar','abr':'Apr','mai':'May','jun':'Jun','jul':'Jul','ago':'Aug','set':'Sep','out':'Oct','nov':'Nov','dez':'Dec'}
        df_raw[c_data] = df_raw[c_data].astype(str)
        for pt, en in meses_pt.items(): df_raw[c_data] = df_raw[c_data].str.replace(pt, en, case=False)
        
        df_raw['Dt_Obj'] = pd.to_datetime(df_raw[c_data], errors='coerce')
        df_raw = df_raw.dropna(subset=['Dt_Obj'])
        df_raw = df_raw[~df_raw[c_desc].str.contains('Depósito|Deposit|Withdraw|Saque|Transferência', case=False, na=False)].copy()
        df_raw['ID_Ref'] = df_raw[c_desc].apply(lambda x: re.search(r'Ref: (\d+)', str(x)).group(1) if re.search(r'Ref: (\d+)', str(x)) else str(x))
        
        df_clean = df_raw.groupby(['ID_Ref', 'Dt_Obj', c_desc]).agg({'V_F': 'sum'}).reset_index()
        
        def get_metodo(row):
            if row['ID_Ref'] in st.session_state.metodos_salvos: return st.session_state.metodos_salvos[row['ID_Ref']]
            return str(row[c_desc]).split('Ref:')[0].split('/')[-1].strip() if '/' in str(row[c_desc]) else "Match Odds"
        
        df_clean['Metodo'] = df_clean.apply(get_metodo, axis=1)
        df_clean['Data_Apenas'] = df_clean['Dt_Obj'].dt.date
        df_clean['Hora'] = df_clean['Dt_Obj'].dt.hour
        df_clean['Dia_Num'] = df_clean['Dt_Obj'].dt.dayofweek
        df_clean = df_clean.sort_values('Dt_Obj')

        # --- NAVEGAÇÃO ---

        if menu == "📈 Performance Geral":
            st.markdown("<h2 style='color: white;'>📈 Performance Geral</h2>", unsafe_allow_html=True)
            p_perf = st.date_input("Período de Análise", [df_clean['Data_Apenas'].min(), df_clean['Data_Apenas'].max()])
            
            if len(p_perf) == 2:
                df_aba = df_clean[(df_clean['Data_Apenas'] >= p_perf[0]) & (df_clean['Data_Apenas'] <= p_perf[1])].copy()
                total_l = df_aba['V_F'].sum()
                entradas = len(df_aba); wr_geral = (len(df_aba[df_aba['V_F'] > 0.05]) / entradas * 100) if entradas > 0 else 0
                odd_m = df_aba[df_aba['V_F'] > 0]['V_F'].apply(lambda x: (x/stake_padrao)+1).mean() if not df_aba[df_aba['V_F'] > 0].empty else 0
                
                curr_streak = 0
                for v in reversed(df_aba['V_F'].tolist()):
                    if v > 0.05: curr_streak += 1
                    elif v < -0.05: break

                bg_lucro = "linear-gradient(135deg, #10b981 0%, #064e3b 100%)" if total_l >= 0 else "linear-gradient(135deg, #ef4444 0%, #7f1d1d 100%)"
                st.markdown(f'<div class="metric-card metric-card-grande" style="background: {bg_lucro};"><div class="metric-title">Lucro Líquido Consolidado</div><div class="metric-value metric-value-grande">{format_br(total_l)}</div></div>', unsafe_allow_html=True)
                
                c1, c2, c3, c4, c5 = st.columns(5)
                with c1: st.markdown(f'<div class="metric-card"><div class="metric-title">Taxa de Acerto</div><div class="metric-value">{wr_geral:.1f}%</div></div>', unsafe_allow_html=True)
                with c2: st.markdown(f'<div class="metric-card"><div class="metric-title">Saldo Stakes</div><div class="metric-value">{total_l/stake_padrao:,.2f}</div></div>', unsafe_allow_html=True)
                with c3: st.markdown(f'<div class="metric-card"><div class="metric-title">Total Entradas</div><div class="metric-value">{entradas}</div></div>', unsafe_allow_html=True)
                with c4: st.markdown(f'<div class="metric-card"><div class="metric-title">Odd Média</div><div class="metric-value">{odd_m:.2f}</div></div>', unsafe_allow_html=True)
                with c5: st.markdown(f'<div class="metric-card" style="background: #1e293b;"><div class="metric-title">Sequência Atual</div><div class="metric-value" style="color: #10b981;">{curr_streak} 🔥</div></div>', unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown('<div class="section-title">Por Método</div>', unsafe_allow_html=True)
                    res = df_aba.groupby('Metodo').agg({'V_F': ['sum', 'count']}).reset_index()
                    res.columns = ['Metodo', 'Lucro', 'Qtd']
                    for _, row in res.sort_values('Lucro', ascending=False).iterrows():
                        wr_m = (len(df_aba[(df_aba['Metodo']==row['Metodo']) & (df_aba['V_F']>0.05)]) / row['Qtd'] * 100) if row['Qtd']>0 else 0
                        st.markdown(f'<div class="perf-card"><div><b>{row["Metodo"]}</b><br><small style="color:#64748b">{int(row["Qtd"])} entr. | WR: {wr_m:.1f}%</small></div><div style="text-align:right;"><span class="{"val-pos" if row["Lucro"]>=0 else "val-neg"}">{format_br(row["Lucro"])}</span></div></div>', unsafe_allow_html=True)
                with col2:
                    st.markdown('<div class="section-title">Por Range de Odd</div>', unsafe_allow_html=True)
                    df_aba['Odd_T'] = df_aba['V_F'].apply(lambda x: (x/stake_padrao)+1 if x > 0 else 1.50)
                    df_aba['Range'] = pd.cut(df_aba['Odd_T'], bins=[0,1.3,1.59,1.79,2.09,3.0,1000], labels=['1.00-1.30','1.31-1.59','1.60-1.79','1.80-2.09','2.10-3.00','3.00+'])
                    res_odd = df_aba.groupby('Range', observed=False).agg({'V_F': ['sum', 'count']}).reset_index()
                    res_odd.columns = ['Range', 'Lucro', 'Qtd']
                    for _, row in res_odd.iterrows():
                        st.markdown(f'<div class="perf-card"><div><b>Odd: {row["Range"]}</b><br><small style="color:#64748b">{int(row["Qtd"])} entradas</small></div><div style="text-align:right;"><span class="{"val-pos" if row["Lucro"]>=0 else "val-neg"}">{format_br(row["Lucro"])}</span></div></div>', unsafe_allow_html=True)

        elif menu == "📅 Diário de Operações" and st.session_state.is_premium:
            st.markdown("<h2 style='color: white;'>📅 Diário de Operações</h2>", unsafe_allow_html=True)
            ano_c = st.sidebar.selectbox("Ano", sorted(df_clean['Dt_Obj'].dt.year.unique(), reverse=True))
            meses_n = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
            mes_sel = st.sidebar.selectbox("Mês", meses_n, index=datetime.now().month - 1)
            mes_num = meses_n.index(mes_sel) + 1
            df_mes = df_clean[(df_clean['Dt_Obj'].dt.year == ano_c) & (df_clean['Dt_Obj'].dt.month == mes_num)]
            l_mes = df_mes['V_F'].sum(); wr_mes = (len(df_mes[df_mes['V_F'] > 0.05]) / len(df_mes) * 100) if len(df_mes) > 0 else 0
            st.markdown(f'<div class="monthly-profit-card" style="border: 2px solid {"#10b981" if l_mes>=0 else "#f43f5e"};"><small>LUCRO {mes_sel.upper()} | WR: {wr_mes:.1f}%</small><br><span style="font-size: 2rem;">{format_br(l_mes)}</span></div>', unsafe_allow_html=True)
            l_dia = df_mes.groupby(df_mes['Dt_Obj'].dt.day)['V_F'].sum()
            cal_obj = calendar.Calendar(firstweekday=0); dias = list(cal_obj.itermonthdays(ano_c, mes_num))
            html = '<div class="calendar-grid">'
            for n in ['SEG','TER','QUA','QUI','SEX','SAB','DOM']: html += f'<div class="day-name">{n}</div>'
            for d in dias:
                if d == 0: html += '<div style="opacity:0"></div>'
                else:
                    v = l_dia.get(d, 0); cl = "day-card green-card" if v > 0.05 else "day-card red-card" if v < -0.05 else "day-card"
                    html += f'<div class="{cl}"><span class="day-number">{d}</span><span class="day-value">{format_br(v) if abs(v)>0.05 else ""}</span></div>'
            st.markdown(html + '</div>', unsafe_allow_html=True)

        elif menu == "📋 Log de Entradas" and st.session_state.is_premium:
            st.subheader("📋 Classificação de Apostas")
            p_log = st.date_input("Período do Log", [df_clean['Data_Apenas'].min(), df_clean['Data_Apenas'].max()])
            if len(p_log) == 2:
                search = st.text_input("Filtrar")
                df_v = df_clean[(df_clean['Data_Apenas'] >= p_log[0]) & (df_clean['Data_Apenas'] <= p_log[1])]
                df_v = df_v[df_v[c_desc].str.contains(search, case=False)] if search else df_v
                df_v = df_v.sort_values('Dt_Obj', ascending=False)
                itens = 20; total_p = (len(df_v) // itens) + 1
                col_n1, col_n2 = st.columns([1, 4])
                with col_n1:
                    p_nav = st.number_input(f"Página (1-{total_p})", 1, total_p, key="p_nav", value=st.session_state.pagina_atual)
                    st.session_state.pagina_atual = p_nav
                start, end = (st.session_state.pagina_atual - 1) * itens, (st.session_state.pagina_atual - 1) * itens + itens
                for idx, row in df_v.iloc[start:end].iterrows():
                    with st.expander(f"{row['Dt_Obj'].strftime('%d/%m %H:%M')} | {row[c_desc][:60]}... | {format_br(row['V_F'])}"):
                        m_idx = st.session_state.lista_metodos.index(row['Metodo']) if row['Metodo'] in st.session_state.lista_metodos else 0
                        novo = st.selectbox("Método:", st.session_state.lista_metodos, index=m_idx, key=f"log_{row['ID_Ref']}_{idx}")
                        if novo != row['Metodo']: st.session_state.metodos_salvos[row['ID_Ref']] = novo; st.rerun()

        elif menu == "📊 Evolução Patrimonial" and st.session_state.is_premium:
            st.subheader("📊 Evolução Patrimonial Dinâmica")
            p_evol = st.date_input("Período do Gráfico", [df_clean['Data_Apenas'].min(), df_clean['Data_Apenas'].max()])
            if len(p_evol) == 2:
                df_ev = df_clean[(df_clean['Data_Apenas'] >= p_evol[0]) & (df_clean['Data_Apenas'] <= p_evol[1])].copy()
                df_ev = df_ev.groupby('Data_Apenas')['V_F'].sum().reset_index()
                df_ev['Acum'] = df_ev['V_F'].cumsum()
                fig = go.Figure()
                y, x = df_ev['Acum'].tolist(), df_ev['Data_Apenas'].tolist()
                fig.add_hline(y=0, line_dash="dash", line_color="#475569", opacity=0.5)
                for i in range(len(y)-1):
                    cor = '#10b981' if y[i+1] >= 0 else '#f43f5e'
                    fig.add_trace(go.Scatter(x=x[i:i+2], y=y[i:i+2], mode='lines', line=dict(color=cor, width=3.5, shape='spline', smoothing=1.3), fill='tozeroy', fillcolor=f'rgba({16 if cor=="#10b981" else 244}, {185 if cor=="#10b981" else 63}, {129 if cor=="#10b981" else 94}, 0.08)', hoverinfo='skip', showlegend=False))
                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=500, xaxis=dict(color='#475569', showgrid=False), yaxis=dict(color='#475569', gridcolor='rgba(255,255,255,0.05)'))
                st.plotly_chart(fig, use_container_width=True)

        elif menu == "⏰ Análise de Janelas" and st.session_state.is_premium:
            st.subheader("⏰ Análise de Janelas Profunda")
            p_jan = st.date_input("Período das Janelas", [df_clean['Data_Apenas'].min(), df_clean['Data_Apenas'].max()])
            if len(p_jan) == 2:
                df_j = df_clean[(df_clean['Data_Apenas'] >= p_jan[0]) & (df_clean['Data_Apenas'] <= p_jan[1])]
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown('<div class="section-title">Dias da Semana</div>', unsafe_allow_html=True)
                    d_s = {0:'Segunda', 1:'Terça', 2:'Quarta', 3:'Quinta', 4:'Sexta', 5:'Sábado', 6:'Domingo'}
                    res_d = df_j.groupby('Dia_Num').agg({'V_F':['sum','count']}).reset_index()
                    res_d.columns = ['Dia','Lucro','Qtd']
                    for _, row in res_d.iterrows():
                        wr_d = (len(df_j[(df_j['Dia_Num']==row['Dia']) & (df_j['V_F']>0.05)]) / row['Qtd'] * 100) if row['Qtd']>0 else 0
                        st.markdown(f'<div class="perf-card"><div><b>{d_s[row["Dia"]]}</b><br><small style="color:#64748b">{int(row["Qtd"])} entr. | WR: {wr_d:.1f}%</small></div><div style="text-align:right;"><span class="{"val-pos" if row["Lucro"]>=0 else "val-neg"}">{format_br(row["Lucro"])}</span></div></div>', unsafe_allow_html=True)
                with c2:
                    st.markdown('<div class="section-title">Faixas Horárias</div>', unsafe_allow_html=True)
                    df_j['FH'] = pd.cut(df_j['Hora'], bins=[0,6,12,18,24], labels=['Madrugada (00h-06h)','Manhã (06h-12h)','Tarde (12h-18h)','Noite (18h-00h)'], include_lowest=True)
                    res_h = df_j.groupby('FH', observed=False).agg({'V_F':['sum','count']}).reset_index()
                    res_h.columns = ['Faixa','Lucro','Qtd']
                    for _, row in res_h.iterrows():
                        wr_h = (len(df_j[(df_j['FH']==row['Faixa']) & (df_j['V_F']>0.05)]) / row['Qtd'] * 100) if row['Qtd']>0 else 0
                        st.markdown(f'<div class="perf-card"><div><b>{row["Faixa"]}</b><br><small style="color:#64748b">{int(row["Qtd"])} entr. | WR: {wr_h:.1f}%</small></div><div style="text-align:right;"><span class="{"val-pos" if row["Lucro"]>=0 else "val-neg"}">{format_br(row["Lucro"])}</span></div></div>', unsafe_allow_html=True)

        elif menu == "🔥 Sequências" and st.session_state.is_premium:
            st.markdown("<h2 style='color: white;'>🔥 Análise de Sequências</h2>", unsafe_allow_html=True)
            p_seq = st.date_input("Período", [df_clean['Data_Apenas'].min(), df_clean['Data_Apenas'].max()])
            if len(p_seq) == 2:
                df_s = df_clean[(df_clean['Data_Apenas'] >= p_seq[0]) & (df_clean['Data_Apenas'] <= p_seq[1])].copy()
                # Lógica Inclusiva
                str_g = {i: 0 for i in range(2, 12)}; temp_g = 0
                str_r = {i: 0 for i in range(2, 12)}; temp_r = 0
                for v in df_s['V_F'].tolist():
                    if v > 0.05:
                        temp_g += 1; temp_r = 0
                        for i in range(2, min(temp_g + 1, 12)): str_g[i] += 1
                    elif v < -0.05:
                        temp_r += 1; temp_g = 0
                        for i in range(2, min(temp_r + 1, 12)): str_r[i] += 1
                    else: temp_g = 0; temp_r = 0
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown('<div class="section-title">Sequências de Greens</div>', unsafe_allow_html=True)
                    for i in range(2, 12): st.markdown(f'<div class="perf-card"><div><b>{i} Greens Seguidos</b></div><div style="text-align:right;"><span class="val-pos">{str_g[i]} vezes</span></div></div>', unsafe_allow_html=True)
                with c2:
                    st.markdown('<div class="section-title">Sequências de Reds</div>', unsafe_allow_html=True)
                    for i in range(2, 12): st.markdown(f'<div class="perf-card"><div><b>{i} Reds Seguidos</b></div><div style="text-align:right;"><span class="val-neg">{str_r[i]} vezes</span></div></div>', unsafe_allow_html=True)

        elif menu == "⚙️ Gestão de Métodos" and st.session_state.is_premium:
            st.subheader("⚙️ Gestão de Métodos Personalizados")
            novo_m = st.text_input("Adicionar novo método:")
            if st.button("Adicionar"):
                if novo_m and novo_m not in st.session_state.lista_metodos: st.session_state.lista_metodos.append(novo_m); st.success("Adicionado!")
            st.write("Métodos atuais:", ", ".join(st.session_state.lista_metodos))
            st.download_button("BAIXAR MEU BACKUP (.JSON)", json.dumps(st.session_state.metodos_salvos), file_name="backup_bet.json")

    except Exception as e: st.error(f"Erro Crítico: {e}")
else: st.info("Suba seu extrato Betfair na lateral para começar.")

if menu == "📖 Como Extrair":
    st.markdown("<h1 style='color: white; text-align: center;'>📖 Guia de Extração</h1><br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="step-box"><h3>1️⃣ Acesse sua Conta</h3><p>Vá em: <b>Minha Conta</b> > <b>Minha Atividade</b> > <b>Histórico de Transações</b>.</p></div>', unsafe_allow_html=True)
        st.markdown('<div class="step-box"><h3>2️⃣ Filtre o Período</h3><p>Escolha as datas desejadas no site da Betfair.</p></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="step-box"><h3>3️⃣ Baixe o CSV</h3><p>Clique no botão <b>Download como CSV</b> no fim da página.</p></div>', unsafe_allow_html=True)
        st.markdown('<div class="step-box"><h3>4️⃣ Faça o Upload</h3><p>Use o campo de upload no menu à esquerda deste site.</p></div>', unsafe_allow_html=True)
