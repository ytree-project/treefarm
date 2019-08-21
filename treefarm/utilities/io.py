from yt.convenience import \
    load as _yt_load
from yt.utilities.logger import \
    ytLogger

def yt_load(filename, **kwargs):
    """
    Suppress logging for yt.load, but return to original setting.

    This allows yt.load to show logs in scripts, but not in ytree.
    """
    level = ytLogger.level
    if level > 10 and level < 40:
        ytLogger.setLevel(40)
    ds = _yt_load(filename, **kwargs)
    ytLogger.setLevel(level)
    return ds
