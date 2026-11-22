"""Pemuatan dan perapian data PDRB Bojonegoro.

Loader ini sengaja dibuat fleksibel supaya menerima dua bentuk file:

1. **Format panjang** (seperti yang dipakai notebook, 85 baris):
   kolom `Tahun`, `Lapangan Usaha`, `PDRB ADHB`, `PDRB ADHK`,
   `Kontribusi PDRB`, `Pertumbuhan PDRB (%)`; pemisah `;` dan desimal `,`.

2. **Format lebar** (17 baris): kolom `kode`, `lapangan_usaha`, lalu satu
   kolom per tahun yang berisi kontribusi (%).

Keduanya dikembalikan dalam satu bentuk baku (tidy, satu baris = satu
usaha x satu tahun) dengan kolom:
`Tahun, Kode, Usaha_Lengkap, Usaha, Kontribusi` ditambah
`ADHB, ADHK, Pertumbuhan` kalau tersedia di sumber data.
"""

from __future__ import annotations

import io
import re
from dataclasses import dataclass, field

import pandas as pd

# --------------------------------------------------------------------------
# Nama pendek lapangan usaha (dipakai di tabel dan grafik)
# --------------------------------------------------------------------------

KODE_KE_PENDEK = {
    "A": "Pertanian",
    "B": "Pertambangan",
    "C": "Industri Pengolahan",
    "D": "Listrik & Gas",
    "E": "Air & Limbah",
    "F": "Konstruksi",
    "G": "Perdagangan",
    "H": "Transportasi",
    "I": "Akomodasi & Mamin",
    "J": "Info & Komunikasi",
    "K": "Keuangan & Asuransi",
    "L": "Real Estat",
    "M,N": "Jasa Perusahaan",
    "O": "Adm. Pemerintahan",
    "P": "Pendidikan",
    "Q": "Kesehatan",
    "R,S,T,U": "Jasa Lainnya",
}

# Dicocokkan berurutan: kata kunci pertama yang muncul pada nama usaha dipakai.
# Lebih tahan terhadap selisih penulisan nama antar-file BPS
# (misalnya "... Jaminan Sosial" vs "... Jaminan Sosial Wajib").
KATA_KUNCI_KE_PENDEK = [
    ("industri pengolahan", "Industri Pengolahan"),
    ("pertanian", "Pertanian"),
    ("pertambangan", "Pertambangan"),
    ("listrik", "Listrik & Gas"),
    ("sampah", "Air & Limbah"),
    ("pengadaan air", "Air & Limbah"),
    ("konstruksi", "Konstruksi"),
    ("perdagangan", "Perdagangan"),
    ("transportasi", "Transportasi"),
    ("akomodasi", "Akomodasi & Mamin"),
    ("informasi", "Info & Komunikasi"),
    ("keuangan", "Keuangan & Asuransi"),
    ("real estat", "Real Estat"),
    ("jasa perusahaan", "Jasa Perusahaan"),
    ("administrasi", "Adm. Pemerintahan"),
    ("pendidikan", "Pendidikan"),
    ("kesehatan", "Kesehatan"),
    ("jasa lainnya", "Jasa Lainnya"),
]

URUTAN_USAHA_BAKU = list(KODE_KE_PENDEK.values())


def _normalkan(teks: str) -> str:
    return re.sub(r"\s+", " ", str(teks)).strip().lower()


def nama_pendek(nama_lengkap: str, kode: str | None = None) -> str | None:
    """Kembalikan nama pendek usaha dari kode BPS atau dari nama lengkapnya."""
    if kode is not None:
        k = str(kode).replace(" ", "").upper()
        if k in KODE_KE_PENDEK:
            return KODE_KE_PENDEK[k]
    n = _normalkan(nama_lengkap)
    for kunci, pendek in KATA_KUNCI_KE_PENDEK:
        if kunci in n:
            return pendek
    return None


