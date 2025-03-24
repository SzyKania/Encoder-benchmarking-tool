#this file is legacy, the functions work and can be used
#however during the production of this software libsvtav1 in ffmpeg didnt support crf 2-pass encoding
#hence svtav1encapp is required to be installed and added to path
from codec_benchmarking_tool import *
from file_operations import FileInfo
from metrics import generate_xlsx_report, print_statistics
import os

def encode_video_two_pass(fInfo: FileInfo, codec, bitrate, codecargs=[], verbose=False, threadcount=12):
    if verbose:
        print("#" * 40 + codec + " START" + "#" * 40)

    # if codec in ['h264_amf', 'hevc_amf']: #no two-pass support
    #     return encode_video(input_filename, basename, codec, fileinfo, codecargs, verbose)

    vvencparams = []
    input_filename = "..\\..\\test_sequences\\" + fInfo.filename
    if codec == 'libvvenc':
        encoded_extension = '.266'
        if fInfo.pixel_format == 'yuv420p':
            vvencparams.append('-vvenc-params')
            vvencparams.append('internalbitdepth=8')
    else:
        encoded_extension = '.mp4'

    output_filename = ".\\encoded_videos\\" + fInfo.basename + "_" + codec + encoded_extension

    str_threadcount = str(threadcount)
    str_bitrate = str(bitrate)
    str_minrate = str(int(bitrate*0.4))
    str_maxrate = str(int(bitrate*1.6)) #libvvenc crash fix

    encode_args_1 = []
    encode_args_2 = []

    if codec in ['libx264', 'libvpx-vp9', 'libvvenc']:
        if codec == 'libvpx-vp9':
            encode_args_1 = [*DEFAULT_FFMPEG_ARGS, '-threads', str_threadcount,
                '-i', input_filename, '-c:v', codec, '-b:v', str_bitrate,# *codecargs #crash fix
                '-pass', '1', '-passlogfile', './ffmpeg_logs/'+codec, '-f', 'null', '-']
            encode_args_2 = [*DEFAULT_FFMPEG_ARGS, '-threads', str_threadcount,
                '-i', input_filename, '-c:v', codec, '-b:v', str_bitrate, *codecargs, 
                '-pass', '2', '-passlogfile', './ffmpeg_logs/'+codec, output_filename]
        else:
            encode_args_1 = [*DEFAULT_FFMPEG_ARGS, '-threads', str_threadcount,
                '-i', input_filename, '-c:v', codec, '-b:v', str_bitrate, '-minrate', str_minrate, '-maxrate', str_maxrate, *codecargs, 
                '-pass', '1', '-passlogfile', './ffmpeg_logs/'+codec, *vvencparams, '-f', 'null', '-']
            encode_args_2 = [*DEFAULT_FFMPEG_ARGS, '-threads', str_threadcount,
                    '-i', input_filename, '-c:v', codec, '-b:v', str_bitrate, '-minrate', str_minrate, '-maxrate', str_maxrate, *codecargs, 
                    '-pass', '2', '-passlogfile', './ffmpeg_logs/'+codec, *vvencparams, output_filename]
    elif codec == 'libx265':
        encode_args_1 = [*DEFAULT_FFMPEG_ARGS, '-threads', str_threadcount,
                '-i', input_filename, '-c:v', codec, '-b:v', str_bitrate, '-minrate', str_bitrate, '-maxrate', str_bitrate, *codecargs, 
                '-x265-params',  'pass=1:stats=./ffmpeg_logs/'+codec, '-f', 'null', '-']
        encode_args_2 = [*DEFAULT_FFMPEG_ARGS, '-threads', str_threadcount,
                '-i', input_filename, '-c:v', codec, '-b:v', str_bitrate, '-minrate', str_bitrate, '-maxrate', str_bitrate, *codecargs, 
                '-x265-params',  'pass=2:stats=./ffmpeg_logs/'+codec, output_filename]
    elif codec in ['h264_amf', 'hevc_amf']:
        str_bitrate = str(bitrate/2)#TODO HACK
        encode_args_1 = [*DEFAULT_FFMPEG_ARGS, '-i', input_filename, '-c:v', codec, '-rc', 'vbr_peak',
            	'-b:v', str_bitrate, '-maxrate', str_bitrate, *codecargs, output_filename]
    elif codec == 'libsvtav1':
        if threadcount == 1:
            levelofparallelism = '1'
        else:
            levelofparallelism = str(int(threadcount/2))
        encode_args_1 = ['SvtAv1EncApp', '-i', input_filename, '--rc', '1', '--tbr', str(round(bitrate/1000)),
                # '--passes', '2',
                  '--lp', levelofparallelism, '--stats', './ffmpeg_logs/'+codec,
                '--no-progress', '1', *codecargs, '-b', output_filename]

    metrics = []
    if verbose:
        print(os.getcwd())
        print(' '.join(encode_args_1))
        print(' '.join(encode_args_2))
    
    proc = subprocess.run(encode_args_1, stderr=subprocess.PIPE, text=True)
    output = proc.stderr.splitlines()
    if codec not in ['h264_amf', 'hevc_amf', 'libsvtav1']:
        proc2 = subprocess.run(encode_args_2, stderr=subprocess.PIPE, text=True)
        output += proc2.stderr.splitlines()

    if verbose:
        for line in output:
            print(line)


    for line in output:
        if codec == 'libsvtav1':
            if line.startswith('Total Execution Time'):
            # or line.startswith('Average Speed') or line.startswith('Total Encoding Time') or\
            #line.startswith('Total Encoding Time') or  or\
            #line.startswith('Average Latency') or line.startswith('Max Latency'):
                metrics.append(line)
        elif line.startswith('bench'):
            metrics.append(line)
    metrics.append(os.path.getsize(output_filename))

    if verbose:
        print("#" * 40 + codec + " COMPLETE" + "#" * 40)

    return metrics


