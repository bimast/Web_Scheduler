import streamlit as st
import streamlit.components.v1 as components
import os
import uuid
from datetime import datetime
from urllib.parse import urlencode
from utils.scheduler import jadwalkan_semua_post

st.set_page_config(page_title="WordPress Scheduler", layout="wide")

st.title("🗓️ WordPress Post Scheduler")
st.markdown("Aplikasi ini memungkinkan Anda menjadwalkan semua post dari file Excel ke WordPress.com secara otomatis.")


# -- Developer app checker -------------------------------------------------
def has_developer_app():
    """Detect whether the user already has a WordPress developer app.

    Detection checks (in order):
    - Environment variables `WORDPRESS_CLIENT_ID` and `WORDPRESS_CLIENT_SECRET`
    - Presence of local files `client_id.txt` and `client_secret.txt` in project root
    """
    # Env var check
    env_id = os.environ.get("WORDPRESS_CLIENT_ID") or os.environ.get("WP_CLIENT_ID")
    env_secret = os.environ.get("WORDPRESS_CLIENT_SECRET") or os.environ.get("WP_CLIENT_SECRET")
    if env_id and env_secret:
        return True

    # File check
    if os.path.exists("client_id.txt") and os.path.exists("client_secret.txt"):
        try:
            with open("client_id.txt", "r") as f:
                cid = f.read().strip()
            with open("client_secret.txt", "r") as f:
                csec = f.read().strip()
            if cid and csec:
                return True
        except Exception:
            return False

    return False


show_main = False

# Determine whether to show the main credentials form right away.
# We prefer rendering it immediately in the same run after the user clicks
# "Saya sudah punya" to avoid requiring a second click.
if has_developer_app() or st.session_state.get("_dev_app_checked"):
    show_main = True
else:
    st.header("Sebelum mulai — Buat App Pengembang WordPress")
    st.write("Aplikasi ini membutuhkan WordPress Developer App (Client ID & Client Secret). Jika Anda belum membuatnya, silakan buat dulu.")

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("- Jika Anda sudah memiliki `Client ID` dan `Client Secret`, klik **'Saya sudah punya'** untuk melanjutkan.")
        st.markdown("- Jika belum, klik **'Buat Developer App'** untuk membuka halaman pendaftaran app WordPress.")
    with col2:
        have_clicked = st.button("Saya sudah punya")
        create_clicked = st.button("Buat Developer App")

        if have_clicked:
            st.session_state["_dev_app_checked"] = True
            show_main = True
            # Try to immediately rerun the script so the checker block is not
            # rendered in the same run. If experimental_rerun is unavailable,
            # stop the script — the next interaction will rerun.
            try:
                st.experimental_rerun()
            except Exception:
                st.stop()

        if create_clicked:
            # Open the WordPress developer app page in a new tab/window.
            components.html(
                """
                <a id="wpapp" href="https://developer.wordpress.com/apps/new" target="_blank" rel="noopener noreferrer"></a>
                <script>
                    document.getElementById('wpapp').click();
                </script>
                """,
                height=0,
            )

    # Also show the link in case redirect/JS is blocked
    st.markdown("[Buka halaman pembuatan App WordPress di browser](https://developer.wordpress.com/apps/new)")
    with st.expander("Manual: Cara membuat WordPress Developer App (langkah cepat)"):
        st.markdown("Berikut langkah cepat untuk membuat Developer App di WordPress dan mendapatkan Client ID & Client Secret:")
        st.markdown("1. Buka https://developer.wordpress.com/apps/new dan buat aplikasi baru.")
        st.markdown("2. Isi nama aplikasi, deskripsi, dan website (opsional).")
        st.markdown("3. Tambahkan Redirect URL yang diperlukan (misal: `https://web-scheduler.streamlit.app` untuk deployment, atau `http://localhost:8501` untuk pengujian lokal).")
        st.markdown("4. Simpan aplikasi lalu salin **Client ID** dan **Client Secret**.")
        st.markdown("5. Kembali ke halaman ini, klik **'Saya sudah punya'** dan masukkan Client ID/Secret pada form.")
        st.markdown("6. (Opsional) Simpan nilai ke file `client_id.txt` dan `client_secret.txt` di folder project, atau set environment variables `WORDPRESS_CLIENT_ID` / `WORDPRESS_CLIENT_SECRET`.")
        st.markdown("7. Untuk pengujian lokal, jalankan Streamlit dan gunakan redirect `http://localhost:8501` saat membuat app:")
        st.code("pip install -r requirements.txt\nstreamlit run app.py", language="bash")
        st.markdown("Jika Anda ingin panduan lengkap, lihat `README.md` di repo atau buka: https://github.com/bimast/Web_Scheduler/blob/main/README.md")

if show_main:
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
else:
    # Ensure variables used later are defined when the form isn't rendered
    submitted = False

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

        # Summarize results: count successes and failures, then show appropriate
        # top-level message. `hasil` is a list of strings where successes start
        # with '✅'. Treat anything else as a failure/warning.
        success_count = sum(1 for h in hasil if isinstance(h, str) and h.strip().startswith("✅"))
        failure_count = len(hasil) - success_count

        if success_count > 0 and failure_count == 0:
            st.success(f"✅ Semua posting berhasil: {success_count} sukses, {failure_count} gagal")
        elif success_count > 0 and failure_count > 0:
            st.warning(f"⚠️ Proses selesai dengan beberapa kegagalan: {success_count} sukses, {failure_count} gagal")
        else:
            st.error("❌ Tidak ada posting yang berhasil. Periksa pesan kesalahan di bawah.")

        # Show detailed lines. Show failures as errors/warnings and successes as normal text.
        for h in hasil:
            if not isinstance(h, str):
                st.write(h)
                continue

            text = h.strip()
            if text.startswith("✅"):
                st.write(text)
            elif text.startswith("⚠️"):
                st.warning(text)
            else:
                # covers '❌' and other messages
                st.error(text)
