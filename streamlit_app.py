import streamlit as st
import pandas as pd
import yfinance as yf
import os
import json
import numpy as np
import requests
import imaplib
import email
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from streamlit_autorefresh import st_autorefresh
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ==========================================
# 1. PENGATURAN MARKAS (V8.0 ALL-IN-ONE)
# ==========================================
st.set_page_config(page_title="The Commander V8.0", layout="wide", page_icon="🏰")

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
FILE_JURNAL = "jurnal_tempur.csv"
FILE_KATALIS = "katalis_aktif.csv"

# --- IDE 4: MODUL PENCATAT JEJAK TEMPUR (TRADING JOURNAL) ---
def catat_jurnal(ticker, modal, harga_jual, status_jual):
    file_exists = os.path.isfile(FILE_JURNAL)
    pnl_pct = ((harga_jual - modal) / modal) * 100
    pnl_rp = harga_jual - modal # Asumsi per lembar, bisa disesuaikan dengan lot
    
    with open(FILE_JURNAL, 'a') as f:
        if not file_exists:
            f.write("Tanggal,Ticker,Harga_Beli,Harga_Jual,PnL_Pct,Status\n")
        tgl_skrg = datetime.now().strftime("%Y-%m-%d %H:%M")
        f.write(f"{tgl_skrg},{ticker},{modal},{harga_jual},{pnl_pct:.2f},{status_jual}\n")

# --- MODUL GUDANG SENJATA DINAMIS ---
def muat_portofolio():
    if os.path.exists(FILE_PORTOFOLIO):
        with open(FILE_PORTOFOLIO, "r") as f:
            return json.load(f)
    return {}

def simpan_portofolio(data_porto):
    with open(FILE_PORTOFOLIO, "w") as f:
        json.dump(data_porto, f, indent=4)

PORTOFOLIO_AKTIF = muat_portofolio()

# DAFTAR SAHAM (Disesuaikan dengan permintaan rotasi sebelumnya)
DAFTAR_SAHAM_INTI = [
    "BBCA.JK", "BBRI.JK", "BMRI.JK", "BBNI.JK", "ASII.JK", "TLKM.JK", "UNTR.JK", "BFIN.JK",
    "TINS.JK", "SMGR.JK", "PNLF.JK", "DRMA.JK", "SMSM.JK", "BBTN.JK", "AMMN.JK", "GOTO.JK",
    "BRIS.JK", "ADRO.JK", "PTBA.JK", "ITMG.JK", "PGAS.JK", "MEDC.JK", "AKRA.JK", "INDF.JK",
    "ICBP.JK", "MYOR.JK", "AMRT.JK", "KLBF.JK", "SIDO.JK", "HEAL.JK", "MAPI.JK", "ACES.JK"
]

SEKTOR = {
    "FINANCIALS": ["BBCA.JK", "BBRI.JK", "BMRI.JK", "BBNI.JK", "BRIS.JK", "BBTN.JK", "BFIN.JK", "PNLF.JK"],
    "ENERGY": ["ADRO.JK", "PTBA.JK", "MEDC.JK", "ITMG.JK", "AKRA.JK", "PGAS.JK"],
    "INDUSTRIALS": ["ASII.JK", "UNTR.JK", "DRMA.JK", "SMSM.JK"],
    "HEALTHCARE": ["KLBF.JK", "HEAL.JK", "SIDO.JK"]
}

# --- IDE 1: JALUR KOMUNIKASI TELEGRAM ---
def kirim_intelijen_telegram(pesan, token, chat_id):
    if not token or not chat_id: return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": pesan, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except:
        pass

# --- IDE 2: EKSTRAKTOR GMAIL (STOCKBIT SNIPS) ---
def ekstrak_gmail_katalis(email_user, email_pass):
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(email_user, email_pass)
        mail.select("inbox")
        
        # Cari email dari Stockbit Snips hari ini
        status, messages = mail.search(None, '(FROM "snips@stockbit.com" UNSEEN)')
        if status != "OK" or not messages[0]:
            return False, "Tidak ada email intelijen baru."
            
        latest_email_id = messages[0].split()[-1]
        status, msg_data = mail.fetch(latest_email_id, "(RFC822)")
        
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode()
                            # Ekstraksi Ticker sederhana: cari $TINS, $ASII, dll.
                            tickers_found = re.findall(r'\$([A-Z]{4})', body)
                            if tickers_found:
                                # Update CSV (Versi sederhana, menimpa dengan temuan baru)
                                df_baru = pd.DataFrame({"Ticker": [t + ".JK" for t in set(tickers_found)], "Katalis": ["Terdeteksi di Snips hari ini!"] * len(set(tickers_found))})
                                df_baru.to_csv(FILE_KATALIS, index=False)
                                return True, f"Katalis ditarik untuk: {', '.join(set(tickers_found))}"
        return False, "Format email tidak terbaca."
    except Exception as e:
        return False, f"Gagal menyadap Gmail: {str(e)}"

