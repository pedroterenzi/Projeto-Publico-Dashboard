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

# --- ESTILIZAÇÃO CSS PREMIUM (MANTIDA INTEGRALMENTE) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #020617; }
    .main .block-container { max-width: 1200px; padding-top: 1.5rem; margin: auto; }

    /* NAVEGAÇÃO POR BOTÕES LARGOS */
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
    .metric-title { font-size: 0.7rem; text-transform: uppercase; opacity: 0.6; letter-spacing: 1.2px; margin-bottom: 5px; }
    .metric-value { font-size: 1.6rem; margin: 0; letter-spacing: -1px; }

    .monthly-profit-card {
        padding: 15px; border-radius: 15px; text-align: center; color: white; font-weight: 800;
        margin-bottom: 20px; border: 1px solid rgba(255, 255, 255, 0.1);
    }

    .calendar-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 10px; margin-top: 15px; }
    .day-name { text-align: center; color: #475569; font-weight: 800; font-size: 0.7rem; text-transform: uppercase; }
    .day-card { 
        background: #0f172a; border-radius: 12px; padding: 12px; min-height: 95px; 
        display: flex; flex-direction: column; justify-content: space-between;
        border: 1px solid rgba(255, 255, 255, 0.03); 
    }
    .green-card { background: linear-gradient(135deg, #059669 0%, #064e3b 100%); border: none; }
    .red-card { background: linear-gradient(135deg, #dc2626 0%, #7f1d1d 100%); border: none; }
    .day-number { font-size: 0.8rem; font-weight: 800; color: #64748b; }
    .day-value { font-size: 0.85rem; font-weight: 800; color: white; }
    .day-stakes { font-size: 0.65rem; font-weight: 600; color: rgba(255,255,255,0.8); }

    .perf-card { 
        background: #0f172a; border-radius: 12px; padding: 15px 20px; 
        display: flex; align-items: center; justify-content: space-between; 
        border: 1px solid rgba(255, 255, 255, 0.05); margin-bottom: 8px;
    }
    .val-pos { color: #10b981; font-weight: 800; }
    .val-neg { color: #f43f5e; font-weight: 800; }

    .step-box {
        background: #1e293b; padding: 20px; border-radius: 15px; margin-bottom: 10px;
        border-left: 5px solid #10b981;
    }
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

# --- INICIALIZAÇÃO DE ESTADO (PARA NÃO PERDER DADOS) ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'metodos_salvos' not in st.session_state: st.session_state.metodos_salvos = {}
if 'lista_metodos' not in st.session_state: 
    st.session_state.lista_metodos = ["Match Odds", "Under 2.5", "Over 2.5", "Under 1.5", "Over 1.5", "Correct Score", "Sem Categoria"]

# --- SISTEMA DE LOGIN (SECRETS) ---
def check_login():
    try:
        users = st.secrets["users"]
        if user_input in users and users[user_input] == pass_input:
            st.session_state.auth = True
            st.rerun()
        else: st.error("Usuário ou senha incorretos.")
    except: st.error("Erro técnico: Configure os usuários nos Secrets do Streamlit.")

if not st.session_state.auth:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("<div style='text-align: center; margin-top: 100px;'><h1 style='color: #10b981;'>💎 BET ANALYTICS PRO</h1><p style='color: #64748b;'>Acesse sua conta</p></div>", unsafe_allow_html=True)
        user_input = st.text_input("E-mail")
        pass_input = st.text_input("Senha", type="password")
        if st.button("ACESSAR", use_container_width=True): check_login()
    st.stop()

# --- BARRA LATERAL ---
with st.sidebar:
    st.markdown("<h2 style='color: #10b981; margin-bottom: 0;'>💎 BET PRO</h2>", unsafe_allow_html=True)
    if st.button("Sair"):
        st.session_state.auth = False
        st.rerun()
    st.markdown("---")
    uploaded_file = st.file_uploader("Suba seu extrato Betfair (.csv)", type=["csv"])
    
    # Inclusão do Campo de Backup de Métodos
    uploaded_backup = st.file_uploader("Opcional: Suba seu Backup (.json)", type=["json"])
    if uploaded_backup:
        st.session_state.metodos_salvos = json.load(uploaded_backup)
        st.success("Backup Aplicado!")

    stake_padrao = st.number_input("Sua Stake Padrão (R$)", value=600.0)
    st.markdown("---")
    # Menu Atualizado com as Novas Abas solicitadas
    menu = st.radio("Menu", ["📈 Performance Geral", "📅 Diário de Operações", "📋 Log de Entradas", "📊 Evolução Patrimonial", "⏰ Análise de Janelas", "⚙️ Gestão de Métodos", "📖 Como Extrair Arquivo"], label_visibility="collapsed")

# --- LÓGICA DE NORMALIZAÇÃO ---
df_clean = None
total_l = 0

if uploaded_file is not None:
    try:
        df_raw = pd.read_csv(uploaded_file)
        mapa_colunas = {
            'Data': ['Data', 'Date', 'data', 'date'],
            'Descricao': ['Descrição', 'Description', 'descrição', 'description', 'Evento', 'Market'],
            'Valor': ['Valor (R$)', 'Amount', 'valor', 'amount', 'Profit/Loss', 'P&L'],
            'Entrada': ['Entrada de Dinheiro (R$)', 'In'],
            'Saida': ['Saída de Dinheiro (R$)', 'Out']
        }
        def find_col(possible_names):
            for col in df_raw.columns:
                if col in possible_names: return col
            return None

        col_data, col_desc, col_valor, col_entrada, col_saida = find_col(mapa_colunas['Data']), find_col(mapa_colunas['Descricao']), find_col(mapa_colunas['Valor']), find_col(mapa_colunas['Entrada']), find_col(mapa_colunas['Saida'])

        if not col_data or not col_desc:
            st.error("❌ Formato de arquivo não reconhecido.")
            st.stop()

        if col_valor: df_raw['Valor_Final'] = df_raw[col_valor].apply(clean_money)
        elif col_entrada and col_saida: df_raw['Valor_Final'] = df_raw[col_entrada].apply(clean_money) + df_raw[col_saida].apply(clean_money)

        df_proc = df_raw.copy()
        df_proc = df_proc.rename(columns={col_data: 'Data_Ref', col_desc: 'Evento_Ref'})
        meses_pt = {'jan': 'Jan', 'fev': 'Feb', 'mar': 'Mar', 'abr': 'Apr', 'mai': 'May', 'jun': 'Jun', 'jul': 'Jul', 'ago': 'Aug', 'set': 'Sep', 'out': 'Oct', 'nov': 'Nov', 'dez': 'Dec'}
        for pt, en in meses_pt.items(): df_proc['Data_Ref'] = df_proc['Data_Ref'].astype(str).str.replace(pt, en, case=False)

        df_proc['Data_Dt'] = pd.to_datetime(df_proc['Data_Ref'], errors='coerce')
        df_proc = df_proc.dropna(subset=['Data_Dt'])
        df_proc = df_proc[~df_proc['Evento_Ref'].str.contains('Depósito|Deposit|Withdraw|Saque|Transferência', case=False, na=False)].copy()
        df_proc['Data_Apenas'] = df_proc['Data_Dt'].dt.date
        df_proc['Hora'] = df_proc['Data_Dt'].dt.hour
        df_proc['Dia_Semana_Num'] = df_proc['Data_Dt'].dt.dayofweek
        df_proc = df_proc.sort_values('Data_Dt')

        df_proc['ID_Ref'] = df_proc['Evento_Ref'].apply(lambda x: re.search(r'Ref: (\d+)', str(x)).group(1) if re.search(r'Ref: (\d+)', str(x)) else str(x))
        df_clean = df_proc.groupby(['ID_Ref', 'Data_Dt', 'Evento_Ref', 'Hora', 'Dia_Semana_Num']).agg({'Valor_Final': 'sum'}).reset_index()
        
        # --- INTEGRAÇÃO DA LÓGICA DE MÉTODOS SALVOS ---
        def get_metodo(row):
            if row['ID_Ref'] in st.session_state.metodos_salvos: return st.session_state.metodos_salvos[row['ID_Ref']]
            return str(row['Evento_Ref']).split('Ref:')[0].split('/')[-1].strip() if '/' in str(row['Evento_Ref']) else "Match Odds"
        
        df_clean['Metodo'] = df_clean.apply(get_metodo, axis=1)
        df_clean['Data_Apenas'] = df_clean['Data_Dt'].dt.date

        # Filtro de Período
        if menu == "📅 Diário de Operações":
            st.sidebar.markdown("---")
            ano_cal = st.sidebar.selectbox("Ano", sorted(df_clean['Data_Dt'].dt.year.unique(), reverse=True))
            meses_nomes = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
            mes_nome_cal = st.sidebar.selectbox("Mês", meses_nomes, index=datetime.now().month - 1)
            mes_num_cal = meses_nomes.index(mes_nome_cal) + 1
            df_final = df_clean[(df_clean['Data_Dt'].dt.year == ano_cal) & (df_clean['Data_Dt'].dt.month == mes_num_cal)].copy()
        else:
            st.sidebar.markdown("---")
            p_input = st.sidebar.date_input("Filtrar Período", [df_clean['Data_Apenas'].min(), df_clean['Data_Apenas'].max()])
            df_final = df_clean[(df_clean['Data_Apenas'] >= p_input[0]) & (df_clean['Data_Apenas'] <= p_input[1])].copy() if len(p_input) == 2 else pd.DataFrame()

        if not df_final.empty:
            total_l = df_final['Valor_Final'].sum()
            df_final['Odd'] = df_final['Valor_Final'].apply(lambda x: (x / stake_padrao) + 1 if x > 0 else 0)
            avg_odds = df_final[df_final['Odd'] > 0].groupby('Metodo')['Odd'].mean().to_dict()
            df_final.loc[df_final['Odd'] == 0, 'Odd'] = df_final['Metodo'].map(avg_odds).fillna(1.50)
            odd_m = df_final[df_final['Valor_Final'] > 0]['Odd'].mean() if not df_final[df_final['Valor_Final'] > 0].empty else 0

            # --- RENDERIZAÇÃO DAS ABAS ---
            if menu == "📈 Performance Geral":
                st.markdown("<h2 style='color: white;'>Executive Summary</h2>", unsafe_allow_html=True)
                bg_l = "linear-gradient(135deg, #10b981 0%, #064e3b 100%)" if total_l >= 0 else "linear-gradient(135deg, #ef4444 0%, #7f1d1d 100%)"
                c1, c2, c3, c4 = st.columns(4)
                with c1: st.markdown(f'<div class="metric-card" style="background: {bg_l};"><div class="metric-title">Lucro Líquido</div><div class="metric-value">{format_br(total_l)}</div></div>', unsafe_allow_html=True)
                with c2: st.markdown(f'<div class="metric-card"><div class="metric-title">Odd Média</div><div class="metric-value">{odd_m:.2f}</div></div>', unsafe_allow_html=True)
                with c3: st.markdown(f'<div class="metric-card"><div class="metric-title">Saldo Stakes</div><div class="metric-value">{total_l/stake_padrao:,.2f}</div></div>', unsafe_allow_html=True)
                with c4: st.markdown(f'<div class="metric-card"><div class="metric-title">Entradas</div><div class="metric-value">{len(df_final)}</div></div>', unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("🎯 Estratégias")
                    res = df_final.groupby('Metodo').agg({'Valor_Final': 'sum', 'ID_Ref': 'count'}).rename(columns={'ID_Ref': 'Qtd', 'Valor_Final': 'Lucro'}).sort_values('Lucro', ascending=False)
                    for est, row in res.iterrows():
                        st.markdown(f'<div class="perf-card"><div><b>{est}</b><br><small>{int(row["Qtd"])} entr.</small></div><div style="text-align:right;"><span class="{"val-pos" if row["Lucro"]>=0 else "val-neg"}">{format_br(row["Lucro"])}</span><br><small>{(row["Lucro"]/(row["Qtd"]*stake_padrao))*100:.1f}% ROI</small></div></div>', unsafe_allow_html=True)
                with col2:
                    st.subheader("📊 Ranges de Odd")
                    df_final['Range'] = pd.cut(df_final['Odd'], bins=[0,1.3,1.59,1.79,2.09,3.0,1000], labels=['1.00-1.30','1.31-1.59','1.60-1.79','1.80-2.09','2.10-3.00','3.00+'])
                    res_odd = df_final.groupby('Range', observed=False).agg({'Valor_Final': 'sum', 'ID_Ref': 'count'}).rename(columns={'ID_Ref': 'Qtd', 'Valor_Final': 'Lucro'})
                    for r, row in res_odd.iterrows():
                        st.markdown(f'<div class="perf-card"><div><b>Odd: {r}</b></div><div style="text-align:right;"><span class="{"val-pos" if row["Lucro"]>=0 else "val-neg"}">{format_br(row["Lucro"])}</span></div></div>', unsafe_allow_html=True)

            elif menu == "📅 Diário de Operações":
                st.subheader(f"Diário: {mes_nome_cal} {ano_cal}")
                bg_m = "rgba(16, 185, 129, 0.2)" if total_l >= 0 else "rgba(244, 63, 94, 0.2)"
                st.markdown(f'<div class="monthly-profit-card" style="background: {bg_m}; border: 1px solid {"#10b981" if total_l >= 0 else "#f43f5e"};"><small>LUCRO {mes_nome_cal.upper()}</small><br><span style="font-size: 1.8rem;">{format_br(total_l)}</span></div>', unsafe_allow_html=True)
                cal_obj, dias = calendar.Calendar(firstweekday=0), list(calendar.Calendar(firstweekday=0).itermonthdays(ano_cal, mes_num_cal))
                l_dia = df_final.groupby(df_final['Data_Dt'].dt.day)['Valor_Final'].sum()
                html = '<div class="calendar-grid">'
                for n in ['SEG','TER','QUA','QUI','SEX','SAB','DOM']: html += f'<div class="day-name">{n}</div>'
                for d in dias:
                    if d == 0: html += '<div style="opacity:0"></div>'
                    else:
                        v = l_dia.get(d, 0)
                        cl = "day-card green-card" if v > 0.05 else "day-card red-card" if v < -0.05 else "day-card"
                        html += f'<div class="{cl}"><span class="day-number">{d}</span><span class="day-value">{format_br(v) if abs(v)>0.05 else ""}</span><span class="day-stakes">{(v/stake_padrao):,.1f} STK</span></div>'
                st.markdown(html + '</div>', unsafe_allow_html=True)

            elif menu == "📋 Log de Entradas":
                st.subheader("📋 Classificar Métodos por Entrada")
                search = st.text_input("Filtrar por nome do jogo/mercado")
                df_view = df_clean[df_clean['Evento_Ref'].str.contains(search, case=False)] if search else df_clean
                df_view = df_view.sort_values('Data_Dt', ascending=False)
                
                itens_por_pagina = 20
                total_entradas = len(df_view)
                total_paginas = (total_entradas // itens_por_pagina) + (1 if total_entradas % itens_por_pagina > 0 else 0)
                if 'pagina_atual' not in st.session_state: st.session_state.pagina_atual = 1
                
                col_pag1, col_pag2, col_pag3 = st.columns([1, 2, 1])
                with col_pag2:
                    pag = st.number_input(f"Página (1 de {total_paginas})", min_value=1, max_value=total_paginas, value=st.session_state.pagina_atual)
                    st.session_state.pagina_atual = pag
                
                start_idx, end_idx = (st.session_state.pagina_atual - 1) * itens_por_pagina, (st.session_state.pagina_atual - 1) * itens_por_pagina + itens_por_pagina
                for idx, row in df_view.iloc[start_idx:end_idx].iterrows():
                    chave_sel = f"sel_{row['ID_Ref']}_{row['Data_Dt'].timestamp()}"
                    with st.expander(f"{row['Data_Dt'].strftime('%d/%m %H:%M')} | {row['Evento_Ref'][:50]}... | {format_br(row['Valor_Final'])}"):
                        cur_idx = st.session_state.lista_metodos.index(row['Metodo']) if row['Metodo'] in st.session_state.lista_metodos else 0
                        novo = st.selectbox("Classificar como:", st.session_state.lista_metodos, index=cur_idx, key=chave_sel)
                        if novo != row['Metodo']:
                            st.session_state.metodos_salvos[row['ID_Ref']] = novo
                            st.rerun()

            elif menu == "📊 Evolução Patrimonial":
                df_ev = df_final.groupby('Data_Apenas')['Valor_Final'].sum().reset_index()
                df_ev['Acum'] = df_ev['Valor_Final'].cumsum()
                y, x = df_ev['Acum'].tolist(), df_ev['Data_Apenas'].tolist()
                fig = go.Figure()
                for i in range(len(y)-1):
                    fig.add_trace(go.Scatter(x=x[i:i+2], y=y[i:i+2], mode='lines', line=dict(color='#10b981' if y[i+1]>=0 else '#f43f5e', width=3, shape='spline', smoothing=1.3), hoverinfo='skip'))
                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=500, margin=dict(l=0,r=0,t=0,b=0), xaxis=dict(showgrid=False, color='#475569'), yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.03)', color='#475569'))
                st.plotly_chart(fig, use_container_width=True)

            elif menu == "⏰ Análise de Janelas":
                c1, c2 = st.columns(2)
                with c1:
                    st.subheader("📅 Dias")
                    d_s = {0: 'Segunda', 1: 'Terça', 2: 'Quarta', 3: 'Quinta', 4: 'Sexta', 5: 'Sábado', 6: 'Domingo'}
                    res_d = df_final.groupby('Dia_Semana_Num').agg({'Valor_Final': 'sum'}).sort_index()
                    for idx, val in res_d.iterrows():
                        st.markdown(f'<div class="perf-card"><div><b>{d_s[idx]}</b></div><div style="text-align:right;"><span class="{"val-pos" if val["Valor_Final"]>=0 else "val-neg"}">{format_br(val["Valor_Final"])}</span></div></div>', unsafe_allow_html=True)
                with c2:
                    st.subheader("⌚ Horários")
                    df_final['FH'] = pd.cut(df_final['Hora'], bins=[0,6,12,18,24], labels=['Madrugada','Manhã','Tarde','Noite'], include_lowest=True)
                    res_h = df_final.groupby('FH', observed=False).agg({'Valor_Final': 'sum'})
                    for f, val in res_h.iterrows():
                        st.markdown(f'<div class="perf-card"><div><b>{f}</b></div><div style="text-align:right;"><span class="{"val-pos" if val["Valor_Final"]>=0 else "val-neg"}">{format_br(val["Valor_Final"])}</span></div></div>', unsafe_allow_html=True)

            elif menu == "⚙️ Gestão de Métodos":
                st.subheader("⚙️ Seus Métodos Personalizados")
                novo_m = st.text_input("Adicionar novo método:")
                if st.button("Adicionar"):
                    if novo_m and novo_m not in st.session_state.lista_metodos:
                        st.session_state.lista_metodos.append(novo_m); st.success(f"{novo_m} adicionado!")
                st.write("Métodos atuais:", ", ".join(st.session_state.lista_metodos))
                st.markdown("---")
                st.download_button("BAIXAR MEU BACKUP (.JSON)", json.dumps(st.session_state.metodos_salvos), file_name="backup_bet.json")

    except Exception as e: st.error(f"❌ Erro crítico no processamento.")

elif menu == "📖 Como Extrair Arquivo":
    st.markdown("<h1 style='color: white; text-align: center;'>📖 Guia de Extração</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="step-box"><h3>1️⃣ Acesse sua Conta</h3><p>Vá em: <b>Minha Conta</b> > <b>Minha Atividade</b> > <b>Histórico de Transações</b>.</p></div>', unsafe_allow_html=True)
        st.markdown('<div class="step-box"><h3>2️⃣ Filtre o Período</h3><p>Escolha as datas e clique em <b>Visualizar</b>.</p></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="step-box"><h3>3️⃣ Baixe o CSV</h3><p>Clique no botão <b>Download como CSV</b> no fim da página.</p></div>', unsafe_allow_html=True)
        st.markdown('<div class="step-box"><h3>4️⃣ Faça o Upload</h3><p>Clique em <b>Browse files</b> no menu à esquerda.</p></div>', unsafe_allow_html=True)
