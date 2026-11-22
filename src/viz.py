"""Grafik Plotly untuk dashboard.

Aturan yang dipegang di seluruh grafik:
- satu warna tetap untuk satu segmen (biru, hijau-biru, kuning tua);
- merah terakota hanya dipakai untuk risiko dan nilai negatif;
- angka memakai format Indonesia (koma desimal, titik ribuan);
- setiap grafik punya tooltip yang menjelaskan nilainya.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

FONT = "Plus Jakarta Sans, Segoe UI, Helvetica Neue, Arial, sans-serif"

W = {
    "ink": "#1B2330",
    "ink2": "#4A5565",
    "muted": "#7A8494",
    "grid": "#E3EAF4",
    "axis": "#C7D3E3",
    "putih": "#FFFFFF",
    "navy": "#0B4A8F",
    "biru": "#2F6DB5",
    "risiko": "#C8442F",
    "turun": "#9A8F7E",
}

# Segmen berurutan dari yang terbesar. Tiga warna ini sama di semua halaman dan
# sudah lolos uji keterbacaan penyandang buta warna (jarak warna >= 14,8 pada simulasi protan).
_WARNA_SEGMEN = ["#2457A6", "#18A5A2", "#D8982A", "#6B7C93", "#2E5E8C", "#C3CEDB"]
# Warna teks yang terbaca di atas warna segmen di atas.
_TEKS_SEGMEN = ["#FFFFFF", "#0C2B2B", "#2A1C04", "#FFFFFF", "#FFFFFF", "#1B2330"]

# Dipakai bila beberapa lapangan usaha ditampilkan sebagai garis terpisah.
SERI = ["#2a78d6", "#eb6834", "#1baf7a", "#7B61C9", "#e87ba4"]


def warna_segmen(urutan: list[str]) -> dict[str, str]:
    return {s: _WARNA_SEGMEN[i % len(_WARNA_SEGMEN)] for i, s in enumerate(urutan)}


def teks_segmen(urutan: list[str]) -> dict[str, str]:
    return {s: _TEKS_SEGMEN[i % len(_TEKS_SEGMEN)] for i, s in enumerate(urutan)}


# --------------------------------------------------------------------------
# Format angka Indonesia
# --------------------------------------------------------------------------


def idn(x: float, d: int = 1, tanda: bool = False) -> str:
    """1234.5 -> '1.234,5'. Minus memakai tanda minus sebenarnya."""
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "-"
    s = f"{abs(x):,.{d}f}".replace(",", "#").replace(".", ",").replace("#", ".")
    if x < 0 and float(s.replace(".", "").replace(",", ".")) != 0:
        return "−" + s
    return ("+" + s) if tanda and x > 0 else s


def pct(x: float, d: int = 1, tanda: bool = False) -> str:
    return idn(x, d, tanda) + "%"


# --------------------------------------------------------------------------
# Tema bersama
# --------------------------------------------------------------------------


def tema(fig: go.Figure, tinggi: int = 380, legenda: bool = True,
         margin: dict | None = None) -> go.Figure:
    fig.update_layout(
        height=tinggi,
        margin=margin or dict(l=4, r=8, t=8, b=4),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT, size=12, color=W["ink2"]),
        separators=",.",
        showlegend=legenda,
        hoverlabel=dict(bgcolor="white", bordercolor=W["axis"],
                        font=dict(family=FONT, size=12, color=W["ink"])),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="left", x=0,
                    bgcolor="rgba(0,0,0,0)", title_text="", font=dict(size=12)),
    )
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor=W["axis"],
                     ticks="", automargin=True, tickfont=dict(size=12))
    fig.update_yaxes(gridcolor=W["grid"], zeroline=False, linecolor="rgba(0,0,0,0)",
                     ticks="", automargin=True, tickfont=dict(size=12))
    return fig


# --------------------------------------------------------------------------
# Struktur ekonomi
# --------------------------------------------------------------------------


def komposisi_segmen(peran: pd.DataFrame, urutan: list[str], tahun_sorot: int | None = None) -> go.Figure:
    """Kolom bertumpuk: porsi tiap segmen terhadap PDRB per tahun."""
    wn, wt = warna_segmen(urutan), teks_segmen(urutan)
    fig = go.Figure()
    x = [str(t) for t in peran.index]
    for s in urutan:
        if s not in peran.columns:
            continue
        fig.add_bar(
            x=x, y=peran[s].values, name=s,
            marker=dict(color=wn[s], line=dict(color=W["putih"], width=2)),
            text=[pct(v) for v in peran[s].values], textposition="inside",
            insidetextanchor="middle",
            textfont=dict(color=wt[s], size=12), textangle=0,
            hovertemplate="<b>Segmen " + s + "</b><br>Tahun %{x}<br>Porsi terhadap PDRB: %{y:,.2f}%<extra></extra>",
        )
    fig.update_layout(barmode="stack", bargap=0.35)
    tema(fig, 392, margin=dict(l=4, r=8, t=34, b=4))
    fig.update_yaxes(range=[0, 100], ticksuffix="%", dtick=25)
    fig.update_xaxes(type="category", tickmode="array", tickvals=x, ticktext=x)
    return fig


def peta_pohon(nilai: pd.Series, segmen: pd.Series, urutan: list[str]) -> go.Figure:
    """Treemap: luas = porsi lapangan usaha pada satu tahun."""
    wn, wt = warna_segmen(urutan), teks_segmen(urutan)
    ids, label, parent, val, warna, teks = [], [], [], [], [], []
    for s in urutan:
        anggota = [u for u in nilai.index if segmen[u] == s]
        if not anggota:
            continue
        ids.append("seg-" + s); label.append(f"Segmen {s}"); parent.append("")
        val.append(float(nilai[anggota].sum())); warna.append(wn[s]); teks.append(wt[s])
        for u in anggota:
            ids.append(u); label.append(u); parent.append("seg-" + s)
            val.append(float(nilai[u])); warna.append(wn[s]); teks.append(wt[s])
    fig = go.Figure(go.Treemap(
        ids=ids, labels=label, parents=parent, values=val, branchvalues="total",
        marker=dict(colors=warna, line=dict(color=W["putih"], width=2)),
        textfont=dict(family=FONT, color=teks, size=13),
        texttemplate="<b>%{label}</b><br>%{value:,.1f}%",
        textposition="top left",
        hovertemplate="<b>%{label}</b><br>Porsi terhadap PDRB: %{value:,.2f}%<extra></extra>",
        tiling=dict(pad=3), pathbar=dict(visible=False), sort=False,
    ))
    fig.update_layout(uniformtext=dict(minsize=10, mode="hide"))
    return tema(fig, 400, legenda=False, margin=dict(l=0, r=0, t=0, b=0))


def batang_sektor(nilai: pd.Series, segmen: pd.Series, urutan: list[str],
                  judul_hover: str = "Porsi terhadap PDRB") -> go.Figure:
    """Batang horizontal terurut, diwarnai menurut segmen."""
    wn = warna_segmen(urutan)
    urut = nilai.sort_values(ascending=False)
    fig = go.Figure()
    for s in urutan:
        sub = urut[[u for u in urut.index if segmen[u] == s]]
        if sub.empty:
            continue
        fig.add_bar(
            y=sub.index, x=sub.values, orientation="h", name=f"Segmen {s}",
            marker=dict(color=wn[s]),
            text=[pct(v) for v in sub.values], textposition="outside", cliponaxis=False,
            textfont=dict(color=W["ink2"], size=12),
            hovertemplate="<b>%{y}</b><br>" + judul_hover + ": %{x:,.2f}%<extra></extra>",
        )
    fig.update_layout(bargap=0.28)
    tema(fig, 30 * len(urut) + 70, margin=dict(l=4, r=48, t=34, b=4))
    fig.update_yaxes(categoryorder="array", categoryarray=list(urut.index)[::-1], showgrid=False)
    fig.update_xaxes(showgrid=True, gridcolor=W["grid"], ticksuffix="%", rangemode="tozero")
    return fig


def lolipop_selisih(selisih: pd.Series, awal: pd.Series, akhir: pd.Series,
                    t0: int, t1: int) -> go.Figure:
    """Perubahan porsi (poin persentase) antara dua tahun."""
    s = selisih.sort_values()
    warna = [W["biru"] if v >= 0 else W["turun"] for v in s.values]
    fig = go.Figure()
    fig.add_bar(
        y=s.index, x=s.values, orientation="h", width=0.12, marker=dict(color=warna),
        hoverinfo="skip", showlegend=False,
    )
    fig.add_scatter(
        y=s.index, x=s.values, mode="markers+text", showlegend=False,
        marker=dict(color=warna, size=11, line=dict(color=W["putih"], width=2)),
        text=[idn(v, 2, True) for v in s.values],
        textposition=["middle right" if v >= 0 else "middle left" for v in s.values],
        textfont=dict(size=11, color=W["ink2"]),
        customdata=np.c_[awal[s.index].values, akhir[s.index].values],
        hovertemplate=("<b>%{y}</b><br>" + str(t0) + ": %{customdata[0]:,.2f}%<br>"
                       + str(t1) + ": %{customdata[1]:,.2f}%<br>"
                       "Perubahan: %{x:+,.2f} poin persentase<extra></extra>"),
    )
    tema(fig, 26 * len(s) + 50, legenda=False, margin=dict(l=4, r=56, t=6, b=4))
    lim = max(abs(s.min()), abs(s.max())) * 1.35
    fig.update_xaxes(range=[-lim, lim], zeroline=True, zerolinecolor=W["axis"],
                     showgrid=True, gridcolor=W["grid"], ticksuffix=" poin")
    fig.update_yaxes(showgrid=False, categoryorder="array", categoryarray=list(s.index))
    return fig


def garis_banyak(tabel: pd.DataFrame, satuan: str = "%", judul: str = "Porsi") -> go.Figure:
    """Satu garis per lapangan usaha. Kolom tabel = tahun."""
    fig = go.Figure()
    x = [str(t) for t in tabel.columns]
    for i, u in enumerate(tabel.index):
        c = SERI[i % len(SERI)]
        fig.add_scatter(
            x=x, y=tabel.loc[u].values, name=u, mode="lines+markers",
            line=dict(color=c, width=2.4), marker=dict(size=8, color=c, line=dict(color=W["putih"], width=2)),
            hovertemplate="<b>" + u + "</b><br>Tahun %{x}<br>" + judul + ": %{y:,.2f}" + satuan + "<extra></extra>",
        )
    tema(fig, 330, margin=dict(l=4, r=12, t=34, b=4))
    fig.update_yaxes(ticksuffix=satuan)
    fig.update_xaxes(type="category", tickmode="array", tickvals=x, ticktext=x)
    return fig


# --------------------------------------------------------------------------
# Pertumbuhan dan risiko
# --------------------------------------------------------------------------


def peta_panas_tumbuh(ret: pd.DataFrame) -> go.Figure:
    """Pertumbuhan tiap lapangan usaha per tahun. Biru = naik, terakota = turun."""
    urut = ret.mean(axis=1).sort_values(ascending=False)
    z = ret.loc[urut.index]
    skala = [[0.0, "#E27D66"], [0.25, "#F1BFB2"], [0.5, "#F4F7FB"], [0.75, "#B9D3F0"], [1.0, "#6FA6E0"]]
    fig = go.Figure(go.Heatmap(
        z=z.values, x=[str(t) for t in z.columns], y=list(z.index),
        zmid=0, zmin=-12, zmax=12, colorscale=skala, showscale=False,
        xgap=3, ygap=3,
        text=[[idn(v, 1) for v in row] for row in z.values],
        texttemplate="%{text}", textfont=dict(size=12, color=W["ink"]),
        hovertemplate="<b>%{y}</b><br>Tahun %{x}<br>Pertumbuhan: %{z:+,.2f}%<extra></extra>",
    ))
    tema(fig, 28 * len(z) + 60, legenda=False, margin=dict(l=4, r=4, t=4, b=4))
    fig.update_yaxes(autorange="reversed", showgrid=False)
    fig.update_xaxes(side="top", type="category")
    return fig


def _pilih_label(risk: pd.DataFrame, xr: list[float], yr: list[float]) -> set[str]:
    """Pilih titik yang diberi nama tanpa saling menimpa (porsi terbesar didahulukan).

    Titik tanpa nama tetap bisa dibaca lewat tooltip.
    """
    urut = risk.sort_values("Kontribusi_rata2", ascending=False).index
    dipakai: list[tuple[float, float]] = []
    terpilih: set[str] = set()
    for u in urut:
        nx = (risk.loc[u, "Risiko"] - xr[0]) / (xr[1] - xr[0])
        ny = (risk.loc[u, "Imbal_hasil"] - yr[0]) / (yr[1] - yr[0])
        if all(abs(nx - a) > 0.13 or abs(ny - b) > 0.06 for a, b in dipakai):
            dipakai.append((nx, ny))
            terpilih.add(u)
    return terpilih


def sebar_risiko(risk: pd.DataFrame, urutan: list[str], med_r: float, med_s: float) -> go.Figure:
    """Pertumbuhan rata-rata (y) terhadap naik-turunnya pertumbuhan (x).

    Luas titik mengikuti porsi lapangan usaha terhadap PDRB.
    """
    wn = warna_segmen(urutan)
    fig = go.Figure()
    kontr = risk["Kontribusi_rata2"]
    ukuran = 11 + 36 * np.sqrt(kontr / kontr.max())
    xr = [0, float(risk["Risiko"].max()) * 1.12]
    yr = [float(risk["Imbal_hasil"].min()) - 3.4, float(risk["Imbal_hasil"].max()) + 1.8]
    diberi_nama = _pilih_label(risk, xr, yr)
    for s in urutan:
        sub = risk[risk["Segmen"] == s]
        if sub.empty:
            continue
        fig.add_scatter(
            x=sub["Risiko"], y=sub["Imbal_hasil"], mode="markers+text", name=f"Segmen {s}",
            text=[u if u in diberi_nama else "" for u in sub.index], textposition="top center",
            textfont=dict(size=11, color=W["ink2"]),
            marker=dict(color=wn[s], size=ukuran[sub.index], opacity=0.92,
                        line=dict(color=W["putih"], width=2)),
            customdata=np.c_[sub.index, sub["Kontribusi_rata2"], sub["VaR95_SDPP"], sub["Profil_RR"]],
            hovertemplate=("<b>%{customdata[0]}</b><br>Pertumbuhan rata-rata: %{y:+,.2f}%"
                           "<br>Naik-turun pertumbuhan: %{x:,.2f}"
                           "<br>Porsi PDRB rata-rata: %{customdata[1]:,.2f}%"
                           "<br>%{customdata[3]}<extra></extra>"),
        )
    fig.add_vline(x=med_r, line=dict(color=W["axis"], width=1.2, dash="dot"))
    fig.add_hline(y=med_s, line=dict(color=W["axis"], width=1.2, dash="dot"))
    kw = dict(showarrow=False, font=dict(size=12, color=W["muted"]))
    fig.add_annotation(x=xr[0], y=yr[1], text="Tumbuh cepat, stabil", xanchor="left", yanchor="top", **kw)
    fig.add_annotation(x=xr[1], y=yr[1], text="Tumbuh cepat, bergejolak", xanchor="right", yanchor="top", **kw)
    fig.add_annotation(x=xr[0], y=yr[0], text="Tumbuh lambat, stabil", xanchor="left", yanchor="bottom", **kw)
    fig.add_annotation(x=xr[1], y=yr[0], text="Tumbuh lambat, bergejolak", xanchor="right", yanchor="bottom",
                       showarrow=False, font=dict(size=12, color=W["risiko"]))
    tema(fig, 540, margin=dict(l=4, r=8, t=34, b=4))
    fig.update_xaxes(range=xr, title="Seberapa naik-turun pertumbuhannya (simpangan baku, poin)",
                     showgrid=False, title_font=dict(size=12, color=W["muted"]))
    fig.update_yaxes(range=yr, title="Pertumbuhan rata-rata per tahun (%)", ticksuffix="%",
                     title_font=dict(size=12, color=W["muted"]))
    return fig


def batang_var(var: pd.DataFrame) -> go.Figure:
    """VaR 95% per kelompok dengan dua cara hitung."""
    fig = go.Figure()
    kel = list(var.index)
    spesifikasi = [("VaR95_HS", "Simulasi historis", W["navy"]),
                   ("VaR95_SDPP", "Rata-rata dikurangi 1,645 simpangan baku", "#9FB1C6")]
    for kol, nama, c in spesifikasi:
        fig.add_bar(
            x=kel, y=var[kol].values, name=nama, marker=dict(color=c),
            text=[idn(v, 1) for v in var[kol].values], textposition="outside",
            cliponaxis=False, textfont=dict(size=11, color=W["ink2"]),
            hovertemplate="<b>%{x}</b><br>" + nama + ": %{y:,.2f}%<extra></extra>",
        )
    fig.update_layout(barmode="group", bargap=0.35, bargroupgap=0.08)
    tema(fig, 340, margin=dict(l=4, r=8, t=40, b=4))
    ymin = float(var[["VaR95_HS", "VaR95_SDPP"]].min().min())
    ymax = float(var[["VaR95_HS", "VaR95_SDPP"]].max().max())
    fig.update_yaxes(range=[ymin * 1.25 - 1, ymax * 1.4 + 1], ticksuffix="%",
                     zeroline=True, zerolinecolor=W["axis"])
    return fig


def garis_usaha(nilai: pd.Series, rata2: float, nama: str) -> go.Figure:
    """Pertumbuhan satu lapangan usaha dari tahun ke tahun."""
    x = [str(t) for t in nilai.index]
    warna = [W["risiko"] if v < 0 else W["biru"] for v in nilai.values]
    fig = go.Figure()
    fig.add_bar(x=x, y=nilai.values, marker=dict(color=warna), width=0.5, showlegend=False,
                text=[idn(v, 1, True) for v in nilai.values], textposition="outside",
                cliponaxis=False, textfont=dict(size=12, color=W["ink2"]),
                hovertemplate="Tahun %{x}<br>Pertumbuhan: %{y:+,.2f}%<extra></extra>")
    fig.add_hline(y=rata2, line=dict(color=W["ink2"], width=1.4, dash="dash"))
    tema(fig, 300, legenda=False, margin=dict(l=4, r=8, t=24, b=4))
    lo, hi = min(0, float(nilai.min())), max(0, float(nilai.max()))
    pad = (hi - lo) * 0.18 + 0.5
    fig.update_yaxes(range=[lo - pad, hi + pad], ticksuffix="%", zeroline=True, zerolinecolor=W["axis"])
    fig.update_xaxes(type="category")
    return fig


def batang_andil(andil: pd.Series) -> go.Figure:
    s = andil.sort_values()
    warna = [W["risiko"] if v < 0 else W["biru"] for v in s.values]
    fig = go.Figure(go.Bar(
        y=s.index, x=s.values, orientation="h", marker=dict(color=warna),
        text=[idn(v, 2, True) for v in s.values], textposition="outside", cliponaxis=False,
        textfont=dict(size=11, color=W["ink2"]),
        hovertemplate="<b>%{y}</b><br>Andil: %{x:+,.2f} poin persentase<extra></extra>",
    ))
    tema(fig, 26 * len(s) + 50, legenda=False, margin=dict(l=4, r=56, t=6, b=4))
    lim = max(abs(s.min()), abs(s.max())) * 1.3
    fig.update_xaxes(range=[-lim, lim], zeroline=True, zerolinecolor=W["axis"],
                     showgrid=True, gridcolor=W["grid"])
    fig.update_yaxes(showgrid=False)
    return fig


# --------------------------------------------------------------------------
# Gabungan dan metode
# --------------------------------------------------------------------------


def matriks_silang(silang: pd.DataFrame) -> go.Figure:
    """Jumlah lapangan usaha pada tiap pertemuan segmen dan profil."""
    z = silang.values
    teks = [[str(int(v)) if v else "" for v in row] for row in z]
    fig = go.Figure(go.Heatmap(
        z=z, x=list(silang.columns), y=list(silang.index), xgap=4, ygap=4,
        colorscale=[[0, "#EAF0F8"], [0.001, "#D3E2F4"], [1, "#6FA6E0"]], showscale=False,
        text=teks, texttemplate="%{text}", textfont=dict(size=20, color=W["ink"], family=FONT),
        hovertemplate="Segmen %{y}<br>%{x}<br>%{z} lapangan usaha<extra></extra>",
    ))
    tema(fig, 300, legenda=False, margin=dict(l=4, r=4, t=4, b=4))
    fig.update_yaxes(autorange="reversed", showgrid=False)
    fig.update_xaxes(side="top", showgrid=False, tickfont=dict(size=12), tickangle=0,
                     tickmode="array", tickvals=list(silang.columns),
                     ticktext=[c.replace(", ", ",<br>") for c in silang.columns])
    return fig


def evaluasi_klaster(ev: pd.DataFrame, k: int) -> go.Figure:
    warna = [W["navy"] if i == k else "#9FB1C6" for i in ev.index]
    fig = go.Figure(go.Bar(
        x=[f"k = {i}" for i in ev.index], y=ev["Silhouette"].values, marker=dict(color=warna),
        text=[idn(v, 2) for v in ev["Silhouette"].values], textposition="outside", cliponaxis=False,
        hovertemplate="%{x}<br>Silhouette: %{y:,.3f}<extra></extra>",
    ))
    tema(fig, 280, legenda=False, margin=dict(l=4, r=8, t=24, b=4))
    fig.update_yaxes(range=[0, 1.05], title="Skor silhouette")
    return fig


def silhouette_usaha(sil: pd.Series, segmen: pd.Series, urutan: list[str]) -> go.Figure:
    wn = warna_segmen(urutan)
    s = sil.sort_values()
    fig = go.Figure(go.Bar(
        y=s.index, x=s.values, orientation="h", marker=dict(color=[wn[segmen[u]] for u in s.index]),
        hovertemplate="<b>%{y}</b><br>Silhouette: %{x:,.3f}<extra></extra>",
    ))
    tema(fig, 22 * len(s) + 40, legenda=False, margin=dict(l=4, r=8, t=6, b=4))
    fig.update_xaxes(range=[min(0, s.min()) - 0.05, 1], showgrid=True, gridcolor=W["grid"])
    fig.update_yaxes(showgrid=False)
    return fig
