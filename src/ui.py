"""Gaya dan komponen tampilan.

Arah desain: keluarga warna biru (sidebar dan spanduk gradien biru, kartu putih
bersudut bulat), satu jenis huruf sans, banyak ruang kosong. Bagian yang berbeda
fungsi diberi bentuk berbeda: angka utama berupa tipografi tanpa kotak,
grafik berada di kartu, temuan berupa daftar bernomor.
"""

from __future__ import annotations

import base64
from html import escape
from pathlib import Path

import streamlit as st

AKAR = Path(__file__).resolve().parent.parent
LOGO = AKAR / "assets" / "logo_bps.png"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

:root{
  --latar:#EEF4FB; --kartu:#FFFFFF; --tinta:#12263F; --tinta2:#43566F; --redup:#74869C;
  --garis:#DCE6F4; --biru:#1766B3; --biru-tua:#0B4A8F; --biru-muda:#2F7DE1; --risiko:#C8442F;
}

/* ---------- dasar ---------- */
.stApp, .stApp p, .stApp li, .stApp label, .stApp input, .stApp textarea, .stApp button,
.stApp [data-testid="stMarkdownContainer"], .stApp [data-testid="stCaptionContainer"],
.stApp [data-testid="stWidgetLabel"] p {
  font-family:'Plus Jakarta Sans','Segoe UI','Helvetica Neue',Arial,sans-serif;
}
.stApp{ background:var(--latar); color:var(--tinta); }
.block-container{ max-width:1200px; padding:1.6rem 2.2rem 4rem; }
[data-testid="stToolbar"], [data-testid="stDecoration"], footer, #MainMenu{ display:none !important; }
header[data-testid="stHeader"]{ background:transparent; }

