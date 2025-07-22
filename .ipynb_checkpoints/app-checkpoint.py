import streamlit as st
import os
import uuid
from datetime import datetime
from urllib.parse import urlencode
from utils.scheduler import jadwalkan_semua_post

st.set_page_config(page_title="WordPress Scheduler", layout="wide")

st.title("🗓️ WordPress Post Scheduler")
st.markdown("Aplikasi ini memungkinkan Anda menjadwalkan semua post dari file Excel ke WordPress.com secara otomatis.")

with st.form("credentials_form"):
    st.subheader("🔐 Masukkan Data WordPress")
    col1, col2 = st.columns(2)

    with col1:
        client_id = st.text_input("Client ID", placeholder="Masukkan Client ID", key="client_id")
        client_secret = st.text_input("Client Secret", placeholder="Masukkan Client Secret", key="client_secret", type="password")
        site_url = st.text_input("Site URL (misal: mysite.wordpress.com)", key="site_url")

    with col2:
        access_token = st.text_input("Access Token (opsional, jika sudah punya)", key="access_token", type="password")
        uploaded_file = st.file_uploader("Upload File posts.xlsx", type=["xlsx"], key="file_upload")

    submitted = st.form_submit_button("🚀 Proses")

if submitted:
    if not client_id or not client_secret or not site_url:
        st.warning("❗ Harap isi semua data yang dibutuhkan (Client ID, Client Secret, dan Site URL).")
    elif not uploaded_file:
        st.warning("❗ Harap upload file posts.xlsx.")
    elif not access_token:
        # Generate OAuth URL
        st.info("🔑 Akses token belum tersedia. Gunakan tautan di bawah untuk mendapatkan kode OAuth.")
        redirect_uri = "https://web-scheduler.streamlit.app"
        state = str(uuid.uuid4())
        auth_url = f"https://public-api.wordpress.com/oauth2/authorize?" + urlencode({
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "state": state
        })

        st.markdown(f"[👉 Klik di sini untuk login dan mendapatkan kode OAuth]({auth_url})")
        auth_code = st.text_input("Tempelkan kode yang Anda dapatkan dari URL redirect setelah login", key="auth_code")

        if auth_code:
            import requests

            token_url = "https://public-api.wordpress.com/oauth2/token"
            data = {
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
                "code": auth_code,
            }

            try:
                resp = requests.post(token_url, data=data)
                token_data = resp.json()
                access_token = token_data.get("access_token")

                if access_token:
                    st.success("✅ Access token berhasil diperoleh.")
                    st.code(access_token, language="bash")

                    save_token = st.checkbox("Simpan access token sebagai .txt")
                    if save_token:
                        with open("access_token.txt", "w") as f:
                            f.write(access_token)
                        st.success("Token berhasil disimpan.")
                else:
                    st.error("Gagal mendapatkan access token.")
                    st.json(token_data)
            except Exception as e:
                st.error(f"Terjadi kesalahan saat mengambil token: {e}")
    else:
        # Jalankan penjadwalan semua post
        with st.spinner("⏳ Menjadwalkan post ke WordPress..."):
            with open("temp_posts.xlsx", "wb") as f:
                f.write(uploaded_file.read())

            hasil = jadwalkan_semua_post("temp_posts.xlsx", access_token, site_url)
            os.remove("temp_posts.xlsx")

        st.success("✅ Proses penjadwalan selesai!")
        for h in hasil:
            st.write(h)
