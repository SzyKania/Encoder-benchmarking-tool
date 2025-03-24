from .test_sequences_lists import *

FFMPEG_CODECS_LIST = ['libx264', 'libx265', 'h264_amf','hevc_amf',
                      'libsvtav1', 'libvpx-vp9', 'libvvenc']

FFMPEG_CRF_ARGS = {
    'libx264': ["-crf"],
    'h264_amf': ["-rc", "qvbr", "-qvbr_quality_level"],
    'libx265': ["-crf"],
    'hevc_amf': ["-rc", "qvbr", "-qvbr_quality_level"],
    'libsvtav1': ["-crf"],
    'libvpx-vp9': ["-b:v", "0", "-crf"],
    'libvvenc': ["-qpa", "1", "-qp"]
}

class TestConfig:
    def __init__(self, codecs, filenames, testname = "NoName", verbosity = False,
                 codecargs = None, crftables = None, bitrates = None, runs = 1):
        self.codecs = codecs
        self.filenames = filenames
        self.test_name = testname
        self.verbosity = verbosity
        self.crf_tables = crftables
        self.crf_count = len(self.crf_tables[self.codecs[0]])
        self.bitrates = bitrates
        self.runs = runs
        self.codec_args = self.str_crf_to_ffmpeg_crf_args(codecargs)

    def __str__(self):
        fstrings = {'s1': self.codecs, 's2': self.codec_args, 's3': self.crf_tables,
                     's4': self.bitrates, 's5': self.filenames}
        return "Codecs: {s1}\nCodecargs: {s2}\nCrftables: {s3}\nBitrates:  {s4}\nFilenames: {s5}".format(**fstrings)
    
    def str_crf_to_ffmpeg_crf_args(self, codecargs):
        ffmpeg_crf_args = []
        for codec in self.codecs:
            for i in range(len(self.crf_tables[codec])):
                preset = codecargs[codec]
                crf_mode = FFMPEG_CRF_ARGS[codec]
                crf_value = str(self.crf_tables[codec][i])
                command = preset + crf_mode + [crf_value]
                if len(ffmpeg_crf_args) > i:
                    ffmpeg_crf_args[i][codec] = command
                else:
                    ffmpeg_crf_args.append({codec: command})
        return ffmpeg_crf_args
    
#region############# GENERAL PARAMETERS ####################

testname = "vidyo"
filenames = ['vidyo1_720p_60fps.y4m', 'Vidyo3_1280x720p_60fps.y4m']
verbosity = False
encoding_speed = 2 #0 = slowest (vvc slow) 1 = default (vvc fast) 2 = fastest
runs = 1
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
# codecs.append('libsvtav1')
codecs.append('libx265')
# codecs.append('libvpx-vp9')
codecs.append('libx264')

#endregion
#region################### PRESETS #########################

if encoding_speed == 0:   #slowest non-placebo (libvvenc slow)
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
crf_tables_filtered = {}
for codec in codecargs:
    if codec in codecs:
        codecargs_filtered[codec] = codecargs[codec]
        crf_tables_filtered[codec] = codeccrftables[codec]

#endregion

testconfig = TestConfig(codecs, filenames, testname, verbosity, codecargs_filtered,
                         crf_tables_filtered, target_bitrates)