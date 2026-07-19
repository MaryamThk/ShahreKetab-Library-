from datetime import datetime
from decimal import Decimal
import tkinter as tk
from tkinter import messagebox, ttk

from database import fetch_all
from ui_helpers import export_tree_to_csv, make_scrollable_tree, rebuild_tree


def open_reports_window(parent):
    window = tk.Toplevel(parent)
    window.title("جستجو و گزارش‌گیری")
    window.geometry("1250x760")
    window.minsize(1050, 650)

    ttk.Label(
        window,
        text="جستجو و گزارش‌گیری پارامتریک",
        font=("Tahoma", 17, "bold"),
    ).pack(pady=(14, 6))

    selector_frame = ttk.LabelFrame(window, text="انتخاب گزارش", padding=10)
    selector_frame.pack(fill="x", padx=15, pady=6)

    report_var = tk.StringVar()
    report_combo = ttk.Combobox(
        selector_frame,
        textvariable=report_var,
        state="readonly",
        width=75,
        justify="right",
    )
    report_combo.pack(side="right", padx=8)

    parameter_frame = ttk.LabelFrame(window, text="پارامترهای گزارش", padding=10)
    parameter_frame.pack(fill="x", padx=15, pady=6)

    table_frame, tree = make_scrollable_tree(window)
    table_frame.pack(fill="both", expand=True, padx=15, pady=8)

    status_var = tk.StringVar(value="یک گزارش انتخاب کنید.")
    ttk.Label(window, textvariable=status_var).pack(pady=4)

    lookup = {}
    parameter_vars = {}

    def load_lookup_data():
        lookup["cities"] = [
            row[0]
            for row in fetch_all(
                "SELECT DISTINCT CityName FROM dbo.City ORDER BY CityName;"
            )[1]
        ]
        lookup["authors"] = [
            row[0]
            for row in fetch_all(
                "SELECT AuthorName FROM dbo.Author ORDER BY AuthorName;"
            )[1]
        ]
        lookup["stores"] = [
            f"{row[0]} - {row[1]}"
            for row in fetch_all(
                """
                SELECT s.StoreCode, c.CityName
                FROM dbo.Store AS s
                INNER JOIN dbo.City AS c ON c.CityCode = s.CityCode
                ORDER BY s.StoreCode;
                """
            )[1]
        ]
        lookup["employees"] = [
            f"{row[0]} - {row[1]} - فروشگاه {row[2]}"
            for row in fetch_all(
                """
                SELECT NationalCode, FullName, StoreCode
                FROM dbo.Employee
                ORDER BY FullName;
                """
            )[1]
        ]
        lookup["customers"] = [
            f"{row[0]} - {row[1]}"
            for row in fetch_all(
                "SELECT CustomerCode, FullName FROM dbo.Customer ORDER BY FullName;"
            )[1]
        ]
        lookup["books"] = [
            f"{row[0]} - {row[1]}"
            for row in fetch_all(
                "SELECT ISBN, Title FROM dbo.Book ORDER BY Title;"
            )[1]
        ]
        lookup["publishers"] = [
            row[0]
            for row in fetch_all(
                "SELECT PublisherName FROM dbo.Publisher ORDER BY PublisherName;"
            )[1]
        ]

    reports = {
        "۱. مشخصات فروشگاه‌های یک شهر": {
            "fields": [("city", "نام شهر:", "combo", "cities")],
        },
        "۲. فروشگاه‌هایی که کتاب نویسنده مشخص را ندارند": {
            "fields": [("author", "نام نویسنده:", "combo", "authors")],
        },
        "۳. جمع فروش یک فروشگاه در بازه زمانی": {
            "fields": [
                ("store", "فروشگاه:", "combo", "stores"),
                ("start", "تاریخ شروع:", "entry", None),
                ("end", "تاریخ پایان:", "entry", None),
            ],
        },
        "۴. کارمندان یک فروشگاه": {
            "fields": [("store", "فروشگاه:", "combo", "stores")],
        },
        "۵. فروش‌های انجام‌شده توسط یک کارمند": {
            "fields": [("employee", "کارمند:", "combo", "employees")],
        },
        "۶. کتاب‌های مربوط به نویسنده یا موضوع": {
            "fields": [
                ("mode", "نوع جستجو:", "combo_values", ["نویسنده", "موضوع"]),
                ("text", "عبارت جستجو:", "entry", None),
            ],
        },
        "۷. مشتریان با بدهی بیشتر از مقدار مشخص": {
            "fields": [("amount", "حداقل بدهی:", "entry", None)],
        },
        "۸. تمام خریدهای یک مشتری": {
            "fields": [("customer", "مشتری:", "combo", "customers")],
        },
        "۹. کتاب‌های فروخته‌نشده در بازه زمانی": {
            "fields": [
                ("start", "تاریخ شروع:", "entry", None),
                ("end", "تاریخ پایان:", "entry", None),
            ],
        },
        "۱۰. فروشگاه‌های دارای موجودی کمتر از حد مجاز برای یک کتاب": {
            "fields": [("book", "کتاب:", "combo", "books")],
        },
        "۱۱. بدهی شهر کتاب به یک ناشر": {
            "fields": [("publisher", "ناشر:", "combo", "publishers")],
        },
    }

    report_combo.configure(values=list(reports.keys()))

    def parse_store(display):
        return int(display.split(" - ", 1)[0])

    def parse_employee(display):
        return display.split(" - ", 1)[0]

    def parse_customer(display):
        return int(display.split(" - ", 1)[0])

    def parse_book(display):
        return display.split(" - ", 1)[0]

    def valid_date(text):
        return datetime.strptime(text.strip(), "%Y-%m-%d").date()

    def render_parameters(_event=None):
        for widget in parameter_frame.winfo_children():
            widget.destroy()
        parameter_vars.clear()

        selected_report = report_var.get()
        if not selected_report:
            return

        fields = reports[selected_report]["fields"]
        for column, (key, label, widget_type, source) in enumerate(fields):
            ttk.Label(parameter_frame, text=label).grid(
                row=0, column=column * 2, padx=6, pady=6, sticky="e"
            )
            variable = tk.StringVar()
            parameter_vars[key] = variable

            if key == "start":
                variable.set("2009-01-01")
            elif key == "end":
                variable.set(datetime.now().strftime("%Y-%m-%d"))
            elif key == "amount":
                variable.set("10000")

            if widget_type == "entry":
                widget = ttk.Entry(
                    parameter_frame,
                    textvariable=variable,
                    width=24,
                    justify="right",
                )
            elif widget_type == "combo_values":
                widget = ttk.Combobox(
                    parameter_frame,
                    textvariable=variable,
                    values=source,
                    state="readonly",
                    width=22,
                    justify="right",
                )
                if source:
                    variable.set(source[0])
            else:
                values = lookup[source]
                widget = ttk.Combobox(
                    parameter_frame,
                    textvariable=variable,
                    values=values,
                    state="readonly",
                    width=30,
                    justify="right",
                )
                if values:
                    variable.set(values[0])

            widget.grid(row=0, column=column * 2 + 1, padx=6, pady=6)

        ttk.Button(
            parameter_frame,
            text="اجرای گزارش",
            command=run_report,
            width=16,
        ).grid(row=0, column=len(fields) * 2, padx=10, pady=6)

    def run_report():
        selected_report = report_var.get()
        if not selected_report:
            messagebox.showwarning(
                "انتخاب گزارش",
                "ابتدا یک گزارش را انتخاب کنید.",
                parent=window,
            )
            return

        try:
            if selected_report.startswith("۱."):
                city = parameter_vars["city"].get()
                query = """
                SELECT
                    s.StoreCode AS N'کد فروشگاه',
                    c.CityName AS N'شهر',
                    c.ProvinceName AS N'استان',
                    s.Phone AS N'تلفن',
                    s.Address AS N'آدرس'
                FROM dbo.Store AS s
                INNER JOIN dbo.City AS c ON c.CityCode = s.CityCode
                WHERE c.CityName = ?
                ORDER BY s.StoreCode;
                """
                parameters = (city,)

            elif selected_report.startswith("۲."):
                author = parameter_vars["author"].get()
                query = """
                SELECT
                    s.StoreCode AS N'کد فروشگاه',
                    c.CityName AS N'شهر',
                    s.Phone AS N'تلفن',
                    s.Address AS N'آدرس'
                FROM dbo.Store AS s
                INNER JOIN dbo.City AS c ON c.CityCode = s.CityCode
                WHERE NOT EXISTS
                (
                    SELECT 1
                    FROM dbo.Inventory AS i
                    INNER JOIN dbo.BookAuthor AS ba ON ba.ISBN = i.ISBN
                    INNER JOIN dbo.Author AS a ON a.AuthorID = ba.AuthorID
                    WHERE i.StoreCode = s.StoreCode
                      AND i.AvailableQuantity > 0
                      AND a.AuthorName = ?
                )
                ORDER BY s.StoreCode;
                """
                parameters = (author,)

            elif selected_report.startswith("۳."):
                store_code = parse_store(parameter_vars["store"].get())
                start_date = valid_date(parameter_vars["start"].get())
                end_date = valid_date(parameter_vars["end"].get())
                if start_date > end_date:
                    raise ValueError("تاریخ شروع نباید بعد از تاریخ پایان باشد.")
                query = """
                SELECT
                    ? AS N'کد فروشگاه',
                    COUNT(DISTINCT s.InvoiceNumber) AS N'تعداد فاکتور',
                    ISNULL(SUM(si.Quantity), 0) AS N'تعداد کتاب فروخته‌شده',
                    ISNULL(SUM(si.Quantity * si.UnitPrice), 0) AS N'مبلغ کل فروش'
                FROM dbo.Sale AS s
                INNER JOIN dbo.SaleItem AS si ON si.InvoiceNumber = s.InvoiceNumber
                WHERE s.StoreCode = ?
                  AND s.InvoiceDate BETWEEN ? AND ?;
                """
                parameters = (store_code, store_code, start_date, end_date)

            elif selected_report.startswith("۴."):
                store_code = parse_store(parameter_vars["store"].get())
                query = """
                SELECT
                    NationalCode AS N'کد ملی',
                    FullName AS N'نام کارمند',
                    Phone AS N'تلفن',
                    Address AS N'آدرس',
                    Gender AS N'جنسیت',
                    StoreCode AS N'کد فروشگاه'
                FROM dbo.Employee
                WHERE StoreCode = ?
                ORDER BY FullName;
                """
                parameters = (store_code,)

            elif selected_report.startswith("۵."):
                employee_code = parse_employee(parameter_vars["employee"].get())
                query = """
                SELECT
                    s.InvoiceNumber AS N'شماره فاکتور',
                    s.InvoiceDate AS N'تاریخ',
                    e.FullName AS N'نام کارمند',
                    c.FullName AS N'نام مشتری',
                    s.StoreCode AS N'فروشگاه',
                    b.Title AS N'عنوان کتاب',
                    si.Quantity AS N'تعداد',
                    si.UnitPrice AS N'قیمت واحد',
                    si.Quantity * si.UnitPrice AS N'مبلغ ردیف'
                FROM dbo.Sale AS s
                INNER JOIN dbo.Employee AS e
                    ON e.NationalCode = s.EmployeeNationalCode
                INNER JOIN dbo.Customer AS c ON c.CustomerCode = s.CustomerCode
                INNER JOIN dbo.SaleItem AS si ON si.InvoiceNumber = s.InvoiceNumber
                INNER JOIN dbo.Book AS b ON b.ISBN = si.ISBN
                WHERE s.EmployeeNationalCode = ?
                ORDER BY s.InvoiceDate DESC, s.InvoiceNumber;
                """
                parameters = (employee_code,)

            elif selected_report.startswith("۶."):
                mode = parameter_vars["mode"].get()
                text = parameter_vars["text"].get().strip()
                if not text:
                    raise ValueError("عبارت جستجو را وارد کنید.")
                if mode == "نویسنده":
                    query = """
                    SELECT DISTINCT
                        b.ISBN AS N'شابک',
                        b.Title AS N'عنوان کتاب',
                        b.Subject AS N'موضوع',
                        a.AuthorName AS N'نویسنده',
                        p.PublisherName AS N'ناشر',
                        b.Price AS N'قیمت'
                    FROM dbo.Book AS b
                    INNER JOIN dbo.BookAuthor AS ba ON ba.ISBN = b.ISBN
                    INNER JOIN dbo.Author AS a ON a.AuthorID = ba.AuthorID
                    INNER JOIN dbo.Publisher AS p ON p.PublisherID = b.PublisherID
                    WHERE a.AuthorName LIKE ?
                    ORDER BY b.Title;
                    """
                else:
                    query = """
                    SELECT
                        b.ISBN AS N'شابک',
                        b.Title AS N'عنوان کتاب',
                        b.Subject AS N'موضوع',
                        p.PublisherName AS N'ناشر',
                        b.Price AS N'قیمت'
                    FROM dbo.Book AS b
                    INNER JOIN dbo.Publisher AS p ON p.PublisherID = b.PublisherID
                    WHERE b.Subject LIKE ?
                    ORDER BY b.Title;
                    """
                parameters = (f"%{text}%",)

            elif selected_report.startswith("۷."):
                try:
                    amount = Decimal(
                        parameter_vars["amount"].get().replace(",", "").strip()
                    )
                    if amount < 0:
                        raise ValueError
                except Exception as exc:
                    raise ValueError("مبلغ بدهی نامعتبر است.") from exc
                query = """
                SELECT
                    CustomerCode AS N'کد مشتری',
                    FullName AS N'نام مشتری',
                    Phone AS N'تلفن',
                    Address AS N'آدرس',
                    DebtAmount AS N'مبلغ بدهی'
                FROM dbo.Customer
                WHERE DebtAmount > ?
                ORDER BY DebtAmount DESC;
                """
                parameters = (amount,)

            elif selected_report.startswith("۸."):
                customer_code = parse_customer(parameter_vars["customer"].get())
                query = """
                SELECT
                    c.CustomerCode AS N'کد مشتری',
                    c.FullName AS N'نام مشتری',
                    s.InvoiceNumber AS N'شماره فاکتور',
                    s.InvoiceDate AS N'تاریخ خرید',
                    st.StoreCode AS N'کد فروشگاه',
                    st.Address AS N'آدرس فروشگاه',
                    b.ISBN AS N'شابک',
                    b.Title AS N'عنوان کتاب',
                    si.Quantity AS N'تعداد',
                    si.UnitPrice AS N'قیمت واحد',
                    si.Quantity * si.UnitPrice AS N'مبلغ ردیف'
                FROM dbo.Customer AS c
                INNER JOIN dbo.Sale AS s ON s.CustomerCode = c.CustomerCode
                INNER JOIN dbo.Store AS st ON st.StoreCode = s.StoreCode
                INNER JOIN dbo.SaleItem AS si ON si.InvoiceNumber = s.InvoiceNumber
                INNER JOIN dbo.Book AS b ON b.ISBN = si.ISBN
                WHERE c.CustomerCode = ?
                ORDER BY s.InvoiceDate DESC, s.InvoiceNumber;
                """
                parameters = (customer_code,)

            elif selected_report.startswith("۹."):
                start_date = valid_date(parameter_vars["start"].get())
                end_date = valid_date(parameter_vars["end"].get())
                if start_date > end_date:
                    raise ValueError("تاریخ شروع نباید بعد از تاریخ پایان باشد.")
                query = """
                SELECT
                    b.ISBN AS N'شابک',
                    b.Title AS N'عنوان کتاب',
                    b.Subject AS N'موضوع',
                    p.PublisherName AS N'ناشر',
                    b.Price AS N'قیمت'
                FROM dbo.Book AS b
                INNER JOIN dbo.Publisher AS p ON p.PublisherID = b.PublisherID
                WHERE NOT EXISTS
                (
                    SELECT 1
                    FROM dbo.SaleItem AS si
                    INNER JOIN dbo.Sale AS s ON s.InvoiceNumber = si.InvoiceNumber
                    WHERE si.ISBN = b.ISBN
                      AND s.InvoiceDate BETWEEN ? AND ?
                )
                ORDER BY b.Title;
                """
                parameters = (start_date, end_date)

            elif selected_report.startswith("۱۰."):
                isbn = parse_book(parameter_vars["book"].get())
                query = """
                SELECT
                    st.StoreCode AS N'کد فروشگاه',
                    c.CityName AS N'شهر',
                    st.Address AS N'آدرس فروشگاه',
                    b.Title AS N'عنوان کتاب',
                    i.AvailableQuantity AS N'موجودی فعلی',
                    i.MinimumQuantity AS N'حداقل موجودی',
                    i.MinimumQuantity - i.AvailableQuantity AS N'مقدار کسری'
                FROM dbo.Inventory AS i
                INNER JOIN dbo.Store AS st ON st.StoreCode = i.StoreCode
                INNER JOIN dbo.City AS c ON c.CityCode = st.CityCode
                INNER JOIN dbo.Book AS b ON b.ISBN = i.ISBN
                WHERE i.ISBN = ?
                  AND i.AvailableQuantity < i.MinimumQuantity
                ORDER BY i.MinimumQuantity - i.AvailableQuantity DESC;
                """
                parameters = (isbn,)

            else:
                publisher = parameter_vars["publisher"].get()
                query = """
                SELECT
                    p.PublisherName AS N'نام ناشر',
                    SUM(pp.TotalAmount) AS N'جمع خرید',
                    SUM(pp.PaidAmount) AS N'جمع پرداخت‌شده',
                    SUM(pp.TotalAmount - pp.PaidAmount) AS N'مبلغ بدهی'
                FROM dbo.PublisherPurchase AS pp
                INNER JOIN dbo.Publisher AS p ON p.PublisherID = pp.PublisherID
                WHERE p.PublisherName = ?
                GROUP BY p.PublisherName;
                """
                parameters = (publisher,)

            columns, rows = fetch_all(query, parameters)
            rebuild_tree(tree, columns, rows)
            status_var.set(f"تعداد ردیف‌های نتیجه: {len(rows)}")

        except ValueError as error:
            messagebox.showwarning(
                "پارامتر نامعتبر",
                str(error),
                parent=window,
            )
        except Exception as error:
            messagebox.showerror(
                "خطای اجرای گزارش",
                f"گزارش اجرا نشد:\n\n{error}",
                parent=window,
            )

    report_combo.bind("<<ComboboxSelected>>", render_parameters)

    buttons = ttk.Frame(window, padding=(15, 5, 15, 15))
    buttons.pack(fill="x")
    ttk.Button(
        buttons,
        text="ذخیره خروجی CSV",
        command=lambda: export_tree_to_csv(tree, window),
        width=20,
    ).pack(side="right", padx=6, ipady=7)
    ttk.Button(
        buttons,
        text="بستن",
        command=window.destroy,
        width=14,
    ).pack(side="left", padx=6, ipady=7)

    try:
        load_lookup_data()
        first_report = next(iter(reports))
        report_var.set(first_report)
        render_parameters()
    except Exception as error:
        messagebox.showerror(
            "خطای پایگاه داده",
            f"دریافت اطلاعات اولیه گزارش‌ها انجام نشد:\n\n{error}",
            parent=window,
        )
