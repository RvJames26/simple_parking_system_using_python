import os
import shutil
import tempfile
import unittest
from datetime import datetime

from parking_system import (
    load_active_slots,
    log_transaction,
    save_active_slots,
    save_json,
)


class TestPersistence(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.active_file = os.path.join(self.test_dir, "active_slots.json")
        self.records_dir = os.path.join(self.test_dir, "records")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_active_slots_roundtrip(self):
        entry = datetime(2026, 11, 21, 14, 30, 0)
        data = {
            "Slot 1": {"plate": "ABC 1234", "entry_time": entry},
            "Slot 2": {"plate": "NDB 5432", "entry_time": entry.isoformat()},
        }
        save_active_slots(data, path=self.active_file)
        loaded = load_active_slots(path=self.active_file)

        self.assertEqual(len(loaded), 2)
        self.assertEqual(loaded["Slot 1"]["plate"], "ABC 1234")
        self.assertEqual(loaded["Slot 1"]["entry_time"], entry.isoformat())
        self.assertEqual(loaded["Slot 2"]["plate"], "NDB 5432")

    def test_log_transaction_and_daily_totals(self):
        entry_time = datetime(2026, 11, 21, 10, 0, 0)
        exit_time = datetime(2026, 11, 21, 13, 0, 0)

        # First transaction
        record1 = log_transaction(
            "Slot 1", "ABC 1234", entry_time, exit_time, 3.0, 70.0, records_dir=self.records_dir
        )
        self.assertEqual(record1["total_vehicles"], 1)
        self.assertEqual(record1["total_revenue"], 70.0)
        self.assertEqual(len(record1["transactions"]), 1)

        # Second transaction on same day
        record2 = log_transaction(
            "Slot 5", "XYZ 9876", entry_time, exit_time, 2.0, 50.0, records_dir=self.records_dir
        )
        self.assertEqual(record2["total_vehicles"], 2)
        self.assertEqual(record2["total_revenue"], 120.0)
        self.assertEqual(len(record2["transactions"]), 2)

    def test_missing_or_corrupt_active_file(self):
        # Missing file
        missing_file = os.path.join(self.test_dir, "nonexistent.json")
        self.assertEqual(load_active_slots(path=missing_file), {})

        # Corrupt file
        with open(missing_file, "w") as f:
            f.write("{corrupt json...")
        self.assertEqual(load_active_slots(path=missing_file), {})


if __name__ == "__main__":
    unittest.main()
