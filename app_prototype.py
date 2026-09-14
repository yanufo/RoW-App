import streamlit as st

LOGO_ICON = "images/ST_logo_icon.png"
LOGO_FULL = "images/ST_logo_full.png"

st.logo(LOGO_FULL, icon_image=LOGO_ICON)

st.set_page_config(
    page_title="App Prototype",
    page_icon="🛩️",
    layout="wide",
)

home = st.Page(
    "pages/home.py",
    title="Home",
    icon="🏠",
)

row_reports = st.Page(
    "pages/Row_report.py",
    title="Right-of-Way Reports",
    icon="⚡️",
)

# solar_reports = st.Page(
#     "pages/Solar_report.py",
#     title="Solar Reports",
#     icon="☀️",
# )

pg = st.navigation([
    home,
    row_reports
])

pg.run()