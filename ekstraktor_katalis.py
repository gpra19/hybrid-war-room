import imaplib
import email
import pandas as pd
import re
import os
from datetime import datetime
from dotenv import load_dotenv

# Memuat kredensial dari brankas .env
load_dotenv()
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASS = os.getenv("GMAIL_PASS")

KATALIS_KEYWORDS = [
    "Tender Offer", "Dividen", "Akuisisi", "Merger", 
    "RUPS", "Laba Bersih", "Buyback", "Stock Split", "Right Issue"
]

# Daftar sampel untuk pengujian (Jenderal bisa masukkan seluruh 239 ticker nanti)
DAFTAR_MONITOR = [
    "MAPI", "HEAL", "BBCA", "NISP", "HMSP", "KLBF", "SIDO", "UNTR", "ASII"
]

def bersihkan_teks(html_content):
    clean = re.compile('<.*?>')
    return re.sub(clean, ' ', html_content)

def ekstrak_katalis_dari_email():
    print("📡 Menghubungi Markas Pusat Gmail...")
    
    if not GMAIL_USER or not GMAIL_PASS:
        print("❌ Kredensial tidak ditemukan! Cek file .env Jenderal.")
        return

    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_USER, GMAIL_PASS)
        mail.select("inbox")

        print("🔍 Menyisir pesan intelijen 'Stockbit Snips'...")
        status, messages = mail.search(None, '(FROM "Stockbit" SUBJECT "Snips")')
        
        if status != 'OK' or not messages[0]:
            print("🛑 Tidak ditemukan email Stockbit Snips di kotak masuk.")
            return

        # Mengambil ID email paling baru (terakhir)
        email_ids = messages[0].split()
        latest_email_id = email_ids[-1] 
        
        status, data = mail.fetch(latest_email_id, "(RFC822)")
        raw_email = data[0][1]
        msg = email.message_from_bytes(raw_email)
        
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body += part.get_payload(decode=True).decode('utf-8', errors='ignore')
        else:
            body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')

        body = bersihkan_teks(body)
        katalis_ditemukan = []
        
        print("⚙️ Menganalisis kata sandi dan ticker...")
        for ticker in DAFTAR_MONITOR:
            # Cari ticker yang diawali $ (format standar Stockbit: $MAPI)
            if re.search(rf"\${ticker}\b", body, re.IGNORECASE):
                for kw in KATALIS_KEYWORDS:
                    if re.search(kw, body, re.IGNORECASE):
                        katalis_ditemukan.append({
                            "Ticker": f"{ticker}.JK",
                            "Katalis": kw,
                            "Status": "🚨 AKTIF",
                            "Update": datetime.now().strftime('%Y-%m-%d %H:%M')
                        })
                        break # Cukup 1 katalis per saham agar rapi
        
        if katalis_ditemukan:
            df_katalis = pd.DataFrame(katalis_ditemukan)
            df_katalis.to_csv("katalis_aktif.csv", index=False)
            print(f"✅ SUKSES! {len(katalis_ditemukan)} katalis berhasil diekstrak.")
            print("📄 File 'katalis_aktif.csv' telah diperbarui di markas lokal.")
        else:
            # Jika tidak ada katalis, buat file kosong dengan header yang benar
            df_kosong = pd.DataFrame(columns=["Ticker", "Katalis", "Status", "Update"])
            df_kosong.to_csv("katalis_aktif.csv", index=False)
            print("⚪ Surel berhasil dibaca, tapi tidak ada aksi korporasi untuk target operasi kita hari ini.")

        mail.logout()

    except imaplib.IMAP4.error:
        print("❌ GAGAL LOGIN: Pastikan email dan 16 digit App Password sudah benar tanpa spasi.")
    except Exception as e:
        print(f"❌ TERJADI KESALAHAN SISTEM: {e}")

if __name__ == "__main__":
    ekstrak_katalis_dari_email()
