"""Lensa 1: segmentasi lapangan usaha menurut peran terhadap PDRB."""

import pandas as pd
import streamlit as st

from src import pipeline, ui, viz
from src.viz import idn, pct

k = pipeline.konteks()
f, h = k.fitur, k.hasil
urutan = k.urutan
pilih_seg = [s for s in urutan if s in k.segmen_pilih]
terpilih = k.usaha_terpilih
lo, hi, sorot = k.lo, k.hi, k.sorot
porsi_s = k.porsi()

ui.kepala(
    "Lensa 1 · Struktur ekonomi",
    "Siapa besar, siapa kecil, dan bagaimana porsinya berubah",
    "Setiap lapangan usaha punya porsi tertentu terhadap PDRB. Metode K-Means mengelompokkan "
    f"ke-{len(f)} lapangan usaha menjadi {len(urutan)} segmen berdasarkan porsi tahunannya, "
    "sehingga yang berperilaku mirip berada dalam satu kelompok.",
)

# --- analisis segmentasi K-Means (kalimat analisis) ---------------------------
prof = h["profil_segmen"]
sil = h["silhouette"]
kuat = "kuat" if sil > 0.70 else ("wajar" if sil > 0.50 else "lemah")


def _segmen_kalimat(s: str) -> str:
    r = prof.loc[s]
    ang = [u for u in f.index if f.loc[u, "Segmen"] == s]
    nama = ", ".join(ang) if len(ang) <= 6 else f"{', '.join(ang[:3])}, dan {len(ang) - 3} lainnya"
    return (f"<b>Segmen {s}</b> berisi {int(r['Jumlah_usaha'])} lapangan usaha ({nama}), "
            f"rata-rata {pct(r['Rata2_per_usaha'], 1)} PDRB per lapangan usaha dan total {pct(r['Total_porsi_PDRB'], 1)}")


ratio = prof.loc[urutan[0], "Rata2_per_usaha"] / prof.loc[urutan[-1], "Rata2_per_usaha"]
analisis = [
    f"<b>Cara kerjanya.</b> K-Means menilai kemiripan lapangan usaha dari porsi PDRB-nya pada setiap tahun "
    f"({k.periode_teks}). Angka distandarkan lebih dulu, lalu algoritma mencari {len(urutan)} kelompok dengan jarak "
    f"tiap lapangan usaha ke pusat kelompoknya sekecil mungkin. Pencarian diulang dari 50 titik awal acak "
    f"supaya hasilnya tidak bergantung pada tebakan awal.",
    f"<b>Hasilnya: {len(urutan)} segmen.</b><br>" + "<br>".join("\u2022 " + _segmen_kalimat(x) + "." for x in urutan),
    f"<b>Kualitasnya {kuat}.</b> Skor silhouette {idn(sil, 2)} (di atas 0,70 berarti kelompok terpisah jelas) dan "
    f"Davies\u2013Bouldin {idn(h['davies_bouldin'], 2)} (makin kecil makin baik). Metode lain (Ward) menghasilkan "
    f"kelompok yang {'sama persis' if h['ari_ward'] > 0.999 else 'mirip'} (kesesuaian {idn(h['ari_ward'], 2)}), dan hasil K-Means "
    f"sama pada {h['stabil_30_titik_awal']} dari 30 percobaan titik awal.",
    f"<b>Maknanya.</b> Peran lapangan usaha sangat timpang: rata-rata satu lapangan usaha di segmen {urutan[0]} "
    f"sekitar {idn(ratio, 0)} kali lipat segmen {urutan[-1]}. Segmen ini menggambarkan <i>besarnya peran</i> terhadap PDRB, "
    f"bukan kecepatan tumbuhnya. Soal pertumbuhan dan risiko dibahas di halaman Pertumbuhan dan risiko.",
]
with ui.kartu():
    ui.judul_kartu("Analisis segmentasi dengan K-Means", "Ringkasan hasil pengelompokan, dihitung ulang mengikuti filter periode.")
    ui.temuan(analisis)

# --- peringkat + penjelasan segmen -----------------------------------------
kiri, kanan = st.columns([7, 5], gap="large")
with kiri:
    with ui.kartu():
        ui.judul_kartu(f"Porsi tiap lapangan usaha, {k.label_sorot}", "Persen terhadap PDRB kabupaten. Warna = segmen.")
        st.plotly_chart(viz.batang_sektor(porsi_s[terpilih], f["Segmen"], pilih_seg),
                        width="stretch", theme=None, config={"displayModeBar": False})
