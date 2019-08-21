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

class fake_pbar(object):
    def __init__(self, *args):
        pass
    def update(self, *args):
        pass
    def finish(self):
        pass
