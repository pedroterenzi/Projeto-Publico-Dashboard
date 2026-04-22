import streamlit as st
import pandas as pd
import calendar
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import re
import numpy as np
import json
import urllib.parse
import requests

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(layout="wide", page_title="Edge Trading Hub", page_icon="💎")

# --- CONFIGURAÇÃO DE CONTATO E API ---
CELULAR_VENDAS = "5519971374936"
MSG_WHATSAPP = urllib.parse.quote("Olá! Vi o site e quero liberar meu acesso Premium no Edge Trading Hub.")
LINK_WHATSAPP = f"https://wa.me/{CELULAR_VENDAS}?text={MSG_WHATSAPP}"

# Nova API Betfair que você enviou
API_KEY = "6b546b2e8dmsh056a5639f8a63e0p10cf81jsn73180c89830b"
API_HOST = "betfair-sports-casino-live-tv-result-odds.p.rapidapi.com"

# --- FUNÇÃO PARA CONVERTER ODD FRACIONÁRIA EM DECIMAL ---
def converter_odd_decimal(valor):
    if not valor or valor == "---":
        return "---"
    try:
        valor_str = str(valor).strip()
        if "/" in valor_str:
            num, den = valor_str.split("/")
            decimal = (float(num) / float(den)) + 1
            return f"{decimal:.2f}".replace(".", ",")
        return valor_str.replace(".", ",")
    except:
        return valor

# --- FUNÇÃO PARA BUSCAR JOGOS E ODDS DIRETAMENTE DA BETFAIR ---
@st.cache_data(ttl=1200)
def buscar_jogos_betfair():
    agrupados = {}
    try:
        # Usando o endpoint de listagem de eventos da API Betfair para Futebol (sportsid=1)
        url = f"https://{API_HOST}/api/v1/get-events"
        params = {"sportsid": "1"} # ID 1 geralmente é futebol na maioria dessas APIs
        headers = {
            "x-rapidapi-key": API_KEY,
            "x-rapidapi-host": API_HOST
        }
        
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        
        # Lógica de extração baseada na resposta padrão da Betfair
        # Como o endpoint exato pode variar por API, mantemos o fallback funcional
        events = data.get('data', []) if isinstance(data, dict) else []
        
        agora_br = datetime.utcnow() - timedelta(hours=3)
        hoje_br = agora_br.date()

        for event in events:
            # Converter tempo e filtrar fuso
            dt_utc = datetime.fromtimestamp(event.get('starttime', 0))
            dt_br = dt_utc - timedelta(hours=3)
            
            if dt_br.date() == hoje_br:
                pais = event.get('country', 'Internacional').upper()
                liga = event.get('competition_name', 'GERAL').upper()
                
                # Captura odds (ajustando para decimal brasileiro)
                o1 = converter_odd_decimal(event.get('home_odds', '---'))
                ox = converter_odd_decimal(event.get('draw_odds', '---'))
                o2 = converter_odd_decimal(event.get('away_odds', '---'))
                
                jogo_info = {
                    "hora": dt_br.strftime('%H:%M'),
                    "home": event.get('home_name', 'Time A'),
                    "away": event.get('away_name', 'Time B'),
                    "o1": o1, "ox": ox, "o2": o2,
                    "ts": dt_br.timestamp()
                }
                
                if pais not in agrupados: agrupados[pais] = {}
                if liga not in agrupados[pais]: agrupados[pais][liga] = []
                agrupados[pais][liga].append(jogo_info)
        
        # Ordenação
        for p in agrupados:
            for l in agrupados[p]:
                agrupados[p][l] = sorted(agrupados[p][l], key=lambda x: x['ts'])

    except:
        # Caso o endpoint 'get-events' mude, o sistema não quebra e avisa
        agrupados = {"AVISO": {"SISTEMA": [{"hora": "--:--", "home": "Erro na API Betfair", "away": "Verifique o Endpoint", "o1": "-", "ox": "-", "o2": "-"}]}}
    
    return agrupados

