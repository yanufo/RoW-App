from datetime import datetime
import os
import shutil
from pathlib import Path

def make_filename(
    uav_id: str,
    inspection_dt: datetime,
    safe_clearance,
    # clearance_height,
    # sensitivity,
) -> str:

    date_str = inspection_dt.strftime("%Y-%m-%d")
    time_str = inspection_dt.strftime("%H%M%S")

    return (
        f"{uav_id}_"
        f"{date_str}_"
        f"{time_str}_"
        f"{safe_clearance}"
    #     f"{clearance_height}m_"
    #     f"{sensitivity}"
    )

def make_solar_filename(
    uav_id: str,
    inspection_dt: datetime,
    # clearance_height,
    # sensitivity,
) -> str:

    date_str = inspection_dt.strftime("%Y-%m-%d")
    time_str = inspection_dt.strftime("%H%M%S")

    return (
        f"{uav_id}_"
        f"{date_str}_"
        f"{time_str}"
    #     f"{clearance_height}m_"
    #     f"{sensitivity}"
    )
        
