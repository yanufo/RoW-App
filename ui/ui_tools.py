import streamlit as st
import pandas as pd
from sql_tool.queries import get_all_reports, get_all_solar_dag_run_id,get_reports_status_by_ids,get_report_by_id,get_all_dag_run_id,get_all_filename,delete_from_database,get_all_solar_filename,delete_from_solar_database,get_solar_report_by_id,get_solar_reports_status_by_ids
from ui.preview import preview_dialog, preview_dialog_solar
from pathlib import Path
import requests
from ui.download import download_dialog, download_dialog_solar

# region Global Constants 
STATUS_COLORS = {
    "Queued": "#1E88E5",
    "Processing": "#FB8C00",
    "Completed": "#43A047",
    "Failed": "#E53935",
}
COL_WEIGHTS = [1,6,2,3,3,1]
COL_WEIGHTS_2 = [1,6,2,3,1]
STATUS_OPTIONS = ['Queued','Processing','Failed','Completed']
SORT_OPTIONS = ["Newest First","Filename","UAV ID","Inspection Date Time","Safe Clearance Distance (m)","Status",]
SORT_OPTIONS_SOLAR = ["Newest First","Filename","UAV ID","Inspection Date Time","Safe Clearance Distance (m)","Status",]

# endregion Global Constants

def stop_airflow_run(dag_id, dag_run_id):

    url = (
        f"http://host.docker.internal:8082/api/v1/"
        f"dags/{dag_id}/dagRuns/{dag_run_id}"
    )

    response = requests.patch(
        url,
        auth=("airflow", "airflow"),
        json={"state": "failed"},
    )

    return response
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

@st.fragment(run_every=5)
def refresh_statuses(report_ids, status_placeholders):

    latest_reports = get_reports_status_by_ids(report_ids)

    status_map = {
        report["id"]: report["status"]
        for report in latest_reports
    }

    for rid, placeholder in status_placeholders.items():

        status = status_map.get(rid)

        if status is not None:
            placeholder.markdown(
                status_badge_html(status),
                unsafe_allow_html=True,
            )

@st.fragment(run_every=5)
def refresh_solar_statuses(report_ids, status_placeholders):

    latest_reports = get_solar_reports_status_by_ids(report_ids)

    status_map = {
        report["id"]: report["status"]
        for report in latest_reports
    }

    for rid, placeholder in status_placeholders.items():

        status = status_map.get(rid)

        if status is not None:
            placeholder.markdown(
                status_badge_html(status),
                unsafe_allow_html=True,
            )

# Display function
def get_selected_visible_ids(df):
    """
    Return IDs of reports that are currently visible
    and whose checkbox is selected.
    """

    selected_ids = []

    for rid in df["id"].tolist():

        if st.session_state.get(
            f"chk_{rid}",
            False,
        ):
            selected_ids.append(rid)

    return selected_ids

def get_selected_solar_visible_ids(df):
    """
    Return IDs of reports that are currently visible
    and whose checkbox is selected.
    """

    selected_ids = []

    for rid in df["id"].tolist():

        if st.session_state.get(
            f"solar_chk_{rid}",
            False,
        ):
            selected_ids.append(rid)

    return selected_ids


