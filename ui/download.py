import os
import shutil
import streamlit as st

#test
OUTPUT_DIR = "/Users/wongwanyan/Documents/Staero/EGAT/row-app/test_data/output/15005_2026-08-29_000000_1m_1m_1.mp4"


@st.dialog("Download Reports")
def download_dialog(selected_reports):
    st.write(
        f"Download options for **{len(selected_reports)} report(s)**."
    )

    st.write("**Selected files:**")

    for report in selected_reports:
        st.write(f"- {report['Filename']}")

    download_type = st.radio(
        "What would you like to download?",
        [
            "Videos",
            "HTML Reports",
            "Videos + HTML Reports",
        ],
    )

    if st.button(
        "Download",
        type="primary",
        use_container_width=True,
    ):

        # ------------------------------------------
        # Videos
        # ------------------------------------------

        if download_type in [
            "Videos",
            "Videos + HTML Reports",
        ]:

            for report in selected_reports:

                video_path = os.path.join(
                    OUTPUT_DIR,
                    report["Filename"] + ".mp4"
                )

                if os.path.exists(video_path):

                    with open(video_path, "rb") as f:
                        video_bytes = f.read()

                    st.download_button(
                        label=f"Download {report['Filename']} video",
                        data=video_bytes,
                        file_name=report["Filename"] + ".mp4",
                        mime="video/mp4",
                        use_container_width=True,
                    )

                else:
                    st.error(
                        f"Video not found: {report['Filename']}"
                    )

        # ------------------------------------------
        # HTML
        # ------------------------------------------

        if download_type in [
            "HTML Reports",
            "Videos + HTML Reports",
        ]:

            for report in selected_reports:

                html_path = os.path.join(
                    OUTPUT_DIR,
                    report["Filename"] + ".html"
                )

                if os.path.exists(html_path):

                    with open(html_path, "rb") as f:
                        html_bytes = f.read()

                    st.download_button(
                        label=f"Download {report['Filename']} report",
                        data=html_bytes,
                        file_name=report["Filename"] + ".html",
                        mime="text/html",
                        use_container_width=True,
                    )

                else:
                    st.error(
                        f"HTML report not found: {report['Filename']}"
                    )
