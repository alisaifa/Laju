import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import time
import barcode
from barcode.writer import ImageWriter
import base64
from io import BytesIO

# --- CONFIG & THEME ---
st.set_page_config(page_title="Laju - Logistic System", layout="wide")

# Custom CSS untuk Navy, Orange, Cream & Dark Mode
def apply_theme(mode):
    if mode == "Gelap":
        bg, text, card = "#1e1e1e", "#f5f5f5", "#2d2d2d"
    else:
        bg, text, card = "#FFFDD0", "#000080", "#ffffff"
    
    st.markdown(f"""
        <style>
        .stApp {{ background-color: {bg}; color: {text}; }}
        .metric-card {{ background-color: {card}; padding: 20px; border-radius: 10px; border-left: 5px solid #FF8C00; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); }}
        .stButton>button {{ background-color: #000080; color: white; border-radius: 5px; }}
        .stButton>button:hover {{ border: 2px solid #FF8C00; }}
        </style>
    """, unsafe_content_html=True)

# --- DATABASE CONNECTION ---
def init_gsheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    # Gunakan st.secrets untuk deployment
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
    client = gspread.authorize(creds)
    return client.open_by_url("https://docs.google.com/spreadsheets/d/1tSnjFCjfR3_j8OeQP2nzS8IUgPO6tpeV6G3p5mtJraI/edit?usp=sharing")

try:
    sh = init_gsheets()
except:
    st.error("Koneksi Google Sheets Gagal. Cek st.secrets!")

# --- SESSION STATE ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'theme' not in st.session_state: st.session_state.theme = "Terang"
if 'page' not in st.session_state: st.session_state.page = "Dashboard"

# --- ANIMASI LAJU ---
def show_animation():
    placeholder = st.empty()
    for i in range(0, 101, 10):
        placeholder.markdown(f"### 🚄 {' '* (i//5)} LAJU...")
        time.sleep(0.1)
    placeholder.empty()

# --- FUNGSI HELPER ---
def generate_resi():
    return f"LAJU-{int(time.time())}"

def generate_barcode(resi):
    EAN = barcode.get_barcode_class('code128')
    data = EAN(resi, writer=ImageWriter())
    buffer = BytesIO()
    data.write(buffer)
    return base64.b64encode(buffer.getvalue()).decode()

# --- UI COMPONENTS ---
apply_theme(st.session_state.theme)

# Sidebar & Theme Toggle
with st.sidebar:
    st.image("https://via.placeholder.com/150/000080/FFFFFF?text=LAJU", width=100) # Ganti link logo kamu
    if st.button(f"Ubah ke Mode { 'Terang' if st.session_state.theme == 'Gelap' else 'Gelap' }"):
        st.session_state.theme = "Gelap" if st.session_state.theme == "Terang" else "Terang"
        st.rerun()
    
    if st.session_state.logged_in:
        st.write(f"👤 **{st.session_state.user_data['Nama']}**")
        st.write(f"📍 {st.session_state.user_data['Cabang']}")
        menu = st.radio("Menu Utama", ["Dashboard", "Data Active", "Arsip", "Keuangan"])
        if st.button("Log Out"):
            # Logika logout Gsheets rekap jam kerja bisa ditaruh di sini
            st.session_state.logged_in = False
            st.rerun()

# --- HALAMAN LOGIN ---
if not st.session_state.logged_in:
    st.title("🚄 Welcome to LAJU")
    with st.container():
        user = st.text_input("Username")
        pw = st.text_input("Password", type="password")
        if st.button("Login"):
            users_sheet = sh.worksheet("User").get_all_records()
            df_user = pd.DataFrame(users_sheet)
            match = df_user[(df_user['Nama'] == user) & (df_user['Password'].astype(str) == pw)]
            
            if not match.empty:
                show_animation()
                st.session_state.logged_in = True
                st.session_state.user_data = match.iloc[0].to_dict()
                st.success("Login Berhasil!")
                st.rerun()
            else:
                st.error("Username/Password salah!")

