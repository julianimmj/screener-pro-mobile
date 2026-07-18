import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import time
from datetime import datetime


def _reset_yfinance_session():
    """Limpa sessão/crumb do yfinance para forçar reautenticação."""
    try:
        import yfinance.data as _yfdata
        if hasattr(_yfdata, '_crumb') and hasattr(_yfdata, '_cookie'):
            _yfdata._crumb = None
            _yfdata._cookie = None
    except Exception:
        pass
    try:
        if hasattr(yf, 'shared') and hasattr(yf.shared, '_CACHE'):
            yf.shared._CACHE = {}
    except Exception:
        pass

# =====================================================
# CONFIGURAÇÃO DA PÁGINA E CSS
# =====================================================
st.set_page_config(
    page_title="Screener Pro Mobile",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded",
)

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
    # ── 200 Ações B3 Validadas (Alta Liquidez) ──
    "AALR3.SA", "ABEV3.SA", "AERI3.SA", "AGRO3.SA", "AHEB3.SA", "ALLD3.SA", "ALOS3.SA", "ALPA4.SA", "ALUP11.SA", "ALUP3.SA",
    "ALUP4.SA", "AMBP3.SA", "AMER3.SA", "ANIM3.SA", "APTI4.SA", "ARML3.SA", "ASAI3.SA", "AURE3.SA", "AXIA3.SA", "AZEV3.SA",
    "AZEV4.SA", "AZUL3.SA", "AZZA3.SA", "B3SA3.SA", "BALM4.SA", "BAZA3.SA", "BBAS3.SA", "BBDC3.SA", "BBDC4.SA", "BBSE3.SA",
    "BDLL4.SA", "BEEF3.SA", "BEES3.SA", "BGIP3.SA", "BGIP4.SA", "BHIA3.SA", "BLAU3.SA", "BMEB4.SA", "BMOB3.SA", "BNBR3.SA",
    "BOBR4.SA", "BPAC11.SA", "BRAP4.SA", "BRKM5.SA", "BRSR3.SA", "BRSR6.SA", "BSLI4.SA", "CAML3.SA", "CASH3.SA", "CBAV3.SA",
    "CEDO3.SA", "CEDO4.SA", "CGAS3.SA", "CGAS5.SA", "CMIG3.SA", "CMIG4.SA", "COGN3.SA", "CPFE3.SA", "CPLE3.SA", "CSAN3.SA",
    "CSMG3.SA", "CSNA3.SA", "CTKA4.SA", "CTSA3.SA", "CTSA4.SA", "CURY3.SA", "CVCB3.SA", "CXSE3.SA", "CYRE3.SA", "DASA3.SA",
    "DESK3.SA", "DEXP3.SA", "DEXP4.SA", "DIRR3.SA", "DXCO3.SA", "EALT4.SA", "EGIE3.SA", "EMBJ3.SA", "ENEV3.SA", "ENGI11.SA",
    "ENMT3.SA", "ENMT4.SA", "EPAR3.SA", "EQTL3.SA", "EVEN3.SA", "EZTC3.SA", "FHER3.SA", "FIQE3.SA", "FLRY3.SA", "FRAS3.SA",
    "GFSA3.SA", "GGBR3.SA", "GGBR4.SA", "GOAU4.SA", "GRND3.SA", "HAPV3.SA", "HBOR3.SA", "HBRE3.SA", "HBSA3.SA", "HOOT4.SA",
    "HYPE3.SA", "IFCM3.SA", "IGTI11.SA", "INEP4.SA", "INTB3.SA", "IRBR3.SA", "ISAE3.SA", "ISAE4.SA", "ITSA3.SA", "ITSA4.SA",
    "ITUB4.SA", "JALL3.SA", "JBSS32.SA", "JHSF3.SA", "JSLG3.SA", "KEPL3.SA", "KLBN11.SA", "LAND3.SA", "LAVV3.SA", "LEVE3.SA",
    "LIGT3.SA", "LJQQ3.SA", "LOGG3.SA", "LOGN3.SA", "LPSB3.SA", "LREN3.SA", "LWSA3.SA", "MATD3.SA", "MDIA3.SA", "MEAL3.SA",
    "MGLU3.SA", "MLAS3.SA", "MOTV3.SA", "MOVI3.SA", "MRVE3.SA", "MULT3.SA", "MWET4.SA", "MYPK3.SA", "NGRD3.SA", "NUTR3.SA",
    "OIBR3.SA", "OIBR4.SA", "ONCO3.SA", "OPCT3.SA", "ORVR3.SA", "OSXB3.SA", "PCAR3.SA", "PDGR3.SA", "PETR3.SA", "PETR4.SA",
    "PFRM3.SA", "PGMN3.SA", "PINE4.SA", "PLPL3.SA", "PNVL3.SA", "POMO3.SA", "POMO4.SA", "POSI3.SA", "PRIO3.SA", "PRNR3.SA",
    "PSSA3.SA", "QUAL3.SA", "RADL3.SA", "RAIL3.SA", "RAPT4.SA", "RCSL3.SA", "RCSL4.SA", "RDOR3.SA", "RECV3.SA", "RENT3.SA",
    "ROMI3.SA", "RPMG3.SA", "SANB11.SA", "SANB3.SA", "SANB4.SA", "SAPR11.SA", "SAPR3.SA", "SAPR4.SA", "SBFG3.SA", "SBSP3.SA",
    "SEQL3.SA", "SHOW3.SA", "SHUL4.SA", "SIMH3.SA", "SLCE3.SA", "SMFT3.SA", "SMTO3.SA", "SOJA3.SA", "SUZB3.SA", "SYNE3.SA",
    "TAEE11.SA", "TAEE3.SA", "TAEE4.SA", "TASA4.SA", "TEKA4.SA", "TEND3.SA", "TFCO4.SA", "TGMA3.SA", "TIMS3.SA", "TOTS3.SA",

    # ── ETFs Líquidos (12) ──
    "BOVA11.SA", "SMAL11.SA", "IVVB11.SA", "HASH11.SA", "XINA11.SA", "NASD11.SA", "GOLD11.SA", 
    "BOVV11.SA", "DIVO11.SA", "FIND11.SA", "GOVE11.SA", "MATB11.SA",

    # ── BDRs Globais & Tech (45) ──
    "AAPL34.SA", "MSFT34.SA", "AMZO34.SA", "NVDC34.SA", "GOGL34.SA", "TSLA34.SA", "M1TA34.SA", "NFLX34.SA", "BABA34.SA", 
    "DISB34.SA", "MELI34.SA", "COCA34.SA", "PEPB34.SA", "PGCO34.SA", "JNJB34.SA", "PFIZ34.SA", "WFCO34.SA", "JPMC34.SA",
    "VISA34.SA", "MSCD34.SA", "ADBE34.SA", "PYPL34.SA", "ITLC34.SA", "A1MD34.SA", "QCOM34.SA", "AVGO34.SA", "SSFO34.SA",
    "NIKE34.SA", "SBUB34.SA", "MCDC34.SA", "WALM34.SA", "COWC34.SA", "EXXO34.SA", "CHVX34.SA", "BERK34.SA", "GSGI34.SA",
    "U1BE34.SA", "AIRB34.SA", "S1PO34.SA", "T1WL34.SA", "Z1OM34.SA", "D1OC34.SA", "W1DA34.SA", "A1UT34.SA", "L1RC34.SA"
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

