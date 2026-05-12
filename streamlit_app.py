import streamlit as st
import pandas as pd
import yfinance as yf
import os
import json
import numpy as np
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from streamlit_autorefresh import st_autorefresh
import plotly.graph_objects as go

# ==========================================
# 1. PENGATURAN MARKAS (V7.0 TURBO ENGINE)
# ==========================================
st.set_page_config(page_title="The Commander V7.0", layout="centered", page_icon="⚔️")

st.markdown("""
    <style>
    .alarm-box { background-color: #4a1919; padding: 10px; border-radius: 5px; border-left: 5px solid #ff4b4b; margin-bottom: 15px;}
    </style>
""", unsafe_allow_html=True)

st_autorefresh(interval=180000, key="commander_radar_ping")

DAFTAR_HITAM = ["BUMN.JK", "IHSG.JK", "LQ45.JK", "COMP.JK", "IDX.JK"]
BATAS_LIKUIDITAS_RP = 5_000_000_000 
RASIO_SQUEEZE_MAKS = 1.1
FILE_PORTOFOLIO = "portofolio_aktif.json"

# --- MODUL GUDANG SENJATA DINAMIS ---
def muat_portofolio():
    if os.path.exists(FILE_PORTOFOLIO):
        with open(FILE_PORTOFOLIO, "r") as f:
            return json.load(f)
    return {
        "BBCA.JK": {"harga_beli": 7014.67, "stop_loss_pct": 5.0, "pengali_atr": 1.5, "tanggal_beli": "2026-04-21"},
        "NISP.JK": {"harga_beli": 1357.03, "stop_loss_pct": 3.0, "pengali_atr": 1.5, "tanggal_beli": "2026-05-06"},
        "MAPI.JK": {"harga_beli": 1407.10, "stop_loss_pct": 1.8, "pengali_atr": 1.5, "tanggal_beli": "2026-05-08"},
        "TINS.JK": {"harga_beli": 1020.00, "stop_loss_pct": 3.0, "pengali_atr": 1.5, "tanggal_beli": "2026-05-12"}
    }

def simpan_portofolio(data_porto):
    with open(FILE_PORTOFOLIO, "w") as f:
        json.dump(data_porto, f, indent=4)

PORTOFOLIO_AKTIF = muat_portofolio()

DAFTAR_SAHAM_INTI = [
    "BBCA.JK", "SSIA.JK", "DMAS.JK", "INTP.JK", "SMGR.JK", "PTPP.JK", "WTON.JK", "TLKM.JK", "ASII.JK", "GOTO.JK",
    "AMMN.JK", "BRIS.JK", "BBNI.JK", "BBRI.JK", "BMRI.JK", "BBTN.JK", "ADRO.JK", "ANTM.JK", "MDKA.JK", "PTBA.JK",
    "ITMG.JK", "UNTR.JK", "PGAS.JK", "MEDC.JK", "ELSA.JK", "AKRA.JK", "INDY.JK", "HRUM.JK", "BRPT.JK", "TPIA.JK",
    "CPIN.JK", "JPFA.JK", "ICBP.JK", "INDF.JK", "MYOR.JK", "AMRT.JK", "KLBF.JK", "SIDO.JK", "HEAL.JK", "MAPI.JK",
    "ACES.JK", "SCMA.JK", "EMTK.JK", "BUKA.JK", "ISAT.JK", "EXCL.JK", "JSMR.JK", "PGEO.JK", "CTRA.JK", "BSDE.JK",
    "BRMS.JK", "INCO.JK", "INKP.JK", "PTRO.JK", "CUAN.JK", "RAJA.JK", "BUMI.JK", "BIPI.JK", "AADI.JK", "BTPS.JK",
    "SMSM.JK", "PNLF.JK", "AVIA.JK", "VKTR.JK", "BJBR.JK", "BNGA.JK", "BDMN.JK", "SMRA.JK", "PWON.JK", "MIKA.JK", 
    "SILO.JK", "UNVR.JK", "GGRM.JK", "ERAA.JK", "TOWR.JK", "PANI.JK", "SRTG.JK", "BFIN.JK", "AUTO.JK", "NISP.JK",
    "DRMA.JK", "TINS.JK"
]

