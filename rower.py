class Frame:
    """Actual Rower data of a moment, for read-consistency

    While updating the Rower object, a potential read may lead to read in-consistency, which means reader may get
    part of the new data and part of the old data.

    for example:

        while a read has already read total time, now he is reading distance traveled, an serial update just come
        up, which updates all the data to a newer version, in this case, the returned value of read() is a
        combination of old total time and new distance + instant speed.

        when this message got broadcast, the receiver end may get confused, some calculation may went wrong,
        especially in cases calculations are based on event count, or some fields could roll-over.

    To prevent this situation from happening, we have to make it read-consistent.
    For simplicity, we use a create & swap mechanism, upon each update, a new frame got created,
    when everything has been already written, a change to the current_frame happens.

    So whenever a read() happens, the reader always get a complete data with full integrity, so no part-new-part-old
    situations could happen.

    ** Why use this instead of directly hook up a dict? in case caller doesn't provide correct dict.
    This Frame class makes the output dict clean and reliable.

    """

    def __init__(self, incoming_data: dict):
        # try to parse data from incoming dict, if there's no corresponding key, it's a -1 invalid..
        # in seconds
        self.total_elapsed_time = incoming_data.get('total_elapsed_time', -1)
        # in meter
        self.total_distance_traveled = incoming_data.get('total_distance_traveled', -1)
        # in meters/second
        self.instantaneous_speed = incoming_data.get('instantaneous_speed', -1)

    def print_current_info(self):
        print("total time: " + str(self.total_elapsed_time)
              + " distance: " + str(self.total_distance_traveled)
              + " instant speed: " + str(self.instantaneous_speed))

    def to_dict(self):
        return vars(self)


class Rower:
    """A Data Model representing a generic rower.

    Containing all the data fields that a rower is supposed to have.
    A temporary place to hold current rower state in the runtime.

    Data updated by serialReaders, consumed by signal senders (ant+, BLE, web).

    on_update_data(dict) is called by data providers to update data.
    get_current_frame() ==> dict, is called when data consumers want to pullout current data.

    """

    def __init__(self):
        # current frame is what "current" data of rower.
        init_data = {
            'total_elapsed_time': 0,
            'total_distance_traveled': 0,
            'instantaneous_speed': 0
        }
        self._current_frame = Frame(init_data)

    def on_update_data(self, incoming_data: dict):
        # write a new Frame of new data
        new_frame = Frame(incoming_data)
        # change current frame to this new frame, last frame is now discarded, and should be garbage collected.
        # this action is much more 'atomic', so read consistency is conserved.
        self._current_frame = new_frame
        print(self._current_frame.to_dict())

    def get_current_frame(self) -> dict:
        # return current frame
        # even if where current frame points changes, reader still get reference to previous frame, consistency ensured.
        return self._current_frame.to_dict()

    def print_current_frame(self):
        assert isinstance(self._current_frame, Frame)
        self._current_frame.print_current_info()
