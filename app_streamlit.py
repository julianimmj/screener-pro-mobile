import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from datetime import datetime
from fmfi import get_fmfi_signals

# =====================================================
# CONFIGURAÇÃO DA PÁGINA E CSS
# =====================================================
st.set_page_config(
    page_title="Screener Pro Mobile",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded",
)

# HIDE STREAMLIT CLOUD UI
hide_streamlit_style = """
<style>
    /* ══ Esconder o header inteiro visualmente, mas preservar sidebar toggle ══ */
    [data-testid="stHeader"] {
        background: transparent !important;
        visibility: hidden !important;
        height: 0 !important;
        min-height: 0 !important;
        padding: 0 !important;
        overflow: visible !important;
    }

    /* ══ Forçar o botão de abrir/fechar sidebar a permanecer visível ══ */
    [data-testid="collapsedControl"] {
        visibility: visible !important;
        display: flex !important;
        z-index: 999999 !important;
        position: fixed !important;
        top: 0.5rem !important;
        left: 0.5rem !important;
    }

    /* ══ Esconder elementos Cloud individualmente ══ */
    #MainMenu {display: none !important;}
    footer {display: none !important;}
    .stDeployButton {display: none !important;}
    [data-testid="stToolbar"] {display: none !important;}
    [data-testid="manage-app-button"] {display: none !important;}
    [data-testid="stDecoration"] {display: none !important;}
    [data-testid="stStatusWidget"] {display: none !important;}
    #GithubIcon {display: none !important;}
    .viewerBadge_container__1QSob {display: none !important;}
    .viewerBadge_link__qRIco {display: none !important;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)


st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');

/* Typography & Deep Dark Gradient Background */
html, body, [class*="css"]  {
    font-family: 'Outfit', sans-serif !important;
}
.stApp {
    background: linear-gradient(135deg, #0e1117 0%, #1a1e29 100%);
    color: #e2e8f0;
}

/* Glassmorphism Title */
.main-title {
    font-size: 2.8rem;
    font-weight: 700;
    background: -webkit-linear-gradient(45deg, #00E676, #00B0FF);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0px;
    padding-bottom: 0px;
}
.subtitle {
    color: #94a3b8;
    font-weight: 300;
    font-size: 1.1rem;
    margin-bottom: 2rem;
    letter-spacing: 0.5px;
}

/* Stylish Cards for Results */
.glass-card {
    background: rgba(30, 41, 59, 0.4);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 16px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.glass-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 25px rgba(0, 230, 118, 0.1);
    border: 1px solid rgba(0, 230, 118, 0.2);
}

.asset-info {
    display: flex;
    flex-direction: column;
}
.ticker {
    font-size: 1.6rem;
    font-weight: 700;
    color: #f8fafc;
    letter-spacing: 1px;
}
.price {
    font-size: 1rem;
    color: #cbd5e1;
}

.metrics-info {
    display: flex;
    gap: 1.5rem;
    text-align: center;
}
.metric-box {
    display: flex;
    flex-direction: column;
}
.metric-lbl {
    font-size: 0.75rem;
    text-transform: uppercase;
    color: #64748b;
    font-weight: 600;
}
.metric-val {
    font-size: 1.1rem;
    color: #e2e8f0;
    font-weight: 400;
}

/* Signal Badges */
.badge-buy {
    background: rgba(0, 230, 118, 0.15);
    color: #00E676;
    border: 1px solid rgba(0, 230, 118, 0.3);
    padding: 8px 16px;
    border-radius: 30px;
    font-weight: 700;
    font-size: 0.9rem;
    text-transform: uppercase;
    box-shadow: 0 0 10px rgba(0, 230, 118, 0.2);
}
.badge-sell {
    background: rgba(255, 23, 68, 0.15);
    color: #FF1744;
    border: 1px solid rgba(255, 23, 68, 0.3);
    padding: 8px 16px;
    border-radius: 30px;
    font-weight: 700;
    font-size: 0.9rem;
    text-transform: uppercase;
    box-shadow: 0 0 10px rgba(255, 23, 68, 0.2);
}

/* Sidebar Custom */
.stSidebar {
    background-color: rgba(15, 23, 42, 0.95);
    border-right: 1px solid rgba(255, 255, 255, 0.05);
}
</style>
""", unsafe_allow_html=True)

# =====================================================
# LÓGICA DE NEGÓCIO
# =====================================================

