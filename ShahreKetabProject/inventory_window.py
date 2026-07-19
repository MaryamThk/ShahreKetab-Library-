import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

import pyodbc

from database import fetch_all, get_connection
from ui_helpers import clear_tree, make_scrollable_tree


def open_inventory_window(parent):
    window = tk.Toplevel(parent)
    window.title("مدیریت موجودی")
    window.geometry("1200x680")
    window.minsize(1000, 560)

    ttk.Label(
        window,
        text="مدیریت موجودی کتاب‌ها در فروشگاه‌ها",
        font=("Tahoma", 17, "bold"),
    ).pack(pady=(15, 6))

    filter_frame = ttk.LabelFrame(window, text="جستجو", padding=10)
    filter_frame.pack(fill="x", padx=15, pady=(0, 8))
    store_filter_var = tk.StringVar()
    book_filter_var = tk.StringVar()

    ttk.Label(filter_frame, text="کد فروشگاه:").grid(row=0, column=0, padx=6)
    ttk.Entry(
        filter_frame,
        textvariable=store_filter_var,
        width=18,
        justify="right",
    ).grid(row=0, column=1, padx=6)
    ttk.Label(filter_frame, text="عنوان یا شابک:").grid(row=0, column=2, padx=6)
    ttk.Entry(
        filter_frame,
        textvariable=book_filter_var,
        width=28,
        justify="right",
    ).grid(row=0, column=3, padx=6)

    table_frame, tree = make_scrollable_tree(window)
    table_frame.pack(fill="both", expand=True, padx=15, pady=6)

    columns = (
        "کد فروشگاه",
        "شهر",
        "شابک",
        "عنوان کتاب",
        "موجودی فعلی",
        "حداقل موجودی",
        "وضعیت",
        "توضیحات",
    )
    widths = (105, 100, 110, 210, 110, 110, 100, 220)
    tree.configure(columns=columns)
    for name, width in zip(columns, widths):
        tree.heading(name, text=name)
        tree.column(name, width=width, anchor="center")

    status_var = tk.StringVar(value="در حال دریافت اطلاعات...")
    ttk.Label(window, textvariable=status_var).pack(pady=(0, 5))

    def refresh_inventory():
        clear_tree(tree)
        query = """
        SELECT
            i.StoreCode,
            c.CityName,
            i.ISBN,
            b.Title,
            i.AvailableQuantity,
            i.MinimumQuantity,
            CASE
                WHEN i.AvailableQuantity < i.MinimumQuantity THEN N'بحرانی'
                WHEN i.AvailableQuantity = i.MinimumQuantity THEN N'مرزی'
                ELSE N'عادی'
            END,
            ISNULL(i.Description, N'')
        FROM dbo.Inventory AS i
        INNER JOIN dbo.Store AS s ON s.StoreCode = i.StoreCode
        INNER JOIN dbo.City AS c ON c.CityCode = s.CityCode
        INNER JOIN dbo.Book AS b ON b.ISBN = i.ISBN
        WHERE 1 = 1
        """
        parameters = []
        store_filter = store_filter_var.get().strip()
        book_filter = book_filter_var.get().strip()
        if store_filter:
            query += " AND CAST(i.StoreCode AS NVARCHAR(20)) LIKE ?"
            parameters.append(f"%{store_filter}%")
        if book_filter:
            query += " AND (b.Title LIKE ? OR i.ISBN LIKE ?)"
            parameters.extend([f"%{book_filter}%", f"%{book_filter}%"])
        query += " ORDER BY i.StoreCode, b.Title;"

        try:
            _, rows = fetch_all(query, tuple(parameters))
            for row in rows:
                tree.insert("", "end", values=tuple(row))
            status_var.set(f"تعداد رکوردهای موجودی: {len(rows)}")
        except Exception as error:
            status_var.set("خطا در دریافت اطلاعات")
            messagebox.showerror(
                "خطای پایگاه داده",
                f"دریافت موجودی‌ها انجام نشد:\n\n{error}",
                parent=window,
            )

    def store_map():
        _, rows = fetch_all(
            """
            SELECT s.StoreCode, c.CityName, s.Address
            FROM dbo.Store AS s
            INNER JOIN dbo.City AS c ON c.CityCode = s.CityCode
            ORDER BY s.StoreCode;
            """
        )
        return {f"{row[0]} - {row[1]} - {row[2]}": int(row[0]) for row in rows}

    def book_map():
        _, rows = fetch_all("SELECT ISBN, Title FROM dbo.Book ORDER BY Title;")
        return {f"{row[0]} - {row[1]}": str(row[0]) for row in rows}

    def open_form(mode, selected_values=None):
        is_edit = mode == "edit"
        form = tk.Toplevel(window)
        form.title("ویرایش موجودی" if is_edit else "ثبت موجودی جدید")
        form.geometry("650x510")
        form.resizable(False, False)
        form.transient(window)
        form.grab_set()

        body = ttk.Frame(form, padding=30)
        body.pack(fill="both", expand=True)

        store_var = tk.StringVar()
        book_var = tk.StringVar()
        available_var = tk.StringVar()
        minimum_var = tk.StringVar()
        description_var = tk.StringVar()

        try:
            stores = store_map()
            books = book_map()
        except Exception as error:
            messagebox.showerror(
                "خطا",
                f"دریافت اطلاعات اولیه انجام نشد:\n\n{error}",
                parent=form,
            )
            form.destroy()
            return

        ttk.Label(body, text="فروشگاه:").grid(row=0, column=0, padx=10, pady=12, sticky="e")
        store_combo = ttk.Combobox(
            body,
            textvariable=store_var,
            values=list(stores.keys()),
            state="readonly",
            width=45,
            justify="right",
        )
        store_combo.grid(row=0, column=1, padx=10, pady=12)

        ttk.Label(body, text="کتاب:").grid(row=1, column=0, padx=10, pady=12, sticky="e")
        book_combo = ttk.Combobox(
            body,
            textvariable=book_var,
            values=list(books.keys()),
            state="readonly",
            width=45,
            justify="right",
        )
        book_combo.grid(row=1, column=1, padx=10, pady=12)

        fields = [
            ("تعداد موجود:", available_var, 2),
            ("حداقل موجودی:", minimum_var, 3),
            ("توضیحات:", description_var, 4),
        ]
        for label, variable, row_number in fields:
            ttk.Label(body, text=label).grid(
                row=row_number, column=0, padx=10, pady=12, sticky="e"
            )
            ttk.Entry(
                body,
                textvariable=variable,
                width=48,
                justify="right",
            ).grid(row=row_number, column=1, padx=10, pady=12)

        if is_edit and selected_values:
            store_code = int(selected_values[0])
            isbn = str(selected_values[2])
            for display, code in stores.items():
                if code == store_code:
                    store_var.set(display)
                    break
            for display, book_isbn in books.items():
                if book_isbn == isbn:
                    book_var.set(display)
                    break
            available_var.set(selected_values[4])
            minimum_var.set(selected_values[5])
            description_var.set(selected_values[7])
            store_combo.configure(state="disabled")
            book_combo.configure(state="disabled")

        def save_inventory():
            if not store_var.get() or not book_var.get():
                messagebox.showwarning(
                    "اطلاعات ناقص",
                    "فروشگاه و کتاب را انتخاب کنید.",
                    parent=form,
                )
                return
            try:
                available = int(available_var.get().strip())
                minimum = int(minimum_var.get().strip())
                if available < 0 or minimum < 0:
                    raise ValueError
            except ValueError:
                messagebox.showwarning(
                    "مقدار نامعتبر",
                    "تعدادها باید عدد صحیح صفر یا مثبت باشند.",
                    parent=form,
                )
                return

            store_code = stores[store_var.get()]
            isbn = books[book_var.get()]
            description = description_var.get().strip() or None
            connection = None
            try:
                connection = get_connection()
                cursor = connection.cursor()
                if is_edit:
                    cursor.execute(
                        """
                        UPDATE dbo.Inventory
                        SET AvailableQuantity = ?, MinimumQuantity = ?, Description = ?
                        WHERE StoreCode = ? AND ISBN = ?;
                        """,
                        available,
                        minimum,
                        description,
                        store_code,
                        isbn,
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO dbo.Inventory
                            (StoreCode, ISBN, AvailableQuantity, MinimumQuantity, Description)
                        VALUES (?, ?, ?, ?, ?);
                        """,
                        store_code,
                        isbn,
                        available,
                        minimum,
                        description,
                    )
                connection.commit()
                messagebox.showinfo(
                    "عملیات موفق",
                    "اطلاعات موجودی با موفقیت ذخیره شد.",
                    parent=form,
                )
                form.destroy()
                refresh_inventory()
            except pyodbc.IntegrityError as error:
                if connection is not None:
                    connection.rollback()
                messagebox.showerror(
                    "خطای ثبت موجودی",
                    f"برای این کتاب در فروشگاه انتخاب‌شده قبلاً موجودی ثبت شده است.\n\n{error}",
                    parent=form,
                )
            except Exception as error:
                if connection is not None:
                    connection.rollback()
                messagebox.showerror(
                    "خطا",
                    f"ذخیره موجودی انجام نشد:\n\n{error}",
                    parent=form,
                )
            finally:
                if connection is not None:
                    connection.close()

        button_frame = ttk.Frame(body)
        button_frame.grid(row=5, column=0, columnspan=2, pady=(25, 5))
        ttk.Button(
            button_frame,
            text="ثبت تغییرات" if is_edit else "ثبت موجودی",
            command=save_inventory,
            width=18,
        ).pack(side="right", padx=8, ipady=7)
        ttk.Button(
            button_frame,
            text="انصراف",
            command=form.destroy,
            width=14,
        ).pack(side="right", padx=8, ipady=7)

    def selected_values():
        selection = tree.selection()
        if not selection:
            messagebox.showwarning(
                "انتخاب موجودی",
                "ابتدا یک رکورد موجودی را انتخاب کنید.",
                parent=window,
            )
            return None
        return tree.item(selection[0], "values")

    def edit_selected():
        values = selected_values()
        if values:
            open_form("edit", values)

    def change_quantity(direction):
        values = selected_values()
        if not values:
            return
        amount = simpledialog.askinteger(
            "افزایش موجودی" if direction == 1 else "کاهش موجودی",
            f"تعداد موردنظر برای «{values[3]}» را وارد کنید:",
            parent=window,
            minvalue=1,
        )
        if amount is None:
            return

        store_code = int(values[0])
        isbn = str(values[2])
        delta = amount * direction
        connection = None
        try:
            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT AvailableQuantity
                FROM dbo.Inventory WITH (UPDLOCK, ROWLOCK)
                WHERE StoreCode = ? AND ISBN = ?;
                """,
                store_code,
                isbn,
            )
            row = cursor.fetchone()
            if row is None:
                raise ValueError("رکورد موجودی پیدا نشد.")
            new_quantity = int(row[0]) + delta
            if new_quantity < 0:
                connection.rollback()
                messagebox.showwarning(
                    "موجودی ناکافی",
                    f"موجودی فعلی {row[0]} عدد است.",
                    parent=window,
                )
                return
            cursor.execute(
                """
                UPDATE dbo.Inventory
                SET AvailableQuantity = ?
                WHERE StoreCode = ? AND ISBN = ?;
                """,
                new_quantity,
                store_code,
                isbn,
            )
            connection.commit()
            messagebox.showinfo(
                "عملیات موفق",
                f"موجودی جدید: {new_quantity}",
                parent=window,
            )
            refresh_inventory()
        except Exception as error:
            if connection is not None:
                connection.rollback()
            messagebox.showerror(
                "خطا",
                f"تغییر موجودی انجام نشد:\n\n{error}",
                parent=window,
            )
        finally:
            if connection is not None:
                connection.close()

    def clear_filters():
        store_filter_var.set("")
        book_filter_var.set("")
        refresh_inventory()

    ttk.Button(filter_frame, text="جستجو", command=refresh_inventory, width=12).grid(
        row=0, column=4, padx=6
    )
    ttk.Button(
        filter_frame,
        text="پاک‌کردن فیلتر",
        command=clear_filters,
        width=15,
    ).grid(row=0, column=5, padx=6)

    tree.bind("<Double-1>", lambda _event: edit_selected())

    buttons = ttk.Frame(window, padding=(15, 5, 15, 15))
    buttons.pack(fill="x")
    ttk.Button(
        buttons,
        text="ثبت موجودی جدید",
        command=lambda: open_form("add"),
        width=19,
    ).pack(side="right", padx=5, ipady=7)
    ttk.Button(
        buttons,
        text="افزایش موجودی",
        command=lambda: change_quantity(1),
        width=17,
    ).pack(side="right", padx=5, ipady=7)
    ttk.Button(
        buttons,
        text="کاهش موجودی",
        command=lambda: change_quantity(-1),
        width=17,
    ).pack(side="right", padx=5, ipady=7)
    ttk.Button(
        buttons,
        text="ویرایش اطلاعات",
        command=edit_selected,
        width=17,
    ).pack(side="right", padx=5, ipady=7)
    ttk.Button(
        buttons,
        text="تازه‌سازی",
        command=refresh_inventory,
        width=14,
    ).pack(side="right", padx=5, ipady=7)
    ttk.Button(
        buttons,
        text="بستن",
        command=window.destroy,
        width=14,
    ).pack(side="left", padx=5, ipady=7)

    refresh_inventory()
