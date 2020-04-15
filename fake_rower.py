'''Fake rower for testing

Simulate a "virtual rower", to test the ant+ part without actually plug a rower in.

'''
from serial_reader import BaseSerialReader
import time

class FakeRower(BaseSerialReader):
    """Fake Rower class

    Simulate a serial reader, Update the data once a second, send new data to Rower object.
    This class should be substitutable with a actual serial Reader.

    """
    def __init__(self, out_rower):
        super(FakeRower, self).__init__(outbound_rower=out_rower, serial_device_address='')
        self.spd = 2.5
        self.time = 0
        self.distance = 0
        self.power = 196
        self.spm = 31
        self.cal_rate = 159
        self.resistance = 0.5


    def _thread_worker(self):
        while True:
            result_dict = self.generate_fake_data()
            print(result_dict)
            self._send(result_dict)
            time.sleep(1)


    def generate_fake_data(self):
        new_dict = {
            # in second
            'total_elapsed_time': self.time,
            # in meter
            'total_distance_traveled': self.distance,
            # in meter/second, calculate from 500m pace, float
            'instantaneous_speed': self.spd,
            # spm, stroke/minute, int
            'strokes_per_minute': self.spm,
            # power, in watts, int
            'instantaneous_power': self.power,
            # caloric burn rate, in kCal/hour, int
            'calories_burn_rate': self.cal_rate,
            # resistance level, in percentage, float
            # this rower have 4 levels. 1/4 to 4/4
            'resistance_level': self.resistance
        }

        self.time += 1
        self.distance = int(self.distance+self.spd)

        return new_dict
