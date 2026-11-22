from datetime import datetime

try:
    import tkinter as tk
    from tkinter import messagebox
except ImportError:
    tk = None
    messagebox = None


class ParkingApp:
    """Tkinter graphical user interface for the parking system."""

    SLOTS_PER_ROW = 15

    def __init__(self, lot, root=None):
        if tk is None:
            raise RuntimeError("Tkinter is required to run the UI application.")

        self.lot = lot
        self.root = root or tk.Tk()
        self.buttons = {}
        self._init_window()
        self._build_ui()
        self._restore_slots()

    def _init_window(self):
        self.root.title("Parking System")
        try:
            self.root.state("zoomed")
        except tk.TclError:
            try:
                self.root.attributes("-zoomed", True)
            except tk.TclError:
                pass

    def _build_ui(self):
        header = tk.Frame(self.root)
        header.grid(row=0, column=1, columnspan=self.SLOTS_PER_ROW, pady=20, sticky="ew")
        tk.Label(header, text="Parking System", font=("Arial", 18, "bold")).pack(side="left")
        tk.Button(
            header, text="Daily Summary", font=("Arial", 12), command=self.open_daily_summary
        ).pack(side="right")

        for i in range(self.lot.slot_count):
            slot_name = f"Slot {i + 1}"
            btn = tk.Button(
                self.root,
                bg="#00ff00",
                text=slot_name,
                font=("Arial", 14),
                width=5,
                height=3,
                command=lambda s=slot_name: self.handle_slot_click(s),
            )
            row, column = divmod(i, self.SLOTS_PER_ROW)
            btn.grid(row=row + 1, column=column + 1, padx=10, pady=10)
            self.buttons[slot_name] = btn

    def _restore_slots(self):
        for slot_name, info in self.lot.active_slots.items():
            self._set_button_occupied(slot_name, info["plate"], info["entry_time"])

    def _set_button_occupied(self, slot_name, plate, entry_time):
        if slot_name in self.buttons:
            self.buttons[slot_name].config(
                text=f"{plate}\n{entry_time:%I:%M %p}", bg="red", fg="black"
            )

    def _set_button_available(self, slot_name):
        if slot_name in self.buttons:
            self.buttons[slot_name].config(text=slot_name, bg="#00ff00", fg="black")

    def handle_slot_click(self, slot_name):
        if self.lot.is_occupied(slot_name):
            self.open_check_out(slot_name)
        else:
            self.open_check_in(slot_name)

    def open_check_in(self, slot_name):
        win = tk.Toplevel(self.root)
        win.title(f"Check In - {slot_name}")
        win.geometry("500x500")

        tk.Label(win, text=f"Input your Plate Number for {slot_name}:").pack(pady=30, padx=30)
        plate_input = tk.Entry(win, font=("Arial", 14))
        plate_input.pack()

        def submit():
            plate_text = plate_input.get()
            try:
                record = self.lot.check_in(slot_name, plate_text)
                self._set_button_occupied(slot_name, record["plate"], record["entry_time"])
                win.destroy()
            except ValueError as err:
                messagebox.showerror("Invalid plate number", str(err), parent=win)

        tk.Button(win, text="Enter", command=submit).pack(pady=20)
        win.bind("<Return>", lambda _e: submit())
        win.grab_set()
        plate_input.focus_set()

    def open_check_out(self, slot_name):
        try:
            bill = self.lot.calculate_bill(slot_name)
        except ValueError as err:
            messagebox.showerror("Error", str(err), parent=self.root)
            return

        win = tk.Toplevel(self.root)
        win.title(f"Check Out - {slot_name}")
        win.geometry("500x500")

        bill_text = (
            f"Slot: {bill['slot']}\n"
            f"Plate: {bill['plate']}\n\n"
            f"Time Parked: {bill['hours']:.2f} Hours\n\n"
            f"Total Due: P{bill['amount']:,.2f}"
        )
        tk.Label(win, text=bill_text, font=("Arial", 18)).pack(pady=40)

        def pay_and_exit():
            self.lot.check_out(slot_name)
            self._set_button_available(slot_name)
            win.destroy()

        tk.Button(
            win,
            text="Pay & Exit",
            bg="red",
            fg="white",
            font=("Arial", 14),
            command=pay_and_exit,
        ).pack(pady=20)
        win.grab_set()

    def open_daily_summary(self):
        summary = self.lot.get_daily_summary()
        win = tk.Toplevel(self.root)
        win.title(f"Daily Summary - {summary['date']}")
        win.geometry("520x450")

        tk.Label(win, text=f"Daily Summary ({summary['date']})", font=("Arial", 15, "bold")).pack(pady=10)
        tk.Label(
            win,
            text=f"Vehicles Served: {summary['total_vehicles']}    |    Total Revenue: P{summary['total_revenue']:,.2f}",
            font=("Arial", 12),
        ).pack(pady=5)

        list_frame = tk.Frame(win)
        list_frame.pack(fill="both", expand=True, padx=15, pady=10)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")

        listbox = tk.Listbox(list_frame, font=("Courier", 10), yscrollcommand=scrollbar.set)
        for t in summary["transactions"]:
            listbox.insert(
                "end",
                f"{t.get('slot')} | {t.get('plate')} | {t.get('hours_parked', 0):.2f}h | P{t.get('amount_paid', 0):,.2f}",
            )
        if not summary["transactions"]:
            listbox.insert("end", "No completed transactions recorded today.")

        listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=listbox.yview)

        tk.Button(win, text="Close", command=win.destroy).pack(pady=10)
        win.grab_set()

    def run(self):
        self.root.mainloop()
