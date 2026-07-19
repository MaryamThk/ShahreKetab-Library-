import tkinter as tk
from tkinter import messagebox, ttk

from database import fetch_all
from ui_helpers import clear_tree, make_scrollable_tree


def open_critical_inventory_window(parent):
    window = tk.Toplevel(parent)
    window.title("موجودی‌های بحرانی")
    window.geometry("1080x620")
    window.minsize(850, 500)

    ttk.Label(
        window,
        text="کتاب‌های دارای موجودی کمتر از حداقل مجاز",
        font=("Tahoma", 17, "bold"),
    ).pack(pady=(15, 8))

    filter_frame = ttk.LabelFrame(window, text="فیلتر", padding=10)
    filter_frame.pack(fill="x", padx=15, pady=(0, 8))
    store_var = tk.StringVar()
    ttk.Label(filter_frame, text="کد فروشگاه (اختیاری):").pack(side="right", padx=6)
    ttk.Entry(
        filter_frame,
        textvariable=store_var,
        width=20,
        justify="right",
    ).pack(side="right", padx=6)

    table_frame, tree = make_scrollable_tree(window)
    table_frame.pack(fill="both", expand=True, padx=15, pady=8)

    columns = (
        "کد فروشگاه",
        "شهر",
        "عنوان کتاب",
        "شابک",
        "موجودی فعلی",
        "حداقل موجودی",
        "کسری",
        "توضیحات",
    )
    widths = (105, 100, 210, 110, 110, 110, 90, 220)
    tree.configure(columns=columns)
    for name, width in zip(columns, widths):
        tree.heading(name, text=name)
        tree.column(name, width=width, anchor="center")

    status_var = tk.StringVar()
    ttk.Label(window, textvariable=status_var).pack(pady=4)

    def refresh():
        clear_tree(tree)
        query = """
        SELECT
            i.StoreCode,
            c.CityName,
            b.Title,
            i.ISBN,
            i.AvailableQuantity,
            i.MinimumQuantity,
            i.MinimumQuantity - i.AvailableQuantity AS Shortage,
            ISNULL(i.Description, N'')
        FROM dbo.Inventory AS i
        INNER JOIN dbo.Store AS s ON s.StoreCode = i.StoreCode
        INNER JOIN dbo.City AS c ON c.CityCode = s.CityCode
        INNER JOIN dbo.Book AS b ON b.ISBN = i.ISBN
        WHERE i.AvailableQuantity < i.MinimumQuantity
        """
        parameters = []
        store_text = store_var.get().strip()
        if store_text:
            try:
                store_code = int(store_text)
            except ValueError:
                messagebox.showwarning(
                    "کد نامعتبر",
                    "کد فروشگاه باید عدد باشد.",
                    parent=window,
                )
                return
            query += " AND i.StoreCode = ?"
            parameters.append(store_code)
        query += " ORDER BY Shortage DESC, i.StoreCode, b.Title;"

        try:
            _, rows = fetch_all(query, tuple(parameters))
            for row in rows:
                tree.insert("", "end", values=tuple(row))
            status_var.set(f"تعداد موجودی‌های بحرانی: {len(rows)}")
        except Exception as error:
            messagebox.showerror(
                "خطای پایگاه داده",
                f"دریافت موجودی‌های بحرانی انجام نشد:\n\n{error}",
                parent=window,
            )

    ttk.Button(filter_frame, text="نمایش", command=refresh, width=14).pack(
        side="right", padx=8
    )

    buttons = ttk.Frame(window, padding=(15, 5, 15, 15))
    buttons.pack(fill="x")
    ttk.Button(buttons, text="تازه‌سازی", command=refresh, width=15).pack(
        side="right", padx=6, ipady=7
    )
    ttk.Button(buttons, text="بستن", command=window.destroy, width=15).pack(
        side="left", padx=6, ipady=7
    )

    refresh()
