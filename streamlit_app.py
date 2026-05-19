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

# DAFTAR KARANTINA: Saham yang dilarang operasional sementara (MSCI Deletion/Katalis Negatif)
DAFTAR_KARANTINA = [
    "BREN.JK", "AMMN.JK", "TPIA.JK", "DSSA.JK", "CUAN.JK", 
    "ANTM.JK", "BSDE.JK", "SIDO.JK", "MIKA.JK", "TKIM.JK"
]

BATAS_LIKUIDITAS_RP = 5_000_000_000 
RASIO_SQUEEZE_MAKS = 1.1
FILE_PORTOFOLIO = "portofolio_aktif.json"

# --- MODUL GUDANG SENJATA DINAMIS ---
def muat_portofolio():
    if os.path.exists(FILE_PORTOFOLIO):
        with open(FILE_PORTOFOLIO, "r") as f:
            return json.load(f)
    # Default jika belum ada file
    return {
        "BBCA.JK": {"harga_beli": 7014.67, "stop_loss_pct": 5.0, "pengali_atr": 1.5, "tanggal_beli": "2026-04-21"},
        "MAPI.JK": {"harga_beli": 1407.10, "stop_loss_pct": 1.8, "pengali_atr": 1.5, "tanggal_beli": "2026-05-08"}
    }

def simpan_portofolio(data_porto):
    with open(FILE_PORTOFOLIO, "w") as f:
        json.dump(data_porto, f, indent=4)

PORTOFOLIO_AKTIF = muat_portofolio()
# ------------------------------------