/* ---------- sidebar biru ---------- */
[data-testid="stSidebar"]{
  background:linear-gradient(180deg,#0B4A8F 0%,#1260AE 55%,#1976D2 100%); border-right:none; }
[data-testid="stSidebar"] *{ color:#EAF3FF; }
[data-testid="stSidebar"] [data-testid="stSidebarHeader"] img, [data-testid="stLogo"]{
  height:2.6rem !important; max-height:none !important; width:auto;
  background:#fff; border-radius:12px; padding:.25rem; }
[data-testid="stSidebarNavLink"]{ border-radius:10px; font-weight:500; }
[data-testid="stSidebarNavLink"] span{ color:#DCEBFF !important; }
[data-testid="stSidebarNavLink"][aria-current="page"]{
  background:#2F7DE1; box-shadow:0 4px 14px rgba(0,30,80,.25); }
[data-testid="stSidebarNavLink"][aria-current="page"] span{ color:#fff !important; font-weight:700; }
[data-testid="stSidebarNavLink"]:hover{ background:rgba(255,255,255,.12); }
[data-testid="stSidebar"] hr{ border-color:rgba(255,255,255,.2); }
[data-testid="stSidebar"] [class*="st-key-kotak_filter"]{
  background:#fff; border-radius:16px; padding:1rem 1rem .6rem; box-shadow:0 6px 18px rgba(0,30,80,.22); }
[data-testid="stSidebar"] [class*="st-key-kotak_filter"] *{ color:#12263F; }
[data-testid="stSidebar"] [class*="st-key-kotak_filter"] [data-baseweb="tag"]{ background:#0B4A8F !important; }
[data-testid="stSidebar"] [class*="st-key-kotak_filter"] [data-baseweb="tag"] *{ color:#fff !important; }
.filter-judul{ font-size:.72rem; letter-spacing:.14em; text-transform:uppercase; color:#A9CBF5 !important;
  font-weight:700; margin:.6rem 0 .2rem; }
.sumber-kecil{ font-size:.76rem; color:#BFD9F8 !important; line-height:1.5; margin-top:.8rem; }

/* ---------- hero biru ---------- */
.hero{ position:relative; overflow:hidden; border-radius:22px; padding:2rem 2.2rem 1.8rem; margin:0 0 1.8rem;
  background:linear-gradient(135deg,#0B4A8F 0%,#1366B5 55%,#2287E0 100%);
  box-shadow:0 14px 34px rgba(11,74,143,.28); color:#fff; }
.hero::before{ content:""; position:absolute; right:-70px; top:-90px; width:300px; height:300px;
  border-radius:50%; background:rgba(255,255,255,.08); }
.hero::after{ content:""; position:absolute; right:140px; bottom:-120px; width:240px; height:240px;
  border-radius:50%; background:rgba(255,255,255,.06); }
.hero > *{ position:relative; z-index:1; }
.hero .alis{ display:inline-block; font-size:.72rem; letter-spacing:.14em; text-transform:uppercase;
  background:rgba(255,255,255,.16); border:1px solid rgba(255,255,255,.28); color:#fff; font-weight:700;
  padding:.28rem .8rem; border-radius:999px; margin-bottom:.9rem; }
.hero h1{ font-weight:800; font-size:2.25rem; line-height:1.15; color:#fff; margin:0 0 .6rem; padding:0;
  letter-spacing:-0.02em; max-width:860px; }
.hero .lede{ font-size:1.02rem; line-height:1.65; color:rgba(255,255,255,.9); max-width:800px; margin:0; }
.hero .lede b{ color:#fff; }
.kaca{ display:grid; grid-template-columns:repeat(4,1fr); gap:1rem; margin-top:1.5rem; }
.kaca .sel{ background:rgba(255,255,255,.12); border:1px solid rgba(255,255,255,.26); border-radius:16px;
  padding:1rem 1.1rem; backdrop-filter:blur(2px); }
.kaca .label{ font-size:.82rem; color:rgba(255,255,255,.85); font-weight:600; }
.kaca .nilai{ font-size:2rem; font-weight:800; line-height:1.1; margin:.3rem 0 .25rem; color:#fff;
  letter-spacing:-0.02em; }
.kaca .nilai small{ font-size:.95rem; font-weight:700; opacity:.8; margin-left:.15rem; }
.kaca .catatan{ font-size:.78rem; color:rgba(255,255,255,.75); line-height:1.45; }
.kaca .sel.risiko .nilai{ color:#FFC2B5; }

/* ---------- judul bagian ---------- */
.bagian{ margin:2.4rem 0 1rem; }
.bagian h2{ font-weight:800; font-size:1.4rem; color:var(--biru-tua); margin:0 0 .3rem; padding:0;
  letter-spacing:-0.01em; }
.bagian p{ margin:0; color:var(--tinta2); font-size:.95rem; line-height:1.6; max-width:780px; }

/* ---------- kartu ---------- */
[class*="st-key-kartu"]{
  background:var(--kartu); border:1px solid var(--garis); border-radius:20px;
  padding:1.25rem 1.35rem 1rem; box-shadow:0 2px 4px rgba(11,74,143,.04), 0 12px 30px rgba(11,74,143,.07); }
.kartu-judul{ font-weight:700; font-size:1rem; color:var(--tinta); margin:0 0 .15rem; }
.kartu-ket{ font-size:.86rem; color:var(--redup); margin:0 0 .6rem; line-height:1.5; }

/* ---------- angka dalam halaman ---------- */
.angka{ padding:.15rem 0 1.05rem; border-bottom:1px solid var(--garis); }
.angka:last-child{ border-bottom:none; }
.angka .nilai{ font-weight:800; font-size:2.2rem; line-height:1.05; color:var(--biru); letter-spacing:-0.02em; }
.angka .nilai small{ font-size:1rem; font-weight:700; color:var(--redup); margin-left:.2rem; }
.angka .label{ font-size:.9rem; font-weight:700; color:var(--tinta); margin-top:.3rem; }
.angka .catatan{ font-size:.84rem; color:var(--redup); margin-top:.15rem; line-height:1.5; }
.angka.risiko .nilai{ color:var(--risiko); }
.baris-angka{ display:grid; grid-template-columns:repeat(4,1fr); gap:1rem; margin:0 0 .5rem; }
.baris-angka .angka{ background:#fff; border:1px solid var(--garis); border-radius:16px; padding:1rem 1.1rem; }
.baris-angka .nilai{ font-size:1.9rem; }

/* ---------- temuan ---------- */
.temuan{ display:flex; gap:1rem; padding:1rem 0; border-top:1px solid var(--garis); }
.temuan:first-child{ border-top:none; padding-top:.2rem; }
.temuan .no{ font-weight:800; font-size:.95rem; color:#fff; background:var(--biru-muda); border-radius:10px;
  min-width:1.9rem; height:1.9rem; display:flex; align-items:center; justify-content:center; flex:none; }
.temuan .isi{ font-size:.95rem; line-height:1.62; color:var(--tinta); }
.temuan .isi b{ color:var(--biru-tua); }

/* ---------- catatan, legenda, token ---------- */
.catatan-kiri{ border-left:4px solid var(--biru-muda); background:rgba(47,125,225,.07); border-radius:0 12px 12px 0;
  padding:.6rem .9rem; color:var(--tinta2); font-size:.9rem; line-height:1.6; margin:.5rem 0; }
.titik{ display:inline-block; width:.62rem; height:.62rem; border-radius:50%; margin-right:.45rem; vertical-align:baseline; }
.segmen-baris{ padding:.85rem 0; border-top:1px solid var(--garis); }
.segmen-baris:first-child{ border-top:none; padding-top:.2rem; }
.segmen-baris .nama{ font-weight:700; color:var(--tinta); font-size:.98rem; }
.segmen-baris .meta{ color:var(--redup); font-size:.84rem; margin:.1rem 0 .3rem; }
.segmen-baris .anggota{ color:var(--tinta2); font-size:.88rem; line-height:1.6; }
.pil{ display:inline-block; background:#F3F8FE; border:1px solid var(--garis); border-radius:999px;
  padding:.12rem .65rem; font-size:.8rem; margin:.12rem .2rem .12rem 0; color:var(--tinta2); }

/* ---------- kontrol ---------- */
[data-testid="stExpander"]{ border:1px solid var(--garis); border-radius:14px; background:var(--kartu); }
[data-testid="stExpander"] summary{ font-weight:600; color:var(--biru-tua); }
div[data-testid="stDataFrame"]{ border:1px solid var(--garis); border-radius:14px; overflow:hidden; }
.stDownloadButton button, .stButton button{ border-radius:10px; border:1px solid var(--biru); background:#fff;
  color:var(--biru); font-weight:700; }
.stDownloadButton button:hover, .stButton button:hover{ background:var(--biru); color:#fff; border-color:var(--biru); }

/* ---------- layar kecil ---------- */
@media (max-width: 900px){
  .block-container{ padding:1rem 1rem 3rem; }
  .hero{ padding:1.4rem 1.2rem; }
  .hero h1{ font-size:1.65rem; }
  .kaca, .baris-angka{ grid-template-columns:repeat(2,1fr); }
}
@media (max-width: 520px){
  .kaca, .baris-angka{ grid-template-columns:1fr; }
}
</style>
"""


def pasang_gaya() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
    st.session_state["_n_kartu"] = 0


def logo_base64() -> str | None:
    if LOGO.exists():
        return base64.b64encode(LOGO.read_bytes()).decode()
    return None


# --------------------------------------------------------------------------
# Komponen
# --------------------------------------------------------------------------


def kepala(alis: str, judul: str, lede: str = "", angka: list[dict] | None = None) -> None:
    """Spanduk biru di puncak halaman. `angka` menampilkan kartu kaca di dalamnya."""
    sel = ""
    for a in angka or []:
        sat = f"<small>{escape(a.get('satuan', ''))}</small>" if a.get("satuan") else ""
        cat = f'<div class="catatan">{a["catatan"]}</div>' if a.get("catatan") else ""
        kelas = "sel risiko" if a.get("risiko") else "sel"
        sel += (f'<div class="{kelas}"><div class="label">{escape(a["label"])}</div>'
                f'<div class="nilai">{escape(a["nilai"])}{sat}</div>{cat}</div>')
    st.markdown(
        f'<div class="hero"><div class="alis">{escape(alis)}</div><h1>{escape(judul)}</h1>'
        + (f'<p class="lede">{lede}</p>' if lede else "")
        + (f'<div class="kaca">{sel}</div>' if sel else "") + "</div>",
        unsafe_allow_html=True,
    )


def bagian(judul: str, keterangan: str = "") -> None:
    st.markdown(
        f'<div class="bagian"><h2>{escape(judul)}</h2>'
        + (f"<p>{keterangan}</p>" if keterangan else "") + "</div>",
        unsafe_allow_html=True,
    )


def kartu():
    """Wadah putih berbayang halus. Pakai dengan `with ui.kartu():`."""
    n = st.session_state.get("_n_kartu", 0) + 1
    st.session_state["_n_kartu"] = n
    return st.container(key=f"kartu_{n}")


def judul_kartu(judul: str, ket: str = "") -> None:
    st.markdown(
        f'<div class="kartu-judul">{escape(judul)}</div>'
        + (f'<div class="kartu-ket">{ket}</div>' if ket else ""),
        unsafe_allow_html=True,
    )


def angka_html(nilai: str, label: str, catatan: str = "", satuan: str = "", risiko: bool = False) -> str:
    kelas = "angka risiko" if risiko else "angka"
    sat = f"<small>{escape(satuan)}</small>" if satuan else ""
    cat = f'<div class="catatan">{catatan}</div>' if catatan else ""
    return (f'<div class="{kelas}"><div class="nilai">{escape(nilai)}{sat}</div>'
            f'<div class="label">{escape(label)}</div>{cat}</div>')


def angka(nilai: str, label: str, catatan: str = "", satuan: str = "", risiko: bool = False) -> None:
    st.markdown(angka_html(nilai, label, catatan, satuan, risiko), unsafe_allow_html=True)


def baris_angka(butir: list[dict]) -> None:
    """Deretan angka utama dengan garis pemisah halus, tanpa kotak."""
    isi = "".join(angka_html(**b) for b in butir)
    st.markdown(f'<div class="baris-angka">{isi}</div>', unsafe_allow_html=True)


def temuan(daftar: list[str]) -> None:
    """Daftar bernomor bergaya redaksi. Isi boleh memuat <b>."""
    st.markdown(
        "".join(f'<div class="temuan"><div class="no">{i}</div><div class="isi">{t}</div></div>'
                for i, t in enumerate(daftar, 1)),
        unsafe_allow_html=True,
    )


def catatan(teks: str) -> None:
    st.markdown(f'<div class="catatan-kiri">{teks}</div>', unsafe_allow_html=True)


def titik(warna: str) -> str:
    return f'<span class="titik" style="background:{warna}"></span>'


def pil(nama: list[str]) -> str:
    return "".join(f'<span class="pil">{escape(n)}</span>' for n in nama)
