"""Penghubung antara Streamlit dan modul analisis.

Alur: berkas data -> filter periode di sidebar -> analisis dihitung ulang
untuk periode itu -> halaman membaca `Konteks`. Dengan begitu satu perubahan
filter memperbarui semua grafik, angka, dan tabel di semua halaman.
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import streamlit as st

from . import analysis, data as data_mod, ui, viz

AKAR = Path(__file__).resolve().parent.parent
FOLDER_DATA = AKAR / "data"
K_UTAMA = 3
URUTAN_SEGMEN = ["Besar", "Menengah", "Kecil"]


# --------------------------------------------------------------------------
# Data
# --------------------------------------------------------------------------


def berkas_bawaan() -> Path | None:
    if not FOLDER_DATA.exists():
        return None
    kandidat = sorted(
        [p for p in FOLDER_DATA.iterdir()
         if p.suffix.lower() in (".csv", ".xlsx", ".xls") and not p.name.startswith((".", "_"))],
        key=lambda p: (0 if "adhk" in p.name.lower() or "data_pdrb" in p.name.lower() else 1, p.name),
    )
    return kandidat[0] if kandidat else None


@st.cache_data(show_spinner="Memuat data...")
def _muat_dari_path(path: str, _cap_waktu: float) -> data_mod.HasilMuat:
    return data_mod.muat_data(path)


@st.cache_data(show_spinner="Memuat data...")
def _muat_dari_unggahan(isi: bytes, nama: str) -> data_mod.HasilMuat:
    buf = io.BytesIO(isi)
    buf.name = nama
    return data_mod.muat_data(buf)


def ambil_data() -> data_mod.HasilMuat | None:
    terunggah = st.session_state.get("data_terunggah")
    if terunggah is not None:
        isi, nama = terunggah
        try:
            return _muat_dari_unggahan(isi, nama)
        except Exception as e:  # noqa: BLE001
            st.error(f"Berkas unggahan gagal dibaca: {e}")
    path = berkas_bawaan()
    if path is None:
        return None
    try:
        return _muat_dari_path(str(path), path.stat().st_mtime)
    except Exception as e:  # noqa: BLE001
        st.error(f"Berkas `{path.name}` gagal dibaca: {e}")
        return None


@st.cache_data(show_spinner="Menghitung analisis...")
def _hitung(df: pd.DataFrame, k: int, seed: int) -> dict:
    return analysis.jalankan_semua(df, k=k, seed=seed)


# --------------------------------------------------------------------------
# Filter di sidebar (dipasang sekali di app.py, berlaku di semua halaman)
# --------------------------------------------------------------------------


def pasang_filter() -> None:
    hm = ambil_data()
    with st.sidebar:
        if hm is None:
            return
        tahun = hm.tahun
        st.markdown('<div class="filter-judul">Filter</div>', unsafe_allow_html=True)

        with st.container(key="kotak_filter"):
            kunci = "_".join(str(t) for t in tahun)
            lo, hi = st.select_slider(
                "Periode analisis", options=tahun, value=(tahun[0], tahun[-1]),
                key=f"f_periode_{kunci}",
                help="Seluruh angka, grafik, dan pengelompokan dihitung ulang untuk periode ini. "
                     "Minimal 3 tahun.",
            )
            i0, i1 = tahun.index(lo), tahun.index(hi)
            if i1 - i0 < 2:  # minimal 3 tahun supaya risiko bisa dihitung
                i1 = min(i0 + 2, len(tahun) - 1)
                i0 = i1 - 2
                st.caption(f"Periode diperluas menjadi {tahun[i0]}–{tahun[i1]} (minimal 3 tahun).")
            lo, hi = tahun[i0], tahun[i1]
            st.session_state["_periode"] = (lo, hi)

            dalam = [t for t in tahun if lo <= t <= hi]
            pilihan = ["semua"] + dalam
            st.selectbox("Tahun sorotan", pilihan, index=len(pilihan) - 1, key=f"f_sorot_{lo}_{hi}",
                         format_func=lambda t: f"Semua tahun ({lo}\u2013{hi})" if t == "semua" else str(t),
                         help="Satu tahun tertentu, atau semua tahun dalam periode (memakai rata-rata porsi). "
                              "Dipakai untuk angka utama, peta porsi, dan batang peringkat.")
            st.multiselect("Segmen ditampilkan", URUTAN_SEGMEN, default=URUTAN_SEGMEN, key="f_segmen",
                           help="Segmen dibentuk dari ukuran peran tiap lapangan usaha. "
                                "Memilih sebagian segmen menyaring grafik dan tabel.")

        st.markdown(
            '<div class="sumber-kecil">Sumber: PDRB Kabupaten Bojonegoro menurut 17 lapangan usaha, '
            "BPS. Angka 2024 dan 2025 masih sementara.</div>",
            unsafe_allow_html=True,
        )


# --------------------------------------------------------------------------
# Konteks yang dibaca halaman
# --------------------------------------------------------------------------


@dataclass
class Konteks:
    hm: data_mod.HasilMuat
    df: pd.DataFrame          # data pada periode terpilih
    hasil: dict
    lo: int
    hi: int
    sorot: int
    segmen_pilih: list[str]
    semua: bool = False       # True bila "Semua tahun" dipilih pada Tahun sorotan

    @property
    def label_sorot(self) -> str:
        return f"rata-rata {self.lo}\u2013{self.hi}" if self.semua else str(self.sorot)

    @property
    def frasa_sorot(self) -> str:
        return f"Rata-rata {self.lo}\u2013{self.hi}" if self.semua else f"Pada {self.sorot}"

    @property
    def tahun(self) -> list[int]:
        return sorted(self.df["Tahun"].unique().tolist())

    @property
    def fitur(self) -> pd.DataFrame:
        return self.hasil["fitur"]

    @property
    def urutan(self) -> list[str]:
        return self.hasil["urutan_segmen"]

    @property
    def segmen(self) -> pd.Series:
        return self.fitur["Segmen"]

    @property
    def warna(self) -> dict[str, str]:
        return viz.warna_segmen(self.urutan)

    @property
    def usaha_terpilih(self) -> list[str]:
        return [u for u in self.fitur.index if self.segmen[u] in self.segmen_pilih]

    @property
    def lensa2(self) -> dict | None:
        return self.hasil.get("lensa2")

    def porsi(self, tahun: int | None = None) -> pd.Series:
        """Porsi PDRB per lapangan usaha. Tanpa argumen: sesuai pilihan Tahun sorotan
        (satu tahun, atau rata-rata seluruh periode bila "Semua tahun")."""
        if tahun is None:
            return self.fitur["Kontribusi_rata2"] if self.semua else self.fitur[f"Kontribusi_{self.sorot}"]
        return self.fitur[f"Kontribusi_{tahun}"]

    @property
    def periode_teks(self) -> str:
        return f"{self.lo}–{self.hi}" if self.lo != self.hi else str(self.lo)


def konteks() -> Konteks:
    ui.pasang_gaya()  # dipasang ulang di tiap halaman agar tetap ada saat halaman dibuka langsung lewat URL
    hm = ambil_data()
    if hm is None:
        st.error("Data belum ada. Letakkan berkas CSV di folder `data/`.")
        st.stop()

    tahun = hm.tahun
    lo, hi = st.session_state.get("_periode", (tahun[0], tahun[-1]))
    if lo not in tahun or hi not in tahun:
        lo, hi = tahun[0], tahun[-1]
    df = hm.df[(hm.df["Tahun"] >= lo) & (hm.df["Tahun"] <= hi)].copy()
    hasil = _hitung(df, K_UTAMA, analysis.SEED)

    sorot = st.session_state.get(f"f_sorot_{lo}_{hi}", hi)
    semua = sorot == "semua"
    if semua or sorot not in df["Tahun"].unique():
        sorot = hi
    pilih = st.session_state.get("f_segmen") or list(hasil["urutan_segmen"])
    pilih = [s for s in pilih if s in hasil["urutan_segmen"]] or list(hasil["urutan_segmen"])
    return Konteks(hm, df, hasil, int(lo), int(hi), int(sorot), pilih, semua)


def pengganti_berkas() -> None:
    """Kotak unggah berkas data (dipakai di halaman Data dan Metode)."""
    unggah = st.file_uploader(
        "Unggah berkas data baru", type=["csv", "xlsx", "xls"], key="unggahan_data",
        help=("Format panjang (Tahun, Lapangan Usaha, Kontribusi PDRB, Pertumbuhan PDRB (%), "
              "opsional PDRB ADHB dan ADHK) atau format lebar (kode, lapangan_usaha, "
              "satu kolom per tahun berisi kontribusi)."),
    )
    if unggah is not None:
        st.session_state["data_terunggah"] = (unggah.getvalue(), unggah.name)
    if st.session_state.get("data_terunggah") is not None:
        st.success(f"Memakai berkas unggahan: `{st.session_state['data_terunggah'][1]}`")
        if st.button("Kembali ke berkas bawaan"):
            del st.session_state["data_terunggah"]
            st.rerun()
    else:
        b = berkas_bawaan()
        st.caption(f"Memakai berkas di folder `data/`: `{b.name if b else '-'}`")


def unduh(df: pd.DataFrame, nama_berkas: str, label: str = "Unduh tabel (CSV)") -> None:
    st.download_button(label, df.to_csv().encode("utf-8"), file_name=nama_berkas, mime="text/csv")
