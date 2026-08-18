import base64
import io
import os
import shutil
import uuid
import zipfile
from datetime import datetime, timezone

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import mysql.connector as mysql

from database.connection import get_connection


conn = get_connection()
cursor = conn.cursor()


st.set_page_config(page_title="RoW Inspection Reports", layout="wide")

st.title("RoW Inspection Reports")
#BASE_DIR = "/data/EGAT/inspections/row/input"
BASE_DIR = "/home/hj/Downloads/input"
#OUTPUT_DIR = "/data/EGAT/inspections/row/output"
OUTPUT_DIR = "/home/hj/Downloads/output"
os.makedirs(BASE_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True) 


# ---------------------------------------------------------------------------
# Session state setup
# ---------------------------------------------------------------------------
if "reports" not in st.session_state:
    st.session_state.reports = []  # list of dicts, newest first

if "selected" not in st.session_state:
    st.session_state.selected = {}

if "form_key" not in st.session_state:
    st.session_state.form_key = 0

if "popover_open" not in st.session_state:
    st.session_state.popover_open = True

if "confirm_cancel" not in st.session_state:
    st.session_state.confirm_cancel = False

if "preview_report_id" not in st.session_state:
    st.session_state.preview_report_id = None

if "preview_seek" not in st.session_state:
    st.session_state.preview_seek = 0


