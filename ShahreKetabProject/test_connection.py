import os
import pyodbc

print("فایل در حال اجرا:", os.path.abspath(__file__))
print("درایورهای نصب‌شده:", pyodbc.drivers())

driver = "ODBC Driver 17 for SQL Server"

if driver not in pyodbc.drivers():
    raise RuntimeError(f"درایور {driver} نصب نیست.")

server = r"localhost"
database = "ShahreKetabDB"

connection_string = (
    f"DRIVER={{{driver}}};"
    f"SERVER={server};"
    f"DATABASE={database};"
    "Trusted_Connection=yes;"
    "Encrypt=no;"
)

print("درایور انتخاب‌شده:", driver)

connection = None

try:
    connection = pyodbc.connect(connection_string, timeout=5)
    cursor = connection.cursor()

    cursor.execute("SELECT COUNT(*) FROM dbo.Book;")
    print("اتصال موفق شد.")
    print("تعداد کتاب‌ها:", cursor.fetchone()[0])

except pyodbc.Error as error:
    print("خطای جدید:")
    print(error)

finally:
    if connection is not None:
        connection.close()
        print("اتصال بسته شد.")