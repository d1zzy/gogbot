import bisect
import time


class Event:
    """Base event class. Associate timestamped events with some payload."""
    def __init__(self, data):
        self.timestamp = time.time()
        self.data = data

    def __repr__(self):
        return 'Event(timestamp=%r, data=%r)' % (self.timestamp, self.data)

    def __lt__(self, value):
        """Provide comparison to establish strict timestamp based order."""
        return self.timestamp < value.timestamp


class Queue:
    """Ordered queue of events issued in the past "max_age" seconds."""
    def __init__(self, max_age):
        self._max_age = max_age
        self._events = []
        # Create a map that associates an event's payload with the events that
        # have that payload.
        self._idx_data = {}

    def _RemoveExpiredEvents(self):
        now = time.time()
        to_remove = []
        for ev in self._events:
            if ev.timestamp + self._max_age >= now:
                break
            to_remove.append(ev)

        for ev in to_remove:
            self.RemoveEvent(ev)

    def RecordEvent(self, ev):
        # Keep the event queue ordered by timestamp. Usually this insert
        # happens at the end since events will tend to be added in chronological
        # order.
        bisect.insort_right(self._events, ev)
        # Keep events ordered by timestamp in the payload based map.
        bisect.insort_right(self._idx_data.setdefault(ev.data, []), ev)

    def RemoveEvent(self, ev):
        # Use a linear search because events are generally removed from the
        # end of the queue by _RemoveExpiredEvents.
        for idx, candidate in enumerate(self._events):
            if candidate is ev:
                self._events.pop(idx)
                break
        for idx, candidate in enumerate(self._idx_data.get(ev.data, [])):
            if candidate is ev:
                self._idx_data[ev.data].pop(idx)
                break

    def CountAll(self):
        return len(self._events)

    def CountByData(self, data):
        self._RemoveExpiredEvents()
        return len(self._idx_data.get(data, []))
