import pandas as pd
import streamlit as st

from database.queries import get_all_reports
from ui.preview import preview_dialog


STATUS_COLORS = {
    "Queued": "#1E88E5",
    "Processing": "#FB8C00",
    "Completed": "#43A047",
    "Failed": "#E53935",
}

STATUS_OPTIONS = list(STATUS_COLORS.keys())


COL_WEIGHTS = [
    0.6,
    3,
    0.7,
    1.8,
    1.5,
    1.3,
    0.9,
    1.1,
]


SORT_COLUMNS = {
    "Filename": "Filename",
    "UAV ID": "UAV_ID",
    "Inspection Date Time": "Inspection_Datetime",
    "Safe Clearance Distance (m)": "Safe_Clearance_Distance",
    "Clearance Height (m)": "Clearance_Height",
    "Sensitivity": "Sensitivity",
    "Status": "Status",
}

SORT_OPTIONS = [
    "Newest First",
    "Filename",
    "UAV ID",
    "Inspection Date Time",
    "Safe Clearance Distance (m)",
    "Clearance Height (m)",
    "Sensitivity",
    "Status",
]

def status_badge_html(status):

    color = STATUS_COLORS.get(
        status,
        "#757575",
    )

    return (
        f'<span style="'
        f'background-color:{color}; '
        f'color:white; '
        f'padding:3px 12px; '
        f'border-radius:12px; '
        f'font-size:0.85em; '
        f'font-weight:600; '
        f'white-space:nowrap;">'
        f'{status}'
        f'</span>'
    )


def open_preview(report_id):

    st.session_state.preview_report_id = report_id

def reset_filters(min_date, max_date):
    st.session_state["uav_filter"] = []
    st.session_state["status_filter"] = []
    st.session_state["date_range"] = (min_date, max_date)
    st.session_state["safe_range"] = (0, 200)
    st.session_state["height_range"] = (0, 200)
    st.session_state["sens_range"] = (1, 10)

    st.session_state["sort_by"] = "Inspection Date Time"
    st.session_state["sort_order"] = "Descending"


def show_report_table():

    db_reports = get_all_reports()

    if not db_reports:

        st.info(
            "No reports yet. Click **New Report** "
            "to upload media and generate one."
        )

        return

    df = pd.DataFrame(db_reports)

    df["Inspection_Datetime"] = pd.to_datetime(
        df["Inspection_Datetime"]
    )

    # --------------------------------------------------
    # Search
    # --------------------------------------------------

    search_term = st.text_input(
        "🔍 Search filename",
        placeholder="Type part of a filename...",
    )

    # --------------------------------------------------
    # Available filters
    # --------------------------------------------------

    all_uav_ids = sorted(
        df["UAV_ID"]
        .dropna()
        .unique()
        .tolist()
    )

    all_dates = df["Inspection_Datetime"].dt.date

    min_date = all_dates.min()
    max_date = all_dates.max()

    # --------------------------------------------------
    # Filters
    # --------------------------------------------------

    with st.expander("Filters & Sort"):

        f1, f2, f3 = st.columns(3)

        uav_filter = f1.multiselect(
            "UAV ID",
            options=all_uav_ids,
            default=None,
            key="uav_filter",
        )

        status_filter = f2.multiselect(
            "Status",
            options=STATUS_OPTIONS,
            default=None,
            key="status_filter",
        )

        date_range = f3.date_input(
            "Inspection Date range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            key="date_range",
        )

        f4, f5, f6 = st.columns(3)

        safe_range = f4.slider(
            "Safe Clearance Distance (m)",
            min_value=0,
            max_value=200,
            value=(0, 200),
            key="safe_range",
        )

        height_range = f5.slider(
            "Clearance Height (m)",
            min_value=0,
            max_value=200,
            value=(0, 200),
            key="height_range",
        )

        sens_range = f6.slider(
            "Sensitivity",
            min_value=1,
            max_value=10,
            value=(1, 10),
            key="sens_range",
        )

        f7, f8, f9 = st.columns(3)

        sort_by = f7.selectbox(
            "Sort by",
            options=SORT_OPTIONS,
            index=0,
            key="sort_by",
        )

        sort_order = f8.radio(
            "Order",
            options=[
                "Descending",
                "Ascending",
            ],
            horizontal=True,
            key="sort_order",
        )

        reset_button = f9.button(
            "Reset",
            type="secondary",
            on_click=reset_filters,
            args=(min_date, max_date),
        )

    # --------------------------------------------------
    # Normalize date range
    # --------------------------------------------------

    if (
        isinstance(date_range, tuple)
        and len(date_range) == 2
    ):

        date_start, date_end = date_range

    else:

        date_start = min_date
        date_end = max_date

    # --------------------------------------------------
    # Apply filters
    # --------------------------------------------------

    filtered_df = df.copy().sort_values(
        by="id",
        ascending=False,
    )

    if search_term:

        filtered_df = filtered_df[
            filtered_df["Filename"].str.contains(
                search_term,
                case=False,
                na=False,
            )
        ]

    if uav_filter:
        filtered_df = filtered_df[
            filtered_df["UAV_ID"].isin(uav_filter)
        ]

    if status_filter:
        filtered_df = filtered_df[
            filtered_df["Status"].isin(status_filter)
        ]

    if date_range:
        filtered_df = filtered_df[
            filtered_df["Inspection_Datetime"]
            .dt.date
            .between(
                date_start,
                date_end,
            )
        ]

    if safe_range:
        filtered_df = filtered_df[
            filtered_df[
                "Safe_Clearance_Distance"
            ].between(
                safe_range[0],
                safe_range[1],
            )
        ]

    if height_range:
        filtered_df = filtered_df[
            filtered_df[
                "Clearance_Height"
            ].between(
                height_range[0],
                height_range[1],
            )
        ]

    if sens_range:
        filtered_df = filtered_df[
            filtered_df[
                "Sensitivity"
            ].between(
                sens_range[0],
                sens_range[1],
            )
        ]

    # --------------------------------------------------
    # Sort
    # --------------------------------------------------

    if sort_by != "Newest First":
        filtered_df = filtered_df.sort_values(
            by=SORT_COLUMNS[sort_by],
            ascending=(
                sort_order == "Ascending"
            ),
        )

    st.caption(
        f"Showing {len(filtered_df)} "
        f"of {len(df)} report(s)."
    )

    if filtered_df.empty:

        st.info(
            "No reports match the current "
            "search/filters."
        )

        return

    # --------------------------------------------------
    # Header
    # --------------------------------------------------

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
    col_safe.markdown("**Safe Clearance Distance (m)**")
    col_height.markdown("**Clearance Height (m)**")
    col_sens.markdown("**Sensitivity**")
    col_status.markdown("**Status**")

    st.markdown(
        """
        <style>
        .black-text {
            color: black !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------
    # Rows
    # --------------------------------------------------

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

        checked = c_check.checkbox(
            "select",
            value=st.session_state.selected.get(
                rid,
                False,
            ),
            key=f"chk_{rid}",
            label_visibility="collapsed",
        )

        st.session_state.selected[rid] = checked

        c_name.button(
            report["Filename"],
            key=f"btn_{rid}",
            use_container_width=True,
            on_click=open_preview,
            args=(rid,),
        )

        inspection_time = report[
            "Inspection_Datetime"
        ]

        c_uav.markdown(
            f'<span class="black-text">'
            f'{report["UAV_ID"]}'
            f'</span>',
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

        c_status.markdown(
            status_badge_html(
                report["Status"]
            ),
            unsafe_allow_html=True,
        )
