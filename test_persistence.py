import os
import shutil
import tempfile
import unittest
from datetime import datetime, timedelta

from parking_lot import ParkingLot


class TestParkingLot(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.lot = ParkingLot(data_dir=self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_check_in_valid_plate(self):
        record = self.lot.check_in("Slot 1", "ABC 1234")
        self.assertEqual(record["plate"], "ABC 1234")
        self.assertTrue(self.lot.is_occupied("Slot 1"))

    def test_check_in_invalid_plate_raises_error(self):
        with self.assertRaises(ValueError):
            self.lot.check_in("Slot 1", "INVALID_PLATE")

    def test_check_in_occupied_slot_raises_error(self):
        self.lot.check_in("Slot 1", "ABC 1234")
        with self.assertRaises(ValueError):
            self.lot.check_in("Slot 1", "XYZ 5678")

    def test_calculate_bill_and_checkout(self):
        entry_time = datetime(2026, 11, 22, 8, 0, 0)
        exit_time = datetime(2026, 11, 22, 11, 0, 0)  # 3 hours parked

        self.lot.check_in("Slot 1", "ABC 1234", entry_time=entry_time)

        # Base fee (50) for 2 hours + 1 extra hour (20) = 70.0
        bill = self.lot.check_out("Slot 1", exit_time=exit_time)
        self.assertEqual(bill["hours"], 3.0)
        self.assertEqual(bill["amount"], 70.0)
        self.assertFalse(self.lot.is_occupied("Slot 1"))

        # Check daily summary
        summary = self.lot.get_daily_summary(exit_time)
        self.assertEqual(summary["total_vehicles"], 1)
        self.assertEqual(summary["total_revenue"], 70.0)

    def test_persistence_reload(self):
        entry_time = datetime(2026, 11, 22, 8, 0, 0)
        self.lot.check_in("Slot 5", "NDB 5432", entry_time=entry_time)

        # Create new ParkingLot instance pointing to same directory
        reloaded_lot = ParkingLot(data_dir=self.test_dir)
        self.assertTrue(reloaded_lot.is_occupied("Slot 5"))
        self.assertEqual(reloaded_lot.get_slot("Slot 5")["plate"], "NDB 5432")


if __name__ == "__main__":
    unittest.main()