# --- MENU UTAMA ---
else:
    if menu == "Dashboard":
        st.header("Dashboard Logistik")
        # Metric Cards
        col1, col2, col3, col4 = st.columns(4)
        col1.markdown('<div class="metric-card">Total Paket<br><h2>124</h2></div>', unsafe_content_html=True)
        col2.markdown('<div class="metric-card">Dikirim<br><h2>89</h2></div>', unsafe_content_html=True)
        col3.markdown('<div class="metric-card">Transit<br><h2>20</h2></div>', unsafe_content_html=True)
        col4.markdown('<div class="metric-card">Income<br><h2>Rp 2.4M</h2></div>', unsafe_content_html=True)
        
        st.divider()
        c1, c2, c3 = st.columns(3)
        
        # --- INPUT PENGIRIMAN ---
        with c1:
            if st.button("➕ Input Pengiriman", use_container_width=True):
                st.session_state.page = "Input"
        
        if st.session_state.page == "Input":
            with st.form("form_input"):
                resi = generate_resi()
                st.write(f"**No. Resi:** {resi}")
                layanan = st.selectbox("Layanan", ["Express", "Cargo", "Makanan"])
                berat = st.number_input("Berat (kg)", min_value=1)
                
                # Kalkulator Garansi
                garansi_on = st.checkbox("Tambah Layanan Garansi")
                biaya_garansi = 0
                harga_barang = 0
                if garansi_on:
                    harga_barang = st.number_input("Harga Barang (Rp)", min_value=0)
                    if layanan == "Express": biaya_garansi = harga_barang * 0.005
                    elif layanan == "Cargo": biaya_garansi = harga_barang * 0.003
                    else: biaya_garansi = 5000
                    st.info(f"Biaya Garansi: Rp {biaya_garansi:,.0f}")
                
                if st.form_submit_button("Lanjutkan ke Pembayaran"):
                    st.session_state.temp_data = {
                        "resi": resi, "layanan": layanan, "berat": berat, 
                        "garansi": biaya_garansi, "harga_barang": harga_barang
                    }
                    st.session_state.page = "Pembayaran"
                    st.rerun()

        # --- HALAMAN PEMBAYARAN ---
        if st.session_state.page == "Pembayaran":
            st.subheader("💳 Modul Pembayaran")
            data = st.session_state.temp_data
            
            # Hitung Harga Dasar
            if data['layanan'] == "Express": harga_dasar = data['berat'] * 17000
            elif data['layanan'] == "Cargo": harga_dasar = data['berat'] * 4000
            else: harga_dasar = data['berat'] * 5000
            
            total_awal = harga_dasar + data['garansi']
            pilihan = st.radio("Metode Pembayaran", ["COD", "Prepaid"])
            
            biaya_admin = 0
            if pilihan == "COD":
                biaya_admin = total_awal * 0.05 if total_awal < 100000 else total_awal * 0.025
            
            total_akhir = total_awal + biaya_admin
            st.metric("Total Bayar", f"Rp {total_akhir:,.0f}")

            # Logika Tombol Sesuai Request
            if pilihan == "Prepaid":
                if 'sudah_bayar' not in st.session_state: st.session_state.sudah_bayar = False
                if st.button("Sudah Bayar"):
                    st.session_state.sudah_bayar = True
                    # Logika save ke GSheets di sini
                btn_resi = not st.session_state.sudah_bayar
            else:
                btn_resi = False # COD Langsung aktif

            if st.button("Cetak Resi", disabled=btn_resi):
                st.session_state.page = "Resi"
                st.rerun()

    # --- MENU LAINNYA (Placeholder) ---
    elif menu == "Data Active":
        st.write("Tabel Data Active dari GSheets...")
        df = pd.DataFrame(sh.worksheet("Data Active").get_all_records())
        st.dataframe(df)

# --- RESI VIEW (HTML/CSS) ---
if st.session_state.get('page') == "Resi":
    st.balloons()
    resi_id = st.session_state.temp_data['resi']
    bcode = generate_barcode(resi_id)
    
    resi_html = f"""
    <div style="border: 2px solid #000080; padding: 20px; background: white; color: black; font-family: sans-serif;">
        <h2 style="color: #FF8C00;">🚄 LAJU EXPRESS</h2>
        <hr>
        <p><b>No. Resi:</b> {resi_id}</p>
        <img src="data:image/png;base64,{bcode}" width="200">
        <p>Layanan: {st.session_state.temp_data['layanan']}</p>
        <hr>
        <button onclick="window.print()">Print Resi</button>
    </div>
    """
    st.markdown(resi_html, unsafe_content_html=True)
    if st.button("Kembali ke Dashboard"):
        st.session_state.page = "Dashboard"
        st.rerun()