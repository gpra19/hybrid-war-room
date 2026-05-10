import streamlit as st
import pandas as pd
import yfinance as yf
import os
import numpy as np

# ==========================================
# 1. PENGATURAN WAR ROOM
# ==========================================
st.set_page_config(page_title="The Commander V4.0", layout="wide", page_icon="🎯")
st.title("🎯 THE COMMANDER V4.0 - HYBRID RADAR")
st.markdown("---")

# Daftar Saham Pasukan Inti (Jenderal bisa menambahkan hingga puluhan ticker di sini)
DAFTAR_SAHAM = [
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

# ==========================================
# 2. MESIN TEKNIKAL (DATA BURSA LIVE)
# ==========================================
@st.cache_data(ttl=900) # Cache 15 menit agar tidak diblokir Yahoo Finance
def pindai_pasar(tickers):
    hasil = []
    
    # Progress bar untuk visualisasi pemindaian
    progress_text = "Radar sedang menyapu pasar..."
    my_bar = st.progress(0, text=progress_text)
    
    for i, ticker in enumerate(tickers):
        try:
            # Update progress bar
            my_bar.progress((i + 1) / len(tickers), text=f"Memindai {ticker}...")
            
            # Tarik data 6 bulan terakhir
            saham = yf.Ticker(ticker)
            df = saham.history(period="6mo")
            
            if df.empty:
                continue
                
            close = df['Close']
            
            # Perhitungan Indikator Taktis
            sma20 = close.rolling(window=20).mean()
            sma50 = close.rolling(window=50).mean()
            
            # RSI 14
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            # Bollinger Band (Deteksi Squeeze)
            std20 = close.rolling(window=20).std()
            upper_band = sma20 + (std20 * 2)
            lower_band = sma20 - (std20 * 2)
            bandwidth = (upper_band - lower_band) / sma20
            
            # Ambil data hari terakhir
            last_close = close.iloc[-1]
            last_rsi = rsi.iloc[-1]
            last_sma20 = sma20.iloc[-1]
            last_sma50 = sma50.iloc[-1]
            last_bw = bandwidth.iloc[-1]
            
            # Logika Sinyal Sederhana (Bisa disesuaikan dengan strategi Jenderal)
            sinyal = "Standby"
            if last_sma20 > last_sma50 and 40 < last_rsi < 65:
                sinyal = "🟢 Vanguard (Uptrend Awal)"
            elif last_rsi < 30:
                sinyal = "🔴 Kill Zone (Oversold)"
            elif last_bw < 0.05: # Squeeze ketat
                sinyal = "🟡 Saboteur (Squeeze Volatilitas)"
                
            hasil.append({
                "Ticker": ticker,
                "Harga Terakhir": float(last_close),
                "RSI (14)": round(last_rsi, 2),
                "Sinyal Teknikal": sinyal
            })
        except Exception as e:
            pass
            
    my_bar.empty() # Hilangkan progress bar jika selesai
    return pd.DataFrame(hasil)

# Mengeksekusi pemindaian
with st.spinner("Mengaktifkan Mesin Teknikal..."):
    df_radar = pindai_pasar(DAFTAR_SAHAM)

st.sidebar.success(f"Mesin Teknikal: Berhasil Memindai {len(df_radar)} Saham")

# ==========================================
# 3. MESIN INTELIJEN & PERKAWINAN DATA (MERGE)
# ==========================================
file_katalis = "katalis_aktif.csv"

if os.path.exists(file_katalis):
    st.sidebar.success("Mesin Intelijen: Terhubung ke Gmail")
    df_katalis = pd.read_csv(file_katalis)
    
    # Penggabungan Hybrid
    df_final = pd.merge(df_radar, df_katalis[['Ticker', 'Katalis']], on='Ticker', how='left')
    df_final['Katalis'] = df_final['Katalis'].fillna('-')
    df_final['Katalis Fundamental'] = df_final['Katalis'].apply(lambda x: f"🚨 {x}" if x != '-' else x)
    df_final = df_final.drop(columns=['Katalis']) # Buang kolom asli agar rapi
else:
    st.sidebar.warning("Mesin Intelijen: Tidak ada email katalis hari ini")
    df_final = df_radar.copy()
    df_final['Katalis Fundamental'] = '-'

# ==========================================
# 4. MENAMPILKAN KE LAYAR
# ==========================================
# Desain Tabel
st.dataframe(
    df_final, 
    use_container_width=True, 
    hide_index=True,
    column_config={
        "Harga Terakhir": st.column_config.NumberColumn(
            "Harga", format="Rp %d"
        ),
        "RSI (14)": st.column_config.NumberColumn(
            "Kekuatan RSI", format="%.2f"
        )
    }
)

# Tombol Penyegaran Manual (Jadwal otomatis diserahkan ke sistem eksternal)
if st.button("🔄 Pindai Ulang Pasar Sekarang"):
    st.cache_data.clear()
    st.rerun()

st.caption("⚙️ The Commander V4.0 | Harga ditarik dari Yahoo Finance | Sinyal Fundamental dari Ekstraktor Email")