# ==========================================
# 2. ENGINE ANALISIS TAKTIS
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
                    if df.index.tz is None: df.index = df.index.tz_localize('UTC')
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
                
                if harga_skrg <= batas_ts and harga_skrg > modal: 
                    status = "💰 Kunci Laba"
        except: pass
            
    if 'stop_loss_pct' in porto and harga_skrg <= modal * (1 - (porto['stop_loss_pct'] / 100)): status = "🚨 Evakuasi"
    
    pnl_pct = ((harga_skrg - modal) / modal) * 100 if modal > 0 else 0
    return {"Ticker": kode.replace(".JK", ""), "Harga": harga_skrg, "PnL": pnl_pct, "Status": status, "Modal": modal}

def highlight_cells(val, col):
    if col == "RSI" and val < 40: return 'background-color: #4a1919; color: white;'
    if col == "Sqz_Ratio" and val <= RASIO_SQUEEZE_MAKS: return 'background-color: #524b11; color: white;'
    return ''

FORMAT_ANGKA = {"Harga": "{:,.0f}", "Target Profit": "{:,.0f}", "Support": "{:,.0f}", "RSI": "{:.1f}", "Sqz_Ratio": "{:.2f}x"}

# ==========================================
# 3. INTERFACE BRIEFING & EKSEKUSI
# ==========================================
waktu_wib = datetime.now(timezone.utc) + timedelta(hours=7)

with st.sidebar:
    st.markdown("### 🗄️ GUDANG SENJATA")
    
    # Editor Gudang
    df_porto = pd.DataFrame.from_dict(PORTOFOLIO_AKTIF, orient='index')
    if not df_porto.empty:
        df_porto.reset_index(inplace=True)
        df_porto.rename(columns={'index': 'Ticker'}, inplace=True)
    else:
        df_porto = pd.DataFrame(columns=['Ticker', 'harga_beli', 'stop_loss_pct', 'pengali_atr', 'tanggal_beli'])

    edited_df = st.data_editor(df_porto, num_rows="dynamic", use_container_width=True, hide_index=True)
    if st.button("💾 Simpan Gudang"):
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
        st.success("Tersimpan!")
        st.rerun()
        
    st.divider()
    st.markdown("### ⚔️ EKSEKUSI JUAL")
    st.caption("Tutup posisi & catat ke Jurnal Tempur")
    jual_ticker = st.selectbox("Pilih Aset:", ["-"] + list(PORTOFOLIO_AKTIF.keys()))
    jual_harga = st.number_input("Harga Jual Eksekusi:", min_value=0, value=0)
    
    if st.button("🔴 Eksekusi Jual & Catat"):
        if jual_ticker != "-" and jual_harga > 0:
            modal_aset = PORTOFOLIO_AKTIF[jual_ticker]["harga_beli"]
            status_akhir = "Profit" if jual_harga > modal_aset else "Loss"
            catat_jurnal(jual_ticker, modal_aset, jual_harga, status_akhir)
            
            # Hapus dari portofolio aktif
            del PORTOFOLIO_AKTIF[jual_ticker]
            simpan_portofolio(PORTOFOLIO_AKTIF)
            st.success(f"{jual_ticker} Dieksekusi! Jurnal tercatat.")
            st.rerun()

    st.divider()
    with st.expander("⚙️ PENGATURAN V8.0"):
        alarm_aktif = st.toggle("🔊 Alarm Suara", value=True)
        st.caption("Modul Telegram")
        tele_token = st.text_input("Bot Token", type="password")
        tele_chat_id = st.text_input("Chat ID")
        st.caption("Modul Ekstraktor Gmail")
        gmail_user = st.text_input("Email", placeholder="jenderal@gmail.com")
        gmail_pass = st.text_input("App Password", type="password")
        if st.button("🔄 Tarik Intelijen (Gmail)"):
            if gmail_user and gmail_pass:
                sukses, msg = ekstrak_gmail_katalis(gmail_user, gmail_pass)
                if sukses: st.success(msg)
                else: st.error(msg)
            else: st.warning("Masukkan Email & App Password Google.")

# --- BACA DATA KATALIS ---
berita_katalis = {}
if os.path.exists(FILE_KATALIS):
    try:
        df_kat = pd.read_csv(FILE_KATALIS)
        berita_katalis = pd.Series(df_kat.Katalis.values, index=df_kat.Ticker).to_dict()
    except: pass

