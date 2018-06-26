from .Picoquant import Picoquant
from .Intensity import Intensity
from .Limits import Limits
from . import calculate

class Info(object):

    def __init__(self, filename):
        self._filename = filename
        self._pq = Picoquant(self._filename)

    def get_filename(self):
        return(self._filename)

    def get_repetition_rate(self):
        try:
            self._repetition_rate
        except:
            if self._pq.mode() == 't3':
                self._repetition_rate = self._pq.repetition_rate()
            elif self._pq.mode() == 't2':
                self._repetition_rate = None

        return(self._repetition_rate)
    
    def set_repetition_rate(self, repetition_rate):
        self._repetition_rate = repetition_rate

    def get_resolution(self):
        return(self._pq.resolution())
    
    def get_mode(self):
        try:
            self._mode
        except:
            self._mode = self._pq.mode()

        return(self._mode)
    
    def set_mode(self, mode):
        self._mode = mode

    def get_integration_time(self):
        return(self._pq.integration_time())

    def get_channels(self):
        try:
            self._channels
        except:
            if self._pq.channels() == 2:
                self._channels = 2
            else:
                intensity = Intensity(calculate.intensity(self.filename,
                                      channels = 10, count_all=True))
                if self._mode == "t2":
                    self._channels = 0
                elif self._mode == "t3":
                    self._channels = 1

                for channel, counts in intensity:
                    if sum(counts):
                        self._channels += 1

        return(self._channels)

    def set_channels(self, channels):
        self._channels = channels
    
    def set_bin_width(self, bin_width):
        if self.get_mode() == 't2':
            self._bin_width = bin_width
        elif self.get_mode() == 't3':
            self._bin_width = int(bin_width*self.get_repetition_rate()/1E12)

    def get_bin_width(self):
        try:
            self._bin_width
        except:
            if self.get_mode() == 't2':
                self._bin_width = int(5E10)
            elif self.get_mode() == 't3':
                self._bin_width = int(self.get_repetition_rate()*0.05)

        return(int(self._bin_width))

    def set_threshold_max(self, threshold_max):
        if self.get_mode() == 't2':
            self._threshold_max = threshold_max * self.get_bin_width() * 1E-12
        elif self.get_mode() == 't3':
            self._threshold_max = threshold_max * self.get_bin_width() \
                                                / self.get_repetition_rate()

    def set_threshold_min(self, threshold_min):
        if self.get_mode() == 't2':
            self._threshold_min = threshold_min * self.get_bin_width() * 1E-12
        elif self.get_mode() == 't3':
            self._threshold_min = threshold_min * self.get_bin_width() \
                                                / self.get_repetition_rate()

    def get_threshold_max(self):
        try:
            self._threshold_max
        except:
            self._threshold_max = 1000000

        return(int(self._threshold_max))

    def get_threshold_min(self):
        try:
            self._threshold_min
        except:
            self._threshold_min = 0

        return(int(self._threshold_min))

    def set_order(self, order):
        self._order = order

    def get_order(self):
        try:
            self._order
        except:
            if self.get_mode() == 't2':
                self._order = 2
            elif self.get_mode() == 't3':
                self._order = 1

        return(self._order)

    def set_time_bins(self, time_bins):
        self._time_bins = time_bins

    def get_time_bins(self):
        try:
            self._time_bins
        except:
            if self.get_order() == 2:
                self._time_bins = Limits(-1000000,1000000,2000)
            elif self.get_order() == 1:
                self._time_bins = None

        return(self._time_bins)
