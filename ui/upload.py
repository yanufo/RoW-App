from asyncio import sleep
import os
import uuid
from datetime import timezone

import streamlit as st
import yaml

from sql_tool.queries import (
    create_solar_report,
    has_duplicate_solar_report,
    has_processing_report,
    create_report,
    has_duplicate_report,
    has_processing_solar_report
)
from services.report_service import (
    # add_files_to_input,
    make_filename,
    make_solar_filename,
)


with open("/inspection/config.yml", "r") as f:
    config = yaml.safe_load(f)


# ==================================================
# UPLOAD DIALOG
# ==================================================

@st.dialog("New Inspection Report", width="large")
def new_report_dialog():

    if "inspection_type" not in st.session_state:
        st.session_state.inspection_type = None

    # Selection screen
    if st.session_state.inspection_type is None:

        #col1, col2= st.columns(2)

        
        st.button(
            "Row Inspection",
            use_container_width=True,
            on_click=lambda: setattr(
                st.session_state,
                "inspection_type",
                "row",
            ),
        )

        # with col2:
        #     st.button(
        #         "Solar Inspection",
        #         use_container_width=True,
        #         on_click=lambda: setattr(
        #             st.session_state,
        #             "inspection_type",
        #             "solar",
        #         ),
        #     )

        return

    # --------------------------------------------------
    # SOLAR INSPECTION
    # --------------------------------------------------

    if st.session_state.inspection_type == "solar":

        solar_inspection_page()

        return

    # ==================================================
    # ROW INSPECTION
    # ==================================================

    if st.session_state.inspection_type == "row":

        # --------------------------------------------------
        # Form key
        # --------------------------------------------------

        if "form_key" not in st.session_state:
            st.session_state.form_key = 0

        fk = st.session_state.form_key

        # --------------------------------------------------
        # Upload files
        # --------------------------------------------------

        st.write("### Inspection Files")

        col1, col2 = st.columns(2)

        with col1:
            uploaded_video = st.file_uploader(
                "Choose a MP4 file",
                type=["mp4"],
                key=f"video_{fk}",
            )

        with col2:
            uploaded_srt = st.file_uploader(
                "Choose a SRT file",
                type=["srt"],
                key=f"srt_{fk}",
            )

        # --------------------------------------------------
        # Inspection information
        # --------------------------------------------------

        st.write("### Inspection Information")

        col1, col2 = st.columns(2)

        with col1:

            selected_id = st.text_input(
                "UAV ID",
                key=f"uav_{fk}",
            )

            safe_clearance = st.number_input(
                "Safe Clearance Distance (m)",
                min_value=0,
                max_value=200,
                value=None,
                placeholder="0",
                key=f"sc_{fk}",
            )

            with st.expander("ℹ️ What is Safe Clearance Distance?"):
                st.write('''
                    Safe clearance distance is the mandatory minimum distance from electrical line and people, buildings, trees, or equipment to stop electric shocks and arcing
                ''')
                st.image("images/safe_clear_distance_info.png")

        with col2:

            inspection_dt = st.datetime_input(
                "Inspection Date Time",
                value=None,
                key=f"dt_{fk}",
            )

        st.divider()

        # --------------------------------------------------
        # Buttons
        # --------------------------------------------------

        col1, col2 = st.columns(2)

        with col1:
            cancel = st.button(
                "Cancel",
                key=f"cancel_{fk}",
                use_container_width=True,
            )

        with col2:
            start = st.button(
                "Start Processing",
                key=f"start_{fk}",
                use_container_width=True,
                type="primary",
            )

        # --------------------------------------------------
        # Cancel
        # --------------------------------------------------

        if cancel:

            st.session_state.form_key += 1
            st.session_state.inspection_type = None

            st.rerun()

        # --------------------------------------------------
        # Start Processing
        # --------------------------------------------------

        if start:

            # Validation

            if uploaded_video is None:
                st.error("Please upload an MP4 file.")
                return

            if uploaded_srt is None:
                st.error("Please upload an SRT file.")
                return

            if not selected_id.strip():
                st.error("Please enter a UAV ID.")
                return

            if safe_clearance is None:
                st.error(
                    "Please enter the Safe Clearance Distance."
                )
                return

            if inspection_dt is None:
                st.error(
                    "Please select an inspection date/time."
                )
                return

            # --------------------------------------------------
            # Determine status
            # --------------------------------------------------

            processing_exist = has_processing_report()

            if processing_exist:
                status = "Queued"
            else:
                status = "Processing"

            # --------------------------------------------------
            # Generate filename
            # --------------------------------------------------

            inspection_dt_utc = inspection_dt.replace(
                tzinfo=timezone.utc
            )

            filename = make_filename(
                selected_id,
                inspection_dt_utc,
                safe_clearance,
            )

            # --------------------------------------------------
            # Duplicate check
            # --------------------------------------------------

            duplicate_status = has_duplicate_report(filename)

            if duplicate_status:
                st.error("Report already exists.")
                return

            # --------------------------------------------------
            # Add files to input
            # --------------------------------------------------

            # add_files_to_input(
            #     config["directories"]["input"],
            #     [
            #         uploaded_video,
            #         uploaded_srt,
            #     ],
            #     filename,
            # )

            # --------------------------------------------------
            # Create database record
            # --------------------------------------------------

            report_db_id = create_report(
                filename=filename,
                uav_id=selected_id,
                inspection_datetime=inspection_dt,
                safe_clearance=safe_clearance,
                status=status,
            )

            # --------------------------------------------------
            # Save files
            # --------------------------------------------------

            DEST_DIR = "/data/EGAT/inspections/row"

            os.makedirs(
                DEST_DIR,
                exist_ok=True,
            )

            video_path = os.path.join(
                DEST_DIR,
                f"{filename}.mp4",
            )

            srt_path = os.path.join(
                DEST_DIR,
                f"{filename}.srt",
            )

            with open(video_path, "wb") as f:
                f.write(uploaded_video.getvalue())

            with open(srt_path, "wb") as f:
                f.write(uploaded_srt.getvalue())

            # --------------------------------------------------
            # Create Dropbox trigger
            # --------------------------------------------------

            dropbox_path = os.path.join(
                DEST_DIR,
                f"{filename}.dropbox",
            )

            with open(dropbox_path, "w"):
                pass

            # --------------------------------------------------
            # Reset form
            # --------------------------------------------------

            st.session_state.form_key += 1
            st.session_state.inspection_type = None

            st.success(
                f"Report '{filename}' created."
            )

            st.rerun()

        
