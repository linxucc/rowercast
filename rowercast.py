"""Rowercast main entry point

This module should be used as the starting point of rowercast.

This script starts the serial_reader and ant+ radio in separate threads.

Whenever the SerialReader gets a new message, it will update the data model "AntRower".
Whenever an Ant "TX_Event" (the TX "tick") happens, it will get a new message from "AntRower", and
send it as a broadcast.

"""

from rower import Rower
from ant_rower import AntRower
from serial_reader import FDFReader
from config import SERIAL_ADDRESS, ANT_CONFIG


def main():
    print('rowercast, start.')
    # shared data object of a rower.
    my_rower = Rower()
    # serial data reader.
    serial_reader = FDFReader(my_rower, SERIAL_ADDRESS)
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

    print('rowercast, exit.')


if __name__ == "__main__":
    main()
