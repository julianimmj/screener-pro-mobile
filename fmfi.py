"""
fmfi.py
-------
Replicação em Python do indicador Pine Script v5:
"Fourier Transformed Money Flow Index" (FMFI) by profitprotrading.

Configuração fixa (conforme especificação do workflow):
  - FOURIER_PERIOD = 5
  - Fourier Source  = hlc3  = (H + L + C) / 3
  - MFI_LENGTH      = 9
  - MFI_SMOOTH      = 4
  - MFI Source      = hlcc4 = (H + L + C + C) / 4

Sinais gerados:
  - fmfi_firm_buy  : FMFI cruzou PARA CIMA estando ABAIXO de 20
  - fmfi_firm_sell : FMFI cruzou PARA BAIXO estando ACIMA de 80
"""

import numpy as np
import pandas as pd

# ── Parâmetros fixos ────────────────────────────────────────────────────────
FOURIER_PERIOD = 5    # N — Fourier Period
MFI_LENGTH     = 9    # length — MFI period
MFI_SMOOTH     = 4    # smooth — EMA smoothing period
OB_LEVEL       = 80   # Overbought threshold (firm sell zone)
OS_LEVEL       = 20   # Oversold  threshold (firm buy  zone)


# ── Passo 1: Transformada de Fourier Discreta (DFT) ────────────────────────

def _dft_forward(x_arr: np.ndarray, n: int) -> np.ndarray:
    re = np.zeros(n, dtype=float)
    im = np.zeros(n, dtype=float)

    for i in range(n):
        kx   = float(i) / float(n)
        arg  = -2.0 * np.pi * kx
        re_i = 0.0
        im_i = 0.0
        for k in range(n):
            cos_k = np.cos(k * arg)
            sin_k = np.sin(k * arg)
            re_i += x_arr[k] * cos_k
            im_i += x_arr[k] * sin_k
        re[i] = re_i / float(n)
        im[i] = im_i / float(n)

    magnitudes = np.sqrt(re ** 2 + im ** 2)
    return magnitudes


# ── Passo 2: Séries auxiliares ──────────────────────────────────────────────

def _hlc3(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    return (high + low + close) / 3.0


def _hlcc4(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    return (high + low + close + close) / 4.0


# ── Passo 3: Money Flow Index ───────────────────────────────────────────────

def _raw_mfi(typical_price: pd.Series, volume: pd.Series,
             length: int) -> pd.Series:
    money_flow = typical_price * volume

    positive_mf = money_flow.where(
        typical_price > typical_price.shift(1), 0.0
    )
    negative_mf = money_flow.where(
        typical_price <= typical_price.shift(1), 0.0
    )

    pmf = positive_mf.rolling(window=length).sum()
    nmf = negative_mf.rolling(window=length).sum()

    mfi = 100.0 - (100.0 / (1.0 + pmf / nmf.replace(0, np.nan)))
    mfi = mfi.fillna(50.0)
    return mfi


def _ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


# ── Passo 4: Pipeline principal ──────────────────────────────────────────────

def compute_fmfi(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.lower() for c in df.columns]

    required = {'high', 'low', 'close', 'volume'}
    missing  = required - set(df.columns)
    if missing:
        raise ValueError(
            f"DataFrame está faltando as colunas: {missing}. "
            f"Colunas encontradas: {list(df.columns)}"
        )

    high   = df['high'].astype(float)
    low    = df['low'].astype(float)
    close  = df['close'].astype(float)
    volume = df['volume'].astype(float)

    fourier_src = _hlc3(high, low, close)
    ft = fourier_src.rolling(window=FOURIER_PERIOD).mean()
    raw_mfi = _raw_mfi(typical_price=ft, volume=volume, length=MFI_LENGTH)
    mf = _ema(raw_mfi, MFI_SMOOTH)

    mf_prev     = mf.shift(1)
    crossover   = mf > mf_prev
    crossunder  = mf < mf_prev

    df['fmfi']           = mf.values
    df['fmfi_prev']      = mf_prev.values
    df['fmfi_firm_buy']  = (crossover  & (mf < OS_LEVEL)).values
    df['fmfi_firm_sell'] = (crossunder & (mf > OB_LEVEL)).values

    return df


# ── Passo 5: Função de consulta ─────────────────────────────────────────────

def get_fmfi_signals(df: pd.DataFrame) -> dict:
    min_bars = FOURIER_PERIOD + MFI_LENGTH + MFI_SMOOTH + 10
    if len(df) < min_bars:
        raise ValueError(
            f"Dados insuficientes: {len(df)} barras fornecidas, "
            f"mínimo necessário: {min_bars}."
        )

    result_df = compute_fmfi(df)
    last      = result_df.iloc[-1]
    prev      = result_df.iloc[-2]

    is_buy = bool(last['fmfi_firm_buy']) or bool(prev['fmfi_firm_buy'])
    is_sell = bool(last['fmfi_firm_sell']) or bool(prev['fmfi_firm_sell'])

    return {
        'fmfi_value'    : float(last['fmfi']),
        'fmfi_firm_buy' : is_buy,
        'fmfi_firm_sell': is_sell,
        'bars_computed' : len(df),
    }