TICKERS_BASE = [
    # IBOVESPA / Principais Ações / Small Caps Líquidas
    "VALE3.SA", "PETR4.SA", "ITUB4.SA", "BBDC4.SA", "BBAS3.SA", "WEGE3.SA", "ABEV3.SA", "RENT3.SA", "BPAC11.SA", "SUZB3.SA",
    "ITSA4.SA", "HAPV3.SA", "EQTL3.SA", "RDOR3.SA", "LREN3.SA", "PRIO3.SA", "RADL3.SA", "UGPA3.SA", "GGBR4.SA", "CSAN3.SA",
    "VBBR3.SA", "B3SA3.SA", "MGLU3.SA", "RAIL3.SA", "EMBR3.SA", "VIVT3.SA", "CMIG4.SA", "HYPE3.SA", "JBSS3.SA", "TIMS3.SA",
    "BBSE3.SA", "BRFS3.SA", "CPLE6.SA", "ELET3.SA", "CCRO3.SA", "SBSP3.SA", "EGIE3.SA", "CPFE3.SA", "TOTVS3.SA", "MULT3.SA",
    "ENEV3.SA", "CSNA3.SA", "TAEE11.SA", "GOAU4.SA", "BRKM5.SA", "EMBR3.SA", "AZUL4.SA", "YDUQ3.SA", "USIM5.SA", "MRFG3.SA",
    "CVCB3.SA", "GOLL4.SA", "PETR3.SA", "ELET6.SA", "SANB11.SA", "KLBN11.SA", "VAMO3.SA", "ASAI3.SA", "CRFB3.SA", "NTCO3.SA",
    "ALPA4.SA", "BEEF3.SA", "ALSO3.SA", "ARZZ3.SA", "SOMA3.SA", "DXCO3.SA", "EZTC3.SA", "JHSF3.SA", "MRVE3.SA", "CYRE3.SA",
    "POSI3.SA", "SLCE3.SA", "SMTO3.SA", "TOTS3.SA", "ENGI11.SA", "TRPL4.SA", "RECV3.SA", "SIMH3.SA", "PCAR3.SA", "QUAL3.SA",
    "PETZ3.SA", "LIGT3.SA", "COGN3.SA", "IRBR3.SA", "CASH3.SA", "BHIA3.SA", "LWSA3.SA", "FLRY3.SA", "MDIA3.SA", "PSSA3.SA",
    "IGTI11.SA", "AURE3.SA", "AESB3.SA", "ALUP11.SA", "SAPR11.SA", "CXSE3.SA", "STBP3.SA", "RAPT4.SA", "POMO4.SA", "TASA4.SA",
    "MYPK3.SA", "SEQL3.SA", "LJQQ3.SA", "GRND3.SA", "GUAR3.SA", "ODPV3.SA", "PORT3.SA", "INTB3.SA", "MLAS3.SA", "AMBP3.SA",
    "CBAV3.SA", "TTEN3.SA", "AERI3.SA", "MATD3.SA", "ORVR3.SA", "LOGG3.SA", "MOVI3.SA", "JALL3.SA", "ANIM3.SA", "CURY3.SA", "DIRR3.SA",
    
    # ETFs Líquidos
    "BOVA11.SA", "SMAL11.SA", "IVVB11.SA", "HASH11.SA", "XINA11.SA", "NASD11.SA", "EURP11.SA", "GOLD11.SA", 
    "BOVV11.SA", "DIVO11.SA", "FIND11.SA", "GOVE11.SA", "MATB11.SA",
    
    # BDRs (Top Tech & Global)
    "AAPL34.SA", "MSFT34.SA", "AMZO34.SA", "NVDC34.SA", "GOGL34.SA", "TSLA34.SA", "META34.SA", "NFLX34.SA", "BABA34.SA", 
    "DISB34.SA", "MELI34.SA", "COCA34.SA", "PEP34.SA", "PGCO34.SA", "JNJB34.SA", "PFIZ34.SA", "WFCB34.SA", "JPMC34.SA",
    "VISA34.SA", "MA34.SA", "ADBE34.SA", "PYPL34.SA", "INTC34.SA", "AMD34.SA", "QCOM34.SA", "AVGO34.SA", "CRM34.SA",
    "NKE34.SA", "SBUX34.SA", "MCDC34.SA", "WALM34.SA", "COST34.SA", "XOM34.SA", "CVX34.SA", "BERK34.SA", "GSGI34.SA",
    "UBER34.SA", "ABNB34.SA", "SPOT34.SA", "TWLO34.SA", "ZM34.SA", "DOCU34.SA", "WDAY34.SA", "ADSK34.SA", "LRCX34.SA"
]

def calc_stoch_k(df, k_period=14):
    if len(df) < k_period:
        return pd.Series([np.nan] * len(df), index=df.index)
    low_min = df['Low'].rolling(window=k_period).min()
    high_max = df['High'].rolling(window=k_period).max()
    denom = high_max - low_min
    denom = denom.replace(0, 1e-10)
    k = 100 * (df['Close'] - low_min) / denom
    return k

