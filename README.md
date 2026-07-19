# Shahr-e Ketab Chain Store Management System

A Persian-language desktop application for managing multiple bookstore branches. The project was developed as the final assignment for a Database Laboratory course and combines a Tkinter graphical interface with a Microsoft SQL Server database.

The application supports day-to-day bookstore operations such as managing books and branches, tracking inventory, registering sales, identifying debtors and low-stock items, and running database reports.

## Features

- Manage bookstore branches and their managers
- Add, edit, view, and delete book records
- Store multiple authors for each book
- Track book inventory separately for each branch
- Increase or decrease inventory quantities
- Register multi-item sales
- Validate stock before completing a sale
- Roll back the entire transaction if any sale item cannot be processed
- View customers whose debt exceeds a selected amount
- Detect inventory levels below the defined minimum
- Run eleven parameterized reports
- Export report results to UTF-8 CSV files
- Display the database connection status when the application starts

## Reporting

The reporting interface includes queries for:

1. Branches located in a selected city
2. Branches that do not stock books by a selected author
3. Total sales for a branch during a date range
4. Employees working at a selected branch
5. Sales completed by a selected employee
6. Books matching an author or subject
7. Customers whose debt exceeds a selected amount
8. Purchase history for a selected customer
9. Books not sold during a date range
10. Branches where a selected book is below its minimum inventory
11. Outstanding debt to a selected publisher

## Technologies

- Python
- Tkinter and `ttk`
- Microsoft SQL Server
- PyODBC
- T-SQL
- Mermaid for the ER diagram

## Database Design

The database models the following entities:

- City
- Store
- Employee
- Customer
- Publisher
- Author
- Book
- BookAuthor
- Inventory
- Sale
- SaleItem
- PublisherPurchase

The entity-relationship diagram is available in [`ERD.md`](ShahreKetabProject/ERD.md).

## Project Structure

```text
.
├── ShahreKetabProject/
│   ├── main.py                       # Application entry point
│   ├── database.py                   # SQL Server connection and query helpers
│   ├── stores_window.py              # Store management interface
│   ├── books_window.py               # Book and author management interface
│   ├── inventory_window.py           # Inventory management interface
│   ├── sales_window.py               # Transactional sales registration
│   ├── debtors_window.py             # Debtor-customer report
│   ├── critical_inventory_window.py  # Low-stock report
│   ├── reports_window.py             # Search and reporting interface
│   ├── ui_helpers.py                 # Shared table and CSV utilities
│   ├── final_queries.sql             # Standalone T-SQL report queries
│   ├── optional_setup.sql            # Optional table and performance indexes
│   ├── ERD.md                        # Database entity-relationship diagram
│   ├── test_connection.py            # SQL Server connection test
│   └── test_database.py              # Basic database query test
└── README.md
```

## Prerequisites

Before running the application, install:

- Python 3.10 or later
- Microsoft SQL Server
- Microsoft ODBC Driver 17 for SQL Server
- The `pyodbc` Python package

Install the Python dependency with:

```bash
pip install pyodbc
```

> The repository expects an existing SQL Server database whose schema matches the entities documented in `ERD.md`. A complete database creation and sample-data script is not currently included.

## Configuration

Open:

```text
ShahreKetabProject/database.py
```

Update these values to match your SQL Server installation:

```python
DRIVER = "ODBC Driver 17 for SQL Server"
SERVER = r"localhost"
DATABASE = "ShahreKetabDB"
```

The default connection uses Windows Authentication:

```text
Trusted_Connection=yes
```

The optional [`optional_setup.sql`](ShahreKetabProject/optional_setup.sql) script creates the `PublisherPurchase` table when needed and adds indexes used by several reports.

## Running the Application

Move into the project directory:

```bash
cd ShahreKetabProject
```

Test the database connection:

```bash
python test_connection.py
```

Start the desktop application:

```bash
python main.py
```

## Application Workflow

```text
Tkinter interface
       │
       ▼
Input validation
       │
       ▼
PyODBC database layer
       │
       ▼
Microsoft SQL Server
       │
       ├── Books and authors
       ├── Stores and employees
       ├── Inventory
       ├── Sales and sale items
       └── Reports
```

Sales are stored as database transactions. Inventory is reduced only when sufficient stock exists, and all changes are rolled back if any item in the invoice fails.

## Notes

- The graphical interface is in Persian.
- Dates are entered in `YYYY-MM-DD` format.
- The current connection configuration is designed primarily for Windows and SQL Server.
- Generated Python cache folders such as `__pycache__` are not required in the repository and can be removed.

## Future Improvements

- Include a complete database creation and seed script
- Move connection settings to environment variables or a configuration file
- Add a `requirements.txt` file
- Add automated tests
- Add screenshots of the main interface and reports
- Package the application as a Windows executable
- Add authentication and user roles
