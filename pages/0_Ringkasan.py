"""Ringkasan: gambaran besar dalam satu layar."""

import streamlit as st

from src import pipeline, ui, viz
from src.viz import idn, pct

k = pipeline.konteks()
f, L = k.fitur, k.lensa2
urutan = k.urutan
terpilih = k.usaha_terpilih
lo, hi, sorot = k.lo, k.hi, k.sorot

porsi_s, porsi_0 = k.porsi(), k.porsi(lo)
teratas = porsi_s[terpilih].idxmax()

# --- empat angka utama ----------------------------------------------------
peran = k.hasil["peran_per_tahun"]
selisih_seg = {s: peran.loc[hi, s] - peran.loc[lo, s] for s in urutan if s in k.segmen_pilih}
seg_naik = max(selisih_seg, key=selisih_seg.get)

butir = [
    dict(nilai=idn(porsi_s[teratas]), satuan="%", label=f"Porsi {teratas}, {k.label_sorot}",
         catatan=(f"{idn(porsi_0[teratas])}% pada {lo}, {idn(k.porsi(hi)[teratas])}% pada {hi}" if k.semua else f"{idn(porsi_0[teratas])}% pada {lo}")),
    dict(nilai=idn(selisih_seg[seg_naik], 1, True), satuan=" poin", label=f"Segmen {seg_naik}, {lo}→{hi}",
         catatan=f"Perubahan porsi terbesar di antara segmen terpilih: {idn(peran.loc[lo, seg_naik])}% → {idn(peran.loc[hi, seg_naik])}%"
         if selisih_seg[seg_naik] > 0 else f"Porsi {idn(peran.loc[lo, seg_naik])}% → {idn(peran.loc[hi, seg_naik])}%"),
]
if L:
    risk = L["risiko"].loc[[u for u in L["risiko"].index if u in terpilih]]
    cepat, rawan = risk["Imbal_hasil"].idxmax(), risk["VaR95_SDPP"].idxmin()
    butir += [
        dict(nilai=idn(risk.loc[cepat, "Imbal_hasil"]), satuan="%", label=f"Tumbuh tercepat: {cepat}",
             catatan="Rata-rata pertumbuhan per tahun"),
        dict(nilai=idn(risk.loc[rawan, "Terburuk"]), satuan="%", label=f"Terburuk: {rawan}",
             catatan=f"Pertumbuhan terendah dalam periode; naik-turunnya {idn(risk.loc[rawan, 'Risiko'])} poin", risiko=True),
    ]
# --- kepala ---------------------------------------------------------------
ui.kepala(
    f"PDRB Kabupaten Bojonegoro · {k.periode_teks}",
    "Ekonomi Bojonegoro dalam 17 lapangan usaha",
    f"Satu pandangan tentang siapa penopang PDRB, siapa yang tumbuh, dan siapa yang berisiko. "
    f"{k.frasa_sorot}, <b>{teratas}</b> menyumbang {pct(porsi_s[teratas])} dari PDRB kabupaten. "
    f"Seluruh lapangan usaha dikelompokkan menurut perannya, lalu dinilai dari sisi pertumbuhan dan risikonya.",
    angka=butir,
)



# --- komposisi + peta porsi -------------------------------------------------
st.markdown("")
kiri, kanan = st.columns([5, 7], gap="large")
with kiri:
    with ui.kartu():
        ui.judul_kartu("Peran tiap segmen dari tahun ke tahun",
                       "Porsi terhadap PDRB (%). Segmen dibentuk K-Means dari besar kecilnya peran.")
        st.plotly_chart(viz.komposisi_segmen(peran[[s for s in urutan if s in k.segmen_pilih]],
                                             [s for s in urutan if s in k.segmen_pilih]),
                        width="stretch", theme=None, config={"displayModeBar": False})