DAFTAR_SAHAM_INTI = [
    "BBCA.JK", "SSIA.JK", "DMAS.JK", "INTP.JK", "SMGR.JK", "PTPP.JK", "WTON.JK", "TLKM.JK", "ASII.JK", "GOTO.JK",
    "AMMN.JK", "BRIS.JK", "BBNI.JK", "BBRI.JK", "BMRI.JK", "BBTN.JK", "ADRO.JK", "ANTM.JK", "MDKA.JK", "PTBA.JK",
    "ITMG.JK", "UNTR.JK", "PGAS.JK", "MEDC.JK", "ELSA.JK", "AKRA.JK", "INDY.JK", "HRUM.JK", "BRPT.JK", "TPIA.JK",
    "CPIN.JK", "JPFA.JK", "ICBP.JK", "INDF.JK", "MYOR.JK", "AMRT.JK", "KLBF.JK", "SIDO.JK", "HEAL.JK", "MAPI.JK",
    "ACES.JK", "SCMA.JK", "EMTK.JK", "BUKA.JK", "ISAT.JK", "EXCL.JK", "JSMR.JK", "PGEO.JK", "CTRA.JK", "BSDE.JK",
    "BRMS.JK", "INCO.JK", "INKP.JK", "PTRO.JK", "CUAN.JK", "RAJA.JK", "BUMI.JK", "BIPI.JK", "AADI.JK", "BTPS.JK",
    "MSTI.JK", "RMKE.JK", "COAL.JK", "GTSI.JK", "HMSP.JK", "PACK.JK", "STRK.JK", "BBRM.JK", "GIAA.JK", "GMFI.JK",
    "MAHA.JK", "CBRE.JK", "MERI.JK", "HALO.JK", "IATA.JK", "TCPI.JK", "ICON.JK", "INET.JK", "IRSX.JK", "IOTF.JK",
    "AWAN.JK", "SMSM.JK", "ASPI.JK", "MUTU.JK", "NRCA.JK", "WIFI.JK", "BSBK.JK", "SMDM.JK", "RATU.JK", "TRUE.JK",
    "PNLF.JK", "LCKM.JK", "EMAS.JK", "AVIA.JK", "MDIA.JK", "DOOH.JK", "VKTR.JK", "CGAS.JK", "CDIA.JK", "KAQI.JK",
    "BJBR.JK", "BNGA.JK", "BDMN.JK", "SMRA.JK", "PWON.JK", "MIKA.JK", "SILO.JK", "PRDA.JK", "SAME.JK", "BMHS.JK",
    "TSPC.JK", "OMED.JK", "UNVR.JK", "GGRM.JK", "ERAA.JK", "MNCN.JK", "TOWR.JK", "TBIG.JK", "BIRD.JK", "ASSA.JK",
    "PBSA.JK", "MTEL.JK", "WIKA.JK", "ADHI.JK", "PNSE.JK", "BJTM.JK", "ASRI.JK", "JRPT.JK", "BKSL.JK", "APLN.JK",
    "BMTR.JK", "ENRG.JK", "MAPA.JK", "PANS.JK", "PPRO.JK", "TINS.JK", "TKIM.JK", "WOOD.JK", "PANI.JK", "SRTG.JK", 
    "RISE.JK", "CBDK.JK", "LPKR.JK", "BAPA.JK", "KIJA.JK", "LAND.JK", "RODA.JK", "DCII.JK", "BELI.JK", "LSIP.JK",
    "DMMX.JK", "EDGE.JK", "CYBR.JK", "MTDL.JK", "WIRG.JK", "DIVA.JK", "TRON.JK", "KIOS.JK", "HDIT.JK", "BYAN.JK", 
    "DSSA.JK", "ADMR.JK", "GEMS.JK", "DEWA.JK", "BULL.JK", "MBMA.JK", "NCKL.JK", "ESSA.JK", "ELPI.JK", "TMAS.JK", 
    "SMDR.JK", "HATM.JK", "IMJS.JK", "BLOG.JK", "BLTA.JK", "MITI.JK", "JAYA.JK", "WEHA.JK", "SDMU.JK", "LAJU.JK", 
    "PJHB.JK", "IMPC.JK", "BNBR.JK", "SINI.JK", "JTPE.JK", "HEXA.JK", "SKRN.JK", "ARNA.JK", "MARK.JK", "BHIT.JK", 
    "KUAS.JK", "PADA.JK", "HOPE.JK", "CTTH.JK", "KOBX.JK", "BREN.JK", "MORA.JK", "SUPR.JK", "ARKO.JK", "PPRE.JK", 
    "KETR.JK", "DATA.JK", "OASA.JK", "IRRA.JK", "SOHO.JK", "CARE.JK", "PRAY.JK", "KAEF.JK", "MEDS.JK", "RSCH.JK", 
    "MMIX.JK", "ARTO.JK", "BNLI.JK", "SMMA.JK", "CASA.JK", "MEGA.JK", "PADI.JK", "BFIN.JK", "SUPA.JK", "MSIN.JK", 
    "BUVA.JK", "FILM.JK", "MDIY.JK", "HRTA.JK", "AUTO.JK", "POLU.JK", "KOTA.JK", "MINA.JK", "ZATA.JK", "YELO.JK", 
    "KPIG.JK", "PGUN.JK", "TAPG.JK", "CMRY.JK", "WMUU.JK", "SIMP.JK", "COCO.JK", "FORE.JK", "NISP.JK", "ULTJ.JK",
    "DRMA.JK", "DEFI.JK", "PTMP.JK", "BTPN.JK"
]