def display_table(df):

    # ==================================================
    # VISIBLE REPORT IDS
    # ==================================================
    if not df.empty:
        visible_ids = df["id"].tolist()

        completed_ids = df.loc[df["status"] == "Completed","id",].tolist()

        # ==================================================
        # ACTION BAR
        # ==================================================

        selected_visible_ids = get_selected_visible_ids(df)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            select_all_report = st.button(
                "Select All",
                key="select_all_report",
                use_container_width=True,
            )

        with col2:
            clear_all_report = st.button(
                "Clear All",
                key="clear_all_report",
                use_container_width=True,
            )

        with col3:
            download = st.button(
                "Download",
                key="download_report",
                use_container_width=True,
                disabled=not selected_visible_ids,
            )

        with col4:
            delete_all_report = st.button(
                "Delete",
                key="delete_all_report",
                type="secondary",
                use_container_width=True,
                disabled=not selected_visible_ids,
            )

        # ==================================================
        # SELECT ALL
        # ==================================================

        if select_all_report:

            for rid in completed_ids:

                st.session_state[
                    f"chk_{rid}"
                ] = True

            st.rerun()

        # ==================================================
        # CLEAR ALL
        # ==================================================

        if clear_all_report:

            for rid in visible_ids:

                st.session_state[
                    f"chk_{rid}"
                ] = False

            st.rerun()

        # ==================================================
        # DOWNLOAD
        # ==================================================

        if download:

            selected_visible_ids = get_selected_visible_ids(df)

            if selected_visible_ids:

                selected_reports = df[
                    df["id"].isin(selected_visible_ids)
                ].to_dict("records")

                download_dialog(
                    selected_reports
                )

            else:

                st.warning(
                    "Please select at least one report."
                )
        # ==================================================
        # DELETE
        # ==================================================

        if delete_all_report:

            ids_to_delete = get_selected_visible_ids(df)

            if not ids_to_delete:

                st.warning(
                    "No reports are selected."
                )

            else:

                for report_id in ids_to_delete:

                    # ----------------------------------
                    # Database information
                    # ----------------------------------

                    dag_run_id = get_all_dag_run_id(
                        report_id
                    )

                    filename = get_all_filename(
                        report_id
                    )

                    # ----------------------------------
                    # Stop Airflow
                    # ----------------------------------

                    if dag_run_id:

                        stop_airflow_run(
                            dag_id="EGATWorkflowPipeline",
                            dag_run_id=dag_run_id,
                        )

                    # ----------------------------------
                    # Delete database record
                    # ----------------------------------

                    delete_from_database(
                        report_id
                    )

                    # ----------------------------------
                    # Delete input file (Usually Airflow cleans up, but just in case)
                    # ----------------------------------

                    INPUT_DIR = Path(
                        "/data/EGAT/inspections/row"
                    )

                    if INPUT_DIR.exists() and filename:

                        for file_path in INPUT_DIR.iterdir():

                            if (
                                file_path.is_file()
                                and file_path.stem == filename
                            ):
                                file_path.unlink()

                    # ----------------------------------
                    # Delete output file
                    # ----------------------------------

                    OUTPUT_DIR = Path(
                        "/data/EGAT/inspections/output/row"
                    )

                    if OUTPUT_DIR.exists() and filename:

                        for file_path in OUTPUT_DIR.iterdir():

                            if (
                                file_path.is_file()
                                and file_path.name.startswith(f"{filename}.")
                            ):
                                file_path.unlink()

                    # ----------------------------------
                    # Remove selection state
                    # ----------------------------------
                    st.session_state.pop(
                        f"chk_{report_id}",
                        None,
                    )

                st.rerun()

        # ==================================================
        # TABLE HEADER
        # ==================================================

        (
            h_check,
            h_name,
            h_uav,
            h_time,
            h_safe,
            h_status,
        ) = st.columns(COL_WEIGHTS)

        h_check.markdown("**Select**")
        h_name.markdown("**Filename**")
        h_uav.markdown("**UAV ID**")
        h_time.markdown("**Inspection Date Time**")
        h_safe.markdown(
            "**Safe Clearance Distance (m)**"
        )
        h_status.markdown("**Status**")

        # ==================================================
        # STATUS PLACEHOLDERS
        # ==================================================

        status_placeholders = {}

        # ==================================================
        # TABLE ROWS
        # ==================================================

        for _, report in df.iterrows():

            rid = report["id"]

            (
                c_check,
                c_name,
                c_uav,
                c_time,
                c_safe,
                c_status,
            ) = st.columns(COL_WEIGHTS)

            # ----------------------------------
            # Checkbox
            # ----------------------------------

            c_check.checkbox(
                "select",
                key=f"chk_{rid}",
                label_visibility="collapsed",
            )

            # ----------------------------------
            # Filename / Preview
            # ----------------------------------

            clicked = c_name.button(
                report["filename"],
                key=f"btn_{rid}",
                use_container_width=True,
            )

            if clicked:

                latest_report = get_report_by_id(
                    rid
                )

                if latest_report is None:

                    st.error(
                        "Report not found."
                    )

                elif latest_report["status"] == "Completed":

                    preview_dialog(rid)

                else:

                    st.warning(
                        f"Report is currently "
                        f"{latest_report['status']}."
                    )

            # ----------------------------------
            # UAV
            # ----------------------------------

            c_uav.markdown(
                str(report["uav_id"])
            )

            # ----------------------------------
            # Date
            # ----------------------------------

            inspection_time = pd.to_datetime(
                report["inspection_datetime"]
            )

            c_time.markdown(
                inspection_time.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            )

            # ----------------------------------
            # Clearance
            # ----------------------------------

            c_safe.markdown(
                str(
                    report[
                        "safe_clearance_distance"
                    ]
                )
            )

            # ----------------------------------
            # Status
            # ----------------------------------

            with c_status:

                status_placeholders[rid] = (
                    st.empty()
                )

        # ==================================================
        # REFRESH STATUSES
        # ==================================================

        refresh_statuses(
            visible_ids,
            status_placeholders,
        )
    else:
        st.write("")


