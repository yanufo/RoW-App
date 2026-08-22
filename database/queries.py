from database.connection import get_connection


def get_all_reports():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            id,
            filename,
            uav_id,
            inspection_datetime,
            safe_clearance_distance,
            status
        FROM row_database.reports
    """)

    reports = cursor.fetchall()

    cursor.close()
    conn.close()

    return reports


def get_report_by_id(report_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # cursor.execute("""
    #     SELECT
    #         id,
    #         filename,
    #         uav_id,
    #         inspection_datetime,
    #         safe_clearance_distance,
    #         status
    #     FROM row_database.reports
    #     WHERE id = %s
    # """, (report_id,))

    cursor.execute("""
    SELECT
        r.id,
        r.filename,
        r.uav_id,
        r.inspection_datetime,
        r.safe_clearance_distance,
        r.status,
        rf.report_path,
        rf.video_path
    FROM row_database.reports AS r
    LEFT JOIN row_database.report_files AS rf
        ON r.id = rf.report_id
    WHERE r.id = %s
""", (report_id,))

    report = cursor.fetchone()

    cursor.close()
    conn.close()

    return report

def insert_report_files(report_id, report_path, video_path):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO row_database.report_files (
        report_id, 
        report_path, 
        video_path
        )
        VALUES (%s, %s, %s)
    """, (report_id, report_path, video_path))

    conn.commit()

    cursor.close()
    conn.close()


def has_processing_report():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT EXISTS (
            SELECT 1
            FROM row_database.reports
            WHERE status = 'Processing'
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
    status,
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO row_database.reports (
            filename,
            uav_id,
            inspection_datetime,
            safe_clearance_distance,
            status
        )
        VALUES (%s, %s, %s, %s, %s)
    """, (
        filename,
        uav_id,
        inspection_datetime,
        safe_clearance,
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
        UPDATE row_database.reports
        SET status = %s
        WHERE id = %s
    """, (status, report_id))

    conn.commit()

    cursor.close()
    conn.close()