SEKTOR = {
    "FINANCIALS": ["BBCA.JK", "BBRI.JK", "BMRI.JK", "BBNI.JK", "BRIS.JK", "MEGA.JK", "BNGA.JK", "BDMN.JK", "BBTN.JK", "BNLI.JK"],
    "ENERGY": ["BYAN.JK", "ADRO.JK", "DSSA.JK", "PTBA.JK", "MEDC.JK", "ITMG.JK", "AKRA.JK", "PGAS.JK", "ADMR.JK", "BUMI.JK"],
    "PROPERTIES_REAL_ESTATE": ["PANI.JK", "BSDE.JK", "CTRA.JK", "PWON.JK", "SMRA.JK", "ASRI.JK", "KIJA.JK", "APLN.JK", "JRPT.JK", "BKSL.JK"],
    "TECHNOLOGY": ["GOTO.JK", "DCII.JK", "EMTK.JK", "BUKA.JK", "BELI.JK", "WIRG.JK", "MTDL.JK", "WIFI.JK", "DMMX.JK", "EDGE.JK"],
    "CONSUMER_NON_CYCLICALS": ["ICBP.JK", "INDF.JK", "AMRT.JK", "UNVR.JK", "CPIN.JK", "MYOR.JK", "HMSP.JK", "GGRM.JK", "CMRY.JK", "JPFA.JK"],
    "CONSUMER_CYCLICALS": ["MAPI.JK", "MAPA.JK", "ACES.JK", "SCMA.JK", "ERAA.JK", "FILM.JK", "MSIN.JK", "AUTO.JK", "HRTA.JK", "MNCN.JK"],
    "INFRASTRUCTURES": ["BREN.JK", "TLKM.JK", "ISAT.JK", "EXCL.JK", "PGEO.JK", "MTEL.JK", "TBIG.JK", "JSMR.JK", "WIKA.JK", "PTPP.JK"],
    "HEALTHCARE": ["KLBF.JK", "MIKA.JK", "SILO.JK", "HEAL.JK", "SIDO.JK", "OMED.JK", "TSPC.JK", "IRRA.JK", "SAME.JK", "KAEF.JK"],
    "BASIC_MATERIALS": ["AMMN.JK", "TPIA.JK", "BRPT.JK", "MDKA.JK", "MBMA.JK", "NCKL.JK", "INCO.JK", "ANTM.JK", "INKP.JK", "SMGR.JK"],
    "INDUSTRIALS": ["ASII.JK", "UNTR.JK", "IMPC.JK", "PTRO.JK", "VKTR.JK", "AVIA.JK", "ARNA.JK", "MARK.JK", "HEXA.JK", "BNBR.JK"],
    "TRANSPORTATION_LOGISTIC": ["SMDR.JK", "TMAS.JK", "ASSA.JK", "BIRD.JK", "GIAA.JK", "ELPI.JK", "HATM.JK", "IMJS.JK", "WEHA.JK", "LAJU.JK"]
}

# ==========================================
# 2. ENGINE ANALISIS TAKTIS & RADAR TURBO
# ==========================================

@st.cache_data(ttl=180)
def download_data_turbo(tickers):
    """Mesin Asynchronous Sweeping: Mengunduh data puluhan saham serentak dalam hitungan detik."""
    hasil_data = {}
    with ThreadPoolExecutor(max_workers=20) as executor:
        future_to_ticker = {executor.submit(lambda t: yf.Ticker(t).history(period='8mo'), ticker): ticker for ticker in tickers}
        for future in as_completed(future_to_ticker):
            ticker = future_to_ticker[future]
            try:
                df = future.result()
                if not df.empty:
                    # Menyesuaikan zona waktu agar seragam
                    if df.index.tz is None:
                        df.index = df.index.tz_localize('UTC')
                    hasil_data[ticker] = df
            except Exception as e:
                pass
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
                
                # BARIS KRUSIAL PERBAIKAN BUG KUNCI LABA
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

# --- PANEL GUDANG SENJATA (DYNAMIC UI) ---
st.sidebar.markdown("### 🗄️ GUDANG SENJATA")
st.sidebar.caption("Edit, tambah, atau hapus aset yang sedang diamankan.")

df_porto = pd.DataFrame.from_dict(PORTOFOLIO_AKTIF, orient='index')
if not df_porto.empty:
    df_porto.reset_index(inplace=True)
    df_porto.rename(columns={'index': 'Ticker'}, inplace=True)
else:
    df_porto = pd.DataFrame(columns=['Ticker', 'harga_beli', 'stop_loss_pct', 'pengali_atr', 'tanggal_beli'])

edited_df = st.sidebar.data_editor(df_porto, num_rows="dynamic", use_container_width=True, hide_index=True)

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
    st.sidebar.success("Gudang senjata berhasil diperbarui!")
    st.rerun()