def inject_preview_drawer_css():
    """
    Best-effort CSS to turn Streamlit's centered st.dialog into a right-side
    drawer occupying ~2/3 of the viewport width and the full height.

    CAVEAT: this relies on Streamlit's *undocumented* internal dialog DOM
    (the data-testid="stDialog" overlay + its child panel). It was written
    against Streamlit >= 1.35 and MAY BREAK on other versions. If the drawer
    stops sliding in from the side after a Streamlit upgrade, open browser
    devtools, inspect the dialog element, and update the selectors below.
    """
    st.markdown(
        """
        <style>
        div[data-testid="stDialog"] {
            align-items: stretch !important;
            justify-content: flex-end !important;
        }
        div[data-testid="stDialog"] > div {
            width: 66vw !important;
            max-width: 66vw !important;
            height: 100vh !important;
            max-height: 100vh !important;
            margin: 0 !important;
            border-radius: 0 !important;
            animation: rowPreviewSlideIn 0.22s ease-out;
        }
        @keyframes rowPreviewSlideIn {
            from { transform: translateX(100%); }
            to   { transform: translateX(0); }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def format_mmss(seconds: int) -> str:
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"


STATUS_COLORS = {
    "Queued": "#1E88E5",      # blue
    "Processing": "#FB8C00",  # orange
    "Completed": "#43A047",   # green
    "Failed": "#E53935",      # red
}
STATUS_OPTIONS = list(STATUS_COLORS.keys())


def status_badge_html(status: str) -> str:
    color = STATUS_COLORS.get(status, "#757575")
    return (
        f'<span style="background-color:{color}; color:white; padding:3px 12px; '
        f'border-radius:12px; font-size:0.85em; font-weight:600; white-space:nowrap;">'
        f'{status}</span>'
    )


def make_filename(uav_id: str, inspection_dt: datetime, safe_clearance, clearance_height, sensitivity) -> str:
    date_str = inspection_dt.strftime("%Y-%m-%d")
    time_str = inspection_dt.strftime("%H%M%S")
    return f"{uav_id}_{date_str}_{time_str}_{safe_clearance}m_{clearance_height}m_{sensitivity}"


def generate_report_html(report: dict) -> bytes:
    """Placeholder report generator. Replace with a call to your real AI
    engine / report pipeline, which should return the actual HTML bytes."""
    html = f"""
    <html>
    <head><meta charset="utf-8"><title>{report['Filename']}</title></head>
    <body style="font-family: sans-serif; padding: 24px;">
        <h1>RoW Inspection Report</h1>
        <table style="border-collapse: collapse;">
            <tr><td style="padding:4px 12px;"><b>Filename</b></td><td>{report['Filename']}</td></tr>
            <tr><td style="padding:4px 12px;"><b>Source video</b></td><td>{report['video_name']}</td></tr>
            <tr><td style="padding:4px 12px;"><b>Source SRT</b></td><td>{report['srt_name']}</td></tr>
            <tr><td style="padding:4px 12px;"><b>UAV ID</b></td><td>{report['UAV ID']}</td></tr>
            <tr><td style="padding:4px 12px;"><b>Inspection Date Time</b></td><td>{report['Inspection Date Time']}</td></tr>
            <tr><td style="padding:4px 12px;"><b>Safe Clearance Distance (m)</b></td><td>{report['Safe Clearance Distance (m)']}</td></tr>
            <tr><td style="padding:4px 12px;"><b>Clearance Height (m)</b></td><td>{report['Clearance Height (m)']}</td></tr>
            <tr><td style="padding:4px 12px;"><b>Sensitivity</b></td><td>{report['Sensitivity']}</td></tr>
        </table>
        <p style="margin-top:24px; color:#888;">Placeholder report — wire this up to the real inspection pipeline output.</p>
    </body>
    </html>
    """
    return html.encode("utf-8")



def video_player(video_bytes, timestamps):

    video_b64 = base64.b64encode(video_bytes).decode()

    timestamp_buttons = ""

    for i, ts in enumerate(sorted(timestamps, key=lambda t: t["seconds"])):
        seconds = ts["seconds"]
        label = ts["label"]

        timestamp_buttons += f"""
        <button
            onclick="seekVideo({seconds})"
            style="
                display:block;
                width:100%;
                margin:5px 0;
                padding:8px;
                text-align:left;
                border:1px solid #ddd;
                border-radius:6px;
                background:#f8f9fa;
                cursor:pointer;
            "
        >
            ⏱ {format_mmss(seconds)} — {label}
        </button>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <body>

        <video
            id="videoPlayer"
            controls
            width="100%"
            style="max-height:500px;"
        >
            <source
                src="data:video/mp4;base64,{video_b64}"
                type="video/mp4"
            >
        </video>

        <h4>Critical Timestamps</h4>

        {timestamp_buttons}

        <script>
            function seekVideo(seconds) {{
                const video = document.getElementById("videoPlayer");

                video.currentTime = seconds;
                video.play();
            }}
        </script>

    </body>
    </html>
    """

    components.html(
        html,
        height=700,
        scrolling=True,
    )

   
# ---------------------------------------------------------------------------
# Preview popup (side drawer, ~2/3 width) with Report / Processed Video tabs
# ---------------------------------------------------------------------------
# Status,
# Filepath,
# HTML_path
@st.dialog("Preview", width="large")
def preview_dialog(report_id):

    inject_preview_drawer_css()

    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            id,
            Filename,
            UAV_ID,
            Inspection_Datetime,
            Safe_Clearance_Distance,
            Clearance_Height,
            Sensitivity
        FROM row_database.file_detail
        WHERE id = %s
    """, (report_id,))

    report = cursor.fetchone()
    cursor.close()

    if report is None:
        st.error("Report not found.")
        return

    # --------------------------------------------------
    # Reset video position when opening another report
    # --------------------------------------------------

    if "preview_seek" not in st.session_state:
        st.session_state.preview_seek = 0

    st.caption(report["Filename"])

    # --------------------------------------------------
    # Check status
    # --------------------------------------------------

    # if report["Status"] != "Completed":
    #     st.info(
    #         f"Report status: {report['Status']} "
    #         "— no preview available yet."
    #     )
    #     return

    # --------------------------------------------------
    # Tabs
    # --------------------------------------------------

    tab_report, tab_video = st.tabs(
        ["📄 Report", "🎬 Processed Video"]
    )

    # ==================================================
    # REPORT
    # ==================================================

    with tab_report:

        html_path = report["HTML_path"]

        if os.path.exists(html_path):

            with open(html_path, "rb") as f:
                html_bytes = f.read()

            components.html(
                html_bytes.decode(
                    "utf-8",
                    errors="replace"
                ),
                height=550,
                scrolling=True,
            )

            st.download_button(
                "⬇ Download report",
                data=html_bytes,
                file_name=report["Filename"] + ".html",
                mime="text/html",
                key=f"dl_report_{report_id}",
            )

        else:
            st.warning("Report HTML file not found.")

    # ==================================================
    # VIDEO
    # ==================================================

    with tab_video:

        video_path = report["Filepath"]

        if os.path.exists(video_path):

            with open(video_path, "rb") as f:
                video_bytes = f.read()

            timestamps = report.get(
                "critical_timestamps",
                []
            )

            video_player(
                video_bytes,
                timestamps
            )

            st.download_button(
                "⬇ Download video",
                data=video_bytes,
                file_name=report["Filename"] + ".mp4",
                mime="video/mp4",
                key=f"dl_video_{report_id}",
            )

        else:
            st.warning("Processed video file not found.")



