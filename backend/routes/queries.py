
from fastapi import APIRouter
from pydantic import BaseModel
from database import get_connection
import re


router = APIRouter(
    prefix="/queries",
    tags=["Advanced SQL Queries"]
)


# =========================================================
# PYDANTIC MODELS
# =========================================================

class SQLQuery(BaseModel):
    sql: str


class QueryBuilder(BaseModel):
    table: str
    columns: list[str] = ["*"]
    conditions: list[dict] = []
    order_by: str | None = None
    order_direction: str = "ASC"
    limit: int | None = None


# =========================================================
# 1. SQL QUERY CONSOLE
# =========================================================

@router.post("/execute")
def execute_query(query: SQLQuery):

    sql = query.sql.strip()

    if not sql:
        return {
            "success": False,
            "message": "SQL query cannot be empty."
        }

    # Remove leading whitespace and SQL comments
    cleaned_sql = re.sub(
        r"^(?:\s|--[^\n]*\n|/\*.*?\*/)*",
        "",
        sql,
        flags=re.DOTALL
    ).strip()

    # Only SELECT and WITH queries are allowed
    if not (
        cleaned_sql.upper().startswith("SELECT")
        or cleaned_sql.upper().startswith("WITH")
    ):
        return {
            "success": False,
            "message": "Only SELECT queries are allowed."
        }

    # Prevent multiple SQL statements
    if ";" in cleaned_sql[:-1]:
        return {
            "success": False,
            "message": "Multiple SQL statements are not allowed."
        }

    # Prevent modification/admin operations
    forbidden = [
        "INSERT",
        "UPDATE",
        "DELETE",
        "DROP",
        "ALTER",
        "TRUNCATE",
        "CREATE",
        "GRANT",
        "REVOKE",
        "CALL",
        "DO"
    ]

    upper_sql = cleaned_sql.upper()

    for keyword in forbidden:

        if re.search(
            r"\b" + keyword + r"\b",
            upper_sql
        ):
            return {
                "success": False,
                "message": f"{keyword} operation is not allowed."
            }

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        # Start read-only transaction
        cursor.execute("BEGIN")
        cursor.execute("SET TRANSACTION READ ONLY")

        cursor.execute(cleaned_sql)

        rows = cursor.fetchall()

        columns = [
            description.name
            for description in cursor.description
        ]

        connection.rollback()

        return {
            "success": True,
            "columns": columns,
            "rows": [
                list(row)
                for row in rows
            ],
            "row_count": len(rows)
        }

    except Exception as e:

        if connection:
            connection.rollback()

        return {
            "success": False,
            "message": str(e)
        }

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# 2. GET ALL DATABASE TABLES
# =========================================================

@router.get("/tables")
def get_tables():

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)

        tables = [
            row[0]
            for row in cursor.fetchall()
        ]

        return {
            "success": True,
            "tables": tables
        }

    except Exception as e:

        return {
            "success": False,
            "message": str(e)
        }

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# 3. GET COLUMNS OF ONE TABLE
# =========================================================

@router.get("/schema/{table_name}")
def get_table_schema(table_name: str):

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                column_name,
                data_type,
                is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name = %s
            ORDER BY ordinal_position;
        """, (table_name,))

        rows = cursor.fetchall()

        if not rows:

            return {
                "success": False,
                "message": "Table not found."
            }

        columns = []

        for row in rows:

            columns.append({
                "column_name": row[0],
                "data_type": row[1],
                "nullable": row[2]
            })

        return {
            "success": True,
            "table": table_name,
            "columns": columns
        }

    except Exception as e:

        return {
            "success": False,
            "message": str(e)
        }

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# 4. GET COMPLETE DATABASE SCHEMA
# =========================================================

@router.get("/database-schema")
def get_database_schema():

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                table_name,
                column_name,
                data_type,
                is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public'
            ORDER BY table_name, ordinal_position;
        """)

        rows = cursor.fetchall()

        schema = {}

        for (
            table_name,
            column_name,
            data_type,
            nullable
        ) in rows:

            if table_name not in schema:
                schema[table_name] = []

            schema[table_name].append({
                "column_name": column_name,
                "data_type": data_type,
                "nullable": nullable
            })

        return {
            "success": True,
            "schema": schema
        }

    except Exception as e:

        return {
            "success": False,
            "message": str(e)
        }

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# 5. QUERY BUILDER
# =========================================================

@router.post("/build")
def build_query(query: QueryBuilder):

    # Allowed application tables
    allowed_tables = {
        "student",
        "subject",
        "study_task",
        "study_session",
        "difficulty",
        "student_stress",
        "performance"
    }

    if query.table not in allowed_tables:

        return {
            "success": False,
            "message": "Invalid table."
        }

    connection = None
    cursor = None

    try:

        connection = get_connection()
        cursor = connection.cursor()

        # -------------------------------------------------
        # Get valid columns
        # -------------------------------------------------

        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name = %s;
        """, (query.table,))

        valid_columns = {
            row[0]
            for row in cursor.fetchall()
        }

        # -------------------------------------------------
        # Validate selected columns
        # -------------------------------------------------

        if query.columns == ["*"]:

            selected_columns = "*"

        else:

            for column in query.columns:

                if column not in valid_columns:

                    return {
                        "success": False,
                        "message": f"Invalid column: {column}"
                    }

            selected_columns = ", ".join(
                query.columns
            )

        # -------------------------------------------------
        # Build SELECT
        # -------------------------------------------------

        sql = (
            f"SELECT {selected_columns} "
            f"FROM {query.table}"
        )

        values = []
        where_parts = []

        # -------------------------------------------------
        # Allowed operators
        # -------------------------------------------------

        allowed_operators = {
            "=",
            "!=",
            ">",
            "<",
            ">=",
            "<=",
            "LIKE",
            "ILIKE"
        }

        # -------------------------------------------------
        # Build WHERE conditions
        # -------------------------------------------------

        for condition in query.conditions:

            column = condition.get("column")
            operator = condition.get("operator")
            value = condition.get("value")

            # Validate column
            if column not in valid_columns:

                return {
                    "success": False,
                    "message": (
                        f"Invalid condition column: {column}"
                    )
                }

            # Validate operator
            if operator not in allowed_operators:

                return {
                    "success": False,
                    "message": (
                        f"Invalid operator: {operator}"
                    )
                }

            where_parts.append(
                f"{column} {operator} %s"
            )

            values.append(value)

        # -------------------------------------------------
        # Add WHERE
        # -------------------------------------------------

        if where_parts:

            sql += (
                " WHERE "
                + " AND ".join(where_parts)
            )

        # -------------------------------------------------
        # ORDER BY
        # -------------------------------------------------

        if query.order_by:

            if query.order_by not in valid_columns:

                return {
                    "success": False,
                    "message": "Invalid ORDER BY column."
                }

            direction = query.order_direction.upper()

            if direction not in {"ASC", "DESC"}:

                return {
                    "success": False,
                    "message": "Invalid sort direction."
                }

            sql += (
                f" ORDER BY "
                f"{query.order_by} "
                f"{direction}"
            )

        # -------------------------------------------------
        # LIMIT
        # -------------------------------------------------

        if query.limit is not None:

            if query.limit <= 0:

                return {
                    "success": False,
                    "message": "LIMIT must be greater than 0."
                }

            sql += f" LIMIT {query.limit}"

        # -------------------------------------------------
        # Return generated SQL
        # -------------------------------------------------

        return {
            "success": True,
            "sql": sql,
            "parameters": values
        }

    except Exception as e:

        return {
            "success": False,
            "message": str(e)
        }

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()
