import tkinter as tk
from decimal import Decimal, InvalidOperation
from tkinter import messagebox, ttk

import pyodbc

from database import fetch_all, get_connection
from ui_helpers import clear_tree, make_scrollable_tree


BOOKS_QUERY = """
SELECT
    b.ISBN,
    b.Title,
    b.Subject,
    STUFF(
        (
            SELECT N'، ' + a.AuthorName
            FROM dbo.BookAuthor AS ba
            INNER JOIN dbo.Author AS a ON a.AuthorID = ba.AuthorID
            WHERE ba.ISBN = b.ISBN
            ORDER BY a.AuthorName
            FOR XML PATH(''), TYPE
        ).value('.', 'NVARCHAR(MAX)'),
        1, 2, N''
    ) AS Authors,
    p.PublisherName,
    b.Price,
    b.PublicationYear
FROM dbo.Book AS b
INNER JOIN dbo.Publisher AS p ON p.PublisherID = b.PublisherID
ORDER BY b.Title;
"""


def open_books_window(parent):
    window = tk.Toplevel(parent)
    window.title("مدیریت کتاب‌ها")
    window.geometry("1150x650")
    window.minsize(950, 540)

    ttk.Label(
        window,
        text="مدیریت کتاب‌های شهر کتاب",
        font=("Tahoma", 17, "bold"),
    ).pack(pady=(15, 6))

    table_frame, tree = make_scrollable_tree(window)
    table_frame.pack(fill="both", expand=True, padx=15, pady=8)

    columns = (
        "شابک",
        "عنوان کتاب",
        "موضوع",
        "نویسندگان",
        "ناشر",
        "قیمت",
        "سال چاپ",
    )
    tree.configure(columns=columns)
    widths = (110, 210, 120, 220, 130, 120, 90)
    for column_name, width in zip(columns, widths):
        tree.heading(column_name, text=column_name)
        tree.column(column_name, width=width, anchor="center")

    status_var = tk.StringVar(value="در حال دریافت اطلاعات...")
    ttk.Label(window, textvariable=status_var).pack(pady=(0, 5))

    def refresh_books():
        clear_tree(tree)
        try:
            _, rows = fetch_all(BOOKS_QUERY)
            for row in rows:
                tree.insert(
                    "",
                    "end",
                    values=(
                        row[0],
                        row[1],
                        row[2],
                        row[3] or "",
                        row[4],
                        f"{row[5]:,.0f}",
                        row[6] or "",
                    ),
                )
            status_var.set(f"تعداد کتاب‌ها: {len(rows)}")
        except Exception as error:
            status_var.set("خطا در دریافت اطلاعات")
            messagebox.showerror(
                "خطای پایگاه داده",
                f"دریافت اطلاعات کتاب‌ها انجام نشد:\n\n{error}",
                parent=window,
            )

    def publisher_names():
        _, rows = fetch_all(
            "SELECT PublisherName FROM dbo.Publisher ORDER BY PublisherName;"
        )
        return [row[0] for row in rows]

    def parse_authors(text):
        result = []
        for name in text.replace("،", ",").split(","):
            name = name.strip()
            if name and name not in result:
                result.append(name)
        return result

    def save_authors(cursor, isbn, authors):
        for author_name in authors:
            cursor.execute(
                "SELECT AuthorID FROM dbo.Author WHERE AuthorName = ?;",
                author_name,
            )
            row = cursor.fetchone()
            if row is None:
                cursor.execute(
                    "INSERT INTO dbo.Author (AuthorName) VALUES (?);",
                    author_name,
                )
                cursor.execute(
                    "SELECT AuthorID FROM dbo.Author WHERE AuthorName = ?;",
                    author_name,
                )
                row = cursor.fetchone()
            cursor.execute(
                "INSERT INTO dbo.BookAuthor (ISBN, AuthorID) VALUES (?, ?);",
                isbn,
                row[0],
            )

    def open_form(mode, selected_values=None):
        is_edit = mode == "edit"
        form = tk.Toplevel(window)
        form.title("ویرایش کتاب" if is_edit else "افزودن کتاب جدید")
        form.geometry("620x560")
        form.resizable(False, False)
        form.transient(window)
        form.grab_set()

        body = ttk.Frame(form, padding=30)
        body.pack(fill="both", expand=True)

        variables = {
            "isbn": tk.StringVar(),
            "title": tk.StringVar(),
            "subject": tk.StringVar(),
            "authors": tk.StringVar(),
            "publisher": tk.StringVar(),
            "price": tk.StringVar(),
            "year": tk.StringVar(),
        }

        if is_edit and selected_values:
            variables["isbn"].set(selected_values[0])
            variables["title"].set(selected_values[1])
            variables["subject"].set(selected_values[2])
            variables["authors"].set(selected_values[3])
            variables["publisher"].set(selected_values[4])
            variables["price"].set(str(selected_values[5]).replace(",", ""))
            variables["year"].set(selected_values[6])

        fields = [
            ("شابک:", "isbn"),
            ("عنوان کتاب:", "title"),
            ("موضوع:", "subject"),
            ("نویسندگان:", "authors"),
            ("قیمت:", "price"),
            ("سال چاپ:", "year"),
        ]

        entries = {}
        for row_number, (label, key) in enumerate(fields):
            ttk.Label(body, text=label).grid(
                row=row_number, column=0, padx=10, pady=10, sticky="e"
            )
            entry = ttk.Entry(
                body,
                textvariable=variables[key],
                width=42,
                justify="right",
            )
            entry.grid(row=row_number, column=1, padx=10, pady=10, sticky="ew")
            entries[key] = entry

        ttk.Label(
            body,
            text="برای چند نویسنده، نام‌ها را با ویرگول جدا کنید.",
            font=("Tahoma", 8),
        ).grid(row=3, column=2, padx=4, sticky="w")

        ttk.Label(body, text="ناشر:").grid(
            row=6, column=0, padx=10, pady=10, sticky="e"
        )
        try:
            publishers = publisher_names()
        except Exception as error:
            messagebox.showerror(
                "خطا",
                f"دریافت ناشران انجام نشد:\n\n{error}",
                parent=form,
            )
            form.destroy()
            return

        publisher_combo = ttk.Combobox(
            body,
            textvariable=variables["publisher"],
            values=publishers,
            state="readonly",
            width=39,
            justify="right",
        )
        publisher_combo.grid(row=6, column=1, padx=10, pady=10, sticky="ew")

        if is_edit:
            entries["isbn"].configure(state="disabled")

        def save_book():
            isbn = variables["isbn"].get().strip()
            title = variables["title"].get().strip()
            subject = variables["subject"].get().strip()
            authors = parse_authors(variables["authors"].get())
            publisher = variables["publisher"].get().strip()
            price_text = variables["price"].get().replace(",", "").strip()
            year_text = variables["year"].get().strip()

            if not all((isbn, title, subject, authors, publisher, price_text)):
                messagebox.showwarning(
                    "اطلاعات ناقص",
                    "شابک، عنوان، موضوع، نویسنده، ناشر و قیمت الزامی هستند.",
                    parent=form,
                )
                return

            try:
                price = Decimal(price_text)
                if price < 0:
                    raise InvalidOperation
            except (InvalidOperation, ValueError):
                messagebox.showwarning(
                    "قیمت نامعتبر",
                    "قیمت باید عدد صفر یا مثبت باشد.",
                    parent=form,
                )
                return

            publication_year = None
            if year_text:
                try:
                    publication_year = int(year_text)
                    if publication_year < 1000 or publication_year > 9999:
                        raise ValueError
                except ValueError:
                    messagebox.showwarning(
                        "سال نامعتبر",
                        "سال چاپ باید یک عدد چهاررقمی باشد.",
                        parent=form,
                    )
                    return

            connection = None
            try:
                connection = get_connection()
                cursor = connection.cursor()
                cursor.execute(
                    "SELECT PublisherID FROM dbo.Publisher WHERE PublisherName = ?;",
                    publisher,
                )
                publisher_row = cursor.fetchone()
                if publisher_row is None:
                    raise ValueError("ناشر انتخاب‌شده پیدا نشد.")

                if is_edit:
                    cursor.execute(
                        """
                        UPDATE dbo.Book
                        SET Title = ?, Subject = ?, Price = ?,
                            PublisherID = ?, PublicationYear = ?
                        WHERE ISBN = ?;
                        """,
                        title,
                        subject,
                        price,
                        publisher_row[0],
                        publication_year,
                        isbn,
                    )
                    cursor.execute(
                        "DELETE FROM dbo.BookAuthor WHERE ISBN = ?;",
                        isbn,
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO dbo.Book
                            (ISBN, Title, Subject, Price, PublisherID, PublicationYear)
                        VALUES (?, ?, ?, ?, ?, ?);
                        """,
                        isbn,
                        title,
                        subject,
                        price,
                        publisher_row[0],
                        publication_year,
                    )

                save_authors(cursor, isbn, authors)
                connection.commit()
                messagebox.showinfo(
                    "عملیات موفق",
                    "اطلاعات کتاب با موفقیت ذخیره شد.",
                    parent=form,
                )
                form.destroy()
                refresh_books()
            except pyodbc.IntegrityError as error:
                if connection is not None:
                    connection.rollback()
                messagebox.showerror(
                    "خطای ثبت اطلاعات",
                    f"شابک تکراری است یا اطلاعات با محدودیت‌های دیتابیس سازگار نیست.\n\n{error}",
                    parent=form,
                )
            except Exception as error:
                if connection is not None:
                    connection.rollback()
                messagebox.showerror(
                    "خطای پایگاه داده",
                    f"ذخیره اطلاعات انجام نشد:\n\n{error}",
                    parent=form,
                )
            finally:
                if connection is not None:
                    connection.close()

        buttons = ttk.Frame(body)
        buttons.grid(row=7, column=0, columnspan=3, pady=(25, 5))
        ttk.Button(
            buttons,
            text="ثبت تغییرات" if is_edit else "ثبت کتاب",
            command=save_book,
            width=18,
        ).pack(side="right", padx=8, ipady=7)
        ttk.Button(
            buttons,
            text="انصراف",
            command=form.destroy,
            width=14,
        ).pack(side="right", padx=8, ipady=7)

    def edit_selected():
        selection = tree.selection()
        if not selection:
            messagebox.showwarning(
                "انتخاب کتاب",
                "ابتدا یک کتاب را انتخاب کنید.",
                parent=window,
            )
            return
        open_form("edit", tree.item(selection[0], "values"))

    tree.bind("<Double-1>", lambda _event: edit_selected())

    buttons = ttk.Frame(window, padding=(15, 5, 15, 15))
    buttons.pack(fill="x")
    ttk.Button(
        buttons,
        text="افزودن کتاب جدید",
        command=lambda: open_form("add"),
        width=20,
    ).pack(side="right", padx=6, ipady=7)
    ttk.Button(
        buttons,
        text="ویرایش کتاب انتخاب‌شده",
        command=edit_selected,
        width=24,
    ).pack(side="right", padx=6, ipady=7)
    ttk.Button(
        buttons,
        text="تازه‌سازی",
        command=refresh_books,
        width=15,
    ).pack(side="right", padx=6, ipady=7)
    ttk.Button(
        buttons,
        text="بستن",
        command=window.destroy,
        width=15,
    ).pack(side="left", padx=6, ipady=7)

    refresh_books()