# def display_solar_table(df):

#     # ==================================================
#     # VISIBLE REPORT IDS
#     # ==================================================
#     if not df.empty:
#         visible_ids = df["id"].tolist()

#         completed_ids = df.loc[df["status"] == "Completed","id",].tolist()

#         # ==================================================
#         # ACTION BAR
#         # ==================================================

#         selected_visible_ids = get_selected_visible_ids(df)

#         col1, col2, col3, col4 = st.columns(4)

#         with col1:
#             select_all_report = st.button(
#                 "Select All",
#                 key="select_all_report",
#                 use_container_width=True,
#             )

#         with col2:
#             clear_all_report = st.button(
#                 "Clear All",
#                 key="clear_all_report",
#                 use_container_width=True,
#             )

#         with col3:
#             download = st.button(
#                 "Download",
#                 key="download_report",
#                 use_container_width=True,
#                 disabled=not selected_visible_ids,
#             )

#         with col4:
#             delete_all_report = st.button(
#                 "Delete",
#                 key="delete_all_report",
#                 type="secondary",
#                 use_container_width=True,
#                 disabled=not selected_visible_ids,
#             )

#         # ==================================================
#         # SELECT ALL
#         # ==================================================

#         if select_all_report:

#             for rid in completed_ids:

#                 st.session_state[
#                     f"chk_{rid}"
#                 ] = True

#             st.rerun()

#         # ==================================================
#         # CLEAR ALL
#         # ==================================================

#         if clear_all_report:

#             for rid in visible_ids:

#                 st.session_state[
#                     f"chk_{rid}"
#                 ] = False

#             st.rerun()

#         # ==================================================
#         # DOWNLOAD
#         # ==================================================

#         if download:

#             selected_visible_ids = get_selected_solar_visible_ids(df)

#             if selected_visible_ids:

#                 selected_reports = df[
#                     df["id"].isin(selected_visible_ids)
#                 ].to_dict("records")

#                 download_dialog_solar(
#                     selected_reports
#                 )

#             else:

#                 st.warning(
#                     "Please select at least one report."
#                 )
#         # ==================================================
#         # DELETE
#         # ==================================================

#         if delete_all_report:

#             ids_to_delete = get_selected_solar_visible_ids(df)

#             if not ids_to_delete:

#                 st.warning(
#                     "No reports are selected."
#                 )

#             else:

#                 for report_id in ids_to_delete:

#                     # ----------------------------------
#                     # Database information
#                     # ----------------------------------

#                     dag_run_id = get_all_solar_dag_run_id(
#                         report_id
#                     )

#                     filename = get_all_solar_filename(
#                         report_id
#                     )

#                     # ----------------------------------
#                     # Stop Airflow
#                     # ----------------------------------

#                     if dag_run_id:

#                         stop_airflow_run(
#                             dag_id="EGATWorkflowPipeline",
#                             dag_run_id=dag_run_id,
#                         )

#                     # ----------------------------------
#                     # Delete database record
#                     # ----------------------------------

#                     delete_from_solar_database(
#                         report_id
#                     )

#                     # ----------------------------------
#                     # Delete input file (by right airflow would clean up)
#                     # ----------------------------------

#                     INPUT_DIR = Path(
#                         "/data/EGAT/inspections/Solar"
#                     )

#                     if INPUT_DIR.exists() and filename:

#                         for file_path in INPUT_DIR.iterdir():

#                             if (
#                                 file_path.is_file()
#                                 and file_path.stem == filename
#                             ):
#                                 file_path.unlink()

#                     # ----------------------------------
#                     # Delete output file
#                     # ----------------------------------

