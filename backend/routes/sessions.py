from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from database import get_connection

router = APIRouter(
    prefix="/sessions",
    tags=["Study Sessions"]
)


class SessionCreate(BaseModel):
    student_id: int
    subject_id: int
    session_date: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_minutes: Optional[int] = None
    productivity: Optional[int] = None
    notes: Optional[str] = None


class SessionUpdate(BaseModel):
    student_id: Optional[int] = None
    subject_id: Optional[int] = None
    session_date: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_minutes: Optional[int] = None
    productivity: Optional[int] = None
    notes: Optional[str] = None


@router.get("/")
def get_sessions(
    student_id: Optional[int] = None,
    subject_id: Optional[int] = None,
    productivity: Optional[int] = None
):
    connection = get_connection()
    cursor = connection.cursor()

    query = """
        SELECT
            ss.session_id,
            ss.student_id,
            s.name AS student_name,
            ss.subject_id,
            sub.subject_name,
            sub.subject_code,
            ss.session_date,
            ss.start_time,
            ss.end_time,
            ss.duration_minutes,
            ss.productivity,
            ss.notes
        FROM study_session ss
        JOIN student s
            ON ss.student_id = s.student_id
        JOIN subject sub
            ON ss.subject_id = sub.subject_id
        WHERE 1=1
    """

    parameters = []

    if student_id:
        query += " AND ss.student_id = %s"
        parameters.append(student_id)

    if subject_id:
        query += " AND ss.subject_id = %s"
        parameters.append(subject_id)

    if productivity:
        query += " AND ss.productivity = %s"
        parameters.append(productivity)

    query += " ORDER BY ss.session_id"

    cursor.execute(query, parameters)
    rows = cursor.fetchall()

    cursor.close()
    connection.close()

    sessions = []

    for row in rows:
        sessions.append({
            "session_id": row[0],
            "student_id": row[1],
            "student_name": row[2],
            "subject_id": row[3],
            "subject_name": row[4],
            "subject_code": row[5],
            "session_date": str(row[6]),
            "start_time": str(row[7]) if row[7] else None,
            "end_time": str(row[8]) if row[8] else None,
            "duration_minutes": row[9],
            "productivity": row[10],
            "notes": row[11]
        })

    return sessions


@router.get("/{session_id}")
def get_session(session_id: int):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            ss.session_id,
            ss.student_id,
            s.name AS student_name,
            ss.subject_id,
            sub.subject_name,
            sub.subject_code,
            ss.session_date,
            ss.start_time,
            ss.end_time,
            ss.duration_minutes,
            ss.productivity,
            ss.notes
        FROM study_session ss
        JOIN student s
            ON ss.student_id = s.student_id
        JOIN subject sub
            ON ss.subject_id = sub.subject_id
        WHERE ss.session_id = %s
        """,
        (session_id,)
    )

    row = cursor.fetchone()

    cursor.close()
    connection.close()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Study session not found"
        )

    return {
        "session_id": row[0],
        "student_id": row[1],
        "student_name": row[2],
        "subject_id": row[3],
        "subject_name": row[4],
        "subject_code": row[5],
        "session_date": str(row[6]),
        "start_time": str(row[7]) if row[7] else None,
        "end_time": str(row[8]) if row[8] else None,
        "duration_minutes": row[9],
        "productivity": row[10],
        "notes": row[11]
    }


@router.post("/")
def create_session(session: SessionCreate):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO study_session
            (
                student_id,
                subject_id,
                session_date,
                start_time,
                end_time,
                duration_minutes,
                productivity,
                notes
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING session_id
            """,
            (
                session.student_id,
                session.subject_id,
                session.session_date,
                session.start_time,
                session.end_time,
                session.duration_minutes,
                session.productivity,
                session.notes
            )
        )

        generated_id = cursor.fetchone()[0]

        connection.commit()

        return {
            "message": "Study session created successfully",
            "session_id": generated_id
        }

    except Exception as error:
        connection.rollback()

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    finally:
        cursor.close()
        connection.close()


@router.put("/{session_id}")
def update_session(
    session_id: int,
    session: SessionUpdate
):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            UPDATE study_session
            SET
                student_id = COALESCE(%s, student_id),
                subject_id = COALESCE(%s, subject_id),
                session_date = COALESCE(%s, session_date),
                start_time = COALESCE(%s, start_time),
                end_time = COALESCE(%s, end_time),
                duration_minutes = COALESCE(%s, duration_minutes),
                productivity = COALESCE(%s, productivity),
                notes = COALESCE(%s, notes)
            WHERE session_id = %s
            """,
            (
                session.student_id,
                session.subject_id,
                session.session_date,
                session.start_time,
                session.end_time,
                session.duration_minutes,
                session.productivity,
                session.notes,
                session_id
            )
        )

        if cursor.rowcount == 0:
            connection.rollback()

            raise HTTPException(
                status_code=404,
                detail="Study session not found"
            )

        connection.commit()

        return {
            "message": "Study session updated successfully"
        }

    except HTTPException:
        raise

    except Exception as error:
        connection.rollback()

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    finally:
        cursor.close()
        connection.close()


@router.delete("/{session_id}")
def delete_session(session_id: int):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            DELETE FROM study_session
            WHERE session_id = %s
            """,
            (session_id,)
        )

        if cursor.rowcount == 0:
            connection.rollback()

            raise HTTPException(
                status_code=404,
                detail="Study session not found"
            )

        connection.commit()

        return {
            "message": "Study session deleted successfully"
        }

    except HTTPException:
        raise

    except Exception as error:
        connection.rollback()

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    finally:
        cursor.close()
        connection.close()