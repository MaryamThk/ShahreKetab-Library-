import tkinter as tk
from tkinter import messagebox, ttk

import pyodbc

from database import fetch_all, get_connection
from ui_helpers import clear_tree, make_scrollable_tree


STORES_QUERY = """
SELECT
    s.StoreCode,
    c.CityName,
    c.ProvinceName,
    s.Phone,
    s.Address,
    s.ManagerNationalCode,
    e.FullName AS ManagerName
FROM dbo.Store AS s
INNER JOIN dbo.City AS c ON c.CityCode = s.CityCode
LEFT JOIN dbo.Employee AS e
    ON e.NationalCode = s.ManagerNationalCode
   AND e.StoreCode = s.StoreCode
ORDER BY s.StoreCode;
"""


def open_stores_window(parent):
    window = tk.Toplevel(parent)
    window.title("مدیریت فروشگاه‌ها")
    window.geometry("1080x630")
    window.minsize(900, 520)

    ttk.Label(
        window,
        text="مدیریت فروشگاه‌های شهر کتاب",
        font=("Tahoma", 17, "bold"),
    ).pack(pady=(15, 6))

    table_frame, tree = make_scrollable_tree(window)
    table_frame.pack(fill="both", expand=True, padx=15, pady=8)

    columns = (
        "کد فروشگاه",
        "شهر",
        "استان",
        "تلفن",
        "آدرس",
        "کد ملی مدیر",
        "نام مدیر",
    )
    widths = (105, 100, 130, 135, 230, 130, 130)
    tree.configure(columns=columns)
    for name, width in zip(columns, widths):
        tree.heading(name, text=name)
        tree.column(name, width=width, anchor="center")

    status_var = tk.StringVar(value="در حال دریافت اطلاعات...")
    ttk.Label(window, textvariable=status_var).pack(pady=(0, 5))

    def refresh_stores():
        clear_tree(tree)
        try:
            _, rows = fetch_all(STORES_QUERY)
            for row in rows:
                tree.insert(
                    "",
                    "end",
                    values=(
                        row[0],
                        row[1],
                        row[2],
                        row[3],
                        row[4],
                        row[5] or "",
                        row[6] or "تعیین نشده",
                    ),
                )
            status_var.set(f"تعداد فروشگاه‌ها: {len(rows)}")
        except Exception as error:
            status_var.set("خطا در دریافت اطلاعات")
            messagebox.showerror(
                "خطای پایگاه داده",
                f"دریافت فروشگاه‌ها انجام نشد:\n\n{error}",
                parent=window,
            )

    def get_city_map():
        _, rows = fetch_all(
            """
            SELECT CityCode, CityName, ProvinceName
            FROM dbo.City
            ORDER BY CityName;
            """
        )
        return {
            f"{row[1]} - {row[2]} ({row[0]})": int(row[0])
            for row in rows
        }

    def get_employee_map(store_code):
        _, rows = fetch_all(
            """
            SELECT NationalCode, FullName
            FROM dbo.Employee
            WHERE StoreCode = ?
            ORDER BY FullName;
            """,
            (store_code,),
        )
        result = {"بدون مدیر": None}
        for row in rows:
            result[f"{row[1]} - {row[0]}"] = row[0]
        return result

    def open_form(mode, selected_values=None):
        is_edit = mode == "edit"
        form = tk.Toplevel(window)
        form.title("ویرایش فروشگاه" if is_edit else "افزودن فروشگاه جدید")
        form.geometry("620x510")
        form.resizable(False, False)
        form.transient(window)
        form.grab_set()

        body = ttk.Frame(form, padding=30)
        body.pack(fill="both", expand=True)

        store_code_var = tk.StringVar()
        city_var = tk.StringVar()
        phone_var = tk.StringVar()
        address_var = tk.StringVar()
        manager_var = tk.StringVar(value="بدون مدیر")

        try:
            city_map = get_city_map()
        except Exception as error:
            messagebox.showerror(
                "خطا",
                f"دریافت شهرها انجام نشد:\n\n{error}",
                parent=form,
            )
            form.destroy()
            return

        labels = [
            ("کد فروشگاه:", store_code_var),
            ("تلفن:", phone_var),
            ("آدرس:", address_var),
        ]
        row_positions = [0, 2, 3]
        entries = []
        for row_number, (label, variable) in zip(row_positions, labels):
            ttk.Label(body, text=label).grid(
                row=row_number, column=0, padx=10, pady=12, sticky="e"
            )
            entry = ttk.Entry(body, textvariable=variable, width=40, justify="right")
            entry.grid(row=row_number, column=1, padx=10, pady=12)
            entries.append(entry)

        ttk.Label(body, text="شهر:").grid(
            row=1, column=0, padx=10, pady=12, sticky="e"
        )
        city_combo = ttk.Combobox(
            body,
            textvariable=city_var,
            values=list(city_map.keys()),
            state="readonly",
            width=37,
            justify="right",
        )
        city_combo.grid(row=1, column=1, padx=10, pady=12)

        ttk.Label(body, text="مدیر فروشگاه:").grid(
            row=4, column=0, padx=10, pady=12, sticky="e"
        )
        manager_combo = ttk.Combobox(
            body,
            textvariable=manager_var,
            state="readonly",
            width=37,
            justify="right",
        )
        manager_combo.grid(row=4, column=1, padx=10, pady=12)

        employee_map = {"بدون مدیر": None}
        if is_edit and selected_values:
            store_code = int(selected_values[0])
            store_code_var.set(str(store_code))
            phone_var.set(selected_values[3])
            address_var.set(selected_values[4])
            for display, code in city_map.items():
                if selected_values[1] in display and selected_values[2] in display:
                    city_var.set(display)
                    break
            employee_map = get_employee_map(store_code)
            manager_combo.configure(values=list(employee_map.keys()))
            for display, national_code in employee_map.items():
                if str(national_code or "") == str(selected_values[5] or ""):
                    manager_var.set(display)
                    break
            entries[0].configure(state="disabled")
        else:
            manager_combo.configure(values=["بدون مدیر"], state="disabled")

        def save_store():
            try:
                store_code = int(store_code_var.get().strip())
                if store_code <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showwarning(
                    "کد نامعتبر",
                    "کد فروشگاه باید یک عدد مثبت باشد.",
                    parent=form,
                )
                return

            selected_city = city_var.get().strip()
            phone = phone_var.get().strip()
            address = address_var.get().strip()
            if not selected_city or not phone or not address:
                messagebox.showwarning(
                    "اطلاعات ناقص",
                    "شهر، تلفن و آدرس را کامل وارد کنید.",
                    parent=form,
                )
                return

            manager_code = employee_map.get(manager_var.get()) if is_edit else None
            connection = None
            try:
                connection = get_connection()
                cursor = connection.cursor()
                if is_edit:
                    cursor.execute(
                        """
                        UPDATE dbo.Store
                        SET CityCode = ?, ManagerNationalCode = ?, Phone = ?, Address = ?
                        WHERE StoreCode = ?;
                        """,
                        city_map[selected_city],
                        manager_code,
                        phone,
                        address,
                        store_code,
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO dbo.Store
                            (StoreCode, CityCode, ManagerNationalCode, Phone, Address)
                        VALUES (?, ?, NULL, ?, ?);
                        """,
                        store_code,
                        city_map[selected_city],
                        phone,
                        address,
                    )
                connection.commit()
                messagebox.showinfo(
                    "عملیات موفق",
                    "اطلاعات فروشگاه با موفقیت ذخیره شد.",
                    parent=form,
                )
                form.destroy()
                refresh_stores()
            except pyodbc.IntegrityError as error:
                if connection is not None:
                    connection.rollback()
                messagebox.showerror(
                    "خطای ثبت اطلاعات",
                    f"کد فروشگاه تکراری است یا مدیر متعلق به این فروشگاه نیست.\n\n{error}",
                    parent=form,
                )
            except Exception as error:
                if connection is not None:
                    connection.rollback()
                messagebox.showerror(
                    "خطای پایگاه داده",
                    f"ذخیره فروشگاه انجام نشد:\n\n{error}",
                    parent=form,
                )
            finally:
                if connection is not None:
                    connection.close()

        buttons = ttk.Frame(body)
        buttons.grid(row=5, column=0, columnspan=2, pady=(30, 5))
        ttk.Button(
            buttons,
            text="ثبت تغییرات" if is_edit else "ثبت فروشگاه",
            command=save_store,
            width=18,
        ).pack(side="right", padx=8, ipady=7)
        ttk.Button(
            buttons, text="انصراف", command=form.destroy, width=14
        ).pack(side="right", padx=8, ipady=7)

    def selected_values_or_warning():
        selection = tree.selection()
        if not selection:
            messagebox.showwarning(
                "انتخاب فروشگاه",
                "ابتدا یک فروشگاه را انتخاب کنید.",
                parent=window,
            )
            return None
        return tree.item(selection[0], "values")

    def edit_selected():
        values = selected_values_or_warning()
        if values:
            open_form("edit", values)

    def delete_selected():
        values = selected_values_or_warning()
        if not values:
            return
        store_code = int(values[0])
        if not messagebox.askyesno(
            "تأیید حذف",
            f"آیا فروشگاه {store_code} حذف شود؟",
            parent=window,
        ):
            return

        connection = None
        try:
            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute("DELETE FROM dbo.Store WHERE StoreCode = ?;", store_code)
            connection.commit()
            messagebox.showinfo(
                "حذف موفق",
                "فروشگاه با موفقیت حذف شد.",
                parent=window,
            )
            refresh_stores()
        except pyodbc.IntegrityError:
            if connection is not None:
                connection.rollback()
            messagebox.showerror(
                "حذف امکان‌پذیر نیست",
                "این فروشگاه دارای کارمند، موجودی، فروش یا اطلاعات وابسته است.",
                parent=window,
            )
        except Exception as error:
            if connection is not None:
                connection.rollback()
            messagebox.showerror(
                "خطا",
                f"حذف فروشگاه انجام نشد:\n\n{error}",
                parent=window,
            )
        finally:
            if connection is not None:
                connection.close()

    tree.bind("<Double-1>", lambda _event: edit_selected())

    buttons = ttk.Frame(window, padding=(15, 5, 15, 15))
    buttons.pack(fill="x")
    ttk.Button(
        buttons, text="افزودن فروشگاه", command=lambda: open_form("add"), width=19
    ).pack(side="right", padx=6, ipady=7)
    ttk.Button(
        buttons, text="ویرایش فروشگاه", command=edit_selected, width=19
    ).pack(side="right", padx=6, ipady=7)
    ttk.Button(
        buttons, text="حذف فروشگاه", command=delete_selected, width=19
    ).pack(side="right", padx=6, ipady=7)
    ttk.Button(
        buttons, text="تازه‌سازی", command=refresh_stores, width=15
    ).pack(side="right", padx=6, ipady=7)
    ttk.Button(
        buttons, text="بستن", command=window.destroy, width=15
    ).pack(side="left", padx=6, ipady=7)

    refresh_stores()
