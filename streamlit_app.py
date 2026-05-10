import streamlit as st
import pandas as pd
import yfinance as yf
import os
import numpy as np
from datetime import datetime, timedelta, timezone
from streamlit_autorefresh import st_autorefresh

# ==========================================
# 1. PENGATURAN MARKAS & AUTOPILOT
# ==========================================
st.set_page_config(page_title="Hybrid War Room V4.0", layout="wide", page_icon="⚔️")

# KONFIGURASI AUTOPILOT: Segarkan layar setiap 60.000 milidetik (1 Menit)
st_autorefresh(interval=60000, key="commander_radar_ping")

BATAS_LIKUIDITAS_RP = 5_000_000_000 
RASIO_SQUEEZE_MAKS = 1.1

# Pasukan Inti Jenderal
DAFTAR_SAHAM_INTI = [
    "BBCA.JK", "SSIA.JK", "DMAS.JK", "INTP.JK", "SMGR.JK", "PTPP.JK", "WTON.JK", "TLKM.JK", "ASII.JK", "GOTO.JK",
    "AMMN.JK", "BRIS.JK", "BBNI.JK", "BBRI.JK", "BMRI.JK", "BBTN.JK", "ADRO.JK", "ANTM.JK", "MDKA.JK", "PTBA.JK",
    "ITMG.JK", "UNTR.JK", "PGAS.JK", "MEDC.JK", "ELSA.JK", "AKRA.JK", "INDY.JK", "HRUM.JK", "BRPT.JK", "TPIA.JK",
    "CPIN.JK", "JPFA.JK", "ICBP.JK", "INDF.JK", "MYOR.JK", "AMRT.JK", "KLBF.JK", "SIDO.JK", "HEAL.JK", "MAPI.JK",
    "ACES.JK", "SCMA.JK", "EMTK.JK", "BUKA.JK", "ISAT.JK", "EXCL.JK", "JSMR.JK", "PGEO.JK", "CTRA.JK", "BSDE.JK",
    "BRMS.JK", "INCO.JK", "INKP.JK", "PTRO.JK", "CUAN.JK", "RAJA.JK", "BUMI.JK", "BIPI.JK", "AADI.JK", "BTPS.JK",
    "MSTI.JK", "RMKE.JK", "COAL.JK", "GTSI.JK", "HMSP.JK", "PACK.JK", "STRK.JK", "BBRM.JK", "GIAA.JK", "GMFI.JK",
    "MAHA.JK", "CBRE.JK", "MERI.JK", "HALO.JK", "IATA.JK", "TCPI.JK", "ICON.JK", "INET.JK", "IRSX.JK", "IOTF.JK",
    "AWAN.JK", "PTMP.JK", "ASPI.JK", "MUTU.JK", "NRCA.JK", "WIFI.JK", "BSBK.JK", "SMDM.JK", "RATU.JK", "TRUE.JK",
    "DEFI.JK", "LCKM.JK", "EMAS.JK", "AVIA.JK", "MDIA.JK", "DOOH.JK", "VKTR.JK", "CGAS.JK", "CDIA.JK", "KAQI.JK",
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
# 2. ENGINE ANALISIS (THE COMMANDER ENGINE)
# ==========================================

# TTL diatur 60 detik agar sinkron dengan auto-refresh
@st.cache_data(ttl=60)
def download_data(tickers):
    return yf.download(tickers, period='8mo', group_by='ticker', progress=False)

def kalkulasi_unit(ticker, df):
    try:
        df = df.dropna(subset=['Close'])
        if len(df) < 120: return None
        close = df['Close']
        vol = df['Volume']
        
        # Likuiditas check
        nilai_trans = (close * vol).tail(10).mean()
        if nilai_trans < BATAS_LIKUIDITAS_RP: return None

        # 1. Saboteur (Squeeze)
        sma20 = close.rolling(20).mean()
        std20 = close.rolling(20).std()
        bw = ((sma20 + 2*std20) - (sma20 - 2*std20)) / sma20 * 100
        bw_min_120 = bw.rolling(120).min().iloc[-1]
        rasio_sqz = bw.iloc[-1] / bw_min_120
        
        # 2. Vanguard (MACD Cross)
        exp1 = close.ewm(span=12).mean()
        exp2 = close.ewm(span=26).mean()
        macd = exp1 - exp2
        sig = macd.ewm(span=9).mean()
        
        # 3. Scout (RSI)
        delta = close.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = -delta.clip(upper=0).rolling(14).mean()
        rsi = 100 - (100 / (1 + (gain/loss.replace(0, 1e-10))))
        
        # 4. Assassin (Volume Breakout)
        vol_break = vol.iloc[-1] > (vol.tail(20).mean() * 1.5) and close.iloc[-1] > close.iloc[-2]

        return {
            "Ticker": ticker,
            "Harga": close.iloc[-1],
            "RSI": round(rsi.iloc[-1], 1),
            "Sqz_Ratio": round(rasio_sqz, 2),
            "Is_Cross": macd.iloc[-2] <= sig.iloc[-2] and macd.iloc[-1] > sig.iloc[-1],
            "Is_Squeeze": rasio_sqz <= RASIO_SQUEEZE_MAKS,
            "Is_Break": vol_break,
            "Is_Green": close.iloc[-1] > close.iloc[-2]
        }
    except: return None

# ==========================================
# 3. INTERFACE WAR ROOM
# ==========================================

# Membaca Intelijen Gmail (CSV)
berita_katalis = {}
if os.path.exists("katalis_aktif.csv"):
    try:
        df_kat = pd.read_csv("katalis_aktif.csv")
        berita_katalis = pd.Series(df_kat.Katalis.values, index=df_kat.Ticker).to_dict()
    except: pass

# Header War Room
st.title("⚔️ THE COMMANDER: HYBRID WAR ROOM")
waktu_wib = (datetime.now(timezone.utc) + timedelta(hours=7)).strftime('%H:%M:%S')
st.write(f"📅 Mode: **AUTOPILOT (Refresh 1 Menit)** | 🕒 Jam Radar: **{waktu_wib} WIB**")

# Progress Pemindaian
with st.spinner("Radar sedang menyapu pasar..."):
    semua_target = list(set(DAFTAR_SAHAM_INTI + list(berita_katalis.keys())))
    data_all = download_data(semua_target)
    
    hasil_tempur = []
    for t in semua_target:
        res = kalkulasi_unit(t, data_all[t])
        if res:
            res["Berita"] = f"🚨 {berita_katalis[t]}" if t in berita_katalis else "-"
            # Penentuan Combo (Sesuai Referensi Jenderal)
            if res["Is_Cross"] and res["Is_Break"]: res["Combo"] = "⚔️ Full Assault"
            elif res["Is_Squeeze"] and res["Is_Cross"]: res["Combo"] = "🧨 Triggered Bomb"
            elif res["RSI"] < 35 and res["Is_Cross"]: res["Combo"] = "🦅 Phoenix Rising"
            else: res["Combo"] = "-"
            hasil_tempur.append(res)

df_final = pd.DataFrame(hasil_tempur)

# --- PANEL DASHBOARD ---
st.divider()
c1, c2, c3 = st.columns(3)

with c1:
    st.subheader("🔥 COMBO STRIKES")
    df_combo = df_final[df_final["Combo"] != "-"]
    if not df_combo.empty:
        st.dataframe(df_combo[["Ticker", "Combo", "Berita"]], hide_index=True, use_container_width=True)
    else: st.info("Mencari target Combo...")

with c2:
    st.subheader("🎯 RADAR PRIORITAS")
    df_pri = df_final[(df_final["Is_Squeeze"]) | (df_final["Is_Cross"])]
    if not df_pri.empty:
        st.dataframe(df_pri[["Ticker", "Harga", "Sqz_Ratio", "Berita"]].sort_values("Sqz_Ratio"), hide_index=True, use_container_width=True)
    else: st.info("Radar bersih.")

with c3:
    st.subheader("🌊 THE MAGE (Sektor)")
    for sek, tickers in SEKTOR.items():
        hijau = df_final[df_final["Ticker"].isin(tickers) & df_final["Is_Green"]]
        total = len(tickers)
        pct = (len(hijau)/total)*100 if total > 0 else 0
        st.write(f"**{sek}**: {pct:.0f}% Hijau")
        st.progress(pct/100)

st.divider()
st.subheader("🏰 KILL ZONE (Oversold RSI)")
st.dataframe(df_final[df_final["RSI"] < 40].sort_values("RSI"), use_container_width=True, hide_index=True)

st.caption("⚙️ Sistem berjalan otomatis. Setiap perubahan harga di bursa akan langsung terdeteksi pada siklus menit berikutnya.")
