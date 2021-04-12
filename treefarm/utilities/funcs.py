"""
Utility functions



"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import errno
import os

def ensure_dir(path):
    r"""Parallel safe directory maker."""
    if os.path.exists(path):
        return path

    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno == errno.EEXIST:
            pass
        else:
            raise
    return path

def get_output_filename(name, keyword, suffix):
    r"""Return an appropriate filename for output.

    With a name provided by the user, this will decide how to appropriately name the
    output file by the following rules:

    1. if name is None, the filename will be the keyword plus the suffix.
    2. if name ends with "/" (resp "\" on Windows), assume name is a directory and the
       file will be named name/(keyword+suffix).  If the directory does not exist, first
       try to create it and raise an exception if an error occurs.
    3. if name does not end in the suffix, add the suffix.

    Parameters
    ----------
    name : str
        A filename given by the user.
    keyword : str
        A default filename prefix if name is None.
    suffix : str
        Suffix that must appear at end of the filename.
        This will be added if not present.

    Examples
    --------

    >>> get_output_filename(None, "Projection_x", ".png")
    'Projection_x.png'
    >>> get_output_filename("my_file", "Projection_x", ".png")
    'my_file.png'
    >>> get_output_filename("my_dir/", "Projection_x", ".png")
    'my_dir/Projection_x.png'

    """
    if name is None:
        name = keyword
    name = os.path.expanduser(name)
    if name.endswith(os.sep) and not os.path.isdir(name):
        ensure_dir(name)
    if os.path.isdir(name):
        name = os.path.join(name, keyword)
    if not name.endswith(suffix):
        name += suffix
    return name

def is_sequence(obj):
    """
    Grabbed from Python Cookbook / matplotlib.cbook.  Returns true/false for
    *obj* iterable.
    """
    try:
        len(obj)
        return True
    except TypeError:
        return False