st.sidebar.divider()
alarm_aktif = st.sidebar.toggle("🔊 Alarm Suara", value=True)
# -----------------------------------------

berita_katalis = {}
if os.path.exists("katalis_aktif.csv"):
    try:
        df_kat = pd.read_csv("katalis_aktif.csv")
        berita_katalis = pd.Series(df_kat.Katalis.values, index=df_kat.Ticker).to_dict()
    except: pass

st.markdown("## 🎖️ THE COMMANDER V7.0")
st.caption(f"📅 **{waktu_wib.strftime('%Y-%m-%d %H:%M WIB')}** | Turbo & Dynamic UI Update")

panel_ihsg = st.empty()

with st.spinner("Menghidupkan Radar Turbo..."):
    semua_target = list(set(DAFTAR_SAHAM_INTI + list(PORTOFOLIO_AKTIF.keys())))
    if "^JKSE" not in semua_target: semua_target.append("^JKSE")
    
    # EKSEKUSI KARANTINA: Mesin otomatis membuang target yang ada di DAFTAR_HITAM maupun DAFTAR_KARANTINA
    semua_target = [t for t in semua_target if (t not in DAFTAR_HITAM and t not in DAFTAR_KARANTINA) or t == "^JKSE"]
        
    data_all = download_data_turbo(semua_target)
    
    tanggal_maks = waktu_wib
    if data_all:
        tanggal_maks = max([df.index[-1] for t, df in data_all.items() if not df.empty], default=waktu_wib)
    
    # --- PROSES DATA IHSG ---
    ihsg_val, ihsg_pct, ihsg_stat = None, None, "Menunggu Sinyal"
    if "^JKSE" in data_all and not data_all["^JKSE"].empty:
        df_ihsg = data_all["^JKSE"]
        if len(df_ihsg) >= 20:
            close_skrg = float(df_ihsg['Close'].iloc[-1])
            close_kmrn = float(df_ihsg['Close'].iloc[-2])
            ma20 = float(df_ihsg['Close'].rolling(20).mean().iloc[-1])
            ihsg_pct = ((close_skrg - close_kmrn) / close_kmrn) * 100
            ihsg_val = close_skrg
            ihsg_stat = "🐂 BULLISH - Cuaca Cerah!" if close_skrg >= ma20 else "🐻 BEARISH - Hati-hati Badai Beruang!"
            
    if ihsg_val is not None: panel_ihsg.info(f"🌩️ **RADAR IHSG:** {ihsg_val:,.0f} ({ihsg_pct:+.2f}%) | **Status Makro:** {ihsg_stat}")
    else: panel_ihsg.error("📡 **RADAR IHSG:** Data ^JKSE Kosong")
    # ------------------------

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
    st.markdown("#### 🔥 OPERASI KHUSUS (COMBO & GHOST)")
    if not df_final.empty:
        df_combo = df_final[df_final["Sinyal"] != "-"]
        if not df_combo.empty:
            st_combo = df_combo[["Ticker", "Sinyal", "Harga", "Target Profit", "Support", "Berita"]].style.format(FORMAT_ANGKA)
            st.dataframe(st_combo, hide_index=True, use_container_width=True)
        else: st.write("   _KOSONG_")
    else: st.write("   _KOSONG_")

with st.container(border=True):
    st.markdown("#### 🎯 RADAR PRIORITAS TUNGGAL")
    if not df_final.empty:
        boms = df_final[df_final["Is_Squeeze"]].sort_values("Sqz_Ratio").head(10)
        st.markdown("**💣 Bom Waktu (Rasio Kompresi < 1.1x):**")
        if not boms.empty:
            st_boms = boms[["Ticker", "Harga", "Target Profit", "Support", "Sqz_Ratio", "Berita"]].style.format(FORMAT_ANGKA).map(lambda x: highlight_cells(x, "Sqz_Ratio"), subset=["Sqz_Ratio"])
            st.dataframe(st_boms, hide_index=True, use_container_width=True)
        else: st.write("   _KOSONG_")

        vans = df_final[df_final["Is_Cross"]].head(10)
        st.markdown("**🚦 Garda Depan (Golden Cross):**")
        if not vans.empty:
            st_vans = vans[["Ticker", "Harga", "Target Profit", "Support", "Berita"]].style.format(FORMAT_ANGKA)
            st.dataframe(st_vans, hide_index=True, use_container_width=True)
        else: st.write("   _KOSONG_")

