class LoadConfig:
    def __init__(self, load_results = False, load_single_test = False, 
                 load_filename = None, restore_results = False, pkls_to_restore = None):
        self.load_results = load_results
        self.load_single_test = load_single_test
        self.load_filename = load_filename
        self.restore_results = restore_results
        self.pkls_to_restore = pkls_to_restore

#region################ LOAD RESULTS #######################

load_results = False
load_single_test = False
load_filename = "a1_class\\a1_class_tuple_20250123_160417"
load_filename = "vidyo_tuple_20250314_184739"

load_filename += ".pkl"

#endregion
#region############# BATCH RESTORATION #####################

restore_results = False
pkls_to_restore = []
# pkls_to_restore.append("PierSeaSide_3840x2160_2997fps_10bit_420_v2_20250123-125211.pkl")
# pkls_to_restore.append("NocturneDance_3840x2160p_10bit_60fps_20250123-110822.pkl")
#endregion

loadconfig = LoadConfig(load_results, load_single_test, load_filename, restore_results, pkls_to_restore)