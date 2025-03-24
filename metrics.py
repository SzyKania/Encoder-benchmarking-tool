import math
import subprocess
import numpy as np
import bjontegaard as bd
import xlsxwriter.utility
from datetime import datetime
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
from scipy.interpolate import Akima1DInterpolator

from auxillary import float_round_str, log_ssim, log_vmaf
from configs.test_config import TestConfig
from file_operations import FileInfo
from configs.result_config import ResultConfig


class VMAFScores:
    def __init__(self, codec, ssim, psnr_hvs, vmaf):
        self.codec = codec
        self.ssim = float(ssim)
        self.psnr_hvs = float(psnr_hvs)
        self.vmaf = float(vmaf)

    def get_scores(self):
        return self.ssim, self.psnr_hvs, self.vmaf

    def __repr__(self):
        return \
            "Codec: " + self.codec +\
            " SSIM: " + float_round_str(self.ssim, 3) +\
            " PSNR_HVS: " + float_round_str(self.psnr_hvs, 5) +\
            " VMAF: " + float_round_str(self.vmaf, 3)


def plot_results(results_bitrates, codecs, filename, resultconfig: ResultConfig, cpu_only=True, show_annotations=False):
    results_codec = {}
    for codec in codecs:
        results_codec[codec] = []
    for results in results_bitrates:
        for result in results:
            results_codec[result.codec].append(result)
    for codec in codecs:
        results_codec[codec].sort(key=lambda x: x.bitrate)
        # for result in results_codec[codec]:
        #     print(result)
    if cpu_only:
        filtered_codecs = [codec for codec in codecs if codec not in ['hevc_amf', 'h264_amf']]
    else:
        filtered_codecs = codecs

    plot_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for metric in resultconfig.metrics_str:
        plt.clf()
        for i, codec in enumerate(filtered_codecs):
            x = np.array([math.log(result.bitrate*1000) for result in results_codec[codec]])
            # x = np.array([result.bitrate for result in results_codec[codec]])
            if metric == "VMAF":
                y = np.array([log_vmaf(result.vmaf) for result in results_codec[codec]])
            elif metric == "SSIM":
                y = np.array([log_ssim(result.ssim) for result in results_codec[codec]])
            elif metric == "PSNR_HVS":
                y = np.array([result.psnr_hvs for result in results_codec[codec]])
            x_smooth = np.linspace(x.min(), x.max(), 300)
            y_akima = Akima1DInterpolator(x, y, method="akima")(x_smooth)
            cutoff = None
            for j, y_akima_value in enumerate(y_akima):
                if y_akima_value > 99.5:
                    cutoff = j
                    break
            if cutoff:
                x_smooth = x_smooth[:cutoff]
                y_akima = y_akima[:cutoff]
            plt.plot(x, y, 'C'+str(i)+'.')
            if show_annotations:
                for xy in zip([round(x_val, 2) for x_val in x], [round(y_val, 2) for y_val in y]):
                    plt.annotate('(%s, %s)' % xy, xy=xy, textcoords='data', ha='center')

            plt.plot(x_smooth, y_akima, 'C'+str(i), label=codec)
        plt.ylabel(metric)
        plt.xlabel('log(bitrate [bit/s])')
        # plt.xlabel('bitrate [kbit/s]')
        # plt.xscale('log')
        plt.title(filename)
        plt.legend()

        if resultconfig.save_plot:
            plot_filename = "test_results\\" + filename + \
            "_" + plot_time + "_" + metric + ".png"
            plt.savefig(plot_filename)
        if resultconfig.show_plot:
            plt.show()


def plot_frametime_aggregated_results(aggregated_crfs_results, codecs):

    if codecs[0] == 'libsvtav1' and codecs[1] == 'libvvenc':
        codecs[0] = 'libvvenc'
        codecs[1] = 'libsvtav1'

    codec_frametimes = dict.fromkeys(codecs)

    for codec in codec_frametimes:
        codec_frametimes[codec] = []

    for crf_tier in aggregated_crfs_results:
        for result in crf_tier:
            codec_frametimes[result.codec].append(round(result.frametime_avg, 1))

    barWidth = 0.175

    cr_count = len(codec_frametimes[codecs[0]])

    brs = []
    br0 = np.arange(cr_count)
    brs.append(br0)
    for i in range(1, len(codecs)):
        br_i = [x + barWidth for x in brs[i-1]]
        brs.append(br_i)

    myedgecolor = 'white'

    fig, ax = plt.subplots(figsize=(9.75, 4.5))

    for i, codec in enumerate(codecs):
        print("brs[i]:", brs[i])
        print("codec_frametimes[codec]", codec_frametimes[codec])
        print("codec:", codec)
        rects = plt.bar(brs[i], codec_frametimes[codec], width = barWidth,
            edgecolor =myedgecolor, label =codec)
        plt.bar_label(rects, padding=3, transform_rotates_text=True)

    ax.set_yscale('log')
    plt.ylim(top=10**3)
    plt.xlabel('Quality tier')
    plt.ylabel('Average time per frame [ms]')
    plt.xticks([r + barWidth*2 for r in range(cr_count)],
            [*['Q'+str(i) for i in range(cr_count)]])

    plt.title('Time to encode per frame of 720p sequences')
    plt.legend(loc='upper left')
    plt.show()