#                     OUTPUT_DIR = Path(
#                         "/data/EGAT/inspections/Output/Solar"
#                     )

#                     if OUTPUT_DIR.exists() and filename:

#                         for file_path in OUTPUT_DIR.iterdir():

#                             if (
#                                 file_path.is_file()
#                                 and file_path.stem == filename
#                             ):
#                                 file_path.unlink()

#                     # ----------------------------------
#                     # Remove selection state
#                     # ----------------------------------
#                     st.session_state.pop(
#                         f"chk_{report_id}",
#                         None,
#                     )

#                 st.rerun()

#         # ==================================================
#         # TABLE HEADER
#         # ==================================================

#         (
#             h_check,
#             h_name,
#             h_uav,
#             h_time,
#             h_status,
#         ) = st.columns(COL_WEIGHTS_2)

#         h_check.markdown("**Select**")
#         h_name.markdown("**Filename**")
#         h_uav.markdown("**UAV ID**")
#         h_time.markdown("**Inspection Date Time**")
#         h_status.markdown("**Status**")

#         # ==================================================
#         # STATUS PLACEHOLDERS
#         # ==================================================

#         status_placeholders = {}

#         # ==================================================
#         # TABLE ROWS
#         # ==================================================

#         for _, report in df.iterrows():

#             rid = report["id"]

#             (
#                 c_check,
#                 c_name,
#                 c_uav,
#                 c_time,
#                 c_status,
#             ) = st.columns(COL_WEIGHTS_2)

#             # ----------------------------------
#             # Checkbox
#             # ----------------------------------

#             c_check.checkbox(
#                 "select",
#                 key=f"chk_{rid}",
#                 label_visibility="collapsed",
#             )

#             # ----------------------------------
#             # Filename / Preview
#             # ----------------------------------

#             clicked = c_name.button(
#                 report["filename"],
#                 key=f"btn_{rid}",
#                 use_container_width=True,
#             )

#             if clicked:

#                 latest_report = get_solar_report_by_id(
#                     rid
#                 )

#                 if latest_report is None:

#                     st.error(
#                         "Report not found."
#                     )

#                 elif latest_report["status"] == "Completed":

#                     preview_dialog_solar(rid)

#                 else:

#                     st.warning(
#                         f"Report is currently "
#                         f"{latest_report['status']}."
#                     )

#             # ----------------------------------
#             # UAV
#             # ----------------------------------

#             c_uav.markdown(
#                 str(report["uav_id"])
#             )

#             # ----------------------------------
#             # Date
#             # ----------------------------------

#             inspection_time = pd.to_datetime(
#                 report["inspection_datetime"]
#             )

#             c_time.markdown(
#                 inspection_time.strftime(
#                     "%Y-%m-%d %H:%M:%S"
#                 )
#             )


#             # ----------------------------------
#             # Status
#             # ----------------------------------

#             with c_status:
#                 status_placeholders[rid] = (
#                     st.empty()
#                 )

#         # ==================================================
#         # REFRESH STATUSES
#         # ==================================================

#         refresh_statuses(
#             visible_ids,
#             status_placeholders,
#         )
#     else:
#         st.write("")


def reset_filters():
    st.session_state["uav_filter"] = []
    st.session_state["status_filter"] = []
    st.session_state["date_range"] = ()
    st.session_state["safe_range"] = (0, 200)
    st.session_state["sort_by"] = ""
    st.session_state["sort_order"] = ""


def reset_solar_filters():
    st.session_state["uav_filter"] = []
    st.session_state["status_filter"] = []
    st.session_state["date_range"] = ()
    st.session_state["sort_by"] = ""
    st.session_state["sort_order"] = ""
    


