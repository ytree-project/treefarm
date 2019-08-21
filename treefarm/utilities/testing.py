import os

from treefarm.config import \
    treefarmcfg

if "YTREE_TEST_DATA_DIR" in os.environ:
    test_data_dir = os.environ["YTREE_TEST_DATA_DIR"]
else:
    test_data_dir = treefarmcfg["treefarm"].get("test_data_dir", ".")
generate_results = \
  int(os.environ.get("YTREE_GENERATE_TEST_RESULTS", 0)) == 1