def plot_class_aggregated_results(aggregated_crfs_results, codecs, sequences_class_name,
                                  resultconfig: ResultConfig, cpu_only=True, show_annotations=False):
    results_codec = {}
    for codec in codecs:
        results_codec[codec] = []
    for results in aggregated_crfs_results:
        for result in results:
            results_codec[result.codec].append(result)
    for codec in codecs:
        results_codec[codec].sort(key=lambda x: x.bitrate_avg)
        # if codec == 'libx264':
        #     for result in results_codec[codec]:
        #         print(result)

    if cpu_only:
        filtered_codecs = [codec for codec in codecs if codec not in ['hevc_amf', 'h264_amf']]
    else:
        filtered_codecs = codecs

    plot_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    for metric in resultconfig.metrics_str:
        plt.clf()
        for i, codec in enumerate(filtered_codecs):

            x = np.array([math.log(result.bitrate_avg*1000) for result in results_codec[codec]])
            if metric == "VMAF":
                y = np.array([log_vmaf(result.vmaf_avg) for result in results_codec[codec]])
            elif metric == "SSIM":
                y = np.array([log_ssim(result.ssim_avg) for result in results_codec[codec]])
            elif metric == "PSNR_HVS":
                y = np.array([result.psnr_hvs_avg for result in results_codec[codec]])

            x_smooth = np.linspace(x.min(), x.max(), 300)
            y_akima = Akima1DInterpolator(x, y, method="akima")(x_smooth)

            # spl = make_interp_spline(x, y, k=3)
            # y_smooth = spl(x_smooth)
            plt.plot(x, y, 'C'+str(i)+'.')
            if show_annotations:
                for xy in zip([round(x_val, 2) for x_val in x], [round(y_val, 2) for y_val in y]):
                    plt.annotate('(%s, %s)' % xy, xy=xy, textcoords='data', ha='center')
            plt.plot(x_smooth, y_akima, 'C'+str(i), label=codec)
        plt.ylabel(metric)


        plt.xlabel('log(bitrate [bit/s])')
        plt.title(sequences_class_name)
        plt.legend()

        if resultconfig.save_plot:
            plot_filename = "test_results\\" + sequences_class_name + \
            "_" + plot_time + "_" + metric + "_" ".png"
            plt.savefig(plot_filename)
        if resultconfig.show_plot:
            plt.show()


def print_aggregated_results(aggregated_crfs_results, codecs):
    results_codec = {}
    for codec in codecs:
        results_codec[codec] = []
    for results in aggregated_crfs_results:
        for result in results:
            results_codec[result.codec].append(result)
    for codec in codecs:
        results_codec[codec].sort(key=lambda x: x.bitrate_avg)

    for codec in codecs:
        print(codec)
        for result in results_codec[codec]:
            print(result.rtime_avg)
        print()


def print_bd_rates(bd_rates_metric_codecs, metric, testconfig, resultconfig: ResultConfig, bd_filename, bd_psnr = False):

    if bd_psnr:
        method = "BD-PSNR"
    else:
        method = "BD-RATE"

    if resultconfig.print_bd_rates:
        print("Testconfigname= ", testconfig.test_name, "\t", metric, " ", method, sep="")
        print(" "*16, end="")
        for codec in bd_rates_metric_codecs:
            print(codec.ljust(16), end="")
        print()
        for codec in bd_rates_metric_codecs:
            print(codec.ljust(15), *[bd_rate.ljust(15) if bd_rate=="X" else "{0:0.02f}%".format(bd_rate).ljust(15)for bd_rate in bd_rates_metric_codecs[codec]])
        print()

    if resultconfig.csv_bd_rates:

        with open(bd_filename, 'a') as f:
            print("Testconfigname", testconfig.test_name, metric+" "+method, sep=";", file=f)
            print(metric,method,";", end="", file=f)
            for codec in bd_rates_metric_codecs:
                print(codec, end=";", file=f)
            print(file=f)
            for codec in bd_rates_metric_codecs:
                print(codec, *[bd_rate if bd_rate=="X" else "{0:0.02f}%".format(bd_rate)for bd_rate in bd_rates_metric_codecs[codec]], sep=";", file=f)
            print(file=f)