with kanan:
    with ui.kartu():
        ui.judul_kartu("Tiga segmen", f"Ringkasan tiap segmen ({k.label_sorot}).")
        baris = []
        for s in pilih_seg:
            ang = [u for u in f.index if f.loc[u, "Segmen"] == s]
            total = porsi_s[ang].sum()
            baris.append(
                f'<div class="segmen-baris"><div class="nama">{ui.titik(k.warna[s])}Segmen {s}</div>'
                f'<div class="meta">{len(ang)} lapangan usaha · {pct(total)} dari PDRB · '
                f'rata-rata {pct(total / len(ang))} per usaha</div>'
                f'<div class="anggota">{ui.pil(ang)}</div></div>')
        st.markdown("".join(baris), unsafe_allow_html=True)

# --- perubahan porsi -------------------------------------------------------
ui.bagian("Apa yang berubah", f"Perbandingan porsi tahun {lo} dan {hi}, serta lintasan beberapa lapangan usaha.")
kiri, kanan = st.columns(2, gap="large")
with kiri:
    with ui.kartu():
        ui.judul_kartu(f"Perubahan porsi {lo} → {hi}",
                       "Dalam poin persentase. Biru = porsi naik, abu = porsi turun.")
        sel = (k.porsi(hi) - k.porsi(lo))[terpilih]
        st.plotly_chart(viz.lolipop_selisih(sel, k.porsi(lo)[terpilih], k.porsi(hi)[terpilih], lo, hi),
                        width="stretch", theme=None, config={"displayModeBar": False})
with kanan:
    with ui.kartu():
        ui.judul_kartu("Lintasan porsi", "Pilih sampai 5 lapangan usaha untuk dibandingkan.")
        bawaan = list(porsi_s[terpilih].sort_values(ascending=False).index[:4])
        pilihan = st.multiselect("Lapangan usaha", terpilih, default=bawaan, max_selections=5,
                                 key="trend_" + "_".join(pilih_seg), label_visibility="collapsed")
        if pilihan:
            tab = pd.DataFrame({t: k.porsi(t)[pilihan] for t in k.tahun})
            st.plotly_chart(viz.garis_banyak(tab, "%", "Porsi"), width="stretch", theme=None,
                            config={"displayModeBar": False})
        else:
            st.caption("Pilih minimal satu lapangan usaha.")

# --- kualitas pengelompokan -----------------------------------------------
ui.bagian("Seberapa meyakinkan pengelompokan ini")
with st.expander("Lihat uji kualitas pengelompokan", expanded=False):
    sil = h["silhouette"]
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        ui.angka(idn(sil, 2), "Skor silhouette", "Di atas 0,70 berarti kelompok terpisah jelas.")
    with c2:
        ui.angka(idn(h["davies_bouldin"], 2), "Davies–Bouldin", "Makin kecil makin baik.")
    with c3:
        ui.angka(idn(h["ari_ward"], 2), "Kesamaan dengan metode Ward", "1,00 berarti hasilnya identik.")
    with c4:
        ui.angka(f"{h['stabil_30_titik_awal']}/30", "Titik awal acak", "Berapa kali hasilnya sama.")
    a, b = st.columns(2, gap="large")
    with a:
        ui.judul_kartu("Mengapa tiga segmen?", "Skor silhouette untuk jumlah kelompok 2 sampai 6.")
        st.plotly_chart(viz.evaluasi_klaster(h["evaluasi_k"], h["k"]), width="stretch", theme=None,
                        config={"displayModeBar": False})
    with b:
        ui.judul_kartu("Kecocokan tiap lapangan usaha", "Makin dekat 1, makin pas di segmennya.")
        st.plotly_chart(viz.silhouette_usaha(h["silhouette_per_usaha"], f["Segmen"], urutan),
                        width="stretch", theme=None, config={"displayModeBar": False})
    tunggal = [s for s in urutan if (f["Segmen"] == s).sum() == 1]
    ui.catatan(
        "Skor silhouette 0 pada lapangan usaha yang sendirian di segmennya adalah nilai standar, "
        "bukan tanda salah kelompok." + (f" Di sini: segmen {', '.join(tunggal)}." if tunggal else "")
        + " Tiga segmen dipilih karena memisahkan satu penopang utama, lapisan menengah, dan lapisan kecil "
        "dengan skor yang tetap tinggi.")

# --- tabel ------------------------------------------------------------------
ui.bagian("Tabel lengkap", "Dapat diurutkan dengan klik judul kolom dan dicari lewat ikon kaca pembesar di kanan atas tabel.")
tabel = f.loc[terpilih, ["Segmen"] + [c for c in f.columns if c.startswith("Kontribusi_")]].copy()
tabel.columns = ["Segmen"] + [c.replace("Kontribusi_rata2", "Rata-rata").replace("Kontribusi_", "") for c in tabel.columns[1:]]
tabel = tabel.sort_values("Rata-rata", ascending=False)
cfg = {c: st.column_config.NumberColumn(c, format="%.2f%%") for c in tabel.columns if c != "Segmen"}
st.dataframe(tabel, column_config=cfg, width="stretch", height=420)
pipeline.unduh(tabel, "segmentasi_lapangan_usaha.csv")
