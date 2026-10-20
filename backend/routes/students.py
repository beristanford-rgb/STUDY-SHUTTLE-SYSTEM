from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from database import get_connection

router = APIRouter(
    prefix="/students",
    tags=["Students"]
)


class StudentCreate(BaseModel):
    student_id: int
    name: str
    email: str
    phone: Optional[str] = None
    program: Optional[str] = None
    semester: Optional[int] = None
    date_of_join: Optional[str] = None


class StudentUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    program: Optional[str] = None
    semester: Optional[int] = None
    date_of_join: Optional[str] = None


@router.get("/")
def get_students(
    search: Optional[str] = None,
    semester: Optional[int] = None,
    program: Optional[str] = None
):
    connection = get_connection()
    cursor = connection.cursor()

    query = """
        SELECT
            student_id,
            name,
            email,
            phone,
            program,
            semester,
            date_of_join
        FROM student
        WHERE 1=1
    """

    parameters = []

    if search:
        query += """
            AND (
                name ILIKE %s
                OR email ILIKE %s
                OR phone ILIKE %s
            )
        """
        search_value = f"%{search}%"
        parameters.extend([
            search_value,
            search_value,
            search_value
        ])

    if semester:
        query += " AND semester = %s"
        parameters.append(semester)

    if program:
        query += " AND program ILIKE %s"
        parameters.append(f"%{program}%")

    query += " ORDER BY student_id"

    cursor.execute(query, parameters)

    rows = cursor.fetchall()

    cursor.close()
    connection.close()

    students = []

    for row in rows:
        students.append({
            "student_id": row[0],
            "name": row[1],
            "email": row[2],
            "phone": row[3],
            "program": row[4],
            "semester": row[5],
            "date_of_join": str(row[6]) if row[6] else None
        })

    return students


@router.get("/{student_id}")
def get_student(student_id: int):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            student_id,
            name,
            email,
            phone,
            program,
            semester,
            date_of_join
        FROM student
        WHERE student_id = %s
        """,
        (student_id,)
    )

    row = cursor.fetchone()

    cursor.close()
    connection.close()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    return {
        "student_id": row[0],
        "name": row[1],
        "email": row[2],
        "phone": row[3],
        "program": row[4],
        "semester": row[5],
        "date_of_join": str(row[6]) if row[6] else None
    }


@router.post("/")
def create_student(student: StudentCreate):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO student
            (
                student_id,
                name,
                email,
                phone,
                program,
                semester,
                date_of_join
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                student.student_id,
                student.name,
                student.email,
                student.phone,
                student.program,
                student.semester,
                student.date_of_join
            )
        )

        connection.commit()

        return {
            "message": "Student created successfully",
            "student_id": student.student_id
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


@router.put("/{student_id}")
def update_student(
    student_id: int,
    student: StudentUpdate
):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            UPDATE student
            SET
                name = COALESCE(%s, name),
                email = COALESCE(%s, email),
                phone = COALESCE(%s, phone),
                program = COALESCE(%s, program),
                semester = COALESCE(%s, semester),
                date_of_join = COALESCE(%s, date_of_join)
            WHERE student_id = %s
            """,
            (
                student.name,
                student.email,
                student.phone,
                student.program,
                student.semester,
                student.date_of_join,
                student_id
            )
        )

        if cursor.rowcount == 0:
            connection.rollback()

            raise HTTPException(
                status_code=404,
                detail="Student not found"
            )

        connection.commit()

        return {
            "message": "Student updated successfully"
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


@router.delete("/{student_id}")
def delete_student(student_id: int):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            "DELETE FROM student WHERE student_id = %s",
            (student_id,)
        )

        if cursor.rowcount == 0:
            connection.rollback()

            raise HTTPException(
                status_code=404,
                detail="Student not found"
            )

        connection.commit()

        return {
            "message": "Student deleted successfully"
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