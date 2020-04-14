"""Communication with usb rower head unit

Serial reader will continuously read from the serial port which connects with the rower's head unit,
whenever it gets a valid data message, it will parse it to status data fields, and updates the associated rower object.

The serial reader class has to be initialized with:
- A. Serial port information: which serial device should it talking to.
- B. Associated rower listener: when got data, update which rower object.

The serial_reader is configured to run in it's own thread, to prevent it from get blocked when the serial port stops
pushing data (happens often, when machine is idle).

To start the listening-parsing-updating, you have to call some_serial_reader_instance.start()

The recommended usage would be:
1. sr = serial_reader(...), init a new instance.
2. sr.open(), to open the serial port, you can handle the error here if the serial device is not connectible.
3. sr.start(), to open a new thread to continuously read from the serial port at background.

Once it's started, whenever a new message arrives, the associated rower object get updated.

Also a stop() is provided, to stop the reading and updating.
and a release() is provided, to release the serial device to system, and clean itself up.


# C??? , also = connect, show console message. other times, C1164
# T ? = tank??? the volume of water???
# L = level, 2,3,...
# V = version, V1161016
# H ? H000, heart rate maybe???
# R = reset.
# P??? P12, works

self.total_elapsed_time = incoming_data.get('total_elapsed_time', -1)
        self.total_distance_traveled = incoming_data.get('total_distance_traveled', -1)
        self.instantaneous_speed = incoming_data.get('instantaneous_speed', -1)

"""

import threading
import serial

from rower import Rower


class SerialReader:

    def __init__(self, outbound_rower, serial_device_address):
        # When got new data frame, update which rower.
        assert isinstance(outbound_rower, Rower)
        self.receiver = outbound_rower
        # Which TTY device are you going to read.   todo: auto detect, instead of hard code.
        self.serial_device_address = serial_device_address

    def start(self):
        self.worker_thread = threading.Thread(target=self._thread_worker)
        self.worker_thread.start()

    def close(self):
        pass
        # stop the thread, release the resource.

    def _thread_worker(self):
        """This method will run as a thread, to continuously read serial port and update rower object"""
        with serial.Serial(self.serial_device_address, timeout=1) as ser:
            # Connect,
            ser.write(b'C\n')
            # Reset
            ser.write(b'R\n')
            # continuously read the data
            while True:
                ser_bytes = ser.readline()
                if ser_bytes != '':
                    # got something
                    print('Got something from serial')
                    print(ser_bytes)
                    # parse incoming ser_bytes, return value should be a dict
                    result_dict = self._parse(ser_bytes)
                    # if result dict OK, update the receiver.
                    if result_dict is not None:
                        assert isinstance(result_dict, dict)
                        self._send(result_dict)
                else:
                    # EOF or timeout
                    print('No data, timeout.')

    @staticmethod
    def _parse(ser_bytes):
        if len(ser_bytes) == 31:
            # this is the rower's valid frame data, decode and return a dict.
            # get the raw data.

            # time
            total_minutes = int(ser_bytes[3:5], 10)
            total_seconds = int(ser_bytes[5:7], 10)

            # distance, in meter
            distance = int(ser_bytes[7:12], 10)

            # pace
            minutes_to_500m = int(ser_bytes[13:15], 10)
            seconds_to_500m = int(ser_bytes[15:17], 10)

            # spm
            spm = int(ser_bytes[17:20], 10)

            # power
            watt = int(ser_bytes[20:23], 10)

            # calorie per hour
            cal_per_hour = int(ser_bytes[23:27], 10)

            # level
            level = int(ser_bytes[27:29], 10)

            # print('time: '+str(total_minutes)+':'+str(total_seconds)+' distance: '+str(distance))
            # print('pace: '+str(minutes_to_500m)+':'+str(seconds_to_500m)+' spm: '+str(spm))
            # print('power: '+str(watt)+' cal/hr: '+str(cal_per_hour)+' level: '+str(level))

            # calculate to the standard fields.

            new_dict = {
                # in second
                'total_elapsed_time': total_minutes * 60 + total_seconds,
                # in meter
                'total_distance_traveled': distance,
                # in meter/second, calculate from 500m pace, float
                'instantaneous_speed': 500 / (minutes_to_500m * 60 + seconds_to_500m),
                # spm, stroke/minute, int
                'strokes_per_minute': spm,
                # power, in watts, int
                'instantaneous_power': watt,
                # caloric burn rate, in kCal/hour, int
                'calories_burn_rate': cal_per_hour,
                # resistance level, in percentage, float
                # this rower have 4 levels. 1/4 to 4/4
                'resistance_level': level/4
            }

            return new_dict

        else:
            # unexpected, not frame data.
            # todo: handle the commands here, result with leading characters for command, is the result.
            return None

    def _send(self, dict_to_send):
        assert isinstance(dict_to_send, dict)
        self.receiver.on_update_data(dict_to_send)
