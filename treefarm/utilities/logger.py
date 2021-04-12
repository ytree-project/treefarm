"""
ytree logger



"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import logging
import sys
from tqdm import tqdm

from yt.funcs import is_root
from yt.utilities.logger import ytLogger as mylog

# CRITICAL 50
# ERROR    40
# WARNING  30
# INFO     20
# DEBUG    10
# NOTSET   10

ufstring = "%(name)-3s: [%(levelname)-9s] %(asctime)s %(message)s"

treefarmLogger = logging.getLogger("treefarm")
treefarm_sh = logging.StreamHandler(stream=sys.stderr)
formatter = logging.Formatter(ufstring)
treefarm_sh.setFormatter(formatter)
treefarmLogger.addHandler(treefarm_sh)
treefarmLogger.setLevel(20)
treefarmLogger.propagate = False

def set_parallel_logger(comm):
    if comm.size == 1: return
    f = logging.Formatter("P%03i %s" % (comm.rank, ufstring))
    if len(treefarmLogger.handlers) > 0:
        treefarmLogger.handlers[0].setFormatter(f)

class TqdmProgressBar:
    # This is a drop in replacement for pbar
    # called tqdm
    def __init__(self, title, maxval):
        self._pbar = tqdm(leave=True, total=maxval, desc=title)
        self.i = 0

    def update(self, i=None):
        if i is None:
            i = self.i + 1
        n = i - self.i
        self.i = i
        self._pbar.update(n)

    def finish(self):
        self._pbar.close()

class DummyProgressBar:
    # This progressbar gets handed if we don't
    # want ANY output
    def __init__(self, *args, **kwargs):
        return

    def update(self, *args, **kwargs):
        return

    def finish(self, *args, **kwargs):
        return

class ParallelProgressBar:
    # This is just a simple progress bar
    # that prints on start/stop
    def __init__(self, title, maxval):
        self.title = title
        mylog.info("Starting '%s'", title)

    def update(self, *args, **kwargs):
        return

    def finish(self):
        mylog.info("Finishing '%s'", self.title)


def get_pbar(title, maxval, parallel=False):
    """
    This returns a progressbar of the most appropriate type, given a *title*
    and a *maxval*.
    """
    maxval = max(maxval, 1)
    from yt.config import ytcfg

    if (
        ytcfg.get("yt", "suppress_stream_logging")
        or ytcfg.get("yt", "internals", "within_testing")
        or maxval == 1
    ):
        return DummyProgressBar()
    elif ytcfg.get("yt", "internals", "parallel"):
        # If parallel is True, update progress on root only.
        if parallel:
            if is_root():
                return TqdmProgressBar(title, maxval)
            else:
                return DummyProgressBar()
        else:
            return ParallelProgressBar(title, maxval)
    pbar = TqdmProgressBar(title, maxval)
    return pbar