def calculate_bd_rate(testconfig: TestConfig, results, resultconfig: ResultConfig, bd_psnr = False):

    results_codecs = dict.fromkeys(testconfig.codecs)
    bd_rates_vmaf_codecs = dict.fromkeys(testconfig.codecs)
    bd_rates_ssim_codecs = dict.fromkeys(testconfig.codecs)
    bd_rates_psnr_hvs_codecs = dict.fromkeys(testconfig.codecs)
    bd_filename = "test_results\\" + "bd_rates_" + testconfig.test_name + \
        "_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".csv"


    metrics = resultconfig.metrics_str
    
    for codec in results_codecs:
        results_codecs[codec] = []
        bd_rates_vmaf_codecs[codec] = []
        bd_rates_ssim_codecs[codec] = []
        bd_rates_psnr_hvs_codecs[codec] = []
    for result_crf in results:
        for result_codec in result_crf:
            results_codecs[result_codec.codec].append(result_codec)

    for metric in metrics:
        for anchor_codec in results_codecs:
            for test_codec in results_codecs:
                if test_codec == anchor_codec:
                    if metric == "VMAF":
                        bd_rates_vmaf_codecs[test_codec].append("X")
                    elif metric == "SSIM":
                        bd_rates_ssim_codecs[test_codec].append("X")
                    elif metric == "PSNR_HVS":
                        bd_rates_psnr_hvs_codecs[test_codec].append("X")
                else:
                    rate_anchor = []
                    metric_anchor = []

                    rate_test = []
                    metric_test = []

                    for result in results_codecs[anchor_codec]:
                        rate_anchor.append(result.bitrate_avg)
                        metric_anchor.append(log_vmaf(result.vmaf_avg) if metric == "VMAF" else
                                             log_ssim(result.ssim_avg) if metric == "SSIM" else
                                             result.psnr_hvs_avg if metric == "PSNR_HVS" else None)

                    for result in results_codecs[test_codec]:
                        rate_test.append(result.bitrate_avg)
                        metric_test.append(log_vmaf(result.vmaf_avg) if metric == "VMAF" else
                                           log_ssim(result.ssim_avg) if metric == "SSIM" else
                                           result.psnr_hvs_avg if metric == "PSNR_HVS" else None)

                    if bd_psnr:
                        bd_rate = bd.bd_psnr(rate_anchor, metric_anchor, rate_test, metric_test, method='akima', min_overlap=0)
                    else:
                        bd_rate = bd.bd_rate(rate_anchor, metric_anchor, rate_test, metric_test, method='akima', min_overlap=0)

                    if metric == "VMAF":
                        bd_rates_vmaf_codecs[test_codec].append(bd_rate)
                    elif metric == "SSIM":
                        bd_rates_ssim_codecs[test_codec].append(bd_rate)
                    elif metric == "PSNR_HVS":
                        bd_rates_psnr_hvs_codecs[test_codec].append(bd_rate)
        if metric == "VMAF":
            print_bd_rates(bd_rates_vmaf_codecs, "VMAF", testconfig, resultconfig, bd_filename, bd_psnr)
        elif metric == "SSIM":
            print_bd_rates(bd_rates_ssim_codecs, "SSIM", testconfig, resultconfig, bd_filename, bd_psnr)
        elif metric == "PSNR_HVS":
            print_bd_rates(bd_rates_psnr_hvs_codecs, "PSNR_HVS", testconfig, resultconfig, bd_filename, bd_psnr)