def get_signal(row, df, rsi_series, k1_series, k2_series, use_rsi_filter=False):
    try:
        prev_k1 = k1_series.iloc[-2]
        curr_k1 = k1_series.iloc[-1]
        prev_k2 = k2_series.iloc[-2]
        curr_k2 = k2_series.iloc[-1]
    except Exception:
        return ""
        
    stoch_signal = ""
    # COMPRA (BUY)
    if curr_k1 >= prev_k1 and prev_k2 < prev_k1 and curr_k2 >= curr_k1 and curr_k1 < 80:
        stoch_signal = "BUY"
    # VENDA (SELL)
    elif curr_k1 <= prev_k1 and prev_k2 > prev_k1 and curr_k2 <= curr_k1 and curr_k1 > 20:
        stoch_signal = "SELL"
    
    if not stoch_signal:
        return ""
        
    if not use_rsi_filter:
        return "COMPRA" if stoch_signal == "BUY" else "VENDA"

    current_rsi = rsi_series.iloc[-1]
    if stoch_signal == "BUY":
        if current_rsi < 35:
            if detect_divergence(df, rsi_series, "BUY"):
                return "COMPRA"
    elif stoch_signal == "SELL":
        if current_rsi > 65:
            if detect_divergence(df, rsi_series, "SELL"):
                return "VENDA"
                
    return ""

