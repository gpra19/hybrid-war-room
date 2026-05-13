import imaplib
import email
import pandas as pd
import re
import os
from datetime import datetime
from dotenv import load_dotenv
from bs4 import BeautifulSoup

load_dotenv()
GMAIL_USER = os.getenv("GMAIL_USER").strip() if os.getenv("GMAIL_USER") else None
GMAIL_PASS = os.getenv("GMAIL_PASS").strip() if os.getenv("GMAIL_PASS") else None

# AMUNISI KATA KUNCI DIPERLUAS: Mencakup Laba, Proyek, dan Makro Sektoral
KATALIS_KEYWORDS = [
    "Tender Offer", "Dividen", "Akuisisi", "Merger", "RUPS", "Buyback",
    "Laba", "Pendapatan", "Kinerja", "Kontrak", "Ekspansi", "Right Issue",
    "Stock Split", "Proyek", "Joint Venture", "Subsidi", "Tarif"
]

def bersihkan_html(raw_html):
    """Mengelupas seluruh kode sampah HTML menjadi teks murni"""
    soup = BeautifulSoup(raw_html, "html.parser")
    return soup.get_text(separator=" ")

def ekstrak_katalis_dari_email():
    if not GMAIL_USER or not GMAIL_PASS:
        print("❌ ERROR: Email atau Password di .env kosong!")
        return

    try:
        print(f"📡 Menghubungi Gmail untuk: {GMAIL_USER}...")
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_USER, GMAIL_PASS)
        
        mail.select("inbox")
        status, messages = mail.search(None, '(FROM "snips@stockbit.com")')

        if status == 'OK' and messages[0]:
            # Selalu incar email paling akhir (terbaru)
            id_list = messages[0].split()
            latest_id = id_list[-1]
            
            status, data = mail.fetch(latest_id, "(RFC822)")
            print("✅ Email intelijen terbaru ditemukan! Memindai kode emiten ($TICKER)...")
            
            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/html":
                        body += part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    elif part.get_content_type() == "text/plain" and not body:
                        body += part.get_payload(decode=True).decode('utf-8', errors='ignore')
            else:
                body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')

            # Terapkan pengelupasan HTML
            teks_bersih = bersihkan_html(body)

            # Pecah kalimat berdasarkan titik, enter, atau tanda seru
            kalimat_list = re.split(r'[\n\.\!]', teks_bersih)
            
            hasil_katalis = []
            saham_tercatat = set()
            
            for kalimat in kalimat_list:
                katalis_ditemukan = [k for k in KATALIS_KEYWORDS if re.search(r'\b' + k + r'\b', kalimat, re.IGNORECASE)]
                
                if katalis_ditemukan:
                    # KUNCI AKURASI MUTLAK: Hanya cari 4 huruf yang diawali tanda "$" (contoh: $ASII)
                    potensi_ticker = re.findall(r'\$([A-Z]{4})\b', kalimat)
                    
                    for t in potensi_ticker:
                        if t not in saham_tercatat:
                            hasil_katalis.append({
                                "Ticker": f"{t}.JK",
                                "Katalis": ", ".join(katalis_ditemukan)
                            })
                            saham_tercatat.add(t)

            # --- LOGIKA PENYIMPANAN PINTAR (APPEND BERSIH) ---
            file_csv = 'katalis_aktif.csv'
            if os.path.exists(file_csv):
                df_lama = pd.read_csv(file_csv)
            else:
                df_lama = pd.DataFrame(columns=["Ticker", "Katalis"])

            if hasil_katalis:
                df_baru = pd.DataFrame(hasil_katalis)
                
                # Gabungkan data baru di atas data lama
                df_gabungan = pd.concat([df_baru, df_lama], ignore_index=True)
                
                # Buang duplikat berdasarkan Ticker (Hanya simpan berita yang paling baru)
                df_final = df_gabungan.drop_duplicates(subset=['Ticker'], keep='first')
                
                df_final.to_csv(file_csv, index=False)
                print(f"📄 Sukses! {len(hasil_katalis)} katalis baru diperbarui di CSV. Total database intelijen: {len(df_final)} emiten.")
            else:
                print("🛑 Tidak ada sentimen kunci yang cocok di email hari ini.")

        mail.logout()

    except Exception as e:
        print(f"❌ ERROR SISTEM: {e}")

if __name__ == "__main__":
    ekstrak_katalis_dari_email()