def display_solar_table(df):

    # ==================================================
    # VISIBLE REPORT IDS
    # ==================================================
    if not df.empty:
        visible_ids = df["id"].tolist()

        completed_ids = df.loc[df["status"] == "Completed","id",].tolist()

        # ==================================================
        # ACTION BAR
        # ==================================================

        selected_visible_ids = get_selected_solar_visible_ids(df)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            select_all_report = st.button(
                "Select All",
                key="solar_select_all_report",
                use_container_width=True,
            )

        with col2:
            clear_all_report = st.button(
                "Clear All",
                key="solar_clear_all_report",
                use_container_width=True,
            )

        with col3:
            download = st.button(
                "Download",
                key="solar_download_report",
                use_container_width=True,
                disabled=not selected_visible_ids,
            )

        with col4:
            delete_all_report = st.button(
                "Delete",
                key="solar_delete_all_report",
                type="secondary",
                use_container_width=True,
                disabled=not selected_visible_ids,
            )

        # ==================================================
        # SELECT ALL
        # ==================================================

        if select_all_report:

            for rid in completed_ids:

                st.session_state[
                    f"solar_chk_{rid}"
                ] = True

            st.rerun()

        # ==================================================
        # CLEAR ALL
        # ==================================================

        if clear_all_report:

            for rid in visible_ids:

                st.session_state[
                    f"solar_chk_{rid}"
                ] = False

            st.rerun()

        # ==================================================
        # DOWNLOAD
        # ==================================================

        if download:

            selected_visible_ids = get_selected_solar_visible_ids(df)

            if selected_visible_ids:

                selected_reports = df[
                    df["id"].isin(selected_visible_ids)
                ].to_dict("records")

                download_dialog_solar(
                    selected_reports
                )

            else:

                st.warning(
                    "Please select at least one report."
                )
        # ==================================================
        # DELETE
        # ==================================================

        if delete_all_report:

            ids_to_delete = get_selected_solar_visible_ids(df)

            if not ids_to_delete:

                st.warning(
                    "No reports are selected."
                )

            else:

                for report_id in ids_to_delete:

                    # ----------------------------------
                    # Database information
                    # ----------------------------------

                    dag_run_id = get_all_solar_dag_run_id(
                        report_id
                    )

                    filename = get_all_solar_filename(
                        report_id
                    )

                    # ----------------------------------
                    # Stop Airflow
                    # ----------------------------------

                    if dag_run_id:

                        stop_airflow_run(
                            dag_id="EGATWorkflowPipeline",
                            dag_run_id=dag_run_id,
                        )

                    # ----------------------------------
                    # Delete database record
                    # ----------------------------------

                    delete_from_solar_database(
                        report_id
                    )

                    # ----------------------------------
                    # Delete input file (by right airflow would clean up)
                    # ----------------------------------

                    INPUT_DIR = Path(
                        "/data/EGAT/inspections/solar"
                    )

                    if INPUT_DIR.exists() and filename:

                        for file_path in INPUT_DIR.iterdir():

                            if (
                                file_path.is_file()
                                and file_path.name.startswith(f"{filename}.")
                            ):
                                file_path.unlink()

                    # ----------------------------------
                    # Delete output file
                    # ----------------------------------

                    OUTPUT_DIR = Path(
                        "/data/EGAT/inspections/output/solar"
                    )

                    if OUTPUT_DIR.exists() and filename:

                        for file_path in OUTPUT_DIR.iterdir():

                            if (
                                file_path.is_file()
                                and file_path.name.startswith(f"{filename}.")
                            ):
                                file_path.unlink()

                    # ----------------------------------
                    # Remove selection state
                    # ----------------------------------
                    st.session_state.pop(
                        f"solar_chk_{report_id}",
                        None,
                    )

                st.rerun()

        # ==================================================
        # TABLE HEADER
        # ==================================================

        (
            h_check,
            h_name,
            h_uav,
            h_time,
            h_status,
        ) = st.columns(COL_WEIGHTS_2)

        h_check.markdown("**Select**")
        h_name.markdown("**Filename**")
        h_uav.markdown("**UAV ID**")
        h_time.markdown("**Inspection Date Time**")
        h_status.markdown("**Status**")

        # ==================================================
        # STATUS PLACEHOLDERS
        # ==================================================

        status_placeholders = {}

        # ==================================================
        # TABLE ROWS
        # ==================================================

        for _, report in df.iterrows():

            rid = report["id"]

            (
                c_check,
                c_name,
                c_uav,
                c_time,
                c_status,
            ) = st.columns(COL_WEIGHTS_2)

            # ----------------------------------
            # Checkbox
            # ----------------------------------

            c_check.checkbox(
                "select",
                key=f"solar_chk_{rid}",
                label_visibility="collapsed",
            )

            # ----------------------------------
            # Filename / Preview
            # ----------------------------------

            clicked = c_name.button(
                report["filename"],
                key=f"solar_btn_{rid}",
                use_container_width=True,
            )

            if clicked:

                latest_report = get_solar_report_by_id(
                    rid
                )

                if latest_report is None:

                    st.error(
                        "Report not found."
                    )

                elif latest_report["status"] == "Completed":

                    preview_dialog_solar(rid)

                else:

                    st.warning(
                        f"Report is currently "
                        f"{latest_report['status']}."
                    )

            # ----------------------------------
            # UAV
            # ----------------------------------

            c_uav.markdown(
                str(report["uav_id"])
            )

            # ----------------------------------
            # Date
            # ----------------------------------

            inspection_time = pd.to_datetime(
                report["inspection_datetime"]
            )

            c_time.markdown(
                inspection_time.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            )


            # ----------------------------------
            # Status
            # ----------------------------------

            with c_status:
                status_placeholders[rid] = (st.empty())

        # ==================================================
        # REFRESH STATUSES
        # ==================================================

        refresh_solar_statuses(
            visible_ids,
            status_placeholders,
        )
    else:
        st.write("")
 
