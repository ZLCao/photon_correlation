from .Picoquant import Picoquant
from .Intensity import Intensity
from . import calculate

class Info(object):

    def __init__(self, filename):
        self.filename = filename

    def repetition_rate(self):
        try:
            self._repetition
        except:
            self._repetition = Picoquant(self.filename).repetition_rate()

        return(self._repetition)

    def resolution(self):
        return(Picoquant(self.filename).resolution())

    def mode(self):
        try:
            self._mode
        except:
            self._mode = Picoquant(self.filename).mode()

        return(self._mode)

    def integration_time(self):
        return(Picoquant(self.filename).integration_time())

    def channels(self):
        try:
            self._channels
        except:
            intensity = Intensity(calculate.intensity(
                                  self.filename, count_all=True))
            if self._mode == "t2":
                self._channels = 0
            elif self._mode == "t3":
                self._channels = 1

            for channel, counts in intensity:
                if sum(counts):
                    self._channels += 1

        return(self._channels)
