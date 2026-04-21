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

# --- ESTILIZAÇÃO CSS PREMIUM ---
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

    /* CARDS E VISUAIS */
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

# --- INICIALIZAÇÃO DE ESTADO (PERSISTÊNCIA) ---
if 'metodos_salvos' not in st.session_state:
    st.session_state.metodos_salvos = {} # {id_referencia: nome_do_metodo}
if 'lista_metodos' not in st.session_state:
    st.session_state.lista_metodos = ["Match Odds", "Under 2.5", "Over 2.5", "Under 1.5", "Over 1.5", "Correct Score", "Sem Categoria"]

# --- LOGIN (SECRETS) ---
if 'auth' not in st.session_state:
    st.session_state.auth = False

def check_login():
    try:
        users = st.secrets["users"]
        if user_input in users and users[user_input] == pass_input:
            st.session_state.auth = True
            st.rerun()
        else: st.error("Acesso Negado.")
    except: st.error("Erro: Secrets não configurado.")

if not st.session_state.auth:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("<div style='text-align: center; margin-top: 100px;'><h1 style='color: #10b981;'>💎 BET ANALYTICS PRO</h1></div>", unsafe_allow_html=True)
        user_input = st.text_input("E-mail")
        pass_input = st.text_input("Senha", type="password")
        if st.button("ACESSAR DASHBOARD", use_container_width=True): check_login()
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h2 style='color: #10b981; margin-bottom: 0;'>💎 BET PRO</h2>", unsafe_allow_html=True)
    if st.button("Sair"):
        st.session_state.auth = False
        st.rerun()
    st.markdown("---")
    
    uploaded_file = st.file_uploader("1. Suba o Extrato Betfair (.csv)", type=["csv"])
    
    st.markdown("---")
    st.subheader("💾 Backup de Métodos")
    uploaded_backup = st.file_uploader("2. Opcional: Suba seu Backup (.json)", type=["json"])
    if uploaded_backup:
        try:
            st.session_state.metodos_salvos = json.load(uploaded_backup)
            st.success("Backup carregado!")
        except: st.error("Backup inválido.")

    stake_padrao = st.number_input("Sua Stake Padrão (R$)", value=600.0)
    st.markdown("---")
    menu = st.radio("Menu", ["📈 Performance Geral", "📅 Diário de Operações", "📋 Log de Entradas", "⏰ Análise de Janelas", "⚙️ Gestão de Métodos", "📖 Como Extrair"], label_visibility="collapsed")