st.markdown("## 🏰 THE COMMANDER V8.0")
st.caption(f"📅 **{waktu_wib.strftime('%Y-%m-%d %H:%M WIB')}** | Telegram + Profil Volume + Jurnal Tempur")

panel_ihsg = st.empty()

with st.spinner("Menghidupkan Radar V8.0..."):
    semua_target = list(set(DAFTAR_SAHAM_INTI + list(PORTOFOLIO_AKTIF.keys())))
    if "^JKSE" not in semua_target: semua_target.append("^JKSE")
    semua_target = [t for t in semua_target if t not in DAFTAR_HITAM or t == "^JKSE"]
        
    data_all = download_data_turbo(semua_target)
    
    tanggal_maks = waktu_wib
    if data_all:
        tanggal_maks = max([df.index[-1] for t, df in data_all.items() if not df.empty], default=waktu_wib)
    
    ihsg_val, ihsg_pct, ihsg_stat = None, None, "Menunggu Sinyal"
    if "^JKSE" in data_all and not data_all["^JKSE"].empty:
        df_ihsg = data_all["^JKSE"]
        if len(df_ihsg) >= 20:
            close_skrg = float(df_ihsg['Close'].iloc[-1])
            close_kmrn = float(df_ihsg['Close'].iloc[-2])
            ma20 = float(df_ihsg['Close'].rolling(20).mean().iloc[-1])
            ihsg_pct = ((close_skrg - close_kmrn) / close_kmrn) * 100
            ihsg_val = close_skrg
            ihsg_stat = "🐂 BULLISH - Cuaca Cerah!" if close_skrg >= ma20 else "🐻 BEARISH - Badai Beruang!"
            
    if ihsg_val is not None: panel_ihsg.info(f"🌩️ **RADAR IHSG:** {ihsg_val:,.0f} ({ihsg_pct:+.2f}%) | **Status Makro:** {ihsg_stat}")
    else: panel_ihsg.error("📡 **RADAR IHSG:** Data ^JKSE Kosong")

    hasil_tempur, guardian_data, alarm_trigger = [], [], False
    pesan_telegram_queue = []

    for t in semua_target:
        if t == "^JKSE" or t not in data_all: continue 

        if t in PORTOFOLIO_AKTIF:
            g_data = unit_guardian(t, data_all[t], PORTOFOLIO_AKTIF[t])
            guardian_data.append(g_data)
            if g_data["Status"] in ["💰 Kunci Laba", "🚨 Evakuasi"]:
                pesan_telegram_queue.append(f"⚠️ PERINGATAN {t}: Status {g_data['Status']} pada harga {g_data['Harga']}!")

        res = kalkulasi_unit(t, data_all[t], tanggal_maks, waktu_wib)
        if res:
            res["Berita"] = f"🚨 {berita_katalis[t]}" if t in berita_katalis else "-"
            
            if res["Is_Cross"] and res["Is_Break"]: res["Sinyal"] = "⚔️ Full Assault"
            elif res["Is_Ghost"]: res["Sinyal"] = "👻 Ghost Accumulation"
            elif res["Is_Squeeze"] and res["Is_Cross"]: res["Sinyal"] = "🧨 Triggered Bomb"
            elif res["RSI"] < 35 and res["Is_Cross"]: res["Sinyal"] = "🦅 Phoenix Rising"
            else: res["Sinyal"] = "-"
            
            if res["Sinyal"] in ["⚔️ Full Assault", "🧨 Triggered Bomb", "👻 Ghost Accumulation"]: 
                alarm_trigger = True
                pesan_telegram_queue.append(f"🚀 SINYAL {t}: {res['Sinyal']} di harga {res['Harga']}")
                
            hasil_tempur.append(res)
            
    df_final = pd.DataFrame(hasil_tempur)

# Tembak pesan Telegram jika ada alarm
if pesan_telegram_queue and tele_token and tele_chat_id:
    gabungan_pesan = "🏰 **MARKAS COMMANDER V8.0**\n\n" + "\n".join(pesan_telegram_queue)
    kirim_intelijen_telegram(gabungan_pesan, tele_token, tele_chat_id)

if alarm_aktif and alarm_trigger:
    st.markdown("""<audio autoplay="true" src="https://actions.google.com/sounds/v1/alarms/beep_short.ogg"></audio>""", unsafe_allow_html=True)
    st.markdown('<div class="alarm-box"><b>🚨 PERHATIAN KOMANDAN:</b> ANOMALI TARGET (ASSAULT / GHOST) TERDETEKSI! Pesan intelijen ditembakkan.</div>', unsafe_allow_html=True)

