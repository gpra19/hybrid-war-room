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
    "FINANCIALS": ["BBCA.JK", "BBRI.JK", "BMRI.JK", "BBNI.JK", "BRIS.JK", "MEGA.JK", "BNGA.JK", "BDMN.JK", "BBTN.JK", "BNLI.JK"],
    "ENERGY": ["BYAN.JK", "ADRO.JK", "DSSA.JK", "PTBA.JK", "MEDC.JK", "ITMG.JK", "AKRA.JK", "PGAS.JK", "ADMR.JK", "BUMI.JK"],
    "PROPERTIES": ["PANI.JK", "BSDE.JK", "CTRA.JK", "PWON.JK", "SMRA.JK", "ASRI.JK", "KIJA.JK", "APLN.JK", "JRPT.JK", "BKSL.JK"],
    "TECHNOLOGY": ["GOTO.JK", "DCII.JK", "EMTK.JK", "BUKA.JK", "BELI.JK", "WIRG.JK", "MTDL.JK", "WIFI.JK", "DMMX.JK", "EDGE.JK"],
    "CONS. NON CYCLICAL": ["ICBP.JK", "INDF.JK", "AMRT.JK", "UNVR.JK", "CPIN.JK", "MYOR.JK", "HMSP.JK", "GGRM.JK", "CMRY.JK", "JPFA.JK"],
    "CONS. CYCLICAL": ["MAPI.JK", "MAPA.JK", "ACES.JK", "SCMA.JK", "ERAA.JK", "FILM.JK", "MSIN.JK", "AUTO.JK", "HRTA.JK", "MNCN.JK"],
    "INFRASTRUCTURES": ["BREN.JK", "TLKM.JK", "ISAT.JK", "EXCL.JK", "PGEO.JK", "MTEL.JK", "TBIG.JK", "JSMR.JK", "WIKA.JK", "PTPP.JK"],
    "HEALTHCARE": ["KLBF.JK", "MIKA.JK", "SILO.JK", "HEAL.JK", "SIDO.JK", "OMED.JK", "TSPC.JK", "IRRA.JK", "SAME.JK", "KAEF.JK"],
    "BASIC MATERIALS": ["AMMN.JK", "TPIA.JK", "BRPT.JK", "MDKA.JK", "MBMA.JK", "NCKL.JK", "INCO.JK", "ANTM.JK", "INKP.JK", "SMGR.JK"],
    "INDUSTRIALS": ["ASII.JK", "UNTR.JK", "IMPC.JK", "PTRO.JK", "VKTR.JK", "AVIA.JK", "ARNA.JK", "MARK.JK", "HEXA.JK", "BNBR.JK"],
    "TRANSPORTATION": ["SMDR.JK", "TMAS.JK", "ASSA.JK", "BIRD.JK", "GIAA.JK", "ELPI.JK", "HATM.JK", "IMJS.JK", "WEHA.JK", "LAJU.JK"]
}

# ==========================================
# 2. ENGINE ANALISIS TAKTIS
# ==========================================

@st.cache_data(ttl=60)
def download_data(tickers):
    # Mengambil data 6 bulan
    return yf.download(tickers, period='6mo', group_by='ticker', progress=False)

@st.cache_data(ttl=60)
def get_ihsg_weather():
    try:
        df = yf.download("^JKSE", period='1mo', interval='1d', progress=False)
        if not df.empty:
            harga = float(df['Close'].iloc[-1])
            ma20 = float(df['Close'].tail(20).mean())
            return "🌤️ BULLISH (Banteng Mengamuk!)", harga if harga > ma20 else "🌩️ BEARISH (Hati-hati Badai Beruang!)", harga
    except: return "📡 Sinyal Terputus", 0

def unit_guardian(kode, df, porto):
    harga_skrg = float(df['Close'].iloc[-1])
    modal = float(porto['harga_beli'])
    
    if 'tanggal_beli' in porto and 'pengali_atr' in porto:
        tgl_beli = pd.to_datetime(porto['tanggal_beli']).tz_localize(df.index.tz)
        pengali = float(porto['pengali_atr'])
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr_skrg = float(tr.rolling(14).mean().iloc[-1])
        df_porto = df[df.index >= tgl_beli]
        
        if not df_porto.empty:
            pucuk = float(df_porto['High'].max())
            batas_ts = pucuk - (atr_skrg * pengali)
            if harga_skrg <= batas_ts and harga_skrg > modal:
                profit = ((harga_skrg - modal) / modal) * 100
                return f"💰 KUNCI LABA (Jebol ATR TS) | Sisa: {profit:.1f}%"
    
    if 'stop_loss_pct' in porto:
        batas_loss = modal * (1 - (porto['stop_loss_pct'] / 100))
        if harga_skrg <= batas_loss:
            loss = ((harga_skrg - modal) / modal) * 100 
            return f"🚨 EVAKUASI (SL Tembus) | Loss: {loss:.1f}%"
            
    return "✅ Aman"

