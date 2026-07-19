import csv
from datetime import date, datetime
from decimal import Decimal
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


def format_value(value):
    if value is None:
        return ""
    if isinstance(value, Decimal):
        return f"{value:,.0f}"
    if isinstance(value, (date, datetime)):
        return value.strftime("%Y-%m-%d")
    return str(value)


def clear_tree(tree):
    for item_id in tree.get_children():
        tree.delete(item_id)


def rebuild_tree(tree, columns, rows, default_width=140):
    """ستون‌ها و ردیف‌های Treeview را از نو می‌سازد."""
    clear_tree(tree)
    tree.configure(columns=columns, show="headings")

    for column_name in columns:
        tree.heading(column_name, text=column_name)
        tree.column(
            column_name,
            width=default_width,
            minwidth=80,
            anchor="center",
            stretch=True,
        )

    for row in rows:
        tree.insert(
            "",
            "end",
            values=tuple(format_value(value) for value in row),
        )


def export_tree_to_csv(tree, parent):
    columns = list(tree["columns"])
    items = tree.get_children()

    if not columns or not items:
        messagebox.showwarning(
            "خروجی خالی",
            "ابتدا یک گزارش دارای نتیجه اجرا کنید.",
            parent=parent,
        )
        return

    file_path = filedialog.asksaveasfilename(
        parent=parent,
        title="ذخیره خروجی گزارش",
        defaultextension=".csv",
        filetypes=[("CSV UTF-8", "*.csv")],
    )

    if not file_path:
        return

    with open(file_path, "w", encoding="utf-8-sig", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(columns)
        for item_id in items:
            writer.writerow(tree.item(item_id, "values"))

    messagebox.showinfo(
        "ذخیره شد",
        "خروجی گزارش با موفقیت ذخیره شد.",
        parent=parent,
    )


def make_scrollable_tree(parent):
    frame = ttk.Frame(parent)
    tree = ttk.Treeview(frame, show="headings", selectmode="browse")
    v_scroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    h_scroll = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

    tree.grid(row=0, column=0, sticky="nsew")
    v_scroll.grid(row=0, column=1, sticky="ns")
    h_scroll.grid(row=1, column=0, sticky="ew")
    frame.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)
    return frame, tree
