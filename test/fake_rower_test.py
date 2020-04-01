import time
import threading

from rowercast.ant_rower import AntRower
from rowercast.rower import Rower
# this test could not be done automatically, you have to grab a outside display/receive device
# to test for real.
def _fake_rower_updater(rower, update_rate):
    const_speed = 2  # 2m/s

    fake_session_time = 0  # unit, Second
    fake_session_distance = 0  # unit, Meter
    fake_session_instant_speed = 0  # unit, M/s

    while True:
        rower.update(fake_session_time, fake_session_distance, fake_session_instant_speed)
        rower.print_current_info()

        fake_session_time += update_rate
        fake_session_distance += update_rate * const_speed
        fake_session_instant_speed = const_speed

        time.sleep(update_rate)


def _fake_rower_test(update_rate):
    """Test function for ant+ rower broadcast

    This function will fake a rower source, update self rower's data once per X second.

    update_rate: X, update rower data per X seconds,

    sleep for X secs, then update.

    :param update_rate: X, number, in secs
    :return:
    """

    ant_rower = AntRower()
    x = threading.Thread(target=_fake_rower_updater, args=(ant_rower, update_rate))
    x.start()
    x.join()
    ant_rower.start()


if __name__ == '__main__':
    _fake_rower_test(0.5)
