from database.connection import get_connection


def get_all_reports():
    conn = get_connection()
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

    reports = cursor.fetchall()

    cursor.close()
    conn.close()

    return reports


def get_report_by_id(report_id):
    conn = get_connection()
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
            Status,
            Filepath,
            HTML_path
        FROM row_database.file_detail
        WHERE id = %s
    """, (report_id,))

    report = cursor.fetchone()

    cursor.close()
    conn.close()

    return report


def has_processing_report():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT EXISTS (
            SELECT 1
            FROM row_database.file_detail
            WHERE Status = 'Processing'
        )
    """)

    result = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return bool(result)


def create_report(
    filename,
    uav_id,
    inspection_datetime,
    safe_clearance,
    clearance_height,
    sensitivity,
    status,
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO row_database.file_detail (
            Filename,
            UAV_ID,
            Inspection_Datetime,
            Safe_Clearance_Distance,
            Clearance_Height,
            Sensitivity,
            Status
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (
        filename,
        uav_id,
        inspection_datetime,
        safe_clearance,
        clearance_height,
        sensitivity,
        status,
    ))

    conn.commit()

    report_id = cursor.lastrowid

    cursor.close()
    conn.close()

    return report_id


def update_report_status(report_id, status):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE row_database.file_detail
        SET Status = %s
        WHERE id = %s
    """, (status, report_id))

    conn.commit()

    cursor.close()
    conn.close()
