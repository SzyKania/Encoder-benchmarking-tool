import os
import copy
import pickle
import subprocess

from datetime import datetime
from fractions import Fraction

from auxillary import crf_ints_to_strings, float_round_str, parse_metrics
from file_operations import FileInfo, clean_workspace, create_folder_tree, get_file_info
from configs.test_config import TestConfig, testconfig
from configs.load_config import LoadConfig, loadconfig
from configs.result_config import ResultConfig, resultconfig
from metrics import calculate_bd_rate, calculate_vmaf_scores, generate_xlsx_report, plot_class_aggregated_results, plot_frametime_aggregated_results, plot_results, print_statistics

DEFAULT_FFMPEG_ARGS = ['ffmpeg', '-hide_banner', '-y', '-benchmark']

class FilesAggregatedResults:
    def __init__(self, codec, rtime_avg, vmaf_avg, bitrate_avg, crf, psnr_hvs = None, ssim_avg = None, frametime_avg = None):
        self.codec = codec
        self.crf = crf
        self.rtime_avg = rtime_avg
        self.vmaf_avg = vmaf_avg
        self.ssim_avg = ssim_avg
        self.psnr_hvs_avg = psnr_hvs
        self.bitrate_avg = bitrate_avg
        self.frametime_avg = frametime_avg
    def __str__(self):
        fstrings = {'s1': self.codec.ljust(10), 's2': self.crf, 's3': round(self.bitrate_avg, 2),
                     's4': round(self.vmaf_avg, 2), 's5': round(self.rtime_avg, 2),
                       's6': round(self.psnr_hvs_avg), 's7': round(self.ssim_avg), 's8': self.frametime_avg}
        return "Codec: {s1} Crf: {s2}\tBitrate_avg: {s3}\tVmaf_avg: {s4}\tRtime_avg: {s5}\t\
                PSNR_HVS_avg: {s6}\tSSIM_avg: {s7}\t Frametime_avg: {s8}".format(**fstrings)


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
        decoded_filename = ".\\decoded_videos\\" + encoded_basename + '.yuv'
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


def aggregate_crf_test_batch_results(results_crfs_files, crf_count, codecs):

    codeccount = len(codecs)
    try:
        filecount = len(results_crfs_files.keys())
    except AttributeError as e:
        print("If loading a singular test for graph generation make sure to set load_single_test in config.")
        raise e

    all_results = []
    aggregated_crfs_results = []
    for i in range(crf_count):
        aggregated_crfs_results.append([])

    for filename in results_crfs_files:
        for test_runs in results_crfs_files[filename]:
            for result in test_runs:
                all_results.append(result)

    for i in range(crf_count):
        bitrates_codecs = dict.fromkeys(codecs, 0)
        vmaf_codecs = dict.fromkeys(codecs, 0)
        ssim_codecs = dict.fromkeys(codecs, 0)
        psnr_hvs_codecs = dict.fromkeys(codecs, 0)
        rtime_codecs = dict.fromkeys(codecs, 0)
        frametime_codecs = dict.fromkeys(codecs, 0)
        crf_codecs = dict.fromkeys(codecs, 0)

        for filename in results_crfs_files:#vidyo1, vidyo2...
            codecs_results = results_crfs_files[filename][i]#[result(264), result265...]
            for result in codecs_results:#result(264)
                bitrates_codecs[result.codec] += result.bitrate
                vmaf_codecs[result.codec] += result.vmaf
                ssim_codecs[result.codec] += result.ssim
                psnr_hvs_codecs[result.codec] += result.psnr_hvs
                rtime_codecs[result.codec] += float(result.rtime)
                frametime_codecs[result.codec] = result.frametime
                crf_codecs[result.codec] = result.crf
                
        for codec in bitrates_codecs:  
            bitrates_codecs[codec] /= filecount 
            vmaf_codecs[codec] /= filecount 
            ssim_codecs[codec] /= filecount
            psnr_hvs_codecs[codec] /= filecount
            rtime_codecs[codec] /= filecount
            frametime_codecs[codec] /= filecount
            

        for codec in bitrates_codecs:
            aggregated_crfs_results[i].append(FilesAggregatedResults(codec,
                                                rtime_codecs[codec], vmaf_codecs[codec],
                                                bitrates_codecs[codec], crf_codecs[codec], psnr_hvs_codecs[codec], ssim_codecs[codec], frametime_codecs[codec]))
    return aggregated_crfs_results


def load_results(loadconfig: LoadConfig, resultconfig: ResultConfig):
    with open("test_results\\" + loadconfig.load_filename, 'rb') as file:
        loaded_results = pickle.load(file)
    results_crfs_files = loaded_results[0]
    testconfig = loaded_results[1]
    if loadconfig.load_single_test:
        acr = aggregate_crf_test_batch_results()
        plot_results(results_crfs_files, testconfig.codecs, loadconfig.load_filename[:-4], resultconfig)
        quit()
    acr = aggregate_crf_test_batch_results(results_crfs_files,
                                testconfig.crf_count, testconfig.codecs)
    if resultconfig.print_bd_rates or resultconfig.csv_bd_rates:
        calculate_bd_rate(testconfig, acr, resultconfig)

    plot_frametime_aggregated_results(acr, testconfig.codecs)

    plot_class_aggregated_results(acr, testconfig.codecs, testconfig.test_name, resultconfig)
    return results_crfs_files, testconfig


def combine_crf_results(pkls_to_restore):
    results_crfs_files = {}
    video_filenames = []
    testconfig = None
    for pkl in pkls_to_restore:
        video_filename = pkl[:-20]+".y4m"
        video_filenames.append(video_filename)
        with open("test_results\\" + pkl, 'rb') as file:
            loaded_results = pickle.load(file)
            results_crfs_file = loaded_results[0]
            results_crfs_files[video_filename] = results_crfs_file
            testconfig = loaded_results[1]
    testconfig.filenames = video_filenames
    return results_crfs_files, testconfig


def loading_handler(loadconfig: LoadConfig, resultconfig: ResultConfig):
    if loadconfig.restore_results:
        print("Reconstructing batch test results from following files:", loadconfig.pkls_to_restore)
        results_crfs_files, testconfig = combine_crf_results(loadconfig.pkls_to_restore)
        results_filename = "test_results\\" + testconfig.test_name + "_tuple_" \
                    + datetime.now().strftime("%Y%m%d_%H%M%S") + ".pkl"
        with open(results_filename, 'wb') as file:
            results_tuple = (results_crfs_files, testconfig)
            pickle.dump(results_tuple, file)

        print("Reconstructed results saved as", results_filename)

    elif loadconfig.load_results:
        results_crfs_files, testconfig = load_results(loadconfig, resultconfig)


if __name__ == "__main__":
    if loadconfig.restore_results or loadconfig.load_results:
        loading_handler(loadconfig, resultconfig)
    else:
        results_crfs_files = run_crf_test_batch(testconfig, resultconfig)
        if testconfig.crf_count > 3 and (resultconfig.show_plot or resultconfig.save_plot):
            for file in testconfig.filenames:
                plot_results(results_crfs_files[file], testconfig.codecs, file,
                                resultconfig)
            acr = aggregate_crf_test_batch_results(results_crfs_files,
                                testconfig.crf_count, testconfig.codecs)
            plot_class_aggregated_results(acr, testconfig.codecs, testconfig.test_name,
                                    resultconfig)