SEKTOR = {
    "FINANCIALS": ["BBCA.JK", "BBRI.JK", "BMRI.JK", "BBNI.JK", "BRIS.JK", "BNGA.JK", "BDMN.JK", "BBTN.JK", "BFIN.JK", "PNLF.JK"],
    "ENERGY": ["ADRO.JK", "PTBA.JK", "MEDC.JK", "ITMG.JK", "AKRA.JK", "PGAS.JK", "BUMI.JK"],
    "PROPERTIES": ["PANI.JK", "BSDE.JK", "CTRA.JK", "PWON.JK", "SMRA.JK", "ASRI.JK"],
    "TECHNOLOGY": ["GOTO.JK", "EMTK.JK", "BUKA.JK"],
    "CONSUMER_NON_CYCLICALS": ["ICBP.JK", "INDF.JK", "AMRT.JK", "UNVR.JK", "MYOR.JK", "HMSP.JK", "GGRM.JK"],
    "INFRASTRUCTURES": ["TLKM.JK", "ISAT.JK", "EXCL.JK", "PGEO.JK", "JSMR.JK"],
    "HEALTHCARE": ["KLBF.JK", "MIKA.JK", "SILO.JK", "HEAL.JK", "SIDO.JK"],
    "BASIC_MATERIALS": ["AMMN.JK", "TPIA.JK", "BRPT.JK", "MDKA.JK", "INCO.JK", "ANTM.JK", "SMGR.JK"],
    "INDUSTRIALS": ["ASII.JK", "UNTR.JK", "DRMA.JK", "SMSM.JK", "PTRO.JK"]
}

# ==========================================
# 2. ENGINE ANALISIS TAKTIS & RADAR TURBO
# ==========================================

@st.cache_data(ttl=180)
def download_data_turbo(tickers):
    hasil_data = {}
    with ThreadPoolExecutor(max_workers=20) as executor:
        future_to_ticker = {executor.submit(lambda t: yf.Ticker(t).history(period='8mo'), ticker): ticker for ticker in tickers}
        for future in as_completed(future_to_ticker):
            ticker = future_to_ticker[future]
            try:
                df = future.result()
                if not df.empty:
                    if df.index.tz is None:
                        df.index = df.index.tz_localize('UTC')
                    hasil_data[ticker] = df
            except: pass
    return hasil_data

def kalkulasi_unit(ticker, df, tanggal_maks, waktu_sekarang):
    try:
        if len(df) < 120 or (tanggal_maks.date() - df.index[-1].date()).days > 7: return None
        close, vol = df['Close'], df['Volume']
        if (close * vol).tail(10).mean() < BATAS_LIKUIDITAS_RP: return None
        
        sma20 = close.rolling(20).mean()
        std20 = close.rolling(20).std()
        bw = ((sma20 + 2*std20) - (sma20 - 2*std20)) / sma20 * 100
        bw_min_120 = bw.rolling(120).min().iloc[-1]
        rasio_sqz = (bw.iloc[-1] / bw_min_120) if bw_min_120 > 0 else 999.0
        
        macd = close.ewm(span=12).mean() - close.ewm(span=26).mean()
        sig = macd.ewm(span=9).mean()
        
        delta = close.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = -delta.clip(upper=0).rolling(14).mean()
        rsi = 100 - (100 / (1 + (gain/loss.replace(0, 1e-10))))

        sup = close.rolling(20).min().iloc[-1]
        res_tp = close.rolling(20).max().iloc[-1]

        jam_stabil = waktu_sekarang.time() >= datetime.strptime("09:30", "%H:%M").time()
        is_break = jam_stabil and (vol.iloc[-1] > (vol.tail(20).mean() * 1.5)) and (close.iloc[-1] > close.iloc[-2])

        tp = (df['High'] + df['Low'] + close) / 3
        vwap_10 = (tp * vol).rolling(10).sum() / vol.rolling(10).sum()
        obv = (np.sign(close.diff()) * vol).fillna(0).cumsum()
        
        is_ghost = (float(close.iloc[-1]) < float(vwap_10.iloc[-1])) and (float(obv.iloc[-1]) > float(obv.iloc[-11:-1].max()))

        return {
            "Ticker": ticker.replace(".JK", ""), "Harga": float(close.iloc[-1]), "Target Profit": float(res_tp), "Support": float(sup),
            "RSI": float(rsi.iloc[-1]), "Sqz_Ratio": float(rasio_sqz),
            "Is_Cross": macd.iloc[-2] <= sig.iloc[-2] and macd.iloc[-1] > sig.iloc[-1],
            "Is_Squeeze": rasio_sqz <= RASIO_SQUEEZE_MAKS, "Is_Break": is_break,
            "Is_Green": float(close.iloc[-1]) > float(close.iloc[-2]),
            "Is_Ghost": is_ghost
        }
    except: return None

