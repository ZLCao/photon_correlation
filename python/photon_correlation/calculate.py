import csv
import shelve
import os
import subprocess
import re
import math
import logging
from io import StringIO

from .Picoquant import Picoquant
from .Limits import Limits
from .Lifetime import Lifetime

from .util import *

def apply_t3_time_offsets(photons, time_offsets, repetition_rate):
    cmd = ["photon_t3_offsets", 
           "--repetition-rate", str(repetition_rate),
           "--channels", str(len(time_offsets)),
           "--time-offsets", str(time_offsets)]

    return(subprocess.Popen(cmd, stdin=photons.stdout, stdout=subprocess.PIPE))

def picoquant(filename, print_every=0, time_offsets=None,
              number=None, convert=False):
    cmd = ["picoquant"]

    if convert:
        cmd.extend(["--to-t2"])

    if number is not None:
        cmd.extend(("--number", str(number)))
        
    if print_every > 0:
        cmd.extend(("--print-every", str(print_every)))

    if filename.endswith("bz2"):
        photons = subprocess.Popen(["bunzip2", filename, "--stdout"],
                                   stdout=subprocess.PIPE)
        photons = subprocess.Popen(cmd,
                                   stdin=photons.stdout,
                                   stdout=subprocess.PIPE)
    else:
        cmd.extend(["--file-in", filename])
        photons = subprocess.Popen(cmd, stdout=subprocess.PIPE)

    if time_offsets is not None:
        pq = Picoquant(filename)
        if pq.mode() == "t3":
            photons = apply_t3_time_offsets(
                photons, time_offsets, pq.repetition_rate())
        else:
            raise(ValueError("Unsupported mode for time offsets: {}".format(
                pq.mode())))
                
    return(photons)

def intensity(data_filename, bin_width=50000, mode=None, channels=None,
              count_all=False, time_offsets=None, repetition_rate=None):
    logging.info("Calculating intensity of {} with bin width of {}".format(
        data_filename, bin_width))
    pq = Picoquant(data_filename)

    if channels is None:
        channels = pq.channels()

    if mode is None:
        mode = pq.mode()

    if repetition_rate is None:
        repetition_rate = pq.repetition_rate()

    photons = picoquant(data_filename, time_offsets=time_offsets)
    if time_offsets is not None:
        photons = apply_t3_time_offsets(photons, time_offsets, repetition_rate)

    intensity_cmd = ["photon_intensity",
                     "--bin-width", str(bin_width),
                     "--mode", mode,
                     "--channels", str(channels)]

    if count_all:
        intensity_cmd.append("--count-all")

    intensity = StringIO(subprocess.Popen(intensity_cmd, stdin=photons.stdout,
                         stdout=subprocess.PIPE).stdout.read().decode())

    return(intensity)

def number_to_channels(photons, correlate=False):
    cmd = ["photon_number_to_channels"]

    if correlate:
        cmd.append("--correlate-successive")

    return(subprocess.Popen(cmd, stdin=photons.stdout, stdout=subprocess.PIPE))

def photon_time_threshold(photons, correlate=False, time_threshold=10000):
    cmd = ["photon_time_threshold",
           "--time-threshold", str(int(time_threshold))]

    if correlate:
        cmd.append("--correlate-successive")

    return(subprocess.Popen(cmd, stdin=photons.stdout, stdout=subprocess.PIPE))

def photon_threshold(photons, window_width=None, mode=None,
                     threshold_min=None, threshold_max=None):
    cmd = ["photon_threshold",
           "--mode", mode,
           "--window-width", str(int(window_width)),
           "--threshold_min", str(int(threshold_min)),
           "--threshold_max", str(int(threshold_max))]

    return(subprocess.Popen(cmd, stdin=photons.stdout, stdout=subprocess.PIPE))

