import pandas as pd
import os
import streamlit as st

# ==========================================
# ASUMSI: Jenderal sudah memiliki dataframe hasil teknikal
# Contoh: df_radar = pd.DataFrame(...) berisi kolom ['Ticker', 'Sinyal', 'Harga', dll]
# ==========================================

# 1. MEMBACA INTELIJEN FUNDAMENTAL
file_katalis = "katalis_aktif.csv"
if os.path.exists(file_katalis):
    # Membaca file CSV yang dibuat oleh unit ekstraktor
    df_katalis = pd.read_csv(file_katalis)
    
    # Memastikan format ticker seragam (harus ada .JK agar cocok dengan data yfinance)
    # Jika di CSV sudah ada .JK, abaikan langkah modifikasi teks ini.
    
    # 2. PERKAWINAN DATA (MERGE HYBRID)
    # Kita gabungkan data teknikal Jenderal dengan kolom 'Katalis'
    # how='left' memastikan semua saham di radar tetap tampil, 
    # meskipun tidak punya berita fundamental.
    df_final = pd.merge(df_radar, df_katalis[['Ticker', 'Katalis']], on='Ticker', how='left')
    
    # Mengisi nilai kosong (saham yang tidak ada beritanya) dengan tanda strip "-"
    df_final['Katalis'] = df_final['Katalis'].fillna('-')
    
    # Memberi lencana visual untuk saham yang punya katalis
    df_final['Katalis'] = df_final['Katalis'].apply(lambda x: f"🚨 {x}" if x != '-' else x)

else:
    # Jika file csv belum terbuat, tabel radar berjalan normal tanpa kolom katalis
    df_final = df_radar.copy()
    df_final['Katalis'] = '-'

# 3. MENAMPILKAN DI LAYAR WAR ROOM
st.subheader("🎯 RADAR TAKTIS THE COMMANDER")

# Menampilkan tabel yang sudah digabung dengan lebar penuh
st.dataframe(df_final, use_container_width=True)