def calc_rsi(df, period=14):
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss.replace(0, 1e-10)
    return 100 - (100 / (1 + rs))

def detect_divergence(df, rsi_series, signal_type):
    lookback = 30
    if len(df) < lookback: return False
    
    current_price = df['Close'].iloc[-1]
    current_rsi = rsi_series.iloc[-1]
    
    history_price = df['Close'].iloc[-lookback:-2]
    history_rsi = rsi_series.iloc[-lookback:-2]
    
    if signal_type == "BUY":
        prev_low_idx = history_price.idxmin()
        prev_low_price = history_price.min()
        try:
            prev_low_rsi = rsi_series.loc[prev_low_idx]
        except:
            return False 
        if current_price < prev_low_price and current_rsi > prev_low_rsi:
            return True
            
    elif signal_type == "SELL":
        prev_high_idx = history_price.idxmax()
        prev_high_price = history_price.max()
        try:
            prev_high_rsi = rsi_series.loc[prev_high_idx]
        except:
            return False
        if current_price > prev_high_price and current_rsi < prev_high_rsi:
            return True
            
    return False

def get_signal(row, df, rsi_series, k80_series, use_rsi_filter=False, use_fmfi_filter=True):
    kb = row['K_80']
    ky = row['K_170']
    
    try:
        prev_k80 = k80_series.iloc[-2]
        curr_k80 = k80_series.iloc[-1]
    except:
        return "" 
        
    stoch_signal = ""
    if not (pd.isna(kb) or pd.isna(ky)):
            if kb < 20 and kb > ky:
                if curr_k80 >= prev_k80:
                    stoch_signal = "BUY"
            elif kb > 80 and kb < ky:
                if curr_k80 <= prev_k80:
                    stoch_signal = "SELL"
    
    if not stoch_signal:
        return ""
        
    if use_fmfi_filter:
        try:
            fmfi_sig = get_fmfi_signals(df)
            if stoch_signal == "BUY" and not fmfi_sig['fmfi_firm_buy']:
                return ""
            if stoch_signal == "SELL" and not fmfi_sig['fmfi_firm_sell']:
                return ""
        except Exception:
            return ""

    if not use_rsi_filter:
        return f"COMPRA" if stoch_signal == "BUY" else f"VENDA"

    current_rsi = rsi_series.iloc[-1]
    if stoch_signal == "BUY":
        if current_rsi < 35:
            if detect_divergence(df, rsi_series, "BUY"):
                return f"COMPRA"
    elif stoch_signal == "SELL":
        if current_rsi > 65:
            if detect_divergence(df, rsi_series, "SELL"):
                return f"VENDA"
                
    return ""

def run_scan(tickers, use_rsi_filter, use_fmfi_filter, status_placeholder, progress_bar):
    results = []
    total = len(tickers)
    
    status_placeholder.markdown("*(📡) Extraindo e vetorizando o mercado em 1d (Nuvem de Alta Performance)...*")
    data = yf.download(tickers, period="2y", interval="1d", group_by='ticker', progress=False, auto_adjust=True, threads=True)
    
    if data is None or data.empty:
        st.error("ERRO: Nenhum dado baixado. Servidores YF indisponíveis.")
        return pd.DataFrame()

    count = 0
    success_count = 0
    
    for ticker in tickers:
        count += 1
        progress_bar.progress(count / total)
        
        try:
            df = data[ticker].copy()
            if df.empty or 'Close' not in df.columns:
                continue
            
            df.dropna(subset=['Close', 'Volume'], inplace=True)
            if len(df) < 50: continue

            avg_vol = df['Volume'].iloc[-20:].mean() * df['Close'].iloc[-1]
            is_bdr = ticker.endswith(('34.SA', '35.SA', '39.SA'))
            if not is_bdr and avg_vol < 1_000_000:
                continue
            
            k80_series = calc_stoch_k(df, 80)
            k80 = k80_series.iloc[-1]
            
            k170 = calc_stoch_k(df, 170).iloc[-1]
            
            rsi_series = calc_rsi(df, 14)
            last_rsi = rsi_series.iloc[-1]
            last_close = df['Close'].iloc[-1]

            if pd.isna(k80) or pd.isna(k170): continue

            row_data = {
                'Ticker': ticker.replace(".SA", ""),
                'Preço': round(last_close, 2),
                'Volume M (R$)': round(avg_vol / 1_000_000, 2),
                'K_80': round(k80, 1),
                'K_170': round(k170, 1),
                'RSI': round(last_rsi, 1) if not pd.isna(last_rsi) else 0,
                'Sinal': ''
            }
            
            row_data['Sinal'] = get_signal(row_data, df, rsi_series, k80_series, use_rsi_filter, use_fmfi_filter)
            
            if row_data['Sinal'] != "":
                results.append(row_data)
                success_count += 1
                
        except Exception:
            continue

    status_placeholder.markdown(f"**Finalizado!** Mapeamos {success_count} oportunidades na última sessão.")
    df_res = pd.DataFrame(results)
    if not df_res.empty:
        df_res.sort_values(by='Volume M (R$)', ascending=False, inplace=True)
    
    return df_res