# --------------------------------------------------------------------------
# Hasil pemuatan
# --------------------------------------------------------------------------


@dataclass
class HasilMuat:
    """Data baku beserta catatan kolom apa saja yang tersedia."""

    df: pd.DataFrame
    bentuk: str  # "panjang" atau "lebar"
    kolom_tersedia: list[str] = field(default_factory=list)
    catatan: list[str] = field(default_factory=list)

    @property
    def ada_pertumbuhan(self) -> bool:
        return "Pertumbuhan" in self.df.columns

    @property
    def ada_adhk(self) -> bool:
        return "ADHK" in self.df.columns

    @property
    def ada_adhb(self) -> bool:
        return "ADHB" in self.df.columns

    @property
    def lensa2_siap(self) -> bool:
        """Lensa 2 butuh imbal hasil: dari kolom Pertumbuhan atau dari ADHK."""
        return self.ada_pertumbuhan or self.ada_adhk

    @property
    def tahun(self) -> list[int]:
        return sorted(self.df["Tahun"].unique().tolist())


# --------------------------------------------------------------------------
# Pembacaan berkas
# --------------------------------------------------------------------------

_PETA_NAMA_KOLOM = {
    "tahun": "Tahun",
    "year": "Tahun",
    "kode": "Kode",
    "kode lapangan usaha": "Kode",
    "lapangan usaha": "Usaha_Lengkap",
    "lapangan_usaha": "Usaha_Lengkap",
    "usaha": "Usaha_Lengkap",
    "sektor": "Usaha_Lengkap",
    "pdrb adhb": "ADHB",
    "adhb": "ADHB",
    "pdrb adhk": "ADHK",
    "adhk": "ADHK",
    "kontribusi pdrb": "Kontribusi",
    "kontribusi pdrb (%)": "Kontribusi",
    "kontribusi": "Kontribusi",
    "distribusi": "Kontribusi",
    "pertumbuhan pdrb (%)": "Pertumbuhan",
    "pertumbuhan pdrb": "Pertumbuhan",
    "pertumbuhan (%)": "Pertumbuhan",
    "pertumbuhan": "Pertumbuhan",
    "laju pertumbuhan": "Pertumbuhan",
}


def _baca_mentah(sumber) -> pd.DataFrame:
    """Baca CSV/Excel dengan menebak pemisah dan tanda desimal."""
    nama = getattr(sumber, "name", str(sumber))
    if str(nama).lower().endswith((".xlsx", ".xls")):
        return pd.read_excel(sumber)

    if hasattr(sumber, "read"):
        isi = sumber.read()
        if isinstance(isi, bytes):
            isi = isi.decode("utf-8-sig", errors="replace")
    else:
        with open(sumber, "r", encoding="utf-8-sig") as f:
            isi = f.read()

    baris_pertama = isi.splitlines()[0] if isi.splitlines() else ""
    kandidat = [(";", ","), (",", "."), ("\t", ".")]
    # Pemisah ditebak dari baris header: yang paling sering muncul.
    pemisah = max((";", ",", "\t"), key=baris_pertama.count)
    desimal = dict(kandidat)[pemisah]

    df = pd.read_csv(io.StringIO(isi), sep=pemisah, decimal=desimal)
    if df.shape[1] == 1:  # tebakan salah, coba pemisah lain
        for p, d in kandidat:
            if p == pemisah:
                continue
            alt = pd.read_csv(io.StringIO(isi), sep=p, decimal=d)
            if alt.shape[1] > 1:
                return alt
    return df


def _rapikan_nama_kolom(df: pd.DataFrame) -> pd.DataFrame:
    baru = {}
    for k in df.columns:
        kunci = _normalkan(k)
        baru[k] = _PETA_NAMA_KOLOM.get(kunci, k)
    return df.rename(columns=baru)


def _kolom_tahun(df: pd.DataFrame) -> list:
    """Kolom yang namanya berupa tahun 4 angka (penanda format lebar)."""
    out = []
    for k in df.columns:
        s = str(k).strip()
        if re.fullmatch(r"(19|20)\d{2}(\.0)?", s):
            out.append(k)
    return out


