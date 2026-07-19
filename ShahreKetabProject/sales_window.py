from datetime import datetime
from decimal import Decimal
import tkinter as tk
from tkinter import messagebox, ttk

from database import fetch_all, get_connection
from ui_helpers import clear_tree, make_scrollable_tree


def open_sales_window(parent):
    window = tk.Toplevel(parent)
    window.title("ثبت فروش جدید")
    window.geometry("1180x720")
    window.minsize(1000, 620)

    ttk.Label(
        window,
        text="ثبت فاکتور فروش جدید",
        font=("Tahoma", 17, "bold"),
    ).pack(pady=(14, 6))

    invoice_frame = ttk.LabelFrame(window, text="اطلاعات فاکتور", padding=12)
    invoice_frame.pack(fill="x", padx=15, pady=6)

    store_var = tk.StringVar()
    customer_var = tk.StringVar()
    employee_var = tk.StringVar()
    date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))

    ttk.Label(invoice_frame, text="فروشگاه:").grid(row=0, column=0, padx=6, pady=6)
    store_combo = ttk.Combobox(
        invoice_frame,
        textvariable=store_var,
        state="readonly",
        width=34,
        justify="right",
    )
    store_combo.grid(row=0, column=1, padx=6, pady=6)

    ttk.Label(invoice_frame, text="مشتری:").grid(row=0, column=2, padx=6, pady=6)
    customer_combo = ttk.Combobox(
        invoice_frame,
        textvariable=customer_var,
        state="readonly",
        width=34,
        justify="right",
    )
    customer_combo.grid(row=0, column=3, padx=6, pady=6)

    ttk.Label(invoice_frame, text="کارمند:").grid(row=1, column=0, padx=6, pady=6)
    employee_combo = ttk.Combobox(
        invoice_frame,
        textvariable=employee_var,
        state="readonly",
        width=34,
        justify="right",
    )
    employee_combo.grid(row=1, column=1, padx=6, pady=6)

    ttk.Label(invoice_frame, text="تاریخ (YYYY-MM-DD):").grid(
        row=1, column=2, padx=6, pady=6
    )
    ttk.Entry(
        invoice_frame,
        textvariable=date_var,
        width=37,
        justify="right",
    ).grid(row=1, column=3, padx=6, pady=6)

    item_frame = ttk.LabelFrame(window, text="افزودن کتاب به فاکتور", padding=12)
    item_frame.pack(fill="x", padx=15, pady=6)

    book_var = tk.StringVar()
    quantity_var = tk.StringVar(value="1")

    ttk.Label(item_frame, text="کتاب:").grid(row=0, column=0, padx=6, pady=6)
    book_combo = ttk.Combobox(
        item_frame,
        textvariable=book_var,
        state="readonly",
        width=65,
        justify="right",
    )
    book_combo.grid(row=0, column=1, padx=6, pady=6)

    ttk.Label(item_frame, text="تعداد:").grid(row=0, column=2, padx=6, pady=6)
    ttk.Entry(
        item_frame,
        textvariable=quantity_var,
        width=12,
        justify="right",
    ).grid(row=0, column=3, padx=6, pady=6)

    table_frame, tree = make_scrollable_tree(window)
    table_frame.pack(fill="both", expand=True, padx=15, pady=8)

    columns = ("شابک", "عنوان کتاب", "تعداد", "قیمت واحد", "مبلغ ردیف")
    widths = (120, 280, 100, 130, 150)
    tree.configure(columns=columns)
    for name, width in zip(columns, widths):
        tree.heading(name, text=name)
        tree.column(name, width=width, anchor="center")

    total_var = tk.StringVar(value="مبلغ کل فاکتور: 0")
    ttk.Label(
        window,
        textvariable=total_var,
        font=("Tahoma", 12, "bold"),
    ).pack(pady=4)

    stores = {}
    customers = {}
    employees = {}
    books = {}
    invoice_items = []

    def load_stores_and_customers():
        nonlocal stores, customers
        _, store_rows = fetch_all(
            """
            SELECT s.StoreCode, c.CityName, s.Address
            FROM dbo.Store AS s
            INNER JOIN dbo.City AS c ON c.CityCode = s.CityCode
            ORDER BY s.StoreCode;
            """
        )
        stores = {
            f"{row[0]} - {row[1]} - {row[2]}": int(row[0])
            for row in store_rows
        }
        store_combo.configure(values=list(stores.keys()))

        _, customer_rows = fetch_all(
            """
            SELECT CustomerCode, FullName, Phone
            FROM dbo.Customer
            ORDER BY FullName;
            """
        )
        customers = {
            f"{row[0]} - {row[1]} - {row[2] or ''}": int(row[0])
            for row in customer_rows
        }
        customer_combo.configure(values=list(customers.keys()))

    def load_store_dependencies(_event=None):
        nonlocal employees, books, invoice_items
        selected = store_var.get()
        if not selected:
            return
        store_code = stores[selected]

        if invoice_items:
            invoice_items = []
            refresh_items()

        _, employee_rows = fetch_all(
            """
            SELECT NationalCode, FullName
            FROM dbo.Employee
            WHERE StoreCode = ?
            ORDER BY FullName;
            """,
            (store_code,),
        )
        employees = {
            f"{row[0]} - {row[1]}": str(row[0])
            for row in employee_rows
        }
        employee_combo.configure(values=list(employees.keys()))
        employee_var.set("")

        _, book_rows = fetch_all(
            """
            SELECT i.ISBN, b.Title, b.Price, i.AvailableQuantity
            FROM dbo.Inventory AS i
            INNER JOIN dbo.Book AS b ON b.ISBN = i.ISBN
            WHERE i.StoreCode = ? AND i.AvailableQuantity > 0
            ORDER BY b.Title;
            """,
            (store_code,),
        )
        books = {}
        for row in book_rows:
            display = (
                f"{row[0]} - {row[1]} | موجودی: {row[3]} | قیمت: {row[2]:,.0f}"
            )
            books[display] = {
                "isbn": str(row[0]),
                "title": str(row[1]),
                "price": Decimal(row[2]),
                "stock": int(row[3]),
            }
        book_combo.configure(values=list(books.keys()))
        book_var.set("")

    def refresh_items():
        clear_tree(tree)
        total = Decimal("0")
        for item in invoice_items:
            line_total = item["price"] * item["quantity"]
            total += line_total
            tree.insert(
                "",
                "end",
                values=(
                    item["isbn"],
                    item["title"],
                    item["quantity"],
                    f"{item['price']:,.0f}",
                    f"{line_total:,.0f}",
                ),
            )
        total_var.set(f"مبلغ کل فاکتور: {total:,.0f}")

    def add_item():
        selected_book = book_var.get()
        if not selected_book:
            messagebox.showwarning(
                "انتخاب کتاب",
                "ابتدا یک کتاب را انتخاب کنید.",
                parent=window,
            )
            return
        try:
            quantity = int(quantity_var.get().strip())
            if quantity <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning(
                "تعداد نامعتبر",
                "تعداد باید یک عدد صحیح مثبت باشد.",
                parent=window,
            )
            return

        book = books[selected_book]
        existing = next(
            (item for item in invoice_items if item["isbn"] == book["isbn"]),
            None,
        )
        current_quantity = existing["quantity"] if existing else 0
        if current_quantity + quantity > book["stock"]:
            messagebox.showwarning(
                "موجودی ناکافی",
                f"موجودی قابل فروش این کتاب {book['stock']} عدد است.",
                parent=window,
            )
            return

        if existing:
            existing["quantity"] += quantity
        else:
            invoice_items.append(
                {
                    "isbn": book["isbn"],
                    "title": book["title"],
                    "price": book["price"],
                    "quantity": quantity,
                }
            )
        refresh_items()
        quantity_var.set("1")

    def remove_item():
        selection = tree.selection()
        if not selection:
            messagebox.showwarning(
                "انتخاب ردیف",
                "یک ردیف فاکتور را انتخاب کنید.",
                parent=window,
            )
            return
        isbn = tree.item(selection[0], "values")[0]
        invoice_items[:] = [item for item in invoice_items if item["isbn"] != isbn]
        refresh_items()

    def clear_form():
        nonlocal invoice_items
        customer_var.set("")
        employee_var.set("")
        book_var.set("")
        quantity_var.set("1")
        date_var.set(datetime.now().strftime("%Y-%m-%d"))
        invoice_items = []
        refresh_items()
        if store_var.get():
            load_store_dependencies()

    def save_sale():
        if not store_var.get() or not customer_var.get() or not employee_var.get():
            messagebox.showwarning(
                "اطلاعات ناقص",
                "فروشگاه، مشتری و کارمند را انتخاب کنید.",
                parent=window,
            )
            return
        if not invoice_items:
            messagebox.showwarning(
                "فاکتور خالی",
                "حداقل یک کتاب به فاکتور اضافه کنید.",
                parent=window,
            )
            return
        try:
            invoice_date = datetime.strptime(date_var.get().strip(), "%Y-%m-%d").date()
        except ValueError:
            messagebox.showwarning(
                "تاریخ نامعتبر",
                "تاریخ را به شکل YYYY-MM-DD وارد کنید.",
                parent=window,
            )
            return

        store_code = stores[store_var.get()]
        customer_code = customers[customer_var.get()]
        employee_code = employees[employee_var.get()]
        connection = None
        try:
            connection = get_connection()
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT ISNULL(MAX(InvoiceNumber), 0) + 1
                FROM dbo.Sale WITH (UPDLOCK, HOLDLOCK);
                """
            )
            invoice_number = int(cursor.fetchone()[0])

            cursor.execute(
                """
                INSERT INTO dbo.Sale
                    (InvoiceNumber, InvoiceDate, CustomerCode, StoreCode, EmployeeNationalCode)
                VALUES (?, ?, ?, ?, ?);
                """,
                invoice_number,
                invoice_date,
                customer_code,
                store_code,
                employee_code,
            )

            total = Decimal("0")
            for line_number, item in enumerate(invoice_items, start=1):
                cursor.execute(
                    """
                    UPDATE dbo.Inventory WITH (ROWLOCK)
                    SET AvailableQuantity = AvailableQuantity - ?
                    WHERE StoreCode = ? AND ISBN = ?
                      AND AvailableQuantity >= ?;
                    """,
                    item["quantity"],
                    store_code,
                    item["isbn"],
                    item["quantity"],
                )
                if cursor.rowcount != 1:
                    raise ValueError(
                        f"موجودی کتاب «{item['title']}» برای ثبت فروش کافی نیست."
                    )

                cursor.execute(
                    """
                    INSERT INTO dbo.SaleItem
                        (InvoiceNumber, LineNumber, ISBN, Quantity, UnitPrice)
                    VALUES (?, ?, ?, ?, ?);
                    """,
                    invoice_number,
                    line_number,
                    item["isbn"],
                    item["quantity"],
                    item["price"],
                )
                total += item["price"] * item["quantity"]

            connection.commit()
            messagebox.showinfo(
                "ثبت موفق فروش",
                f"فاکتور شماره {invoice_number} با موفقیت ثبت شد.\n"
                f"مبلغ کل: {total:,.0f}",
                parent=window,
            )
            clear_form()
        except Exception as error:
            if connection is not None:
                connection.rollback()
            messagebox.showerror(
                "خطای ثبت فروش",
                f"فروش ثبت نشد و تمام تغییرات لغو شد:\n\n{error}",
                parent=window,
            )
        finally:
            if connection is not None:
                connection.close()

    ttk.Button(
        item_frame,
        text="افزودن به فاکتور",
        command=add_item,
        width=18,
    ).grid(row=0, column=4, padx=8, pady=6)

    store_combo.bind("<<ComboboxSelected>>", load_store_dependencies)

    buttons = ttk.Frame(window, padding=(15, 5, 15, 15))
    buttons.pack(fill="x")
    ttk.Button(
        buttons,
        text="ثبت نهایی فروش",
        command=save_sale,
        width=20,
    ).pack(side="right", padx=6, ipady=8)
    ttk.Button(
        buttons,
        text="حذف ردیف انتخاب‌شده",
        command=remove_item,
        width=22,
    ).pack(side="right", padx=6, ipady=8)
    ttk.Button(
        buttons,
        text="پاک‌کردن فرم",
        command=clear_form,
        width=16,
    ).pack(side="right", padx=6, ipady=8)
    ttk.Button(
        buttons,
        text="بستن",
        command=window.destroy,
        width=14,
    ).pack(side="left", padx=6, ipady=8)

    try:
        load_stores_and_customers()
    except Exception as error:
        messagebox.showerror(
            "خطای پایگاه داده",
            f"دریافت اطلاعات اولیه فروش انجام نشد:\n\n{error}",
            parent=window,
        )
