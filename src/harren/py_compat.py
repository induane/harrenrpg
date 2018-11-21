from __future__ import absolute_import

"""Python compatibility."""
import os
import errno


try:
    xrange
except Exception:
    range = range     # Python 3
else:
    range = xrange    # Python 2


try:
    import cPickle as pickle
except Exception:
    import pickle


def mkdir_p(path):
    """Create a folder structure without erroring (mirror mkdir -p)."""
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


__all__ = (
    'mkdir_p',
    'pickle',
    'range',
)
