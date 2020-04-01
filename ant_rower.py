import array
import threading

from ant.easy.node import Node
from ant.easy.channel import Channel

from rower import Rower


class BaseDataPage:
    def __init__(self):
        self.bytes = array.array('B', [0, 0, 0, 0, 0, 0, 0, 0])

    def to_payload(self):
        return self.bytes

    def _self_check(self):
        for i in [1, 7]:
            assert 0 <= self.bytes[i] <= 255


class DataPage16(BaseDataPage):
    # class attributes, shared across instances.
    # for accumulated values to be calculated correctly, last time value is needed.
    last_total_elapsed_time = 0
    last_distance_traveled = 0

    def __init__(self, incoming_rower_dict):
        super(DataPage16, self).__init__()
        assert isinstance(incoming_rower_dict, dict)

        # this is a page 16
        self.bytes[0] = 16

        # construct data page 16 from incoming dict.

        # Byte 1
        # bit 0-4 is FE Type, rower is 22; bit 5-7 is 0.
        # so it's 22 left shifted by 3 bit, so it's 22*2*2*2 = 176
        equipment_type_bit_field = 176

        # Byte 2
        # elapsed_time_increment is a accumulated field, the unit is 0.25s.
        elapsed_time_increment = int((incoming_rower_dict['total_elapsed_time']
                                      - DataPage16.last_total_elapsed_time) / 0.25)
        if elapsed_time_increment > 255:
            # if ant+ rower is started later than the actual rower, the total_elapsed_time may already be very big,
            # we just ignore the work before, and assume now as the start.
            # the first time a 255 (64s) will be sent, above then it will be normal.
            # you can't avoid the bad that in this situation, you display device (watch) will not have the same
            # total time as your head unit on the rower.
            # so make sure the program is started before actual rowing.
            elapsed_time_increment = 255
        # update last value for next time, use tmp copy to prevent the possibility the value could change meanwhile.
        DataPage16.last_total_elapsed_time = incoming_rower_dict['total_elapsed_time']

        # Byte 3
        # unit is 1 meter.
        distance_traveled_increment = int(incoming_rower_dict['total_distance_traveled']
                                          - DataPage16.last_distance_traveled)
        DataPage16.last_distance_traveled = incoming_rower_dict['total_distance_traveled']

        # Byte 4 & 5,
        # Combined to represent instant speed.
        # tmp_current_instant_speed = self.instantaneous_speed
        # todo: implement this. Current disable it first.
        instant_speed_lsb = 255
        instant_speed_msb = 255

        # Byte 6
        # HR, we don't use it.
        hr = 255

        # Byte 7
        # Capabilities Bit Field + RE State Bit Field
        # 00 (no HR) +  1 (distance enabled) + 0 (real speed) + 011 (FE in_use state) + 0
        # 00100110 = 38
        # todo: make them configurable. for now hard code.
        capability_and_fe_state = 38

        # set the bytes accordingly.
        self.bytes[1] = equipment_type_bit_field
        self.bytes[2] = elapsed_time_increment
        self.bytes[3] = distance_traveled_increment
        self.bytes[4] = instant_speed_lsb
        self.bytes[5] = instant_speed_msb
        self.bytes[6] = hr
        self.bytes[7] = capability_and_fe_state

        # make sure it's a data page 16
        assert self.bytes[0] == 16
        self._self_check()


class DataPage17(BaseDataPage):
    """General settings page"""

    def __init__(self, incoming_rower_dict):
        super(DataPage17, self).__init__()
        assert isinstance(incoming_rower_dict, dict)

        # resistance level
        resistance_level = incoming_rower_dict.get('resistance_level', None)
        if resistance_level is not None:
            # unit is 0.5%
            resistance_level_number = int(resistance_level / 0.005)
            assert 0 < resistance_level_number <= 200
        else:
            # if no resistance data, it's a 100%, so 200.
            resistance_level_number = 200

        # assume stroke length in meters
        stroke_length = incoming_rower_dict.get('stroke_length', None)
        if stroke_length is not None:
            stroke_length_number = int(stroke_length / 0.01)
            assert 0 <= stroke_length_number <= 254
        else:
            # 0xFF indicates it's invalid on this rower.
            stroke_length_number = 255

        # set the bytes
        self.bytes[0] = 17
        self.bytes[1] = 255
        self.bytes[2] = 255
        self.bytes[3] = stroke_length_number
        self.bytes[4] = 0x7F
        self.bytes[5] = 0xFF
        self.bytes[6] = resistance_level_number
        self.bytes[7] = 6  # 0x0, 0x6=in use. # todo: configurable.

        assert self.bytes[0] == 17
        self._self_check()


