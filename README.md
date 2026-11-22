# Dashboard PDRB Kabupaten Bojonegoro 2021-2025

Dashboard Streamlit untuk analisis **Pendekatan Dua Lensa** atas PDRB Kabupaten Bojonegoro menurut 17 lapangan usaha:

- **Lensa 1, struktur ekonomi**: segmentasi K-Means (Besar, Menengah, Kecil) menurut porsi terhadap PDRB.
- **Lensa 2, pertumbuhan dan risiko**: pertumbuhan rata-rata, naik-turun pertumbuhan, dan VaR 95%.
- **Peta gabungan**: tipologi dari kedua lensa.

Filter di sidebar (periode, tahun sorotan, segmen) berlaku di semua halaman dan menghitung ulang seluruh analisis.

## Menjalankan di komputer

```
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Lalu buka http://localhost:8501.

## Struktur

```
app.py              titik masuk, filter sidebar, navigasi
pages/              enam halaman
src/data.py         pembaca data (format panjang atau lebar)
src/analysis.py     K-Means, risiko, VaR, uji statistik
src/viz.py          grafik Plotly
src/ui.py           gaya dan komponen tampilan
src/pipeline.py     data, filter, dan konteks halaman
data/               berkas CSV sumber
assets/logo_bps.png logo
```

## Memperbarui data

Ganti berkas CSV di folder `data/` (atau pakai panel *Ganti berkas data* di halaman Data dan metode).
Format panjang: `Tahun; Lapangan Usaha; Kontribusi PDRB; Pertumbuhan PDRB (%)`, opsional `PDRB ADHB` dan `PDRB ADHK`.
Bila kolom ADHK ada, bagian *andil pertumbuhan* otomatis muncul.
