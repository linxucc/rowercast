"""Unittest for ant+ FE broadcasting"""
import unittest

from ant_rower import *


class DataPageTestGood(unittest.TestCase):
    """Test with the most common fields, which is reported by my rower"""

    def setUp(self):
        # the dict validity is guaranteed by the Rower class itself.
        # all the keys and value are already good.
        self.good_dict = {
            # in second
            'total_elapsed_time': 1255,
            # in meter
            'total_distance_traveled': 2789,
            # in meter/second, calculate from 500m pace, float
            'instantaneous_speed': 2.468,
            # spm, stroke/minute, int
            'strokes_per_minute': 32,
            # power, in watts, int
            'instantaneous_power': 152,
            # caloric burn rate, in kCal/hour, int
            'calories_burn_rate': 673,
            # resistance level, in percentage, float
            # this rower have 4 levels. 1/4 to 4/4
            'resistance_level': 0.10
        }

    def tearDown(self):
        self.good_dict = None

    def test_base_page(self):
        base_page = BaseDataPage()
        # to payload should return the same bytes.
        self.assertEqual(base_page.bytes, base_page.to_payload())

        # invalid values, should raise error.
        # length problems and range problems is tested here, for subclasses it's OK.

        # data length error.
        base_page.bytes = array.array('B', [0, 0, 0, 0, 0, 0, 0, 0, 0])
        with self.assertRaises(AssertionError):
            base_page._self_check()
        # data value not in range
        with self.assertRaises([AssertionError, OverflowError]):
            base_page.bytes = array.array('B', [12, 256, 0, 0, 0, 0, 0, 0])
            base_page._self_check()

    def test_page_16(self):
        page_16 = DataPage16(self.good_dict)

        page_bytes = page_16.to_payload()

        # page 16 is page 16
        self.assertEqual(page_bytes[0], 16)
        # todo: configurable
        # type = rower, capability is capability.
        self.assertEqual(page_bytes[1], 176)
        # time, rollover by 256, but in 0.25s, so rollover by 64s
        self.assertEqual(page_bytes[2], (1255 % 64) * 4)
        # distance, rollover by 256
        self.assertEqual(page_bytes[3], 2789 % 256)
        # spd, lsb = 2468 & 0xFF 
        self.assertEqual(page_bytes[4], (2468 & 0xFF))
        # spd, msb = 2468 & 0xFF00, then >> 8
        self.assertEqual(page_bytes[5], (2468 >> 8))
        # hr, 255, 0xFF = invalid.
        self.assertEqual(page_bytes[6], 255)
        # todo: configurable
        self.assertEqual(page_bytes[7], 38)

    def test_page_17(self):
        page_17 = DataPage17(self.good_dict)

        page_bytes = page_17.to_payload()

        # page 17 is page 17
        self.assertEqual(page_bytes[0], 17)
        self.assertEqual(page_bytes[1], 0xFF)
        self.assertEqual(page_bytes[2], 0xFF)
        # stroke length number is not used in this data, 0xFF = 255 = invalid.
        self.assertEqual(page_bytes[3], 0xFF)
        # incline in 4,5 should be invalid for a rower.
        self.assertEqual(page_bytes[4], 0x7F)
        self.assertEqual(page_bytes[5], 0xFF)
        # resistance, in 0.5% precision. 0.10 = 10% = 20*0.5%, should be 20
        self.assertEqual(page_bytes[6], 20)
        # status and capability. for now, fixed.
        self.assertEqual(page_bytes[7], 6)

    def test_page_18(self):
        page_18 = DataPage18(self.good_dict)

        page_bytes = page_18.to_payload()

        # page 18 is page 18
        self.assertEqual(page_bytes[0], 18)
        self.assertEqual(page_bytes[1], 0xFF)
        self.assertEqual(page_bytes[2], 0xFF)
        self.assertEqual(page_bytes[3], 0xFF)
        # only cal_rate in 4,5 is used,
        # cal rate lsb = 673 & 0xFF
        self.assertEqual(page_bytes[4], 673 & 0xFF)
        # cal rate msb = 673 >> 8
        self.assertEqual(page_bytes[5], 673 >> 8)
        # accumulated calories, could be OFF.
        self.assertEqual(page_bytes[6], 0x00)
        self.assertEqual(page_bytes[7], 6)

    def test_page_22(self):
        page_22 = DataPage22(self.good_dict)

        page_bytes = page_22.to_payload()

        # page 22 is page 22
        self.assertEqual(page_bytes[0], 22)
        self.assertEqual(page_bytes[1], 0xFF)
        self.assertEqual(page_bytes[2], 0xFF)
        self.assertEqual(page_bytes[3], 0)
        # spm
        self.assertEqual(page_bytes[4], 32)
        # power, in watts, integer. 0-65534 w
        # lsb, <256, should be itself
        self.assertEqual(page_bytes[5], 152)
        # msb, should be 0x00
        self.assertEqual(page_bytes[6], 0)
        self.assertEqual(page_bytes[7], 6)


