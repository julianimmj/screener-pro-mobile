import customtkinter as ctk
import pandas as pd
import yfinance as yf
import numpy as np
import threading
from tkinter import ttk
import tkinter as tk
from datetime import datetime

# =====================================================
# CONFIGURAÇÃO DE APARENCIA
# =====================================================
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# =====================================================
# DADOS E LÓGICA (BACKEND)
# =====================================================

TICKERS_BASE = [
    # IBOVESPA / Principais Ações / Small Caps Líquidas
    "VALE3.SA", "PETR4.SA", "ITUB4.SA", "BBDC4.SA", "BBAS3.SA", "WEGE3.SA", "ABEV3.SA", "RENT3.SA", "BPAC11.SA", "SUZB3.SA",
    "ITSA4.SA", "HAPV3.SA", "EQTL3.SA", "RDOR3.SA", "LREN3.SA", "PRIO3.SA", "RADL3.SA", "UGPA3.SA", "GGBR4.SA", "CSAN3.SA",
    "VBBR3.SA", "B3SA3.SA", "MGLU3.SA", "RAIL3.SA", "EMBJ3.SA", "VIVT3.SA", "CMIG4.SA", "HYPE3.SA", "JBSS32.SA", "TIMS3.SA",
    "BBSE3.SA", "MBRF3.SA", "CPLE3.SA", "AXIA3.SA", "MOTV3.SA", "SBSP3.SA", "EGIE3.SA", "CPFE3.SA", "TOTS3.SA", "MULT3.SA",
    "ENEV3.SA", "CSNA3.SA", "TAEE11.SA", "GOAU4.SA", "BRKM5.SA", "AZUL3.SA", "YDUQ3.SA", "USIM5.SA", "CVCB3.SA", "PETR3.SA",
    "AXIA6.SA", "SANB11.SA", "KLBN11.SA", "VAMO3.SA", "ASAI3.SA", "NATU3.SA", "ALPA4.SA", "BEEF3.SA", "ALOS3.SA", "AZZA3.SA",
    "DXCO3.SA", "EZTC3.SA", "JHSF3.SA", "MRVE3.SA", "CYRE3.SA", "POSI3.SA", "SLCE3.SA", "SMTO3.SA", "TOTS3.SA", "ENGI11.SA",
    "ISAE4.SA", "RECV3.SA", "SIMH3.SA", "PCAR3.SA", "QUAL3.SA", "AUAU3.SA", "LIGT3.SA", "COGN3.SA", "IRBR3.SA", "CASH3.SA",
    "BHIA3.SA", "LWSA3.SA", "FLRY3.SA", "MDIA3.SA", "PSSA3.SA", "IGTI11.SA", "AURE3.SA", "ALUP11.SA", "SAPR11.SA", "CXSE3.SA",
    "RAPT4.SA", "POMO4.SA", "TASA4.SA", "MYPK3.SA", "SEQL3.SA", "LJQQ3.SA", "GRND3.SA", "RIAA3.SA", "SAUD3.SA",
    "INTB3.SA", "MLAS3.SA", "AMBP3.SA", "CBAV3.SA", "TTEN3.SA", "AERI3.SA", "MATD3.SA", "ORVR3.SA", "LOGG3.SA", "MOVI3.SA",
    "JALL3.SA", "ANIM3.SA", "CURY3.SA", "DIRR3.SA",
    
    # ETFs Líquidos
    "BOVA11.SA", "SMAL11.SA", "IVVB11.SA", "HASH11.SA", "XINA11.SA", "NASD11.SA", "GOLD11.SA", 
    "BOVV11.SA", "DIVO11.SA", "FIND11.SA", "GOVE11.SA", "MATB11.SA",
    
    # BDRs (Top Tech & Global)
    "AAPL34.SA", "MSFT34.SA", "AMZO34.SA", "NVDC34.SA", "GOGL34.SA", "TSLA34.SA", "M1TA34.SA", "NFLX34.SA", "BABA34.SA", 
    "DISB34.SA", "MELI34.SA", "COCA34.SA", "PEPB34.SA", "PGCO34.SA", "JNJB34.SA", "PFIZ34.SA", "WFCO34.SA", "JPMC34.SA",
    "VISA34.SA", "MSCD34.SA", "ADBE34.SA", "PYPL34.SA", "ITLC34.SA", "A1MD34.SA", "QCOM34.SA", "AVGO34.SA", "SSFO34.SA",
    "NIKE34.SA", "SBUB34.SA", "MCDC34.SA", "WALM34.SA", "COWC34.SA", "EXXO34.SA", "CHVX34.SA", "BERK34.SA", "GSGI34.SA",
    "U1BE34.SA", "AIRB34.SA", "S1PO34.SA", "T1WL34.SA", "Z1OM34.SA", "D1OC34.SA", "W1DA34.SA", "A1UT34.SA", "L1RC34.SA"
]