class DataPage18(BaseDataPage):
    """General FE Metabolic Data"""

    def __init__(self, incoming_rower_dict):
        super(DataPage18, self).__init__()
        assert isinstance(incoming_rower_dict, dict)

        # caloric burn rate
        cal_per_hour = incoming_rower_dict.get('calories_burn_rate', None)
        if cal_per_hour is not None:
            # ant+ FE use unit of 0.1kCal/hr
            cal_rate_number = cal_per_hour / 0.1
            assert 0 <= cal_rate_number <= 65534
        else:
            cal_rate_number = 65535

        # transfer to LSB, MSB
        cal_rate_lsb = cal_rate_number & 0x00FF
        cal_rate_msb = (cal_rate_number & 0xFF00) >> 8

        # set the bytes
        self.bytes[0] = 18
        self.bytes[1] = 0xFF
        self.bytes[2] = 0xFF
        self.bytes[3] = 0xFF
        self.bytes[4] = cal_rate_lsb
        self.bytes[5] = cal_rate_msb
        self.bytes[6] = 0x00  # accumulated calories, not available.
        self.bytes[7] = 6  # 0x0, 0x6, in-use, todo: configurable.

        assert self.bytes[0] == 18
        self._self_check()


class DataPage22(BaseDataPage):
    """Specific Rower Data"""

    def __init__(self, incoming_rower_dict):
        super(DataPage22, self).__init__()
        assert isinstance(incoming_rower_dict, dict)

        # get the spm
        spm = incoming_rower_dict.get('strokes_per_minute', None)
        if spm is None:
            spm = 0xFF  # 0xFF indicates spm is not available
        assert 0 <= spm <= 255

        # get the power
        power = incoming_rower_dict.get('instantaneous_power', None)
        if power is None:
            power = 65535  # 0xFF = invalid.
        assert 0 <= power <= 65535
        power_lsb = power & 0x00FF
        power_msb = (power & 0xFF00) >> 8

        # set the bits
        self.bytes[0] = 22
        self.bytes[1] = 255
        self.bytes[2] = 255
        self.bytes[3] = 0  # my case stroke count is not available.
        self.bytes[4] = spm
        self.bytes[5] = power_lsb
        self.bytes[6] = power_msb
        self.bytes[7] = 6  # 0x0, 0x6, in use. todo: configurable

        assert self.bytes[0] == 22
        self._self_check()


class DataPage80(BaseDataPage):
    """Common Data Page 80: Manufacturer’s Information

    Supposed to be a singleton to AntRower class, information is mainly fixed.

    """

    def __init__(self):
        super(DataPage80, self).__init__()

        # this is a data page 80
        self.bytes[0] = 80
        # byte 1,2 reserved to 0xFF
        self.bytes[1] = 255
        self.bytes[2] = 255

        # Byte 3, HW Revision, set to 0x0A or whatever.
        hw_revision = 10

        # byte 4,5: Manufacturer ID LSB, Manufacturer ID MSB
        # use developer ID, 0x00FF
        manufacturer_id_lsb = 255  # 0xFF
        manufacturer_id_msb = 0  # 0x00

        # byte 6,7: Model Number LSB, MSB.
        # use whatever, here use 1, 0x0001
        model_number_lsb = 1  # 0x01
        model_number_msb = 0  # 0x00

        # set the bytes accordingly.
        self.bytes[3] = hw_revision
        self.bytes[4] = manufacturer_id_lsb
        self.bytes[5] = manufacturer_id_msb
        self.bytes[6] = model_number_lsb
        self.bytes[7] = model_number_msb

        # make sure it's page 80
        assert self.bytes[0] == 80
        self._self_check()


class DataPage81(BaseDataPage):
    """Common Data Page 81: Product Information

    Supposed to be a singleton to AntRower class, information is mainly fixed.

    """

    def __init__(self):
        super(DataPage81, self).__init__()

        # this is a data page 81
        self.bytes[0] = 81
        # byte 1 reserved to 0xFF
        self.bytes[1] = 255

        # byte 2, Supplemental SW Revision (Invalid = 0xFF)
        supplemental_sw_revision = 255

        # byte 3, SW Revision (Main), SW version defined by manufacturer if byte 2 is set to 0xFF.
        # we use version 01
        sw_revision = 1

        # byte 4-7
        # Serial Number. The lowest 32 bits of the serial number.
        # Value 0xFFFFFFFF to be used for devices without serial numbers
        # we use 0xFFFFFFFF, low_1 means 1st LSB, low_2 means 2nd LSB, ...
        sn_low_1 = 255
        sn_low_2 = 255
        sn_low_3 = 255
        sn_low_4 = 255

        # set the bytes accordingly.
        self.bytes[2] = supplemental_sw_revision
        self.bytes[3] = sw_revision
        self.bytes[4] = sn_low_1
        self.bytes[5] = sn_low_2
        self.bytes[6] = sn_low_3
        self.bytes[7] = sn_low_4

        # make sure it's page 81
        assert self.bytes[0] == 81
        self._self_check()