def gn(data_filename, photon_mode=None, gn_mode=None,
       order=2, channels=None,
       time_bins=None, pulse_bins=None,
       repetition_rate=None, time_offsets=None,
       window_width=None, bin_width=None,
       photon_number=False, number_correlate=False,
       time_bin_width=1024, time_threshold=None,
       threshold_min=None, threshold_max=None):
    logging.info("Calculating g{} for {}".format(order, data_filename))

    DEFAULT_REPETITION_RATE = 4999990

    if not bin_width is None:
        logging.info("This is a time-dependent calculation with a bin "
                     "width of {}".format(bin_width))

    pq = Picoquant(data_filename)

    if photon_mode is None:
        photon_mode = pq.mode()

    if repetition_rate is None:
        if photon_mode == "t3":
            repetition_rate = int(pq.repetition_rate())
        else:
            repetition_rate = DEFAULT_REPETITION_RATE

    repetition_time = 1e12/repetition_rate    
        
    if channels is None:
        channels = pq.channels()

    if gn_mode is None:
        gn_mode = photon_mode
        convert = False
    elif gn_mode == photon_mode:
        convert = False
    elif gn_mode == "t2" and photon_mode == "t3":
        convert = True
    else:
        raise(ValueError("Can't trans t2 file into t3"))

    if time_threshold:
        channels = 4            

    if isinstance(time_bins, int):
        time_bins = Limits(-repetition_time, repetition_time, n_bins=time_bins)
    
    if time_bins is None:
        if gn_mode == "t3" and order == 1:
            # Determine the resolution-limited time bins from the t3 file.
            resolution = int(pq.resolution())

            n_bins = 2**15
#            if data_filename.endswith("ht3"):
#                n_bins = 2**15
#            else:
#                raise(ValueError("Unsupported file type for "
#                                 "lifetime: {}".format(t3_filename)))

            time_bins = Limits(0, resolution*n_bins, n_bins=n_bins)
        elif gn_mode == "t3" and order >= 2:
            bins_per_side = int(math.ceil(repetition_time/time_bin_width))
            n_bins = bins_per_side*2 + 1
            time_bound = bins_per_side*time_bin_width + time_bin_width/2

            time_bins = Limits(-time_bound, time_bound, n_bins=n_bins)
        elif gn_mode == "t2":
            bins_per_side = int(math.ceil(repetition_time/time_bin_width*1.5))
            n_bins = bins_per_side*2 + 1
            time_bound = bins_per_side*time_bin_width + time_bin_width/2

            time_bins = Limits(-time_bound, time_bound, n_bins=n_bins)
        else:
            raise(ValueError("Unsupported mode for automatic time bins"
                             ": {}".format(mode)))

    # if photon_number:
        # channels = sum(range(1, channels+1))
        # dst_filename += ".number"

        # if number_correlate:
            # dst_filename += ".corr"

#    if convert:
#        dst_filename += ".{}".format(gn_mode)

    gn_cmd = ["photon_gn",
              "--mode", gn_mode,
              "--order", str(order),
              "--time", str(time_bins)]
   
    if gn_mode == "t3" and order > 1:
        if pulse_bins is None:
            pulse_bins = Limits(-1.5, 1.5, n_bins=3)

        gn_cmd.extend(("--pulse", str(pulse_bins)))


#    if not bin_width is None:
#        gn_cmd.extend(("--bin-width", str(bin_width)))
#
#        if window_width is None:
#            gn_cmd.extend(("--window-width", str(bin_width)))
#
#    if window_width and not time_threshold:
#        gn_cmd.extend(("--window-width", str(window_width)))


    photons = picoquant(data_filename, time_offsets=time_offsets, convert=convert)

    if photon_number:
        photons = number_to_channels(photons, correlate=number_correlate)
    elif threshold_min or threshold_max:
        photons = photon_threshold(photons, window_width=window_width,
                                   mode=gn_mode, threshold_min=threshold_min,
                                                 threshold_max=threshold_max)
    elif time_threshold:
        photons = photon_time_threshold(photons, correlate=number_correlate,
                                        time_threshold=time_threshold)

    gn_cmd.extend(("--channels", str(channels)))
    
    gn = StringIO(subprocess.Popen(gn_cmd, stdin=photons.stdout,
                  stdout=subprocess.PIPE).stdout.read().decode())

    # if bin_width is not None:
        # # In case of time-dependent results, bzip2 the files to save space.
        # root, filename = os.path.split(dst_filename)

        # for my_root, dirs, files in os.walk(root):
            # for filename in files:
                # if filename.endswith("td"):
                    # dst = os.path.join(my_root, filename)
                    # logging.info("Compressing {}".format(dst))
                    # subprocess.Popen(["bzip2", dst]).wait()

    return(gn)

def flid(src_filename, dst_filename, intensity_bins,
         window_width, time_bins=None, time_offsets=None):
    logging.info("Calculating flid for {} with window width {}".format(
        src_filename, window_width))
    
    pq = Picoquant(src_filename)

    if not pq.mode() == "t3":
        raise(ValueError("T3 mode data expected for flid calculation."))

    if time_bins is None:
        time_bins = Limits(0, int(1e12/pq.repetition_rate()), 1000)
        
    photons = picoquant(src_filename, time_offsets=time_offsets)

    if time_offsets is not None:
        photons = apply_t3_time_offsets(photons,
                                        time_offsets, pq.repetition_rate())
    

    cmd = ["photon_flid",
           "--window-width", str(window_width),
           "--time", str(time_bins),
           "--intensity", str(intensity_bins),
           "--file-out", dst_filename]

    subprocess.Popen(cmd, stdin=photons.stdout).wait()