def calculate_vmaf_scores(fInfo: FileInfo, codecs, results, verbose=False):
    vmaf_scores = {}

    print('Converting sequence to yuv format for VMAF')
    raw_filepath = "..\\..\\test_sequences\\" + fInfo.filename
    ffargs = ['ffmpeg', '-hide_banner', '-y', '-i', raw_filepath, '.\\'+fInfo.basename+'.yuv']
    proc = subprocess.run(ffargs, stderr=subprocess.PIPE, text=True)
    if verbose:
        print(proc.stderr)

    for codec in codecs:
        print('Calculating metrics of sequence encoded by', codec)

        vmaf_scores[codec] = None
        decoded_filename = ".\\decoded_videos\\" + fInfo.basename + "_" + codec + '.yuv'
        log_path = './libvmaf_logs/' + fInfo.basename + "_" + codec + '.xml'

        if fInfo.pixel_format == 'yuv420p':
            pix_fmt = '420'
            bit_depth = '8'
        elif fInfo.pixel_format == 'yuv420p10le':
            pix_fmt = '420'
            bit_depth = '10'
        vmafargs = ['vmaf', '-r', '.\\'+fInfo.basename+'.yuv', '-d', decoded_filename,
                    '-w', fInfo.width, '-h', fInfo.height, '-p', pix_fmt, '-b', bit_depth,
                    '--feature', 'float_ssim', '--feature', 'psnr_hvs',  # '--feature', 'psnr', '--feature', 'float_ms_ssim',
                    '--threads', '12', '-q', '-o', log_path]

        proc = subprocess.run(vmafargs, stdout=subprocess.PIPE, text=True)
        if verbose:
            print(proc.stdout)

        with open(log_path, 'r') as f:
            data = f.read()
        Bs_data = BeautifulSoup(data, "xml")

        ssim = Bs_data.find('metric', {'name': 'float_ssim'}).get('mean')
        psnr_hvs = Bs_data.find('metric', {'name': 'psnr_hvs'}).get('mean')
        vmaf = Bs_data.find('metric', {'name': 'vmaf'}).get('mean')

        vmaf_scores[codec] = VMAFScores(codec, ssim, psnr_hvs, vmaf)
    for codec in vmaf_scores:
        for result in results:
            if result.codec == codec:
                result.set_scores(*vmaf_scores[codec].get_scores())
                break
        # print(result)
    return vmaf_scores


def print_statistics(results, codecs, vmaf_scores, runs = 1):
    runtime_sums = {}
    frametime_sums = {}

    for result in results:
        if result.codec not in runtime_sums:
            runtime_sums[result.codec] = float(result.rtime)
            frametime_sums[result.codec] = result.frametime
        else:
            runtime_sums[result.codec] += float(result.rtime)
            frametime_sums[result.codec] += result.frametime

    runtime_avgs = runtime_sums
    frametime_avgs = frametime_sums
    for codec in codecs:
        runtime_avgs[codec] /= runs
        frametime_avgs[codec] /= runs
    print()
    print("Average metrics achieved by each encoder:")
    print(
        "Codec".ljust(12), "Time [s]".ljust(10), "Time/frame [ms]".ljust(17), "SSIM:".ljust(8), "VMAF:", sep="")
    for codec in runtime_avgs:
        print(codec.ljust(12), float_round_str(runtime_avgs[codec], 4).ljust(10), float_round_str(
            frametime_avgs[codec], 4).ljust(18), float_round_str(vmaf_scores[codec].ssim, 4).ljust(8),
             vmaf_scores[codec].vmaf, sep="")
    print("\n\n")


def generate_xlsx_report(basename, framecount, original_filesize, results, vmaf_scores, codecargs):
    now = datetime.now()
    test_name = "..\\..\\test_results\\" + basename + \
        "_" + now.strftime("%Y%m%d-%H%M%S") + ".xlsx"
    test_outputs = xlsxwriter.Workbook(test_name)

    nonvariables_ws = test_outputs.add_worksheet("Nonvariables")
    allruns_ws = test_outputs.add_worksheet("All runs")

    header = ['Name', basename, 'Framecount',
              framecount, 'Filesize', original_filesize]
    allruns_ws.write_row(0, 0, header)
    data_header = ['Codec', 'T[s]', 'T/frame[ms]',
                   'CR', 'Filesize [B]', 'Max memory [KiB]']
    allruns_ws.write_row(1, 0, data_header)
    for i, result in enumerate(results):
        row = [result.codec, result.rtime, result.frametime,
               result.compression_ratio, result.filesize, result.maxrss]
        allruns_ws.write_row(i+2, 0, row)

    unique_codec_results = {}
    for result in results:
        if result.codec not in unique_codec_results:
            unique_codec_results[result.codec] = result

    header = ['Name', basename, 'Framecount',
              framecount, 'Filesize', original_filesize]
    nonvariables_ws.write_row(0, 0, header)
    dataheader = ['Codec', 'Filesize [B]', 'CR',
        'SSIM', 'VMAF', 'PSNR_HVS', 'ARGS']
    nonvariables_ws.write_row(1, 0, dataheader)

    for i, codec in enumerate(unique_codec_results):
        data = [unique_codec_results[codec].codec, unique_codec_results[codec].filesize,
                unique_codec_results[codec].compression_ratio,
                vmaf_scores[codec].ssim, vmaf_scores[codec].vmaf,
                vmaf_scores[codec].psnr_hvs, ' '.join(codecargs[codec])]
        nonvariables_ws.write_row(i+2, 0, data)

    allruns_ws.autofit()
    nonvariables_ws.autofit()
    test_outputs.close()