# ---------------------------------------------------------------------------
# Header + New Report popover
# ---------------------------------------------------------------------------
if st.session_state.popover_open:

    with st.popover("➕ New Report"):

        st.write("NEW INSPECTION REPORT")

        if st.session_state.confirm_cancel:

            # ==================================================
            # CONFIRMATION SCREEN
            # ==================================================

            st.warning(
                "Discard this report? Uploaded files and entered values will be lost."
            )

            yes_col, no_col = st.columns(2)

            if yes_col.button(
                "Yes, cancel",
                key="confirm_yes",
                use_container_width=True
            ):

                st.session_state.confirm_cancel = False

                # Reset form
                st.session_state.form_key += 1

                # Remove saved backup
                st.session_state.cancel_backup = {}

                st.rerun()

            if no_col.button(
                "No, go back",
                key="confirm_no",
                use_container_width=True
            ):

                backup = st.session_state.cancel_backup

                # Restore widget state
                st.session_state[f"video_{fk}"] = backup["video"]
                st.session_state[f"srt_{fk}"] = backup["srt"]
                st.session_state[f"uav_{fk}"] = backup["uav"]
                st.session_state[f"sc_{fk}"] = backup["safe_clearance"]
                st.session_state[f"ch_{fk}"] = backup["clearance_height"]
                st.session_state[f"dt_{fk}"] = backup["inspection_dt"]
                st.session_state[f"sens_{fk}"] = backup["sensitivity"]

                st.session_state.confirm_cancel = False

                st.rerun()

        else:

            # ==================================================
            # NORMAL FORM
            # ==================================================

            fk = st.session_state.form_key

            uploaded_video = st.file_uploader(
                "Choose a MP4 file",
                type="mp4",
                key=f"video_{fk}"
            )

            uploaded_srt = st.file_uploader(
                "Choose a SRT file",
                type="srt",
                key=f"srt_{fk}"
            )

            uav = ["15005", "16001"]

            selected_id = st.selectbox(
                "UAV ID",
                uav,
                index=None,
                placeholder="Select UAV ID",
                key=f"uav_{fk}"
            )

            safe_clearance = st.number_input(
                "Safe Clearance Distance (m)",
                min_value=0,
                max_value=200,
                step=1,
                value=None,
                key=f"sc_{fk}"
            )

            clearance_height = st.number_input(
                "Clearance Height (m)",
                min_value=0,
                max_value=200,
                step=1,
                value=None,
                key=f"ch_{fk}"
            )

            inspection_dt = st.datetime_input(
                "Inspection Date Time",
                value=None,
                key=f"dt_{fk}"
            )

            sensitivity = st.slider(
                "Sensitivity",
                min_value=1,
                max_value=10,
                key=f"sens_{fk}"
            )

            # --------------------------------------------------
            # Buttons
            # --------------------------------------------------

            col1, col2 = st.columns(2)

            cancel = col1.button(
                "Cancel",
                key=f"cancel_{fk}",
                use_container_width=True
            )

            start = col2.button(
                "Start Processing",
                key=f"start_{fk}",
                use_container_width=True,
                type="primary",
            )

            # --------------------------------------------------
            # Cancel
            # --------------------------------------------------

            if cancel:

                # Save everything BEFORE removing the form
                st.session_state.cancel_backup = {
                    "video": uploaded_video,
                    "srt": uploaded_srt,
                    "uav": selected_id,
                    "safe_clearance": safe_clearance,
                    "clearance_height": clearance_height,
                    "inspection_dt": inspection_dt,
                    "sensitivity": sensitivity,
                }

                st.session_state.confirm_cancel = True

                st.rerun()

            if start:
                
                #Check if database contain any data thats processing.
                cursor = conn.cursor()
                cursor.execute("""SELECT EXISTS (SELECT 1 FROM row_database.file_detail WHERE Status = 'Processing')""")
                processing_exist = cursor.fetchone()[0]
                if processing_exist:
                    status = 'Queing'
                else:
                    status = 'Processing'
                report_id = str(uuid.uuid4())
                inspection_dt_utc = inspection_dt.replace(tzinfo=timezone.utc)
                filename = make_filename(selected_id, inspection_dt_utc, safe_clearance, clearance_height, sensitivity)
                cursor = conn.cursor()
                cursor.execute("""INSERT INTO row_database.file_detail(Filename,UAV_ID,Inspection_Datetime,Safe_Clearance_Distance,Clearance_Height,Sensitivity,Status) VALUES (%s,%s,%s,%s,%s,%s,%s)""",(filename,selected_id,inspection_dt,safe_clearance,clearance_height,sensitivity,status))
                conn.commit()      
                report_db_id = cursor.lastrowid
                #cursor.execute("""INSERT INTO row_database.Video_file(Filename,Filepath,HTML_path) VALUES (%s,%s,%s)""",(filename,f"{OUTPUT_DIR}/{filename}.mp4",f"{OUTPUT_DIR}/{filename}.html"))
                #shutil.move("/home/gve/Downloads/videoplayback.mp4", f"/home/gve/Documents/EGAT/EGAT/sample_data/{filename}.mp4")
                
                report = {
                    "id": report_id,
                    "Filename": filename,
                    "UAV ID": selected_id,
                    "Inspection Date Time": inspection_dt_utc,
                    "Safe Clearance Distance (m)": str(safe_clearance),
                    "Clearance Height (m)": str(clearance_height),
                    "Sensitivity": str(sensitivity),
                    "Status": "Completed",
                    "video_name": uploaded_video.name,
                    "srt_name": uploaded_srt.name,
                    "video_bytes": uploaded_video.getvalue(),
                    "srt_bytes": uploaded_srt.getvalue(),
                    # Placeholder events — replace with the actual detected
                    # timestamps (e.g. vegetation encroachment, clearance
                    # violations) returned by your AI engine / report pipeline.
                    "critical_timestamps": [
                        {"seconds": 5, "label": "Vegetation encroachment"},
                        {"seconds": 18, "label": "Clearance violation"},
                        {"seconds": 34, "label": "Optical flow anomaly"},
                    ],
                }

                # Simulate processing completing immediately. For a real
                # async pipeline: set Status="Queued"/"Processing" here,
                # insert the row, and flip it to "Completed" (generating
                # html_bytes then) once your engine actually finishes.
                # report["html_bytes"] = generate_report_html(report)

                # #If the process failed
                # if not report["html_bytes"]:
                #     status = 'failed'
                # else:
                #     status = 'Completed'
                import subprocess
                subprocess.Popen([
                    "python",
                    "/path/to/trigger_test.py",
                    "Processing",
                    (report_db_id),
                ])

                #Once the process completed

                
                cursor = conn.cursor()
                cursor.execute("""UPDATE row_database.file_detail SET STATUS = %s WHERE id = %s""",(status,report_db_id))
                conn.commit()  

                st.session_state.reports.insert(0, report)
                st.session_state.selected[report_id] = False
                st.session_state.form_key += 1     # reset form fields
                st.session_state.popover_open = False  # force popover closed
                st.success(f"Report '{filename}' created.")
                st.rerun()
