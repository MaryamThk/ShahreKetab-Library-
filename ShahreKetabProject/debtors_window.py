import tkinter as tk
from tkinter import messagebox, ttk

from database import fetch_all
from ui_helpers import clear_tree, make_scrollable_tree


def open_debtors_window(parent):
    window = tk.Toplevel(parent)
    window.title("مشتریان بدهکار")
    window.geometry("950x600")
    window.minsize(780, 500)

    ttk.Label(
        window,
        text="فهرست مشتریان بدهکار",
        font=("Tahoma", 17, "bold"),
    ).pack(pady=(15, 8))

    filter_frame = ttk.LabelFrame(window, text="فیلتر بدهی", padding=10)
    filter_frame.pack(fill="x", padx=15, pady=(0, 8))

    minimum_var = tk.StringVar(value="0")
    ttk.Label(filter_frame, text="حداقل مبلغ بدهی:").pack(side="right", padx=6)
    ttk.Entry(
        filter_frame,
        textvariable=minimum_var,
        width=22,
        justify="right",
    ).pack(side="right", padx=6)

    table_frame, tree = make_scrollable_tree(window)
    table_frame.pack(fill="both", expand=True, padx=15, pady=8)

    columns = ("کد مشتری", "نام مشتری", "تلفن", "آدرس", "مبلغ بدهی")
    widths = (120, 160, 140, 260, 160)
    tree.configure(columns=columns)
    for name, width in zip(columns, widths):
        tree.heading(name, text=name)
        tree.column(name, width=width, anchor="center")

    status_var = tk.StringVar()
    ttk.Label(
        window,
        textvariable=status_var,
        font=("Tahoma", 11, "bold"),
    ).pack(pady=5)

    def refresh():
        try:
            minimum = float(minimum_var.get().replace(",", "").strip())
            if minimum < 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning(
                "مبلغ نامعتبر",
                "حداقل مبلغ بدهی باید صفر یا مثبت باشد.",
                parent=window,
            )
            return

        clear_tree(tree)
        try:
            _, rows = fetch_all(
                """
                SELECT CustomerCode, FullName, Phone, Address, DebtAmount
                FROM dbo.Customer
                WHERE DebtAmount > ?
                ORDER BY DebtAmount DESC;
                """,
                (minimum,),
            )
            total = 0
            for row in rows:
                total += row[4]
                tree.insert(
                    "",
                    "end",
                    values=(
                        row[0],
                        row[1],
                        row[2] or "",
                        row[3] or "",
                        f"{row[4]:,.0f}",
                    ),
                )
            status_var.set(
                f"تعداد مشتریان: {len(rows)}   |   جمع بدهی: {total:,.0f}"
            )
        except Exception as error:
            messagebox.showerror(
                "خطای پایگاه داده",
                f"دریافت مشتریان بدهکار انجام نشد:\n\n{error}",
                parent=window,
            )

    ttk.Button(
        filter_frame,
        text="نمایش",
        command=refresh,
        width=14,
    ).pack(side="right", padx=8)

    buttons = ttk.Frame(window, padding=(15, 5, 15, 15))
    buttons.pack(fill="x")
    ttk.Button(buttons, text="تازه‌سازی", command=refresh, width=15).pack(
        side="right", padx=6, ipady=7
    )
    ttk.Button(buttons, text="بستن", command=window.destroy, width=15).pack(
        side="left", padx=6, ipady=7
    )

    refresh()
