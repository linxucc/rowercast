class IncomingRowerDictInvalidKeyError(Exception):
    pass


class IncomingRowerDictMissingKeyError(Exception):
    pass


class IncomingRowerDictInvalidValueError(Exception):
    pass


class IncomingRowerDictDuplicateError(Exception):
    pass


class Rower:
    """A Data Model representing a generic rower.

    Containing all the data fields that a rower is supposed to have.
    Provide a unified interface for different rower data source and data consumers.

    In this case, data source is the serialReader class, consumer is the signal senders/readers (ant+, BLE, web).

    All the rower data is stored in a dict, upon each update, a new dict will be created and replace the old one,
    so for the data reader/consumers, the read-consistency is assured, all the fields will match.

    Data provider should call: on_update_data()
    Data consumer should call: get_current_frame()

    """

    def __init__(self):
        # fields definitions, keys that are not recognized will be rejected.
        self.all_valid_keys = [
            'total_elapsed_time',   # total time
            'total_distance_traveled',  # total distance
            'instantaneous_speed',  # current speed
            'strokes_per_minute',   # spm
            'instantaneous_power',  # power
            'calories_burn_rate',   # kCal/hr
            'resistance_level'      # resistance, x%
        ]

        # required fields.
        self.mandatory_keys = [
            'total_elapsed_time',
            'total_distance_traveled',
            'instantaneous_speed'
        ]

        # keys that should have integer value.
        self.integer_keys = [
            'total_elapsed_time',
            'total_distance_traveled',
            'strokes_per_minute',
            'instantaneous_power'
        ]

        # for now, no negative keys.
        self.negative_keys = []
        # not implemented, some keys should only add 0 or positive value, like distance.
        self.incremental_keys = []

        # set initial data frame. current frame is what "current" data of rower.
        init_data = {
            'total_elapsed_time': 0,
            'total_distance_traveled': 0,
            'instantaneous_speed': 0,
            'strokes_per_minute': 0,
            'instantaneous_power': 0,
            'calories_burn_rate': 0,
            'resistance_level': 0
        }
        # Current frame is a dict that stores current rower's data.
        # Upon each update, the old frame should be replaced by the new frame, not modified, for read-consistency.
        self._current_frame = init_data
        assert isinstance(self._current_frame, dict)

    def on_update_data(self, new_frame: dict):
        # write a new Frame of new data
        # change current frame to this new frame, last frame is now discarded, and should be garbage collected.
        # this action is much more 'atomic', so read consistency is conserved.
        if new_frame is self._current_frame:
            raise IncomingRowerDictDuplicateError("Incoming frame is the same dict object, each time you have to "
                                                  "pass a new dict object to have the read-consistency.")
        # Invalid data frame should be rejected, and notify the caller.
        self._check_dict_validity(new_frame)
        self._current_frame = new_frame

    def get_current_frame(self) -> dict:
        # return current frame
        # even if where current frame points changes, reader still get reference to previous frame, consistency ensured.
        print(self._current_frame)
        return self._current_frame

    def print_current_frame(self):
        print(self._current_frame)

    def _check_dict_validity(self, incoming_dict: dict):
        """Make sure the incoming dict is a valid rower data frame, so the out coming data is consistent.

            Check the validity of the incoming dict fields, make sure all the required fields exists, and the value
            of each key is in the corresponded data type or format. So the data consumers is guaranteed that the
            out coming data is in a known format.

            Raises: IncomingRowerDictInvalidError, indicates that the incoming dict did not pass the validity check.

        """
        # check key error
        # check value error

        for key in incoming_dict.keys():
            # check invalid key.
            if key not in self.all_valid_keys:
                raise IncomingRowerDictInvalidKeyError("Incoming rower data dict has unknown key, data rejected. "
                                                       + key)

            # check value if key is valid.
            value = incoming_dict.get(key, None)
            if value is None:
                if key in self.mandatory_keys:
                    # Mandatory keys should have value.
                    raise IncomingRowerDictInvalidKeyError("Incoming rower data dict has wrong key, data rejected. "
                                                           + key)
            else:
                # Got the value, check the value.
                if key in self.integer_keys:
                    # integer keys should be integer
                    if int(value) != value:
                        raise IncomingRowerDictInvalidValueError("Incoming rower data dict has wrong key, "
                                                                 "data rejected. " + key + ":" + str(value))
                if key not in self.negative_keys:
                    # non-negative keys should be non-negative
                    if value < 0:
                        raise IncomingRowerDictInvalidValueError("Incoming rower data dict has wrong key, "
                                                                 "data rejected. " + key + ":" + str(value))

        # make sure mandatory keys exists.
        for m_key in self.mandatory_keys:
            if m_key not in incoming_dict.keys():
                raise IncomingRowerDictMissingKeyError('Incoming rower data dict has insufficient keys, '
                                                       'mandatory keys not found. '+m_key)
