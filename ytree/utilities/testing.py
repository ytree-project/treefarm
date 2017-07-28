"""
testing utilities



"""

#-----------------------------------------------------------------------------
# Copyright (c) 2016-2017, Britton Smith <brittonsmith@gmail.com>
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import h5py
from numpy.testing import \
    assert_array_equal
import os
import shutil
import tempfile
from unittest import \
    TestCase
from yt.testing import \
    assert_rel_equal

from ytree.config import \
    ytreecfg

if "YTREE_TEST_DATA_DIR" in os.environ:
    test_data_dir = os.environ["YTREE_TEST_DATA_DIR"]
else:
    test_data_dir = ytreecfg["ytree"].get("test_data_dir", ".")
generate_results = \
  int(os.environ.get("YTREE_GENERATE_TEST_RESULTS", 0)) == 1

class TempDirTest(TestCase):
    """
    A test class that runs in a temporary directory and
    removes it afterward.
    """

    def setUp(self):
        self.curdir = os.getcwd()
        self.tmpdir = tempfile.mkdtemp()
        os.chdir(self.tmpdir)

    def tearDown(self):
        os.chdir(self.curdir)
        shutil.rmtree(self.tmpdir)

def compare_arbors(a1, a2, groups=None, fields=None):
    """
    Compare all fields for all trees in two arbors.
    """

    if groups is None:
        groups = ["tree", "prog"]

    if fields is None:
        fields = a1.field_list

    for t1, t2 in zip(a1, a2):
        for field in fields:
            for group in groups:
                assert (t1[group, field] == t2[group, field]).all()
        t1.clear_fields()
        t2.clear_fields()

def compare_hdf5(fh1, fh2, compare=None, compare_groups=True,
                 **kwargs):
    """
    Compare all datasets between two hdf5 files.
    """

    if compare is None:
        compare = assert_array_equal
    if isinstance(fh1, str):
        fh1 = h5py.File(fh1, "r")
    if isinstance(fh2, str):
        fh2 = h5py.File(fh2, "r")

    if compare_groups:
        assert sorted(list(fh1.keys())) == sorted(list(fh2.keys())), \
          "%s and %s have different datasets in group %s." % \
          (fh1.file.filename, fh2.file.filename, fh1.name)

    for key in fh1.keys():
        if isinstance(fh1[key], h5py.Group):
            compare_hdf5(fh1[key], fh2[key],
                         compare_groups=compare_groups,
                         compare=compare, **kwargs)
        else:
            err_msg = "%s field not equal for %s and %s" % \
              (key, fh1.file.filename, fh2.file.filename)
            if fh1[key].dtype == "int":
                assert_array_equal(fh1[key].value, fh2[key].value,
                                   err_msg=err_msg)
            else:
                compare(fh1[key].value, fh2[key].value,
                        err_msg=err_msg, **kwargs)

def assert_array_rel_equal(a1, a2, decimals=16, **kwargs):
    """
    Wraps assert_rel_equal with, but decimals is a keyword arg.
    """
    assert_rel_equal(a1, a2, decimals, **kwargs)

def requires_file(req_file):

    def ffalse(func):
        return None

    def ftrue(func):
        return func

    if os.path.exists(req_file):
        return ftrue
    else:
        return ffalse