col_kiri, col_kanan = st.columns([2, 1])

with col_kiri:
    with st.container(border=True):
        st.markdown("#### 🔥 OPERASI KHUSUS (COMBO & GHOST)")
        if not df_final.empty:
            df_combo = df_final[df_final["Sinyal"] != "-"]
            if not df_combo.empty:
                st_combo = df_combo[["Ticker", "Sinyal", "Harga", "Target Profit", "Support", "Berita"]].style.format(FORMAT_ANGKA)
                st.dataframe(st_combo, hide_index=True, use_container_width=True)
            else: st.write("   _KOSONG_")
            
    with st.container(border=True):
        st.markdown("#### 🎯 RADAR PRIORITAS TUNGGAL")
        if not df_final.empty:
            boms = df_final[df_final["Is_Squeeze"]].sort_values("Sqz_Ratio").head(10)
            st.markdown("**💣 Bom Waktu (Rasio Kompresi < 1.1x):**")
            if not boms.empty:
                st.dataframe(boms[["Ticker", "Harga", "Sqz_Ratio", "Berita"]].style.format(FORMAT_ANGKA).map(lambda x: highlight_cells(x, "Sqz_Ratio"), subset=["Sqz_Ratio"]), hide_index=True, use_container_width=True)
            else: st.write("   _KOSONG_")

with col_kanan:
    with st.container(border=True):
        st.markdown("#### 🛡️ STATUS MARKAS (GUARDIAN)")
        if guardian_data:
            for g in guardian_data:
                st.metric(label=f"**{g['Ticker']}**", value=f"Rp {g['Harga']:,.0f}", delta=f"{g['PnL']:.2f}%")
                st.caption(f"Status: **{g['Status']}**")
        else: st.write("   _Gudang Senjata Kosong_")
        
    with st.container(border=True):
        st.markdown("#### 📖 JURNAL TEMPUR")
        if os.path.exists(FILE_JURNAL):
            df_jurnal = pd.read_csv(FILE_JURNAL)
            st.dataframe(df_jurnal.tail(5), hide_index=True, use_container_width=True)
            win_rate = (len(df_jurnal[df_jurnal['Status'] == 'Profit']) / len(df_jurnal)) * 100 if len(df_jurnal) > 0 else 0
            st.caption(f"**Win Rate Keseluruhan:** {win_rate:.1f}%")
        else:
            st.write("Belum ada sejarah pertempuran.")

with st.container(border=True):
    st.markdown("#### 📊 PETA TACTICAL V8.0 (DILENGKAPI VOLUME PROFILE)")
    with st.expander("Buka Peta Visual Institusi", expanded=True):
        ticker_pilihan = st.selectbox("Pilih Target Operasi:", options=["-"] + sorted(df_final["Ticker"].tolist()) if not df_final.empty else ["-"])
        if ticker_pilihan != "-":
            ticker_jk = ticker_pilihan + ".JK"
            if ticker_jk in data_all and not data_all[ticker_jk].empty:
                df_chart = data_all[ticker_jk].tail(90) # 3 bulan terakhir untuk profile
                
                # --- IDE 3: RADAR LOGISTIK PAUS (VOLUME PROFILE) ---
                fig = make_subplots(rows=1, cols=2, shared_yaxes=True, column_widths=[0.8, 0.2], horizontal_spacing=0.01)
                
                # Chart Utama (Kiri)
                fig.add_trace(go.Candlestick(x=df_chart.index, open=df_chart['Open'], high=df_chart['High'], low=df_chart['Low'], close=df_chart['Close'], name="Harga"), row=1, col=1)
                fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['Close'].rolling(20).mean(), line=dict(color='orange', width=1), name="MA20"), row=1, col=1)
                
                # Volume Profile (Kanan) - Histogram Horizontal
                fig.add_trace(go.Histogram(y=df_chart['Close'], x=df_chart['Volume'], histfunc='sum', orientation='h', name="Vol Profile", marker_color='rgba(0, 191, 255, 0.4)'), row=1, col=2)
                
                fig.update_layout(template="plotly_dark", height=500, margin=dict(l=10, r=10, t=10, b=10), xaxis_rangeslider_visible=False)
                fig.update_xaxes(title_text="Tanggal", row=1, col=1)
                fig.update_xaxes(title_text="Akumulasi Vol", row=1, col=2)
                st.plotly_chart(fig, use_container_width=True)
                st.caption("💡 *Area biru tebal di sebelah kanan menunjukkan benteng pertahanan/tumpukan modal terbesar para institusi selama 3 bulan terakhir.*")