def _ke_angka(s: pd.Series) -> pd.Series:
    """Paksa jadi angka; tangani '1.234,56', '12,87', dan spasi."""
    if pd.api.types.is_numeric_dtype(s):
        return s.astype(float)
    t = s.astype(str).str.strip().str.replace(r"\s+", "", regex=True)
    pakai_koma = t.str.contains(",") & ~t.str.contains(r",\d{3}(\D|$)", regex=True)
    t = t.mask(pakai_koma, t.str.replace(".", "", regex=False).str.replace(",", ".", regex=False))
    t = t.mask(~pakai_koma, t.str.replace(",", "", regex=False))
    return pd.to_numeric(t, errors="coerce")


def muat_data(sumber) -> HasilMuat:
    """Muat data PDRB dari CSV/Excel, format panjang atau lebar."""
    mentah = _rapikan_nama_kolom(_baca_mentah(sumber))
    mentah.columns = [str(k).strip() for k in mentah.columns]

    kol_tahun = _kolom_tahun(mentah)
    catatan: list[str] = []

    if kol_tahun and "Tahun" not in mentah.columns:
        # ---------------- format lebar ----------------
        id_vars = [k for k in ("Kode", "Usaha_Lengkap") if k in mentah.columns]
        if not id_vars:
            raise ValueError(
                "Format lebar terdeteksi tetapi kolom nama lapangan usaha tidak ditemukan. "
                "Pastikan ada kolom 'lapangan_usaha' (dan sebaiknya 'kode')."
            )
        df = mentah.melt(id_vars=id_vars, value_vars=kol_tahun,
                         var_name="Tahun", value_name="Kontribusi")
        df["Tahun"] = df["Tahun"].astype(str).str.extract(r"((?:19|20)\d{2})")[0].astype(int)
        df["Kontribusi"] = _ke_angka(df["Kontribusi"])
        bentuk = "lebar"
        catatan.append(
            "File berformat lebar dan hanya memuat kolom kontribusi, "
            "sehingga hanya Lensa 1 (segmentasi) yang dapat dihitung."
        )
    else:
        # ---------------- format panjang ----------------
        if "Tahun" not in mentah.columns or "Usaha_Lengkap" not in mentah.columns:
            raise ValueError(
                "Kolom wajib tidak lengkap. Format panjang membutuhkan kolom "
                "'Tahun' dan 'Lapangan Usaha'."
            )
        df = mentah.copy()
        df["Tahun"] = _ke_angka(df["Tahun"]).astype("Int64").astype(int)
        for k in ("ADHB", "ADHK", "Kontribusi", "Pertumbuhan"):
            if k in df.columns:
                df[k] = _ke_angka(df[k])
        bentuk = "panjang"

    if "Usaha_Lengkap" not in df.columns:
        raise ValueError("Nama lapangan usaha tidak ditemukan pada data.")
    df["Usaha_Lengkap"] = df["Usaha_Lengkap"].astype(str).str.strip()
    if "Kode" not in df.columns:
        df["Kode"] = None

    df["Usaha"] = [nama_pendek(n, k) for n, k in zip(df["Usaha_Lengkap"], df["Kode"])]
    belum = df.loc[df["Usaha"].isna(), "Usaha_Lengkap"].unique().tolist()
    if belum:
        catatan.append("Nama usaha ini belum dikenali dan dipakai apa adanya: " + ", ".join(belum))
        df["Usaha"] = df["Usaha"].fillna(df["Usaha_Lengkap"])

    # Kontribusi dihitung dari ADHB kalau belum ada di data.
    if "Kontribusi" not in df.columns:
        if "ADHB" in df.columns:
            df["Kontribusi"] = df["ADHB"] / df.groupby("Tahun")["ADHB"].transform("sum") * 100
            catatan.append("Kolom kontribusi tidak ada di data, jadi dihitung dari ADHB.")
        else:
            raise ValueError("Data tidak memuat kontribusi maupun ADHB, sehingga Lensa 1 tidak bisa dihitung.")

    # Pertumbuhan dihitung dari ADHK kalau belum ada di data.
    if "Pertumbuhan" not in df.columns and "ADHK" in df.columns:
        df = df.sort_values(["Usaha", "Tahun"])
        df["Pertumbuhan"] = df.groupby("Usaha")["ADHK"].pct_change() * 100
        catatan.append("Kolom pertumbuhan dihitung dari ADHK; tahun pertama otomatis kosong.")

    urut_kategori = pd.Categorical(
        df["Usaha"],
        categories=[u for u in URUTAN_USAHA_BAKU if u in set(df["Usaha"])]
        + sorted(set(df["Usaha"]) - set(URUTAN_USAHA_BAKU)),
        ordered=True,
    )
    df = df.assign(_urut=urut_kategori).sort_values(["_urut", "Tahun"]).drop(columns="_urut")

    kolom_akhir = [k for k in ("Tahun", "Kode", "Usaha", "Usaha_Lengkap",
                               "ADHB", "ADHK", "Kontribusi", "Pertumbuhan") if k in df.columns]
    df = df[kolom_akhir].reset_index(drop=True)

    return HasilMuat(
        df=df,
        bentuk=bentuk,
        kolom_tersedia=[k for k in ("ADHB", "ADHK", "Kontribusi", "Pertumbuhan") if k in df.columns],
        catatan=catatan,
    )