def kalkulasi_unit(ticker, df, tanggal_maks_bursa, waktu_sekarang):
    try:
        df = df.dropna(subset=['Close'])
        if len(df) < 120: return None
        if df.index[-1].date() < tanggal_maks_bursa.date(): return None

        close = df['Close']
        vol = df['Volume']
        
        # Likuiditas check
        nilai_trans = (close * vol).tail(10).mean()
        if nilai_trans < BATAS_LIKUIDITAS_RP: return None

        # Unit Saboteur
        sma20 = close.rolling(20).mean()
        std20 = close.rolling(20).std()
        bw = ((sma20 + 2*std20) - (sma20 - 2*std20)) / sma20 * 100
        rasio_sqz = bw.iloc[-1] / bw.rolling(120).min().iloc[-1]
        
        # Unit Vanguard
        macd = close.ewm(span=12).mean() - close.ewm(span=26).mean()
        sig = macd.ewm(span=9).mean()
        is_cross = macd.iloc[-2] <= sig.iloc[-2] and macd.iloc[-1] > sig.iloc[-1]
        
        # Unit Scout (RSI)
        delta = close.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = -delta.clip(upper=0).rolling(14).mean()
        rsi = 100 - (100 / (1 + (gain/loss.replace(0, 1e-10))))
        
        # Unit Assassin
        jam_stabil = waktu_sekarang.time() >= datetime.strptime("09:30", "%H:%M").time()
        vol_break = jam_stabil and (vol.iloc[-1] > (vol.tail(20).mean() * 1.5)) and (close.iloc[-1] > close.iloc[-2])

        # Unit Defender (MA20 Pullback)
        ma20_val = close.tail(20).mean()
        is_defender = float(close.iloc[-1]) < (ma20_val * 0.98)

        # Unit Rogue (OBV Divergence)
        obv = (np.sign(close.diff()) * vol).fillna(0).cumsum()
        obv_max_10 = obv.iloc[-11:-1].max()
        ma10_kemarin = close.iloc[-11:-1].mean()
        is_rogue = (float(close.iloc[-1]) <= float(ma10_kemarin)) and (float(obv.iloc[-1]) > float(obv_max_10))

        return {
            "Ticker": ticker,
            "Harga": float(close.iloc[-1]),
            "RSI": round(rsi.iloc[-1], 1),
            "Sqz_Ratio": round(rasio_sqz, 2),
            "Is_Cross": is_cross,
            "Is_Squeeze": rasio_sqz <= RASIO_SQUEEZE_MAKS,
            "Is_Break": vol_break,
            "Is_Green": float(close.iloc[-1]) > float(close.iloc[-2]),
            "Is_Defender": is_defender,
            "Is_Rogue": is_rogue
        }
    except: return None

# ==========================================
# 3. INTERFACE HYBRID WAR ROOM
# ==========================================

waktu_wib = datetime.now(timezone.utc) + timedelta(hours=7)

# Intelijen Gmail (CSV)
berita_katalis = {}
if os.path.exists("katalis_aktif.csv"):
    try:
        df_kat = pd.read_csv("katalis_aktif.csv")
        berita_katalis = pd.Series(df_kat.Katalis.values, index=df_kat.Ticker).to_dict()
    except: pass

st.title("⚔️ THE COMMANDER: HYBRID WAR ROOM V4.0")
col_hdr1, col_hdr2 = st.columns([2, 1])
with col_hdr1:
    st.write(f"📅 Mode: **AUTOPILOT (Refresh 1 Menit)** | 🕒 Jam Radar: **{waktu_wib.strftime('%H:%M:%S')} WIB**")
with col_hdr2:
    status_ihsg, harga_ihsg = get_ihsg_weather()
    st.write(f"**IHSG:** {harga_ihsg:,.0f} | {status_ihsg}")

