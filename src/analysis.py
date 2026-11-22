"""Analisis dua lensa: segmentasi K-Means dan imbal hasil-risiko.

Seluruh fungsi di sini murni (tidak bergantung Streamlit) supaya bisa diuji
terpisah. Angkanya mengikuti notebook
`Pendekatan_Dua_Lensa_PDRB_Bojonegoro_FINAL.ipynb`.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats
from scipy.spatial.distance import pdist, squareform
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.metrics import (
    adjusted_rand_score,
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_samples,
    silhouette_score,
)
from sklearn.preprocessing import StandardScaler

SEED = 42
Z95 = float(stats.norm.ppf(0.95))  # 1,645

NAMA_SEGMEN = {1: "Besar", 2: "Menengah", 3: "Kecil"}
URUTAN_SEGMEN = ["Besar", "Menengah", "Kecil"]


# ==========================================================================
# Lensa 1: segmentasi
# ==========================================================================


def bangun_fitur(df: pd.DataFrame) -> pd.DataFrame:
    """Pivot kontribusi: satu baris per usaha, satu kolom per tahun."""
    kt = df.pivot_table(index="Usaha", columns="Tahun", values="Kontribusi", observed=True)
    kt.columns = [f"Kontribusi_{t}" for t in kt.columns]
    fitur = kt.copy()
    fitur["Kontribusi_rata2"] = kt.mean(axis=1)
    return fitur.sort_values("Kontribusi_rata2", ascending=False)


def kolom_kontribusi(fitur: pd.DataFrame) -> list[str]:
    return [k for k in fitur.columns if k.startswith("Kontribusi_") and k != "Kontribusi_rata2"]


def standardisasi(fitur: pd.DataFrame) -> pd.DataFrame:
    """Z-score tiap kolom tahun (StandardScaler, pembagi n)."""
    cols = kolom_kontribusi(fitur)
    scaler = StandardScaler()
    return pd.DataFrame(scaler.fit_transform(fitur[cols]), index=fitur.index, columns=cols)


def matriks_jarak(Z: pd.DataFrame) -> pd.DataFrame:
    """Jarak Euclidean antarusaha pada data terstandardisasi."""
    return pd.DataFrame(squareform(pdist(Z.values, metric="euclidean")),
                        index=Z.index, columns=Z.index)


def pasangan_jarak(D: pd.DataFrame) -> pd.DataFrame:
    """Daftar semua pasangan usaha beserta jaraknya, terurut dari termirip."""
    baris = [(D.index[i], D.columns[j], D.iloc[i, j])
             for i in range(len(D)) for j in range(i + 1, len(D))]
    return (pd.DataFrame(baris, columns=["Usaha A", "Usaha B", "Jarak"])
            .sort_values("Jarak").reset_index(drop=True))


def evaluasi_jumlah_klaster(Z: pd.DataFrame, k_min: int = 2, k_max: int = 6,
                            seed: int = SEED) -> pd.DataFrame:
    """Empat ukuran evaluasi untuk tiap jumlah klaster."""
    hasil = []
    k_max = min(k_max, len(Z) - 1)
    for k in range(k_min, k_max + 1):
        km = KMeans(n_clusters=k, n_init=50, random_state=seed).fit(Z.values)
        ukuran = sorted(np.bincount(km.labels_), reverse=True)
        hasil.append({
            "k": k,
            "Inertia": float(km.inertia_),
            "Silhouette": float(silhouette_score(Z.values, km.labels_)),
            "Davies-Bouldin": float(davies_bouldin_score(Z.values, km.labels_)),
            "Calinski-Harabasz": float(calinski_harabasz_score(Z.values, km.labels_)),
            "Klaster 1 anggota": int(sum(1 for v in ukuran if v == 1)),
            "Ukuran klaster": ", ".join(str(int(v)) for v in ukuran),
        })
    return pd.DataFrame(hasil).set_index("k")


def kmeans_manual(Z: pd.DataFrame, fitur: pd.DataFrame, centroid_awal: list[str],
                  maks_iterasi: int = 10) -> tuple[np.ndarray, list[dict]]:
    """K-Means langkah demi langkah, untuk memperlihatkan alurnya.

    Mengembalikan label akhir dan catatan tiap iterasi.
    """
    X = Z.values
    rata2 = fitur.loc[Z.index, "Kontribusi_rata2"].values
    pusat = Z.loc[centroid_awal].values.copy()
    k = len(centroid_awal)
    lab_lama = None
    lab = np.zeros(len(X), dtype=int)
    catatan: list[dict] = []

    for it in range(1, maks_iterasi + 1):
        jarak = np.linalg.norm(X[:, None, :] - pusat[None, :, :], axis=2)
        lab = jarak.argmin(axis=1)
        ringkas = [{"Klaster": j + 1,
                    "Jumlah usaha": int((lab == j).sum()),
                    "Rata-rata kontribusi (%)": float(rata2[lab == j].mean()) if (lab == j).any() else np.nan}
                   for j in range(k)]
        pindah = [] if lab_lama is None else Z.index[lab != lab_lama].tolist()
        catatan.append({"iterasi": it, "ringkasan": pd.DataFrame(ringkas),
                        "pindah": pindah, "selesai": lab_lama is not None and not pindah})
        if lab_lama is not None and not pindah:
            break
        lab_lama = lab
        pusat = np.array([X[lab == j].mean(axis=0) if (lab == j).any() else pusat[j]
                          for j in range(k)])
    return lab, catatan


def segmentasi(Z: pd.DataFrame, fitur: pd.DataFrame, k: int = 3,
               seed: int = SEED) -> dict:
    """K-Means sklearn, label diurutkan dari rata-rata kontribusi terbesar."""
    km = KMeans(n_clusters=k, n_init=50, random_state=seed).fit(Z.values)

    urut = (fitur.loc[Z.index].assign(raw=km.labels_)
            .groupby("raw")["Kontribusi_rata2"].mean()
            .sort_values(ascending=False).index)
    peta = {raw: i + 1 for i, raw in enumerate(urut)}
    klaster = pd.Series(km.labels_, index=Z.index).map(peta)

    if k == 3:
        nama = NAMA_SEGMEN
        urutan = URUTAN_SEGMEN
    else:  # jumlah klaster selain 3 diberi nama generik
        nama = {i + 1: f"Klaster {i + 1}" for i in range(k)}
        urutan = [nama[i + 1] for i in range(k)]
    segmen = klaster.map(nama)

    hasil = fitur.loc[Z.index].copy()
    hasil["Klaster"] = klaster
    hasil["Segmen"] = segmen

    sil = pd.Series(silhouette_samples(Z.values, klaster.values),
                    index=Z.index, name="Silhouette")

    ward = AgglomerativeClustering(n_clusters=k, linkage="ward").fit_predict(Z.values)
    ari_ward = float(adjusted_rand_score(klaster.values, ward))
    ari_awal = [adjusted_rand_score(klaster.values,
                                    KMeans(k, n_init=1, random_state=s).fit_predict(Z.values))
                for s in range(30)]
    stabil = int(np.sum(np.isclose(ari_awal, 1.0)))

    return {
        "k": k,
        "fitur": hasil.sort_values("Kontribusi_rata2", ascending=False),
        "urutan_segmen": urutan,
        "silhouette_per_usaha": sil,
        "silhouette": float(silhouette_score(Z.values, klaster.values)),
        "davies_bouldin": float(davies_bouldin_score(Z.values, klaster.values)),
        "calinski_harabasz": float(calinski_harabasz_score(Z.values, klaster.values)),
        "ari_ward": ari_ward,
        "stabil_30_titik_awal": stabil,
        "labels": klaster,
    }


def profil_segmen(fitur: pd.DataFrame, urutan: list[str]) -> pd.DataFrame:
    """Ringkasan tiap segmen: jumlah usaha, rata-rata, rentang, total porsi."""
    profil = fitur.groupby("Segmen", observed=True).agg(
        Jumlah_usaha=("Kontribusi_rata2", "size"),
        Rata2_per_usaha=("Kontribusi_rata2", "mean"),
        Terkecil=("Kontribusi_rata2", "min"),
        Terbesar=("Kontribusi_rata2", "max"),
        Total_porsi_PDRB=("Kontribusi_rata2", "sum"),
    )
    return profil.reindex([s for s in urutan if s in profil.index])


def peran_segmen_per_tahun(df: pd.DataFrame, fitur: pd.DataFrame,
                           urutan: list[str]) -> pd.DataFrame:
    """Total kontribusi tiap segmen pada tiap tahun."""
    gab = df.merge(fitur[["Segmen"]].reset_index(), on="Usaha")
    tabel = gab.groupby(["Tahun", "Segmen"], observed=True)["Kontribusi"].sum().unstack()
    return tabel[[s for s in urutan if s in tabel.columns]]


# ==========================================================================
# Lensa 2: imbal hasil dan risiko
# ==========================================================================


def pivot_imbal_hasil(df: pd.DataFrame) -> pd.DataFrame:
    """Imbal hasil (pertumbuhan, %) per usaha per tahun."""
    if "Pertumbuhan" not in df.columns:
        raise ValueError("Data tidak memuat kolom pertumbuhan.")
    return df.pivot_table(index="Usaha", columns="Tahun", values="Pertumbuhan", observed=True)


def andil_pertumbuhan(df: pd.DataFrame) -> pd.DataFrame | None:
    """Andil (sumber) pertumbuhan tiap usaha per tahun, dalam poin persen.

    Istilah yang dipakai BPS pada publikasi PDRB. Rumusnya:

        andil_t = (ADHK_t - ADHK_{t-1}) / total ADHK_{t-1} x 100

    Jumlah andil seluruh usaha pada satu tahun sama dengan pertumbuhan
    ekonomi kabupaten pada tahun itu, sehingga terlihat usaha mana yang
    menarik naik dan mana yang menarik turun.
    """
    if "ADHK" not in df.columns:
        return None
    adhk = df.pivot_table(index="Usaha", columns="Tahun", values="ADHK", observed=True)
    total_lalu = adhk.sum(axis=0).shift(1)
    andil = adhk.diff(axis=1).div(total_lalu, axis=1) * 100
    return andil.dropna(axis=1, how="all")


def ringkas_andil(andil: pd.DataFrame) -> dict:
    """Ringkasan andil: pertumbuhan kabupaten, penarik naik, penarik turun."""
    pertumbuhan_total = andil.sum(axis=0)
    rata2 = andil.mean(axis=1).sort_values(ascending=False)
    tahun_akhir = andil.columns[-1]
    return {
        "pertumbuhan_kabupaten": pertumbuhan_total,
        "andil_rata2": rata2,
        "penarik_naik": rata2.head(5),
        "penarik_turun": rata2[rata2 < 0].sort_values(),
        "tahun_akhir": tahun_akhir,
        "andil_tahun_akhir": andil[tahun_akhir].sort_values(ascending=False),
    }


def tabel_risiko(ret: pd.DataFrame, fitur: pd.DataFrame) -> pd.DataFrame:
    """Imbal hasil, risiko, pertumbuhan terburuk, dan VaR 95% per usaha."""
    risk = pd.DataFrame({
        "Imbal_hasil": ret.mean(axis=1),
        "Risiko": ret.std(axis=1, ddof=1),
        "Terburuk": ret.min(axis=1),
        "Jumlah_pengamatan": ret.notna().sum(axis=1),
    })
    risk["VaR95_SDPP"] = risk["Imbal_hasil"] - Z95 * risk["Risiko"]
    risk["Kontribusi_rata2"] = fitur["Kontribusi_rata2"]
    if "Segmen" in fitur.columns:
        risk["Segmen"] = fitur["Segmen"]
    return risk.sort_values("Imbal_hasil", ascending=False)


def tambah_profil_rr(risk: pd.DataFrame) -> tuple[pd.DataFrame, float, float]:
    """Bagi usaha jadi empat profil memakai median imbal hasil dan risiko."""
    med_r = float(risk["Imbal_hasil"].median())
    med_s = float(risk["Risiko"].median())

    def label(b):
        cepat = "Tumbuh cepat" if b["Imbal_hasil"] >= med_r else "Tumbuh lambat"
        stabil = "bergejolak" if b["Risiko"] >= med_s else "stabil"
        return f"{cepat}, {stabil}"

    out = risk.copy()
    out["Profil_RR"] = out.apply(label, axis=1)
    return out, med_r, med_s


def var_per_kelompok(df: pd.DataFrame, fitur: pd.DataFrame,
                     urutan: list[str]) -> pd.DataFrame:
    """VaR 95% gabungan per segmen: Historical Simulation dan SDPP."""
    pengamatan = df.merge(fitur[["Segmen"]].reset_index(), on="Usaha").dropna(subset=["Pertumbuhan"])
    baris = []
    for s in list(urutan) + ["Semua usaha"]:
        x = (pengamatan["Pertumbuhan"] if s == "Semua usaha"
             else pengamatan.loc[pengamatan["Segmen"] == s, "Pertumbuhan"])
        if len(x) == 0:
            continue
        baris.append([s, int(len(x)), float(x.mean()), float(x.std(ddof=1)),
                      float(np.percentile(x, 5)), float(x.mean() - Z95 * x.std(ddof=1))])
    return pd.DataFrame(
        baris, columns=["Kelompok", "n", "Rata2", "Simpangan_baku", "VaR95_HS", "VaR95_SDPP"]
    ).set_index("Kelompok")


def uji_antarsegmen(df: pd.DataFrame, fitur: pd.DataFrame,
                    urutan: list[str]) -> dict:
    """Shapiro-Wilk, Levene, Kruskal-Wallis, ANOVA, dan uji lanjut Mann-Whitney."""
    pengamatan = df.merge(fitur[["Segmen"]].reset_index(), on="Usaha").dropna(subset=["Pertumbuhan"])
    kel = {s: pengamatan.loc[pengamatan["Segmen"] == s, "Pertumbuhan"].values
           for s in urutan if (pengamatan["Segmen"] == s).any()}

    normalitas = []
    for s, x in kel.items():
        p = float(stats.shapiro(x).pvalue) if len(x) >= 3 else np.nan
        normalitas.append({"Segmen": s, "n": int(len(x)), "p Shapiro-Wilk": p})

    p_levene = float(stats.levene(*kel.values()).pvalue) if len(kel) >= 2 else np.nan
    h = p_kw = f = p_an = np.nan
    if len(kel) >= 2:
        h, p_kw = stats.kruskal(*kel.values())
        f, p_an = stats.f_oneway(*kel.values())

    lanjut = []
    nama = list(kel)
    n_pasangan = max(len(nama) * (len(nama) - 1) // 2, 1)
    for i in range(len(nama)):
        for j in range(i + 1, len(nama)):
            a, b = nama[i], nama[j]
            _, p = stats.mannwhitneyu(kel[a], kel[b], alternative="two-sided")
            lanjut.append({"Pasangan": f"{a} vs {b}", "p": float(p),
                           "p terkoreksi (Bonferroni)": float(min(p * n_pasangan, 1.0))})

    return {
        "normalitas": pd.DataFrame(normalitas),
        "p_levene": p_levene,
        "kruskal_H": float(h), "kruskal_p": float(p_kw),
        "anova_F": float(f), "anova_p": float(p_an),
        "uji_lanjut": pd.DataFrame(lanjut),
        "pengamatan": pengamatan,
    }


# ==========================================================================
# Gabungan kedua lensa
# ==========================================================================


def hubungan_peran_imbal_hasil(risk: pd.DataFrame,
                               kecualikan: str | None = "Pertambangan") -> dict:
    """Korelasi Spearman kontribusi vs imbal hasil, dengan dan tanpa outlier."""
    rho, p = stats.spearmanr(risk["Kontribusi_rata2"], risk["Imbal_hasil"])
    out = {"rho": float(rho), "p": float(p), "rho_tanpa": None, "p_tanpa": None,
           "dikecualikan": None}
    if kecualikan and kecualikan in risk.index and len(risk) > 3:
        tanpa = risk.drop(index=kecualikan)
        rho2, p2 = stats.spearmanr(tanpa["Kontribusi_rata2"], tanpa["Imbal_hasil"])
        out.update(rho_tanpa=float(rho2), p_tanpa=float(p2), dikecualikan=kecualikan)
    return out


def tipologi_gabungan(risk: pd.DataFrame, fitur: pd.DataFrame,
                      urutan: list[str]) -> dict:
    """Tabel silang segmen x profil imbal hasil-risiko, plus ARI keduanya."""
    silang = pd.crosstab(risk["Segmen"], risk["Profil_RR"])
    silang = silang.reindex([s for s in urutan if s in silang.index])

    kode_rr = risk["Profil_RR"].astype("category").cat.codes
    ari = float(adjusted_rand_score(fitur.loc[risk.index, "Klaster"], kode_rr))

    kolom = [k for k in ["Segmen", "Kontribusi_rata2", "Imbal_hasil", "Risiko",
                         "VaR95_SDPP", "Profil_RR"] if k in risk.columns]
    peta_urut = {s: i for i, s in enumerate(urutan)}
    gabung = risk[kolom].sort_values(
        ["Segmen", "Kontribusi_rata2"],
        key=lambda s: s.map(peta_urut) if s.name == "Segmen" else -s,
    )
    return {"silang": silang, "ari": ari, "gabung": gabung}


# ==========================================================================
# Pembungkus: jalankan seluruh alur
# ==========================================================================


def jalankan_semua(df: pd.DataFrame, k: int = 3, seed: int = SEED,
                   centroid_awal: list[str] | None = None) -> dict:
    """Jalankan lensa 1, lensa 2 (kalau datanya ada), dan gabungannya."""
    fitur = bangun_fitur(df)
    Z = standardisasi(fitur)

    hasil = {
        "fitur_mentah": fitur,
        "Z": Z,
        "korelasi_antartahun": float(fitur[kolom_kontribusi(fitur)].corr().values.min()),
        "jarak": matriks_jarak(Z),
        "evaluasi_k": evaluasi_jumlah_klaster(Z, seed=seed),
    }
    hasil["pasangan_jarak"] = pasangan_jarak(hasil["jarak"])

    seg = segmentasi(Z, fitur, k=k, seed=seed)
    hasil.update(seg)
    hasil["profil_segmen"] = profil_segmen(seg["fitur"], seg["urutan_segmen"])
    hasil["peran_per_tahun"] = peran_segmen_per_tahun(df, seg["fitur"], seg["urutan_segmen"])

    if centroid_awal is None:
        urut = seg["fitur"].sort_values("Kontribusi_rata2", ascending=False).index.tolist()
        if len(urut) >= k:
            langkah = max(len(urut) // k, 1)
            centroid_awal = [urut[min(i * langkah, len(urut) - 1)] for i in range(k)]
    tersedia = [u for u in (centroid_awal or []) if u in Z.index]
    if len(set(tersedia)) == k:
        lab_manual, catatan = kmeans_manual(Z, seg["fitur"], list(dict.fromkeys(tersedia)))
        hasil["manual_catatan"] = catatan
        hasil["manual_centroid_awal"] = list(dict.fromkeys(tersedia))
        hasil["manual_sama_dengan_sklearn"] = bool(
            np.isclose(adjusted_rand_score(lab_manual, seg["labels"].values), 1.0))

    andil = andil_pertumbuhan(df)
    hasil["andil"] = None
    if andil is not None and not andil.empty:
        hasil["andil"] = {"tabel": andil, **ringkas_andil(andil)}

    hasil["lensa2"] = None
    if "Pertumbuhan" in df.columns and df["Pertumbuhan"].notna().any():
        ret = pivot_imbal_hasil(df)
        risk = tabel_risiko(ret, seg["fitur"])
        risk, med_r, med_s = tambah_profil_rr(risk)
        hasil["lensa2"] = {
            "imbal_hasil_per_tahun": ret,
            "risiko": risk,
            "median_imbal_hasil": med_r,
            "median_risiko": med_s,
            "var_kelompok": var_per_kelompok(df, seg["fitur"], seg["urutan_segmen"]),
            "uji": uji_antarsegmen(df, seg["fitur"], seg["urutan_segmen"]),
        }
        hasil["gabungan"] = {
            **tipologi_gabungan(risk, seg["fitur"], seg["urutan_segmen"]),
            "korelasi": hubungan_peran_imbal_hasil(risk),
        }
    else:
        hasil["gabungan"] = None

    return hasil
