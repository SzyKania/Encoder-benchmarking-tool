class ResultConfig:
    def __init__(self, save_plot = False, show_plot = False, print_bd_rates = False,
                  csv_bd_rates = False, include_vmaf = False, include_ssim = False,
                  include_psnr_hvs = False, per_file_pickle_dump = False, per_batch_pickle_dump = False,
                  print_per_encode_statistics = False, per_file_xlsx_report = False):
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
        self.per_file_pickle_dump = per_file_pickle_dump
        self.per_batch_pickle_dump = per_batch_pickle_dump
        self.print_per_encode_statistics = print_per_encode_statistics
        self.per_file_xlsx_report = per_file_xlsx_report

print_per_encode_statistics = False
per_file_xlsx_report = False
save_plot = False
show_plot = False
print_bd_rates = True
csv_bd_rates = True
include_vmaf = True
include_ssim = True
include_psnr_hvs = True
per_file_pickle_dump = False
per_batch_pickle_dump = False

resultconfig = ResultConfig(save_plot, show_plot,
                            print_bd_rates, csv_bd_rates,
                            include_vmaf, include_ssim, include_psnr_hvs,
                            per_file_pickle_dump, per_batch_pickle_dump,
                            print_per_encode_statistics, per_file_xlsx_report)