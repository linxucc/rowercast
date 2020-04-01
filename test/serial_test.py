"""Rowercast main entry point

This module should be used as the starting point of rowercast.

This script starts the serial_reader and ant+ radio in separate threads.

Whenever the SerialReader gets a new message, it will update the data model "AntRower".
Whenever an Ant "TX_Event" (the TX "tick") happens, it will get a new message from "AntRower", and
send it as a broadcast.

"""

from rower import Rower
# from ant_rower import AntRower
from serial_reader import SerialReader

SERIAL_ADDRESS = '/dev/tty.usbserial-AH05EI1N'


def main():
    print('serial test, start.')
    # shared data object of a rower.
    my_rower = Rower()
    # serial data reader.
    serial_reader = SerialReader(my_rower, SERIAL_ADDRESS)
    # Ant+ FE rower broadcaster.
    # ant_broadcaster = AntRower(my_rower)

    # start reading, start broadcasting.
    try:
        # ant_broadcaster.start()
        serial_reader.start()
    # except:
    #     # todo: how to deal with the exception?
    #     pass
    finally:
        # todo: close the program, release the hardware.
        serial_reader.close()
        # ant_broadcaster.close()

    print('serial test, exit.')


if __name__ == "__main__":
    main()