def periksa_mutu(df: pd.DataFrame) -> dict:
    """Ringkasan pemeriksaan kualitas data, seperti bagian 1.2 notebook."""
    jumlah_kontribusi = df.groupby("Tahun")["Kontribusi"].sum().round(2)
    selisih_kontribusi = None
    if "ADHB" in df.columns:
        hitung = df["ADHB"] / df.groupby("Tahun")["ADHB"].transform("sum") * 100
        selisih_kontribusi = float((hitung - df["Kontribusi"]).abs().max())

    selisih_pertumbuhan = None
    if {"ADHK", "Pertumbuhan"} <= set(df.columns):
        urut = df.sort_values(["Usaha", "Tahun"])
        hitung_r = urut.groupby("Usaha")["ADHK"].pct_change() * 100
        beda = (hitung_r - urut["Pertumbuhan"]).abs()
        if beda.notna().any():
            selisih_pertumbuhan = float(beda.max())

    # Kolom Kode sering kosong pada data format lebar dan tidak dipakai analisis,
    # jadi tidak dihitung sebagai nilai hilang.
    kol_nilai = [k for k in ("Tahun", "Usaha", "Usaha_Lengkap", "ADHB", "ADHK",
                             "Kontribusi", "Pertumbuhan") if k in df.columns]
    kosong = df[kol_nilai].isna()
    if "Pertumbuhan" in kosong.columns:
        # Tahun pertama memang tidak punya pertumbuhan kalau dihitung dari ADHK.
        tahun_awal = df["Tahun"].min()
        kosong.loc[df["Tahun"] == tahun_awal, "Pertumbuhan"] = False

    return {
        "baris": int(len(df)),
        "jumlah_usaha": int(df["Usaha"].nunique()),
        "jumlah_tahun": int(df["Tahun"].nunique()),
        "nilai_kosong": int(kosong.to_numpy().sum()),
        "baris_duplikat": int(df[kol_nilai].duplicated().sum()),
        "duplikat_tahun_usaha": int(df.duplicated(["Tahun", "Usaha"]).sum()),
        "jumlah_kontribusi_per_tahun": jumlah_kontribusi,
        "selisih_kontribusi_vs_adhb": selisih_kontribusi,
        "selisih_pertumbuhan_vs_adhk": selisih_pertumbuhan,
    }