def unit_guardian(kode, df, porto):
    harga_skrg, modal = float(df['Close'].iloc[-1]), float(porto['harga_beli'])
    status = "✅ Aman"
    
    if 'tanggal_beli' in porto and 'pengali_atr' in porto:
        try:
            tgl_beli = pd.to_datetime(porto['tanggal_beli'])
            if tgl_beli.tzinfo is None: tgl_beli = tgl_beli.tz_localize('UTC')
            
            tr = pd.concat([df['High'] - df['Low'], np.abs(df['High'] - df['Close'].shift()), np.abs(df['Low'] - df['Close'].shift())], axis=1).max(axis=1)
            df_porto = df[df.index >= tgl_beli]
            if not df_porto.empty:
                batas_ts = float(df_porto['High'].max()) - (float(tr.rolling(14).mean().iloc[-1]) * float(porto['pengali_atr']))
                
                # BARIS PERBAIKAN: Hanya bunyi jika Cuan
                if harga_skrg <= batas_ts and harga_skrg > modal: 
                    status = "💰 Kunci Laba"
        except: pass
            
    if 'stop_loss_pct' in porto and harga_skrg <= modal * (1 - (porto['stop_loss_pct'] / 100)): status = "🚨 Evakuasi"
    
    pnl_pct = ((harga_skrg - modal) / modal) * 100 if modal > 0 else 0
    return {"Ticker": kode.replace(".JK", ""), "Harga": harga_skrg, "PnL": pnl_pct, "Status": status}

def highlight_cells(val, col):
    if col == "RSI" and val < 40: return 'background-color: #4a1919; color: white;'
    if col == "Sqz_Ratio" and val <= RASIO_SQUEEZE_MAKS: return 'background-color: #524b11; color: white;'
    return ''

FORMAT_ANGKA = {"Harga": "{:,.0f}", "Target Profit": "{:,.0f}", "Support": "{:,.0f}", "RSI": "{:.1f}", "Sqz_Ratio": "{:.2f}x"}

# ==========================================
# 3. INTERFACE BRIEFING & EKSEKUSI
# ==========================================
waktu_wib = datetime.now(timezone.utc) + timedelta(hours=7)

st.sidebar.markdown("### 🗄️ GUDANG SENJATA")
df_porto_ui = pd.DataFrame.from_dict(PORTOFOLIO_AKTIF, orient='index')
if not df_porto_ui.empty:
    df_porto_ui.reset_index(inplace=True)
    df_porto_ui.rename(columns={'index': 'Ticker'}, inplace=True)
else:
    df_porto_ui = pd.DataFrame(columns=['Ticker', 'harga_beli', 'stop_loss_pct', 'pengali_atr', 'tanggal_beli'])

edited_df = st.sidebar.data_editor(df_porto_ui, num_rows="dynamic", use_container_width=True, hide_index=True)

if st.sidebar.button("💾 Simpan Gudang"):
    new_porto = {}
    for _, row in edited_df.iterrows():
        if pd.notna(row['Ticker']) and str(row['Ticker']).strip() != "":
            t = str(row['Ticker']).strip().upper()
            if not t.endswith(".JK"): t += ".JK"
            new_porto[t] = {
                "harga_beli": float(row['harga_beli']) if pd.notna(row['harga_beli']) else 0.0,
                "stop_loss_pct": float(row['stop_loss_pct']) if pd.notna(row['stop_loss_pct']) else 0.0,
                "pengali_atr": float(row['pengali_atr']) if pd.notna(row['pengali_atr']) else 1.5,
                "tanggal_beli": str(row['tanggal_beli']) if pd.notna(row['tanggal_beli']) else datetime.now().strftime("%Y-%m-%d")
            }
    simpan_portofolio(new_porto)
    st.sidebar.success("Tersimpan!")
    st.rerun()

st.sidebar.divider()
alarm_aktif = st.sidebar.toggle("🔊 Alarm Suara", value=True)

berita_katalis = {}
if os.path.exists("katalis_aktif.csv"):
    try:
        df_kat = pd.read_csv("katalis_aktif.csv")
        berita_katalis = pd.Series(df_kat.Katalis.values, index=df_kat.Ticker).to_dict()
    except: pass

st.markdown("## 🎖️ THE COMMANDER V7.0")
st.caption(f"📅 **{waktu_wib.strftime('%Y-%m-%d %H:%M WIB')}** | Turbo Engine Restored")

panel_ihsg = st.empty()

