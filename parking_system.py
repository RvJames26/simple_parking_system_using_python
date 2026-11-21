import json
import os
import re
from datetime import datetime

try:
    import tkinter as tk
    from tkinter import messagebox
except ImportError:
    tk = None
    messagebox = None

SLOT_COUNT = 90
SLOTS_PER_ROW = 15
BASE_HOURS = 2
BASE_FEE = 50
EXTRA_HOURLY_FEE = 20

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
RECORDS_DIR = os.path.join(DATA_DIR, "records")
ACTIVE_FILE = os.path.join(DATA_DIR, "active_slots.json")

# shortcut: standard MV and MC series only; add a category-specific pattern for special plates.
PH_PLATE_PATTERN = re.compile(
    r"(?:[A-Z]{3}[ -]?[0-9]{2,4}|[0-9]{3}[ -]?[A-Z]{2,3}|[A-Z]{2}[ -]?[0-9]{5})"
)


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp_path, path)


def load_active_slots(path=ACTIVE_FILE):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_active_slots(active_data, path=ACTIVE_FILE):
    data = {
        slot: {
            "plate": info["plate"],
            "entry_time": info["entry_time"].isoformat()
            if isinstance(info["entry_time"], datetime)
            else info["entry_time"],
        }
        for slot, info in active_data.items()
    }
    save_json(path, data)


def log_transaction(slot, plate, entry_time, exit_time, hours, amount, records_dir=RECORDS_DIR):
    date_str = f"{exit_time:%Y-%m-%d}"
    record_file = os.path.join(records_dir, f"{date_str}.json")
    record = {
        "date": date_str,
        "total_vehicles": 0,
        "total_revenue": 0.0,
        "transactions": [],
    }
    if os.path.exists(record_file):
        try:
            with open(record_file, "r", encoding="utf-8") as f:
                record = json.load(f)
        except Exception:
            pass

    tx = {
        "slot": slot,
        "plate": plate,
        "entry_time": entry_time.isoformat() if isinstance(entry_time, datetime) else entry_time,
        "exit_time": exit_time.isoformat() if isinstance(exit_time, datetime) else exit_time,
        "hours_parked": round(hours, 2),
        "amount_paid": round(amount, 2),
    }
    record["transactions"].append(tx)
    record["total_vehicles"] = len(record["transactions"])
    record["total_revenue"] = round(sum(t["amount_paid"] for t in record["transactions"]), 2)
    save_json(record_file, record)
    return record


def main():
    if tk is None:
        raise RuntimeError("Tkinter is required to run the UI application.")

    root = tk.Tk()
    root.title("Parking System")
    try:
        root.state("zoomed")
    except tk.TclError:
        try:
            root.attributes("-zoomed", True)
        except tk.TclError:
            pass

    header = tk.Frame(root)
    header.grid(row=0, column=1, columnspan=SLOTS_PER_ROW, pady=20, sticky="ew")
    tk.Label(header, text="Parking System", font=("Arial", 18, "bold")).pack(side="left")

    parking_data = {}
    buttons = {}

    def open_daily_summary():
        today_str = f"{datetime.now():%Y-%m-%d}"
        today_file = os.path.join(RECORDS_DIR, f"{today_str}.json")
        total_v = 0
        total_r = 0.0
        txs = []
        if os.path.exists(today_file):
            try:
                with open(today_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    total_v = data.get("total_vehicles", 0)
                    total_r = data.get("total_revenue", 0.0)
                    txs = data.get("transactions", [])
            except Exception:
                pass

        win = tk.Toplevel(root)
        win.title(f"Daily Summary - {today_str}")
        win.geometry("520x450")

        tk.Label(win, text=f"Daily Summary ({today_str})", font=("Arial", 15, "bold")).pack(pady=10)
        tk.Label(
            win,
            text=f"Vehicles Served: {total_v}    |    Total Revenue: P{total_r:,.2f}",
            font=("Arial", 12),
        ).pack(pady=5)

        list_frame = tk.Frame(win)
        list_frame.pack(fill="both", expand=True, padx=15, pady=10)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")

        listbox = tk.Listbox(list_frame, font=("Courier", 10), yscrollcommand=scrollbar.set)
        for t in txs:
            listbox.insert(
                "end",
                f"{t.get('slot')} | {t.get('plate')} | {t.get('hours_parked', 0):.2f}h | P{t.get('amount_paid', 0):,.2f}",
            )
        if not txs:
            listbox.insert("end", "No completed transactions recorded today.")
        listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=listbox.yview)

        tk.Button(win, text="Close", command=win.destroy).pack(pady=10)
        win.grab_set()

    tk.Button(header, text="Daily Summary", font=("Arial", 12), command=open_daily_summary).pack(side="right")

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
            parking_data[slot_name] = {"plate": plate_text, "entry_time": entry_time}
            save_active_slots(parking_data)
            new_window.destroy()

        tk.Button(new_window, text="Enter", command=clicked_enter).pack(pady=20)
        new_window.bind("<Return>", lambda _e: clicked_enter())
        new_window.grab_set()
        plate_number.focus_set()

    def check_out(button, slot_name):
        new_window = tk.Toplevel(root)
        new_window.title(f"Check Out - {slot_name}")
        new_window.geometry("500x500")

        info = parking_data[slot_name]
        start_time = info["entry_time"]
        plate_text = info["plate"]
        exit_time = datetime.now()
        hours_parked = (exit_time - start_time).total_seconds() / 3600
        amount_to_pay = BASE_FEE + max(0, hours_parked - BASE_HOURS) * EXTRA_HOURLY_FEE

        bill_text = (
            f"Slot: {slot_name}\n"
            f"Plate: {plate_text}\n\n"
            f"Time Parked: {hours_parked:.2f} Hours\n\n"
            f"Total Due: P{amount_to_pay:,.2f}"
        )
        tk.Label(new_window, text=bill_text, font=("Arial", 18)).pack(pady=40)

        def clicked_pay():
            log_transaction(
                slot_name, plate_text, start_time, exit_time, hours_parked, amount_to_pay
            )
            del parking_data[slot_name]
            save_active_slots(parking_data)
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
        buttons[slot_name] = button

    # Restore persisted active slots on startup
    for s_name, s_info in load_active_slots().items():
        if s_name in buttons:
            try:
                e_time = datetime.fromisoformat(s_info["entry_time"])
                p_text = s_info.get("plate", "")
                parking_data[s_name] = {"plate": p_text, "entry_time": e_time}
                buttons[s_name].config(
                    text=f"{p_text}\n{e_time:%I:%M %p}", bg="red", fg="black"
                )
            except (ValueError, KeyError, TypeError):
                continue

    root.mainloop()


if __name__ == "__main__":
    main()