class AntRower:
    """Ant+ FE Rower signal broadcaster class

    Start an Ant+ FE channel to broadcast the status of the source "Rower".

    """

    def __init__(self, source: Rower):
        # only take one parameter, source.
        # source is a object represents a rower, best to be an instance of Rower,
        # it should have a method of get_current_frame(), which returns a K-V dict, containing the rower info.
        # this method is called whenever the current rower data is needed, mostly, in a TX event to send out data.
        self.source = source

        # channel configurations
        self.channel_type = Channel.Type.BIDIRECTIONAL_TRANSMIT  # Master TX
        self.network_key = [0xb9, 0xa5, 0x21, 0xfb, 0xbd, 0x72, 0xc3, 0x45]  # Ant+ key
        self.RF_frequency = 57  # Ant+ frequency.
        self.transmission_type = 5  # MSN = 0x0, LSN = 0x5, detail see ant+ device profile document.
        self.device_type = 17  # Ant+ FE
        self.device_number = 33333  # Device number could be whatever between 1~65535. Change if you need.
        self.channel_period = 8192  # 4hz, as device profile requires.

        # openant radio objects.
        self.node = None  # later, when opened, node will be a instance of Node.
        self.channel = None  # later, when opened, will be the assigned channel object on the node.

        # outbound message count
        # used to implement specific transmission pattern, will be rollovered according to the specific pattern.
        # transmission pattern is implemented in function _get_next_page(), for detail check there.
        self.message_count = 1
        self.transmission_pattern = 'a'  # 1=a, 2=b, 3=c, 4=d, see Ant+ FE device profile page 24 of 74.
        self.transmission_pattern_func_dict = {
            'a': self._get_next_page_transmission_pattern_a,
            'b': self._get_next_page_transmission_pattern_b,
            'c': self._get_next_page_transmission_pattern_c,
            'd': self._get_next_page_transmission_pattern_d
        }
        self.transmission_pattern_d_internal_count = 1

        # singleton, fixed data pages, 80 and 81
        self.page_80 = DataPage80()
        self.page_81 = DataPage81()

    def on_tx_event(self):
        # data = array.array('B', [1, 255, 133, 128, 8, 0, 128, 0])
        page_to_send = self._get_next_page()
        data_payload = page_to_send.to_payload()  # get new data payload to sent at this TX event.
        # call channel's send_broadcast_data to set the TX buffer to new data.
        self.channel.send_broadcast_data(data_payload)
        print("send TX")

    def _open_and_start(self):
        """Open ant+ channel, if no error, start broadcast immediately"""

        # todo: add the try, catch, maybe Node not available, or network key error, or channel can't acquire

        # initialize the ant device, a node represent an ant USB device.
        self.node = Node()
        # set network key at net#0, only net#0 is used.
        self.node.set_network_key(0x00, self.network_key)

        # try get a new TX channel
        self.channel = self.node.new_channel(Channel.Type.BIDIRECTIONAL_TRANSMIT)
        # set the callback function for TX tick, each TX tick, this function will be called.
        self.channel.on_TX_event = self.on_tx_event

        # set the channel configurations
        self.channel.set_period(self.channel_period)
        self.channel.set_rf_freq(self.RF_frequency)
        # channel id is defined as <device num, device type, transmission type>
        self.channel.set_id(self.device_number, self.device_type, self.transmission_type)

        # try open channel,
        # once opened, the channel could be found by other devices, but No data sending yet.
        try:
            self.channel.open()
            # start the message loop on the ant device.
            # once started, the messages will be dispatched to callback functions of each channel.
            self.node.start()
        finally:
            self.node.stop()

    def start(self):
        """Start the broadcast event loop, from now on, each TX tick, send new broadcast"""
        ant_thread = threading.Thread(target=self._open_and_start())
        ant_thread.start()
        # this ensures the function is returned immediately to main thread, not blocking other lines in caller.

    def close(self):
        # todo: cleaning things up.
        pass

    # Transmission pattern handling

    def _get_next_page(self) -> BaseDataPage:
        """Implemented the suggested transmission patterns illustrated in Ant+ FE device profile.

        This function will return the next new page which should be sent out,
        it handles when and what here, according the message count and the specific pattern.

        """
        assert 0 < self.message_count < 133

        if self.message_count == 65 or self.message_count == 66:
            # send page 80
            next_page = self.page_80
        elif self.message_count == 131 or self.message_count == 132:
            # send page 81
            next_page = self.page_81
        else:
            # send data page according to transmission type
            # use dict in a way of switch statement, call different functions of different transmission type.
            next_page = self.transmission_pattern_func_dict[self.transmission_pattern]()

        # roll-over to 1 if msg count reaches 132
        if self.message_count == 132:
            self.message_count = 1

        return next_page

    def _get_next_page_transmission_pattern_a(self):
        """Transmission pattern A

        Only send page 16, the minimum requirement.

        :return: data payload of page 16.
        """
        # construct a data page 16 from current rower data of source Rower object.
        return DataPage16(self.source.get_current_frame())

    def _get_next_page_transmission_pattern_b(self):
        """Transmission pattern B

        [16 16 X X ...(64)...] (65)80 (66)80 [(67)16 16 X X ....(130)] (131)81 (132)81

        Mod left part directly, mode right part with minus 2.

        """
        if self.message_count <= 64:
            # left half
            # 1-64, directly mod 4 will be fine, remainder is the sequence.
            # 1 % 4 = 1, 2%4 = 2, 3%4 = 3, 4%4 =0, 5%4 = 1, ..., 8%4 = 0.
            if self.message_count % 4 == 1 or self.message_count % 4 == 2:
                return DataPage16(self.source.get_current_frame())
            else:
                # could only be 3, 0
                return DataPage22(self.source.get_current_frame())
        elif self.message_count >= 67:
            # right half, -2 before mod.
            if ((self.message_count - 2) % 4 == 1) or ((self.message_count - 2) % 4 == 2):
                return DataPage16(self.source.get_current_frame())
            else:
                # could only be 3, 0
                return DataPage22(self.source.get_current_frame())

    def _get_next_page_transmission_pattern_c(self):
        """Transmission pattern C

        Note that the illustrated pattern in the document is
        first 64 message are          16 16 X 17 16 16 18 X
        but second 64 messages are    16 16 17 X 16 16 X 18

        Don't know why, but better follow.

        simply look into message count, see which patter should used.

        mod by 8 (right part -2 first), then know which page to go.

        """

        if self.message_count <= 64:
            # left half
            # 1-64, directly mod 8 will be fine, remainder is the sequence.
            msg_count_mod_8 = self.message_count % 8
            assert 0 <= msg_count_mod_8 < 8

            if msg_count_mod_8 == 1 or msg_count_mod_8 == 2:
                return DataPage16(self.source.get_current_frame())
            elif msg_count_mod_8 == 3:
                return DataPage22(self.source.get_current_frame())
            elif msg_count_mod_8 == 4:
                return DataPage17(self.source.get_current_frame())
            elif msg_count_mod_8 == 5 or msg_count_mod_8 == 6:
                return DataPage16(self.source.get_current_frame())
            elif msg_count_mod_8 == 7:
                return DataPage18(self.source.get_current_frame())
            else:
                # could only be 0, so the 8th
                return DataPage22(self.source.get_current_frame())
        elif self.message_count >= 67:
            # right half, -2 before mod.
            msg_count_mod_8 = (self.message_count - 2) % 8
            assert 0 <= msg_count_mod_8 < 8

            if msg_count_mod_8 == 1 or msg_count_mod_8 == 2:
                return DataPage16(self.source.get_current_frame())
            elif msg_count_mod_8 == 3:
                return DataPage17(self.source.get_current_frame())
            elif msg_count_mod_8 == 4:
                return DataPage22(self.source.get_current_frame())
            elif msg_count_mod_8 == 5 or msg_count_mod_8 == 6:
                return DataPage16(self.source.get_current_frame())
            elif msg_count_mod_8 == 7:
                return DataPage22(self.source.get_current_frame())
            else:
                # could only be 0, so the 8th
                return DataPage18(self.source.get_current_frame())

    def _get_next_page_transmission_pattern_d(self):
        """Transmission pattern D

        This pattern is a little bit different from others, pattern repeat in 20 messages, ignore others.

        16 X X X X 16 X X X 18 16 X X X X 16 X X X 17

        1,6,11,16 is page 16
        10, is page 18
        20, page 17
        others, page 22

        this pattern it self repeats, whenever it in time slot for 64 pages of data, after 80 and 81 interrupts,
        it resumes, it's independent from the 64-2-64-2 134 messages pattern.

        So we use a function property to maintain its own pattern counts.
        This property roll-over every 20 data messages.

        """

        assert 0 < self.transmission_pattern_d_internal_count <= 20

        if (self.transmission_pattern_d_internal_count == 1
                or self.transmission_pattern_d_internal_count == 6
                or self.transmission_pattern_d_internal_count == 11
                or self.transmission_pattern_d_internal_count == 16):
            return DataPage16(self.source.get_current_frame())
        elif self.transmission_pattern_d_internal_count == 10:
            return DataPage18(self.source.get_current_frame())
        elif self.transmission_pattern_d_internal_count == 20:
            # roll-over to 1
            self.transmission_pattern_d_internal_count = 1
            # return page 17 for current time
            return DataPage17(self.source.get_current_frame())
        else:
            # should be all page 22.
            return DataPage22(self.source.get_current_frame())

    # others implemented later.
