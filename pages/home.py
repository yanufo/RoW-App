import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

from sql_tool.queries import get_all_reports
from ui.drone_model import display_3d_drone
from ui.upload import show_new_report
from ui.usagi_model import display_3d_usagi
from ui.drone_model import display_3d_drone
import base64

# ============================================================
# Hide Streamlit Deploy button
# ============================================================

st.markdown("""
<style>
[data-testid="stAppDeployButton"] {
    display: none;
}
</style>
""", unsafe_allow_html=True)


# ============================================================
# New Report
# ============================================================
st.title("Inspection Report Generation")

show_new_report()

# ============================================================
# 3D King Usagi Viewer
# ============================================================

# display_3d_usagi()



# ============================================================
# 3D Drone Viewer
# ============================================================

display_3d_drone()


# # ============================================================
# # Database
# # ============================================================

# db_report = get_all_reports()

# df = pd.DataFrame(db_report)


# # ============================================================
# # Session State
# # ============================================================

# if "popover_open" not in st.session_state:
#     st.session_state.popover_open = False

# if "confirm_cancel" not in st.session_state:
#     st.session_state.confirm_cancel = False


# # ============================================================
# # UAV IDs
# # ============================================================

# if not df.empty and "uav_id" in df.columns:

#     uav_ids = sorted(
#         df["uav_id"]
#         .dropna()
#         .unique()
#         .tolist()
#     )

# else:

#     uav_ids = []


