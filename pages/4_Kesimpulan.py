"""Kesimpulan dan pemanfaatan untuk BPS."""

import streamlit as st

from src import pipeline, ui
from src.viz import idn, pct

k = pipeline.konteks()
f, L, G = k.fitur, k.lensa2, k.hasil.get("gabungan")
urutan = k.urutan
lo, hi = k.lo, k.hi
peran = k.hasil["peran_per_tahun"]
besar = [u for u in f.index if f.loc[u, "Segmen"] == urutan[0]]
menengah_seg = urutan[1]

ui.kepala("Penutup", "Kesimpulan dan pemanfaatan",
          f"Rangkuman temuan untuk periode {k.periode_teks}. Angka di bawah dihitung dari data yang dipilih di filter.",
          angka=[
    dict(nilai=str(len(f)), label="Lapangan usaha", catatan=f"{len(k.tahun)} tahun pengamatan"),
    dict(nilai=str(len(urutan)), label="Segmen peran", catatan=f"Skor silhouette {idn(k.hasil['silhouette'], 2)}"),
    dict(nilai=str(L["risiko"]["Profil_RR"].nunique()) if L else "-", label="Profil pertumbuhan-risiko",
         catatan="Gabungan kecepatan dan kestabilan"),
    dict(nilai=pct(peran.loc[hi, urutan[0]], 1), label=f"Porsi segmen {urutan[0]}, {hi}",
         catatan=f"{pct(peran.loc[lo, urutan[0]], 1)} pada {lo}"),
])

ui.bagian("Lima kesimpulan")
s = []
b0 = besar[0]
s.append(f"<b>Struktur ekonomi bertumpu pada {b0}.</b> Porsinya {pct(k.porsi(hi)[b0])} pada {hi}. "
         f"Segmen {urutan[0]} berisi {len(besar)} lapangan usaha, sehingga perubahan pada {b0} sangat menentukan PDRB kabupaten.")
d = peran.loc[hi, menengah_seg] - peran.loc[lo, menengah_seg]
s.append(f"<b>Lapisan menengah {'menguat' if d > 0 else 'melemah'}.</b> Porsi segmen {menengah_seg} "
         f"{'naik' if d > 0 else 'turun'} {idn(abs(d))} poin persentase antara {lo} dan {hi}.")
if L:
    r = L["risiko"]
    cep = r[r["Profil_RR"] == "Tumbuh cepat, stabil"]
    s.append(f"<b>{len(cep)} lapangan usaha tumbuh cepat dan stabil:</b> {', '.join(cep.sort_values('Kontribusi_rata2', ascending=False).index)}.")
    gej = r[r["Profil_RR"] == "Tumbuh cepat, bergejolak"]
    semua_kecil = bool(len(gej)) and (gej["Segmen"] == urutan[-1]).all()
    s.append(f"<b>{len(gej)} lapangan usaha tumbuh cepat tetapi bergejolak,</b> "
             f"{'semuanya berukuran kecil; ' if semua_kecil else ''}"
             f"tertinggi {gej['Imbal_hasil'].idxmax()} ({pct(gej['Imbal_hasil'].max())} per tahun)." if len(gej)
             else "<b>Tidak ada lapangan usaha yang tumbuh cepat sekaligus bergejolak</b> pada periode ini.")
    w = r["VaR95_SDPP"].idxmin()
    s.append(f"<b>{w} menanggung risiko terbesar.</b> Pertumbuhan rata-rata {pct(r.loc[w, 'Imbal_hasil'])}, "
             f"tahun terburuk {pct(r.loc[w, 'Terburuk'])}, dan VaR 95% {pct(r.loc[w, 'VaR95_SDPP'])}.")
ui.temuan(s)

ui.bagian("Usulan pemanfaatan untuk BPS Kabupaten Bojonegoro",
          "Ini usulan penggunaan hasil analisis, bukan temuan yang diuji dari data.")
a, b = st.columns(2, gap="large")
with a:
    ui.angka("1", "Membaca struktur dengan tiga segmen", "Segmen dapat menjadi kerangka ringkas untuk narasi PDRB, "
             "sehingga pembahasan tidak harus menyebut 17 lapangan usaha satu per satu.")
    ui.angka("3", "Menyiapkan sorotan lapangan usaha tumbuh cepat dan stabil", "Daftar pada halaman Peta gabungan dapat "
             "dipakai sebagai bahan cerita tentang kekuatan ekonomi di luar penopang utama.")
with b:
    ui.angka("2", "Memberi perhatian pada lapangan usaha bergejolak", "Lapangan usaha dengan naik-turun besar "
             "layak diperiksa lebih teliti saat angka PDRB dievaluasi.")
    ui.angka("4", "Memperbarui dengan mudah", "Saat data tahun baru tersedia, cukup ganti berkas CSV di folder data. "
             "Seluruh segmen, grafik, dan tabel dihitung ulang.")

ui.bagian("Batasan yang perlu dipahami")
ui.temuan([
    "<b>Hanya lima tahun data.</b> Tiap lapangan usaha memiliki 5 pengamatan, sehingga risiko dan VaR bersifat indikatif.",
    "<b>Angka 2024 dan 2025 masih sementara.</b> Hasil dapat bergeser saat angka final terbit.",
    "<b>Segmen dibentuk dari porsi.</b> Satu penopang utama membuat segmen terbesar hanya berisi satu lapangan usaha.",
    "<b>Tidak menguji sebab-akibat.</b> Analisis ini menggambarkan pola, bukan menjelaskan penyebabnya."
    + ("" if k.hasil.get("andil") else " Andil pertumbuhan juga belum dapat dihitung karena data PDRB ADHK belum disertakan."),
])

ui.bagian("Unduh hasil")
c1, c2, c3 = st.columns(3)
with c1:
    pipeline.unduh(f, "segmentasi.csv", "Segmentasi")
if L:
    with c2:
        pipeline.unduh(L["risiko"], "pertumbuhan_risiko.csv", "Pertumbuhan dan risiko")
    if G:
        with c3:
            pipeline.unduh(G["gabung"], "tipologi_gabungan.csv", "Tipologi gabungan")
