import json
import os
import re
from datetime import datetime

# shortcut: standard MV and MC series only; add a category-specific pattern for special plates.
PH_PLATE_PATTERN = re.compile(
    r"(?:[A-Z]{3}[ -]?[0-9]{2,4}|[0-9]{3}[ -]?[A-Z]{2,3}|[A-Z]{2}[ -]?[0-9]{5})"
)


def _save_json_atomic(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp_path, path)


class ParkingLot:
    """Manages parking slots, business rules, fee calculation, and persistence."""

    def __init__(
        self,
        slot_count=90,
        base_hours=2,
        base_fee=50.0,
        extra_hourly_fee=20.0,
        data_dir=None,
    ):
        self.slot_count = slot_count
        self.base_hours = base_hours
        self.base_fee = base_fee
        self.extra_hourly_fee = extra_hourly_fee

        base_dir = data_dir or os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        self.data_dir = base_dir
        self.records_dir = os.path.join(base_dir, "records")
        self.active_file = os.path.join(base_dir, "active_slots.json")

        self.active_slots = self._load_active_slots()

    def is_occupied(self, slot_name):
        return slot_name in self.active_slots

    def get_slot(self, slot_name):
        return self.active_slots.get(slot_name)

    def validate_plate(self, plate_text):
        normalized = (plate_text or "").strip().upper()
        if not PH_PLATE_PATTERN.fullmatch(normalized):
            return None
        return normalized

    def check_in(self, slot_name, plate_text, entry_time=None):
        cleaned_plate = self.validate_plate(plate_text)
        if not cleaned_plate:
            raise ValueError(
                "Use a standard Philippine plate, e.g. ABC 1234, ABC 123, 123 ABC, or AB 12345."
            )
        if self.is_occupied(slot_name):
            raise ValueError(f"{slot_name} is already occupied.")

        time_in = entry_time or datetime.now()
        self.active_slots[slot_name] = {"plate": cleaned_plate, "entry_time": time_in}
        self._save_active_slots()
        return self.active_slots[slot_name]

    def calculate_bill(self, slot_name, exit_time=None):
        if not self.is_occupied(slot_name):
            raise ValueError(f"{slot_name} is not occupied.")

        info = self.active_slots[slot_name]
        time_out = exit_time or datetime.now()
        hours = max(0.0, (time_out - info["entry_time"]).total_seconds() / 3600)
        extra_hours = max(0.0, hours - self.base_hours)
        amount = self.base_fee + (extra_hours * self.extra_hourly_fee)

        return {
            "slot": slot_name,
            "plate": info["plate"],
            "entry_time": info["entry_time"],
            "exit_time": time_out,
            "hours": hours,
            "amount": amount,
        }

    def check_out(self, slot_name, exit_time=None):
        bill = self.calculate_bill(slot_name, exit_time)
        del self.active_slots[slot_name]
        self._save_active_slots()
        self._log_transaction(bill)
        return bill

    def get_daily_summary(self, target_date=None):
        date_str = f"{(target_date or datetime.now()):%Y-%m-%d}"
        file_path = os.path.join(self.records_dir, f"{date_str}.json")
        default_summary = {
            "date": date_str,
            "total_vehicles": 0,
            "total_revenue": 0.0,
            "transactions": [],
        }
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return default_summary
        return default_summary

    def _load_active_slots(self):
        if not os.path.exists(self.active_file):
            return {}
        try:
            with open(self.active_file, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
            slots = {}
            for s_name, s_info in raw_data.items():
                slots[s_name] = {
                    "plate": s_info.get("plate", ""),
                    "entry_time": datetime.fromisoformat(s_info["entry_time"]),
                }
            return slots
        except Exception:
            return {}

    def _save_active_slots(self):
        payload = {
            slot: {
                "plate": info["plate"],
                "entry_time": info["entry_time"].isoformat(),
            }
            for slot, info in self.active_slots.items()
        }
        _save_json_atomic(self.active_file, payload)

    def _log_transaction(self, bill):
        date_str = f"{bill['exit_time']:%Y-%m-%d}"
        file_path = os.path.join(self.records_dir, f"{date_str}.json")
        summary = self.get_daily_summary(bill["exit_time"])

        summary["transactions"].append(
            {
                "slot": bill["slot"],
                "plate": bill["plate"],
                "entry_time": bill["entry_time"].isoformat(),
                "exit_time": bill["exit_time"].isoformat(),
                "hours_parked": round(bill["hours"], 2),
                "amount_paid": round(bill["amount"], 2),
            }
        )
        summary["total_vehicles"] = len(summary["transactions"])
        summary["total_revenue"] = round(sum(t["amount_paid"] for t in summary["transactions"]), 2)
        _save_json_atomic(file_path, summary)
