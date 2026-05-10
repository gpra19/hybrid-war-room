import imaplib
import email
import pandas as pd
import re
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
GMAIL_USER = os.getenv("GMAIL_USER").strip() if os.getenv("GMAIL_USER") else None
GMAIL_PASS = os.getenv("GMAIL_PASS").strip() if os.getenv("GMAIL_PASS") else None

KATALIS_KEYWORDS = ["Tender Offer", "Dividen", "Akuisisi", "Merger", "RUPS", "Buyback"]
# DAFTAR_MONITOR DIHAPUS - Radar kini membaca semua pergerakan

# Daftar kata 4 huruf yang bukan saham (agar mesin tidak terkecoh)
BUKAN_SAHAM = ["IHSG", "RUPS", "FED", "BANK", "DATA", "INFO", "NEWS"]

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
        
        if status != 'OK' or not messages[0]:
            mail.select('"[Gmail]/All Mail"')
            status, messages = mail.search(None, '(FROM "snips@stockbit.com")')

        if status == 'OK' and messages[0]:
            latest_id = messages[0].split()[-1]
            status, data = mail.fetch(latest_id, "(RFC822)")
            print("✅ Email intelijen terbaru ditemukan! Memindai seluruh kode emiten...")
            
            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() in ["text/plain", "text/html"]:
                        try:
                            body += part.get_payload(decode=True).decode('utf-8')
                        except:
                            pass
            else:
                body = msg.get_payload(decode=True).decode('utf-8')

            # Memecah email per kalimat/paragraf untuk mencari konteks berita
            kalimat_list = re.split(r'\n|\.', body)
            hasil_katalis = []
            saham_tercatat = set()
            
            for kalimat in kalimat_list:
                # Cek apakah ada kata kunci katalis di kalimat ini
                katalis_ditemukan = [k for k in KATALIS_KEYWORDS if re.search(r'\b' + k + r'\b', kalimat, re.IGNORECASE)]
                
                if katalis_ditemukan:
                    # Cari semua kata yang terdiri dari 4 huruf kapital (potensi kode saham)
                    potensi_ticker = re.findall(r'\b[A-Z]{4}\b', kalimat)
                    for t in potensi_ticker:
                        if t not in BUKAN_SAHAM and t not in saham_tercatat:
                            hasil_katalis.append({
                                "Ticker": f"{t}.JK",
                                "Katalis": ", ".join(katalis_ditemukan)
                            })
                            saham_tercatat.add(t)

            if hasil_katalis:
                df_katalis = pd.DataFrame(hasil_katalis)
            else:
                df_katalis = pd.DataFrame(columns=["Ticker", "Katalis"])
                
            df_katalis.to_csv('katalis_aktif.csv', index=False)
            print(f"📄 Sukses! {len(hasil_katalis)} saham potensial ditambahkan ke 'katalis_aktif.csv'.")
            
        else:
            print("🛑 Target email tidak ditemukan.")

        mail.logout()

    except Exception as e:
        print(f"❌ ERROR SISTEM: {e}")

if __name__ == "__main__":
    ekstrak_katalis_dari_email()
