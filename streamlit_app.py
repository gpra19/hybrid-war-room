import imaplib
import email
import pandas as pd
import re
import os
from datetime import datetime

# ==========================================
# 1. KONFIGURASI INTELIJEN (GMAIL)
# ==========================================
# Disarankan menggunakan Environment Variables untuk keamanan
GMAIL_USER = os.environ.get("GMAIL_USER")
GMAIL_PASS = os.environ.get("GMAIL_PASS") # Gunakan "App Password" jika 2FA aktif

# Kata kunci yang akan dicari sebagai katalis
KATALIS_KEYWORDS = [
    "Tender Offer", "Dividen", "Akuisisi", "Merger", 
    "RUPS", "Laporan Keuangan", "Laba Bersih", "Buyback", "Stock Split"
]

# Daftar Saham Utama (Singkatan tanpa .JK untuk pencocokan teks email)
DAFTAR_MONITOR = [
    "BBCA", "SSIA", "DMAS", "INTP", "SMGR", "PTPP", "WTON", "TLKM", "ASII", "GOTO",
    "AMMN", "BRIS", "BBNI", "BBRI", "BMRI", "BBTN", "ADRO", "ANTM", "MDKA", "PTBA",
    "MAPI", "NISP", "HEAL", "KLBF", "SIDO", "HMSP" # Tambahkan ticker lainnya di sini
]

def bersihkan_teks(html_content):
    """Menghapus tag HTML agar teks bersih mudah dibaca mesin."""
    clean = re.compile('<.*?>')
    return re.sub(clean, '', html_content)

def ekstrak_katalis_dari_email():
    print("📡 Unit Ekstraktor: Menghubungi Server Gmail...")
    try:
        # Koneksi ke Server imap
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_USER, GMAIL_PASS)
        mail.select("inbox")

        # Mencari email dari Stockbit dengan subjek Snips
        # Jenderal bisa menyesuaikan filter pencarian di sini
        status, messages = mail.search(None, '(FROM "Stockbit" SUBJECT "Snips")')
        
        if status != 'OK' or not messages[0]:
            print("🛑 Tidak ditemukan email Stockbit Snips terbaru.")
            return

        # Ambil ID email terbaru
        latest_email_id = messages[0].split()[-1]
        status, data = mail.fetch(latest_email_id, "(RFC822)")
        
        raw_email = data[0][1]
        msg = email.message_from_bytes(raw_email)
        
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode()
        else:
            body = msg.get_payload(decode=True).decode()

        body = bersihkan_teks(body)
        
        katalis_ditemukan = []
        
        # Pemindaian Ticker dan Katalis
        for ticker in DAFTAR_MONITOR:
            # Mencari Ticker (biasanya diawali $ atau spasi di Stockbit)
            if re.search(rf"(\$|\s){ticker}(\s|\.|\,)", body, re.IGNORECASE):
                # Jika ticker ditemukan, cari kalimat di sekitarnya untuk mencari kata kunci
                for kw in KATALIS_KEYWORDS:
                    if re.search(kw, body, re.IGNORECASE):
                        katalis_ditemukan.append({
                            "Ticker": f"{ticker}.JK",
                            "Katalis": kw,
                            "Detail": f"Terdeteksi di Snips {datetime.now().strftime('%d %b')}",
                            "Update_Terakhir": datetime.now().strftime('%Y-%m-%d %H:%M')
                        })
                        break # Satu ticker satu katalis utama untuk efisiensi
        
        if katalis_ditemukan:
            df_katalis = pd.DataFrame(katalis_ditemukan)
            df_katalis.to_csv("katalis_aktif.csv", index=False)
            print(f"✅ Berhasil mengekstrak {len(katalis_ditemukan)} katalis ke database.")
        else:
            print("⚪ Tidak ada katalis relevan untuk daftar saham Jenderal hari ini.")

        mail.logout()

    except Exception as e:
        print(f"❌ Kegagalan Operasi Ekstraksi: {e}")

if __name__ == "__main__":
    ekstrak_katalis_dari_email()
