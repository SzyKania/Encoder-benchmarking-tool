from test_sequences_lists import *

class TestConfig:
    def __init__(self, codecs, filenames, testname = "NoName", verbosity = False,
                 codecargs = None, crftables = None, bitrates = None, runs = 1):
        self.codecs = codecs
        self.filenames = filenames
        self.test_name = testname
        self.verbosity = verbosity
        self.crf_tables = crftables
        self.crf_count = len(self.crf_tables[self.codecs[0]])
        self.codec_args = codecargs
        self.bitrates = bitrates
        self.runs = runs
    def __str__(self):
        fstrings = {'s1': self.codecs, 's2': self.codec_args, 's3': self.crf_tables,
                     's4': self.bitrates, 's5': self.filenames}
        return "Codecs: {s1}\nCodecargs: {s2}\nCrftables: {s3}\nBitrates:  {s4}\nFilenames: {s5}".format(**fstrings)

class LoadConfig:
    def __init__(self, load_results = False, load_single_test = False, 
                 load_filename = None, restore_results = False, pkls_to_restore = None):
        self.load_results = load_results
        self.load_single_test = load_single_test
        self.load_filename = load_filename
        self.restore_results = restore_results
        self.pkls_to_restore = pkls_to_restore

class PlotConfig:
    def __init__(self, save_plot = False, show_plot = False, print_bd_rates = False,
                  csv_bd_rates = False, include_vmaf = False, include_ssim = False,
                  include_psnr_hvs = False):
        self.save_plot = save_plot
        self.show_plot = show_plot
        self.print_bd_rates = print_bd_rates
        self.csv_bd_rates = csv_bd_rates
        self.include_vmaf = include_vmaf
        self.include_ssim = include_ssim
        self.include_psnr_hvs = include_psnr_hvs
        self.metrics_str = []
        if self.include_vmaf: self.metrics_str.append("VMAF")
        if self.include_ssim: self.metrics_str.append("SSIM")
        if self.include_psnr_hvs: self.metrics_str.append("PSNR_HVS")

#region############# GENERAL PARAMETERS ####################

testname = "vidyo"
filenames = ['vidyo1_720p_60fps.y4m']
verbosity = False
encoding_speed = 2 #0 = slowest (vvc slow) 1 = default (vvc fast) 2 = fastest
runs = 1
#endregion
#region############# RESULTS PARAMETERS ####################

save_plot = False
show_plot = False
print_bd_rates = True
csv_bd_rates = True
include_vmaf = False
include_ssim = True
include_psnr_hvs = True
#endregion
#region################ LOAD RESULTS #######################

load_results = True
load_single_test = False
load_filename = "a1_class\\a1_class_tuple_20250123_160417"
load_filename = "vidyo_tuple_20250314_184739"

load_filename += ".pkl"

#endregion
#region############# BATCH RESTORATION #####################

restore_results = False
pkls_to_restore = []
# pkls_to_restore.append("PierSeaSide_3840x2160_2997fps_10bit_420_v2_20250123-125211.pkl")
# pkls_to_restore.append("NocturneDance_3840x2160p_10bit_60fps_20250123-110822.pkl")


#endregion
#region################ RATE CONTROL #######################

rate_control_crf = True
if rate_control_crf:
    codeccrftables = {
        'libx264':      [40, 31, 24, 17],
        'libx265':      [40, 30, 25, 17],
        'libvvenc':     [45, 36, 28, 20],
        'libvpx-vp9':   [63, 51, 39, 27],
        'libsvtav1':    [63, 50, 37, 20],
        'h264_amf':     [10, 15, 20, 24],
        'hevc_amf':     [ 9, 23, 28, 33]
    }
    codeccrftables = {
        'libx264':      [31, 24, 17],
        'libx265':      [30, 25, 17],
        'libvvenc':     [36, 28, 20],
        'libvpx-vp9':   [51, 39, 27],
        'libsvtav1':    [50, 37, 20],
        'h264_amf':     [15, 20, 24],
        'hevc_amf':     [23, 28, 33]
    }

    crf_count = len(codeccrftables["libx264"])
    target_bitrates = None
else:
    target_bitrates = [600000, 800000, 1000000, 1200000, 1400000]
    target_bitrates = [1200000, 1600000, 1800000, 2000000, 2200000]
    target_bitrates = [800000]

#endregion
#region############### CODEC SELECTION #####################

codecs = []
# codecs.append('libvvenc')
codecs.append('libsvtav1')
codecs.append('libx265')
# codecs.append('libvpx-vp9')
codecs.append('libx264')

#endregion
#region################### PRESETS #########################

if encoding_speed == 0:   #slowest
    codecargs = {
        'libx264': ['-preset', 'veryslow'],
        'h264_amf': ['-preset', '2'],
        'libx265': ['-preset', 'veryslow'],
        'hevc_amf': ['-preset', '0'],
        'libsvtav1': ['-preset', '1'],
        'libvpx-vp9': ['-deadline', 'best'],
        'libvvenc': ['-preset', 'slow']
    }

elif encoding_speed == 1: #default
    codecargs = {
        'libx264': [],
        'h264_amf': [],
        'libx265': [],
        'hevc_amf': [],
        'libsvtav1': [],
        'libvpx-vp9':['-row-mt', '1'],
        'libvvenc': ['-preset', 'fast']
    }

elif encoding_speed == 2: #fastest
    codecargs = {
        'libx264': ['-preset', 'ultrafast'],
        'h264_amf': ['-preset', '1'],
        'libx265': ['-preset', 'ultrafast'],
        'hevc_amf': ['-preset', '10'],
        'libsvtav1': ['-preset', '13'],
        'libvpx-vp9': ['-row-mt', '1', '-deadline', 'realtime', '-cpu-used', '8'],
        'libvvenc': ['-preset', 'faster']
    }

else:
    raise ValueError("ENCODING SPEED NOT SELECTED")


codecargs_filtered = {}
for codec in codecargs:
    if codec in codecs:
        codecargs_filtered[codec] = codecargs[codec]

#endregion
#region################## EXECUTION ########################

testconfig = TestConfig(codecs, filenames, testname, verbosity, codecargs_filtered,
                         codeccrftables, target_bitrates)

loadconfig = LoadConfig(load_results, load_single_test, load_filename, restore_results, pkls_to_restore)

plotconfig = PlotConfig(save_plot, show_plot, print_bd_rates, csv_bd_rates, include_vmaf, include_ssim, include_psnr_hvs)
#endregion