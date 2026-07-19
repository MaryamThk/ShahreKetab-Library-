from database import fetch_all

query = """
SELECT ISBN, Title, Subject, Price
FROM dbo.Book
ORDER BY Title;
"""

try:
    columns, rows = fetch_all(query)

    print(columns)

    for row in rows:
        print(row)

except Exception as error:
    print("خطا:", error)