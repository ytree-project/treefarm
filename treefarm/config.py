"""
ytree config



"""

#-----------------------------------------------------------------------------
# Copyright (c) ytree development team. All rights reserved.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import configparser
import os

CONFIG_DIR = os.environ.get("XDG_CONFIG_HOME",
    os.path.join(os.path.expanduser("~"), ".config", "treefarm"))

treefarmcfg = configparser.ConfigParser()
treefarmcfg.read(os.path.join(CONFIG_DIR, "treefarmrc"))
if not treefarmcfg.has_section("treefarm"):
    treefarmcfg.add_section("treefarm")
