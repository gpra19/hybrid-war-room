import streamlit as st
import pandas as pd
import os

# ==========================================
# KONFIGURASI LAYAR WAR ROOM
# ==========================================
st.set_page_config(page_title="The Commander V4.0", layout="wide", page_icon="🎯")
st.title("🎯 THE COMMANDER V4.0 - HYBRID RADAR")
st.markdown("---")

# ==========================================
# FASE 1: MESIN TEKNIKAL (DARI YAHOO FINANCE)
# ==========================================
# Nanti di sini adalah tempat Jenderal menaruh fungsi 
# unit_vanguard, unit_saboteur, dan Batch Download yfinance.
# Untuk saat ini, kita gunakan simulasi data hasil pemindaian:

st.sidebar.header("Status Operasi")
st.sidebar.success("Mesin Teknikal: Online")

data_teknikal = {
    'Ticker': ['MAPI.JK', 'HEAL.JK', 'BBCA.JK', 'NISP.JK', 'UNTR.JK'],
    'Sinyal': ['Vanguard (Golden Cross)', 'Kill Zone (Oversold)', 'Hold', 'Hold', 'Saboteur (Squeeze)'],
    'Harga Terakhir': [1450, 1200, 9800, 1350, 24000],
    'RSI': [55, 28, 60, 45, 70]
}
df_radar = pd.DataFrame(data_teknikal)

# ==========================================
# FASE 2: MESIN INTELIJEN & PERKAWINAN DATA (MERGE)
# ==========================================
file_katalis = "katalis_aktif.csv"

# Mesin mengecek apakah file CSV dari ekstraktor Gmail ada di markas
if os.path.exists(file_katalis):
    st.sidebar.success("Mesin Intelijen: Terhubung")
    
    # 1. Membaca CSV
    df_katalis = pd.read_csv(file_katalis)
    
    # 2. LOGIKA MERGE (Perkawinan Data)
    # how='left' artinya: Pertahankan semua saham di df_radar, 
    # lalu tempelkan info Katalis jika tickernya sama.
    df_final = pd.merge(df_radar, df_katalis[['Ticker', 'Katalis']], on='Ticker', how='left')
    
    # 3. Merapikan tampilan (Mengganti NaN/Kosong dengan strip)
    df_final['Katalis'] = df_final['Katalis'].fillna('-')
    
    # 4. Memberikan Lencana Sirine pada saham yang punya berita
    df_final['Katalis'] = df_final['Katalis'].apply(lambda x: f"🚨 {x}" if x != '-' else x)

else:
    st.sidebar.warning("Mesin Intelijen: Menunggu Data (CSV tidak ditemukan)")
    # Jika CSV belum ada, tabel tetap aman dan hanya menampilkan kolom kosong
    df_final = df_radar.copy()
    df_final['Katalis'] = '-'

# ==========================================
# FASE 3: MENAMPILKAN TABEL KE LAYAR PANTAU
# ==========================================
st.subheader("RADAR TAKTIS HARI INI")

# Memaksa tabel agar melebar penuh menyesuaikan ukuran layar laptop/HP
st.dataframe(df_final, use_container_width=True, hide_index=True)

st.caption("Pembaruan data teknikal diambil dari Yahoo Finance. Intelijen dikumpulkan dari Stockbit Snips.")