with st.container(border=True):
    st.markdown("#### 🏰 KILL ZONE (RSI Adaptif < 40)")
    if not df_final.empty:
        kz = df_final[df_final["RSI"] < 40].sort_values("RSI").head(10)
        if not kz.empty:
            st_kz = kz[["Ticker", "Harga", "Target Profit", "Support", "RSI", "Berita"]].style.format(FORMAT_ANGKA).map(lambda x: highlight_cells(x, "RSI"), subset=["RSI"])
            st.dataframe(st_kz, hide_index=True, use_container_width=True)
        else: st.write("   _KOSONG_")

with st.container(border=True):
    st.markdown("#### 🛡️ STATUS MARKAS & THE MAGE V2.0")
    st.markdown("**🔰 The Guardian (Aset Aktif):**")
    if guardian_data:
        cols = st.columns(len(guardian_data))
        for i, g in enumerate(guardian_data):
            with cols[i]:
                st.metric(label=f"**{g['Ticker']}**", value=f"Rp {g['Harga']:,.0f}", delta=f"{g['PnL']:.2f}%")
                st.caption(f"Status: **{g['Status']}**")
    else: st.write("   _Gudang Senjata Kosong_")
        
    st.markdown("**🌊 Arus Uang (Rotasi Sektor Visual):**")
    if not df_final.empty:
        mage_data = []
        for sek, tickers in SEKTOR.items():
            sektor_bersih = [t.replace('.JK', '') for t in tickers]
            df_sektor = df_final[df_final["Ticker"].isin(sektor_bersih)]
            total = len(df_sektor)
            if total > 0:
                hijau = df_sektor["Is_Green"].sum()
                pct = (hijau / total) * 100
                mage_data.append((sek, pct))
        mage_data.sort(key=lambda x: x[1], reverse=True)
        for sek, pct in mage_data:
            c1, c2 = st.columns([1, 4])
            c1.write(f"**{sek}**")
            if pct >= 50: c2.progress(pct/100, text=f"🔥 {pct:.0f}%")
            elif pct > 0: c2.progress(pct/100, text=f"❄️ {pct:.0f}%")
            else: c2.write("🧊 0%")

with st.container(border=True):
    st.markdown("#### 📊 PETA TACTICAL")
    with st.expander("Buka Peta Visual (Live Chart)"):
        ticker_pilihan = st.selectbox("Pilih Target:", options=["-"] + sorted(df_final["Ticker"].tolist()) if not df_final.empty else ["-"])
        if ticker_pilihan != "-":
            ticker_jk = ticker_pilihan + ".JK"
            if ticker_jk in data_all and not data_all[ticker_jk].empty:
                df_chart = data_all[ticker_jk].tail(60)
                fig = go.Figure(data=[go.Candlestick(x=df_chart.index, open=df_chart['Open'], high=df_chart['High'], low=df_chart['Low'], close=df_chart['Close'])])
                tp = (df_chart['High'] + df_chart['Low'] + df_chart['Close']) / 3
                vwap = (tp * df_chart['Volume']).rolling(10).sum() / df_chart['Volume'].rolling(10).sum()
                fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['Close'].rolling(20).mean(), line=dict(color='orange', width=1), name="MA20"))
                fig.add_trace(go.Scatter(x=df_chart.index, y=vwap, line=dict(color='cyan', width=1, dash='dot'), name="VWAP 10d"))
                fig.update_layout(template="plotly_dark", height=400, margin=dict(l=10, r=10, t=10, b=10), xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)
