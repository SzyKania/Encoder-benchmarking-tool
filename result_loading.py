from datetime import datetime
from configs.load_config import LoadConfig
from configs.result_config import ResultConfig
from metrics import plot_results
import pickle


def load_results(loadconfig: LoadConfig, resultconfig: ResultConfig):
    with open("test_results\\" + loadconfig.load_filename, 'rb') as file:
        loaded_results = pickle.load(file)
    results_crfs_files = loaded_results[0]
    testconfig = loaded_results[1]
    if loadconfig.load_single_test:
        if testconfig.crf_count >= 3 and (resultconfig.show_plot or resultconfig.save_plot):
            plot_results(results_crfs_files, testconfig.codecs, loadconfig.load_filename[:-4], resultconfig)
        quit()
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


def create_batch_pkl_from_single_test_pkls(loadconfig: LoadConfig):
    print("Reconstructing batch test results from following files:", loadconfig.pkls_to_restore)
    results_crfs_files, testconfig = combine_crf_results(loadconfig.pkls_to_restore)
    results_filename = "test_results\\" + testconfig.test_name + "_tuple_" \
                + datetime.now().strftime("%Y%m%d_%H%M%S") + ".pkl"
    with open(results_filename, 'wb') as file:
        results_tuple = (results_crfs_files, testconfig)
        pickle.dump(results_tuple, file)

    print("Reconstructed results saved as", results_filename)