with st.spinner("Radar sedang menyapu pasar..."):
    semua_target = list(set(DAFTAR_SAHAM_INTI + list(berita_katalis.keys()) + list(PORTOFOLIO_AKTIF.keys())))
    data_all = download_data(semua_target)
    
    tanggal_maks = None
    for t in semua_target:
        try:
            if not data_all[t].empty:
                tgl_terakhir = data_all[t].index[-1]
                if tanggal_maks is None or tgl_terakhir > tanggal_maks:
                    tanggal_maks = tgl_terakhir
        except: pass
    if tanggal_maks is None: tanggal_maks = waktu_wib
    
    hasil_tempur = []
    guardian_status = []

    for t in semua_target:
        # Proses Portofolio Aktif (Guardian)
        if t in PORTOFOLIO_AKTIF and not data_all[t].empty:
            status_grd = unit_guardian(t, data_all[t], PORTOFOLIO_AKTIF[t])
            curr_harga = float(data_all[t]['Close'].iloc[-1])
            pnl = ((curr_harga - PORTOFOLIO_AKTIF[t]['harga_beli']) / PORTOFOLIO_AKTIF[t]['harga_beli']) * 100
            guardian_status.append({"Saham": t, "Harga": curr_harga, "PnL": f"{pnl:.2f}%", "Status": status_grd})

        # Proses Radar Utama
        res = kalkulasi_unit(t, data_all[t], tanggal_maks, waktu_wib)
        if res:
            res["Berita"] = f"🚨 {berita_katalis[t]}" if t in berita_katalis else "-"
            
            # Penentuan Combo / Tactical Unit
            if res["Is_Cross"] and res["Is_Break"]: res["Combo"] = "⚔️ Full Assault"
            elif res["Is_Squeeze"] and res["Is_Cross"]: res["Combo"] = "🧨 Triggered Bomb"
            elif res["RSI"] < 35 and res["Is_Cross"]: res["Combo"] = "🦅 Phoenix Rising"
            elif res["Is_Rogue"]: res["Combo"] = "🥷 Rogue (Akumulasi)"
            elif res["Is_Defender"]: res["Combo"] = "🛡️ Defender (MA20 Pullback)"
            else: res["Combo"] = "-"
            
            hasil_tempur.append(res)

df_final = pd.DataFrame(hasil_tempur)
df_guardian = pd.DataFrame(guardian_status)

# --- PANEL DASHBOARD ---
st.divider()
c_kiri, c_kanan = st.columns([3, 1])

with c_kiri:
    st.subheader("🔥 COMBO STRIKES & TACTICAL UNITS")
    if not df_final.empty:
        df_combo = df_final[df_final["Combo"] != "-"]
        if not df_combo.empty:
            st.dataframe(df_combo[["Ticker", "Combo", "Harga", "Berita"]], hide_index=True, use_container_width=True)
        else: st.info("Mencari target Combo...")
    else: st.info("Mencari target Combo...")

    st.subheader("🎯 RADAR PRIORITAS (Squeeze / Cross)")
    if not df_final.empty:
        df_pri = df_final[(df_final["Is_Squeeze"]) | (df_final["Is_Cross"])]
        if not df_pri.empty:
            st.dataframe(df_pri[["Ticker", "Harga", "Sqz_Ratio", "Berita"]].sort_values("Sqz_Ratio"), hide_index=True, use_container_width=True)
        else: st.info("Radar bersih.")

with c_kanan:
    st.subheader("🛡️ THE GUARDIAN")
    if not df_guardian.empty:
        for index, row in df_guardian.iterrows():
            st.markdown(f"**{row['Saham']}** | Rp {row['Harga']:,.0f}")
            st.markdown(f"*{row['Status']}* | PnL: {row['PnL']}")
            st.write("---")

    st.subheader("🌊 THE MAGE (Sektor)")
    if not df_final.empty:
        for sek, tickers in SEKTOR.items():
            hijau = df_final[df_final["Ticker"].isin(tickers) & df_final["Is_Green"]]
            total = len([t for t in tickers if t in df_final["Ticker"].values])
            pct = (len(hijau)/total)*100 if total > 0 else 0
            st.write(f"**{sek}**: {pct:.0f}% Hijau")
            st.progress(pct/100)

st.divider()
st.subheader("🏰 KILL ZONE (Oversold RSI < 40)")
if not df_final.empty:
    st.dataframe(df_final[df_final["RSI"] < 40].sort_values("RSI"), use_container_width=True, hide_index=True)

st.caption("⚙️ Engine The Commander V4.0 | Saham Suspend & Likuiditas < 5M Otomatis Dibuang.")
