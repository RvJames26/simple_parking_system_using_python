from parking_app import ParkingApp
from parking_lot import ParkingLot


def main():
    lot = ParkingLot()
    app = ParkingApp(lot)
    app.run()


if __name__ == "__main__":
    main()
