import imaplib
import email
import pandas as pd
import re
import os
from datetime import datetime
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from email.utils import parsedate_to_datetime

load_dotenv()
GMAIL_USER = os.getenv("GMAIL_USER").strip() if os.getenv("GMAIL_USER") else None
GMAIL_PASS = os.getenv("GMAIL_PASS").strip() if os.getenv("GMAIL_PASS") else None

KATALIS_KEYWORDS = [
    "Tender Offer", "Dividen", "Akuisisi", "Merger", "RUPS", "Buyback",
    "Laba", "Pendapatan", "Penjualan", "Kinerja", "Kontrak", "Ekspansi", 
    "Right", "Stock Split", "Proyek", "Joint Venture", "Kerjasama", 
    "Kemitraan", "Subsidi", "Tarif", "Volume", "Capex", "Indeks"
]

def bersihkan_html(raw_html):
    soup = BeautifulSoup(raw_html, "html.parser")
    # KUNCI PERBAIKAN: Gunakan enter (\n) sebagai pemisah blok HTML, bukan spasi!
    teks = soup.get_text(separator="\n")
    # Bersihkan enter yang berlebihan (lebih dari 2) menjadi maksimal 2 enter
    return re.sub(r'\n{3,}', '\n\n', teks)

def ekstrak_katalis_dari_email():
    if not GMAIL_USER or not GMAIL_PASS:
        print("❌ ERROR: Email atau Password di .env kosong!")
        return

    try:
        print(f"📡 Menghubungi markas Gmail...")
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_USER, GMAIL_PASS)
        mail.select("inbox")
        
        status, messages = mail.search(None, '(FROM "snips@stockbit.com")')

        if status == 'OK' and messages[0]:
            id_list = messages[0].split()
            latest_id = id_list[-1]
            
            status, data = mail.fetch(latest_id, "(RFC822)")
            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            tgl_raw = msg.get("Date")
            tgl_obj = parsedate_to_datetime(tgl_raw)
            tgl_format = tgl_obj.strftime("%Y-%m-%d")
            
            print(f"✅ Intelijen Stockbit Snips tanggal {tgl_format} ditemukan!")
            
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/html":
                        body += part.get_payload(decode=True).decode('utf-8', errors='ignore')
            else:
                body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')

            teks_bersih = bersihkan_html(body)
            
            # KUNCI PERBAIKAN 2: Pecah teks berdasarkan enter (\n) sehingga diproses PER BARIS/PARAGRAF
            kalimat_list = teks_bersih.split('\n')
            
            pangkalan_data_ticker = {}
            
            for kalimat in kalimat_list:
                # Lewati baris kosong
                if not kalimat.strip(): continue
                
                tickers_di_kalimat = re.findall(r'\$([A-Z]{4})\b', kalimat)
                katalis_di_kalimat = [k for k in KATALIS_KEYWORDS if re.search(r'\b' + k + r'\b', kalimat, re.IGNORECASE)]
                
                # Hanya pasangkan JIKA dalam SATU BARIS/PARAGRAF yang sama terdapat Ticker dan Katalis
                if tickers_di_kalimat and katalis_di_kalimat:
                    for t in tickers_di_kalimat:
                        ticker_full = f"{t}.JK"
                        if ticker_full not in pangkalan_data_ticker:
                            pangkalan_data_ticker[ticker_full] = set()
                        for k in katalis_di_kalimat:
                            pangkalan_data_ticker[ticker_full].add(k.capitalize())

            hasil_katalis = []
            for ticker, set_katalis in pangkalan_data_ticker.items():
                hasil_katalis.append({
                    "Tanggal": tgl_format,
                    "Ticker": ticker,
                    "Katalis": ", ".join(sorted(list(set_katalis)))
                })

            file_csv = 'katalis_aktif.csv'
            if os.path.exists(file_csv):
                df_lama = pd.read_csv(file_csv)
            else:
                df_lama = pd.DataFrame(columns=["Tanggal", "Ticker", "Katalis"])

            if hasil_katalis:
                df_baru = pd.DataFrame(hasil_katalis)
                # KUNCI PERBAIKAN 3: Jika Jenderal menjalankan skrip berulang kali di hari yang sama,
                # kita harus menghapus data di CSV hari tersebut agar tidak tumpang tindih.
                if not df_lama.empty:
                    df_lama = df_lama[df_lama['Tanggal'] != tgl_format]
                
                df_gabungan = pd.concat([df_baru, df_lama], ignore_index=True)
                df_final = df_gabungan.drop_duplicates(subset=['Ticker'], keep='first')
                
                df_final.to_csv(file_csv, index=False)
                print(f"📄 Sukses! {len(hasil_katalis)} emiten berhasil diekstrak dengan presisi tinggi.")
            else:
                print(f"🛑 Tidak ada sentimen yang memenuhi kriteria.")

        mail.logout()

    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    ekstrak_katalis_dari_email()
