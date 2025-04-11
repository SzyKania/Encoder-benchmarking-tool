# Encoder benchmarking tool

This tool allows batch encoding of raw video sequences, via multiple encoders with multiple CRF values.

The results of encoding are later compared with raw input by multiple metrics, which can be chosen in the config (VMAF, SSIM, PSNR_HVS). Subsequent scores are later visualised via matplotlib in the form of RD-Curves. BD-Rates are also calculated and provided between all encoders.


## Dependencies
The following programs need to be added to your PATH in order for the program to run.
- [FFmpeg](https://ffmpeg.org) - for encoding and decoding purposes
- [vmaf](https://github.com/Netflix/vmaf) - for calculating metric scores

## Supported encoders
Currently five encoders are supported:
- libx264
- libx265
- libvvenc
- libvpx-vp9
- libsvtav1

## Supported metrics
- VMAF
- SSIM
- PSNR_HVS

## Configuration

Currently the encoding process is configurated by setting appropriate variables in three config files.

### test_config

This file has the most important settings, pertaining to the encoding parameters and the sequences used.

- codecs - a list of string names of encoders used for the test batch
- encoding_speed - 0-2, where 0 is slowest, 1 is default, 2 is fastest
- codeccrftables - dictionary, where key is encoder name and value is list of CRFs to be used during encoding. Ideally each encoder should have the same amount of CRF values.
- filenames - list of test sequence filenames in y4m format
- verbosity - if True, outputs stderr of ffmpeg, useful for debugging

### result_config

This file dictates which parameters should be measured, and the form in which they are later presented.

- include_vmaf/ssim/psnr_hvs - enables calculation of metrics. Note that VMAF is always calculated, but not including it via this flag omits it from plots and bd_rates.
- save_plot - saves RD curve plots to .png
- show_plot - creates a matplotlib popup with RD curves
- print_per_encode_statistics - enables console 
- per_file_xlsx_report - creates .xlsx reports per file encoded, including metric scores, compression rates, size of encoded sequences etc.
- print_bd_rates
- csv_bd_rates - saves bd_rates to a .csv files, useful for later processing.
- per_file_pickle_dump - saves a .pkl file including results for each file encoded. Useful for big encoding batches of multiple files, allowing later reconstruction of the test in case of a crash.
- per_batch_pickle_dump - saves a .pkl file including results from all files.

### load_config

This file is used in conjunction with the .pkl files, which can be enabled in result_config. It allows to recreate plots, statistics and to recreate batch results from per-file .pkl files.

- load_results - True/False, if enabled results are loaded instead of conducting a test batch.
- load_single_test - enable if the .pkl file is of a single test sequence instead of a batch.
- load_filename -  path to file, from root\test_results\
- restore_results - if enabled, combines the .pkl per sequence files into a batch pkl
- pkls_to_restore - list of pkl names to restore

