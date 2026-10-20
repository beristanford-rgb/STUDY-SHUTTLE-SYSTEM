from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from database import get_connection

router = APIRouter(
    prefix="/difficulties",
    tags=["Difficulties"]
)


class DifficultyCreate(BaseModel):
    difficulty_id: int
    session_id: int
    difficulty_type: str
    description: Optional[str] = None
    severity: Optional[int] = None
    resolved: Optional[bool] = False
    resolved_date: Optional[str] = None


class DifficultyUpdate(BaseModel):
    session_id: Optional[int] = None
    difficulty_type: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[int] = None
    resolved: Optional[bool] = None
    resolved_date: Optional[str] = None


@router.get("/")
def get_difficulties(
    resolved: Optional[bool] = None,
    severity: Optional[int] = None,
    session_id: Optional[int] = None
):
    connection = get_connection()
    cursor = connection.cursor()

    query = """
        SELECT
            d.difficulty_id,
            d.session_id,
            ss.student_id,
            s.name AS student_name,
            ss.subject_id,
            sub.subject_name,
            d.difficulty_type,
            d.description,
            d.severity,
            d.resolved,
            d.resolved_date
        FROM difficulty d
        JOIN study_session ss
            ON d.session_id = ss.session_id
        JOIN student s
            ON ss.student_id = s.student_id
        JOIN subject sub
            ON ss.subject_id = sub.subject_id
        WHERE 1=1
    """

    parameters = []

    if resolved is not None:
        query += " AND d.resolved = %s"
        parameters.append(resolved)

    if severity:
        query += " AND d.severity = %s"
        parameters.append(severity)

    if session_id:
        query += " AND d.session_id = %s"
        parameters.append(session_id)

    query += " ORDER BY d.difficulty_id"

    cursor.execute(query, parameters)
    rows = cursor.fetchall()

    cursor.close()
    connection.close()

    difficulties = []

    for row in rows:
        difficulties.append({
            "difficulty_id": row[0],
            "session_id": row[1],
            "student_id": row[2],
            "student_name": row[3],
            "subject_id": row[4],
            "subject_name": row[5],
            "difficulty_type": row[6],
            "description": row[7],
            "severity": row[8],
            "resolved": row[9],
            "resolved_date": str(row[10]) if row[10] else None
        })

    return difficulties


@router.get("/{difficulty_id}")
def get_difficulty(difficulty_id: int):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            d.difficulty_id,
            d.session_id,
            ss.student_id,
            s.name AS student_name,
            ss.subject_id,
            sub.subject_name,
            d.difficulty_type,
            d.description,
            d.severity,
            d.resolved,
            d.resolved_date
        FROM difficulty d
        JOIN study_session ss
            ON d.session_id = ss.session_id
        JOIN student s
            ON ss.student_id = s.student_id
        JOIN subject sub
            ON ss.subject_id = sub.subject_id
        WHERE d.difficulty_id = %s
        """,
        (difficulty_id,)
    )

    row = cursor.fetchone()

    cursor.close()
    connection.close()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Difficulty record not found"
        )

    return {
        "difficulty_id": row[0],
        "session_id": row[1],
        "student_id": row[2],
        "student_name": row[3],
        "subject_id": row[4],
        "subject_name": row[5],
        "difficulty_type": row[6],
        "description": row[7],
        "severity": row[8],
        "resolved": row[9],
        "resolved_date": str(row[10]) if row[10] else None
    }


@router.post("/")
def create_difficulty(record: DifficultyCreate):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO difficulty
            (
                difficulty_id,
                session_id,
                difficulty_type,
                description,
                severity,
                resolved,
                resolved_date
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                record.difficulty_id,
                record.session_id,
                record.difficulty_type,
                record.description,
                record.severity,
                record.resolved,
                record.resolved_date
            )
        )

        connection.commit()

        return {
            "message": "Difficulty record created successfully",
            "difficulty_id": record.difficulty_id
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


@router.put("/{difficulty_id}")
def update_difficulty(
    difficulty_id: int,
    record: DifficultyUpdate
):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            UPDATE difficulty
            SET
                session_id = COALESCE(%s, session_id),
                difficulty_type = COALESCE(%s, difficulty_type),
                description = COALESCE(%s, description),
                severity = COALESCE(%s, severity),
                resolved = COALESCE(%s, resolved),
                resolved_date = COALESCE(%s, resolved_date)
            WHERE difficulty_id = %s
            """,
            (
                record.session_id,
                record.difficulty_type,
                record.description,
                record.severity,
                record.resolved,
                record.resolved_date,
                difficulty_id
            )
        )

        if cursor.rowcount == 0:
            connection.rollback()

            raise HTTPException(
                status_code=404,
                detail="Difficulty record not found"
            )

        connection.commit()

        return {
            "message": "Difficulty record updated successfully"
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


@router.delete("/{difficulty_id}")
def delete_difficulty(difficulty_id: int):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            DELETE FROM difficulty
            WHERE difficulty_id = %s
            """,
            (difficulty_id,)
        )

        if cursor.rowcount == 0:
            connection.rollback()

            raise HTTPException(
                status_code=404,
                detail="Difficulty record not found"
            )

        connection.commit()

        return {
            "message": "Difficulty record deleted successfully"
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