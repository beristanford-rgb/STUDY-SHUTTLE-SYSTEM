from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from database import get_connection

router = APIRouter(
    prefix="/tasks",
    tags=["Study Tasks"]
)


class TaskCreate(BaseModel):
    task_id: int
    student_id: int
    subject_id: int
    task_name: str
    description: Optional[str] = None
    deadline: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = "Pending"


class TaskUpdate(BaseModel):
    student_id: Optional[int] = None
    subject_id: Optional[int] = None
    task_name: Optional[str] = None
    description: Optional[str] = None
    deadline: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None


@router.get("/")
def get_tasks(
    search: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    student_id: Optional[int] = None,
    subject_id: Optional[int] = None
):
    connection = get_connection()
    cursor = connection.cursor()

    query = """
        SELECT
            t.task_id,
            t.student_id,
            s.name AS student_name,
            t.subject_id,
            sub.subject_name,
            sub.subject_code,
            t.task_name,
            t.description,
            t.deadline,
            t.priority,
            t.status
        FROM study_task t
        JOIN student s
            ON t.student_id = s.student_id
        JOIN subject sub
            ON t.subject_id = sub.subject_id
        WHERE 1=1
    """

    parameters = []

    if search:
        query += """
            AND (
                t.task_name ILIKE %s
                OR t.description ILIKE %s
                OR s.name ILIKE %s
                OR sub.subject_name ILIKE %s
            )
        """

        search_value = f"%{search}%"

        parameters.extend([
            search_value,
            search_value,
            search_value,
            search_value
        ])

    if status:
        query += " AND t.status ILIKE %s"
        parameters.append(status)

    if priority:
        query += " AND t.priority ILIKE %s"
        parameters.append(priority)

    if student_id:
        query += " AND t.student_id = %s"
        parameters.append(student_id)

    if subject_id:
        query += " AND t.subject_id = %s"
        parameters.append(subject_id)

    query += " ORDER BY t.task_id"

    cursor.execute(query, parameters)

    rows = cursor.fetchall()

    cursor.close()
    connection.close()

    tasks = []

    for row in rows:
        tasks.append({
            "task_id": row[0],
            "student_id": row[1],
            "student_name": row[2],
            "subject_id": row[3],
            "subject_name": row[4],
            "subject_code": row[5],
            "task_name": row[6],
            "description": row[7],
            "deadline": str(row[8]) if row[8] else None,
            "priority": row[9],
            "status": row[10]
        })

    return tasks


@router.get("/{task_id}")
def get_task(task_id: int):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            t.task_id,
            t.student_id,
            s.name AS student_name,
            t.subject_id,
            sub.subject_name,
            sub.subject_code,
            t.task_name,
            t.description,
            t.deadline,
            t.priority,
            t.status
        FROM study_task t
        JOIN student s
            ON t.student_id = s.student_id
        JOIN subject sub
            ON t.subject_id = sub.subject_id
        WHERE t.task_id = %s
        """,
        (task_id,)
    )

    row = cursor.fetchone()

    cursor.close()
    connection.close()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Study task not found"
        )

    return {
        "task_id": row[0],
        "student_id": row[1],
        "student_name": row[2],
        "subject_id": row[3],
        "subject_name": row[4],
        "subject_code": row[5],
        "task_name": row[6],
        "description": row[7],
        "deadline": str(row[8]) if row[8] else None,
        "priority": row[9],
        "status": row[10]
    }


@router.post("/")
def create_task(task: TaskCreate):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO study_task
            (
                task_id,
                student_id,
                subject_id,
                task_name,
                description,
                deadline,
                priority,
                status
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                task.task_id,
                task.student_id,
                task.subject_id,
                task.task_name,
                task.description,
                task.deadline,
                task.priority,
                task.status
            )
        )

        connection.commit()

        return {
            "message": "Study task created successfully",
            "task_id": task.task_id
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


@router.put("/{task_id}")
def update_task(
    task_id: int,
    task: TaskUpdate
):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            UPDATE study_task
            SET
                student_id = COALESCE(%s, student_id),
                subject_id = COALESCE(%s, subject_id),
                task_name = COALESCE(%s, task_name),
                description = COALESCE(%s, description),
                deadline = COALESCE(%s, deadline),
                priority = COALESCE(%s, priority),
                status = COALESCE(%s, status)
            WHERE task_id = %s
            """,
            (
                task.student_id,
                task.subject_id,
                task.task_name,
                task.description,
                task.deadline,
                task.priority,
                task.status,
                task_id
            )
        )

        if cursor.rowcount == 0:
            connection.rollback()

            raise HTTPException(
                status_code=404,
                detail="Study task not found"
            )

        connection.commit()

        return {
            "message": "Study task updated successfully"
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


@router.delete("/{task_id}")
def delete_task(task_id: int):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            DELETE FROM study_task
            WHERE task_id = %s
            """,
            (task_id,)
        )

        if cursor.rowcount == 0:
            connection.rollback()

            raise HTTPException(
                status_code=404,
                detail="Study task not found"
            )

        connection.commit()

        return {
            "message": "Study task deleted successfully"
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