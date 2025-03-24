from bs4 import BeautifulSoup
import os.path
import subprocess
import os
import shutil


class FileInfo:
    def __init__(self, height, width, framerate, framecount, pixel_format, filesize, filename):
        self.height = height
        self.width = width
        self.framerate = framerate
        self.framecount = framecount
        self.pixel_format = pixel_format
        self.resolution = self.width+"x"+self.height
        self.filesize = filesize
        self.filename = filename
        self.basename = filename.split(".")[0]
    def __str__(self):
        return \
            "Frames: " + self.framecount +\
            " FPS: " + self.framerate +\
            " Pixel format: " + self.pixel_format+\
            " Resolution: " + self.resolution


def get_file_info(filename, write_to_file=False):
    filepath = os.getcwd() + "\\test_sequences\\" + filename
    proc = subprocess.run(['ffprobe', '-v', 'quiet', '-print_format', 'xml', '-show_format', '-show_streams', filepath], stdout=subprocess.PIPE)
    output = proc.stdout
    Bs_data = BeautifulSoup(output, "xml")
    if write_to_file:
        f = open(filename + '_ffprobe.xml', 'x')
        f.write(str(Bs_data))
        f.close()
    height = Bs_data.find('stream').get('height')
    width = Bs_data.find('stream').get('width')
    framerate = Bs_data.find('stream').get('r_frame_rate')
    framecount = Bs_data.find('stream').get('duration_ts')
    pix_fmt = Bs_data.find('stream').get('pix_fmt')
    original_filesize = os.path.getsize(filepath)
    fileinfo = FileInfo(height, width, framerate, framecount, pix_fmt, original_filesize, filename)
    return fileinfo


def create_folder_tree(basename):
    path = os.getcwd() + "\\sequence_workspaces\\" + basename
    if os.path.isdir(path):
        print("Removing encoded files from last run")
        shutil.rmtree(path+"\\encoded_videos")
        shutil.rmtree(path+"\\decoded_videos")
        shutil.rmtree(path+"\\libvmaf_logs")
        shutil.rmtree(path+"\\ffmpeg_logs")
        os.makedirs(path+"\\encoded_videos")
        os.makedirs(path+"\\decoded_videos")
        os.makedirs(path+"\\libvmaf_logs")
        os.makedirs(path+"\\ffmpeg_logs")
    if not os.path.isdir(path):
        os.makedirs(path)
        os.chdir(path)
        os.makedirs(".\\encoded_videos")
        os.makedirs(".\\decoded_videos")
        os.makedirs(".\\libvmaf_logs")
        os.makedirs(".\\ffmpeg_logs")
    os.chdir(path)


def clean_workspace(basename):
    path = os.getcwd() + "\\sequence_workspaces\\" + basename
    if os.path.isdir(path):
        print("Remove files after encoding")
        shutil.rmtree(path)