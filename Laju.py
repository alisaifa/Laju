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
    """, unsafe_allow_html=True)

# --- DATABASE CONNECTION ---
def init_gsheets():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
        client = gspread.authorize(creds)
        # Buka berdasarkan URL agar lebih akurat
        return client.open_by_url("https://docs.google.com/spreadsheets/d/1tSnjFCjfR3_j8OeQP2nzS8IUgPO6tpeV6G3p5mtJraI/edit?usp=sharing")
    except Exception as e:
        return None

# Definisi Global agar tidak NameError
sh = init_gsheets()

# --- SESSION STATE ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'theme' not in st.session_state: st.session_state.theme = "Terang"
if 'page' not in st.session_state: st.session_state.page = "Dashboard"

# --- ANIMASI LAJU ---
def show_animation():
    placeholder = st.empty()
    for i in range(0, 101, 20):
        placeholder.markdown(f"### 🚄 {' '* (i//5)} LAJU...")
        time.sleep(0.05)
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

# --- HALAMAN LOGIN ---
if not st.session_state.logged_in:
    st.title("🚄 Welcome to LAJU")
    if sh is None:
        st.error("Koneksi Google Sheets Gagal. Pastikan Email Robot sudah di-Share ke Sheets sebagai Editor!")
    else:
        with st.container():
            user_input = st.text_input("Username")
            pw_input = st.text_input("Password", type="password")
            if st.button("Login"):
                try:
                    users_sheet = sh.worksheet("User").get_all_records()
                    df_user = pd.DataFrame(users_sheet)
                    # Sesuaikan dengan nama kolom di Sheets kamu
                    match = df_user[(df_user['Nama'] == user_input) & (df_user['Password'].astype(str) == pw_input)]
                    
                    if not match.empty:
                        show_animation()
                        st.session_state.logged_in = True
                        st.session_state.user_data = match.iloc[0].to_dict()
                        st.rerun()
                    else:
                        st.error("Username/Password salah!")
                except Exception as e:
                    st.error(f"Error Membaca Data User: {e}")

# --- MENU UTAMA ---
else:
    # Sidebar
    with st.sidebar:
        st.write(f"👤 **{st.session_state.user_data['Nama']}**")
        st.write(f"📍 {st.session_state.user_data['Cabang']}")
        menu = st.radio("Menu Utama", ["Dashboard", "Data Active", "Arsip"])
        
        if st.button(f"Mode {'Terang' if st.session_state.theme == 'Gelap' else 'Gelap'}"):
            st.session_state.theme = "Gelap" if st.session_state.theme == "Terang" else "Terang"
            st.rerun()
            
        if st.button("Log Out"):
            st.session_state.logged_in = False
            st.rerun()

    if menu == "Dashboard":
        st.header("Dashboard Logistik")
        col1, col2, col3, col4 = st.columns(4)
        col1.markdown('<div class="metric-card">Total Paket<br><h2>124</h2></div>', unsafe_allow_html=True)
        col2.markdown('<div class="metric-card">Dikirim<br><h2>89</h2></div>', unsafe_allow_html=True)
        col3.markdown('<div class="metric-card">Transit<br><h2>20</h2></div>', unsafe_allow_html=True)
        col4.markdown('<div class="metric-card">Income<br><h2>Rp 2.4M</h2></div>', unsafe_allow_html=True)
        
        st.divider()
        if st.button("➕ Input Pengiriman Baru"):
            st.session_state.page = "Input"

        if st.session_state.page == "Input":
            with st.form("form_input"):
                resi = generate_resi()
                st.write(f"**No. Resi Baru:** {resi}")
                layanan = st.selectbox("Layanan", ["Express", "Cargo", "Makanan"])
                berat = st.number_input("Berat (kg)", min_value=1)
                
                if st.form_submit_button("Simpan Data"):
                    st.success(f"Data {resi} Berhasil Disimpan!")
                    st.session_state.page = "Dashboard"

    elif menu == "Data Active":
        st.subheader("📦 Data Pengiriman Aktif")
        try:
            df = pd.DataFrame(sh.worksheet("Data Active").get_all_records())
            st.dataframe(df, use_container_width=True)
        except:
            st.warning("Tab 'Data Active' tidak ditemukan atau kosong.")

