from configs.load_config import loadconfig
from configs.test_config import testconfig
from configs.result_config import resultconfig

from result_loading import create_batch_pkl_from_single_test_pkls, load_results
from encoding import run_crf_test_batch
from metrics import visualise_results

if __name__ == "__main__":
    if loadconfig.restore_results:
        create_batch_pkl_from_single_test_pkls(loadconfig)
        quit()
    if not loadconfig.load_results:
        results_crfs_files = run_crf_test_batch(testconfig, resultconfig)
    else:
        results_crfs_files, testconfig = load_results(loadconfig, resultconfig)
    visualise_results(results_crfs_files, testconfig, resultconfig)