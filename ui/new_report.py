import os
import uuid
import subprocess
from datetime import timezone

import streamlit as st
import yaml

with open("config.yml", "r") as f:
    config = yaml.safe_load(f)

from database.queries import (
    has_processing_report,
    create_report,
    insert_report_files,
)
from services.report_service import add_files_to_input, make_filename


def show_new_report():

    if st.session_state.popover_open:

        with st.popover("➕ New Report"):

            st.write("NEW INSPECTION REPORT")

            if st.session_state.confirm_cancel:

                st.warning(
                    "Discard this report? Uploaded files and entered "
                    "values will be lost."
                )

                yes_col, no_col = st.columns(2)

                if yes_col.button(
                    "Yes, cancel",
                    key="confirm_yes",
                    use_container_width=True,
                ):

                    st.session_state.confirm_cancel = False
                    st.session_state.form_key += 1
                    st.session_state.cancel_backup = {}

                    st.rerun()

                if no_col.button(
                    "No, go back",
                    key="confirm_no",
                    use_container_width=True,
                ):

                    backup = st.session_state.cancel_backup

                    fk = st.session_state.form_key

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

                fk = st.session_state.form_key

                uploaded_video = st.file_uploader(
                    "Choose a MP4 file",
                    type="mp4",
                    key=f"video_{fk}",
                )

                uploaded_srt = st.file_uploader(
                    "Choose a SRT file",
                    type="srt",
                    key=f"srt_{fk}",
                )

                uav = ["15005", "16001"]

                selected_id = st.selectbox(
                    "UAV ID",
                    uav,
                    index=None,
                    placeholder="Select UAV ID",
                    key=f"uav_{fk}",
                )

                safe_clearance = st.number_input(
                    "Safe Clearance Distance (m)",
                    min_value=0,
                    max_value=200,
                    step=1,
                    value=None,
                    key=f"sc_{fk}",
                )

                # clearance_height = st.number_input(
                #     "Clearance Height (m)",
                #     min_value=0,
                #     max_value=200,
                #     step=1,
                #     value=None,
                #     key=f"ch_{fk}",
                # )

                inspection_dt = st.datetime_input(
                    "Inspection Date Time",
                    value=None,
                    key=f"dt_{fk}",
                )

                # sensitivity = st.slider(
                #     "Sensitivity",
                #     min_value=1,
                #     max_value=10,
                #     key=f"sens_{fk}",
                # )

                col1, col2 = st.columns(2)

                cancel = col1.button(
                    "Cancel",
                    key=f"cancel_{fk}",
                    use_container_width=True,
                )

                start = col2.button(
                    "Start Processing",
                    key=f"start_{fk}",
                    use_container_width=True,
                    type="primary",
                )

                if cancel:

                    st.session_state.cancel_backup = {
                        "video": uploaded_video,
                        "srt": uploaded_srt,
                        "uav": selected_id,
                        "safe_clearance": safe_clearance,
                        # "clearance_height": clearance_height,
                        "inspection_dt": inspection_dt,
                        # "sensitivity": sensitivity,
                    }

                    st.session_state.confirm_cancel = True

                    st.rerun()

                if start:

                    if uploaded_video is None:
                        st.error("Please upload an MP4 file.")
                        return

                    if uploaded_srt is None:
                        st.error("Please upload an SRT file.")
                        return

                    if selected_id is None:
                        st.error("Please select a UAV ID.")
                        return

                    if inspection_dt is None:
                        st.error("Please select an inspection date/time.")
                        return

                    processing_exist = has_processing_report()

                    if processing_exist:
                        status = "Queued"
                    else:
                        status = "Processing"

                    report_uuid = str(uuid.uuid4())

                    inspection_dt_utc = inspection_dt.replace(
                        tzinfo=timezone.utc
                    )

                    filename = make_filename(
                        selected_id,
                        inspection_dt_utc,
                        safe_clearance,
                        # clearance_height,
                        # sensitivity,
                    )

                    add_files_to_input(config["directories"]["input"], [uploaded_video, uploaded_srt], filename)
                        

                    report_db_id = create_report(
                        filename=filename,
                        uav_id=selected_id,
                        inspection_datetime=inspection_dt,
                        safe_clearance=safe_clearance,
                        # clearance_height=clearance_height,
                        # sensitivity=sensitivity,
                        status=status,
                    )

                    # Update video_file table in database, mimic airflow updating the database after processing is complete
                    output_dir = config["directories"]["output"]    
                    report_path = os.path.join(output_dir, f"{filename}.html")
                    out_vid_path = os.path.join(output_dir, f"{filename}.mp4")
                    insert_report_files(report_db_id, report_path, out_vid_path)



                    report = {
                        "id": report_uuid,
                        "db_id": report_db_id,
                        "Filename": filename,
                        "UAV ID": selected_id,
                        "Inspection Date Time": inspection_dt_utc,
                        "Safe Clearance Distance (m)": str(
                            safe_clearance
                        ),
                        # "Clearance Height (m)": str(
                        #     clearance_height
                        # ),
                        # "Sensitivity": str(sensitivity),
                        "Status": status,
                        "video_name": uploaded_video.name,
                        "srt_name": uploaded_srt.name,
                        "video_bytes": uploaded_video.getvalue(),
                        "srt_bytes": uploaded_srt.getvalue(),
                    }

                    # Temporary test trigger
                    subprocess.Popen([
                        "python",
                        "/path/to/trigger_test.py",
                        status,
                        str(report_db_id),
                    ])

                    st.session_state.reports.insert(
                        0,
                        report,
                    )

                    st.session_state.selected[
                        report_uuid
                    ] = False

                    st.session_state.form_key += 1
                    st.session_state.popover_open = False

                    st.success(
                        f"Report '{filename}' created."
                    )
                    
                    st.rerun()

    else:

        if st.button("➕ New Report"):

            st.session_state.popover_open = True

            st.rerun()