class ScreenerLogic:
    def __init__(self, callback_progress=None, callback_finished=None, callback_status=None):
        self.callback_progress = callback_progress
        self.callback_finished = callback_finished
        self.callback_status = callback_status
        self.is_running = False

    def calc_stoch_k(self, df, k_period=14):
        if len(df) < k_period:
            return pd.Series([np.nan] * len(df), index=df.index)
        low_min = df['Low'].rolling(window=k_period).min()
        high_max = df['High'].rolling(window=k_period).max()
        denom = high_max - low_min
        denom = denom.replace(0, 1e-10)
        k = 100 * (df['Close'] - low_min) / denom
        return k

    def calc_rsi(self, df, period=14):
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss.replace(0, 1e-10)
        return 100 - (100 / (1 + rs))

    def detect_divergence(self, df, rsi_series, signal_type):
        # Lookback window to find pivot (e.g., last 30 bars except the very last few)
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
                return False # Safety
            
            # Condition: Current Price < Prev Low but Current RSI > Prev RSI
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

            # Condition: Current Price > Prev High but Current RSI < Prev RSI
            if current_price > prev_high_price and current_rsi < prev_high_rsi:
                return True
                
        return False

    def get_signal(self, row, df, rsi_series, k1_series, k2_series, use_rsi_filter=False):
        try:
            prev_k1 = k1_series.iloc[-2]
            curr_k1 = k1_series.iloc[-1]
            prev_k2 = k2_series.iloc[-2]
            curr_k2 = k2_series.iloc[-1]
        except Exception:
            return "" # Not enough data
            
        stoch_signal = ""
        # COMPRA (BUY)
        if curr_k1 >= prev_k1 and prev_k2 < prev_k1 and curr_k2 >= curr_k1 and curr_k1 < 80:
            stoch_signal = "BUY"
        # VENDA (SELL)
        elif curr_k1 <= prev_k1 and prev_k2 > prev_k1 and curr_k2 <= curr_k1 and curr_k1 > 20:
            stoch_signal = "SELL"
        
        if not stoch_signal:
            return ""

        # Se filtro DESLIGADO, retorna o sinal puro
        if not use_rsi_filter:
            return "COMPRA (Stoch)" if stoch_signal == "BUY" else "VENDA (Stoch)"

        # 2. RSI Zone Check & Divergence Check (FILTRO LIGADO)
        current_rsi = rsi_series.iloc[-1]
        
        if stoch_signal == "BUY":
            if current_rsi < 35:
                if self.detect_divergence(df, rsi_series, "BUY"):
                    return f"COMPRA (Div {round(current_rsi,0)})"
        
        elif stoch_signal == "SELL":
            if current_rsi > 65:
                if self.detect_divergence(df, rsi_series, "SELL"):
                    return f"VENDA (Div {round(current_rsi,0)})"
            
        return ""

    def run_scan(self, use_rsi_filter=False):
        self.is_running = True
        mode_text = "COM FILTRO IFR" if use_rsi_filter else "SEM FILTRO"
        if self.callback_status: self.callback_status(f"Iniciando varredura v7 ({mode_text})...")
        if self.callback_progress: self.callback_progress(0.01)

        try:
            tickers = list(set(TICKERS_BASE))
            if self.callback_status: self.callback_status(f"Baixando dados para {len(tickers)} ativos...")
            
            data = yf.download(tickers, period="2y", group_by='ticker', progress=False, auto_adjust=True, threads=True)
            
            if data is None or data.empty:
                if self.callback_status: self.callback_status("ERRO CRÍTICO: Nenhum dado baixado. Verifique internet.")
                if self.callback_finished: self.callback_finished(pd.DataFrame())
                return

            results = []
            total = len(tickers)
            count = 0
            
            error_count = 0
            success_count = 0

            for ticker in tickers:
                count += 1
                try:
                    df = data[ticker].copy()
                    
                    if df.empty or 'Close' not in df.columns:
                        error_count += 1
                        continue

                    df.dropna(subset=['Close', 'Volume'], inplace=True)
                    
                    if len(df) < 200:
                        error_count += 1
                        continue

                    avg_vol = df['Volume'].iloc[-20:].mean() * df['Close'].iloc[-1]
                    
                    is_bdr = ticker.endswith(('34.SA', '35.SA', '39.SA'))
                    if not is_bdr and avg_vol < 1_000_000:
                        error_count += 1
                        continue
                    
                    k1_raw = self.calc_stoch_k(df, 80)
                    k2_raw = self.calc_stoch_k(df, 15)
                    
                    # %K1 e %K2 representam as linhas suavizadas uma vez do indicador no TradingView
                    k1_series = k1_raw.rolling(window=40).mean()
                    k2_series = k2_raw.rolling(window=3).mean()
                    
                    # %D1 e %D2 são as segundas suavizações (Smooth1 e Smooth2)
                    d1_series = k1_series.rolling(window=3).mean()
                    d2_series = k2_series.rolling(window=9).mean()
                    
                    k1 = k1_series.iloc[-1]
                    k2 = k2_series.iloc[-1]
                    
                    # Logica RSI (14)
                    rsi_series = self.calc_rsi(df, 14)
                    last_rsi = rsi_series.iloc[-1]
                    
                    last_close = df['Close'].iloc[-1]

                    if pd.isna(k1) or pd.isna(k2):
                         error_count += 1
                         continue

                    success_count += 1
                    row_data = {
                        'Ticker': ticker.replace(".SA", ""),
                        'Preço': round(last_close, 2),
                        'Volume ($)': avg_vol,
                        'K_80': round(k1, 1),
                        'K_15': round(k2, 1),
                        'RSI': round(last_rsi, 1) if not pd.isna(last_rsi) else 0
                    }
                    # Passa DF, RSI Series, K1 Series e K2 Series
                    row_data['Sinal'] = self.get_signal(row_data, df, rsi_series, k1_series, k2_series, use_rsi_filter)
                    
                    if row_data['Sinal'] != "":
                        results.append(row_data)
                    
                    if count % 10 == 0:
                        if self.callback_status: self.callback_status(f"Processando... ({count}/{total})", log=False)
                    
                except Exception as e:
                    if self.callback_status: self.callback_status(f"Erro em {ticker}: {str(e)}", log=True)
                    error_count += 1
                    continue
                
                if self.callback_progress: self.callback_progress(count / total)

            if self.callback_status: self.callback_status(f"Fim. Sucessos: {success_count}, Falhas: {error_count}", log=True)

            df_res = pd.DataFrame(results)
            if not df_res.empty:
                df_res.sort_values(by='Volume ($)', ascending=False, inplace=True)
                df_res['Volume ($)'] = df_res['Volume ($)'].apply(lambda x: f"{x:,.0f}")
            
            if self.callback_progress: self.callback_progress(1.0)
            if self.callback_finished: self.callback_finished(df_res)

        except Exception as e:
            if self.callback_status: self.callback_status(f"ERRO GERAL: {str(e)}", log=True)
            if self.callback_finished: self.callback_finished(pd.DataFrame())
        
        self.is_running = False

