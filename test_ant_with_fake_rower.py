"""Use fake data to test the ant+ part of code."""

from rower import Rower
from ant_rower import AntRower
from serial_reader import FakeRower
from config import ANT_CONFIG

SERIAL_ADDRESS = ''


def main():
    print('fake rower, start.')
    # shared data object of a rower.
    my_rower = Rower()
    # serial data reader.
    serial_reader = FakeRower(my_rower)
    # Ant+ FE rower broadcaster.
    ant_broadcaster = AntRower(my_rower, ANT_CONFIG)

    # start reading, start broadcasting.
    try:
        ant_broadcaster.start()
        serial_reader.start()
    # except:
    #     # todo: how to deal with the exception?
    #     pass
    finally:
        # todo: close the program, release the hardware.
        serial_reader.close()
        ant_broadcaster.close()

    print('fake rower, exit.')


if __name__ == "__main__":
    main()
