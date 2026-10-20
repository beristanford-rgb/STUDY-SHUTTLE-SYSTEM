from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from database import get_connection

router = APIRouter(
    prefix="/stress",
    tags=["Student Stress"]
)


class StressCreate(BaseModel):
    stress_id: int
    student_id: int
    session_id: Optional[int] = None
    stress_level: Optional[int] = None
    reason: Optional[str] = None
    notes: Optional[str] = None


class StressUpdate(BaseModel):
    student_id: Optional[int] = None
    session_id: Optional[int] = None
    stress_level: Optional[int] = None
    reason: Optional[str] = None
    notes: Optional[str] = None


@router.get("/")
def get_stress(
    student_id: Optional[int] = None,
    session_id: Optional[int] = None,
    stress_level: Optional[int] = None
):
    connection = get_connection()
    cursor = connection.cursor()

    query = """
        SELECT
            st.stress_id,
            st.student_id,
            s.name AS student_name,
            st.session_id,
            st.stress_level,
            st.reason,
            st.notes
        FROM student_stress st
        JOIN student s
            ON st.student_id = s.student_id
        WHERE 1=1
    """

    parameters = []

    if student_id:
        query += " AND st.student_id = %s"
        parameters.append(student_id)

    if session_id:
        query += " AND st.session_id = %s"
        parameters.append(session_id)

    if stress_level:
        query += " AND st.stress_level = %s"
        parameters.append(stress_level)

    query += " ORDER BY st.stress_id"

    cursor.execute(query, parameters)
    rows = cursor.fetchall()

    cursor.close()
    connection.close()

    stress_records = []

    for row in rows:
        stress_records.append({
            "stress_id": row[0],
            "student_id": row[1],
            "student_name": row[2],
            "session_id": row[3],
            "stress_level": row[4],
            "reason": row[5],
            "notes": row[6]
        })

    return stress_records


@router.get("/{stress_id}")
def get_stress_record(stress_id: int):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            st.stress_id,
            st.student_id,
            s.name AS student_name,
            st.session_id,
            st.stress_level,
            st.reason,
            st.notes
        FROM student_stress st
        JOIN student s
            ON st.student_id = s.student_id
        WHERE st.stress_id = %s
        """,
        (stress_id,)
    )

    row = cursor.fetchone()

    cursor.close()
    connection.close()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Stress record not found"
        )

    return {
        "stress_id": row[0],
        "student_id": row[1],
        "student_name": row[2],
        "session_id": row[3],
        "stress_level": row[4],
        "reason": row[5],
        "notes": row[6]
    }


@router.post("/")
def create_stress(record: StressCreate):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO student_stress
            (
                stress_id,
                student_id,
                session_id,
                stress_level,
                reason,
                notes
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                record.stress_id,
                record.student_id,
                record.session_id,
                record.stress_level,
                record.reason,
                record.notes
            )
        )

        connection.commit()

        return {
            "message": "Stress record created successfully",
            "stress_id": record.stress_id
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


@router.put("/{stress_id}")
def update_stress(
    stress_id: int,
    record: StressUpdate
):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            UPDATE student_stress
            SET
                student_id = COALESCE(%s, student_id),
                session_id = COALESCE(%s, session_id),
                stress_level = COALESCE(%s, stress_level),
                reason = COALESCE(%s, reason),
                notes = COALESCE(%s, notes)
            WHERE stress_id = %s
            """,
            (
                record.student_id,
                record.session_id,
                record.stress_level,
                record.reason,
                record.notes,
                stress_id
            )
        )

        if cursor.rowcount == 0:
            connection.rollback()

            raise HTTPException(
                status_code=404,
                detail="Stress record not found"
            )

        connection.commit()

        return {
            "message": "Stress record updated successfully"
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


@router.delete("/{stress_id}")
def delete_stress(stress_id: int):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            DELETE FROM student_stress
            WHERE stress_id = %s
            """,
            (stress_id,)
        )

        if cursor.rowcount == 0:
            connection.rollback()

            raise HTTPException(
                status_code=404,
                detail="Stress record not found"
            )

        connection.commit()

        return {
            "message": "Stress record deleted successfully"
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