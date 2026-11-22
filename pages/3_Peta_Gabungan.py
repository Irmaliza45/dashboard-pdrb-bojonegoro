"""Gabungan dua lensa: segmen (ukuran peran) dan profil (pertumbuhan dan risiko)."""

import streamlit as st

from src import pipeline, ui, viz
from src.viz import idn, pct

k = pipeline.konteks()
f, L = k.fitur, k.lensa2
urutan = k.urutan
terpilih = k.usaha_terpilih

ui.kepala(
    "Dua lensa disatukan",
    "Ukuran peran dan perilaku pertumbuhan tidak selalu sejalan",
    "Segmen menjawab seberapa besar peran sebuah lapangan usaha. Profil menjawab bagaimana ia tumbuh dan "
    "seberapa tidak menentu. Jika digabung, terlihat lapangan usaha mana yang perlu dipantau lebih dekat.",
)

G = k.hasil.get("gabungan")
if not G or not L:
    ui.catatan("Halaman ini memerlukan data pertumbuhan. Berkas yang dipakai belum memuatnya.")
    st.stop()

PROFIL = ["Tumbuh cepat, stabil", "Tumbuh cepat, bergejolak", "Tumbuh lambat, stabil", "Tumbuh lambat, bergejolak"]
gab = G["gabung"].loc[terpilih]

kiri, kanan = st.columns([6, 6], gap="large")
with kiri:
    with ui.kartu():
        ui.judul_kartu("Berapa lapangan usaha di tiap pertemuan",
                       "Baris = segmen (ukuran). Kolom = profil pertumbuhan dan risiko.")
        sil = G["silang"].reindex(index=[s for s in urutan if s in k.segmen_pilih],
                                  columns=[p for p in PROFIL if p in G["silang"].columns])
        st.plotly_chart(viz.matriks_silang(sil), width="stretch", theme=None, config={"displayModeBar": False})
with kanan:
    with ui.kartu():
        ui.judul_kartu("Siapa saja di tiap profil", "Titik berwarna menunjukkan segmennya.")
        blok = []
        for p in PROFIL:
            sub = gab[gab["Profil_RR"] == p].sort_values("Kontribusi_rata2", ascending=False)
            if sub.empty:
                continue
            isi = "".join(
                f'<span class="pil">{ui.titik(k.warna[sub.loc[u, "Segmen"]])}{u}</span>' for u in sub.index)
            warna = "#C8442F" if p == "Tumbuh lambat, bergejolak" else "#1B2330"
            blok.append(f'<div class="segmen-baris"><div class="nama" style="color:{warna}">{p}</div>'
                        f'<div class="meta">{len(sub)} lapangan usaha</div><div class="anggota">{isi}</div></div>')
        st.markdown("".join(blok), unsafe_allow_html=True)

# --- perlu perhatian -----------------------------------------------------------
rawan = gab[gab["Profil_RR"] == "Tumbuh lambat, bergejolak"].sort_values("Kontribusi_rata2", ascending=False)
ui.bagian("Yang perlu dipantau lebih dekat",
          "Lapangan usaha yang tumbuh di bawah nilai tengah sekaligus naik-turun di atas nilai tengah, diurutkan dari porsi PDRB terbesar.")
if rawan.empty:
    ui.catatan("Tidak ada lapangan usaha dengan profil ini pada periode dan segmen yang dipilih.")
else:
    t = rawan[["Segmen", "Kontribusi_rata2", "Imbal_hasil", "Risiko", "VaR95_SDPP"]].copy()
    t.columns = ["Segmen", "Porsi PDRB (%)", "Pertumbuhan rata-rata (%)", "Naik-turun (poin)", "VaR 95% (%)"]
    cfg = {c: st.column_config.NumberColumn(c, format="%.2f") for c in t.columns if c != "Segmen"}
    st.dataframe(t, column_config=cfg, width="stretch")

# --- ukuran vs pertumbuhan ------------------------------------------------------
ui.bagian("Apakah yang besar tumbuh lebih lambat?")
kor, ari = G["korelasi"], G["ari"]
a, b = st.columns(2, gap="large")
with a:
    ui.angka(idn(kor["rho"], 2), "Korelasi Spearman porsi vs pertumbuhan",
             f"p = {idn(kor['p'], 3)}" + (f"; tanpa {kor['dikecualikan']}: {idn(kor['rho_tanpa'], 2)} (p = {idn(kor['p_tanpa'], 3)})"
                                          if kor.get("dikecualikan") else ""))
    st.markdown(
        ("Tandanya negatif, artinya lapangan usaha yang porsinya besar cenderung tumbuh lebih lambat. "
           if kor["rho"] < 0 else
           "Tandanya positif, artinya lapangan usaha yang porsinya besar cenderung tumbuh lebih cepat. ")
        + ("Namun hubungan ini **belum cukup kuat secara statistik** (p di atas 0,05), "
           "sehingga tidak bisa disimpulkan berlaku umum." if kor["p"] >= 0.05
           else "Hubungan ini nyata secara statistik.")
    )
with b:
    ui.angka(idn(ari, 2), "Kesesuaian segmen dengan profil", "Adjusted Rand Index; 1,00 = identik")
    st.markdown("Nilai yang rendah berarti pengelompokan menurut ukuran dan menurut pertumbuhan-risiko "
                "**memang berbeda**. Karena itu kedua lensa saling melengkapi dan tidak saling menggantikan.")

# --- tabel ------------------------------------------------------------------------
ui.bagian("Tipologi lengkap")
t = gab[["Segmen", "Profil_RR", "Kontribusi_rata2", "Imbal_hasil", "Risiko", "VaR95_SDPP"]].copy()
t.columns = ["Segmen", "Profil", "Porsi PDRB (%)", "Pertumbuhan rata-rata (%)", "Naik-turun (poin)", "VaR 95% (%)"]
cfg = {c: st.column_config.NumberColumn(c, format="%.2f") for c in t.columns if c not in ("Segmen", "Profil")}
st.dataframe(t, column_config=cfg, width="stretch", height=420)
pipeline.unduh(t, "tipologi_gabungan.csv")
