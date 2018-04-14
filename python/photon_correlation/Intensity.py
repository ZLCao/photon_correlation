import os
import bz2
import csv
import collections
import bisect
import statistics

import numpy
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

from .Blinking import *
from .util import *

def mode_error(mode):
    raise(KeyError("Unknown mode: {}".format(mode)))

class Intensity(object):
    """
    Implements the tools necessary for analyzing intensity data.
    """
    def __init__(self, stream_in=None, filename=None, mode=None):
        self.times = list()
        self.counts = dict()

        if stream_in is not None:
            self.from_stream(stream_in)
        elif filename is not None:
            self.from_file(filename)

        if mode is not None:
            self.mode = mode
        else:
            if sum(self[0]):
                self.mode = "t2"
            else:
                self.mode = "t3"

    def __getitem__(self, channel):
        return(self.counts[channel])

    def __setitem__(self, channel, value):
        self.counts[channel] = value

    def __delitem__(self, channel):
        del(self.counts[channel])

    def __iter__(self):
        for channel in sorted(self.counts.keys()):
            yield(channel, self[channel])

    def __len__(self):
        return(len(self.counts.keys()))

    @property
    def time_bins(self):
        return(list(map(statistics.mean, self.times)))

    def max(self):
        my_max = 0
        
        for curve, counts in self:
            if max(counts) > my_max:
                my_max = max(counts)

        return(my_max)

    def dt(self):
        return(self.times[1][1] - self.times[1][0])

    def channels(self):
        return(len(self.counts.keys()))

    def from_stream(self, stream_in):
        raw_counts = list()

        for line in csv.reader(stream_in):
            bin_left = int(line[0])
            bin_right = int(line[1])

            counts = tuple(map(int, line[2:]))

            self.times.append((bin_left, bin_right))

            raw_counts.append(counts)

        for channel, counts in enumerate(numpy.transpose(raw_counts)):
            self[channel] = counts
    
        return(self)

    def from_file(self, filename):
        """
        Read data from the file and return an intensity object wtih
        that data.
        """
        if not os.path.exists(filename):
            bz2_name = "{}.bz2".format(filename)
            if os.path.exists(bz2_name):
                filename = bz2_name
                
        if filename.endswith("bz2"): 
            open_f = lambda x: bz2.open(x, "rt")
        else:
            open_f = open
        with open_f(filename) as stream_in:
            return(self.from_stream(stream_in))

        return(self)

    def stream(self):
        channels = list(sorted(self.counts.keys()))

        for index, time_bin in enumerate(self.times):
            yield(index, tuple(map(lambda x: x[index],
                                   map(lambda x: self[x], channels))))

    def time_unit(self):
        if self.mode == "t2":
            return("s")
        elif self.mode == "t3":
            return("pulse")

    def normalized(self):
        """
        Return the counts, normalized to pulse or time as necessary.
        """
        intensity = Intensity(mode=self.mode)
        
        if self.mode == "t2":
            time_factor = 1e-12
            # for index, time in enumerate(numpy.array(self.times)*1e-12):
                # intensity.times.append(tuple(time))

            intensity.times = list(map(lambda x: (x[0] * time_factor,
                                       x[1] * time_factor), self.times))

        elif self.mode == "t3":
            intensity.times = self.times

        norm = lambda t, c: float(c)/(t[1]-t[0])

        for channel, counts in self:
            intensity[channel] = list(map(norm, intensity.times, counts))

        return(intensity)

    def add_intensity_axes(self, ax):
        """
        Add the lifetime information to the specified set of axes.
        """
        times = list(map(lambda x: x[0], self.times))
        
        if len(self) == 1:
            ax.plot(times, self[0])
        else:

            for channel, counts in self:
                if max(counts):
                    ax.plot(times, counts, label=str(channel))

            ax.legend()

        ax.set_xlim((times[0], times[-1]))
        ax.set_xlabel("Time/{}".format(self.time_unit()))
        ax.set_ylabel("Intensity/(count/{})".format(self.time_unit()))

    def make_figure(self):
        fig = plt.figure()
        spec = gridspec.GridSpec(ncols=4, nrows=1)
        ax_intensity = fig.add_subplot(spec[0, :-1])
        ax_histogram = fig.add_subplot(spec[0, -1])
        self.add_intensity_axes(ax_intensity)
        self.add_histogram_axes(ax=ax_histogram)
        fig.tight_layout()
        return(fig)
        
    def n_channels(self):
        if isinstance(self.counts[0], collections.Iterable):
            return(len(self.counts[0]))
        else:
            return(1)

    def mean(self):
        """
        Return the counts across all channels,
        """
        return(self.summed()[0]/float(self.channels()))

    def summed(self):
        total = None
        
        for channel, counts in self:
            if total is None:
                total = numpy.array(counts)
            else:
                total += counts

        intensity = Intensity(mode=self.mode)
        intensity.times = self.times
        intensity[0] = total
        
        return(intensity)
    
    def histogram(self, bins=200, summed=True):
        """
        Produce a histogram of intensities found in the intensity trace.
        """
        if summed:
            if len(self) > 1:
                counts = self.summed()[0]
            else:
                counts = self[0]

            return(numpy.histogram(counts, bins=bins))
        else:
            hists = list()
            
            for channel, counts in self.normalized():
                hists.append((channel, numpy.histogram(counts, bins=bins)))

            return(hists)
            
    def add_histogram_axes(self, ax, bins=200):

        counts, bins = self.histogram(bins=bins)

        ax.barh(bins[:-1], counts, height=statistics.mean(numpy.diff(bins)))
        
        ax.set_xlabel("Occurences")
        ax.yaxis.set_ticks_position("right")
        # ax.yaxis.set_ticklabels([])
        # ax.set_ylabel("Intensity/(counts/{})".format(self.time_unit()))

    def blinking(self):
        """
        Produce the blinking analysis for the data, using the normalized
        and summed data.
        """
        return(Blinking(self.summed().normalized()))

    def pulses_to_seconds(self, repetition_rate):
        """
        Use the repetiion rate to transform the time data into seconds,
        and the counts per pulse into counts per second.
        """
        times = list(map(lambda x: (x[0]/repetition_rate,
                                    x[1]/repetition_rate),
                         self.times))

        intensity = Intensity(mode="t2")
        intensity.times = times

        norm = self.normalized()

        for channel, counts in self:
            intensity[channel] = list(map(lambda x: x*repetition_rate,
                                          norm[channel]))

        return(intensity)

    def range(self, start_time, stop_time):
        """
        Return the intensity trace between the start and stop times.
        """
        times = list(map(lambda x: x[0], self.times))
        
        start_index = bisect.bisect_left(times, start_time)
        stop_index = bisect.bisect_left(times, stop_time)

        intensity = Intensity(mode=self.mode)
        intensity.times = self.times[start_index:stop_index]
    
        for channel, counts in self:
            intensity[channel] = counts[start_index:stop_index]

        return(intensity)

    def zero_origin(self):
        """
        Subtract the first time from all times, such that time starts from zero.
        """
        intensity = Intensity(mode=self.mode)
        start = self.times[0][0]
        intensity.times = list(map(lambda x: (x[0] - start,
                                              x[1] - start),
                                   self.times))

        for channel, counts in self:
            intensity[channel] = counts

        return(intensity)

    def threshold(self, threshold=0.7):
        """
        Remove all events below the specified threshold intensity (relative
        to maximum).
        """
        total = self.summed()
        min_intensity = max(total[0])*threshold

        result = Intensity(mode=self.mode)

        result.times = list(map(lambda y: y[0],
                                filter(
                                    lambda x: x[1] >= min_intensity,
                                    zip(self.times, total[0]))))
        
        for channel, counts in self:
            result[channel] = list(map(lambda y: y[0],
                                       filter(
                                           lambda x: x[1] >= min_intensity,
                                           zip(counts, total[0]))))
            
        return(result)
