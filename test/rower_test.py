import time
import threading
import unittest

import rower

# Test of the three things: rower, ant_rower, serial_reader.

# Test of the rower class
class RowerTestCase(unittest.TestCase):

    def setUp(self):
        self.rower = rower.Rower()

    def tearDown(self):
        self.rower = None

    def test_rower_init(self):
        self.assertEqual(self.rower['total_elapsed_time'], 0)
        self.assertEqual(self.rower['total_distance_traveled'],0)
        self.assertEqual(self.rower['instantaneous_speed'], 0)

    def test_validity_check(self):
        wrong_key_data = {
            'time': 1,
            'dist': 20,
            'spd': 2.5
        }
        # should raise this error
        with self.assertRaises(rower.IncomingRowerDictInvalidKeyError) as cm:
            self.rower._check_dict_validity(wrong_key_data)

        # int field with float.
        wrong_value_1 = {
            'total_elapsed_time': 10,
            'total_distance_traveled': 10.5,
            'instantaneous_speed': 5
        }
        with self.assertRaises(rower.IncomingRowerDictInvalidValueError) as cm:
            self.rower._check_dict_validity(wrong_value_1)

        # negative value
        wrong_value_2 = {
            'total_elapsed_time': 10,
            'total_distance_traveled': 10.5,
            'instantaneous_speed': 5
        }
        with self.assertRaises(rower.IncomingRowerDictInvalidValueError) as cm:
            self.rower._check_dict_validity(wrong_value_2)

        # insufficient fields
        missing_key = {
            'total_elapsed_time': 10,
            'total_distance_traveled': 10.5,
            'instantaneous_power': 243
        }
        with self.assertRaises(rower.IncomingRowerDictMissingKeyError) as cm:
            self.rower._check_dict_validity(missing_key)

    def test_rower_update_success(self):
        good_data = {
            'total_elapsed_time': 12,
            'total_distance_traveled': 150,
            'instantaneous_speed': 2.35
        }
        self.rower.on_update_data(good_data)

        self.assertEqual(self.rower.get_current_frame()['total_elapsed_time'], 12)
        self.assertEqual(self.rower.get_current_frame()['total_distance_traveled'], 150)
        self.assertEqual(self.rower.get_current_frame()['instantaneous_speed'], 2.35)

        good_data_with_optional_fields = {
            'total_elapsed_time': 16,
            'total_distance_traveled': 170,
            'instantaneous_speed': 2.1,
            'strokes_per_minute': 32,
            'instantaneous_power': 125
        }
        self.rower.on_update_data(good_data_with_optional_fields)

        self.assertEqual(self.rower.get_current_frame()['total_elapsed_time'], 16)
        self.assertEqual(self.rower.get_current_frame()['total_distance_traveled'], 170)
        self.assertEqual(self.rower.get_current_frame()['instantaneous_speed'], 2.1)
        self.assertEqual(self.rower.get_current_frame()['strokes_per_minute'], 32)
        self.assertEqual(self.rower.get_current_frame()['instantaneous_power'], 125)

    def test_rower_update_fail_same_dict(self):
        good_data = {
            'total_elapsed_time': 12,
            'total_distance_traveled': 150,
            'instantaneous_speed': 2.35
        }
        self.rower.on_update_data(good_data)

        self.assertEqual(self.rower.get_current_frame()['total_elapsed_time'], 12)
        self.assertEqual(self.rower.get_current_frame()['total_distance_traveled'], 150)
        self.assertEqual(self.rower.get_current_frame()['instantaneous_speed'], 2.35)

        # this should be a new dict obj, with same value.
        # this case should NOT raise.
        another_good_data = {
            'total_elapsed_time': 12,
            'total_distance_traveled': 150,
            'instantaneous_speed': 2.35
        }
        self.rower.on_update_data(another_good_data)

        # same data obj again,
        # should raise error.
        with self.assertRaises(rower.IncomingRowerDictDuplicateError) as cm:
            self.rower.on_update_data(another_good_data)

if __name__=='__main__':
    unittest.main()

# # this test could not be done automatically, you have to grab a outside display/receive device
# # to test for real.
# def _fake_rower_updater(rower, update_rate):
#     const_speed = 2  # 2m/s
#
#     fake_session_time = 0  # unit, Second
#     fake_session_distance = 0  # unit, Meter
#     fake_session_instant_speed = 0  # unit, M/s
#
#     while True:
#         rower.update(fake_session_time, fake_session_distance, fake_session_instant_speed)
#         rower.print_current_info()
#
#         fake_session_time += update_rate
#         fake_session_distance += update_rate * const_speed
#         fake_session_instant_speed = const_speed
#
#         time.sleep(update_rate)
#
#
# def _fake_rower_test(update_rate):
#     """Test function for ant+ rower broadcast
#
#     This function will fake a rower source, update self rower's data once per X second.
#
#     update_rate: X, update rower data per X seconds,
#
#     sleep for X secs, then update.
#
#     :param update_rate: X, number, in secs
#     :return:
#     """
#
#     ant_rower = AntRower()
#     x = threading.Thread(target=_fake_rower_updater, args=(ant_rower, update_rate))
#     x.start()
#     x.join()
#     ant_rower.start()
#
#
# if __name__ == '__main__':
#     _fake_rower_test(0.5)
