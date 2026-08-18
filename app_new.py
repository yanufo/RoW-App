import os

import streamlit as st

from ui.new_report import show_new_report
from ui.report_table import show_report_table
from ui.preview import preview_dialog


# --------------------------------------------------
# Configuration
# --------------------------------------------------

st.set_page_config(
    page_title="RoW Inspection Reports",
    layout="wide",
)

st.title("RoW Inspection Reports")


# BASE_DIR = "/home/hj/Downloads/input"
# OUTPUT_DIR = "/home/hj/Downloads/output"

# os.makedirs(BASE_DIR, exist_ok=True)
# os.makedirs(OUTPUT_DIR, exist_ok=True)


# --------------------------------------------------
# Session state
# --------------------------------------------------

if "preview_report_id" not in st.session_state:
    st.session_state.preview_report_id = None

if "reports" not in st.session_state:
    st.session_state.reports = []

if "selected" not in st.session_state:
    st.session_state.selected = {}

if "form_key" not in st.session_state:
    st.session_state.form_key = 0

if "popover_open" not in st.session_state:
    st.session_state.popover_open = True

if "confirm_cancel" not in st.session_state:
    st.session_state.confirm_cancel = False


# --------------------------------------------------
# New Report Button
# --------------------------------------------------

show_new_report()


st.divider()


# --------------------------------------------------
# Report Table
# --------------------------------------------------

show_report_table()


# --------------------------------------------------
# Preview
# --------------------------------------------------

if st.session_state.preview_report_id is not None:

    preview_id = (
        st.session_state.preview_report_id
    )

    st.session_state.preview_report_id = None

    preview_dialog(preview_id)