# =====================================================
# INTERFACE GRÁFICA (FRONTEND)
# =====================================================

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Screener Estocástico Pro v7.0 (Slope Filter)")
        self.geometry("1250x750")

        # Layout Main
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Antigravity\nScreener v7", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.scan_button = ctk.CTkButton(self.sidebar_frame, text="INICIAR SCAN", command=self.start_scan_thread, fg_color="#106A43", hover_color="#0C4F32")
        self.scan_button.grid(row=1, column=0, padx=20, pady=10)

        # Filtro RSI Toggle
        self.rsi_filter_var = ctk.BooleanVar(value=False)
        self.rsi_switch = ctk.CTkSwitch(self.sidebar_frame, text="Filtrar Divergência IFR", variable=self.rsi_filter_var)
        self.rsi_switch.grid(row=2, column=0, padx=20, pady=10)

        self.export_button = ctk.CTkButton(self.sidebar_frame, text="Exportar Excel", command=self.export_excel, state="disabled")
        self.export_button.grid(row=3, column=0, padx=20, pady=10)
        
        self.progress_bar = ctk.CTkProgressBar(self.sidebar_frame)
        self.progress_bar.grid(row=4, column=0, padx=20, pady=(10, 0))
        self.progress_bar.set(0)

        self.status_label = ctk.CTkLabel(self.sidebar_frame, text="Pronto.", wraplength=180)
        self.status_label.grid(row=5, column=0, padx=20, pady=20)
        
        # Main Area with Tabs
        self.tab_view = ctk.CTkTabview(self, corner_radius=10)
        self.tab_view.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        self.tab_res = self.tab_view.add("Resultados")
        self.tab_log = self.tab_view.add("Logs & Diagnóstico")
        
        # --- TAB RESULTADOS ---
        self.tab_res.grid_columnconfigure(0, weight=1)
        self.tab_res.grid_rowconfigure(1, weight=1)

        # Filtros
        self.filter_frame = ctk.CTkFrame(self.tab_res, fg_color="transparent")
        self.filter_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        self.filter_var = ctk.StringVar(value="Todos")
        self.filter_combo = ctk.CTkComboBox(self.filter_frame, values=["Todos", "Com Sinal", "Compra", "Venda"], command=self.filter_table, variable=self.filter_var)
        self.filter_combo.pack(side="left")
        
        self.label_info = ctk.CTkLabel(self.filter_frame, text="Top Volume (150+ Ativos)", text_color="gray")
        self.label_info.pack(side="right")

        # Treeview (Tabela)
        self.tree_frame = ctk.CTkFrame(self.tab_res)
        self.tree_frame.grid(row=1, column=0, sticky="nsew")
        self.tree_frame.grid_columnconfigure(0, weight=1)
        self.tree_frame.grid_rowconfigure(0, weight=1)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", 
                        background="#2b2b2b", 
                        foreground="white", 
                        fieldbackground="#2b2b2b", 
                        bordercolor="#343638", 
                        borderwidth=0,
                        font=('Arial', 10))
        style.configure("Treeview.Heading", background="#343638", foreground="white", relief="flat", font=('Arial', 11, 'bold'))
        style.map("Treeview", background=[('selected', '#1f538d')])

        columns = ("Ticker", "Preço", "Sinal", "K 80", "K 15", "RSI", "Volume ($)")
        self.tree = ttk.Treeview(self.tree_frame, columns=columns, show="headings", style="Treeview")
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=90, anchor="center")
        
        self.tree.column("Ticker", width=70)
        self.tree.column("Sinal", width=140)
        self.tree.column("Volume ($)", width=110)

        scrollbar = ctk.CTkScrollbar(self.tree_frame, orientation="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        
        self.tree.tag_configure("COMPRA", foreground="#00E676") 
        self.tree.tag_configure("VENDA", foreground="#FF1744")
        self.tree.tag_configure("NORMAL", foreground="white")

        # --- TAB LOGS ---
        self.tab_log.grid_columnconfigure(0, weight=1)
        self.tab_log.grid_rowconfigure(0, weight=1)
        
        self.log_box = ctk.CTkTextbox(self.tab_log, font=("Consolas", 12))
        self.log_box.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.log_box.insert("0.0", "--- Log do Sistema Iniciado ---\nAguardando comando...\n")

        self.current_df = pd.DataFrame()

    def start_scan_thread(self):
        self.scan_button.configure(state="disabled")
        self.export_button.configure(state="disabled")
        self.progress_bar.set(0)
        self.clear_logs()
        
        use_filter = self.rsi_filter_var.get()
        self.update_status(f"Iniciando... (Filtro={'LIGADO' if use_filter else 'DESLIGADO'})", log=True)
        
        logic = ScreenerLogic(
            callback_progress=self.update_progress,
            callback_finished=self.on_scan_finished,
            callback_status=self.update_status
        )
        
        thread = threading.Thread(target=logic.run_scan, args=(use_filter,), daemon=True)
        thread.start()

    def update_progress(self, val):
        self.progress_bar.set(val)

    def update_status(self, text, log=False):
        # Update label
        self.status_label.configure(text=text[:50] + "..." if len(text) > 50 else text)
        if log:
            timestamp = datetime.now().strftime("[%H:%M:%S] ")
            self.log_box.insert("end", timestamp + text + "\n")
            self.log_box.see("end")

    def clear_logs(self):
        self.log_box.delete("0.0", "end")

    def on_scan_finished(self, df):
        self.current_df = df
        self.scan_button.configure(state="normal")
        self.progress_bar.set(0)
        
        if not df.empty:
            self.export_button.configure(state="normal")
            self.after(0, self.populate_table)
            self.update_status(f"Scan finalizado. {len(df)} ativos carregados.", log=True)
        else:
            self.update_status("Scan finalizado SEM RESULTADOS.", log=True)
            
    def populate_table(self):
        # Limpa tabela
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        if self.current_df.empty:
            return

        # Filtros
        filter_type = self.filter_var.get()
        df_show = self.current_df.copy()
        
        if filter_type == "Com Sinal":
            df_show = df_show[df_show['Sinal'] != ""]
        elif filter_type == "Compra":
            df_show = df_show[df_show['Sinal'].str.contains("COMPRA")]
        elif filter_type == "Venda":
            df_show = df_show[df_show['Sinal'].str.contains("VENDA")]
            
        # Limite visual (top 150)
        df_show = df_show.head(150)
        
        for _, row in df_show.iterrows():
            tag = "NORMAL"
            if "COMPRA" in row['Sinal']: tag = "COMPRA"
            if "VENDA" in row['Sinal']: tag = "VENDA"
            
            self.tree.insert("", "end", values=(
                row['Ticker'], row['Preço'], row['Sinal'], 
                row['K_80'], row['K_15'], row['RSI'], row['Volume ($)']
            ), tags=(tag,))
            
        self.update_status(f"Tabela atualizada: {len(df_show)} ativos.", log=True)

    def filter_table(self, choice):
        if not self.current_df.empty:
            self.populate_table()

    def export_excel(self):
        if self.current_df.empty: return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screener_result_{timestamp}.csv"
        self.current_df.to_csv(filename, index=False, sep=";", decimal=",")
        self.update_status(f"Salvo: {filename}")

if __name__ == "__main__":
    app = App()
    app.mainloop()