def idgn(src_filename, dst_filename, intensity_bins,
         order=2, window_width=50000, repetition_rate=None,
         channels=None,
         time_bins=None, pulse_bins=None, mode=None,
         time_bin_width=1024, photon_number=False, number_correlate=False,
         time_offsets=None):
    logging.info("Calculating idg{} for {}".format(order, src_filename))

    pq = Picoquant(src_filename)

    if mode is None:
        mode = pq.mode()

    if mode == "t3":
        if repetition_rate is None:
            repetition_rate = pq.repetition_rate()

    if channels is None:
        channels = pq.channels()

    if photon_number:
        channels = sum(range(1, channels+1))

    if time_bins is None:
        if mode == "t3" and order == 1:
            # Determine the resolution-limited time bins from the t3 file.
            resolution = int(pq.resolution())

            if src_filename.endswith("ht3"):
                n_bins = 2**15
            else:
                raise(ValueError("Unsupported file type for "
                                 "lifetime: {}".format(t3_filename)))

            time_bins = Limits(0, resolution*n_bins, n_bins=n_bins)
        elif mode == "t3" and order >= 2:
            repetition_time = 1e12/repetition_rate

            bins_per_side = int(math.ceil(repetition_time/time_bin_width))
            n_bins = bins_per_side*2 + 1
            time_bound = bins_per_side*time_bin_width + time_bin_width/2

            time_bins = Limits(-time_bound, time_bound, n_bins=n_bins)
        elif mode == "t2":
            repetition_time = 1e12/repetition_rate

            bins_per_side = int(math.ceil(repetition_time/time_bin_width*1.5))
            n_bins = bins_per_side*2 + 1
            time_bound = bins_per_side*time_bin_width + time_bin_width/2

            time_bins = Limits(-time_bound, time_bound, n_bins=n_bins)
        else:
            raise(ValueError("Unsupported mode for automatic time bins"
                             ": {}".format(mode)))

    gn_cmd = ["photon_intensity_dependent_gn",
              "--file-out", dst_filename,
              "--mode", mode,
              "--order", str(order),
              "--channels", str(channels),
              "--intensity", str(intensity_bins),
              "--window-width", str(window_width),
              "--time", str(time_bins)]
   
    if mode == "t3" and order > 1:
        if pulse_bins is None:
            pulse_bins = Limits(-1.5, 1.5, n_bins=3)

        gn_cmd.extend(("--pulse", str(pulse_bins)))

    photons = picoquant(src_filename, time_offsets=time_offsets)

    if photon_number:
        photons = number_to_channels(photons, correlate=number_correlate)

    gn = subprocess.Popen(gn_cmd, stdin=photons.stdout).wait()

def max_counts(data_filename, window_width,
               dst_filename=None, mode=None, channels=None,
               time_offsets=None):
    logging.info("Calculating maximum counts of {} with bin width of {}".format(
        data_filename, window_width))
    pq = Picoquant(data_filename)

    if dst_filename is None:    
        dst_filename = os.path.join("{}.max_counts.run".format(data_filename),
                                    "max_counts.{}".format(window_width))

    root_dir =  os.path.split(dst_filename)[0]

    if not os.path.isdir(root_dir):
        os.makedirs(root_dir)

    if channels is None:
        channels = pq.channels()

    if mode is None:
        mode = pq.mode()

    photons = picoquant(data_filename, time_offsets=time_offsets)

    intensity_cmd = ["photon_intensity",
                     "--bin-width", str(window_width),
                     "--mode", mode,
                     "--channels", str(channels)]

    intensity = subprocess.Popen(intensity_cmd,
                                 stdin=photons.stdout,
                                 stdout=subprocess.PIPE)

    max_bin = (0, 0)
    max_counts = 0

    for line in csv.reader(map(lambda x: x.decode(), intensity.stdout)):
        counts = sum(map(int, line[2:]))
        if counts > max_counts:
            max_bin = line[:2]
            max_counts = counts

    with open(dst_filename, "w") as stream_out:
        writer = csv.writer(stream_out)
        writer.writerow(max_bin + [str(max_counts)])
