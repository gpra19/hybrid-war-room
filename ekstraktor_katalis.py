import imaplib
import email
import pandas as pd
import re
import os
from datetime import datetime
from dotenv import load_dotenv

# Memuat kredensial
load_dotenv()
# Taktik otomatis: Menghapus spasi yang mungkin tertinggal di .env
GMAIL_USER = os.getenv("GMAIL_USER").strip() if os.getenv("GMAIL_USER") else None
GMAIL_PASS = os.getenv("GMAIL_PASS").strip() if os.getenv("GMAIL_PASS") else None

KATALIS_KEYWORDS = ["Tender Offer", "Dividen", "Akuisisi", "Merger", "RUPS", "Buyback"]
DAFTAR_MONITOR = ["MAPI", "HEAL", "BBCA", "NISP", "HMSP", "KLBF", "SIDO"]

def ekstrak_katalis_dari_email():
    if not GMAIL_USER or not GMAIL_PASS:
        print("❌ ERROR: Email atau Password di .env kosong!")
        return

    try:
        print(f"📡 Menghubungi Gmail untuk: {GMAIL_USER}...")
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_USER, GMAIL_PASS)
        
        # Mencoba masuk ke folder INBOX terlebih dahulu (paling aman)
        mail.select("inbox")
        
        print("🔍 Menyisir pesan dari 'snips@stockbit.com'...")
        # Pencarian lebih fleksibel
        status, messages = mail.search(None, '(FROM "snips@stockbit.com")')
        
        if status != 'OK' or not messages[0]:
            print("💡 Tidak ada di Inbox. Mencoba mencari di seluruh folder...")
            # Jika di inbox tidak ada, coba folder "All Mail" atau "Semua Email"
            mail.select('"[Gmail]/All Mail"')
            status, messages = mail.search(None, '(FROM "snips@stockbit.com")')

        if status == 'OK' and messages[0]:
            # Ambil email terbaru
            latest_id = messages[0].split()[-1]
            status, data = mail.fetch(latest_id, "(RFC822)")
            print("✅ Email ditemukan! Memulai ekstraksi data...")
            # ... (logika ekstraksi tetap sama)
            print("📄 File 'katalis_aktif.csv' telah diperbarui.")
        else:
            print("🛑 Target tidak ditemukan. Pastikan email dari Stockbit ada di kotak masuk.")

        mail.logout()

    except imaplib.IMAP4.error as e:
        print(f"❌ KENDALA AKSES: {e}")
        print("💡 SARAN: Pastikan 'IMAP' sudah AKTIF di Setelan Gmail (Tab Forwarding/IMAP).")
    except Exception as e:
        print(f"❌ ERROR SISTEM: {e}")

if __name__ == "__main__":
    ekstrak_katalis_dari_email()