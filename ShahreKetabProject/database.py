import pyodbc

DRIVER = "ODBC Driver 17 for SQL Server"
SERVER = r"localhost"
DATABASE = "ShahreKetabDB"

CONNECTION_STRING = (
    f"DRIVER={{{DRIVER}}};"
    f"SERVER={SERVER};"
    f"DATABASE={DATABASE};"
    "Trusted_Connection=yes;"
    "Encrypt=no;"
)


def get_connection(autocommit=False):
    """یک اتصال جدید به SQL Server می‌سازد."""
    return pyodbc.connect(
        CONNECTION_STRING,
        timeout=10,
        autocommit=autocommit,
    )


def fetch_all(query, parameters=()):
    """یک SELECT اجرا می‌کند و نام ستون‌ها و همه ردیف‌ها را برمی‌گرداند."""
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(query, parameters)
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        return columns, rows
    finally:
        if connection is not None:
            connection.close()


def fetch_one(query, parameters=()):
    """یک SELECT اجرا می‌کند و فقط یک ردیف برمی‌گرداند."""
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(query, parameters)
        return cursor.fetchone()
    finally:
        if connection is not None:
            connection.close()


def execute_query(query, parameters=()):
    """یک INSERT، UPDATE یا DELETE اجرا می‌کند."""
    connection = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(query, parameters)
        affected_rows = cursor.rowcount
        connection.commit()
        return affected_rows
    except Exception:
        if connection is not None:
            connection.rollback()
        raise
    finally:
        if connection is not None:
            connection.close()


def test_connection():
    """در شروع برنامه اتصال و وجود دیتابیس را آزمایش می‌کند."""
    row = fetch_one("SELECT DB_NAME(), COUNT(*) FROM dbo.Book;")
    return row[0], row[1]
