import streamlit as st
import pandas as pd
import altair as alt
import yfinance as yf

# KONSTANTA
LITER_PER_BAREL = 159
DENSITAS = 0.85
USD_TO_IDR = 16000  # kurs contoh, sesuaikan jika perlu

# Konfigurasi halaman
st.set_page_config(page_title="Analisis Minyak Mentah", page_icon="🛢️", layout="wide")

# CSS background gradient
st.markdown("""
<style>
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #74ebd5 0%, #ACB6E5 100%);
}
[data-testid="stHeader"] {
    background: rgba(0,0,0,0);
}
</style>
""", unsafe_allow_html=True)

# Judul
st.markdown("<h1 style='text-align:center; color:#2E4053;'>🛢️ Analisis Kualitas Minyak Mentah</h1>", unsafe_allow_html=True)

# Inisialisasi session_state
for key, default in {
    "logged_in": False,
    "username": "",
    "notes": "",
    "history": []
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# Ambil harga minyak realtime dari Yahoo Finance (WTI Crude Oil: CL=F)
try:
    oil_ticker = yf.Ticker("CL=F")
    oil_hist = oil_ticker.history(period="1d")
    oil_price = float(oil_hist["Close"].iloc[-1]) if not oil_hist.empty else None
except Exception:
    oil_price = None

# Sidebar login
st.sidebar.title("⚙️ Pengaturan")
st.sidebar.subheader("🔐 Login Pengguna")
username = st.sidebar.text_input("Username", value=st.session_state.username or "")
password = st.sidebar.text_input("Password", type="password")
col_login1, col_login2 = st.sidebar.columns(2)
if col_login1.button("Login"):
    if username == "admin" and password == "1234":
        st.session_state.logged_in = True
        st.session_state.username = username
        st.sidebar.success(f"Selamat datang, {username}!")
    else:
        st.sidebar.error("Username atau password salah!")
if col_login2.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.success("Anda telah logout.")

# Sidebar harga minyak realtime
st.sidebar.subheader("🛢️ Harga Minyak Realtime")
if oil_price is not None:
    st.sidebar.metric(label="WTI Crude Oil (USD/barel)", value=f"${oil_price:,.2f}")
    st.sidebar.metric(label="WTI Crude Oil (Rp/barel)", value=f"Rp {oil_price*USD_TO_IDR:,.0f}")
else:
    st.sidebar.warning("Gagal memuat harga minyak realtime. Gunakan koneksi internet dan coba lagi.")

# Sidebar catatan
st.sidebar.subheader("📝 Catatan")
notes_input = st.sidebar.text_area("Tulis catatan di sini", value=st.session_state.notes)
if st.sidebar.button("Simpan Catatan"):
    st.session_state.notes = notes_input
    st.sidebar.success("Catatan berhasil disimpan!")

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📥 Input", "📊 Analisis", "📈 Grafik", "📂 History", "📝 Catatan"])

data = []

if st.session_state.logged_in:
    # Tab Input
    with tab1:
        st.subheader("Input Data Sampel")
        jumlah = st.number_input("Masukkan jumlah sampel minyak", min_value=1, step=1)

        for i in range(jumlah):
            with st.expander(f"➕ Input Sampel ke-{i+1}", expanded=True):
                nama = st.text_input(f"Nama sampel {i+1}", key=f"nama{i}")
                api = st.number_input(f"API gravity {i+1}", min_value=0.0, max_value=100.0, step=0.1, key=f"api{i}")
                sulfur = st.number_input(f"Kadar sulfur (%) {i+1}", min_value=0.0, max_value=100.0, step=0.1, key=f"sulfur{i}")
                berat = st.number_input(f"Berat minyak (kg) {i+1}", min_value=0.0, step=0.1, key=f"berat{i}")
                tempat = st.text_input(f"Tempat pengambilan sampel {i+1}", key=f"tempat{i}")
                alamat = st.text_area(f"Alamat lokasi sampel {i+1}", key=f"alamat{i}")
                foto = st.file_uploader(f"Upload foto lokasi sampel {i+1}", type=["jpg","jpeg","png"], key=f"foto{i}")

                if nama and berat > 0:
                    # Klasifikasi API
                    if api > 31.1:
                        kategori_api = "Light"
                    elif api >= 22.3:
                        kategori_api = "Medium"
                    else:
                        kategori_api = "Heavy"

                    # Klasifikasi Sulfur
                    kategori_sulfur = "Sweet" if sulfur < 1.0 else "Sour"
                    kategori_total = f"{kategori_api} & {kategori_sulfur}"

                    # Harga per barel: realtime jika tersedia, fallback default
                    harga_barel = oil_price if oil_price is not None else 75.0

                    # Estimasi volume & nilai
                    volume_liter = berat / DENSITAS
                    volume_barel = volume_liter / LITER_PER_BAREL
                    nilai_usd = volume_barel * harga_barel
                    nilai_idr = nilai_usd * USD_TO_IDR

                    data.append({
                        "Sampel": nama,
                        "API": api,
                        "Sulfur (%)": sulfur,
                        "Berat (kg)": berat,
                        "Kategori": kategori_total,
                        "Harga/barel ($)": round(harga_barel, 2),
                        "Volume (barel)": round(volume_barel, 2),
                        "Estimasi Nilai ($)": round(nilai_usd, 2),
                        "Estimasi Nilai (Rp)": int(nilai_idr),
                        "Tempat": tempat,
                        "Alamat": alamat,
                        "Foto": foto
                    })

        # Simpan ke history
        if data and st.button("💾 Simpan ke History"):
            st.session_state.history.extend(data)
            st.success("Data sampel berhasil disimpan ke history!")

    # Tab Analisis
    with tab2:
        if data:
            st.subheader("📊 Hasil Analisis")
            df = pd.DataFrame(data).drop(columns=["Foto"])
            st.dataframe(df, use_container_width=True)

            total_usd = sum(d["Estimasi Nilai ($)"] for d in data)
            total_idr = sum(d["Estimasi Nilai (Rp)"] for d in data)
            col_a, col_b = st.columns(2)
            col_a.metric(label="💰 Total Nilai Ekonomi (USD)", value=f"${total_usd:,.2f}")
            col_b.metric(label="💰 Total Nilai Ekonomi (Rp)", value=f"Rp {total_idr:,.0f}")

            st.subheader("🖼️ Foto Lokasi Sampel")
            for d in data:
                if d["Foto"] is not None:
                    caption = f"{d['Sampel']} | {d['Tempat']} | {d['Alamat']}"
                    st.image(d["Foto"], caption=caption, use_container_width=True)

    # Tab Grafik
    with tab3:
        if data:
            st.subheader("📈 Grafik Estimasi Nilai Ekonomi per Sampel (USD)")
            chart_data_usd = pd.DataFrame(data)[["Sampel", "Estimasi Nilai ($)", "Kategori"]]
            bar_chart_usd = alt.Chart(chart_data_usd).mark_bar().encode(
                x=alt.X("Sampel", sort=None, title="Sampel"),
                y=alt.Y("Estimasi Nilai ($)", title="Nilai (USD)"),
                color=alt.Color("Kategori", scale=alt.Scale(scheme="set2")),
                tooltip=["Sampel", "Kategori", "Estimasi Nilai ($)"]
            ).properties(width=700, height=400)
            st.altair_chart(bar_chart_usd, use_container_width=True)

            st.subheader("📈 Grafik Estimasi Nilai Ekonomi per Sampel (Rupiah)")
            chart_data_idr = pd.DataFrame([
                {"Sampel": d["Sampel"], "Estimasi Nilai (Rp)": d["Estimasi Nilai (Rp)"], "Kategori": d["Kategori"]}
                for d in data
            ])
            bar_chart_idr = alt.Chart(chart_data_idr).mark_bar().encode(
                x=alt.X("Sampel", sort=None, title="Sampel"),
                y=alt.Y("Estimasi Nilai (Rp)", title="Nilai (Rp)"),
                color=alt.Color("Kategori", scale=alt.Scale(scheme="set3")),
                tooltip=["Sampel", "Kategori", "Estimasi Nilai (Rp)"]
            ).properties(width=700, height=400)
            st.altair_chart(bar_chart_idr, use_container_width=True)

    # Tab History
    with tab4:
        st.subheader("📂 History Sampel")
        if st.session_state.history:
            hist_df = pd.DataFrame(st.session_state.history).drop(columns=["Foto"])
            st.dataframe(hist_df, use_container_width=True)
            col_h1, col_h2 = st.columns(2)
            if col_h1.button("🧹 Bersihkan History"):
                st.session_state.history = []
                st.success("History dibersihkan.")
            if col_h2.button("⬇️ Download History (CSV)"):
                csv = hist_df.to_csv(index=False).encode("utf-8")
                st.download_button("Download CSV", csv, "history_sampel.csv", "text/csv")
        else:
            st.info("Belum ada data history. Simpan data dari tab Input.")

    # Tab Catatan
    with tab5:
        st.subheader("📝 Catatan yang Disimpan")
        if st.session_state.notes:
            st.info(st.session_state.notes)
        else:
            st.warning("Belum ada catatan yang disimpan.")
else:
    st.warning("🔒 Silakan login terlebih dahulu di sidebar untuk mengakses fitur aplikasi.")