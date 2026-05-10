import streamlit as st
import pandas as pd
import yfinance as yf
import os
import numpy as np
from datetime import datetime, timedelta, timezone

# ==========================================
# 1. KONFIGURASI PUSAT & PORTOFOLIO
# ==========================================
st.set_page_config(page_title="The Commander V4.0", layout="wide", page_icon="🎯")
st.title("🎯 THE COMMANDER V4.0 - HYBRID WAR ROOM")

BATAS_LIKUIDITAS_RP = 5_000_000_000 
RASIO_SQUEEZE_MAKS = 1.1

PORTOFOLIO_AKTIF = {
    "NISP.JK": {"harga_beli": 1357.03, "tanggal_beli": "2026-05-06", "stop_loss_pct": 3.0, "pengali_atr": 1.5},
    "MAPI.JK": {"harga_beli": 1407.10, "tanggal_beli": "2026-05-08", "stop_loss_pct": 1.8, "pengali_atr": 1.5}
}

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
    "KPIG.JK", "PGUN.JK", "TAPG.JK", "CMRY.JK", "WMUU.JK", "SIMP.JK", "COCO.JK", "FORE.JK", "NISP.JK", "ULTJ.JK"
]

SEKTOR = {
    "FINANCIALS": ["BBCA.JK", "BBRI.JK", "BMRI.JK", "BBNI.JK", "BRIS.JK"],
    "HEALTHCARE": ["KLBF.JK", "MIKA.JK", "SILO.JK", "HEAL.JK", "SIDO.JK"],
    "ENERGY": ["ADRO.JK", "ITMG.JK", "PTBA.JK", "MEDC.JK"],
    "CONSUMER_CYCLICALS": ["MAPI.JK", "MAPA.JK", "ACES.JK"]
}

# ==========================================
# 2. MESIN ANALISIS (THE COMMANDER LOGIC)
# ==========================================

@st.cache_data(ttl=300) # Cache 5 menit
def ambil_data_pasar(tickers):
    data = yf.download(tickers, period='8mo', group_by='ticker', progress=False)
    return data

def hitung_sinyal(ticker, df):
    try:
        df = df.dropna(subset=['Close'])
        if len(df) < 120: return None
        
        close = df['Close']
        # 1. Saboteur (Squeeze)
        sma20 = close.rolling(20).mean()
        std20 = close.rolling(20).std()
        bw = ((sma20 + 2*std20) - (sma20 - 2*std20)) / sma20 * 100
        bw_min_120 = bw.rolling(120).min().iloc[-1]
        rasio_sqz = bw.iloc[-1] / bw_min_120
        
        # 2. Vanguard (MACD Golden Cross)
        exp1 = close.ewm(span=12).mean()
        exp2 = close.ewm(span=26).mean()
        macd = exp1 - exp2
        sig = macd.ewm(span=9).mean()
        
        # 3. Scout (RSI)
        delta = close.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = -delta.clip(upper=0).rolling(14).mean()
        rsi = 100 - (100 / (1 + (gain/loss)))
        
        # Penentuan Sinyal
        sinyal = "Standby"
        if rasio_sqz <= RASIO_SQUEEZE_MAKS: sinyal = "🟡 Saboteur (Squeeze)"
        if macd.iloc[-2] <= sig.iloc[-2] and macd.iloc[-1] > sig.iloc[-1]: sinyal = "🟢 Vanguard (Cross)"
        if rsi.iloc[-1] < 30: sinyal = "🔴 Kill Zone (Oversold)"
        
        return {
            "Ticker": ticker,
            "Harga": float(close.iloc[-1]),
            "RSI": round(rsi.iloc[-1], 2),
            "Sinyal Teknikal": sinyal,
            "Squeeze Ratio": round(rasio_sqz, 2)
        }
    except: return None

# ==========================================
# 3. INTERFACE WAR ROOM
# ==========================================

# Sidebar - Filter & Intelijen
st.sidebar.header("📡 INTELIJEN PUSAT")
file_katalis = "katalis_aktif.csv"
berita_dict = {}
if os.path.exists(file_katalis):
    df_katalis = pd.read_csv(file_katalis)
    berita_dict = pd.Series(df_katalis.Katalis.values, index=df_katalis.Ticker).to_dict()
    st.sidebar.success(f"Ditemukan {len(berita_dict)} Berita Fundamental")

# --- PROSES DATA ---
with st.spinner("Memindai Seluruh Pasukan..."):
    tickers_to_scan = list(set(DAFTAR_SAHAM_INTI + list(berita_dict.keys())))
    raw_data = ambil_data_pasar(tickers_to_scan)
    
    hasil_list = []
    for t in tickers_to_scan:
        res = hitung_sinyal(t, raw_data[t])
        if res:
            # Gabungkan dengan Berita
            res["Katalis Fundamental"] = f"🚨 {berita_dict[t]}" if t in berita_dict else "-"
            hasil_list.append(res)

df_final = pd.DataFrame(hasil_list)

# --- TAMPILAN UTAMA ---
col1, col2 = st.columns([3, 1])

with col1:
    st.subheader("🎯 RADAR STRATEGIS")
    st.dataframe(df_final, use_container_width=True, hide_index=True)

with col2:
    st.subheader("🛡️ THE GUARDIAN")
    for ticker, info in PORTOFOLIO_AKTIF.items():
        if ticker in raw_data:
            harga_skrg = raw_data[ticker]['Close'].iloc[-1]
            profit_loss = ((harga_skrg - info['harga_beli']) / info['harga_beli']) * 100
            color = "green" if profit_loss > 0 else "red"
            st.markdown(f"**{ticker}**")
            st.markdown(f"PnL: :{color}[{profit_loss:.2f}%]")
            st.progress(max(0, min(100, int(100 + profit_loss))))

if st.button("🔄 REFRESH RADAR (REAL-TIME)"):
    st.cache_data.clear()
    st.rerun()

st.caption(f"Update Terakhir: {datetime.now().strftime('%H:%M:%S')} WIB | Sinyal Otomatis ditarik setiap kali halaman direfresh.")