def solar_inspection_page():

    st.write("### Solar Inspection")
    # --------------------------------------------------
    # Form key
    # --------------------------------------------------

    if "form_key" not in st.session_state:
        st.session_state.form_key = 0

    fk = st.session_state.form_key

    # --------------------------------------------------
    # Upload files
    # --------------------------------------------------

    st.write("### Inspection Files")

    col1, col2 = st.columns(2)

    with col1:
        uploaded_video = st.file_uploader(
            "Choose a MP4 file",
            type=["mp4"],
            key=f"solar_video_{fk}",
        )

    with col2:
        uploaded_srt = st.file_uploader(
            "Choose a SRT file",
            type=["srt"],
            key=f"solar_srt_{fk}",
        )
    # --------------------------------------------------
    # Inspection information
    # --------------------------------------------------

    st.write("### Inspection Information")

    col1, col2 = st.columns(2)

    with col1:

        selected_id = st.text_input(
            "UAV ID",
            key=f"uav_{fk}",
        )

   
    with col2:
    
        inspection_dt = st.datetime_input(
            "Inspection Date Time",
            value=None,
            key=f"dt_{fk}",
        )

    st.divider()
    # --------------------------------------------------
    # Buttons
    # --------------------------------------------------

    col1, col2 = st.columns(2)

    with col1:
        cancel = st.button(
            "Cancel",
            key=f"solar_cancel_{fk}",
            use_container_width=True,
        )

    with col2:
        start = st.button(
            "Start Processing",
            key=f"solar_start_{fk}",
            use_container_width=True,
            type="primary",
        )

    # --------------------------------------------------
    # Cancel
    # --------------------------------------------------

    if cancel:

        st.session_state.form_key += 1
        st.session_state.inspection_type = None

        st.rerun()

    
    # --------------------------------------------------
    # Start Processing
    # --------------------------------------------------

    if start:

        # Validation

        if uploaded_video is None:
            st.error("Please upload an MP4 file.")
            return

        if uploaded_srt is None:
            st.error("Please upload an SRT file.")
            return

        if not selected_id.strip():
            st.error("Please enter a UAV ID.")
            return

        if inspection_dt is None:
            st.error(
                "Please select an inspection date/time."
            )
            return

        # --------------------------------------------------
        # Determine status
        # --------------------------------------------------

        processing_exist = has_processing_solar_report()

        if processing_exist:
            status = "Queued"
        else:
            status = "Processing"

        # --------------------------------------------------
        # Generate filename
        # --------------------------------------------------

        inspection_dt_utc = inspection_dt.replace(
            tzinfo=timezone.utc
        )

        filename = make_solar_filename(
            selected_id,
            inspection_dt_utc,
        )

        # --------------------------------------------------
        # Duplicate check
        # --------------------------------------------------

        duplicate_status = has_duplicate_solar_report(filename)

        if duplicate_status:
            st.error("Report already exists.")
            return

        # --------------------------------------------------
        # Add files to input
        # --------------------------------------------------

        # add_files_to_input(
        #     config["directories"]["input"],
        #     [
        #         uploaded_video,
        #         uploaded_srt,
        #     ],
        #     filename,
        # )

        # --------------------------------------------------
        # Create database record
        # --------------------------------------------------

        report_db_id = create_solar_report(
            filename=filename,
            uav_id=selected_id,
            inspection_datetime=inspection_dt,
            status=status,
        )

        # --------------------------------------------------
        # Save files
        # --------------------------------------------------

        DEST_DIR = "/data/EGAT/inspections/solar"

        os.makedirs(
            DEST_DIR,
            exist_ok=True,
        )

        video_path = os.path.join(
            DEST_DIR,
            f"{filename}.mp4",
        )

        srt_path = os.path.join(
            DEST_DIR,
            f"{filename}.srt",
        )

        with open(video_path, "wb") as f:
            f.write(uploaded_video.getvalue())

        with open(srt_path, "wb") as f:
            f.write(uploaded_srt.getvalue())

        # --------------------------------------------------
        # Create Dropbox trigger
        # --------------------------------------------------

        sleep(2)

        dropbox_path = os.path.join(
            DEST_DIR,
            f"{filename}.dropbox",
        )

        with open(dropbox_path, "w"):
            pass

        # --------------------------------------------------
        # Reset form
        # --------------------------------------------------

        st.session_state.form_key += 1
        st.session_state.inspection_type = None

        st.success(
            f"Report '{filename}' created."
        )

        st.rerun()



# ==================================================
# MAIN BUTTON
# ==================================================

def show_new_report():

    if "form_key" not in st.session_state:
        st.session_state.form_key = 0

    if st.button(
        "➕ New Report",
        type="primary",
        use_container_width=True,
    ):

        new_report_dialog()
