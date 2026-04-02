import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from datetime import datetime

# =====================================================
# CONFIGURAÇÃO DA PÁGINA
# =====================================================
st.set_page_config(
    page_title="Screener Pro Mobile",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =====================================================
# LÓGICA DE NEGÓCIO (Replicada da v6)
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
    
    # Slice recent history (excluding current candle to find prior pivot)
    # We look at [-30:-2] to find a completed pivot
    history_price = df['Close'].iloc[-lookback:-2]
    history_rsi = rsi_series.iloc[-lookback:-2]
    
    if signal_type == "BUY":
        # Bullish Divergence: Price Lower Low, RSI Higher Low
        prev_low_idx = history_price.idxmin()
        prev_low_price = history_price.min()
        try:
            prev_low_rsi = rsi_series.loc[prev_low_idx]
        except:
            return False 
        
        if current_price < prev_low_price and current_rsi > prev_low_rsi:
            return True
            
    elif signal_type == "SELL":
        # Bearish Divergence: Price Higher High, RSI Lower High
        prev_high_idx = history_price.idxmax()
        prev_high_price = history_price.max()
        try:
            prev_high_rsi = rsi_series.loc[prev_high_idx]
        except:
            return False

        if current_price > prev_high_price and current_rsi < prev_high_rsi:
            return True
            
    return False

def get_signal(row, df, rsi_series, k80_series, use_rsi_filter=False):
    # 1. Stoch Check (v4 Logic)
    kb = row['K_80']
    ky = row['K_170']
    
    # New: K80 Slope Check
    try:
        prev_k80 = k80_series.iloc[-2]
        curr_k80 = k80_series.iloc[-1]
    except:
        return "" # Not enough data
        
    stoch_signal = ""
    if not (pd.isna(kb) or pd.isna(ky)):
            if kb < 20 and kb > ky:
                # BUY Slope Logic: Current >= Prev (Rising or Flat)
                if curr_k80 >= prev_k80:
                    stoch_signal = "BUY"
            elif kb > 80 and kb < ky:
                # SELL Slope Logic: Current <= Prev (Falling or Flat)
                if curr_k80 <= prev_k80:
                    stoch_signal = "SELL"
    
    if not stoch_signal:
        return ""

    # Se filtro DESLIGADO, retorna o sinal puro
    if not use_rsi_filter:
        return f"COMPRA (Stoch)" if stoch_signal == "BUY" else f"VENDA (Stoch)"

    # 2. RSI Zone Check & Divergence Check (FILTRO LIGADO)
    current_rsi = rsi_series.iloc[-1]
    
    if stoch_signal == "BUY":
        if current_rsi < 35: # Using 35 as tolerance for "oversold area"
            if detect_divergence(df, rsi_series, "BUY"):
                return f"COMPRA (Div {round(current_rsi,0)})"
    
    elif stoch_signal == "SELL":
        if current_rsi > 65: # Tolerance for overbought
            if detect_divergence(df, rsi_series, "SELL"):
                return f"VENDA (Div {round(current_rsi,0)})"
        
    return ""

def run_scan(tickers, use_rsi_filter, status_placeholder, progress_bar):
    results = []
    total = len(tickers)
    
    status_placeholder.text(f"Baixando dados para {total} ativos...")
    data = yf.download(tickers, period="2y", group_by='ticker', progress=False, auto_adjust=True, threads=True)
    
    if data is None or data.empty:
        st.error("ERRO: Nenhum dado baixado.")
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
            if len(df) < 200: continue

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
                'Volume M (R$)': round(avg_vol / 1_000_000, 2), # Em Milhões
                'K_80': round(k80, 1),
                'K_170': round(k170, 1),
                'RSI': round(last_rsi, 1) if not pd.isna(last_rsi) else 0,
                'Sinal': ''
            }
            
            row_data['Sinal'] = get_signal(row_data, df, rsi_series, k80_series, use_rsi_filter)
            
            if row_data['Sinal'] != "":
                results.append(row_data)
                success_count += 1
                
        except Exception:
            continue

    status_placeholder.text(f"Finalizado. {success_count} oportunidades encontradas.")
    df_res = pd.DataFrame(results)
    if not df_res.empty:
        df_res.sort_values(by='Volume M (R$)', ascending=False, inplace=True)
    
    return df_res

# =====================================================
# UI FRONTEND (STREAMLIT)
# =====================================================

st.sidebar.title("🦅 Screener Pro")
st.sidebar.markdown("---")

rsi_filter_on = st.sidebar.toggle("Filtrar Divergência IFR", value=False)
run_btn = st.sidebar.button("INICIAR SCAN", type="primary")

st.title("Screener Estocástico Mobile (v6)")
st.caption("Versão Web responsiva para Android/iOS")

if run_btn:
    status_text = st.sidebar.empty()
    progress_bar = st.sidebar.progress(0)
    
    with st.spinner('Analisando o mercado...'):
        df = run_scan(list(set(TICKERS_BASE)), rsi_filter_on, status_text, progress_bar)
    
    if not df.empty:
        st.success(f"Encontrados {len(df)} ativos!")
        st.dataframe(
            df, 
            key="data",
            hide_index=True,
            use_container_width=True,
            column_config={
                "Ticker": st.column_config.TextColumn("Ativo"),
                "Preço": st.column_config.NumberColumn("Preço", format="R$ %.2f"),
                "Volume M (R$)": st.column_config.NumberColumn("Vol (M)", format="%.1f M"),
                "Sinal": st.column_config.TextColumn("Sinal"),
                "K_80": None,   # Ocultar
                "K_170": None,  # Ocultar
                "RSI": None     # Ocultar
            }
        )
        
        # Color coding in Streamlit isn't as direct as Tkinter tags,
        # but the dataframe is searchable and sortable natively.
        
    else:
        st.warning("Nenhum ativo encontrado com os critérios atuais.")
else:
    st.info("Clique em INICIAR SCAN na barra lateral.")
