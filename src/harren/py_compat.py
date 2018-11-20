from __future__ import absolute_import

"""Python compatibility."""


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


__all__ = (
    'pickle',
    'range',
)
