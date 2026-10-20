from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from database import get_connection

router = APIRouter(
    prefix="/subjects",
    tags=["Subjects"]
)


class SubjectCreate(BaseModel):
    subject_id: int
    subject_name: str
    subject_code: str
    difficulty_level: Optional[str] = None


class SubjectUpdate(BaseModel):
    subject_name: Optional[str] = None
    subject_code: Optional[str] = None
    difficulty_level: Optional[str] = None


@router.get("/")
def get_subjects(
    search: Optional[str] = None,
    difficulty: Optional[str] = None
):
    connection = get_connection()
    cursor = connection.cursor()

    query = """
        SELECT
            subject_id,
            subject_name,
            subject_code,
            difficulty_level
        FROM subject
        WHERE 1=1
    """

    parameters = []

    if search:
        query += """
            AND (
                subject_name ILIKE %s
                OR subject_code ILIKE %s
            )
        """

        search_value = f"%{search}%"
        parameters.extend([search_value, search_value])

    if difficulty:
        query += " AND difficulty_level ILIKE %s"
        parameters.append(difficulty)

    query += " ORDER BY subject_id"

    cursor.execute(query, parameters)
    rows = cursor.fetchall()

    cursor.close()
    connection.close()

    subjects = []

    for row in rows:
        subjects.append({
            "subject_id": row[0],
            "subject_name": row[1],
            "subject_code": row[2],
            "difficulty_level": row[3]
        })

    return subjects


@router.get("/{subject_id}")
def get_subject(subject_id: int):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            subject_id,
            subject_name,
            subject_code,
            difficulty_level
        FROM subject
        WHERE subject_id = %s
        """,
        (subject_id,)
    )

    row = cursor.fetchone()

    cursor.close()
    connection.close()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Subject not found"
        )

    return {
        "subject_id": row[0],
        "subject_name": row[1],
        "subject_code": row[2],
        "difficulty_level": row[3]
    }


@router.post("/")
def create_subject(subject: SubjectCreate):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO subject
            (
                subject_id,
                subject_name,
                subject_code,
                difficulty_level
            )
            VALUES (%s, %s, %s, %s)
            """,
            (
                subject.subject_id,
                subject.subject_name,
                subject.subject_code,
                subject.difficulty_level
            )
        )

        connection.commit()

        return {
            "message": "Subject created successfully",
            "subject_id": subject.subject_id
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


@router.put("/{subject_id}")
def update_subject(
    subject_id: int,
    subject: SubjectUpdate
):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            UPDATE subject
            SET
                subject_name = COALESCE(%s, subject_name),
                subject_code = COALESCE(%s, subject_code),
                difficulty_level = COALESCE(%s, difficulty_level)
            WHERE subject_id = %s
            """,
            (
                subject.subject_name,
                subject.subject_code,
                subject.difficulty_level,
                subject_id
            )
        )

        if cursor.rowcount == 0:
            connection.rollback()

            raise HTTPException(
                status_code=404,
                detail="Subject not found"
            )

        connection.commit()

        return {
            "message": "Subject updated successfully"
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


@router.delete("/{subject_id}")
def delete_subject(subject_id: int):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            DELETE FROM subject
            WHERE subject_id = %s
            """,
            (subject_id,)
        )

        if cursor.rowcount == 0:
            connection.rollback()

            raise HTTPException(
                status_code=404,
                detail="Subject not found"
            )

        connection.commit()

        return {
            "message": "Subject deleted successfully"
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