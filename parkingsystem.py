import tkinter as tk
import datetime

root = tk.Tk()
root.title("Parking System")
root.state('zoomed')

label = tk.Label(root, text="Parking system")
label.grid(pady=30, padx=30)
parking_data = {}

def open_second_window(b, slot_name):
    new_window = tk.Toplevel(root)
    new_window.title(f"Check In - {slot_name}")
    new_window.geometry("500x500")

    lbl = tk.Label(new_window, text=(f"Input your Plate Number for {slot_name}: "))
    lbl.pack(pady=30, padx=30);

    plate_number = tk.Entry(new_window, font=("Arial", 14));
    plate_number.pack()

    def clicked_enter():
        entry_time = datetime.datetime.now()
        display_time = entry_time.strftime("%I:%M %p")
        plate_text = plate_number.get()
        if plate_text:
            b.config(text=f"{plate_text}\n{display_time}", bg="red", fg="black")
            parking_data[slot_name] = entry_time
            new_window.destroy()

    btn_enter = tk.Button(new_window, text="Enter", command=clicked_enter)
    btn_enter.pack(pady=20)

def check_out(b, slot_name):
    new_window = tk.Toplevel(root)
    new_window.title(f"Check In - {slot_name}")
    new_window.geometry("500x500")

    start_time = parking_data[slot_name]
    end_time = datetime.datetime.now()

    duration = end_time - start_time
    total_time = duration.total_seconds()
    hours_parked = total_time / 3600

    if hours_parked <= 2:
        amount_to_pay = 50
    else:
        extra_hours = hours_parked - 2
        amount_to_pay = 50 + (extra_hours * 20)
        int(amount_to_pay)

    bill_text = f"Slot: {slot_name}\n\nTime Parked: {hours_parked} Hours\n\nTotal Due: P{amount_to_pay}"

    lbl_bill = tk.Label(new_window, text=bill_text, font=("Arial", 18))
    lbl_bill.pack(pady=40)

    def clicked_pay():
        del parking_data[slot_name]
        b.config(text=slot_name, bg="#00ff00", fg="black") 
        new_window.destroy()

    btn_pay = tk.Button(new_window, text="Pay & Exit", bg="red", fg="white", font=("Arial", 14), command=clicked_pay)
    btn_pay.pack(pady=20)

def handle_click(b, slot_name):
    if slot_name in parking_data:
        check_out(b, slot_name)
    else:
        open_second_window(b, slot_name)
row_num = 1
col_num = 1

for i in range(1, 91):
    slot_name = f"Slot {i}"

    btn = tk.Button(root,bg="#00ff00", text=f"Slot {i}", font=("Arial", 14), width=5, height=3)

    btn.config(command=lambda b=btn, s=slot_name: handle_click(b, s))

    btn.grid(row=row_num, column=col_num, padx=10, pady=10)

    col_num += 1
    if col_num > 15:
        col_num = 1
        row_num += 1

root.mainloop()