import base64
import os

import streamlit as st
import streamlit.components.v1 as components

from database.queries import get_report_by_id


def format_mmss(seconds: int) -> str:
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"


def inject_preview_drawer_css():

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
            from {
                transform: translateX(100%);
            }

            to {
                transform: translateX(0);
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def video_player(video_bytes):

    video_b64 = base64.b64encode(video_bytes).decode()

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

        <script>

        function seekVideo(seconds) {{

            const video =
                document.getElementById("videoPlayer");

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


@st.dialog("Preview", width="large")
def preview_dialog(report_id):

    inject_preview_drawer_css()

    report = get_report_by_id(report_id)

    if report is None:
        st.error("Report not found.")
        return

    st.caption(report["filename"])

    tab_report, tab_video = st.tabs(
        ["📄 Report", "🎬 Processed Video"]
    )

    with tab_report:

        html_path = report["report_path"]

        if os.path.exists(html_path):

            with open(html_path, "rb") as f:
                html_bytes = f.read()

            components.html(
                html_bytes.decode(
                    "utf-8",
                    errors="replace",
                ),
                height=550,
                scrolling=True,
            )

            st.download_button(
                "⬇ Download report",
                data=html_bytes,
                file_name=report["filename"] + ".html",
                mime="text/html",
                key=f"dl_report_{report_id}",
            )

        else:

            st.warning(
                "Report HTML file not found."
            )

    with tab_video:

        video_path = report["video_path"]

        if os.path.exists(video_path):

            with open(video_path, "rb") as f:
                video_bytes = f.read()

            video_player(
                video_bytes,
            )

            st.download_button(
                "⬇ Download video",
                data=video_bytes,
                file_name=report["filename"] + ".mp4",
                mime="video/mp4",
                key=f"dl_video_{report_id}",
            )

        else:

            st.warning(
                "Processed video file not found."
            )