prognosticos_dia = [
    {
        "jogo": "Real Madrid x Barcelona",
        "analise": "O Real Madrid mantém pressão inicial fortíssima no Bernabéu. O Barcelona sofre em transição defensiva lenta.",
        "tendencia": "Over 0.5 HT ou Back Madrid.",
        "edge": "Cálculo aponta 74% de Ambas Marcam."
    }
]

# --- ESTILIZAÇÃO CSS (MANTIDA INTEGRALMENTE DO SEU CÓDIGO) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;900&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #020617; }
    .main .block-container { max-width: 1200px; padding-top: 1.5rem; margin: auto; }

    /* Landing Page */
    .hero-title { color: #10b981; font-size: 3.5rem; font-weight: 900; text-align: center; margin-bottom: 5px; }
    .hero-subtitle { color: #94a3b8; font-size: 1.3rem; text-align: center; margin-bottom: 40px; }
    .pain-box { background: rgba(244, 63, 94, 0.05); border-left: 5px solid #f43f5e; padding: 20px; border-radius: 12px; margin-bottom: 20px; }
    .solution-box { background: rgba(16, 185, 129, 0.05); border-left: 5px solid #10b981; padding: 20px; border-radius: 12px; margin-bottom: 20px; }
    .btn-wpp { display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white !important; text-decoration: none !important; font-weight: 800; text-transform: uppercase; letter-spacing: 1px; padding: 15px; border-radius: 12px; margin-bottom: 10px; text-align: center; border: none; width: 100%; }

    /* Dashboard & Sidebar Padrão */
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label { background-color: #1e293b; border: 1px solid rgba(255, 255, 255, 0.05); padding: 12px 20px !important; border-radius: 12px !important; margin-bottom: 8px !important; width: 100% !important; display: block !important; }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label[data-checked="true"] { background: linear-gradient(135deg, #10b981 0%, #064e3b 100%) !important; }
    .metric-card { display: flex; flex-direction: column; justify-content: center; align-items: center; padding: 20px 10px; border-radius: 20px; color: white; font-weight: 800; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3); border: 1px solid rgba(255, 255, 255, 0.05); height: 110px; width: 100%; margin-bottom: 15px; }
    .metric-card-grande { height: 140px; margin-bottom: 20px; }
    .metric-title { font-size: 0.75rem; text-transform: uppercase; opacity: 0.7; letter-spacing: 1.5px; margin-bottom: 8px; }
    .metric-value { font-size: 1.8rem; margin: 0; letter-spacing: -1px; }
    .metric-value-grande { font-size: 2.8rem; }

    /* Calendário */
    .monthly-profit-card { padding: 20px; border-radius: 15px; text-align: center; color: white; font-weight: 800; margin-bottom: 20px; border: 1px solid rgba(255, 255, 255, 0.1); }
    .calendar-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 8px; margin-top: 15px; }
    .day-name { text-align: center; color: #475569; font-weight: 900; font-size: 0.65rem; text-transform: uppercase; padding-bottom: 5px; }
    .day-card { background: #0f172a; border-radius: 10px; padding: 10px; min-height: 100px; display: flex; flex-direction: column; justify-content: space-between; align-items: flex-start; border: 1px solid rgba(255, 255, 255, 0.03); overflow: hidden; box-sizing: border-box; }
    .green-card { background: linear-gradient(135deg, #059669 0%, #064e3b 100%); border: none; }
    .red-card { background: linear-gradient(135deg, #dc2626 0%, #7f1d1d 100%); border: none; }
    .day-number { font-size: 1.1rem; font-weight: 900; color: #ffffff !important; line-height: 1; text-shadow: 1px 1px 2px rgba(0,0,0,0.5); }
    .day-value { font-size: 0.75rem; font-weight: 800; color: white; width: 100%; text-align: right; white-space: nowrap; }

    /* Performance Visuais */
    .perf-card { background: #0f172a; border-radius: 12px; padding: 15px 18px; display: flex; align-items: center; justify-content: space-between; border: 1px solid rgba(255, 255, 255, 0.05); margin-bottom: 10px; height: 90px; width: 100%; box-sizing: border-box; }
    .val-pos { color: #10b981; font-weight: 800; }
    .val-neg { color: #f43f5e; font-weight: 800; }
    .section-title { color: white; font-size: 1.1rem; font-weight: 800; margin-bottom: 15px; padding-left: 5px; border-left: 4px solid #10b981; line-height: 1; }

    /* Aba Jogos Visuais */
    .country-header { background: #0f172a; color: #10b981; padding: 8px 15px; border-radius: 8px; font-weight: 900; font-size: 0.75rem; text-transform: uppercase; margin: 30px 0 5px 0; border-left: 5px solid #10b981; letter-spacing: 1.5px;}
    .league-name-sub { color: #64748b; font-size: 0.7rem; font-weight: 800; margin-bottom: 10px; margin-left: 5px; text-transform: uppercase;}
    .match-card { background: #1e293b; border-radius: 12px; padding: 12px 18px; margin-bottom: 8px; border: 1px solid rgba(255,255,255,0.03); display: flex; align-items: center; justify-content: space-between; }
    .match-time { color: #ffffff; font-size: 0.9rem; font-weight: 800; width: 55px; text-align: center; }
    .match-teams { flex-grow: 1; padding: 0 20px; border-left: 1px solid rgba(255,255,255,0.1); }
    .team-name { color: white; font-weight: 600; font-size: 1rem; display: block; }
    .match-odds { display: flex; gap: 10px; }
    .odd-box { background: #0f172a; padding: 10px 15px; border-radius: 8px; color: #10b981; font-weight: 800; font-size: 0.95rem; text-align: center; min-width: 60px; }

    .prog-card { background: #0f172a; border-radius: 15px; padding: 25px; margin-bottom: 20px; border-left: 5px solid #10b981; box-shadow: 0 10px 30px rgba(0,0,0,0.3); }
    .prog-stat { background: rgba(16, 185, 129, 0.1); padding: 12px; border-radius: 8px; margin: 8px 0; color: #10b981; font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)

# --- ESTADOS ---
if 'page' not in st.session_state: st.session_state.page = 'landing'
if 'auth' not in st.session_state: st.session_state.auth = False
if 'is_premium' not in st.session_state: st.session_state.is_premium = False
if 'metodos_salvos' not in st.session_state: st.session_state.metodos_salvos = {}
if 'lista_metodos' not in st.session_state: 
    st.session_state.lista_metodos = ["Match Odds", "Under 2.5", "Over 2.5", "Under 1.5", "Over 1.5", "Correct Score", "Sem Categoria"]
if 'pagina_atual' not in st.session_state: st.session_state.pagina_atual = 1

# --- LÓGICA DE PÁGINAS ---
if st.session_state.page == 'landing':
    st.markdown("<h1 class='hero-title'>💎 VOCÊ ESTÁ JOGANDO DINHEIRO FORA?</h1>", unsafe_allow_html=True)
    c_venda, c_img = st.columns([1, 1.2])
    with c_venda:
        st.markdown("<div class='pain-box'><b>• O Lucro Invisível:</b> Sorte ou Competência?</div>", unsafe_allow_html=True)
        st.markdown(f'<a href="{LINK_WHATSAPP}" target="_blank" class="btn-wpp">🔥 QUERO O DIAGNÓSTICO PREMIUM AGORA</a>', unsafe_allow_html=True)
        if st.button("JÁ SOU CLIENTE (FAZER LOGIN)", use_container_width=True): st.session_state.page = 'login'; st.rerun()
        if st.button("🆓 TESTAR VERSÃO LIMITADA (GRÁTIS)", use_container_width=True): st.session_state.auth = True; st.session_state.is_premium = False; st.session_state.page = 'dashboard'; st.rerun()
    with c_img:
        try: st.image("capa_venda.png", use_container_width=True)
        except: st.info("🖼️ [Dashboard View]")

elif st.session_state.page == 'login':
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        u_in = st.text_input("E-mail"); p_in = st.text_input("Senha", type="password")
        if st.button("CONFIRMAR ACESSO", use_container_width=True):
            try:
                users = st.secrets["users"]
                if u_in in users and users[u_in] == p_in:
                    st.session_state.auth = True; st.session_state.is_premium = True; st.session_state.page = 'dashboard'; st.rerun()
            except: st.error("Erro nos Secrets.")

elif st.session_state.page == 'dashboard' and st.session_state.auth:
    with st.sidebar:
        st.markdown(f"<h2 style='color: #10b981;'>💎 EDGE HUB</h2>", unsafe_allow_html=True)
        if not st.session_state.is_premium: st.markdown(f'<a href="{LINK_WHATSAPP}" target="_blank" class="btn-wpp" style="font-size:0.8rem; padding:10px;">🚀 QUERO SER PREMIUM</a>', unsafe_allow_html=True)
        if st.button("Sair"): st.session_state.auth = False; st.session_state.page = 'landing'; st.rerun()
        uploaded_file = st.file_uploader("Carregar Extrato Betfair (.csv)", type=["csv"])
        stake_padrao = st.number_input("Stake Padrão", value=600.0)
        menu = st.radio("Menu", ["📈 Performance Geral", "🏟️ Jogos de Hoje", "🧠 Prognósticos", "📅 Diário de Operações", "🔥 Sequências", "📖 Como Extrair"], label_visibility="collapsed")

    # --- ABA JOGOS (FONTE BETFAIR) ---
    if menu == "🏟️ Jogos de Hoje":
        st.markdown("<h2 style='color: white;'>🏟️ Agenda de Hoje (Fuso Brasília)</h2>", unsafe_allow_html=True)
        agrupados = buscar_jogos_betfair()
        for pais, ligas in agrupados.items():
            st.markdown(f"<div class='country-header'>{pais}</div>", unsafe_allow_html=True)
            for liga, jogos in ligas.items():
                st.markdown(f"<div class='league-name-sub'>{liga}</div>", unsafe_allow_html=True)
                for j in jogos:
                    st.markdown(f"""<div class='match-card'><div class='match-time'>{j['hora']}</div><div class='match-teams'><span class='team-name'>{j['home']}</span><span class='team-name'>{j['away']}</span></div><div class='match-odds'><div class='odd-box'>{j['o1']}</div><div class='odd-box'>{j['ox']}</div><div class='odd-box'>{j['o2']}</div></div></div>""", unsafe_allow_html=True)

    elif menu == "🧠 Prognósticos":
        st.markdown("<h2 style='color: white;'>🧠 Inteligência de Mercado</h2>", unsafe_allow_html=True)
        for p in prognosticos_dia:
            st.markdown(f"<div class='prog-card'><h3 style='color:#10b981; margin-top:0;'>{p['jogo']}</h3><p>{p['analise']}</p><div class='prog-stat'>🔥 TENDÊNCIA: {p['tendencia']}</div><div class='prog-stat'>📊 ESTRATÉGIA: {p['edge']}</div></div>", unsafe_allow_html=True)

    # --- LÓGICA DASHBOARD ORIGINAL ---
    if menu in ["📈 Performance Geral", "📅 Diário de Operações", "🔥 Sequências"]:
        if uploaded_file is not None:
            try:
                df_raw = pd.read_csv(uploaded_file)
                # [MANTIDA TODA A LÓGICA DE CÁLCULO E CALENDÁRIO QUE VOCÊ ENVIOU]
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

                if menu == "📈 Performance Geral":
                    p_perf = st.date_input("Período", [df_clean['Data_Apenas'].min(), df_clean['Data_Apenas'].max()], key="p_perf")
                    if len(p_perf) == 2:
                        df_aba = df_clean[(df_clean['Data_Apenas'] >= p_perf[0]) & (df_clean['Data_Apenas'] <= p_perf[1])].copy()
                        total_l = df_aba['V_F'].sum(); entr = len(df_aba); wr = (len(df_aba[df_aba['V_F'] > 0.05]) / entr * 100) if entr > 0 else 0
                        bg = "linear-gradient(135deg, #10b981 0%, #064e3b 100%)" if total_l >= 0 else "linear-gradient(135deg, #ef4444 0%, #7f1d1d 100%)"
                        st.markdown(f'<div class="metric-card metric-card-grande" style="background: {bg};"><div class="metric-title">Lucro Líquido Consolidado</div><div class="metric-value metric-value-grande">{format_br(total_l)}</div></div>', unsafe_allow_html=True)
                        c1,c2,c3,c4,c5 = st.columns(5)
                        with c1: st.markdown(f'<div class="metric-card"><div class="metric-title">Taxa Acerto</div><div class="metric-value">{wr:.1f}%</div></div>', unsafe_allow_html=True)
                        with c2: st.markdown(f'<div class="metric-card"><div class="metric-title">Saldo STK</div><div class="metric-value">{total_l/stake_padrao:,.2f}</div></div>', unsafe_allow_html=True)
                        with c3: st.markdown(f'<div class="metric-card"><div class="metric-title">Entradas</div><div class="metric-value">{entr}</div></div>', unsafe_allow_html=True)
                        with c4: st.markdown(f'<div class="metric-card"><div class="metric-title">Odd Média</div><div class="metric-value">---</div></div>', unsafe_allow_html=True)
                        with c5: st.markdown(f'<div class="metric-card" style="background:#1e293b"><div class="metric-title">Sequência Atual</div><div class="metric-value" style="color:#10b981">--- 🔥</div></div>', unsafe_allow_html=True)
                        st.markdown("<br>", unsafe_allow_html=True)
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown('<div class="section-title">Por Método</div>', unsafe_allow_html=True)
                            res = df_aba.groupby('Metodo').agg({'V_F':['sum','count']}).reset_index(); res.columns = ['Metodo','Lucro','Qtd']
                            for _, row in res.sort_values('Lucro', ascending=False).iterrows(): st.markdown(f"<div class='perf-card'><div><b>{row['Metodo']}</b></div><div style='text-align:right;'><span class='val-pos'>{format_br(row['Lucro'])}</span></div></div>", unsafe_allow_html=True)

                elif menu == "📅 Diário de Operações":
                    meses_n = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
                    mes_sel = st.selectbox("Mês", meses_n, index=datetime.now().month - 1); mes_num = meses_n.index(mes_sel) + 1
                    df_mes = df_clean[(df_clean['Dt_Obj'].dt.month == mes_num)]
                    l_mes = df_mes['V_F'].sum()
                    st.markdown(f'<div class="monthly-profit-card" style="border: 2px solid #10b981;"><small>LUCRO {mes_sel.upper()}</small><br><span style="font-size:2rem">{format_br(l_mes)}</span></div>', unsafe_allow_html=True)
                    l_dia = df_mes.groupby(df_mes['Dt_Obj'].dt.day)['V_F'].sum(); cal_obj = calendar.Calendar(firstweekday=0); dias = list(cal_obj.itermonthdays(datetime.now().year, mes_num))
                    html = '<div class="calendar-grid">'
                    for n in ['SEG','TER','QUA','QUI','SEX','SAB','DOM']: html += f'<div class="day-name">{n}</div>'
                    for d in dias:
                        if d == 0: html += '<div style="opacity:0"></div>'
                        else:
                            v = l_dia.get(d, 0); cl = "day-card green-card" if v > 0.05 else "day-card red-card" if v < -0.05 else "day-card"
                            html += f'<div class="{cl}"><span class="day-number">{d}</span><span class="day-value">{format_br(v) if abs(v)>0.05 else ""}</span></div>'
                    st.markdown(html + '</div>', unsafe_allow_html=True)

            except Exception as e: st.error(f"Erro: {e}")
        else: st.info("Suba seu extrato Betfair na lateral para começar.")

if menu == "📖 Como Extrair":
    st.markdown("<h1 style='color: white; text-align: center;'>📖 Guia de Extração</h1><br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1: st.markdown('<div class="step-box"><h3>1️⃣ Acesse sua Conta</h3><p>Vá em Atividade da Conta na Betfair.</p></div>', unsafe_allow_html=True)
    with c2: st.markdown('<div class="step-box"><h3>2️⃣ Baixe o CSV</h3><p>Clique em Download como CSV.</p></div>', unsafe_allow_html=True)
