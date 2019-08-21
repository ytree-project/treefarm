import os

from treefarm.config import \
    treefarmcfg

if "TREEFARM_TEST_DATA_DIR" in os.environ:
    test_data_dir = os.environ["TREEFARM_TEST_DATA_DIR"]
else:
    test_data_dir = treefarmcfg["treefarm"].get("test_data_dir", ".")
