import pandas as pd
from utils.wordpress import post_to_wordpress

def jadwalkan_semua_post(xlsx_path, access_token, site_url):
    """
    This function schedules all posts from an Excel file to WordPress.
    """

    try:
        df = pd.read_excel(xlsx_path)
    except Exception as e:
        return [f"❌ Gagal membaca file: {e}"]

    hasil = []

    for idx, row in df.iterrows():
        try:
            title = str(row['judul']).strip()
            content = str(row['konten_html']).strip()
            tags = str(row['tag']).strip()
            publish_date = str(row['tanggal_publish']).strip()  # Format: YYYY-MM-DD

            if not (title and content and publish_date):
                hasil.append(f"⚠️ Data tidak lengkap di baris {idx + 2}, dilewati.")
                continue

            res = post_to_wordpress(title, content, tags, publish_date, access_token, site_url)

            if res.get('success'):
                hasil.append(f"✅ Terjadwal: {title} ({res.get('status')}) → {res.get('url')}")
            else:
                # Append a helpful error message
                err = res.get('error') or 'Unknown error'
                hasil.append(f"❌ Gagal posting: {title} | Error: {err}")

                # If authentication failed, stop further attempts and inform user
                status_code = res.get('status_code')
                if status_code in (401, 403) or 'Autentikasi gagal' in str(err):
                    hasil.append("🔒 Autentikasi gagal — periksa Access Token, Client ID, dan Client Secret. Hentikan proses.")
                    return hasil
        except Exception as err:
            hasil.append(f"⚠️ Error saat memproses baris {idx + 2}: {err}")

    return hasil
