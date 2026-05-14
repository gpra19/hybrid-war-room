import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# ==========================================
# 1. PARAMETER SIMULASI
# ==========================================
MODAL_AWAL = 10_000_000
PENGALI_ATR = 1.5  # Jarak aman Trailing Stop
PERIODE_UJI = "3y" # Uji mundur data 3 tahun ke belakang

# Daftar pasukan elit yang akan diuji
TARGET_UJI = ["BBCA.JK", "BMRI.JK", "BREN.JK", "AMMN.JK", "TLKM.JK", "BRPT.JK", "PANI.JK", "ADRO.JK"]

def uji_mundur_ghost(ticker):
    print(f"⏳ Menguji {ticker}...")
    try:
        # Unduh data historis
        df = yf.Ticker(ticker).history(period=PERIODE_UJI)
        if len(df) < 100:
            return None
        
        # --- PERHITUNGAN INDIKATOR ---
        close = df['Close']
        high = df['High']
        low = df['Low']
        vol = df['Volume']
        
        # 1. VWAP 10 Hari
        tp = (high + low + close) / 3
        df['VWAP_10'] = (tp * vol).rolling(10).sum() / vol.rolling(10).sum()
        
        # 2. OBV & Max OBV 10 Hari (Mendeteksi Akumulasi Bandar)
        df['OBV'] = (np.sign(close.diff()) * vol).fillna(0).cumsum()
        df['OBV_Max_10'] = df['OBV'].shift(1).rolling(10).max()
        
        # 3. ATR 14 Hari (Untuk Trailing Stop)
        tr = pd.concat([high - low, np.abs(high - close.shift(1)), np.abs(low - close.shift(1))], axis=1).max(axis=1)
        df['ATR_14'] = tr.rolling(14).mean()
        
        # Sinyal Masuk Ghost Accumulation
        df['Ghost_Signal'] = (close < df['VWAP_10']) & (df['OBV'] > df['OBV_Max_10'])
        
        # --- MESIN SIMULASI ---
        posisi_aktif = False
        harga_beli = 0
        lembar_saham = 0
        kas = MODAL_AWAL
        titik_stop = 0
        harga_tertinggi_sejak_beli = 0
        
        rekam_jejak = []
        
        for i in range(20, len(df)):
            tgl_skrg = df.index[i].date()
            c = float(close.iloc[i])
            h = float(high.iloc[i])
            atr = float(df['ATR_14'].iloc[i])
            
            if not posisi_aktif:
                # DETEKSI SINYAL BELI
                if df['Ghost_Signal'].iloc[i]:
                    harga_beli = c
                    lembar_saham = kas // harga_beli
                    kas -= (lembar_saham * harga_beli)
                    posisi_aktif = True
                    harga_tertinggi_sejak_beli = h
                    # Set stop loss awal (2x ATR di bawah harga beli agar tidak tersapu noise)
                    titik_stop = harga_beli - (2 * atr)
                    
                    rekam_jejak.append({"Aksi": "BELI", "Tanggal": tgl_skrg, "Harga": harga_beli, "Alasan": "👻 Ghost Signal"})
                    
            else:
                # UPDATE PELINDUNG TRAILING STOP (Mengunci Laba)
                if h > harga_tertinggi_sejak_beli:
                    harga_tertinggi_sejak_beli = h
                    batas_baru = harga_tertinggi_sejak_beli - (PENGALI_ATR * atr)
                    if batas_baru > titik_stop:
                        titik_stop = batas_baru
                
                # DETEKSI SINYAL JUAL (Terkena Trailing Stop / Stop Loss)
                if c <= titik_stop:
                    harga_jual = c
                    hasil_jual = lembar_saham * harga_jual
                    kas += hasil_jual
                    
                    pnl_pct = ((harga_jual - harga_beli) / harga_beli) * 100
                    status = "✅ WIN" if pnl_pct > 0 else "❌ LOSS"
                    
                    rekam_jejak.append({"Aksi": "JUAL", "Tanggal": tgl_skrg, "Harga": harga_jual, "PnL (%)": round(pnl_pct, 2), "Status": status})
                    
                    posisi_aktif = False
                    lembar_saham = 0

        # Jual paksa di hari terakhir jika masih pegang barang (untuk hitung evaluasi akhir)
        if posisi_aktif:
            kas += (lembar_saham * float(close.iloc[-1]))
            
        return {"Ticker": ticker, "Kas Akhir": kas, "Riwayat": rekam_jejak}
    except Exception as e:
        print(f"Gagal memproses {ticker}: {e}")
        return None

# ==========================================
# 2. EKSEKUSI & LAPORAN INTELIJEN
# ==========================================
print("🚀 MEMULAI SIMULASI UJI MUNDUR (3 TAHUN TERAKHIR)...\n")

hasil_global = []
for saham in TARGET_UJI:
    hasil = uji_mundur_ghost(saham)
    if hasil and len(hasil['Riwayat']) > 0:
        kas_akhir = hasil['Kas Akhir']
        pertumbuhan = ((kas_akhir - MODAL_AWAL) / MODAL_AWAL) * 100
        
        transaksi_jual = [r for r in hasil['Riwayat'] if r['Aksi'] == 'JUAL']
        total_trade = len(transaksi_jual)
        win_trade = len([r for r in transaksi_jual if r['Status'] == '✅ WIN'])
        
        win_rate = (win_trade / total_trade) * 100 if total_trade > 0 else 0
        
        hasil_global.append({
            "Saham": saham,
            "Total Trade": total_trade,
            "Win Rate (%)": round(win_rate, 2),
            "Pertumbuhan Modal (%)": round(pertumbuhan, 2),
            "Kas Akhir": f"Rp {kas_akhir:,.0f}"
        })

print("\n🎯 Laporan Performa Ghost Accumulation (Modal Awal: Rp 10.000.000/saham)")
print("-" * 75)
df_laporan = pd.DataFrame(hasil_global)
if not df_laporan.empty:
    print(df_laporan.to_string(index=False))
else:
    print("Tidak ada sinyal tereksekusi pada periode ini.")
print("-" * 75)
