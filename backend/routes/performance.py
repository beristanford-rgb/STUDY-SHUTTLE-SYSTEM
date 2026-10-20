from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from database import get_connection

router = APIRouter(
    prefix="/performance",
    tags=["Performance"]
)


class PerformanceCreate(BaseModel):
    performance_id: int
    student_id: int
    subject_id: int
    assessment_type: Optional[str] = None
    assessment_name: Optional[str] = None
    marks_obtained: Optional[float] = None
    max_marks: Optional[float] = None
    assessment_date: Optional[str] = None
    remarks: Optional[str] = None


class PerformanceUpdate(BaseModel):
    student_id: Optional[int] = None
    subject_id: Optional[int] = None
    assessment_type: Optional[str] = None
    assessment_name: Optional[str] = None
    marks_obtained: Optional[float] = None
    max_marks: Optional[float] = None
    assessment_date: Optional[str] = None
    remarks: Optional[str] = None


@router.get("/")
def get_performance(
    student_id: Optional[int] = None,
    subject_id: Optional[int] = None,
    assessment_type: Optional[str] = None
):
    connection = get_connection()
    cursor = connection.cursor()

    query = """
        SELECT
            p.performance_id,
            p.student_id,
            s.name AS student_name,
            p.subject_id,
            sub.subject_name,
            sub.subject_code,
            p.assessment_type,
            p.assessment_name,
            p.marks_obtained,
            p.max_marks,
            p.assessment_date,
            p.remarks
        FROM performance p
        JOIN student s
            ON p.student_id = s.student_id
        JOIN subject sub
            ON p.subject_id = sub.subject_id
        WHERE 1=1
    """

    parameters = []

    if student_id:
        query += " AND p.student_id = %s"
        parameters.append(student_id)

    if subject_id:
        query += " AND p.subject_id = %s"
        parameters.append(subject_id)

    if assessment_type:
        query += " AND p.assessment_type ILIKE %s"
        parameters.append(assessment_type)

    query += " ORDER BY p.performance_id"

    cursor.execute(query, parameters)
    rows = cursor.fetchall()

    cursor.close()
    connection.close()

    performance_records = []

    for row in rows:
        performance_records.append({
            "performance_id": row[0],
            "student_id": row[1],
            "student_name": row[2],
            "subject_id": row[3],
            "subject_name": row[4],
            "subject_code": row[5],
            "assessment_type": row[6],
            "assessment_name": row[7],
            "marks_obtained": float(row[8]) if row[8] is not None else None,
            "max_marks": float(row[9]) if row[9] is not None else None,
            "assessment_date": str(row[10]) if row[10] else None,
            "remarks": row[11]
        })

    return performance_records


@router.get("/{performance_id}")
def get_performance_record(performance_id: int):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            p.performance_id,
            p.student_id,
            s.name AS student_name,
            p.subject_id,
            sub.subject_name,
            sub.subject_code,
            p.assessment_type,
            p.assessment_name,
            p.marks_obtained,
            p.max_marks,
            p.assessment_date,
            p.remarks
        FROM performance p
        JOIN student s
            ON p.student_id = s.student_id
        JOIN subject sub
            ON p.subject_id = sub.subject_id
        WHERE p.performance_id = %s
        """,
        (performance_id,)
    )

    row = cursor.fetchone()

    cursor.close()
    connection.close()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Performance record not found"
        )

    return {
        "performance_id": row[0],
        "student_id": row[1],
        "student_name": row[2],
        "subject_id": row[3],
        "subject_name": row[4],
        "subject_code": row[5],
        "assessment_type": row[6],
        "assessment_name": row[7],
        "marks_obtained": float(row[8]) if row[8] is not None else None,
        "max_marks": float(row[9]) if row[9] is not None else None,
        "assessment_date": str(row[10]) if row[10] else None,
        "remarks": row[11]
    }


@router.post("/")
def create_performance(record: PerformanceCreate):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO performance
            (
                performance_id,
                student_id,
                subject_id,
                assessment_type,
                assessment_name,
                marks_obtained,
                max_marks,
                assessment_date,
                remarks
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                record.performance_id,
                record.student_id,
                record.subject_id,
                record.assessment_type,
                record.assessment_name,
                record.marks_obtained,
                record.max_marks,
                record.assessment_date,
                record.remarks
            )
        )

        connection.commit()

        return {
            "message": "Performance record created successfully",
            "performance_id": record.performance_id
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


@router.put("/{performance_id}")
def update_performance(
    performance_id: int,
    record: PerformanceUpdate
):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            UPDATE performance
            SET
                student_id = COALESCE(%s, student_id),
                subject_id = COALESCE(%s, subject_id),
                assessment_type = COALESCE(%s, assessment_type),
                assessment_name = COALESCE(%s, assessment_name),
                marks_obtained = COALESCE(%s, marks_obtained),
                max_marks = COALESCE(%s, max_marks),
                assessment_date = COALESCE(%s, assessment_date),
                remarks = COALESCE(%s, remarks)
            WHERE performance_id = %s
            """,
            (
                record.student_id,
                record.subject_id,
                record.assessment_type,
                record.assessment_name,
                record.marks_obtained,
                record.max_marks,
                record.assessment_date,
                record.remarks,
                performance_id
            )
        )

        if cursor.rowcount == 0:
            connection.rollback()

            raise HTTPException(
                status_code=404,
                detail="Performance record not found"
            )

        connection.commit()

        return {
            "message": "Performance record updated successfully"
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


@router.delete("/{performance_id}")
def delete_performance(performance_id: int):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            DELETE FROM performance
            WHERE performance_id = %s
            """,
            (performance_id,)
        )

        if cursor.rowcount == 0:
            connection.rollback()

            raise HTTPException(
                status_code=404,
                detail="Performance record not found"
            )

        connection.commit()

        return {
            "message": "Performance record deleted successfully"
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