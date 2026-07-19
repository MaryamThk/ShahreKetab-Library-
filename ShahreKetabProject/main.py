import tkinter as tk
from tkinter import messagebox, ttk

from books_window import open_books_window
from critical_inventory_window import open_critical_inventory_window
from database import test_connection
from debtors_window import open_debtors_window
from inventory_window import open_inventory_window
from reports_window import open_reports_window
from sales_window import open_sales_window
from stores_window import open_stores_window


def main():
    root = tk.Tk()
    root.title("سیستم مدیریت فروشگاه‌های زنجیره‌ای شهر کتاب")
    root.geometry("940x650")
    root.minsize(820, 570)

    style = ttk.Style()
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    style.configure("Main.TButton", font=("Tahoma", 11), padding=(12, 13))
    style.configure("Title.TLabel", font=("Tahoma", 19, "bold"))
    style.configure("Subtitle.TLabel", font=("Tahoma", 10))

    main_frame = ttk.Frame(root, padding=30)
    main_frame.pack(fill="both", expand=True)

    ttk.Label(
        main_frame,
        text="سیستم مدیریت فروشگاه‌های زنجیره‌ای شهر کتاب",
        style="Title.TLabel",
    ).pack(pady=(15, 8))

    ttk.Label(
        main_frame,
        text="پروژه نهایی آزمایشگاه پایگاه داده",
        style="Subtitle.TLabel",
    ).pack(pady=(0, 18))

    connection_var = tk.StringVar(value="در حال بررسی اتصال به پایگاه داده...")
    connection_label = ttk.Label(
        main_frame,
        textvariable=connection_var,
        font=("Tahoma", 9),
    )
    connection_label.pack(pady=(0, 20))

    buttons_frame = ttk.Frame(main_frame)
    buttons_frame.pack(expand=True)

    buttons = [
        ("مدیریت فروشگاه‌ها", lambda: open_stores_window(root)),
        ("مدیریت کتاب‌ها", lambda: open_books_window(root)),
        ("مدیریت موجودی", lambda: open_inventory_window(root)),
        ("ثبت فروش جدید", lambda: open_sales_window(root)),
        ("مشتریان بدهکار", lambda: open_debtors_window(root)),
        ("موجودی‌های بحرانی", lambda: open_critical_inventory_window(root)),
        ("جستجو و گزارش‌گیری", lambda: open_reports_window(root)),
        ("خروج از سیستم", root.destroy),
    ]

    for index, (button_text, command) in enumerate(buttons):
        row = index // 2
        column = index % 2
        ttk.Button(
            buttons_frame,
            text=button_text,
            command=command,
            width=31,
            style="Main.TButton",
        ).grid(
            row=row,
            column=column,
            padx=18,
            pady=14,
            sticky="nsew",
        )

    for row in range(4):
        buttons_frame.rowconfigure(row, weight=1)
    for column in range(2):
        buttons_frame.columnconfigure(column, weight=1)

    ttk.Label(
        main_frame,
        text="Python + Tkinter + SQL Server + PyODBC",
        font=("Tahoma", 9),
    ).pack(pady=(25, 5))

    try:
        database_name, book_count = test_connection()
        connection_var.set(
            f"اتصال برقرار است | دیتابیس: {database_name} | تعداد کتاب‌ها: {book_count}"
        )
    except Exception as error:
        connection_var.set("اتصال به پایگاه داده برقرار نشد.")
        messagebox.showerror(
            "خطای اتصال",
            "برنامه نتوانست به SQL Server متصل شود.\n"
            "تنظیمات فایل database.py را بررسی کنید.\n\n"
            f"{error}",
            parent=root,
        )

    root.mainloop()


if __name__ == "__main__":
    main()