if __name__ == '__main__':
    unittest.main()


class DataPageTestMinimum(unittest.TestCase):
    """Test with the minimum fields, with the required fields only."""

    def setUp(self):
        # the dict validity is guaranteed by the Rower class itself.
        # all the keys and value are already good.
        self.good_dict = {
            # in second
            'total_elapsed_time': 1255,
            # in meter
            'total_distance_traveled': 2789,
            # in meter/second, calculate from 500m pace, float
            'instantaneous_speed': 2.468,
            # resistance level, in percentage, float
            'resistance_level': 0.10
        }

    def tearDown(self):
        self.good_dict = None

    def test_page_16(self):
        page_16 = DataPage16(self.good_dict)

        page_bytes = page_16.to_payload()

        # page 16 is page 16
        self.assertEqual(page_bytes[0], 16)
        # todo: configurable
        # type = rower, capability is capability.
        self.assertEqual(page_bytes[1], 176)
        # time, rollover by 256, but in 0.25s, so rollover by 64s
        self.assertEqual(page_bytes[2], (1255 % 64) * 4)
        # distance, rollover by 256
        self.assertEqual(page_bytes[3], 2789 % 256)
        # spd, lsb = 2468 & 0xFF
        self.assertEqual(page_bytes[4], (2468 & 0xFF))
        # spd, msb = 2468 & 0xFF00, then >> 8
        self.assertEqual(page_bytes[5], (2468 >> 8))
        # hr, 255, 0xFF = invalid.
        self.assertEqual(page_bytes[6], 255)
        # todo: configurable
        self.assertEqual(page_bytes[7], 38)

    def test_page_17(self):
        page_17 = DataPage17(self.good_dict)

        page_bytes = page_17.to_payload()

        # page 17 is page 17
        self.assertEqual(page_bytes[0], 17)
        self.assertEqual(page_bytes[1], 0xFF)
        self.assertEqual(page_bytes[2], 0xFF)
        # stroke length number is not used in this data, 0xFF = 255 = invalid.
        self.assertEqual(page_bytes[3], 0xFF)
        # incline in 4,5 should be invalid for a rower.
        self.assertEqual(page_bytes[4], 0x7F)
        self.assertEqual(page_bytes[5], 0xFF)
        # only resistance is required on a rower by ant+ standard.
        # resistance, in 0.5% precision. 0.10 = 10% = 20*0.5%, should be 20
        self.assertEqual(page_bytes[6], 20)
        # status and capability. for now, fixed.
        self.assertEqual(page_bytes[7], 6)

    def test_page_18(self):
        page_18 = DataPage18(self.good_dict)

        page_bytes = page_18.to_payload()

        # page 18 is page 18
        self.assertEqual(page_bytes[0], 18)
        self.assertEqual(page_bytes[1], 0xFF)
        self.assertEqual(page_bytes[2], 0xFF)
        self.assertEqual(page_bytes[3], 0xFF)

        self.assertEqual(page_bytes[4], 0xFF)
        # cal rate msb = 673 >> 8
        self.assertEqual(page_bytes[5], 0xFF)
        # accumulated calories, could be OFF.
        self.assertEqual(page_bytes[6], 0x00)
        self.assertEqual(page_bytes[7], 6)

    def test_page_22(self):
        page_22 = DataPage22(self.good_dict)

        page_bytes = page_22.to_payload()

        # page 22 is page 22
        self.assertEqual(page_bytes[0], 22)
        self.assertEqual(page_bytes[1], 0xFF)
        self.assertEqual(page_bytes[2], 0xFF)
        self.assertEqual(page_bytes[3], 0)
        # spm
        self.assertEqual(page_bytes[4], 0xFF)
        # power, in watts, integer. 0-65534 w
        # lsb, <256, should be itself
        self.assertEqual(page_bytes[5], 0xFF)
        # msb, should be 0x00
        self.assertEqual(page_bytes[6], 0xFF)
        self.assertEqual(page_bytes[7], 6)