# --- PROCESSAMENTO ---
if uploaded_file is not None:
    try:
        df_raw = pd.read_csv(uploaded_file)
        
        # Mapeamento inteligente de colunas (Suporta Mobile e Desktop)
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

        # Tradução de datas
        meses_pt = {'jan': 'Jan', 'fev': 'Feb', 'mar': 'Mar', 'abr': 'Apr', 'mai': 'May', 'jun': 'Jun', 'jul': 'Jul', 'ago': 'Aug', 'set': 'Sep', 'out': 'Oct', 'nov': 'Nov', 'dez': 'Dec'}
        df_raw[c_data] = df_raw[c_data].astype(str)
        for pt, en in meses_pt.items(): df_raw[c_data] = df_raw[c_data].str.replace(pt, en, case=False)
        
        df_raw['Dt_Obj'] = pd.to_datetime(df_raw[c_data], errors='coerce')
        df_raw = df_raw.dropna(subset=['Dt_Obj'])
        df_raw = df_raw[~df_raw[c_desc].str.contains('Depósito|Deposit|Withdraw|Saque|Transferência', case=False, na=False)].copy()
        
        # ID de Referência para linkar com os Métodos Salvos
        df_raw['ID_Ref'] = df_raw[c_desc].apply(lambda x: re.search(r'Ref: (\d+)', str(x)).group(1) if re.search(r'Ref: (\d+)', str(x)) else str(x))
        
        # Agrupamento Consolidado
        df_clean = df_raw.groupby(['ID_Ref', 'Dt_Obj', c_desc]).agg({'Valor_Final': 'sum'}).reset_index()
        df_clean['Data_Apenas'] = df_clean['Dt_Obj'].dt.date
        df_clean['Hora'] = df_clean['Dt_Obj'].dt.hour
        df_clean['Dia_Num'] = df_clean['Dt_Obj'].dt.dayofweek

        # Atribuição de Método (Manual vs Automática)
        def get_metodo(row):
            if row['ID_Ref'] in st.session_state.metodos_salvos:
                return st.session_state.metodos_salvos[row['ID_Ref']]
            # Fallback: Extrai do nome do mercado se não houver classificação manual
            return str(row[c_desc]).split('Ref:')[0].split('/')[-1].strip() if '/' in str(row[c_desc]) else "Sem Categoria"
        
        df_clean['Metodo'] = df_clean.apply(get_metodo, axis=1)

        # --- ABAS DE RENDERIZAÇÃO ---
        
        if menu == "📈 Performance Geral":
            total_l = df_clean['Valor_Final'].sum()
            bg = "linear-gradient(135deg, #10b981 0%, #064e3b 100%)" if total_l >= 0 else "linear-gradient(135deg, #ef4444 0%, #7f1d1d 100%)"
            st.markdown(f'<div class="metric-card" style="background: {bg};"><div>LUCRO LÍQUIDO</div><div style="font-size: 2.5rem;">{format_br(total_l)}</div></div>', unsafe_allow_html=True)
            
            st.subheader("🎯 Performance por Método")
            res = df_clean.groupby('Metodo').agg({'Valor_Final': 'sum', 'ID_Ref': 'count'}).rename(columns={'Valor_Final': 'Lucro', 'ID_Ref': 'Qtd'}).sort_values('Lucro', ascending=False)
            for m, row in res.iterrows():
                cor = "val-pos" if row['Lucro'] >= 0 else "val-neg"
                st.markdown(f'<div class="perf-card"><div><b>{m}</b><br><small>{int(row["Qtd"])} entradas</small></div><div style="text-align:right;"><span class="{cor}">{format_br(row["Lucro"])}</span></div></div>', unsafe_allow_html=True)

        elif menu == "📋 Log de Entradas":
            st.subheader("📋 Classificar Métodos por Entrada")
            st.info("Exibindo 20 entradas por página para maior velocidade.")
            
            # 1. FILTRO DE BUSCA
            search = st.text_input("Filtrar por nome do jogo/mercado")
            df_view = df_clean[df_clean[c_desc].str.contains(search, case=False)] if search else df_clean
            df_view = df_view.sort_values('Dt_Obj', ascending=False)

            # 2. LÓGICA DE PAGINAÇÃO
            itens_por_pagina = 20
            total_entradas = len(df_view)
            total_paginas = (total_entradas // itens_por_pagina) + (1 if total_entradas % itens_por_pagina > 0 else 0)
            
            col_pag1, col_pag2, col_pag3 = st.columns([1, 2, 1])
            if 'pagina_atual' not in st.session_state:
                st.session_state.pagina_atual = 1

            with col_pag2:
                # Seletor de página simples
                pag = st.number_input(f"Página (1 de {total_paginas})", min_value=1, max_value=total_paginas, value=st.session_state.pagina_atual)
                st.session_state.pagina_atual = pag

            # Cálculo do índice de início e fim
            start_idx = (st.session_state.pagina_atual - 1) * itens_por_pagina
            end_idx = start_idx + itens_por_pagina

            # 3. EXIBIÇÃO APENAS DOS ITENS DA PÁGINA
            st.write(f"Mostrando entradas {start_idx + 1} a {min(end_idx, total_entradas)} de {total_entradas}")
            
            for idx, row in df_view.iloc[start_idx:end_idx].iterrows():
                # Usamos o ID_Ref e a Data para garantir uma chave única para o componente
                chave_seletor = f"sel_{row['ID_Ref']}_{row['Dt_Obj'].timestamp()}"
                
                with st.expander(f"{row['Dt_Obj'].strftime('%d/%m %H:%M')} | {row[c_desc][:50]}... | {format_br(row['Valor_Final'])}"):
                    current_idx = st.session_state.lista_metodos.index(row['Metodo']) if row['Metodo'] in st.session_state.lista_metodos else 0
                    
                    novo = st.selectbox(
                        "Classificar como:", 
                        st.session_state.lista_metodos, 
                        index=current_idx, 
                        key=chave_seletor
                    )
                    
                    if novo != row['Metodo']:
                        st.session_state.metodos_salvos[row['ID_Ref']] = novo
                        st.rerun()

            # Botões de navegação no rodapé
            c_prev, c_next = st.columns(2)
            with c_prev:
                if st.button("⬅️ Anterior") and st.session_state.pagina_atual > 1:
                    st.session_state.pagina_atual -= 1
                    st.rerun()
            with c_next:
                if st.button("Próximo ➡️") and st.session_state.pagina_atual < total_paginas:
                    st.session_state.pagina_atual += 1
                    st.rerun()
        elif menu == "⚙️ Gestão de Métodos":
            st.subheader("⚙️ Seus Métodos Personalizados")
            col_a, col_b = st.columns(2)
            with col_a:
                novo_m = st.text_input("Nome do novo método:")
                if st.button("Adicionar Método"):
                    if novo_m and novo_m not in st.session_state.lista_metodos:
                        st.session_state.lista_metodos.append(novo_m)
                        st.success(f"{novo_m} adicionado!")
            with col_b:
                st.write("Métodos Atuais:")
                st.write(", ".join(st.session_state.lista_metodos))

            st.markdown("---")
            st.subheader("💾 Salvar meu Progresso")
            st.write("Baixe este arquivo para manter suas classificações na próxima vez que usar o site.")
            backup_data = json.dumps(st.session_state.metodos_salvos)
            st.download_button("BAIXAR MEU BACKUP (.JSON)", backup_data, file_name=f"backup_analytics_{datetime.now().strftime('%d_%m')}.json")

        elif menu == "📅 Diário de Operações":
            # [Lógica original do calendário que você gosta]
            ano_c = st.sidebar.selectbox("Ano", sorted(df_clean['Dt_Obj'].dt.year.unique(), reverse=True))
            meses_n = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
            mes_n = st.sidebar.selectbox("Mês", meses_n, index=datetime.now().month - 1)
            mes_num = meses_n.index(mes_n) + 1
            
            df_mes = df_clean[(df_clean['Dt_Obj'].dt.year == ano_c) & (df_clean['Dt_Obj'].dt.month == mes_num)]
            l_mes = df_mes['Valor_Final'].sum()
            
            st.markdown(f'<div class="monthly-profit-card" style="border: 2px solid {"#10b981" if l_mes>=0 else "#f43f5e"};"><small>LUCRO {mes_n.upper()}</small><br><span style="font-size: 2rem;">{format_br(l_mes)}</span></div>', unsafe_allow_html=True)
            
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

        elif menu == "📊 Evolução Patrimonial":
            df_ev = df_clean.groupby('Data_Apenas')['Valor_Final'].sum().reset_index()
            df_ev['Acumulado'] = df_ev['Valor_Final'].cumsum()
            fig = go.Figure()
            y, x = df_ev['Acumulado'].tolist(), df_ev['Data_Apenas'].tolist()
            for i in range(len(y)-1):
                fig.add_trace(go.Scatter(x=x[i:i+2], y=y[i:i+2], mode='lines', line=dict(color='#10b981' if y[i+1]>=0 else '#f43f5e', width=3, shape='spline', smoothing=1.3), hoverinfo='skip', showlegend=False))
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=500, margin=dict(l=0,r=0,t=0,b=0), xaxis=dict(showgrid=False, color='#475569'), yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.03)', color='#475569'))
            st.plotly_chart(fig, use_container_width=True)

        elif menu == "⏰ Análise de Janelas":
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("📅 Dias da Semana")
                d_s = {0: 'Segunda', 1: 'Terça', 2: 'Quarta', 3: 'Quinta', 4: 'Sexta', 5: 'Sábado', 6: 'Domingo'}
                res_d = df_clean.groupby('Dia_Num').agg({'Valor_Final': 'sum'}).sort_index()
                for idx, row in res_d.iterrows():
                    st.markdown(f'<div class="perf-card"><div><b>{d_s[idx]}</b></div><div style="text-align:right;"><span class="{"val-pos" if row["Valor_Final"]>=0 else "val-neg"}">{format_br(row["Valor_Final"])}</span></div></div>', unsafe_allow_html=True)
            with c2:
                st.subheader("⌚ Horários")
                df_clean['FH'] = pd.cut(df_clean['Hora'], bins=[0,6,12,18,24], labels=['Madrugada','Manhã','Tarde','Noite'], include_lowest=True)
                res_h = df_clean.groupby('FH', observed=False).agg({'Valor_Final': 'sum'})
                for f, row in res_h.iterrows():
                    st.markdown(f'<div class="perf-card"><div><b>{f}</b></div><div style="text-align:right;"><span class="{"val-pos" if row["Valor_Final"]>=0 else "val-neg"}">{format_br(row["Valor_Final"])}</span></div></div>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Erro no processamento.")

elif menu == "📖 Como Extrair":
    st.markdown("<h1 style='color: white; text-align: center;'>📖 Guia de Extração</h1><br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="step-box"><h3>1️⃣ Acesse sua Conta</h3><p>Vá em: <b>Minha Conta</b> > <b>Minha Atividade</b> > <b>Histórico de Transações</b>.</p></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="step-box"><h3>2️⃣ Baixe o CSV</h3><p>Filtre o período e clique em <b>Download como CSV</b> no fim da página.</p></div>', unsafe_allow_html=True)
else:
    st.info("👋 Bem-vindo! Suba o extrato Betfair no menu lateral.")
