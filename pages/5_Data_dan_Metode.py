"""Data, mutu data, dan penjelasan metode."""

import streamlit as st

from src import data as data_mod, pipeline, ui
from src.viz import idn

k = pipeline.konteks()
hm = k.hm
df = k.df

mutu = data_mod.periksa_mutu(df)
ui.kepala("Lampiran", "Data dan metode",
          "Asal data, hasil pemeriksaan mutunya, dan penjelasan singkat cara tiap angka dihitung.",
          angka=[
    dict(nilai=str(mutu["jumlah_usaha"]), label="Lapangan usaha"),
    dict(nilai=str(mutu["jumlah_tahun"]), label="Tahun", catatan=k.periode_teks),
    dict(nilai=str(mutu["baris"]), label="Baris data"),
    dict(nilai=str(mutu["nilai_kosong"] + mutu["duplikat_tahun_usaha"]), label="Nilai kosong atau ganda",
         catatan="Hasil pemeriksaan otomatis"),
])

ui.bagian("Data yang dipakai", "Satu baris = satu lapangan usaha pada satu tahun, sesuai periode yang dipilih.")
tampil = df[[c for c in ["Tahun", "Usaha_Lengkap", "Usaha", "Kontribusi", "Pertumbuhan"] if c in df.columns]].copy()
tampil = tampil.rename(columns={"Usaha_Lengkap": "Nama lengkap", "Usaha": "Nama singkat",
                                "Kontribusi": "Porsi PDRB (%)", "Pertumbuhan": "Pertumbuhan (%)"})
st.dataframe(tampil, width="stretch", hide_index=True, height=400,
             column_config={"Tahun": st.column_config.NumberColumn(format="%d")})
pipeline.unduh(tampil, "data_pdrb_terpilih.csv", "Unduh data (CSV)")

jml = mutu["jumlah_kontribusi_per_tahun"]
ui.catatan("Jumlah porsi seluruh lapangan usaha per tahun: "
           + ", ".join(f"{t}: {idn(v, 2)}%" for t, v in jml.items())
           + ". Selisih dari 100% berasal dari pembulatan sumber.")
for c in hm.catatan:
    ui.catatan(c)

with st.expander("Ganti berkas data"):
    pipeline.pengganti_berkas()

ui.bagian("Cara kerja")
with st.expander("Segmentasi dengan K-Means"):
    st.markdown(
        "1. Setiap lapangan usaha dicirikan oleh porsinya terhadap PDRB pada tiap tahun.\n"
        "2. Angka distandarkan agar semua tahun berbobot sama.\n"
        "3. K-Means (50 titik awal acak, seed 42) membagi lapangan usaha ke dalam 3 kelompok yang jaraknya ke pusat kelompok paling kecil.\n"
        "4. Kelompok diberi nama berdasarkan rata-rata porsinya: Besar, Menengah, Kecil.\n"
        "5. Hasil diperiksa dengan skor silhouette, Davies–Bouldin, dan dibandingkan dengan metode Ward."
    )
with st.expander("Pertumbuhan, risiko, dan nilai berisiko"):
    st.markdown(
        "- **Pertumbuhan rata-rata**: rata-rata pertumbuhan tahunan tiap lapangan usaha (data BPS).\n"
        "- **Risiko**: simpangan baku pertumbuhan, yaitu seberapa jauh pertumbuhan biasanya menyimpang dari rata-ratanya.\n"
        "- **VaR 95%**: batas pertumbuhan yang hanya terlewati sekitar 1 dari 20 kali. "
        "Dihitung dengan dua cara: rata-rata dikurangi 1,645 kali simpangan baku, dan simulasi historis (persentil ke-5).\n"
        "- **Profil**: *cepat atau lambat* menurut pertumbuhan di atas atau di bawah median 17 lapangan usaha; "
        "*stabil atau bergejolak* menurut risiko di bawah atau di atas median."
    )
with st.expander("Uji statistik"):
    st.markdown(
        "Perbedaan pertumbuhan antarsegmen diuji dengan Kruskal–Wallis (karena data tidak seluruhnya normal), "
        "dilanjutkan Mann–Whitney antar pasangan dengan koreksi Bonferroni. "
        "Hubungan porsi dan pertumbuhan diukur dengan korelasi Spearman."
    )
with st.expander("Istilah"):
    st.markdown(
        "- **PDRB**: Produk Domestik Regional Bruto, nilai tambah seluruh kegiatan ekonomi di kabupaten.\n"
        "- **Lapangan usaha**: kelompok kegiatan ekonomi, misalnya Pertanian atau Konstruksi.\n"
        "- **Porsi (kontribusi)**: bagian suatu lapangan usaha dari PDRB total, dalam persen.\n"
        "- **Poin persentase**: selisih dua angka persen, misalnya 50% ke 45% = turun 5 poin."
    )
