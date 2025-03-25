import os
import pickle
import subprocess

from datetime import datetime
from fractions import Fraction

from auxillary import float_round_str, parse_metrics
from configs.test_config import TestConfig
from configs.result_config import ResultConfig
from file_operations import FileInfo, clean_workspace, create_folder_tree, get_file_info
from metrics import calculate_vmaf_scores, generate_xlsx_report, print_statistics

DEFAULT_FFMPEG_ARGS = ['ffmpeg', '-hide_banner', '-y', '-benchmark']


class EncodingResults:
    def __init__(self, codec, rtime, maxrss, framecount, filesize, og_filesize, fps, crf):
        self.codec = codec
        self.rtime = rtime
        self.maxrss = maxrss
        self.frametime = float(self.rtime) * 1000/framecount  # ms
        self.filesize = filesize #[bytes]
        self.compression_ratio = og_filesize/self.filesize
        self.bitrate = int(self.filesize) * 8 / (1000 * int(framecount) / float(Fraction(fps))) #[kilobits]
        self.ssim = r"N\A"
        self.psnr_hvs = r"N\A"
        self.vmaf = r"N\A"
        self.crf = crf

    def set_scores(self, ssim, psnr_hvs, vmaf):
        self.ssim = ssim
        self.psnr_hvs = psnr_hvs
        self.vmaf = vmaf

    def __str__(self):
        return \
            "Codec: " + self.codec.ljust(12, ' ') +\
            "Time [s]: " + self.rtime.ljust(10)+\
            "T/frame [ms]: " + float_round_str(self.frametime, 3).ljust(8)+\
            "Compression ratio: " + float_round_str(self.compression_ratio, 2).ljust(10)+\
            "Size [KiB]: " + str(int(self.filesize/1024)).ljust(10) +\
            "Max memory [KiB]: " + self.maxrss.ljust(10) +\
            "Bitrate [kbps]: " + str(int(self.bitrate)) + "\t"\
            # "CRF/CQ: " + self.crf + "\t"\
            # "SSIM: " + str(self.ssim) + "\t"\
            # "PSNR_HVS: " + str(self.psnr_hvs) + "\t"\
            # "VMAF: " + str(self.vmaf) + "\t"


def encode_video_crf(fInfo: FileInfo, codec, codecargs=[], verbose=False, threadcount=12):
    if verbose:
        print("#" * 40 + codec + " START" + "#" * 40)

    vvencparams = []
    input_filename = "..\\..\\test_sequences\\" + fInfo.filename
    if codec == 'libvvenc':
        encoded_extension = '.266'
        if fInfo.pixel_format == 'yuv420p':
            vvencparams.append('-vvenc-params')
            vvencparams.append('internalbitdepth=8')
    else:
        encoded_extension = '.mp4'#TODO change to mkv?

    output_filename = ".\\encoded_videos\\" + fInfo.basename + "_" + codec + encoded_extension

    str_threadcount = str(threadcount)

    encode_args = [*DEFAULT_FFMPEG_ARGS, '-threads', str_threadcount,
                   '-i', input_filename, '-c:v', codec, *codecargs, *vvencparams, output_filename]

    metrics = []
    if verbose:
        print(os.getcwd())
        print(' '.join(encode_args))
    
    proc = subprocess.run(encode_args, stderr=subprocess.PIPE, text=True)
    output = proc.stderr.splitlines()

    if verbose:
        for line in output:
            print(line)

    for line in output:
        if line.startswith('bench'):
            metrics.append(line)

    if verbose:
        print("#" * 40 + codec + " COMPLETE" + "#" * 40)

    return metrics, os.path.getsize(output_filename)


def decode_encoded_videos(basename, codecs, verbose=False):
    for codec in codecs:
        if verbose:
            print('Decoding file encoded by', codec)
        encoded_basename = basename + "_" + codec
        if codec == 'libvvenc':
            encoded_extension = '.266'
        else:
            encoded_extension = '.mp4'
        encoded_filename = ".\\encoded_videos\\" + encoded_basename + encoded_extension
        decoded_filename = ".\\decoded_videos\\" + encoded_basename + '.y4m'
        ffargs = ['ffmpeg', '-hide_banner', '-y',
                  '-i', encoded_filename,  decoded_filename]
        proc = subprocess.run(ffargs, stderr=subprocess.PIPE, text=True)
        if verbose:
            print(proc.stderr)
            print()


def run_tests_crf(fInfo: FileInfo, codecs, codecargs, verbosity, resultconfig: ResultConfig):

    framecount = int(fInfo.framecount)    

    print("File name: ", fInfo.filename, ", file size: ", float_round_str(fInfo.filesize/1024, 2), "KiB", sep = "")
    print(fInfo)

    create_folder_tree(fInfo.basename)

    results = []
    for codec in codecs:
        metrics, filesize = encode_video_crf(fInfo, codec, codecargs[codec], verbose=verbosity)
        timings, maxrss = parse_metrics(metrics, verbose=verbosity)
        result = EncodingResults(codec, timings[2], maxrss, framecount, filesize, fInfo.filesize, fInfo.framerate, codecargs[codec][-1])
        results.append(result)
        if resultconfig.print_per_encode_statistics:
            print(result)
    print()

    decode_encoded_videos(fInfo.basename, codecs, verbose=verbosity)

    print("Calculating metrics of encoded materials")
    vmaf_scores = calculate_vmaf_scores(fInfo, codecs, results, verbose=verbosity)

    print_statistics(results, codecs, vmaf_scores)

    if resultconfig.per_file_xlsx_report:
        generate_xlsx_report(fInfo.basename, framecount,
                            fInfo.filesize, results, vmaf_scores, codecargs)

    os.chdir("..\\..")

    clean_workspace(fInfo.basename)

    return results


def run_crf_test_batch(testconfig: TestConfig, resultconfig: ResultConfig):
    results_crfs_files = {}
    for filename in testconfig.filenames:

        results_crfs = []
        fileinfo = get_file_info(filename)

        for i in range(len(testconfig.codec_args)):
            results = run_tests_crf(fileinfo, testconfig.codecs, testconfig.codec_args[i], testconfig.verbosity, resultconfig)
            results_crfs.append(results)

        results_crfs_files[filename] = results_crfs

        if resultconfig.per_file_pickle_dump:
            results_filename = "test_results\\" + fileinfo.basename + \
            "_" + datetime.now().strftime("%Y%m%d-%H%M%S") + ".pkl"

            with open(results_filename, 'wb') as file:
                results_tuple = (results_crfs, testconfig)
                pickle.dump(results_tuple, file)

    if resultconfig.per_batch_pickle_dump:
        results_filename = "test_results\\" + testconfig.test_name + "_tuple_" \
                            + datetime.now().strftime("%Y%m%d_%H%M%S") + ".pkl"
        with open(results_filename, 'wb') as file:
            results_tuple = (results_crfs_files, testconfig)
            pickle.dump(results_tuple, file)
        
    return results_crfs_files