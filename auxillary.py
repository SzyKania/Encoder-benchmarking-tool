import math


def float_round_str(float: float, precision: int):  # round and zeropad
    return str(("%."+str(precision)+"f") % round(float, precision))


def crf_ints_to_strings(codeccrftables, codec):
    if codec not in codeccrftables:
        return None
    crf_values = codeccrftables[codec]
    str_crf_values = [str(crf) for crf in crf_values]
    return str_crf_values


def log_vmaf(vmaf):
    return -10*math.log(1-(vmaf/100), 10)


def log_ssim(ssim):
    return -10*math.log(1-ssim, 10)


def parse_metrics(metrics, verbose=False):
    if verbose:
        print(metrics)
    timings = [timing[6:-1] for timing in metrics[0].split(' ')[1:]]
    maxrss = metrics[1][14:-3]
    return timings, maxrss