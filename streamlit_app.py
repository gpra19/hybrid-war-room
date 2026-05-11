import streamlit as st
import pandas as pd
import yfinance as yf
import os
import numpy as np
from datetime import datetime, timedelta, timezone
from streamlit_autorefresh import st_autorefresh
import plotly.graph_objects as go

# ==========================================
# 1. PENGATURAN MARKAS (V6.0 ADVANCED ENGINE)
# ==========================================
st.set_page_config(page_title="The Commander V6.0", layout="centered", page_icon="⚔️")

st.markdown("""
    <style>
    .alarm-box { background-color: #4a1919; padding: 10px; border-radius: 5px; border-left: 5px solid #ff4b4b; margin-bottom: 15px;}
    </style>
""", unsafe_allow_html=True)

st_autorefresh(interval=180000, key="commander_radar_ping")

DAFTAR_HITAM = ["BUMN.JK", "IHSG.JK", "LQ45.JK", "COMP.JK", "IDX.JK"]
BATAS_LIKUIDITAS_RP = 5_000_000_000 
RASIO_SQUEEZE_MAKS = 1.1

PORTOFOLIO_AKTIF = {
    "NISP.JK": {"harga_beli": 1357.03, "stop_loss_pct": 3.0, "pengali_atr": 1.5, "tanggal_beli": "2026-05-06"},
    "MAPI.JK": {"harga_beli": 1407.10, "stop_loss_pct": 1.8, "pengali_atr": 1.5, "tanggal_beli": "2026-05-08"}
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

@st.cache_data(ttl=180)
def download_data(tickers):
    return yf.download(tickers, period='8mo', group_by='ticker', progress=False)

def kalkulasi_unit(ticker, df, tanggal_maks, waktu_sekarang):
    try:
        df = df.dropna(subset=['Close'])
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

        # UNIT GHOST: Kalkulasi VWAP 10 Hari & OBV
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
    if 'tanggal_beli' in porto and 'pengali_atr' in porto:
        tgl_beli = pd.to_datetime(porto['tanggal_beli']).tz_localize(df.index.tz)
        tr = pd.concat([df['High'] - df['Low'], np.abs(df['High'] - df['Close'].shift()), np.abs(df['Low'] - df['Close'].shift())], axis=1).max(axis=1)
        df_porto = df[df.index >= tgl_beli]
        if not df_porto.empty:
            batas_ts = float(df_porto['High'].max()) - (float(tr.rolling(14).mean().iloc[-1]) * float(porto['pengali_atr']))
            if harga_skrg <= batas_ts and harga_skrg > modal: return "Kunci Laba"
    if 'stop_loss_pct' in porto and harga_skrg <= modal * (1 - (porto['stop_loss_pct'] / 100)): return "Evakuasi"
    return "Aman"

def highlight_cells(val, col):
    if col == "RSI" and val < 40: return 'background-color: #4a1919; color: white;'
    if col == "Sqz_Ratio" and val <= RASIO_SQUEEZE_MAKS: return 'background-color: #524b11; color: white;'
    return ''

FORMAT_ANGKA = {"Harga": "{:,.0f}", "Target Profit": "{:,.0f}", "Support": "{:,.0f}", "RSI": "{:.1f}", "Sqz_Ratio": "{:.2f}x"}

# ==========================================
# 3. INTERFACE BRIEFING V6.0
# ==========================================
waktu_wib = datetime.now(timezone.utc) + timedelta(hours=7)

st.sidebar.header("🎛️ KONTROL RADAR")
alarm_aktif = st.sidebar.toggle("🔊 Alarm Suara", value=True)

berita_katalis = {}
if os.path.exists("katalis_aktif.csv"):
    try:
        df_kat = pd.read_csv("katalis_aktif.csv")
        berita_katalis = pd.Series(df_kat.Katalis.values, index=df_kat.Ticker).to_dict()
    except: pass

st.markdown("## 🎖️ THE COMMANDER V6.0")
st.caption(f"📅 **{waktu_wib.strftime('%Y-%m-%d %H:%M WIB')}** | Ghost & Mage Upgrade")

with st.spinner("Mengumpulkan Intelijen (Menghitung VWAP)..."):
    semua_target = [t for t in list(set(DAFTAR_SAHAM_INTI + list(PORTOFOLIO_AKTIF.keys()))) if t not in DAFTAR_HITAM]
    data_all = download_data(semua_target)
    tanggal_maks = max([data_all[t].index[-1] for t in semua_target if not data_all[t].empty], default=waktu_wib)
    
    hasil_tempur, guardian_status, alarm_trigger = [], [], False

    for t in semua_target:
        if t in PORTOFOLIO_AKTIF and not data_all[t].empty:
            stat = unit_guardian(t, data_all[t], PORTOFOLIO_AKTIF[t])
            if stat != "Aman": guardian_status.append(f"{t.replace('.JK','')} ({stat})")

        res = kalkulasi_unit(t, data_all[t], tanggal_maks, waktu_wib)
        if res:
            res["Berita"] = f"🚨 {berita_katalis[t]}" if t in berita_katalis else "-"
            
            # Prioritas Sinyal Baru
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
    st.markdown('<div class="alarm-box"><b>🚨 PERHATIAN KOMANDAN:</b> ANOMALI TARGET (ASSAULT / GHOST) TERDETEKSI!</div>', unsafe_allow_html=True)

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
    if guardian_status: st.markdown(f"**🔰 The Guardian:** Waspada! {', '.join(guardian_status)}")
    else: st.markdown("**🔰 The Guardian:** Aman.")
        
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
        
        # Urutkan sektor dari yang terkuat ke terlemah
        mage_data.sort(key=lambda x: x[1], reverse=True)
        
        for sek, pct in mage_data:
            c1, c2 = st.columns([1, 4])
            c1.write(f"**{sek}**")
            # Tampilan Progress Bar Dinamis
            if pct >= 50:
                c2.progress(pct/100, text=f"🔥 {pct:.0f}%")
            elif pct > 0:
                c2.progress(pct/100, text=f"❄️ {pct:.0f}%")
            else:
                c2.write("🧊 0%")

with st.container(border=True):
    st.markdown("#### 📊 PETA TACTICAL")
    with st.expander("Buka Peta Visual (Live Chart)"):
        ticker_pilihan = st.selectbox("Pilih Target:", options=["-"] + sorted(df_final["Ticker"].tolist()) if not df_final.empty else ["-"])
        if ticker_pilihan != "-":
            ticker_jk = ticker_pilihan + ".JK"
            if ticker_jk in data_all and not data_all[ticker_jk].empty:
                df_chart = data_all[ticker_jk].tail(60)
                fig = go.Figure(data=[go.Candlestick(x=df_chart.index, open=df_chart['Open'], high=df_chart['High'], low=df_chart['Low'], close=df_chart['Close'])])
                # Menambahkan garis VWAP dan MA20
                tp = (df_chart['High'] + df_chart['Low'] + df_chart['Close']) / 3
                vwap = (tp * df_chart['Volume']).rolling(10).sum() / df_chart['Volume'].rolling(10).sum()
                
                fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['Close'].rolling(20).mean(), line=dict(color='orange', width=1), name="MA20"))
                fig.add_trace(go.Scatter(x=df_chart.index, y=vwap, line=dict(color='cyan', width=1, dash='dot'), name="VWAP 10d"))
                
                fig.update_layout(template="plotly_dark", height=400, margin=dict(l=10, r=10, t=10, b=10), xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)
