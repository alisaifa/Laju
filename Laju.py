import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
import barcode
from barcode.writer import ImageWriter
import base64
from io import BytesIO

# --- CONFIG & THEME ---
st.set_page_config(page_title="Laju - Logistic System", layout="wide")

def apply_theme(mode):
    if mode == "Gelap":
        bg, text, card = "#1e1e1e", "#f5f5f5", "#2d2d2d"
    else:
        bg, text, card = "#FFFDD0", "#000080", "#ffffff"
    
    st.markdown(f"""
        <style>
        .stApp {{ background-color: {bg}; color: {text}; }}
        .metric-card {{ background-color: {card}; padding: 20px; border-radius: 10px; border-left: 5px solid #FF8C00; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); }}
        .stButton>button {{ background-color: #000080; color: white; border-radius: 5px; font-weight: bold; width: 100%; }}
        .stButton>button:hover {{ border: 2px solid #FF8C00; background-color: #000066; }}
        </style>
    """, unsafe_allow_html=True)

# --- DATABASE CONNECTION ---
def init_gsheets():
    try:
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]

        creds = ServiceAccountCredentials.from_json_keyfile_dict(
            st.secrets["gcp_service_account"], scope
        )
        client = gspread.authorize(creds)

        return client.open_by_key(https://docs.google.com/spreadsheets/d/1tSnjFCjfR3_j8OeQP2nzS8IUgPO6tpeV6G3p5mtJraI/edit?usp=sharing)
            "1tSnjFCjfR3_j80eQP2nzS8IUgP06tpeV6G3p5mtJraI"
        )

    except Exception as e:
        st.error(e)
        return None

# Definisi Global
sh = init_gsheets()

# --- SESSION STATE ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'theme' not in st.session_state: st.session_state.theme = "Terang"
if 'page' not in st.session_state: st.session_state.page = "Dashboard"

# --- HELPER FUNCTIONS ---
def generate_barcode(resi):
    COD128 = barcode.get_barcode_class('code128')
    data = COD128(resi, writer=ImageWriter())
    buffer = BytesIO()
    data.write(buffer)
    return base64.b64encode(buffer.getvalue()).decode()

apply_theme(st.session_state.theme)

# --- HALAMAN LOGIN ---
if not st.session_state.logged_in:
    st.title("🚄 Welcome to LAJU")
    
    if sh is None:
        st.error("❌ Koneksi Gagal! Pastikan email robot sudah jadi 'Editor' di Google Sheets.")
    else:
        with st.container():
            # Menggunakan kolom 'Username' sesuai gambar terbaru Abang
            user_input = st.text_input("Username")
            pw_input = st.text_input("Password", type="password")
            
            if st.button("Masuk"):
                try:
                    user_sheet = sh.worksheet("User").get_all_records()
                    df_user = pd.DataFrame(user_sheet)
                    
                    # Mencocokkan Username dan Password
                    match = df_user[(df_user['Username'] == user_input) & (df_user['Password'].astype(str) == pw_input)]
                    
                    if not match.empty:
                        st.session_state.logged_in = True
                        st.session_state.user_data = match.iloc[0].to_dict()
                        st.rerun()
                    else:
                        st.error("Username atau Password salah!")
                except Exception as e:
                    st.error(f"Error baca Sheets: {e}")

# --- DASHBOARD UTAMA ---
else:
    with st.sidebar:
        st.header("🚄 LAJU SYSTEM")
        st.write(f"Halo, **{st.session_state.user_data.get('Username')}**")
        st.write(f"Cabang: {st.session_state.user_data.get('Cabang')}")
        menu = st.radio("Navigasi", ["Dashboard", "Data Pengiriman"])
        
        if st.button("Keluar"):
            st.session_state.logged_in = False
            st.rerun()

    if menu == "Dashboard":
        st.subheader("📊 Ringkasan Bisnis")
        c1, c2, c3 = st.columns(3)
        c1.markdown('<div class="metric-card">Paket Aktif<br><h2>45</h2></div>', unsafe_allow_html=True)
        c2.markdown('<div class="metric-card">Selesai<br><h2>120</h2></div>', unsafe_allow_html=True)
        c3.markdown('<div class="metric-card">Omzet Hari Ini<br><h2>Rp 1.2jt</h2></div>', unsafe_allow_html=True)

    elif menu == "Data Pengiriman":
        st.subheader("📦 Daftar Kiriman")
        try:
            df = pd.DataFrame(sh.worksheet("Data Active").get_all_records())
            st.dataframe(df, use_container_width=True)
        except:
            st.warning("Tab 'Data Active' tidak ditemukan.")