else:
    if st.button("➕ New Report"):
        st.session_state.popover_open = True
        st.rerun()

st.divider()

if not st.session_state.reports:
    st.info("No reports yet. Click **New Report** to upload media and generate one.")
    st.stop()


cursor = conn.cursor(dictionary=True)

cursor.execute("""
    SELECT
        id,
        Filename,
        UAV_ID,
        Inspection_Datetime,
        Safe_Clearance_Distance,
        Clearance_Height,
        Sensitivity,
        Status
    FROM row_database.file_detail
""")

db_reports = cursor.fetchall()
cursor.close()

df = pd.DataFrame(db_reports)

# ---------------------------------------------------------------------------
# Prepare database dataframe
# ---------------------------------------------------------------------------

df["Inspection_Datetime"] = pd.to_datetime(
    df["Inspection_Datetime"]
)

# ---------------------------------------------------------------------------
# Search + Filters & Sort
# ---------------------------------------------------------------------------

search_term = st.text_input(
    "🔍 Search filename",
    placeholder="Type part of a filename..."
)

# ---------------------------------------------------------------------------
# Available filter values FROM DATABASE
# ---------------------------------------------------------------------------

all_uav_ids = sorted(
    df["UAV_ID"]
    .dropna()
    .unique()
    .tolist()
)

