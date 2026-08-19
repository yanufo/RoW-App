from datetime import datetime
import os
import shutil
from pathlib import Path

def make_filename(
    uav_id: str,
    inspection_dt: datetime,
    safe_clearance,
    clearance_height,
    sensitivity,
) -> str:

    date_str = inspection_dt.strftime("%Y-%m-%d")
    time_str = inspection_dt.strftime("%H%M%S")

    return (
        f"{uav_id}_"
        f"{date_str}_"
        f"{time_str}_"
        f"{safe_clearance}m_"
        f"{clearance_height}m_"
        f"{sensitivity}"
    )

def add_files_to_input(input_dir, files, filename):
    """
    Add files to the input directory.

    Args:
        input_dir (str): The path to the input directory.
        files (list): A list of file objects from file uploader to add to the input directory.
    """

    for file in files:
        if file is not None:
            extension = os.path.splitext(file.name)[1]
            full_filename = f"{filename}{extension}"
            file_path = os.path.join(input_dir, full_filename)
            with open(file_path, "wb") as f:
                f.write(file.getbuffer())

    dropbox_path = os.path.join(input_dir, f"{filename}.dropbox")
    Path(dropbox_path).touch()  # Create an empty .Dropbox file to signal processing
        
