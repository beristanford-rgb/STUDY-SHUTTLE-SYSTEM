from fastapi import FastAPI
from database import get_connection

from routes.students import router as students_router
from routes.subjects import router as subjects_router
from routes.sessions import router as sessions_router
from routes.tasks import router as tasks_router
from routes.difficulties import router as difficulties_router
from routes.stress import router as stress_router
from routes.performance import router as performance_router
from routes.queries import router as queries_router

app = FastAPI(
    title="Study Shuttle System API",
    description="Backend API for the Study Shuttle System",
    version="1.0.0"
)


@app.get("/")
def root():
    return {
        "message": "Study Shuttle API is running"
    }


@app.get("/test-db")
def test_database():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT current_database(), current_user;"
    )

    result = cursor.fetchone()

    cursor.close()
    connection.close()

    return {
        "database": result[0],
        "user": result[1],
        "status": "Database connected successfully"
    }


app.include_router(students_router)
app.include_router(subjects_router)
app.include_router(tasks_router)
app.include_router(sessions_router)
app.include_router(difficulties_router)
app.include_router(stress_router)
app.include_router(performance_router)
app.include_router(queries_router)