"""Lensa 2: pertumbuhan, risiko, dan nilai berisiko tiap lapangan usaha."""

import pandas as pd
import streamlit as st

from src import pipeline, ui, viz
from src.viz import idn, pct

k = pipeline.konteks()
f, L = k.fitur, k.lensa2
urutan = k.urutan
pilih_seg = [s for s in urutan if s in k.segmen_pilih]
terpilih = k.usaha_terpilih

ui.kepala(
    "Lensa 2 · Pertumbuhan dan risiko",
    "Siapa tumbuh cepat, dan siapa paling bergejolak",
    "Pertumbuhan tiap lapangan usaha dari tahun ke tahun dibaca bersama seberapa tidak menentu "
    "pertumbuhan itu. Dua sisi ini yang membedakan lapangan usaha yang sehat dari yang rawan.",
)

if not L:
    ui.catatan("Halaman ini memerlukan kolom <b>Pertumbuhan PDRB (%)</b> pada berkas data. "
               "Berkas yang sedang dipakai belum memuatnya.")
    st.stop()

risk = L["risiko"].loc[terpilih]
ret = L["imbal_hasil_per_tahun"].loc[terpilih]

# --- peta panas + VaR -------------------------------------------------------
kiri, kanan = st.columns([7, 5], gap="large")
with kiri:
    with ui.kartu():
        ui.judul_kartu("Pertumbuhan per tahun (%)",
                       "Biru = tumbuh, terakota = menyusut. Diurutkan dari rata-rata tertinggi.")
        st.plotly_chart(viz.peta_panas_tumbuh(ret), width="stretch", theme=None,
                        config={"displayModeBar": False})
with kanan:
    with ui.kartu():
        ui.judul_kartu("Perkiraan pertumbuhan pada kondisi buruk",
                       "VaR 95%: batas pertumbuhan yang hanya terlewati sekitar 1 dari 20 kali. "
                       "Makin negatif, makin rawan.")
        v = L["var_kelompok"]
        st.plotly_chart(viz.batang_var(v), width="stretch", theme=None, config={"displayModeBar": False})
        st.caption("Dihitung dari 5 pengamatan per lapangan usaha, jadi bersifat indikatif.")

# --- sebaran ---------------------------------------------------------------
ui.bagian("Peta pertumbuhan dan risiko", "Kuadran dibatasi oleh nilai tengah (median) seluruh lapangan usaha.")
with ui.kartu():
    st.plotly_chart(viz.sebar_risiko(risk, pilih_seg, L["median_risiko"], L["median_imbal_hasil"]),
                    width="stretch", theme=None, config={"displayModeBar": False})
    st.caption("Luas titik mengikuti porsi lapangan usaha terhadap PDRB. Titik tanpa nama: arahkan kursor untuk melihat rinciannya.")

# --- telusuri satu lapangan usaha -------------------------------------------
ui.bagian("Telusuri satu lapangan usaha")
urut_pil = list(f.loc[terpilih].sort_values("Kontribusi_rata2", ascending=False).index)
pilih = st.selectbox("Lapangan usaha", urut_pil, key="telusur_" + "_".join(pilih_seg))
r = L["risiko"].loc[pilih]
kiri, kanan = st.columns([7, 5], gap="large")
with kiri:
    with ui.kartu():
        ui.judul_kartu(f"Pertumbuhan {pilih}", f"Persen per tahun. Garis putus-putus = rata-rata periode ({idn(r['Imbal_hasil'], 2)}%).")
        st.plotly_chart(viz.garis_usaha(L["imbal_hasil_per_tahun"].loc[pilih], float(r["Imbal_hasil"]), pilih),
                        width="stretch", theme=None, config={"displayModeBar": False})
with kanan:
    a, b = st.columns(2)
    with a:
        ui.angka(idn(r["Imbal_hasil"], 2), "Rata-rata pertumbuhan", f"Segmen {r['Segmen']}", "%")
        ui.angka(idn(r["Risiko"], 2), "Naik-turun pertumbuhan", "Simpangan baku, poin")
    with b:
        ui.angka(idn(r["Terburuk"], 2), "Tahun terburuk", "", "%", risiko=r["Terburuk"] < 0)
        ui.angka(idn(r["VaR95_SDPP"], 2), "VaR 95%", r["Profil_RR"], "%", risiko=r["VaR95_SDPP"] < 0)

# --- andil (hanya bila data ADHK tersedia) -----------------------------------
if h := k.hasil.get("andil"):
    ui.bagian("Siapa penarik pertumbuhan", "Andil = sumbangan tiap lapangan usaha terhadap pertumbuhan ekonomi kabupaten.")
    with ui.kartu():
        st.plotly_chart(viz.batang_andil(h["andil_rata2"].loc[[u for u in h["andil_rata2"].index if u in terpilih]]),
                        width="stretch", theme=None, config={"displayModeBar": False})

# --- tabel ------------------------------------------------------------------
ui.bagian("Tabel pertumbuhan dan risiko")
t = risk[["Segmen", "Imbal_hasil", "Risiko", "Terburuk", "VaR95_SDPP", "Kontribusi_rata2", "Profil_RR"]].copy()
t.columns = ["Segmen", "Pertumbuhan rata-rata (%)", "Naik-turun (poin)", "Tahun terburuk (%)",
             "VaR 95% (%)", "Porsi PDRB (%)", "Profil"]
cfg = {c: st.column_config.NumberColumn(c, format="%.2f") for c in t.columns if c not in ("Segmen", "Profil")}
st.dataframe(t, column_config=cfg, width="stretch", height=420)
pipeline.unduh(t, "pertumbuhan_dan_risiko.csv")

# --- uji statistik ------------------------------------------------------------
with st.expander("Apakah pertumbuhan benar-benar berbeda antarsegmen?"):
    u = L["uji"]
    nyata = u["kruskal_p"] < 0.05
    st.markdown(
        f"Uji Kruskal–Wallis memberi H = {idn(u['kruskal_H'], 2)} dengan p = {idn(u['kruskal_p'], 3)}. "
        + ("Artinya pertumbuhan **berbeda nyata** antarsegmen." if nyata
           else "Artinya **belum cukup bukti** bahwa pertumbuhan berbeda antarsegmen.")
    )
    uj = u["uji_lanjut"].copy()
    uj["Kesimpulan"] = uj["p terkoreksi (Bonferroni)"].map(lambda p: "Berbeda nyata" if p < 0.05 else "Tidak berbeda nyata")
    st.dataframe(uj, width="stretch", hide_index=True,
                 column_config={"p": st.column_config.NumberColumn(format="%.4f"),
                                "p terkoreksi (Bonferroni)": st.column_config.NumberColumn(format="%.4f")})
    ui.catatan("Pengamatan antar tahun pada lapangan usaha yang sama tidak sepenuhnya saling bebas, "
               "jadi hasil uji dibaca sebagai petunjuk, bukan bukti pasti.")