# =====================================================
# UI FRONTEND SUPERIOR (STREAMLIT)
# =====================================================

st.markdown('<div class="main-title">Screener Estocástico Pro</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Inteligência de varredura ativa conectada em tempo real (Versão Nuvem)</div>', unsafe_allow_html=True)

st.sidebar.markdown("## 🦅 Painel de Controle")
st.sidebar.markdown("Configure a densidade analítica e o motor de decisão do algoritmo.")

st.sidebar.markdown("---")
fmfi_filter_on = st.sidebar.toggle("🌐 Confirmação Extrema FMFI", value=True)
st.sidebar.markdown("<p style='font-size:0.85rem; color:#94a3b8; font-weight:300; margin-bottom:15px; line-height:1.4;'>Garante através da <strong>Transformada de Fourier</strong> que a recomendação só seja exibida se o ativo estiver em uma zona aguda de sobrecompra (VENDA) ou sobrevivência (COMPRA). Minimiza drasticamente os ruídos.</p>", unsafe_allow_html=True)

rsi_filter_on = st.sidebar.toggle("📉 Filtro Divergência IFR", value=False)
st.sidebar.markdown("<p style='font-size:0.85rem; color:#94a3b8; font-weight:300; margin-bottom:15px; line-height:1.4;'>Exige visualmente uma <strong>divergência</strong> clássica entre o fluxo do preço e o momentum (IFR). Se o preço fez fundo duplo mais baixo e o IFR fez fundo mais alto, a compra é aprovada.</p>", unsafe_allow_html=True)
st.sidebar.markdown("---")

run_btn = st.sidebar.button("INICIAR SCAN PROFUNDO", type="primary", use_container_width=True)

if run_btn:
    status_text = st.sidebar.empty()
    progress_bar = st.sidebar.progress(0)
    
    with st.spinner('Acessando malha de ativos globais...'):
        df = run_scan(list(set(TICKERS_BASE)), rsi_filter_on, fmfi_filter_on, status_text, progress_bar)
    
    if not df.empty:
        st.markdown(f"##### Encontramos **{len(df)}** ativos convergindo nos algoritmos:")
        
        df_buy = df[df['Sinal'].str.contains("COMPRA")]
        df_sell = df[df['Sinal'].str.contains("VENDA")]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("<h4 style='text-align: center; color: #00E676; margin-bottom: 20px;'>🛒 Sinais de COMPRA</h4>", unsafe_allow_html=True)
            if df_buy.empty:
                st.info("Nenhum sinal de compra agudo detectado hoje.")
            else:
                for idx, row in df_buy.iterrows():
                    badge_class = "badge-buy"
                    card_html = f'<div class="glass-card"><div class="asset-info"><span class="ticker">{row["Ticker"]}</span><span class="price">R$ {row["Preço"]:.2f}</span></div><div class="metrics-info"><div class="metric-box"><span class="metric-lbl">Volume</span><span class="metric-val">{row["Volume M (R$)"]}M</span></div></div><div class="{badge_class}">{row["Sinal"]}</div></div>'
                    st.markdown(card_html, unsafe_allow_html=True)
                    
        with col2:
            st.markdown("<h4 style='text-align: center; color: #FF1744; margin-bottom: 20px;'>📉 Sinais de VENDA</h4>", unsafe_allow_html=True)
            if df_sell.empty:
                st.info("Nenhum sinal de venda agudo detectado hoje.")
            else:
                for idx, row in df_sell.iterrows():
                    badge_class = "badge-sell"
                    card_html = f'<div class="glass-card"><div class="asset-info"><span class="ticker">{row["Ticker"]}</span><span class="price">R$ {row["Preço"]:.2f}</span></div><div class="metrics-info"><div class="metric-box"><span class="metric-lbl">Volume</span><span class="metric-val">{row["Volume M (R$)"]}M</span></div></div><div class="{badge_class}">{row["Sinal"]}</div></div>'
                    st.markdown(card_html, unsafe_allow_html=True)
            
    else:
        st.warning("Nenhum ativo detectado sob as fortes condições matemáticas configuradas.")
else:
    st.info("Algoritmo em repouso. Selecione suas preferências na barra esférica lateral e inicie.")