def run_scan(tickers, use_rsi_filter, status_placeholder, progress_bar):
    results = []
    total = len(tickers)
    
    status_placeholder.markdown("*(📡) Extraindo e vetorizando o mercado em 1d (Nuvem de Alta Performance)...*")
    data = pd.DataFrame()
    for attempt in range(2):
        try:
            data = yf.download(tickers, period="2y", interval="1d", group_by='ticker', progress=False, auto_adjust=True, threads=True)
            if not data.empty:
                break
        except Exception:
            _reset_yfinance_session()
            time.sleep(1.0)
    
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
            
            k1_raw = calc_stoch_k(df, 80)
            k2_raw = calc_stoch_k(df, 15)
            
            # %K1 (80, 40) e %K2 (15, 3)
            k1_series = k1_raw.rolling(window=40).mean()
            k2_series = k2_raw.rolling(window=3).mean()
            
            # %D1 e %D2
            d1_series = k1_series.rolling(window=3).mean()
            d2_series = k2_series.rolling(window=9).mean()
            
            k1 = k1_series.iloc[-1]
            k2 = k2_series.iloc[-1]
            
            rsi_series = calc_rsi(df, 14)
            last_rsi = rsi_series.iloc[-1]
            last_close = df['Close'].iloc[-1]

            if pd.isna(k1) or pd.isna(k2): continue

            row_data = {
                'Ticker': ticker.replace(".SA", ""),
                'Preço': round(last_close, 2),
                'Volume M (R$)': round(avg_vol / 1_000_000, 2),
                'K_80': round(k1, 1),
                'K_15': round(k2, 1),
                'RSI': round(last_rsi, 1) if not pd.isna(last_rsi) else 0,
                'Sinal': ''
            }
            
            row_data['Sinal'] = get_signal(row_data, df, rsi_series, k1_series, k2_series, use_rsi_filter)
            
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
rsi_filter_on = st.sidebar.toggle("📉 Filtro Divergência IFR", value=False)
st.sidebar.markdown("<p style='font-size:0.85rem; color:#94a3b8; font-weight:300; margin-bottom:15px; line-height:1.4;'>Exige visualmente uma <strong>divergência</strong> clássica entre o fluxo do preço e o momentum (IFR). Se o preço fez fundo duplo mais baixo e o IFR fez fundo mais alto, a compra é aprovada.</p>", unsafe_allow_html=True)
st.sidebar.markdown("---")

run_btn = st.sidebar.button("INICIAR SCAN PROFUNDO", type="primary", use_container_width=True)

if run_btn:
    status_text = st.sidebar.empty()
    progress_bar = st.sidebar.progress(0)
    
    with st.spinner('Acessando malha de ativos globais...'):
        df = run_scan(list(set(TICKERS_BASE)), rsi_filter_on, status_text, progress_bar)
    
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