def render_filter(uav_ids):

    with st.expander(
        "Filters & Sort",
        expanded=True,
    ):

        f1, f2, f3, f4 = st.columns(4)

        # -----------------------------------------
        # UAV
        # -----------------------------------------
        uav_selected = f1.multiselect(
            "UAV ID",
            options=uav_ids,
            key="uav_filter",
        )

        # -----------------------------------------
        # Status
        # -----------------------------------------
        status_selected = f2.multiselect(
            "Status",
            options=STATUS_OPTIONS,
            key="status_filter",
        )

        # -----------------------------------------
        # Date
        # -----------------------------------------
        date_selected = f3.date_input(
            "Inspection Date range",
            value=(),
            key="date_range",
        )

        # -----------------------------------------
        # Safe clearance
        # -----------------------------------------
        clearance_distance_selected = f4.slider(
            "Safe Clearance Distance (m)",
            min_value=0,
            max_value=200,
            value=(0, 200),
            key="safe_range",
        )

        f7, f8, f9 = st.columns(3)

        # -----------------------------------------
        # Sorting
        # -----------------------------------------
        sorting_criteria = f7.selectbox(
            "Sort by",
            options=[""] + SORT_OPTIONS,
            key="sort_by",
        )

        # -----------------------------------------
        # Order
        # -----------------------------------------
        order_selected = f8.radio(
            "Order",
            options=["", "Descending", "Ascending"],
            horizontal=True,
            key="sort_order",
        )

        # -----------------------------------------
        # Reset
        # -----------------------------------------
        f9.button(
            "Reset",
            key="report_reset_button",
            type="secondary",
            use_container_width=True,
            on_click=reset_filters,
        )

    # -----------------------------------------
    # No clearance filter if full range
    # -----------------------------------------
    if clearance_distance_selected == (0, 200):
        clearance_distance_selected = None

    return (
        uav_selected,
        status_selected,
        date_selected,
        clearance_distance_selected,
        sorting_criteria,
        order_selected,
    )

def render_solar_filter(uav_ids):

    with st.expander(
        "Filters & Sort",
        expanded=True,
    ):

        f1, f2, f3, f4 = st.columns(4)

        # -----------------------------------------
        # UAV
        # -----------------------------------------
        uav_selected = f1.multiselect(
            "UAV ID",
            options=uav_ids,
            key="uav_filter",
        )

        # -----------------------------------------
        # Status
        # -----------------------------------------
        status_selected = f2.multiselect(
            "Status",
            options=STATUS_OPTIONS,
            key="status_filter",
        )

        # -----------------------------------------
        # Date
        # -----------------------------------------
        date_selected = f3.date_input(
            "Inspection Date range",
            value=(),
            key="date_range",
        )


        # -----------------------------------------
        # Sorting
        # -----------------------------------------
        sorting_criteria = f4.selectbox(
            "Sort by",
            options=[""] + SORT_OPTIONS_SOLAR,
            key="sort_by",
        )
        f7, f8, f9 = st.columns(3)
        # -----------------------------------------
        # Order
        # -----------------------------------------
        order_selected = f7.radio(
            "Order",
            options=["", "Descending", "Ascending"],
            horizontal=True,
            key="sort_order",
        )

        # -----------------------------------------
        # Reset
        # -----------------------------------------
        f8.button(
            "Reset",
            key="report_reset_button",
            type="secondary",
            use_container_width=True,
            on_click=reset_solar_filters,
        )

    return (
        uav_selected,
        status_selected,
        date_selected,
        sorting_criteria,
        order_selected,
    )

