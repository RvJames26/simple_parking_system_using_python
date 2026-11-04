import re
import tkinter as tk
from datetime import datetime
from tkinter import messagebox

SLOT_COUNT = 90
SLOTS_PER_ROW = 15
BASE_HOURS = 2
BASE_FEE = 50
EXTRA_HOURLY_FEE = 20
# shortcut: standard MV and MC series only; add a category-specific pattern for special plates.
PH_PLATE_PATTERN = re.compile(
    r"(?:[A-Z]{3}[ -]?[0-9]{2,4}|[0-9]{3}[ -]?[A-Z]{2,3}|[A-Z]{2}[ -]?[0-9]{5})"
)

root = tk.Tk()
root.title("Parking System")
root.state("zoomed")

label = tk.Label(root, text="Parking system")
label.grid(pady=30, padx=30)
parking_data = {}


def open_check_in(button, slot_name):
    new_window = tk.Toplevel(root)
    new_window.title(f"Check In - {slot_name}")
    new_window.geometry("500x500")

    tk.Label(new_window, text=f"Input your Plate Number for {slot_name}:").pack(
        pady=30, padx=30
    )
    plate_number = tk.Entry(new_window, font=("Arial", 14))
    plate_number.pack()

    def clicked_enter():
        plate_text = plate_number.get().strip().upper()
        if not PH_PLATE_PATTERN.fullmatch(plate_text):
            messagebox.showerror(
                "Invalid plate number",
                "Use a standard Philippine plate, e.g. ABC 1234, ABC 123, 123 ABC, or AB 12345.",
                parent=new_window,
            )
            return

        entry_time = datetime.now()
        button.config(
            text=f"{plate_text}\n{entry_time:%I:%M %p}", bg="red", fg="black"
        )
        parking_data[slot_name] = entry_time
        new_window.destroy()

    tk.Button(new_window, text="Enter", command=clicked_enter).pack(pady=20)
    new_window.grab_set()
    plate_number.focus_set()


def check_out(button, slot_name):
    new_window = tk.Toplevel(root)
    new_window.title(f"Check Out - {slot_name}")
    new_window.geometry("500x500")

    start_time = parking_data[slot_name]
    hours_parked = (datetime.now() - start_time).total_seconds() / 3600
    amount_to_pay = BASE_FEE + max(0, hours_parked - BASE_HOURS) * EXTRA_HOURLY_FEE

    bill_text = (
        f"Slot: {slot_name}\n\n"
        f"Time Parked: {hours_parked:.2f} Hours\n\n"
        f"Total Due: P{amount_to_pay:,.2f}"
    )
    tk.Label(new_window, text=bill_text, font=("Arial", 18)).pack(pady=40)

    def clicked_pay():
        del parking_data[slot_name]
        button.config(text=slot_name, bg="#00ff00", fg="black")
        new_window.destroy()

    tk.Button(
        new_window,
        text="Pay & Exit",
        bg="red",
        fg="white",
        font=("Arial", 14),
        command=clicked_pay,
    ).pack(pady=20)
    new_window.grab_set()


def handle_click(button, slot_name):
    if slot_name in parking_data:
        check_out(button, slot_name)
    else:
        open_check_in(button, slot_name)


for i in range(SLOT_COUNT):
    slot_name = f"Slot {i + 1}"
    button = tk.Button(
        root, bg="#00ff00", text=slot_name, font=("Arial", 14), width=5, height=3
    )
    button.config(command=lambda b=button, s=slot_name: handle_click(b, s))
    row, column = divmod(i, SLOTS_PER_ROW)
    button.grid(row=row + 1, column=column + 1, padx=10, pady=10)

root.mainloop()
