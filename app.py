"""Titik masuk dashboard: pengaturan halaman, gaya, filter, dan navigasi."""

from __future__ import annotations

import streamlit as st

from src import pipeline, ui

st.set_page_config(
    page_title="PDRB Kabupaten Bojonegoro",
    page_icon=":material/insights:",
    layout="wide",
    initial_sidebar_state="auto",
)
ui.pasang_gaya()
if ui.LOGO.exists():
    st.logo(str(ui.LOGO), size="large")

pipeline.pasang_filter()

HALAMAN = [
    st.Page("pages/0_Ringkasan.py", title="Ringkasan", icon=":material/space_dashboard:", default=True),
    st.Page("pages/1_Struktur_Ekonomi.py", title="Struktur ekonomi", icon=":material/account_tree:"),
    st.Page("pages/2_Pertumbuhan_dan_Risiko.py", title="Pertumbuhan dan risiko",
            icon=":material/show_chart:"),
    st.Page("pages/3_Peta_Gabungan.py", title="Peta gabungan", icon=":material/grid_view:"),
    st.Page("pages/4_Kesimpulan.py", title="Kesimpulan", icon=":material/fact_check:"),
    st.Page("pages/5_Data_dan_Metode.py", title="Data dan metode", icon=":material/menu_book:"),
]

st.navigation(HALAMAN).run()