def filter_reports(
    df,
    uavids_selection,
    status_selection,
    date_selection,
    clearance_selection,
    sorting_selection,
    order_selection,
):
    # -----------------------------------------
    # Reset
    # -----------------------------------------
    # if reset_selection:
    #     return df.copy()

    filtered_df = df.copy()

    # -----------------------------------------
    # UAV ID filter
    # -----------------------------------------
    if uavids_selection:
        filtered_df = filtered_df[
            filtered_df["uav_id"].isin(uavids_selection)
        ]

    # -----------------------------------------
    # Status filter
    # -----------------------------------------
    if status_selection:
        filtered_df = filtered_df[
            filtered_df["status"].isin(status_selection)
        ]

    # -----------------------------------------
    # Inspection Date filter
    # -----------------------------------------
    if (
        date_selection
        and isinstance(date_selection, (tuple, list))
        and len(date_selection) == 2
    ):
        date_start, date_end = date_selection

        inspection_dates = pd.to_datetime(
            filtered_df["inspection_datetime"]
        ).dt.date

        filtered_df = filtered_df[
            (inspection_dates >= date_start)
            & (inspection_dates <= date_end)
        ]

    # -----------------------------------------
    # Clearance Distance filter
    # -----------------------------------------
    if (
        clearance_selection
        and isinstance(clearance_selection, (tuple, list))
        and len(clearance_selection) == 2
    ):
        clearance_min, clearance_max = clearance_selection

        filtered_df = filtered_df[
            (
                filtered_df["safe_clearance_distance"]
                >= clearance_min
            )
            & (
                filtered_df["safe_clearance_distance"]
                <= clearance_max
            )
        ]

    # -----------------------------------------
    # Sorting
    # -----------------------------------------
    SORT_COLUMNS = {
        "Inspection Date Time": "inspection_datetime",
        "Filename": "filename",
        "Clearance Distance": "safe_clearance_distance",
        "UAV ID": "uav_id",
        "Status": "status",
    }

    if sorting_selection in SORT_COLUMNS:

        sort_column = SORT_COLUMNS[sorting_selection]

        ascending = (
            order_selection == "Ascending"
        )

        filtered_df = filtered_df.sort_values(
            by=sort_column,
            ascending=ascending,
        )
    else:
        filtered_df = filtered_df.sort_index(ascending=False)

    return filtered_df


def filter_solar_reports(
    df,
    uavids_selection,
    status_selection,
    date_selection,
    sorting_selection,
    order_selection,
):
    # -----------------------------------------
    # Reset
    # -----------------------------------------
    # if reset_selection:
    #     return df.copy()

    filtered_df = df.copy()

    # -----------------------------------------
    # UAV ID filter
    # -----------------------------------------
    if uavids_selection:
        filtered_df = filtered_df[
            filtered_df["uav_id"].isin(uavids_selection)
        ]

    # -----------------------------------------
    # Status filter
    # -----------------------------------------
    if status_selection:
        filtered_df = filtered_df[
            filtered_df["status"].isin(status_selection)
        ]

    # -----------------------------------------
    # Inspection Date filter
    # -----------------------------------------
    if (
        date_selection
        and isinstance(date_selection, (tuple, list))
        and len(date_selection) == 2
    ):
        date_start, date_end = date_selection

        inspection_dates = pd.to_datetime(
            filtered_df["inspection_datetime"]
        ).dt.date

        filtered_df = filtered_df[
            (inspection_dates >= date_start)
            & (inspection_dates <= date_end)
        ]

    # -----------------------------------------
    # Sorting
    # -----------------------------------------
    SORT_COLUMNS = {
        "Inspection Date Time": "inspection_datetime",
        "Filename": "filename",
        "UAV ID": "uav_id",
        "Status": "status",
    }

    if sorting_selection in SORT_COLUMNS:

        sort_column = SORT_COLUMNS[sorting_selection]

        ascending = (
            order_selection == "Ascending"
        )

        filtered_df = filtered_df.sort_values(
            by=sort_column,
            ascending=ascending,
        )
    else:
        filtered_df = filtered_df.sort_index(ascending=False)

    return filtered_df