with st.spinner("Menghidupkan Radar V7.0..."):
    semua_target = list(set(DAFTAR_SAHAM_INTI + list(PORTOFOLIO_AKTIF.keys())))
    if "^JKSE" not in semua_target: semua_target.append("^JKSE")
    semua_target = [t for t in semua_target if t not in DAFTAR_HITAM or t == "^JKSE"]
        
    data_all = download_data_turbo(semua_target)
    
    tanggal_maks = waktu_wib
    if data_all:
        tanggal_maks = max([df.index[-1] for t, df in data_all.items() if not df.empty], default=waktu_wib)
    
    if "^JKSE" in data_all and not data_all["^JKSE"].empty:
        df_ihsg = data_all["^JKSE"]
        close_skrg = float(df_ihsg['Close'].iloc[-1])
        close_kmrn = float(df_ihsg['Close'].iloc[-2])
        ma20 = float(df_ihsg['Close'].rolling(20).mean().iloc[-1])
        ihsg_pct = ((close_skrg - close_kmrn) / close_kmrn) * 100
        stat = "🐂 BULLISH" if close_skrg >= ma20 else "🐻 BEARISH"
        panel_ihsg.info(f"🌩️ **RADAR IHSG:** {close_skrg:,.0f} ({ihsg_pct:+.2f}%) | **Status:** {stat}")

    hasil_tempur, guardian_data, alarm_trigger = [], [], False

    for t in semua_target:
        if t == "^JKSE" or t not in data_all: continue 

        if t in PORTOFOLIO_AKTIF:
            guardian_data.append(unit_guardian(t, data_all[t], PORTOFOLIO_AKTIF[t]))

        res = kalkulasi_unit(t, data_all[t], tanggal_maks, waktu_wib)
        if res:
            res["Berita"] = f"🚨 {berita_katalis[t]}" if t in berita_katalis else "-"
            
            if res["Is_Cross"] and res["Is_Break"]: res["Sinyal"] = "⚔️ Full Assault"
            elif res["Is_Ghost"]: res["Sinyal"] = "👻 Ghost Accumulation"
            elif res["Is_Squeeze"] and res["Is_Cross"]: res["Sinyal"] = "🧨 Triggered Bomb"
            elif res["RSI"] < 35 and res["Is_Cross"]: res["Sinyal"] = "🦅 Phoenix Rising"
            else: res["Sinyal"] = "-"
            
            if res["Sinyal"] in ["⚔️ Full Assault", "🧨 Triggered Bomb", "👻 Ghost Accumulation"]: alarm_trigger = True
            hasil_tempur.append(res)
            
    df_final = pd.DataFrame(hasil_tempur)

if alarm_aktif and alarm_trigger:
    st.markdown("""<audio autoplay="true" src="https://actions.google.com/sounds/v1/alarms/beep_short.ogg"></audio>""", unsafe_allow_html=True)
    st.markdown('<div class="alarm-box"><b>🚨 PERHATIAN KOMANDAN:</b> ANOMALI TARGET TERDETEKSI!</div>', unsafe_allow_html=True)

with st.container(border=True):
    st.markdown("#### 🔥 OPERASI KHUSUS")
    if not df_final.empty:
        df_combo = df_final[df_final["Sinyal"] != "-"]
        st.dataframe(df_combo[["Ticker", "Sinyal", "Harga", "Target Profit", "Support", "Berita"]].style.format(FORMAT_ANGKA), hide_index=True, use_container_width=True)

with st.container(border=True):
    st.markdown("#### 🛡️ STATUS GUARDIAN")
    if guardian_data:
        cols = st.columns(len(guardian_data))
        for i, g in enumerate(guardian_data):
            with cols[i]:
                st.metric(label=f"**{g['Ticker']}**", value=f"Rp {g['Harga']:,.0f}", delta=f"{g['PnL']:.2f}%")
                st.caption(f"Status: **{g['Status']}**")

with st.container(border=True):
    st.markdown("#### 🌊 ARUS UANG (THE MAGE)")
    if not df_final.empty:
        for sek, tickers in SEKTOR.items():
            sektor_bersih = [t.replace('.JK', '') for t in tickers]
            df_sektor = df_final[df_final["Ticker"].isin(sektor_bersih)]
            total = len(df_sektor)
            if total > 0:
                hijau = df_sektor["Is_Green"].sum()
                pct = (hijau / total) * 100
                st.progress(pct/100, text=f"**{sek}**: {pct:.0f}% Hijau")

with st.container(border=True):
    st.markdown("#### 📊 PETA TACTICAL")
    ticker_pilihan = st.selectbox("Pilih Target:", options=["-"] + sorted(df_final["Ticker"].tolist()) if not df_final.empty else ["-"])
    if ticker_pilihan != "-":
        df_chart = data_all[ticker_pilihan + ".JK"].tail(60)
        fig = go.Figure(data=[go.Candlestick(x=df_chart.index, open=df_chart['Open'], high=df_chart['High'], low=df_chart['Low'], close=df_chart['Close'])])
        fig.update_layout(template="plotly_dark", height=400, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)