with kanan:
    with ui.kartu():
        ui.judul_kartu(f"Peta peran lapangan usaha, {k.label_sorot}",
                       "Luas kotak = porsi terhadap PDRB. Arahkan kursor untuk melihat angka tepatnya.")
        st.plotly_chart(
            viz.peta_pohon(porsi_s[terpilih], f["Segmen"], [s for s in urutan if s in k.segmen_pilih]),
            width="stretch", theme=None, config={"displayModeBar": False})
        kecil = [u for u in terpilih if f.loc[u, "Segmen"] == urutan[-1]]
        if kecil and urutan[-1] in k.segmen_pilih:
            st.caption(f"Kotak-kotak kecil di bawah = segmen {urutan[-1]} ({len(kecil)} lapangan usaha, "
                       f"{pct(porsi_s[kecil].sum())}). Rinciannya ada di halaman Struktur ekonomi.")

# --- temuan + sebaran -------------------------------------------------------
ui.bagian("Yang perlu diketahui", "Lima hal dari analisis, dihitung ulang mengikuti periode yang dipilih.")

besar = [u for u in f.index if f.loc[u, "Segmen"] == urutan[0]]
menengah_seg = urutan[1]
tem = []
tem.append(
    f"<b>{teratas if teratas in besar else besar[0]} adalah penopang utama.</b> Porsinya {pct(k.porsi(sorot)[besar[0]])} "
    f"pada {sorot}, {'naik' if k.porsi(sorot)[besar[0]] >= k.porsi(lo)[besar[0]] else 'turun'} "
    f"dari {pct(k.porsi(lo)[besar[0]])} pada {lo}. Segmen {urutan[0]} hanya berisi "
    f"{len(besar)} lapangan usaha."
)
d = peran.loc[hi, menengah_seg] - peran.loc[lo, menengah_seg]
tem.append(
    f"<b>Porsi segmen {menengah_seg} {'naik' if d >= 0 else 'turun'}.</b> "
    f"Dari {pct(peran.loc[lo, menengah_seg])} pada {lo} menjadi {pct(peran.loc[hi, menengah_seg])} "
    f"pada {hi}, selisih {idn(abs(d))} poin persentase."
)
if L:
    r = L["risiko"]
    stabil = [u for u in r.index if r.loc[u, "Segmen"] == menengah_seg and r.loc[u, "Profil_RR"] == "Tumbuh cepat, stabil"]
    if stabil:
        tem.append(f"<b>{len(stabil)} lapangan usaha menengah tumbuh cepat dan stabil:</b> "
                   f"{', '.join(stabil)}. Pertumbuhannya di atas nilai tengah dan naik-turunnya di bawah nilai tengah.")
    gej = r[r["Profil_RR"] == "Tumbuh cepat, bergejolak"]
    if len(gej):
        tem.append(f"<b>{len(gej)} lapangan usaha tumbuh cepat tetapi bergejolak.</b> "
                   f"Yang tertinggi {gej['Imbal_hasil'].idxmax()} dengan rata-rata {pct(gej['Imbal_hasil'].max())} per tahun; "
                   f"{'Porsi PDRB-nya masing-masing masih kecil.' if (gej['Segmen'] == urutan[-1]).all() else ''}")
    w = r["VaR95_SDPP"].idxmin()
    tem.append(f"<b>{w} paling rawan.</b> Pertumbuhan rata-rata {pct(r.loc[w, 'Imbal_hasil'])}, "
               f"terburuk {pct(r.loc[w, 'Terburuk'])}. Perkiraan pertumbuhan pada kondisi buruk (VaR 95%) {pct(r.loc[w, 'VaR95_SDPP'])}.")

kiri, kanan = st.columns([5, 7], gap="large")
with kiri:
    ui.temuan(tem)
with kanan:
    if L:
        with ui.kartu():
            ui.judul_kartu("Pertumbuhan terhadap risiko",
                           "Makin ke atas = tumbuh makin cepat. Makin ke kiri = makin stabil. "
                           "Luas titik = porsi PDRB.")
            rs = L["risiko"].loc[terpilih]
            st.plotly_chart(viz.sebar_risiko(rs, [s for s in urutan if s in k.segmen_pilih],
                                             L["median_risiko"], L["median_imbal_hasil"]),
                            width="stretch", theme=None, config={"displayModeBar": False})
            st.caption("Garis putus-putus = nilai tengah (median) 17 lapangan usaha. Titik tanpa nama: arahkan kursor.")
    else:
        ui.catatan("Data pertumbuhan belum tersedia pada berkas yang dipakai, "
                   "jadi bagian pertumbuhan dan risiko belum bisa ditampilkan.")