all_dates = df["Inspection_Datetime"].dt.date

min_date = all_dates.min()
max_date = all_dates.max()


# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------

with st.expander("Filters & Sort"):

    fc1, fc2, fc3 = st.columns(3)

    uav_filter = fc1.multiselect(
        "UAV ID",
        options=all_uav_ids,
        default=all_uav_ids,
    )

    status_filter = fc2.multiselect(
        "Status",
        options=STATUS_OPTIONS,
        default=STATUS_OPTIONS,
    )

    date_range = fc3.date_input(
        "Inspection Date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    fc4, fc5, fc6 = st.columns(3)

    safe_range = fc4.slider(
        "Safe Clearance Distance (m)",
        min_value=0,
        max_value=200,
        value=(0, 200),
    )

    height_range = fc5.slider(
        "Clearance Height (m)",
        min_value=0,
        max_value=200,
        value=(0, 200),
    )

    sens_range = fc6.slider(
        "Sensitivity",
        min_value=1,
        max_value=10,
        value=(1, 10),
    )

    fc7, fc8 = st.columns(2)

    sort_by = fc7.selectbox(
        "Sort by",
        options=[
            "Filename",
            "UAV ID",
            "Inspection Date Time",
            "Safe Clearance Distance (m)",
            "Clearance Height (m)",
            "Sensitivity",
            "Status",
        ],
        index=2,
    )

    sort_order = fc8.radio(
        "Order",
        options=["Descending", "Ascending"],
        horizontal=True,
    )


# ---------------------------------------------------------------------------
# Normalize date range
# ---------------------------------------------------------------------------

if isinstance(date_range, tuple) and len(date_range) == 2:

    date_start, date_end = date_range

else:

    date_start = min_date
    date_end = max_date


# ---------------------------------------------------------------------------
# Apply filters
# ---------------------------------------------------------------------------

filtered_df = df.copy()


# --------------------------------------------------
# Filename
# --------------------------------------------------

if search_term:
    filtered_df = filtered_df[
        filtered_df["Filename"].str.contains(
            search_term,
            case=False,
            na=False
        )
    ]


# --------------------------------------------------
# UAV
# --------------------------------------------------

filtered_df = filtered_df[
    filtered_df["UAV_ID"].isin(uav_filter)
]


# --------------------------------------------------
# Status
# --------------------------------------------------

filtered_df = filtered_df[
    filtered_df["Status"].isin(status_filter)
]


# --------------------------------------------------
# Date
# --------------------------------------------------

filtered_df = filtered_df[
    filtered_df["Inspection_Datetime"].dt.date.between(
        date_start,
        date_end
    )
]


# --------------------------------------------------
# Safe Clearance
# --------------------------------------------------

filtered_df = filtered_df[
    filtered_df["Safe_Clearance_Distance"].between(
        safe_range[0],
        safe_range[1]
    )
]


# --------------------------------------------------
# Clearance Height
# --------------------------------------------------

filtered_df = filtered_df[
    filtered_df["Clearance_Height"].between(
        height_range[0],
        height_range[1]
    )
]


# --------------------------------------------------
# Sensitivity
# --------------------------------------------------

filtered_df = filtered_df[
    filtered_df["Sensitivity"].between(
        sens_range[0],
        sens_range[1]
    )
]


# ---------------------------------------------------------------------------
# Sort
# ---------------------------------------------------------------------------

SORT_COLUMNS = {

    "Filename":
        "Filename",

    "UAV ID":
        "UAV_ID",

    "Inspection Date Time":
        "Inspection_Datetime",

    "Safe Clearance Distance (m)":
        "Safe_Clearance_Distance",

    "Clearance Height (m)":
        "Clearance_Height",

    "Sensitivity":
        "Sensitivity",

    "Status":
        "Status",
}


filtered_df = filtered_df.sort_values(
    by=SORT_COLUMNS[sort_by],
    ascending=(sort_order == "Ascending"),
)


# ---------------------------------------------------------------------------
# Result count
# ---------------------------------------------------------------------------

st.caption(
    f"Showing {len(filtered_df)} of {len(df)} report(s)."
)


# ---------------------------------------------------------------------------
# No results
# ---------------------------------------------------------------------------

if filtered_df.empty:

    st.info(
        "No reports match the current search/filters."
    )

    st.stop()


# ---------------------------------------------------------------------------
# Table header
# ---------------------------------------------------------------------------

COL_WEIGHTS = [
    0.4,
    3,
    0.7,
    1.8,
    1.5,
    1.3,
    0.9,
    1.1,
]

(
    col_check,
    col_name,
    col_uav,
    col_time,
    col_safe,
    col_height,
    col_sens,
    col_status,
) = st.columns(COL_WEIGHTS)


col_check.markdown("**Select**")
col_name.markdown("**Filename**")
col_uav.markdown("**UAV ID**")
col_time.markdown("**Inspection Date Time**")
col_safe.markdown("**Safe Clearance (m)**")
col_height.markdown("**Clearance Height (m)**")
col_sens.markdown("**Sensitivity**")
col_status.markdown("**Status**")

# ---------------------------------------------------------------------------
# Table rows
# ---------------------------------------------------------------------------

st.markdown("""
<style>
.black-text {
    color: black !important;
}
</style>
""", unsafe_allow_html=True)


# ============================================================
# Preview callback
# ============================================================

def open_preview(rid):
    st.session_state.preview_report_id = rid


# ============================================================
# Display filtered rows
# ============================================================

for _, report in filtered_df.iterrows():

    rid = report["id"]

    (
        c_check,
        c_name,
        c_uav,
        c_time,
        c_safe,
        c_height,
        c_sens,
        c_status,
    ) = st.columns(COL_WEIGHTS)


    # --------------------------------------------------
    # Checkbox
    # --------------------------------------------------

    checked = c_check.checkbox(
        "select",
        value=st.session_state.selected.get(rid, False),
        key=f"chk_{rid}",
        label_visibility="collapsed",
    )

    st.session_state.selected[rid] = checked


    # --------------------------------------------------
    # Filename button
    # --------------------------------------------------

    c_name.button(
        report["Filename"],
        key=f"btn_{rid}",
        use_container_width=True,
        on_click=open_preview,
        args=(rid,),
    )


    # --------------------------------------------------
    # Other columns
    # --------------------------------------------------

    inspection_time = report["Inspection_Datetime"]

    c_uav.markdown(
        f'<span class="black-text">{report["UAV_ID"]}</span>',
        unsafe_allow_html=True,
    )

    c_time.markdown(
        f'<span class="black-text">'
        f'{inspection_time.strftime("%Y-%m-%d %H:%M:%S")}'
        f'</span>',
        unsafe_allow_html=True,
    )

    c_safe.markdown(
        f'<span class="black-text">'
        f'{report["Safe_Clearance_Distance"]}'
        f'</span>',
        unsafe_allow_html=True,
    )

    c_height.markdown(
        f'<span class="black-text">'
        f'{report["Clearance_Height"]}'
        f'</span>',
        unsafe_allow_html=True,
    )

    c_sens.markdown(
        f'<span class="black-text">'
        f'{report["Sensitivity"]}'
        f'</span>',
        unsafe_allow_html=True,
    )

    # IMPORTANT: use the actual status
    c_status.markdown(
        status_badge_html(report["Status"]),
        unsafe_allow_html=True,
    )


# ============================================================
# Open Preview
# ============================================================

if st.session_state.preview_report_id is not None:

    preview_id = st.session_state.preview_report_id

    # Consume the request BEFORE opening the dialog
    st.session_state.preview_report_id = None

    preview_dialog(preview_id)


st.divider()

# ---------------------------------------------------------------------------
# Download selected reports (selection persists across filters)
# ---------------------------------------------------------------------------
selected_ids = [rid for rid, is_sel in st.session_state.selected.items() if is_sel]
selected_reports = [r for r in st.session_state.reports if r["id"] in selected_ids]

if selected_reports:
    names = ", ".join(r["Filename"] for r in selected_reports)
    st.write(f"**{len(selected_reports)} file(s) selected:** {names}")

    if len(selected_reports) == 1:
        r = selected_reports[0]
        st.download_button(
            label=f"Download {r['Filename']}",
            data=r["html_bytes"],
            file_name=r["Filename"],
            mime="text/html",
        )
    else:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for r in selected_reports:
                zf.writestr(r["Filename"], r["html_bytes"])
        buf.seek(0)
        st.download_button(
            label=f"Download {len(selected_reports)} reports as .zip",
            data=buf,
            file_name="selected_reports.zip",
            mime="application/zip",
        )
else:
    st.caption("Select one or more rows to enable download.")