def parse_two_pass_metrics(metrics, codec, verbose=False):
    if codec in ['h264_amf', 'hevc_amf']:
        timings = [timing[6:-1] for timing in metrics[0].split(' ')[1:]]
        maxrss = metrics[1][14:-3]
        filesize = metrics[-1]
    elif codec != 'libsvtav1':
        timings1 = [timing[6:-1] for timing in metrics[0].split(' ')[1:]]
        timings2 = [timing[6:-1] for timing in metrics[2].split(' ')[1:]]
        maxrss1 = metrics[1][14:-3]
        maxrss2 = metrics[3][14:-3]
        
        filesize = metrics[-1]
        
        timings = []
        for x,y in zip(timings1, timings2):
            timings.append(float_round_str(float(x)+float(y), 3))

        maxrss = maxrss1 if int(maxrss1) > int(maxrss2) else maxrss2
    else:
        parsed_exectimes = []
        for exectime in metrics[:-1]:
            parsed_exectimes.append(exectime[22:-3])
        exectime = float_round_str((int(parsed_exectimes[0])+int(parsed_exectimes[1]))/1000, 3)
        maxrss = "N/A"
        timings = ["N/A", "N/A", exectime]
        filesize = metrics[-1]

    return timings, maxrss, filesize


def run_tests_two_pass(fInfo: FileInfo, codecs, codecargs, runs, target_bitrate, verbosity):

    framecount = int(fInfo.framecount)    

    print("File name: ", fInfo.filename, ", file size: ", float_round_str(fInfo.filesize/1024, 2), "KiB", sep = "")
    print(fInfo)
    print("Target bitrate:", target_bitrate, "Target filesize:", int(target_bitrate * float(fInfo.framecount)/(float(Fraction(fInfo.framerate))*1024*8)), 'KiB')

    create_folder_tree(fInfo.basename)

    results = []
    for i in range(runs):
        print("Encoding batch no#", i)
        for codec in codecs:
            metrics = encode_video_two_pass(fInfo, codec, target_bitrate, codecargs[codec], verbose=verbosity)
            timings, maxrss, filesize = parse_two_pass_metrics(metrics, codec, verbose=verbosity)
            result = EncodingResults(codec, timings[2], maxrss, framecount, filesize, fInfo.filesize, fInfo.framerate)
            results.append(result)
            print(result)
        print()

    decode_encoded_videos(fInfo.basename, codecs, verbose=verbosity)

    vmaf_scores = calculate_vmaf_scores(fInfo, codecs, results, verbose=verbosity)

    print_statistics(results, codecs, vmaf_scores)

    generate_xlsx_report(fInfo.basename, framecount,
                         fInfo.filesize, results, vmaf_scores, codecargs)

    os.chdir("..\\..")

    clean_workspace(fInfo.basename)

    return results